#!/usr/bin/env python3
"""
OMEGA SHADOW / PAPER LOOP ENGINE v3.0 — MT5 REAL INTEGRADO
nebular-kuiper\core_engines\shadow_loop.py

SHADOW : gera sinais, loga, NÃO envia ordens (zero risco).
PAPER  : envia ordens reais para conta DEMO via MetaTrader5 API.
         Kill switch: DD diário ≥ 5% OU 3 retcodes de falha consecutivos.

Retcodes MT5 monitorados:
  10009 TRADE_RETCODE_DONE     ← sucesso
  10004 TRADE_RETCODE_REQUOTE  ← re-quote (slippage)
  10006 TRADE_RETCODE_REJECT   ← rejeitado pelo broker
  10007 TRADE_RETCODE_CANCEL   ← cancelado pelo cliente
  10010 TRADE_RETCODE_PLACED   ← ordem colocada
  10013 TRADE_RETCODE_INVALID  ← parâmetros inválidos
  10016 TRADE_RETCODE_INVALID_STOPS ← SL/TP inválidos
  10019 TRADE_RETCODE_NO_MONEY ← fundos insuficientes
  10030 TRADE_RETCODE_LIMIT_ORDERS ← limite de ordens atingido

Uso:
  python shadow_loop.py --mode shadow --ativos XAUUSD GBPUSD --timeframes H1 H4
  python shadow_loop.py --mode paper  --ativos XAUUSD GBPUSD USDJPY AUDUSD AUDJPY \
                                               ETHUSD US500 SOLUSD DOGUSD \
                                       --timeframes H1 H4 --equity 10000
"""

import argparse
import hashlib
import json
import logging
import sys


import time
import traceback
from core_engines.integration_gate import OmegaIntegrationGate
from modules.risk.scale_manager import OmegaScaleManager
from modules.validation.mfa_engine import OmegaMFAEngine

from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

AGENT_IA_PATH = Path(__file__).parent.parent / "agent_ia"
if AGENT_IA_PATH.exists():
    sys.path.insert(0, str(AGENT_IA_PATH))

USE_AGENT_IA = os.getenv("OMEGA_USE_AGENT_IA", "0").strip() == "1"  # Habilitar: OMEGA_USE_AGENT_IA=1
if USE_AGENT_IA:
    try:
        from agent_ia.core.omega_strategy_catalog import StrategyCatalog
        from agent_ia.core.omega_agent_ecosystem import AgentEcosystem
        from agent_ia.core.omega_quantum_brain import OmegaQuantumBrain
        # Fase 4 — integração oficial (não duplicar classe; importar)
        from agent_ia.integration.shadow_loop_integration import OmegaAgentIntegration
        AGENT_IA_AVAILABLE = True
    except ImportError:
        AGENT_IA_AVAILABLE = False
        print("[AVISO] Agent IA modules não disponíveis — fallback para lógica padrão")
else:
    AGENT_IA_AVAILABLE = False

from modules.detection import SpoofIcebergDetector
from modules.portfolio import CorrelationFilter
from core_engines.intra_candle_executor import IntraCandleExecutor

# ─── OMEGA REGIME INJECTION (CQO MOD #5 - THREAD SAFE) ──────────────
import os
import json
import threading
from enum import Enum

class ExecutionRegime(Enum):
    TRADICIONAL = "TRADICIONAL"
    HUNTER = "HUNTER"

_regime_local = threading.local()
def get_regime_config():
    if not hasattr(_regime_local, 'config'):
        _regime_env = os.getenv("OMEGA_REGIME", "TRADICIONAL")
        regime = ExecutionRegime(_regime_env)
        MAX_LOT = 0.01; MIN_CONFIDENCE = 0.65; CAPITAL_ALLOCATION = 0.01; REGIME_CONFIG = None
        if regime == ExecutionRegime.HUNTER:
            CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "regimes" / "hunter.json"
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f: REGIME_CONFIG = json.load(f)
                MAX_LOT = REGIME_CONFIG['parametros_execucao']['lote_maximo']
                MIN_CONFIDENCE = REGIME_CONFIG['parametros_execucao']['confianca_minima']
                CAPITAL_ALLOCATION = REGIME_CONFIG['parametros_execucao']['capital_alocado_pct']
        _regime_local.config = {'regime': regime, 'MAX_LOT': MAX_LOT, 'MIN_CONFIDENCE': MIN_CONFIDENCE, 'CAPITAL_ALLOCATION': CAPITAL_ALLOCATION, 'REGIME_CONFIG': REGIME_CONFIG}
    return _regime_local.config

def get_max_lot() -> float: return get_regime_config()['MAX_LOT']
# ────────────────────────────────────────────────────────────────────────────

# ─── Caminhos ───────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent
CORE        = Path(__file__).resolve().parent
OHLCV       = Path(os.getenv("OMEGA_OHLCV_PATH", str(ROOT / "data" / "ohlcv"))).resolve()
AUDIT_PAPER = ROOT / "audit" / "paper"
AUDIT_PAPER.mkdir(parents=True, exist_ok=True)

# ─── Configuração de Risco ───────────────────────────────────────────────────
DEMO_EQUITY_USD    = 10_000.0
RISK_PER_TRADE_PCT = 0.0025     # 0,25% por trade
MAX_POSITIONS      = 6          # V10: 3 ativos × 2 TFs stress
DD_DAILY_MAX       = 0.05       # 5% kill switch
MAX_CONSEC_FAIL    = 3
OMEGA_MAGIC        = 234001     # ID do EA OMEGA

# ─── Guardrails ─────────────────────────────────────────────────────────────
TIER1_ASSETS = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "XAUUSD", "XAGUSD", "US500", "NAS100", "GER40", "BTCUSD", "ETHUSD"} # Whitelist restrita para DEMO
HIT_RATE_MIN = 80.0
MACH_MAX     = 1.5
DEMO_WINDOW  = (0, 24) # V9: 24/5 intencional (CQO/CTO liberaram). NIGHT_PASS ou HUNTER override em run_loop.
MAX_LOT_DEMO = 0.01

# ─── Retcodes MT5 ────────────────────────────────────────────────────────────
RETCODE_OK   = {10009, 10010}   # DONE, PLACED
RETCODE_WARN = {10004}          # REQUOTE — logar mas não falhar
RETCODE_FAIL = {10006, 10007, 10013, 10016, 10018, 10019, 10030}

RETCODE_DESC = {
    10004: "REQUOTE",       10006: "REJECT",
    10007: "CANCEL",        10009: "DONE",
    10010: "PLACED",        10013: "INVALID_REQUEST",
    10016: "INVALID_STOPS", 10018: "NO_MONEY",
    10019: "NO_CHANGES",    10030: "LIMIT_ORDERS",
    10014: "TOO_MANY_REQ",
}

# ─── Logging ─────────────────────────────────────────────────────────────────
ts_str   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
log_file = AUDIT_PAPER / f"paper_loop_{ts_str}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("PAPER")


# ─── SHA3-256 ────────────────────────────────────────────────────────────────
def sha3(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


# ─── Wilson IC ────────────────────────────────────────────────────────────────
def wilson_ic(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0: return 0.0, 1.0
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    m = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return max(0.0, c - m), min(1.0, c + m)


# ─── Margens Dinâmicas ───────────────────────────────────────────────────────
def load_dynamic_margins() -> dict:
    p = ROOT / "audit" / "dynamic_margins.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("margins", {})
    return {}


# ─── A2: EDGE GATE (ATR + spread + ADX) ────────────────────────────────────
# Bloqueia fallback momentum em mercado lateral / spread caro.
# Aprovado por CEO+CKO+COO+CTO+CQO+CIO+TECH-LEAD em 2026-04-27.
# Fundamento: trade só tem edge se ATR ≫ spread E há tendência (ADX ≥ thr).

EDGE_MIN_ATR_PCT      = float(os.getenv("OMEGA_EDGE_MIN_ATR_PCT", "0.0015"))   # 0.15% do preço
EDGE_MIN_ATR_OVER_SPR = float(os.getenv("OMEGA_EDGE_MIN_ATR_OVER_SPR", "5.0")) # ATR ≥ 5× spread
EDGE_MIN_ADX          = float(os.getenv("OMEGA_EDGE_MIN_ADX", "20.0"))         # ADX ≥ 20

def _atr_simple(highs, lows, closes, n: int = 14) -> float:
    import numpy as np
    if len(closes) < n + 1:
        return 0.0
    tr = np.maximum.reduce([
        highs[1:] - lows[1:],
        np.abs(highs[1:] - closes[:-1]),
        np.abs(lows[1:]  - closes[:-1]),
    ])
    return float(np.mean(tr[-n:]))

def _adx_simple(highs, lows, closes, n: int = 14) -> float:
    import numpy as np
    if len(closes) < n + 2:
        return 0.0
    up   = highs[1:] - highs[:-1]
    down = lows[:-1] - lows[1:]
    plus_dm  = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = np.maximum.reduce([
        highs[1:] - lows[1:],
        np.abs(highs[1:] - closes[:-1]),
        np.abs(lows[1:]  - closes[:-1]),
    ])
    atr_ = np.convolve(tr, np.ones(n)/n, mode='valid')
    if len(atr_) == 0 or atr_[-1] == 0:
        return 0.0
    plus_di  = 100 * np.convolve(plus_dm,  np.ones(n)/n, mode='valid')[-len(atr_):] / atr_
    minus_di = 100 * np.convolve(minus_dm, np.ones(n)/n, mode='valid')[-len(atr_):] / atr_
    dx = 100 * np.abs(plus_di - minus_di) / np.maximum(plus_di + minus_di, 1e-9)
    if len(dx) < n:
        return float(np.mean(dx)) if len(dx) > 0 else 0.0
    return float(np.mean(dx[-n:]))

def has_edge_for_momentum(symbol: str) -> Tuple[bool, dict]:
    """A2: Edge gate para fallback momentum. Retorna (ok, metrics)."""
    import MetaTrader5 as mt5
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 60)
    if rates is None or len(rates) < 30:
        return False, {"reason": "no_rates"}
    import numpy as np
    highs  = np.array([r['high']  for r in rates], dtype=float)
    lows   = np.array([r['low']   for r in rates], dtype=float)
    closes = np.array([r['close'] for r in rates], dtype=float)

    tick = mt5.symbol_info_tick(symbol)
    sym  = mt5.symbol_info(symbol)
    if not tick or not sym:
        return False, {"reason": "no_tick"}
    spread_abs = (tick.ask - tick.bid)
    price = float(closes[-1]) or 1.0
    atr   = _atr_simple(highs, lows, closes, 14)
    adx   = _adx_simple(highs, lows, closes, 14)
    atr_pct       = atr / price if price > 0 else 0.0
    atr_over_spr  = (atr / spread_abs) if spread_abs > 0 else 0.0

    metrics = {
        "atr": round(atr, 6),
        "atr_pct": round(atr_pct, 6),
        "spread": round(spread_abs, 6),
        "atr_over_spread": round(atr_over_spr, 3),
        "adx": round(adx, 2),
        "thr_atr_pct": EDGE_MIN_ATR_PCT,
        "thr_atr_over_spr": EDGE_MIN_ATR_OVER_SPR,
        "thr_adx": EDGE_MIN_ADX,
    }
    ok = (atr_pct >= EDGE_MIN_ATR_PCT
          and atr_over_spr >= EDGE_MIN_ATR_OVER_SPR
          and adx >= EDGE_MIN_ADX)
    metrics["ok"] = ok
    if not ok:
        reasons = []
        if atr_pct < EDGE_MIN_ATR_PCT: reasons.append(f"atr_pct<{EDGE_MIN_ATR_PCT}")
        if atr_over_spr < EDGE_MIN_ATR_OVER_SPR: reasons.append(f"atr/spr<{EDGE_MIN_ATR_OVER_SPR}")
        if adx < EDGE_MIN_ADX: reasons.append(f"adx<{EDGE_MIN_ADX}")
        metrics["reason"] = "|".join(reasons)
    return ok, metrics


# ─── MT5 — Inicialização e Shutdown ─────────────────────────────────────────
def mt5_init() -> bool:
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            log.error("MT5 initialize() falhou: %s", mt5.last_error())
            return False
        info = mt5.terminal_info()
        log.info("MT5 conectado | build=%s | trade_allowed=%s | connected=%s",
                 info.build if info else "?",
                 info.trade_allowed if info else "?",
                 info.connected if info else "?")
        return True
    except ImportError:
        log.error("MetaTrader5 package não instalado. Execute: pip install MetaTrader5")
        return False


def mt5_shutdown():
    try:
        import MetaTrader5 as mt5
        mt5.shutdown()
    except Exception:
        pass


# ─── MT5 — Verificar Requisição Antes de Enviar (OrderCheck) ────────────────
def mt5_check_order(request: dict) -> Optional[dict]:
    import MetaTrader5 as mt5
    result = mt5.order_check(request)
    if result is None:
        log.warning("order_check retornou None: %s", mt5.last_error())
        return None
    r = result._asdict()
    if r["retcode"] != 0:
        log.warning("order_check FAIL retcode=%d comment=%s", r["retcode"], r.get("comment"))
    else:
        log.info("order_check OK | margin=%.2f balance=%.2f equity=%.2f free_margin=%.2f",
                 r.get("margin", 0), r.get("balance", 0),
                 r.get("equity", 0), r.get("margin_free", 0))
    return r


# ─── Guardrail de Mercado Aberto ──────────────────────────────────────────────
def is_market_open(symbol: str = "XAUUSD") -> bool:
    """Verifica se mercado está aberto via MT5 (trade_mode FULL + tick disponível).
    Reutiliza sessão MT5 existente (run_loop já fez mt5.initialize())."""
    import MetaTrader5 as mt5
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        return False
    tick = mt5.symbol_info_tick(symbol)
    return (
        symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
        and symbol_info.session_deals is not None
        and tick is not None
    )


# ─── MT5 — Enviar Ordem Real (Demo) ─────────────────────────────────────────
def mt5_send_order(asset: str, tf: str, lot: float,
                   sl_pts: float, tp_pts: float, direction: str = "BUY") -> Dict:
    """
    Envia ordem de execução a mercado via mt5.order_send().
    Usa TRADE_ACTION_DEAL + ORDER_TYPE (BUY/SELL) Dinâmico!
    Retorna dict com retcode, deal, price, slippage, latência.
    """
    import MetaTrader5 as mt5

    tick = mt5.symbol_info_tick(asset)
    sym  = mt5.symbol_info(asset)
    if tick is None or sym is None:
        log.error("[%s] symbol_info_tick falhou", asset)
        return {"retcode": -1, "retcode_str": "NO_TICK", "error": "symbol_info_tick returned None"}

    price    = tick.ask if direction == "BUY" else tick.bid
    point    = sym.point
    digits   = sym.digits
    min_dist = max(getattr(sym, 'trade_stops_level', 0), getattr(sym, 'spread', 0) * 2)
    final_sl_pts = max(sl_pts, min_dist + 50)  # Safe buffer
    final_tp_pts = max(tp_pts, min_dist + 50)
    
    if direction == "BUY":
        sl_price = round(price - final_sl_pts * point, digits)
        tp_price = round(price + final_tp_pts * point, digits)
        order_type_mt5 = mt5.ORDER_TYPE_BUY
    else:
        sl_price = round(price + final_sl_pts * point, digits)
        tp_price = round(price - final_tp_pts * point, digits)
        order_type_mt5 = mt5.ORDER_TYPE_SELL

    # Selecionar filling mode suportado pelo broker (bit 0=FOK, bit 1=IOC, bit 2=RETURN)
    fm = sym.filling_mode if sym else 3
    if fm & 2:    filling = mt5.ORDER_FILLING_IOC     # IOC — preferido para demo
    elif fm & 1:  filling = mt5.ORDER_FILLING_FOK     # FOK — alternativa
    else:         filling = mt5.ORDER_FILLING_RETURN  # RETURN — fallback

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       asset,
        "volume":       lot,
        "type":         order_type_mt5,
        "price":        price,
        "sl":           sl_price,
        "tp":           tp_price,
        "deviation":    20,
        "magic":        OMEGA_MAGIC,
        "comment":      f"OMEGA-AMI-{tf}-{direction}",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": filling,
    }
    log.info("[%s %s] filling_mode=%d → tipo=%s", asset, tf, fm,
             {mt5.ORDER_FILLING_IOC: "IOC", mt5.ORDER_FILLING_FOK: "FOK",
              mt5.ORDER_FILLING_RETURN: "RETURN"}.get(filling, str(filling)))

    # Pre-check
    check = mt5_check_order(request)
    if check and check.get("retcode", 0) not in (0, 10009):
        log.warning("[%s %s] order_check retcode=%d — enviando mesmo assim (demo)",
                    asset, tf, check.get("retcode", -1))

    t0     = time.perf_counter()
    result = mt5.order_send(request)
    lat_ms = round((time.perf_counter() - t0) * 1000, 1)

    if result is None:
        err = mt5.last_error()
        log.error("[%s %s] order_send retornou None: %s", asset, tf, err)
        return {"retcode": -1, "retcode_str": "NULL_RESULT", "error": str(err),
                "latency_ms": lat_ms}

    r = result._asdict()
    retcode     = r.get("retcode", -1)
    retcode_str = RETCODE_DESC.get(retcode, f"UNKNOWN_{retcode}")
    slippage    = round(abs(r.get("price", price) - price) / point, 2)

    out = {
        "retcode":          retcode,
        "retcode_str":      retcode_str,
        "success":          retcode in RETCODE_OK,
        "deal":             r.get("deal", 0),
        "order":            r.get("order", 0),
        "fill_price":       r.get("price", price),
        "ask_at_send":      price,
        "sl_price":         sl_price,
        "tp_price":         tp_price,
        "volume_confirmed": r.get("volume", lot),
        "slippage_pts":     slippage,
        "comment":          r.get("comment", ""),
        "request_id":       r.get("request_id", 0),
        "latency_ms":       lat_ms,
        "mode":             "MT5_DEMO_REAL",
    }

    if out["success"]:
        log.info("[%s %s] ✅ ORDER DONE | deal=%d price=%.5f slip=%.2fpts lat=%dms",
                 asset, tf, out["deal"], out["fill_price"], out["slippage_pts"], lat_ms)
    elif retcode in RETCODE_WARN:
        log.warning("[%s %s] ⚠️ REQUOTE | bid=%.5f ask=%.5f", asset, tf,
                    r.get("bid", 0), r.get("ask", 0))
    else:
        log.error("[%s %s] ❌ ORDER FAIL | retcode=%d (%s) | %s",
                  asset, tf, retcode, retcode_str, out["comment"])

    return out


# ─── Rodar Motor Harmônico ────────────────────────────────────────────────────
def run_harmonic(asset: str, tf: str, margin: float, out_dir: Path) -> Optional[dict]:
    import subprocess
    out_dir.mkdir(parents=True, exist_ok=True)
    motor = CORE / "omega_harmonic_engine_v3.py"
    cmd   = [sys.executable, str(motor),
             "--symbol", asset, "--timeframe", tf,
             "--base_path", str(OHLCV),
             "--margin", str(margin),
             "--lookback", "3", "--lookahead", "5"]
    try:
        t0 = time.perf_counter()
        r  = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=str(out_dir), timeout=300)
        lat = time.perf_counter() - t0
        if r.returncode != 0:
            log.error("[%s %s] Motor V3 exit %d: %s", asset, tf, r.returncode, r.stderr[:200])
            return None
        jf = out_dir / f"harmonic_events_{asset}_{tf}.json"
        if not jf.exists():
            return None
        with open(jf, encoding="utf-8") as f:
            data = json.load(f)
        data["_latency_s"] = round(lat, 3)
        return data
    except Exception as e:
        log.error("[%s %s] Exceção motor: %s", asset, tf, e)
        return None


# ─── Price Engine ────────────────────────────────────────────────────────────
def get_price_result(asset: str = "XAUUSD", current_price: float = 0.0) -> dict:
    sys.path.insert(0, str(CORE))
    from omega_module_v553 import DCECalibratedPriceEngine, ModuleConfig
    cfg = ModuleConfig()
    cfg.symbol = asset
    if current_price > 0:
        cfg.calibrated_params.P0 = current_price
    
    engine = DCECalibratedPriceEngine(cfg)
    return engine.compute_price(Q=1000, PBoc=0.0, volume_anomaly=0.1)


# ─── Guardrail Check ─────────────────────────────────────────────────────────
def check_guardrails(asset: str, tf: str, hr: float,
                     mach: float, dm: dict) -> dict:
    reasons = []
    dyn_min_hr = get_regime_config().get('MIN_CONFIDENCE', 0.8) * 100
    if hr < dyn_min_hr:    reasons.append(f"hit_rate_134={hr:.2f}% < {dyn_min_hr}%")
    if mach > MACH_MAX:      reasons.append(f"Mach={mach:.2f} > {MACH_MAX}")
    margin = 150.0
    d = dm.get(asset, {}).get(tf)
    if d and isinstance(d, dict): margin = float(d.get("margin_dynamic", 150.0))
    tier   = "T1" if asset in TIER1_ASSETS else ("T2" if hr >= HIT_RATE_MIN else "T3")
    return {"asset": asset, "timeframe": tf, "tier": tier,
            "hit_rate_134": hr, "mach": mach, "margin_used": margin,
            "skip": len(reasons) > 0, "skip_reasons": reasons}


# ─── Position Sizing (MT5 contract-aware) ─────────────────────────────────────
def calc_lot(equity: float, margin_pts: float, asset: str) -> Dict:
    """
    Calcula lote com base no contrato real do MT5.
    Risco máximo: equity × 0.25%
    Stop: 2 × margin_pts
    Lote mínimo: 0.01
    """
    import MetaTrader5 as mt5
    sym  = mt5.symbol_info(asset)
    tick = mt5.symbol_info_tick(asset)

    if sym is None or tick is None:
        return {"lot": 0.01, "risk_usd": equity * RISK_PER_TRADE_PCT,
                "stop_pts": margin_pts * 2, "error": "symbol_info_none"}

    price         = tick.ask
    point         = sym.point
    contract_size = sym.trade_contract_size   # ex: 100 (GBPUSD), 100 (XAUUSD)
    digit         = sym.digits

    # Valor de 1 pip = point × contract_size × price_in_USD_per_unit
    # Para forex simples: pip_value = point × contract_size
    # Para XAUUSD: pip_value = point × contract_size (em USD já)
    pip_value_per_lot = point * contract_size

    risk_usd = equity * RISK_PER_TRADE_PCT
    stop_pts = 2.0 * margin_pts
    lot_raw  = risk_usd / max(stop_pts * pip_value_per_lot, 0.0001)
    min_lot  = sym.volume_min if hasattr(sym, 'volume_min') else 0.01
    lot      = max(min_lot, round(lot_raw, 2))
    guardrail_max = max(get_max_lot(), min_lot)
    lot      = min(lot, guardrail_max) # Guardrail Demo / Hunter Dinâmico Centralizado

    return {
        "lot":            lot,
        "risk_usd":       round(risk_usd, 2),
        "stop_pts":       stop_pts,
        "pip_value_lot":  round(pip_value_per_lot, 6),
        "contract_size":  contract_size,
        "price_at_calc":  price,
    }



# ─── Build AnalysisReport ───────────────────────────────────────────────────
def build_report(asset, tf, mode, harmonic, price_data, guard, exec_result, lot_info) -> dict:
    now  = datetime.now(timezone.utc).isoformat()
    m    = harmonic.get("engines", {}).get("harmonic", {}).get("metrics", {})
    s134 = m.get("134_stats", {}); s34 = m.get("34_stats", {})
    k, n = s134.get("hits", 0), s134.get("total_touches", 1)
    lb, ub = wilson_ic(k, n)
    report = {
        "mission_id":        f"PAPER-{asset}-{tf}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "asset": asset, "timeframe": tf, "status": "COMPLETED",
        "mode": mode, "created_at": now, "agent_version": "shadow_loop_v3.0",
        "omega_integration": True, "guardrail": guard,
        "binomial_ic_95": {
            "hits": k, "total": n,
            "p_hat": round(k / max(n, 1), 6),
            "lower_bound": round(lb, 6), "upper_bound": round(ub, 6),
            "interval": f"[{lb*100:.4f}%, {ub*100:.4f}%]",
        },
        "engines": {
            "harmonic": {"metrics": {"34_stats": s34, "134_stats": s134}},
            "price": {
                "price":   price_data.get("price"),
                "base_price": price_data.get("base_price"),
                "flash_crash_adjustment": price_data.get("flash_crash_adjustment"),
                "metadata": {k2: v2 for k2, v2 in price_data.get("metadata", {}).items()
                             if k2 in ["params_checksum", "rmse_expected", "r_squared"]},
            },
        },
        "signal": {
            "action":       "SKIP" if guard["skip"] else ("MT5_PAPER_EXECUTE" if mode == "paper" else "MONITOR"),
            "skip_reasons": guard["skip_reasons"],
            "margin_used":  guard["margin_used"],
            "tier":         guard["tier"],
        },
        "execution": exec_result,
        "lot_info":  lot_info,
        "latency_motor_s": harmonic.get("_latency_s"),
    }
    jb = json.dumps(report, indent=2).encode("utf-8")
    report["checksum"] = sha3(jb)
    return report


# ─── Kill Switch ─────────────────────────────────────────────────────────────
class KillSwitch:
    def __init__(self, equity: float):
        self.equity = equity; self.daily_pnl = 0.0
        self.consec_fail = 0; self.triggered = False; self.reason = ""
    def update(self, success: bool, pnl_usd: float = 0.0) -> bool:
        if self.triggered: return True
        self.daily_pnl += pnl_usd
        if not success: self.consec_fail += 1
        else:           self.consec_fail = 0
        if abs(self.daily_pnl) / self.equity >= DD_DAILY_MAX:
            self.reason = f"DD diário {abs(self.daily_pnl)/self.equity*100:.2f}% ≥ {DD_DAILY_MAX*100:.0f}%"
            self.triggered = True; log.critical("💀 KILL SWITCH: %s", self.reason)
        if self.consec_fail >= MAX_CONSEC_FAIL:
            self.reason = f"{self.consec_fail} falhas consecutivas"
            self.triggered = True; log.critical("💀 KILL SWITCH: %s", self.reason)
        return self.triggered


# ─── Online Statistics ────────────────────────────────────────────────────────
class OnlineStats:
    def __init__(self):
        self.signals = 0; self.executed = 0; self.skipped = 0
        self.pnl = 0.0; self.slippage = []; self.latencies = []; self.hrs = []
    def record(self, report: dict):
        self.signals += 1
        action = report["signal"]["action"]
        if "SKIP" in action: self.skipped += 1; return
        self.executed += 1
        hr = report["engines"]["harmonic"]["metrics"]["134_stats"].get("hit_rate", 0)
        self.hrs.append(hr)
        ex = report.get("execution") or {}
        self.slippage.append(ex.get("slippage_pts", 0))
        self.latencies.append(ex.get("latency_ms", 0))
    def summary(self) -> dict:
        n = max(len(self.hrs), 1)
        return {
            "total_signals":    self.signals,
            "executed":         self.executed,
            "skipped":          self.skipped,
            "avg_hit_rate_134": round(sum(self.hrs) / n, 4) if self.hrs else 0,
            "avg_slippage_pts": round(sum(self.slippage) / max(len(self.slippage), 1), 3),
            "avg_latency_ms":   round(sum(self.latencies) / max(len(self.latencies), 1), 1),
            "max_latency_ms":   round(max(self.latencies, default=0), 1),
        }


# ─── Loop Principal ───────────────────────────────────────────────────────────
def run_loop(ativos: List[str], timeframes: List[str], mode: str, equity: float):
    import MetaTrader5 as mt5
    log.info("=" * 72)
    log.info("OMEGA %s LOOP v3.0 | %d ativos × %d TFs | equity=USD %.2f",
             mode.upper(), len(ativos), len(timeframes), equity)
    log.info("Risk/trade=%.2f%% | MaxPos=%d | DD_max=%.0f%% | MT5_MAGIC=%d",
             RISK_PER_TRADE_PCT * 100, MAX_POSITIONS, DD_DAILY_MAX * 100, OMEGA_MAGIC)
    log.info("=" * 72)

    mt5_connected = False
    if mode == "paper":
        mt5_connected = mt5_init()
        if not mt5_connected:
            log.critical("MT5 não disponível. Abortando modo paper.")
            return {"error": "MT5 não conectado", "kill_switch": True}

    dm       = load_dynamic_margins()
    ks       = KillSwitch(equity)
    stats    = OnlineStats()
    
    # Sincronização de Estado Real com o MT5 (PSA FIX - State Awareness)
    if mode == "paper" and mt5_connected:
        real_pos = mt5.positions_get(magic=OMEGA_MAGIC)
        open_pos = len(real_pos) if real_pos else 0
        log.info("MT5 State Sync: %d posicoes ativas detectadas.", open_pos)
    else:
        open_pos = 0
    
    skip_tbl = []
    results  = []

    intra_executor = IntraCandleExecutor(symbols=list(TIER1_ASSETS))
    spoof_detector = SpoofIcebergDetector()
    correlation_filter = CorrelationFilter()

    # Fase 4 — inicialização do Agente IA (somente se flag e imports OK)
    agent_ia = None
    _processed_tickets: set = set()
    if USE_AGENT_IA and AGENT_IA_AVAILABLE:
        try:
            agent_ia = OmegaAgentIntegration(
                assets=list(ativos),
                total_capital=float(equity),
                enable_agent_ia=True,
            )
            log.info("[FASE4] Agente IA inicializado (assets=%d, capital=$%.2f)", len(ativos), equity)
        except Exception as _ia_init_err:
            log.error("[FASE4] Falha ao inicializar Agente IA: %s — fallback momentum", _ia_init_err)
            agent_ia = None

    # FIX #5 — Scheduler de-bias: embaralha a ordem dos ativos a cada ciclo
    # com seed determinística por minuto (auditável). Quando MAX_POSITIONS
    # limita slots, a lista determinística fazia com que apenas o primeiro
    # ativo (BTCUSD) recebesse 100% das ordens. Shuffle quebra esse viés.
    import random as _rnd_fix5
    _rnd_fix5.seed(int(time.time()) // 60)
    ativos_scheduled = list(ativos)
    _rnd_fix5.shuffle(ativos_scheduled)
    log.info("[FIX5] Scheduler de-bias aplicado | ordem=%s", ativos_scheduled)

    try:
        for asset in ativos_scheduled:
            for tf in timeframes:
                # Guardrail de Janela — V9: 24/5 liberado (CQO/CTO)
                import os
                h_now = datetime.now().hour
                has_night_pass = os.environ.get("OMEGA_NIGHT_PASS", "").upper() == "AUTHORISED_BY_CEO"

                regime_cfg = get_regime_config()
                is_within = False

                if has_night_pass:
                    is_within = True  # V9: override total — 24/5
                elif regime_cfg['regime'] == ExecutionRegime.HUNTER and regime_cfg['REGIME_CONFIG']:
                    j_asia = regime_cfg['REGIME_CONFIG']['janelas_operacao']['asia']
                    j_ny = regime_cfg['REGIME_CONFIG']['janelas_operacao']['pos_ny']
                    asia_start = int(j_asia['inicio'].split(':')[0]); asia_end = int(j_asia['fim'].split(':')[0])
                    ny_start = int(j_ny['inicio'].split(':')[0]); ny_end = int(j_ny['fim'].split(':')[0])
                    is_within = (asia_start <= h_now < asia_end) or (ny_start <= h_now < ny_end)
                else:
                    w_start, w_end = DEMO_WINDOW  # V9: (0,24) — sem restrição
                    is_within = (w_start <= h_now < w_end)

                if not is_within:
                    log.warning("[%s %s] FORA DA JANELA DO REGIME %s. Agora: %02d:00", 
                                asset, tf, regime_cfg['regime'].value, h_now)
                    results.append({"asset": asset, "timeframe": tf, "status": "SKIP_WINDOW"})
                    continue

                if has_night_pass:
                    log.info("[%s %s] 🛡️ NIGHT_PASS ATIVO — operação 24/5 autorizada pelo CEO", asset, tf)

                if ks.triggered:
                    log.critical("[%s %s] KS ativo — abortando.", asset, tf); break

                log.info("[%s %s] ── Ciclo ──", asset, tf)

                # Guardrail pré-motor
                prev_hr = 100.0
                rep_f = ROOT / "audit" / f"{asset}_{tf}" / f"AnalysisReport_{asset}_{tf}.json"
                if rep_f.exists():
                    try:
                        with open(rep_f, encoding="utf-8") as f2:
                            prev = json.load(f2)
                        prev_hr = (prev.get("engines", {}).get("harmonic", {})
                                   .get("metrics", {}).get("134_stats", {})
                                   .get("hit_rate", 100.0))
                    except Exception: pass

                guard = check_guardrails(asset, tf, prev_hr, 1.0, dm)
                if guard["skip"]:
                    log.warning("[%s %s] SKIP (pre) — %s", asset, tf, guard["skip_reasons"])
                    skip_tbl.append(guard)
                    dummy = {"asset": asset, "timeframe": tf, "status": "SKIP",
                             "signal": {"action": "SKIP",
                                        "skip_reasons": guard["skip_reasons"],
                                        "tier": guard["tier"],
                                        "margin_used": guard["margin_used"]},
                             "engines": {"harmonic": {"metrics": {"134_stats": {}}},
                                         "price": {}},
                             "execution": None, "lot_info": None, "binomial_ic_95": {}}
                    stats.record(dummy); ks.update(True)
                    results.append({"asset": asset, "timeframe": tf, "status": "SKIP",
                                    "reasons": guard["skip_reasons"]}); continue

                if mode == "paper" and open_pos >= MAX_POSITIONS:
                    log.warning("[%s %s] MAX_POSITIONS=%d atingido.", asset, tf, MAX_POSITIONS); continue

                # Motor Harmônico V3
                out_dir  = AUDIT_PAPER / f"{asset}_{tf}"
                harmonic = run_harmonic(asset, tf, guard["margin_used"], out_dir)
                if harmonic is None:
                    ks.update(False)
                    results.append({"asset": asset, "timeframe": tf, "status": "FAIL"}); continue

                # Guardrail final
                s134    = (harmonic.get("engines", {}).get("harmonic", {})
                           .get("metrics", {}).get("134_stats", {}))
                hr_real = s134.get("hit_rate", 0.0)
                guard   = check_guardrails(asset, tf, hr_real, 1.0, dm)

                # Execução e Preços (PSA FIX - Zero Initialization)
                lot_info = exec_result = None
                a_price = b_price = 0.0

                if not guard["skip"] and mode == "paper" and mt5_connected:
                    # Guardrail: mercado aberto?
                    if not is_market_open(asset):
                        log.warning("[%s %s] MERCADO FECHADO — skip (reenqueue na próxima iteração)", asset, tf)
                        results.append({"asset": asset, "timeframe": tf, "status": "SKIP_MARKET_CLOSED"})
                        continue

                    lot_info = calc_lot(equity, guard["margin_used"], asset)

                    # === FASE 4 — Decisão IA (com fallback momentum MT5) ===
                    signal_dir = None
                    signal_source = "MOMENTUM_MT5"
                    ia_signal = None
                    ia_lot_override = None
                    ia_sl_pts = None
                    ia_tp_pts = None
                    ia_agent_id = "AGENT_IA"

                    if USE_AGENT_IA and AGENT_IA_AVAILABLE and agent_ia is not None:
                        sig_scores = {}
                        try:
                            if spoof_detector and hasattr(spoof_detector, "get_signature_scores"):
                                sig_scores = spoof_detector.get_signature_scores() or {}
                        except Exception as e:
                            log.warning("[%s %s] spoof_detector falhou: %s", asset, tf, e)
                        try:
                            # FIX #6 — Latency split: medimos só a decisão IA (CPU pura),
                            # excluindo o roundtrip MT5/broker (medido em latency_ms).
                            _t_dec_0 = time.perf_counter()
                            ia_signal = agent_ia.get_signal(asset, signature_scores=sig_scores or {})
                            _ai_decision_ms = round((time.perf_counter() - _t_dec_0) * 1000, 2)
                            log.info("[%s %s] FIX6 ai_decision_ms=%.2f", asset, tf, _ai_decision_ms)
                            if isinstance(ia_signal, dict):
                                ia_signal['_ai_decision_ms'] = _ai_decision_ms
                            required_keys = ['action', 'direction', 'confidence']
                            if not all(k in ia_signal for k in required_keys):
                                raise ValueError(f"Sinal IA malformado: faltam {required_keys}")
                            # FIX #7 (RCA #7) — Removido gate paralelo MIN_CONFIDENCE=0.65.
                            # IA já validou contra effective_min_conf dinâmico (FIX #4) no
                            # OmegaGlobalOrchestrator. Aqui apenas verificamos action válida,
                            # eliminando o threshold hard-coded que anulava o trabalho do M4.
                            if ia_signal.get('action') in (None, 'HOLD'):
                                log.info("[%s %s] [IA] Sinal rejeitado: action=%s",
                                         asset, tf, ia_signal.get('action'))
                                ia_signal = None
                            else:
                                log.info("[%s %s] [IA] Sinal aprovado: action=%s, confidence=%.2f",
                                         asset, tf, ia_signal['action'],
                                         ia_signal.get('confidence', 0) or 0)
                        except Exception as e:
                            log.warning("[%s %s] IA falhou: %s — fallback momentum", asset, tf, e)
                            ia_signal = None

                    if ia_signal and ia_signal.get('action') not in (None, 'HOLD'):
                        signal_dir = ia_signal.get('direction') or ia_signal.get('action')
                        signal_source = "AGENT_IA"
                        ia_lot_override = ia_signal.get('lot')
                        ia_sl_pts = ia_signal.get('stop_loss_pips')
                        ia_tp_pts = ia_signal.get('take_profit_pips')
                        ia_agent_id = ia_signal.get('agent_id', 'AGENT_IA')
                        log.info("[%s %s] FASE4 DECISION=AGENT_IA | dir=%s conf=%.3f strategy=%s",
                                 asset, tf, signal_dir, ia_signal.get('confidence', 0),
                                 ia_signal.get('strategy'))
                    else:
                        # === A2: EDGE GATE (CEO+Conselho 2026-04-27) ===
                        # Bloquear fallback momentum quando ATR/spread/ADX
                        # indicarem que não há edge matemático suficiente.
                        edge_ok, edge_m = has_edge_for_momentum(asset)
                        if not edge_ok:
                            log.info("[%s %s] [EDGE_GATE] BLOCKED reason=%s atr_pct=%s atr/spr=%s adx=%s",
                                     asset, tf, edge_m.get("reason", "?"),
                                     edge_m.get("atr_pct"), edge_m.get("atr_over_spread"),
                                     edge_m.get("adx"))
                            results.append({
                                "asset": asset, "timeframe": tf,
                                "status": "SKIP_EDGE_GATE",
                                "edge_metrics": edge_m,
                            })
                            continue
                        # Fallback momentum MT5 (lógica original) — só após edge OK
                        rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_M1, 0, 5)
                        if rates is not None and len(rates) >= 3:
                            tick_now = mt5.symbol_info_tick(asset)
                            c_price = tick_now.ask if tick_now else rates[-1]['close']
                            avg_3   = (rates[-1]['close'] + rates[-2]['close'] + rates[-3]['close']) / 3
                            signal_dir = "BUY" if c_price > avg_3 else "SELL"
                            log.info("[%s %s] Sentiment: Current=%.5f | Avg3=%.5f | DIR: %s (src=%s) edge=ok adx=%.1f atr/spr=%.1f",
                                     asset, tf, c_price, avg_3, signal_dir, signal_source,
                                     edge_m.get("adx", 0), edge_m.get("atr_over_spread", 0))
                        else:
                            log.warning("[%s %s] Falha ao ler candles MT5 para direcao — SKIP", asset, tf)
                            results.append({"asset": asset, "timeframe": tf, "status": "SKIP_NO_RATES"})
                            continue

                    current_positions = []
                    if mt5_connected:
                        pos_list = mt5.positions_get(symbol=asset)
                        if pos_list:
                            current_positions = [p._asdict() for p in pos_list]

                    if correlation_filter.should_trade(asset, current_positions):
                        # Lote: clamp(min(lot_info, ia_lot_override or lot_info), 0.01, MAX_LOT)
                        eff_lot = lot_info["lot"]
                        if ia_lot_override is not None:
                            try:
                                eff_lot = max(0.01, min(eff_lot, float(ia_lot_override)))
                            except Exception:
                                pass
                        # Concentração por ativo (Fix 5): >40% → reduz 50%
                        try:
                            same_asset = sum(1 for p in (mt5.positions_get(magic=OMEGA_MAGIC) or []) if p.symbol == asset)
                            total_omega = len(mt5.positions_get(magic=OMEGA_MAGIC) or [])
                            if total_omega > 0 and (same_asset / total_omega) > 0.40:
                                eff_lot = max(0.01, round(eff_lot * 0.5, 2))
                                log.info("[%s %s] FASE4 concentration>40%% → lot reduzido a %.2f", asset, tf, eff_lot)
                        except Exception:
                            pass
                        eff_sl = float(ia_sl_pts) if ia_sl_pts is not None else guard["margin_used"] * 2
                        eff_tp = float(ia_tp_pts) if ia_tp_pts is not None else guard["margin_used"] * 2
                        exec_result = mt5_send_order(
                            asset, tf, eff_lot,
                            sl_pts=eff_sl,
                            tp_pts=eff_tp,
                            direction=signal_dir)
                        success = exec_result.get("success", False)
                        # Idempotência / dedup ticket
                        deal_id = exec_result.get("deal")
                        if success and deal_id is not None and deal_id not in _processed_tickets:
                            _processed_tickets.add(deal_id)
                            if agent_ia is not None and signal_source == "AGENT_IA":
                                try:
                                    agent_ia.record_trade_open(
                                        asset, int(deal_id),
                                        float(exec_result.get("fill_price", 0) or 0),
                                        float(eff_lot), ia_agent_id)
                                except Exception as _re:
                                    log.warning("[%s %s] record_trade_open falhou: %s", asset, tf, _re)
                        # Log de auditoria do source
                        log.info("[%s %s] FASE4 EXEC source=%s success=%s deal=%s",
                                 asset, tf, signal_source, success, deal_id)
                        open_pos = min(open_pos + (1 if success else 0), MAX_POSITIONS)
                        ks.update(success, 0.0)
                elif not guard["skip"] and mode == "shadow":
                    log.info("[%s %s] MONITOR | hr134=%.2f%% | margin=%.1fpts | NO ORDER",
                             asset, tf, hr_real, guard["margin_used"])
                    ks.update(True)

                report = build_report(asset, tf, mode, harmonic, 
                                      {"price": a_price, "base_price": b_price, "metadata": {}}, 
                                      guard, exec_result, lot_info)
                out_f = out_dir / f"PaperReport_{asset}_{tf}.json"
                with open(out_f, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                stats.record(report)
                action = report["signal"]["action"]
                if exec_result:
                    log.info("[%s %s] %s | hr134=%.2f%% IC=%s lot=%.2f slip=%.2f lat=%dms | SHA3=%s...",
                             asset, tf, action, hr_real,
                             report["binomial_ic_95"]["interval"],
                             lot_info["lot"],
                             exec_result.get("slippage_pts", 0),
                             exec_result.get("latency_ms", 0),
                             report["checksum"][:16])
                else:
                    log.info("[%s %s] %s | hr134=%.2f%% IC=%s | SHA3=%s...",
                             asset, tf, action, hr_real,
                             report["binomial_ic_95"]["interval"],
                             report["checksum"][:16])

                results.append({
                    "asset": asset, "timeframe": tf, "status": action,
                    "hit_rate_134": hr_real,
                    "ic_95": report["binomial_ic_95"]["interval"],
                    "margin_used": guard["margin_used"],
                    "lot": lot_info["lot"] if lot_info else None,
                    "retcode": exec_result.get("retcode") if exec_result else None,
                    "slippage_pts": exec_result.get("slippage_pts") if exec_result else None,
                    "checksum": report["checksum"][:24],
                })
    finally:
        if mt5_connected:
            mt5_shutdown()
            log.info("MT5 desconectado.")

    # Skip table
    skip_out  = AUDIT_PAPER / "skip_table.json"
    skip_data = {"generated": datetime.now(timezone.utc).isoformat(), "skips": skip_tbl}
    skip_data["checksum"] = sha3(json.dumps(skip_data, indent=2).encode("utf-8"))
    with open(skip_out, "w", encoding="utf-8") as f:
        json.dump(skip_data, f, indent=2, ensure_ascii=False)

    # Stats
    stat_sum = stats.summary()
    log.info("── ESTATÍSTICAS ONLINE ──────────────────────────────────────")
    for k, v in stat_sum.items(): log.info("  %-25s : %s", k, v)

    # Summary
    now = datetime.now(timezone.utc).isoformat()
    summary = {
        "mode": mode, "generated": now, "equity_demo": equity,
        "total_cycles": len(results),
        "kill_switch": ks.triggered, "ks_reason": ks.reason,
        "online_stats": stat_sum, "results": results,
        "log_file": str(log_file),
    }
    sb = json.dumps(summary, indent=2).encode("utf-8")
    summary["checksum"] = sha3(sb)
    sum_out = AUDIT_PAPER / "paper_summary.json"
    with open(sum_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info("=" * 72)
    log.info("%s LOOP CONCLUÍDO | cycles=%d | KS=%s", mode.upper(), len(results), ks.triggered)
    log.info("SHA3 summary: %s", summary["checksum"])
    log.info("Artifacts: %s", AUDIT_PAPER)
    log.info("=" * 72)
    return summary


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OMEGA Shadow/Paper Loop v3.0 — MT5 Real")
    parser.add_argument("--mode",       choices=["shadow", "paper"], default="shadow")
    parser.add_argument("--ativos",     nargs="+", default=sorted(TIER1_ASSETS))
    parser.add_argument("--timeframes", nargs="+", default=["H1", "H4"])
    parser.add_argument("--equity",     type=float, default=DEMO_EQUITY_USD)
    args = parser.parse_args()
    try:
        r = run_loop(args.ativos, args.timeframes, args.mode, args.equity)
        sys.exit(0 if r and not r.get("kill_switch") else 1)
    except Exception:
        log.critical("ERRO CRÍTICO:\n%s", traceback.format_exc())
        sys.exit(2)
