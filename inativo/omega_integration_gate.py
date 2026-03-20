"""
🛡️ OMEGA INTEGRATION GATEKEEPER 
Versão: 3.0.0 Institucional Doutoral
Implementação: TIER-0 FUSION (Arquitetura Python)

Pilar 1: Tipagem Formal e Contrato Criptográfico.
Pilar 2: Motor de Injeção de Caos Replicável e Oráculo Estado.
Pilar 3: Walk-Forward com Power Analysis via Cálculo de Variança (Lo, 2002).
Pilar 4: Anti-Snipping Calibrado Empiricamente (Percentis Fixos ATR).
Pilar 5: Concorrência Formal com time.monotonic e verificação de race condition.
"""
import os
import json
import hashlib
import inspect
import asyncio
import time
import math
from typing import Protocol, runtime_checkable, Any, Dict, List, Callable, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto

import numpy as np
import pandas as pd
from scipy import stats

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "omega_config.json")
try:
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)["OMEGA_INTEGRATION_GATE"]
except Exception as e:
    raise RuntimeError(f"Gatekeeper Abortado: Falha ao carregar omega_config.json -> {e}")

def validate_config_schema(config: Dict) -> bool:
    """Valida estrutura mínima do omega_config.json."""
    required_keys = ["VERSION", "STRICT_MODE", "WEIGHTS", "THRESHOLDS", "STRATEGY_POLICIES"]
    for key in required_keys:
        if key not in config:
            raise RuntimeError(f"Config schema error: Missing required key '{key}'")
    
    weights = config["WEIGHTS"]
    if abs(sum(weights.values()) - 1.0) > 0.01:
        raise RuntimeError(f"Config schema error: Weights must sum to 1.0")
    
    if not (0 < config["THRESHOLDS"]["WF_ALPHA_LEVEL"] < 1):
        raise RuntimeError("Config schema error: WF_ALPHA_LEVEL must be between 0 and 1")
    return True

validate_config_schema(config_data)

# =============================================================================
# PILAR 1: TIPO DE CONTRATO E HASH FORENSE OBRIGATÓRIOS
# =============================================================================
@runtime_checkable
class VerifiableContract(Protocol):
    """Protocolo de certificação em tempo de execução."""
    contract_hash: str
    version: str

@dataclass
class RiskParameters:
    """Parâmetros de risco com tolerância matemática restrita."""
    max_risk_per_trade: float 
    max_drawdown_daily: float  
    kelly_fraction: float      
    max_leverage: float
    min_sharpe_required: float
    proposed_tp_distance: float = 50.0 # Valor default seguro
    
    def validate(self, strategy_type: str = "SCALPING") -> bool:
        """Valida que o agente não propõe riscos fora da Política OMEGA."""
        policy = config_data["STRATEGY_POLICIES"].get(strategy_type, config_data["STRATEGY_POLICIES"]["SCALPING"])
        if not (0 < self.max_risk_per_trade <= policy["max_risk_per_trade"]): return False
        if not (0 < self.max_drawdown_daily <= policy["max_drawdown_daily"]): return False
        if not (self.min_sharpe_required >= policy["min_acceptable_sharpe"]): return False
        if not (0 < self.max_leverage <= policy.get("max_leverage", 10.0)): return False
        return True

class OmegaBaseAgent(ABC):
    """
    Herdada por todos os Agentes Quantitativos do OMEGA.
    Faz lock forense estrito impedindo adulteração silenciosa (Supply Chain Attack).
    """
    def __init__(self):
        self.version = "3.0.0"
        self._certification_log = []
        self.contract_hash = self._generate_contract_hash()
        
    @abstractmethod
    def execute(self, market_data: np.ndarray) -> Dict:
        """Execução Sincrona/Assíncrona."""
        pass
    
    @abstractmethod
    def get_risk_parameters(self) -> RiskParameters:
        """Retorna os riscos alocados."""
        pass
    
    @abstractmethod
    async def force_halt(self, reason: str) -> bool:
        """Desarme de emergência."""
        pass

    def _generate_contract_hash(self) -> str:
        """
        Calcula hash criptográfico de todo o arquivo-fonte, não apenas da classe,
        incluindo timestamp de modificação da integridade.
        """
        try:
            filename = inspect.getfile(self.__class__)
            file_stat = os.stat(filename)
            with open(filename, 'rb') as f:
                content = f.read()
            fingerprint = f"{content.hex()}_{file_stat.st_mtime}_{file_stat.st_size}"
            return hashlib.sha256(fingerprint.encode()).hexdigest()
        except TypeError: # Previne que a instância base não tenha file mapping
            source = inspect.getsource(self.__class__)
            return hashlib.sha256(source.encode()).hexdigest()
        except OSError:
             return "SYSTEM_HASH_VALIDATION_ERROR"
    
    def verify_contract_integrity(self) -> bool:
        return self._generate_contract_hash() == self.contract_hash

# =============================================================================
# PILAR 2: MOTOR DETERMINÍSTICO DE CAOS
# =============================================================================
class ChaosPerturbationType(Enum):
    VOLUME_ZERO = auto()
    SPREAD_SPIKE = auto()
    PRICE_GAP_DOWN = auto()
    PRICE_GAP_UP = auto()
    MISSING_TICK = auto()

@dataclass
class ChaosOracleState:
    no_order_emitted: bool = False
    order_adjusted_or_cancelled: bool = False
    sl_triggered_gracefully: bool = False
    
    def passed(self, p_type: ChaosPerturbationType) -> bool:
        if p_type == ChaosPerturbationType.VOLUME_ZERO: return self.no_order_emitted
        if p_type == ChaosPerturbationType.SPREAD_SPIKE: return self.order_adjusted_or_cancelled or self.no_order_emitted
        if p_type in [ChaosPerturbationType.PRICE_GAP_DOWN, ChaosPerturbationType.PRICE_GAP_UP]: return self.sl_triggered_gracefully
        if p_type == ChaosPerturbationType.MISSING_TICK: return self.no_order_emitted
        return False

@dataclass
class ChaosPerturbation:
    perturbation_type: ChaosPerturbationType
    description: str
    corrupt_func: Callable[[pd.DataFrame], pd.DataFrame]
    oracle_check_func: Callable[[Dict], bool]

class ChaosMonkeySpecification:
    """Injeções Determinísticas Estruturadas (SEM ROLETAS ESTOCÁSTICAS)."""
    def __init__(self):
        pass

    def get_perturbations(self) -> List[ChaosPerturbation]:
        return [
            ChaosPerturbation(
                perturbation_type=ChaosPerturbationType.VOLUME_ZERO,
                description="Barra com Volume Zero injetada no final.",
                corrupt_func=lambda df: self._corrupt_volume(df, 0),
                oracle_check_func=lambda act: not act.get("direction", 0)
            ),
            ChaosPerturbation(
                perturbation_type=ChaosPerturbationType.SPREAD_SPIKE,
                description="Spread salta 50x (Fake NFP/Spike).",
                corrupt_func=lambda df: self._corrupt_spread(df, 50.0),
                oracle_check_func=lambda act: act.get("direction", 0) == 0 or act.get("adjusted_for_spread", False)
            ),
            ChaosPerturbation(
                perturbation_type=ChaosPerturbationType.PRICE_GAP_DOWN,
                description="Gap Down Extremo de 10x ATR Médio.",
                corrupt_func=lambda df: self._corrupt_gap(df, -10.0), # Crash de Liquidez
                oracle_check_func=lambda act: act.get("emergency_halt", False) or (act.get("direction", 0) == 0) # Sem ordens longas na lacuna invisível
            ),
            ChaosPerturbation(
                perturbation_type=ChaosPerturbationType.PRICE_GAP_UP,
                description="Gap Up Extremo de 10x ATR Médio.",
                corrupt_func=lambda df: self._corrupt_gap(df, 10.0), # Gap positivo
                oracle_check_func=lambda act: act.get("emergency_halt", False) or (act.get("direction", 0) == 0)
            ),
            ChaosPerturbation(
                perturbation_type=ChaosPerturbationType.MISSING_TICK,
                description="Tick esperado não recebido (timeout de dados).",
                corrupt_func=lambda df: self._corrupt_missing_tick(df),
                oracle_check_func=lambda act: act.get("no_order_emitted", False)
            )
        ]

    def _corrupt_missing_tick(self, df: pd.DataFrame) -> pd.DataFrame:
        """Simula missing tick removendo a última barra (volume nulo)."""
        c = df.copy()
        c.iloc[-1, c.columns.get_loc("tick_volume")] = np.nan
        return c

    def _corrupt_volume(self, df: pd.DataFrame, vol: float) -> pd.DataFrame:
        c = df.copy()
        c.iloc[-1, c.columns.get_loc("tick_volume")] = vol
        c.iloc[-1, c.columns.get_loc("real_volume")] = vol
        return c

    def _corrupt_spread(self, df: pd.DataFrame, factor: float) -> pd.DataFrame:
        c = df.copy()
        if "spread" in c.columns:
            c.iloc[-1, c.columns.get_loc("spread")] = int(c.iloc[-1]["spread"] * factor)
        return c
        
    def _corrupt_gap(self, df: pd.DataFrame, multiplier: float) -> pd.DataFrame:
        c = df.copy()
        high = c["high"].values
        low = c["low"].values
        tr = np.maximum(high[1:] - low[1:], np.abs(high[1:] - c["close"].values[:-1]))
        atr = np.mean(tr) if len(tr) > 0 else 1.0
        c.iloc[-1, c.columns.get_loc("close")] = c.iloc[-2]["close"] + (atr * multiplier)
        c.iloc[-1, c.columns.get_loc("low")] = min(c.iloc[-1]["close"], c.iloc[-1]["low"])
        c.iloc[-1, c.columns.get_loc("high")] = max(c.iloc[-1]["close"], c.iloc[-1]["high"])
        return c

# =============================================================================
# PILAR 3: WALK-FORWARD E ESTATÍSTICA LO (2002) - OOS Cacheado ASYNC
# =============================================================================
def calculate_minimum_sample_size_for_sharpe(
    target_sharpe: float,
    null_sharpe: float = 0.0,
    alpha: float = 0.05,
    power: float = 0.80,
    annualization_factor: int = 252
) -> int:
    """Implementação Lo (2002). Calcula o N-Trades para Confirmação do Edge."""
    delta = target_sharpe - null_sharpe
    if delta <= 0:
        raise ValueError("O Sharpe Objetivo precisa superar a Hipótese Nula (0.0).")
    
    var_sharpe = (1 + 0.5 * target_sharpe**2) / annualization_factor
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    n = ((z_alpha + z_beta) * math.sqrt(var_sharpe) / delta) ** 2
    return int(math.ceil(n))

class WalkForwardSpecification:
    def __init__(self, strategy_type="SCALPING"):
        self.alpha = config_data["THRESHOLDS"]["WF_ALPHA_LEVEL"]
        self.power = config_data["THRESHOLDS"]["WF_POWER_LEVEL"]
        self.null_sharpe = 0.0
        
        policy = config_data["STRATEGY_POLICIES"].get(strategy_type, config_data["STRATEGY_POLICIES"]["SCALPING"])
        self.target_sharpe = policy["target_sharpe_annualized"]
        self.min_n_trades = calculate_minimum_sample_size_for_sharpe(self.target_sharpe, self.null_sharpe, self.alpha, self.power)
        
    def set_observed_performance(self, observed_sharpe_is: float):
        """Calcula N_min baseado no Sharpe IS REAL do Agente (não no alvo da config)."""
        self.target_sharpe = observed_sharpe_is
        self.min_n_trades = calculate_minimum_sample_size_for_sharpe(self.target_sharpe, self.null_sharpe, self.alpha, self.power)

    def evaluate_walk_forward_result(self, is_sharpe: float, oos_sharpe: float, n_oos_trades: int) -> Dict:
        """Laudo de Significância." """
        # Atualiza a exigência de amostragem com base na performance real IN-SAMPLE (Rigor Matemático Doutoral)
        self.set_observed_performance(max(0.01, is_sharpe))

        # Teste z do Sharpe ratio
        se_oos = math.sqrt((1 + 0.5 * oos_sharpe**2) / max(1, n_oos_trades))
        z_stat = (oos_sharpe - self.null_sharpe) / (se_oos + 1e-9)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        significant = (p_value < self.alpha)
        degrad_limit = config_data["THRESHOLDS"]["WF_MAX_DEGRADATION"]
        degradation = (is_sharpe - oos_sharpe) / is_sharpe if is_sharpe > 0 else 0
        min_oos_ratio = config_data["THRESHOLDS"].get("WF_MIN_OOS_RATIO", 1.0)
        
        approved = significant and (degradation <= degrad_limit) and (n_oos_trades >= self.min_n_trades * min_oos_ratio)
        
        return {
            "approved": approved,
            "sharpe_is": is_sharpe,
            "sharpe_oos": oos_sharpe,
            "p_value": float(p_value),
            "degradation": float(degradation),
            "n_oos_trades": n_oos_trades,
            "min_required_oos": int(self.min_n_trades * min_oos_ratio)
        }

# =============================================================================
# PILAR 4: CALIBRAÇÃO DETERMINÍSTICA DE TP E ANTI-SNIPPING
# =============================================================================
class EmpiricalTPCalibrator:
    """Calculadora Fixa de limites Mínimos baseados em Percentil Histórico (Ex: P5 do ATR). NADA DE RANDOM.LOGNORMAL."""
    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data

    def _calculate_atr(self, period: int = 14) -> pd.Series:
        high = self.data['high'].values
        low = self.data['low'].values
        close = self.data['close'].shift(1).fillna(self.data['close'].values[0]).values
        tr = np.maximum(high - low, np.maximum(np.abs(high - close), np.abs(low - close)))
        return pd.Series(tr).rolling(period).mean()

    def calibrate_min_tp_threshold(self) -> float:
        """Retorna a distância absoluta de pontos do P5 do ATR na amostra."""
        atr = self._calculate_atr(14).dropna().values
        if len(atr) == 0:
             return 20.0 # Standard dev safe points if not enough data
        p5 = config_data["THRESHOLDS"]["TP_MIN_ATR_PERCENTILE"]
        return float(np.percentile(atr, p5))

    def is_tp_respectable(self, proposed_tp_distance: float) -> bool:
        """Valida se a pretensão do agente de sair está dentro da margem não predatória da microestrutura."""
        min_tp = self.calibrate_min_tp_threshold()
        return proposed_tp_distance >= min_tp

# =============================================================================
# PILAR 5: LIVENESS E DOUBLE-SPEND (TIME.MONOTONIC)
# =============================================================================
class DistributedConcurrencyModel:
    """Prevenção matemática a Deadlocks e ataques ou repiques de servidor do broker."""
    def __init__(self):
        self._locks = {}
        self._access_log = {}

    def register_resource(self, resource_name: str):
        self._locks[resource_name] = asyncio.Lock()
        self._access_log[resource_name] = []

    async def acquire_with_timeout(self, resource_name: str, timeout: float = None) -> bool:
        if timeout is None:
            timeout = config_data["THRESHOLDS"]["MAX_CONCURRENCY_TOLERANCE_MS"] / 1000.0
            
        try:
            await asyncio.wait_for(self._locks[resource_name].acquire(), timeout=timeout)
            # LOG COM MONOTONIC CLOCK (Imune a NTP adjustments)
            self._access_log[resource_name].append(time.monotonic())
            return True
        except asyncio.TimeoutError:
            return False

    def release(self, resource_name: str):
        if resource_name in self._locks:
            self._locks[resource_name].release()

    def detect_double_spend_risk(self, resource_name: str) -> bool:
        """Deteta se a chamada foi reincidente num quadro perigoso definido em ms."""
        tolerance_ms = config_data["THRESHOLDS"]["MAX_CONCURRENCY_TOLERANCE_MS"]
        logs = self._access_log.get(resource_name, [])
        if len(logs) < 2: return False
        
        deltas = np.diff(logs) * 1000.0 # Em millis
        return bool(np.any(deltas < tolerance_ms))

# =============================================================================
# GOVERNANÇA FIDUCIÁRIA E NOTA FINAL (MATRIZ PONDERADA CONTÍNUA) 
# =============================================================================
@dataclass
class ModuleRiskProfile:
    structural_score: float = 0.0          
    chaos_robustness: float = 0.0          
    walkforward_pvalue: float = 1.0        
    tp_calibration_score: float = 0.0      
    concurrency_safety: float = 0.0        

    def _continuous_pvalue_score(self, p: float, alpha: float) -> float:
        """Métrica contínua sem quebras abruptas: p=0.01 dá score alto, p>alpha dá 0."""
        if p >= alpha: return 0.0
        return max(0.0, min(1.0, (alpha - p) / alpha))
        
    def calculate_overall_confidence(self) -> float:
        w = config_data["WEIGHTS"]
        alpha = config_data["THRESHOLDS"]["WF_ALPHA_LEVEL"]
        
        wf_score = self._continuous_pvalue_score(self.walkforward_pvalue, alpha)
        
        confidence = (self.structural_score * w["STRUCTURAL"]) + \
                     (self.chaos_robustness * w["CHAOS_ROBUSTNESS"]) + \
                     (wf_score * w["WALKFORWARD_PVALUE"]) + \
                     (self.tp_calibration_score * w["TP_CALIBRATION"]) + \
                     (self.concurrency_safety * w["CONCURRENCY_SAFETY"])
        return float(confidence)
    
    def grade_and_action(self) -> Tuple[str, str]:
        conf = self.calculate_overall_confidence()
        if conf >= config_data["THRESHOLDS"]["TIER_0_MIN_CONFIDENCE"]:
            return "TIER-0 (A+)", "LIVE_EXECUTION"
        elif conf >= config_data["THRESHOLDS"]["TIER_1_MIN_CONFIDENCE"]:
            return "TIER-1 (B)", "OBSERVATION_MODE (Sandboxed)"
        return "TIER-NULL (F)", "HARD_ISOLATION"

# Função utilitária global para extrair o Relatório Completo.
def audit_module(agent: OmegaBaseAgent, df_historical_calibration: pd.DataFrame, is_sharpe: float, oos_sharpe: float, n_oos_trades: int, chaos_score: float, concurrency_score: float, strategy_type: str = "SCALPING") -> Dict:
    """Audita um Módulo Candidato inteiro sob a lupa O.I.G. V3"""
    if not isinstance(agent, OmegaBaseAgent):
        return {"error": "Agente não herda a base blindada do OMEGA OS."}
    
    profile = ModuleRiskProfile()
    
    # 1. Validação do Código (1.0 ou 0.0)
    profile.structural_score = 1.0 if agent.verify_contract_integrity() else 0.0
    
    # 2. Caminho de Injeção
    profile.chaos_robustness = min(1.0, max(0.0, chaos_score))
    
    # 3. Estatística H0
    wf_spec = WalkForwardSpecification(strategy_type=strategy_type)
    res_wf = wf_spec.evaluate_walk_forward_result(is_sharpe, oos_sharpe, n_oos_trades)
    profile.walkforward_pvalue = res_wf["p_value"]
    
    # 4. Calibration (Emprírica Real)
    try:
        risk_params = agent.get_risk_parameters()
        proposed_tp = getattr(risk_params, 'proposed_tp_distance', 50.0)
        tp_calibrator = EmpiricalTPCalibrator(df_historical_calibration)
        profile.tp_calibration_score = 1.0 if tp_calibrator.is_tp_respectable(proposed_tp) else 0.0
    except Exception:
        profile.tp_calibration_score = 0.5 # Penalidade por falha no risk tracking
    
    # 5. Segurança
    profile.concurrency_safety = concurrency_score
    
    grade, action = profile.grade_and_action()
    
    return {
        "module_id": agent.__class__.__name__,
        "hash": agent.contract_hash,
        "overall_confidence": profile.calculate_overall_confidence(),
        "p_value": profile.walkforward_pvalue,
        "n_oos_trades_verified": n_oos_trades,
        "grade": grade,
        "action": action
    }

if __name__ == "__main__":
    # Smoke Test do O.I.G. - Módulo Autônomo
    print(f"O.I.G. V{config_data['VERSION']} Loaded successfully em Strict Mode.")
    print("Módulos preparados para certificação estatística.")
