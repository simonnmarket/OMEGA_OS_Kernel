import os
import time
import asyncio
import numpy as np
import pandas as pd
from scipy import stats
from omega_integration_gate import (
    config_data,
    validate_config_schema,
    RiskParameters,
    OmegaBaseAgent,
    ChaosMonkeySpecification,
    ChaosPerturbationType,
    ChaosOracleState,
    WalkForwardSpecification,
    EmpiricalTPCalibrator,
    DistributedConcurrencyModel,
    ModuleRiskProfile,
    audit_module
)

# =============================================================================
# MOCKS E ARTEFATOS DE TESTE
# =============================================================================

class MockValidAgent(OmegaBaseAgent):
    def execute(self, market_data: np.ndarray) -> dict:
        return {"direction": 1, "size": 1.0}
    def get_risk_parameters(self) -> RiskParameters:
        return RiskParameters(
            max_risk_per_trade=0.01,
            max_drawdown_daily=0.03,
            kelly_fraction=0.1,
            max_leverage=5.0,
            min_sharpe_required=0.5,
            proposed_tp_distance=100.0
        )
    async def force_halt(self, reason: str) -> bool:
        return True

def generate_mock_market_data(rows=100) -> pd.DataFrame:
    np.random.seed(42)
    base_price = 2000.0
    close = base_price + np.random.randn(rows).cumsum() * 5
    high = close + abs(np.random.randn(rows) * 2)
    low = close - abs(np.random.randn(rows) * 2)
    spread = np.random.randint(5, 15, size=rows)
    tick_volume = np.random.randint(100, 1000, size=rows)
    real_volume = tick_volume * 10
    
    return pd.DataFrame({
        'time': pd.date_range('2026-03-01', periods=rows, freq='5min'),
        'high': high,
        'low': low,
        'close': close,
        'spread': spread,
        'tick_volume': tick_volume,
        'real_volume': real_volume
    })

# =============================================================================
# CASOS DE TESTE
# =============================================================================

def test_config_schema():
    print("Testando Schema do Config...")
    assert validate_config_schema(config_data) == True
    print("  ✅ Schema validado com sucesso.")

def test_pilar_1_hash_forense():
    print("\nTestando Pilar 1 (Contrato e Hash Forense)...")
    agent = MockValidAgent()
    assert agent.contract_hash != "SYSTEM_HASH_VALIDATION_ERROR"
    assert agent.verify_contract_integrity() == True
    print("  ✅ Imutabilidade confirmada. Hash gerado:", agent.contract_hash[:16])

def test_pilar_2_chaos_monkey():
    print("\nTestando Pilar 2 (Chaos Monkey Determinístico)...")
    df = generate_mock_market_data(50)
    spec = ChaosMonkeySpecification()
    perturbations = spec.get_perturbations()
    assert len(perturbations) == 5, "Devem existir 5 cenários de Chaos."
    
    # Testa Volume Zero
    p_vol = next(p for p in perturbations if p.perturbation_type == ChaosPerturbationType.VOLUME_ZERO)
    corrupted_vol = p_vol.corrupt_func(df)
    assert corrupted_vol.iloc[-1]['tick_volume'] == 0, "Deveria corromper "
    
    # Testa Oracle (Agente Responde Corretamente)
    assert p_vol.oracle_check_func({"direction": 0}) == True
    assert p_vol.oracle_check_func({"direction": 1}) == False
    
    print("  ✅ Configurações de Caos e Oracle instanciadas e corrompendo DataFrames devidamente.")

def test_pilar_3_walk_forward():
    print("\nTestando Pilar 3 (Estatística de Lo 2002)...")
    wf_spec = WalkForwardSpecification("SCALPING")
    
    # Agente God Mode
    result_god = wf_spec.evaluate_walk_forward_result(is_sharpe=3.0, oos_sharpe=2.8, n_oos_trades=500)
    assert result_god["approved"] == True, "Agente excepcional deveria passar"
    
    # Agente Medíocre e Ruídos
    result_noise = wf_spec.evaluate_walk_forward_result(is_sharpe=0.6, oos_sharpe=0.1, n_oos_trades=100)
    assert result_noise["approved"] == False, "Agente com degradação/P-value fraco deve falhar"
    
    print(f"  ✅ Diferenciação estatística robusta (God Mode p-value: {result_god['p_value']:.4f}, Noise: {result_noise['p_value']:.4f})")

def test_pilar_4_tp_empirical():
    print("\nTestando Pilar 4 (Calibração Empírica ATR)...")
    df = generate_mock_market_data(100)
    calibrator = EmpiricalTPCalibrator(df)
    min_tp = calibrator.calibrate_min_tp_threshold()
    
    assert min_tp > 0, "O threshold ATR base não deve ser zero."
    assert calibrator.is_tp_respectable(min_tp + 10) == True
    assert calibrator.is_tp_respectable(min_tp - 10) == False
    
    print(f"  ✅ Percentil 5 ATR estabelecido rigorosamente em: {min_tp:.4f} pts")

async def test_pilar_5_concurrency():
    print("\nTestando Pilar 5 (Prevenção Assíncrona Liveness)...")
    model = DistributedConcurrencyModel()
    model.register_resource("TRADE_LOCK")
    
    t1 = await model.acquire_with_timeout("TRADE_LOCK")
    assert t1 == True
    
    # Duplicata (Double Spend simulado falha de forma silente ou timeout)
    t2 = await model.acquire_with_timeout("TRADE_LOCK", timeout=0.01) # Reduzido para testar rápido
    assert t2 == False
    
    model.release("TRADE_LOCK")
    # Testa risco temporal em chamadas seguidas (< 20ms)
    await model.acquire_with_timeout("TRADE_LOCK")
    risk_detected = model.detect_double_spend_risk("TRADE_LOCK")
    assert risk_detected == True, "Deveria barrar chamadas < 20ms"
    
    print("  ✅ Mutex Locks, time.monotonic() e double spend mitigados.")

def test_matriz_avaliacao_e_auditoria():
    print("\nTestando Matriz Escalonada e Função de Auditoria...")
    agent = MockValidAgent()
    df = generate_mock_market_data()
    
    audit_res = audit_module(
        agent=agent,
        df_historical_calibration=df,
        is_sharpe=2.5,
        oos_sharpe=2.2,
        n_oos_trades=1500,
        chaos_score=1.0,
        concurrency_score=1.0,
        strategy_type="SCALPING"
    )
    
    assert audit_res["grade"] == "TIER-0 (A+)"
    assert audit_res["overall_confidence"] >= 0.85
    assert audit_res["action"] == "LIVE_EXECUTION"
    
    print(f"  ✅ Agente God-Mode auditado. Overall Score: {audit_res['overall_confidence']:.4f}. Verdict: {audit_res['action']}")

async def run_all():
    print("=" * 60)
    print("🚀 INICIANDO BATERIA DE TESTES DO O.I.G. V3.0.0")
    print("=" * 60)
    
    try:
        test_config_schema()
        test_pilar_1_hash_forense()
        test_pilar_2_chaos_monkey()
        test_pilar_3_walk_forward()
        test_pilar_4_tp_empirical()
        await test_pilar_5_concurrency()
        test_matriz_avaliacao_e_auditoria()
        
        print("\n" + "=" * 60)
        print("🏆 TODOS OS PILARES (UNITÁRIOS E INTEGRAÇÃO) PASSARAM. SISTEMA BLINDADO.")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ FALHA ESTRUTURAL DE TESTE: {e}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all())
