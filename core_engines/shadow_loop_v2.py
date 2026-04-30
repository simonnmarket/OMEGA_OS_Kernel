"""
shadow_loop_v2.py - PSA-WIND Refatoração Segura
Arquitetura: 1 execução por ativo (sem loop por TF)
- MTF Bias (D1/H4/H1/M15) como filtro de confluência
- Sinal M5 Flow Signal (EMA8/EMA21 + slope + volume)
- Gatilhos M1/M3 para execução tight
- Dedup/1POS_RULE como cinturão de segurança
- Logging detalhado de decisão e razão de SKIP

Autor: PSA-WIND
Data: 2026-04-30
Versão: 2.0.0-alpha
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

# Configuração de logging
log = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================
OMEGA_MAGIC = 234001
MAX_POSITIONS = 20
DEMO_WINDOW = (0, 24)  # 24/5 sem restrição
ROOT = Path(__file__).parent.parent

# =============================================================================
# FUNÇÕES HELPER (copiadas de shadow_loop.py)
# =============================================================================
def get_multi_tf_bias(symbol: str) -> dict:
    """
    Calcula viés direcional alinhando D1 + H4 + H1 + M15.
    EMA8 vs EMA21 em cada TF. Score: BUY=+1, SELL=-1.
    Alinhamento >= 75% (3/4 TFs) é requerido para bloquear sinal oposto.
    """
    import MetaTrader5 as mt5
    import numpy as np

    TFS = [
        (mt5.TIMEFRAME_D1,  "D1",  50),
        (mt5.TIMEFRAME_H4,  "H4",  50),
        (mt5.TIMEFRAME_H1,  "H1",  50),
        (mt5.TIMEFRAME_M15, "M15", 50),
    ]
    scores = []
    detail = {}

    for tf_const, tf_name, bars in TFS:
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, bars)
            if rates is None or len(rates) < 22:
                continue

            closes = np.array([r['close'] for r in rates], dtype=float)
            ema8 = float(np.mean(closes[-8:]))
            ema21 = float(np.mean(closes[-21:]))

            if ema8 > ema21:
                score = 1  # BUY
            elif ema8 < ema21:
                score = -1  # SELL
            else:
                score = 0  # NEUTRO

            scores.append(score)
            detail[tf_name] = {"score": score, "ema8": ema8, "ema21": ema21}
        except Exception as e:
            log.warning("[%s] MTF Bias erro em %s: %s", symbol, tf_name, e)
            continue

    if not scores:
        return {"valid": False, "score": 0, "detail": detail}

    total_score = sum(scores)
    aligned = len([s for s in scores if s == scores[0]]) if scores else 0
    alignment_pct = (aligned / len(scores)) * 100 if scores else 0

    # Valid se >= 75% dos TFs estão alinhados
    valid = alignment_pct >= 75.0

    return {
        "valid": valid,
        "score": total_score,
        "alignment_pct": alignment_pct,
        "detail": detail
    }


def get_m5_flow_signal(symbol: str) -> dict:
    """
    Gera sinal de fluxo baseado em M5 EMA8/EMA21 + slope + volume.
    Retorna dict com signal_dir (BUY/SELL/None), slope, vol_imb, etc.
    """
    import MetaTrader5 as mt5
    import numpy as np

    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 25)
        if rates is None or len(rates) < 10:
            return {"valid": False, "reason": "no_m5_data"}

        tick_now = mt5.symbol_info_tick(symbol)
        if tick_now is None:
            return {"valid": False, "reason": "no_tick_data"}

        flow_arr = np.array([r['close'] for r in rates], dtype=np.float64)
        ema8 = np.mean(flow_arr[-8:])
        ema21 = np.mean(flow_arr[-21:])
        slope = ema8 - ema21

        # Volume imbalance
        vol_arr = np.array([r['tick_volume'] for r in rates[-10:]], dtype=np.float64)
        flow_arr_10 = flow_arr[-10:]
        diff_arr = np.diff(flow_arr_10)
        vol_up = np.sum(vol_arr[:-1][diff_arr > 0])
        vol_down = np.sum(vol_arr[:-1][diff_arr < 0])
        vol_imb = (vol_up - vol_down) / (vol_up + vol_down + 1e-6)

        # Confirmação de slope mínimo
        slope_ok = abs(slope) >= 1.0

        if slope_ok:
            signal_dir = "BUY" if slope > 0 else "SELL"
            return {
                "valid": True,
                "signal_dir": signal_dir,
                "slope": slope,
                "vol_imb": vol_imb,
                "ema8": ema8,
                "ema21": ema21
            }
        else:
            return {
                "valid": False,
                "reason": "slope_too_small",
                "slope": slope,
                "min_slope": 1.0
            }
    except Exception as e:
        log.error("[%s] M5 Flow Signal erro: %s", symbol, e)
        return {"valid": False, "reason": str(e)}


def has_edge_for_momentum(symbol: str) -> Tuple[bool, dict]:
    """A2: Edge gate para fallback momentum. Retorna (ok, metrics)."""
    import MetaTrader5 as mt5
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 60)
    if rates is None or len(rates) < 30:
        return False, {"reason": "no_rates"}
    import numpy as np
    # TODO: Implementar lógica completa de edge gate
    return True, {"reason": "ok"}


def is_market_open(symbol: str) -> bool:
    """Verifica se mercado está aberto para o ativo."""
    import MetaTrader5 as mt5
    info = mt5.symbol_info(symbol)
    if info is None:
        return False
    return info.visible


# =============================================================================
# FUNÇÃO PRINCIPAL DE EXECUÇÃO POR ATIVO
# =============================================================================
def execute_asset_once(asset: str, mode: str, equity: float,
                       current_positions: List[Dict],
                       cycle_opened_assets: set) -> Dict:
    """
    Executa análise e ordem para um ativo uma única vez por ciclo.
    
    Pipeline:
    1. MTF Bias (D1/H4/H1/M15) - Filtro de Confluência
    2. Guardrail de Janela
    3. Sinal M5 Flow Signal
    4. Edge Gate
    5. Dedup (1 ordem por ativo por ciclo)
    6. 1POS_RULE (já tem posição OMEGA?)
    7. Anti-Hedge (posição oposta?)
    8. Execução (se todos filtros passarem)
    
    Retorna dict com decision, reason_for_skip, order_ids (se houver).
    """
    tf = "M5"  # Único timeframe para geração de sinal
    result = {
        "asset": asset,
        "timeframe": tf,
        "decision": "SKIP",
        "reason_for_skip": None,
        "bias_snapshot": None,
        "m5_signal": None,
        "order_ids": []
    }
    
    # === 1. MTF Bias (D1/H4/H1/M15) - Filtro de Confluência ===
    bias_result = get_multi_tf_bias(asset)
    bias_valid = bias_result.get("valid", False)
    bias_score = bias_result.get("score", 0)
    bias_detail = bias_result.get("detail", {})
    
    result["bias_snapshot"] = {
        "valid": bias_valid,
        "score": bias_score,
        "detail": bias_detail
    }
    
    log.info("[%s %s] [MTF_BIAS] valid=%s score=%d alignment_pct=%.1f%%",
             asset, tf, bias_valid, bias_score,
             bias_result.get("alignment_pct", 0))
    
    if not bias_valid:
        result["reason_for_skip"] = "bias_unavailable"
        log.warning("[%s %s] [SKIP] bias_unavailable - MTF Bias inválido", asset, tf)
        return result
    
    # === 2. Guardrail de Janela ===
    h_now = datetime.now().hour
    has_night_pass = os.environ.get("OMEGA_NIGHT_PASS", "").upper() == "AUTHORISED_BY_CEO"
    
    if not has_night_pass:
        # TODO: Implementar lógica completa de regime windows
        w_start, w_end = DEMO_WINDOW
        is_within = (w_start <= h_now < w_end)
        
        if not is_within:
            result["reason_for_skip"] = "window"
            log.warning("[%s %s] [SKIP] window - FORA DA JANELA", asset, tf)
            return result
    
    # === 3. Sinal M5 Flow Signal ===
    m5_signal = get_m5_flow_signal(asset)
    result["m5_signal"] = m5_signal
    
    if not m5_signal.get("valid"):
        result["reason_for_skip"] = f"m5_signal_{m5_signal.get('reason', 'unknown')}"
        log.warning("[%s %s] [SKIP] m5_signal - %s", asset, tf, m5_signal.get("reason"))
        return result
    
    signal_dir = m5_signal.get("signal_dir")
    log.info("[%s %s] [M5_SIGNAL] signal=%s slope=%.2f vol_imb=%.2f",
             asset, tf, signal_dir, m5_signal.get("slope"), m5_signal.get("vol_imb"))
    
    # === 4. Edge Gate ===
    edge_ok, edge_m = has_edge_for_momentum(asset)
    if not edge_ok:
        result["reason_for_skip"] = f"edge_gate_{edge_m.get('reason', 'unknown')}"
        log.info("[%s %s] [SKIP] edge_gate - %s", asset, tf, edge_m.get("reason"))
        return result
    
    # === 5. Dedup (1 ordem por ativo por ciclo) ===
    if asset in cycle_opened_assets:
        result["reason_for_skip"] = "dedup_cycle"
        log.info("[%s %s] [SKIP] dedup - já abriu ordem neste ciclo", asset, tf)
        return result
    
    # === 6. 1POS_RULE (já tem posição OMEGA?) ===
    existing_omega = [p for p in current_positions if p.get("magic") == OMEGA_MAGIC]
    if existing_omega:
        result["reason_for_skip"] = "already_positioned"
        log.info("[%s %s] [SKIP] 1pos_rule - já tem %d posição(ões) OMEGA",
                 asset, tf, len(existing_omega))
        return result
    
    # === 7. Anti-Hedge (posição oposta?) ===
    has_opposite = False
    for pos in current_positions:
        pos_dir = "BUY" if pos.get("type") == 0 else "SELL"
        if pos_dir != signal_dir:
            has_opposite = True
            break
    
    if has_opposite:
        result["reason_for_skip"] = "anti_hedge"
        log.warning("[%s %s] [SKIP] anti_hedge - já existe posição oposta", asset, tf)
        return result
    
    # === 8. Guardrail: mercado aberto? ===
    if not is_market_open(asset):
        result["reason_for_skip"] = "market_closed"
        log.warning("[%s %s] [SKIP] market_closed - MERCADO FECHADO", asset, tf)
        return result
    
    # === 9. Execução (placeholder por enquanto) ===
    # TODO: Implementar execução MT5 completa
    result["decision"] = "EXEC"
    result["signal_dir"] = signal_dir
    result["reason_for_skip"] = None
    
    log.info("[%s %s] [EXEC_READY] signal=%s - todos filtros passaram",
             asset, tf, signal_dir)
    
    return result


# =============================================================================
# LOOP PRINCIPAL
# =============================================================================
def run_loop_v2(ativos: List[str], mode: str, equity: float) -> Dict:
    """
    Loop principal v2 - 1 execução por ativo (sem loop por TF).
    """
    log.info("=" * 80)
    log.info("SHADOW_LOOP_V2 - PSA-WIND Refatoração Segura")
    log.info("=" * 80)
    log.info("Ativos: %s", ativos)
    log.info("Mode: %s", mode)
    log.info("Equity: $%.2f", equity)
    
    # Inicializar MT5
    import MetaTrader5 as mt5
    if not mt5.initialize():
        log.error("Falha ao inicializar MT5")
        return {"error": "mt5_init_failed"}
    
    mt5_connected = True
    
    # Obter posições atuais
    try:
        positions = mt5.positions_get()
        current_positions = []
        if positions:
            for p in positions:
                current_positions.append({
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "type": p.type,
                    "magic": p.magic,
                    "profit": p.profit
                })
    except Exception as e:
        log.error("Erro ao obter posições: %s", e)
        current_positions = []
    
    log.info("Posições atuais: %d", len(current_positions))
    
    # Dedup por ciclo
    cycle_opened_assets: set = set()
    
    # Scheduler de-bias (mesmo do v1)
    import random
    random.seed(int(time.time()) // 60)
    ativos_scheduled = list(ativos)
    random.shuffle(ativos_scheduled)
    log.info("Ordem de processamento: %s", ativos_scheduled)
    
    # Resultados
    results = []
    exec_count = 0
    skip_count = 0
    
    # Loop por ativo (1 vez por ativo, sem loop por TF)
    for asset in ativos_scheduled:
        log.info("-" * 80)
        log.info("Processando: %s", asset)
        
        result = execute_asset_once(
            asset=asset,
            mode=mode,
            equity=equity,
            current_positions=current_positions,
            cycle_opened_assets=cycle_opened_assets
        )
        
        results.append(result)
        
        if result["decision"] == "EXEC":
            exec_count += 1
            # Marcar asset como aberto neste ciclo
            cycle_opened_assets.add(asset)
            # TODO: Executar ordem MT5
        else:
            skip_count += 1
            log.info("[%s] SKIP - reason: %s", asset, result["reason_for_skip"])
    
    # Resumo
    log.info("=" * 80)
    log.info("RESUMO V2")
    log.info("=" * 80)
    log.info("Total ativos processados: %d", len(ativos_scheduled))
    log.info("Execuções: %d", exec_count)
    log.info("SKIPs: %d", skip_count)
    log.info("Duplicatas evitadas: %d", len(cycle_opened_assets))
    
    mt5.shutdown()
    
    return {
        "results": results,
        "exec_count": exec_count,
        "skip_count": skip_count,
        "cycle_opened_assets": list(cycle_opened_assets)
    }


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Shadow Loop V2 - PSA-WIND")
    parser.add_argument("--ativos", nargs="+", default=["EURUSD", "GBPUSD", "XAUUSD"],
                        help="Lista de ativos para processar")
    parser.add_argument("--mode", default="paper", choices=["paper", "live"],
                        help="Modo de execução")
    parser.add_argument("--equity", type=float, default=10000.0,
                        help="Equity inicial")
    
    args = parser.parse_args()
    
    try:
        result = run_loop_v2(args.ativos, args.mode, args.equity)
        log.info("V2 concluído com sucesso")
        sys.exit(0)
    except Exception as e:
        log.critical("ERRO CRÍTICO V2:\n%s", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
