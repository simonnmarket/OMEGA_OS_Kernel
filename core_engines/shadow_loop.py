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
import os
import sys


import time
import traceback
from core_engines.integration_gate import OmegaIntegrationGate
from modules.risk.scale_manager import OmegaScaleManager
from modules.validation.mfa_engine import OmegaMFAEngine
from core_engines.lot_calculator_v2 import LotCalculatorV2, LotCfgV2

# ── RISK_GATE: métricas institucionais de risco (nebular integration phase-1) ──
try:
    import pandas as _pd_risk
    from modules.risk_metrics import RiskMetricsEngine as _RiskMetricsEngine
    _RISK_ENGINE = _RiskMetricsEngine()
except Exception:
    _RISK_ENGINE = None
    _pd_risk = None

# ── REGIME_GATE: Hurst exponent + regime de mercado (nebular integration phase-1) ─
try:
    from modules.fractal_hurst import FractalEngineV2 as _FractalEngineV2, FractalConfig as _FractalConfig
    _FRACTAL_ENGINE = _FractalEngineV2(
        _FractalConfig(min_samples=50, cache_ttl_ms=60_000, use_caching=True)
    )
except Exception:
    _FRACTAL_ENGINE = None

# ── KALMAN PULLBACK: entry timing scorer (nebular integration phase-1) ──────
try:
    from modules.kalman_pullback_engine import OmegaKalmanPullbackEngine as _KalmanPullbackCls
    _KALMAN_ENGINE = _KalmanPullbackCls()
except Exception:
    _KALMAN_ENGINE = None

# ── CIRCUIT_BREAKER: daily loss gate P1 (nebular integration phase-1) ────────
_CB_DD_LIMIT = float(os.getenv("OMEGA_DD_CIRCUIT_BREAK", "3.5"))
try:
    from modules.risk_circuit_breaker import (
        RiskCircuitBreaker as _RiskCircuitBreakerCls,
        CircuitBreakerConfig as _CircuitBreakerConfig,
    )
    _CIRCUIT_BREAKER = _RiskCircuitBreakerCls(
        _CircuitBreakerConfig(daily_loss_threshold_pct=-_CB_DD_LIMIT)
    )
except Exception:
    _CIRCUIT_BREAKER = None

# ── TAIL_RISK_HALT: intraday tail-risk stop P1 (nebular integration phase-1) ─
try:
    from modules.risk_valves_v31 import EmergencyTailRiskHalt as _EmergencyTailRiskHaltCls
    _TAIL_RISK_HALT = _EmergencyTailRiskHaltCls(max_drawdown_per_event=0.03)
except Exception:
    _TAIL_RISK_HALT = None

# ── FLOW DETECTORS: institutional flow modules (awakened for directional trading) ─
try:
    from modules.v_flow_microstructure import VFlowReversalEngine as _VFlowReversalEngineCls
    _V_FLOW_ENGINE = _VFlowReversalEngineCls(window_size=20, leverage_max=5.0)
except Exception:
    _V_FLOW_ENGINE = None

try:
    from modules.volume_physics import VolumePhysicsEngine as _VolumePhysicsEngineCls, PhysicsConfig as _PhysicsConfig
    _VOL_PHYSICS_ENGINE = _VolumePhysicsEngineCls(_PhysicsConfig())
except Exception:
    _VOL_PHYSICS_ENGINE = None

try:
    from modules.volume_profile import VolumeProfileEngine as _VolumeProfileEngineCls
    _VOL_PROFILE_ENGINE = _VolumeProfileEngineCls()
except Exception:
    _VOL_PROFILE_ENGINE = None

try:
    from modules.anomaly_detector import AnomalyDetector as _AnomalyDetectorCls
    _ANOMALY_ENGINE = _AnomalyDetectorCls()
except Exception:
    _ANOMALY_ENGINE = None

try:
    from modules.momentum_physics import MomentumPhysicsEngine as _MomentumPhysicsEngineCls
    _MOMENTUM_ENGINE = _MomentumPhysicsEngineCls()
except Exception:
    _MOMENTUM_ENGINE = None

from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ─── Flow Confluence Scorer ───────────────────────────────────────────────────
def compute_flow_confluence(bar: Dict, symbol: str, direction: int) -> Tuple[float, Dict]:
    """
    Combina sinais dos 5 módulos de fluxo institucional em um score 0-100.
    Retorna (confluence_score, details_dict).
    """
    scores = {}
    weights = {
        "v_flow": 0.25,
        "vol_physics": 0.20,
        "vol_profile": 0.20,
        "anomaly": 0.15,
        "momentum": 0.20
    }
    
    try:
        if _V_FLOW_ENGINE and hasattr(_V_FLOW_ENGINE, 'process_candle'):
            # v_flow_microstructure: VFRSignal com score 0-100
            vflow = _V_FLOW_ENGINE.process_candle(bar.get('close', 0), bar.get('high', 0), 
                                                 bar.get('low', 0), bar.get('volume', 0))
            if hasattr(vflow, 'score'):
                scores['v_flow'] = vflow.score if vflow.direction == direction else 0
            else:
                scores['v_flow'] = 50
        else:
            scores['v_flow'] = 50
    except Exception:
        scores['v_flow'] = 50
    
    try:
        if _VOL_PHYSICS_ENGINE and hasattr(_VOL_PHYSICS_ENGINE, 'update'):
            # volume_physics: PhysicsState com trap_score, urgency
            state = _VOL_PHYSICS_ENGINE.update(bar.get('close', 0), bar.get('high', 0),
                                               bar.get('low', 0), bar.get('volume', 0))
            if hasattr(state, 'trap_score'):
                scores['vol_physics'] = state.trap_score * 100
            elif hasattr(state, 'urgency'):
                scores['vol_physics'] = state.urgency.value * 33
            else:
                scores['vol_physics'] = 50
        else:
            scores['vol_physics'] = 50
    except Exception:
        scores['vol_physics'] = 50
    
    try:
        if _VOL_PROFILE_ENGINE and hasattr(_VOL_PROFILE_ENGINE, 'update'):
            # volume_profile: VolumeState com volume_ratio
            state = _VOL_PROFILE_ENGINE.update(symbol, bar)
            if hasattr(state, 'volume_ratio'):
                scores['vol_profile'] = min(state.volume_ratio * 50, 100)
            else:
                scores['vol_profile'] = 50
        else:
            scores['vol_profile'] = 50
    except Exception:
        scores['vol_profile'] = 50
    
    try:
        if _ANOMALY_ENGINE and hasattr(_ANOMALY_ENGINE, 'detect'):
            # anomaly_detector: AnomalyDetectionResult com severity
            result = _ANOMALY_ENGINE.detect(bar)
            if hasattr(result, 'severity'):
                scores['anomaly'] = result.severity * 100
            else:
                scores['anomaly'] = 50
        else:
            scores['anomaly'] = 50
    except Exception:
        scores['anomaly'] = 50
    
    try:
        if _MOMENTUM_ENGINE and hasattr(_MOMENTUM_ENGINE, 'update'):
            # momentum_physics: MomentumState com velocity
            state = _MOMENTUM_ENGINE.update(symbol, bar)
            if hasattr(state, 'velocity'):
                scores['momentum'] = min(abs(state.velocity) * 50, 100)
            else:
                scores['momentum'] = 50
        else:
            scores['momentum'] = 50
    except Exception:
        scores['momentum'] = 50
    
    # Weighted confluence
    confluence = sum(scores[k] * weights[k] for k in weights)
    return confluence, scores

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
RISK_PER_TRADE_PCT = float(os.getenv("OMEGA_RISK_PER_TRADE", "0.0025"))  # COO Fase1: 0.001 (0.1%)
MIN_LOT_OVERRIDE   = float(os.getenv("OMEGA_MIN_LOT", "0.0"))            # CEO: lote mínimo (0=auto)
MAX_POSITIONS      = int(os.getenv("OMEGA_MAX_POSITIONS", "2"))          # CONSELHO 29/04/2026: default=2 (unanimidade)
DD_DAILY_MAX       = float(os.getenv("OMEGA_DD_DAILY_MAX", "0.01"))       # CONSELHO 29/04/2026: default=1% (unanimidade)
CONCENTRATION_MAX  = float(os.getenv("OMEGA_CONCENTRATION_MAX", "0.40"))   # CQO/COO: max por ativo
MAX_CONSEC_FAIL    = 3

# ─── Perfis por Ativo (CQO 28/04/2026) ──────────────────────────────────────
# cost_pts    : spread+slippage+comissão mínimo para entrar (cost barrier)
# sl_atr_mult : SL = ATR × mult  (stop tighter em forex, wider em crypto)
# tp_atr_mult : TP = ATR × mult  (R/R: tp/sl)
# min_conf    : confiança mínima adicional por ativo (crypto exige mais)
# lot_cap     : lote máximo por ativo (independente do guardrail global)
# regime      : forex | commodity | index | crypto | crypto_alt
ASSET_PROFILES: dict = {
    # ── FOREX: spreads mínimos, session-bound, mean-reverting ──────────────
    "EURUSD": {"cost_pts":   3, "sl_atr_mult": 1.2, "tp_atr_mult": 4.0, "min_conf": 0.62, "lot_cap": 0.25, "regime": "forex"},
    "GBPUSD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.63, "lot_cap": 0.25, "regime": "forex"},
    "AUDUSD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.63, "lot_cap": 0.20, "regime": "forex"},
    "USDCAD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.63, "lot_cap": 0.20, "regime": "forex"},
    "USDCHF": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.63, "lot_cap": 0.20, "regime": "forex"},
    "NZDUSD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.63, "lot_cap": 0.20, "regime": "forex"},
    # ── COMMODITIES: spreads médios, safe-haven/fluxos ──────────────────────
    "XAUUSD": {"cost_pts":  30, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.68, "lot_cap": 0.15, "regime": "commodity"},
    "XAGUSD": {"cost_pts":  20, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.68, "lot_cap": 0.15, "regime": "commodity"},
    # ── INDICES: gap risk, fluxos institucionais ─────────────────────────────
    "US500":  {"cost_pts":  10, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.68, "lot_cap": 0.20, "regime": "index"},
    "NAS100": {"cost_pts":  15, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.70, "lot_cap": 0.15, "regime": "index"},
    "GER40":  {"cost_pts":  10, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.68, "lot_cap": 0.20, "regime": "index"},
    # ── CRYPTO MAJOR: momentum, spread wide, 24/7 ───────────────────────────
    "BTCUSD": {"cost_pts": 100, "sl_atr_mult": 2.0, "tp_atr_mult": 7.0, "min_conf": 0.75, "lot_cap": 0.25, "regime": "crypto"},
    "ETHUSD": {"cost_pts":  50, "sl_atr_mult": 2.0, "tp_atr_mult": 7.0, "min_conf": 0.75, "lot_cap": 0.25, "regime": "crypto"},
    "SOLUSD": {"cost_pts":  30, "sl_atr_mult": 2.0, "tp_atr_mult": 7.0, "min_conf": 0.75, "lot_cap": 0.25, "regime": "crypto"},
    # ── CRYPTO ALT: alta volatilidade, spreads extremos ─────────────────────
    "DOGUSD": {"cost_pts": 200, "sl_atr_mult": 2.5, "tp_atr_mult": 8.0, "min_conf": 0.80, "lot_cap": 0.05, "regime": "crypto_alt"},
    # ── JPY MAJOR: carry-trade flow, direcional sem ruído ─────────────────────
    # Estratégia: USDJPY lidera → todas as crosses seguem a mesma direção JPY.
    # 500+ pips em movimento sustentado são comuns em eventos macro (BOJ/Fed).
    "USDJPY": {"cost_pts":  3, "sl_atr_mult": 1.2, "tp_atr_mult": 4.2, "min_conf": 0.63, "lot_cap": 0.25, "regime": "jpy_major"},
    # ── JPY CROSS: amplificam o movimento do USDJPY ────────────────────────────
    "EURJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.65, "lot_cap": 0.25, "regime": "jpy_cross"},
    "GBPJPY": {"cost_pts":  8, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.67, "lot_cap": 0.25, "regime": "jpy_cross"},
    "AUDJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.65, "lot_cap": 0.25, "regime": "jpy_cross"},
    "CADJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.65, "lot_cap": 0.25, "regime": "jpy_cross"},
    "CHFJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.65, "lot_cap": 0.25, "regime": "jpy_cross"},
}
_PROFILE_DEFAULT = {"cost_pts": 19, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.65, "lot_cap": 0.25, "regime": "generic"}

# ─── EDGE GATE por Classe de Ativo (COO 28/04/2026) ─────────────────────────
# Thresholds mínimos por regime: ATR% e ADX mínimo
# Referências: FIA automated trading risk controls; ESMA automation controls
_EDGE_GATE: dict = {
    "forex":      {"atr_pct_min": 0.0008, "adx_min": 20.0},
    "commodity":  {"atr_pct_min": 0.0012, "adx_min": 18.0},
    "metal":      {"atr_pct_min": 0.0012, "adx_min": 18.0},
    "index":      {"atr_pct_min": 0.0010, "adx_min": 18.0},
    "crypto":     {"atr_pct_min": 0.0040, "adx_min": 16.0},
    "crypto_alt": {"atr_pct_min": 0.0060, "adx_min": 16.0},
    "jpy_major":  {"atr_pct_min": 0.0006, "adx_min": 18.0},
    "jpy_cross":  {"atr_pct_min": 0.0008, "adx_min": 18.0},
    "generic":    {"atr_pct_min": 0.0008, "adx_min": 18.0},
}

# ─── SL MÁXIMO POR CLASSE (hard cap) ────────────────────────────────────────
# Garantia de que o SL nunca excede o limite de risco por operação.
# Calibrado com base em ATR M3 real observado 29/04/2026.
# Env vars permitem ajuste sem deploy: OMEGA_SL_MAX_FOREX=150, etc.
_MAX_SL_PTS: dict = {
    "forex":     int(os.getenv("OMEGA_SL_MAX_FOREX",      "150")),  # 15 pips JPY
    "jpy_major": int(os.getenv("OMEGA_SL_MAX_FOREX",      "150")),
    "jpy_cross": int(os.getenv("OMEGA_SL_MAX_FOREX",      "150")),
    "metal":     int(os.getenv("OMEGA_SL_MAX_METAL",      "250")),
    "commodity": int(os.getenv("OMEGA_SL_MAX_METAL",      "250")),  # XAUUSD usa regime=commodity
    "index":     int(os.getenv("OMEGA_SL_MAX_INDEX",      "600")),
    "crypto":    int(os.getenv("OMEGA_SL_MAX_CRYPTO",    "1500")),
    "crypto_alt":int(os.getenv("OMEGA_SL_MAX_CRYPTO",    "1500")),
    "generic":   int(os.getenv("OMEGA_SL_MAX_GENERIC",    "300")),
}

# ─── JPY Correlation Cluster ──────────────────────────────────────────────────
# Quando USDJPY confirma direção com força, todas as crosses JPY seguem.
JPY_CROSSES = ["EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY"]
OMEGA_MAGIC        = 234001     # ID do EA OMEGA

# ─── Guardrails ─────────────────────────────────────────────────────────────
TIER1_ASSETS = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
                "XAUUSD", "XAGUSD", "US500", "NAS100", "GER40",
                "BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD",
                "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY"}  # Whitelist OMEGA
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

EDGE_MIN_ATR_PCT      = float(os.getenv("OMEGA_EDGE_MIN_ATR_PCT", "0.0015"))   # fallback global (0.15%)
EDGE_MIN_ATR_OVER_SPR = float(os.getenv("OMEGA_EDGE_MIN_ATR_OVER_SPR", "5.0")) # ATR ≥ 5× spread (global)
EDGE_MIN_ADX          = float(os.getenv("OMEGA_EDGE_MIN_ADX", "20.0"))         # ADX ≥ 20 (global)

# CTO-spec: classificação por classe de ativo (thresholds de volume_ratio)
_CRYPTO_ASSETS = {"BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD"}
_METAL_ASSETS  = {"XAUUSD", "XAGUSD"}
_INDEX_ASSETS  = {"US500", "NAS100", "GER40", "UK100", "US30"}
# Calibrado 29/04/2026: dados reais mostram vol_ratio=0.19-0.28 na maior parte do tempo.
# Threshold de 0.70-0.80 bloqueava 95%+ das oportunidades. Reduzido para 0.30/0.35.
_VOL_MIN_BY_CLASS = {
    "forex":  float(os.getenv("OMEGA_VOL_MIN_FOREX",  "0.30")),
    "crypto": float(os.getenv("OMEGA_VOL_MIN_CRYPTO", "0.35")),
    "metal":  float(os.getenv("OMEGA_VOL_MIN_METAL",  "0.30")),
    "index":  float(os.getenv("OMEGA_VOL_MIN_INDEX",  "0.30")),
}

# Conselho Executivo 28/04/2026 — thresholds por classe (CONSENSO UNANIME)
# CTO/CQO/CFO/COO/CIO/TechLead aprovaram calibracao individual por classe.
# Crypto: manter 0.15% (ATR% tipico BTC 0.30-1.00% — threshold correto)
# Forex:  reduzir 0.08% (EURUSD London Open tipico 0.05-0.10%)
# Metais: reduzir 0.12% (XAUUSD volatilidade moderada 0.08-0.25%)
# Indices: reduzir 0.10% (US500/GER40 volatilidade intraday 0.10-0.60%)
# Calibrado 29/04/2026: atr_pct medido em M5 — tipico USDJPY M5=0.015-0.023%, nao 0.08%
# Threshold de 0.08% era calibrado para H1. Corrigido para M5 realista.
_EDGE_THRESHOLDS_BY_CLASS = {
    "crypto": {
        "min_atr_pct":       float(os.getenv("OMEGA_EDGE_CRYPTO_ATR",   "0.0010")),  # 0.10% (era 0.15%)
        "min_atr_over_spr":  float(os.getenv("OMEGA_EDGE_CRYPTO_SPR",   "4.0")),     # era 5.0
        "min_adx":           float(os.getenv("OMEGA_EDGE_CRYPTO_ADX",   "18.0")),    # era 20.0
    },
    "forex": {
        "min_atr_pct":       float(os.getenv("OMEGA_EDGE_FOREX_ATR",    "0.0001")),  # 0.01% (calibrado M5 JPY 29/04)
        "min_atr_over_spr":  float(os.getenv("OMEGA_EDGE_FOREX_SPR",    "1.5")),     # era 2.0
        "min_adx":           float(os.getenv("OMEGA_EDGE_FOREX_ADX",    "13.0")),
    },
    "metal": {
        "min_atr_pct":       float(os.getenv("OMEGA_EDGE_METAL_ATR",    "0.0007")),  # 0.07% (era 0.12%)
        "min_atr_over_spr":  float(os.getenv("OMEGA_EDGE_METAL_SPR",    "3.0")),     # era 4.0
        "min_adx":           float(os.getenv("OMEGA_EDGE_METAL_ADX",    "15.0")),    # era 18.0
    },
    "index": {
        "min_atr_pct":       float(os.getenv("OMEGA_EDGE_INDEX_ATR",    "0.0008")),  # 0.08% (era 0.10%)
        "min_atr_over_spr":  float(os.getenv("OMEGA_EDGE_INDEX_SPR",    "3.0")),     # era 4.0
        "min_adx":           float(os.getenv("OMEGA_EDGE_INDEX_ADX",    "15.0")),    # era 18.0
    },
}

def classify_asset(symbol: str) -> str:
    """Classifica ativo em forex/crypto/metal/index (CTO spec)."""
    s = symbol.upper()
    if s in _CRYPTO_ASSETS: return "crypto"
    if s in _METAL_ASSETS:  return "metal"
    if s in _INDEX_ASSETS:  return "index"
    return "forex"

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

    # Volume ratio (CTO spec: liquidez relativa = vol_atual / media_20c)
    volumes = np.array([r['tick_volume'] for r in rates], dtype=float)
    avg_vol_20    = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else 0.0
    cur_vol       = float(volumes[-1])            if len(volumes) > 0  else 0.0
    vol_ratio     = (cur_vol / avg_vol_20) if avg_vol_20 > 0 else 1.0
    asset_class   = classify_asset(symbol)
    min_vol_ratio = _VOL_MIN_BY_CLASS.get(asset_class, 0.70)

    cls_thr       = _EDGE_THRESHOLDS_BY_CLASS.get(asset_class, _EDGE_THRESHOLDS_BY_CLASS["crypto"])
    thr_atr_pct   = cls_thr["min_atr_pct"]
    thr_atr_spr   = cls_thr["min_atr_over_spr"]
    thr_adx       = cls_thr["min_adx"]

    metrics = {
        "atr": round(atr, 6),
        "atr_pct": round(atr_pct, 6),
        "spread": round(spread_abs, 6),
        "atr_over_spread": round(atr_over_spr, 3),
        "adx": round(adx, 2),
        "vol_ratio": round(vol_ratio, 3),
        "asset_class": asset_class,
        "thr_atr_pct": thr_atr_pct,
        "thr_atr_over_spr": thr_atr_spr,
        "thr_adx": thr_adx,
        "thr_vol_ratio": min_vol_ratio,
    }
    ok = (atr_pct >= thr_atr_pct
          and atr_over_spr >= thr_atr_spr
          and adx >= thr_adx
          and vol_ratio >= min_vol_ratio)
    metrics["ok"] = ok
    if not ok:
        reasons = []
        if atr_pct < thr_atr_pct: reasons.append(f"atr_pct={atr_pct*100:.3f}%<{thr_atr_pct*100:.3f}%[{asset_class}]")
        if atr_over_spr < thr_atr_spr: reasons.append(f"atr/spr={atr_over_spr:.2f}<{thr_atr_spr}")
        if adx < thr_adx: reasons.append(f"adx={adx:.1f}<{thr_adx}[{asset_class}]")
        if vol_ratio < min_vol_ratio: reasons.append(f"vol_ratio<{min_vol_ratio}({asset_class})")
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
        acct = mt5.account_info()
        log.info("MT5 conectado | build=%s | trade_allowed=%s | connected=%s",
                 info.build if info else "?",
                 info.trade_allowed if info else "?",
                 info.connected if info else "?")
        if acct:
            log.info("MT5 conta: login=%d servidor=%s balance=%.2f currency=%s",
                     acct.login, acct.server, acct.balance, acct.currency)
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
    final_sl_pts = max(sl_pts, min_dist + 50)          # Safe buffer para SL
    final_tp_pts = max(tp_pts, min_dist + 50)          # Distância mínima para TP
    final_tp_pts = max(final_tp_pts, final_sl_pts * 3.0)  # R:R mínimo 1:3.0
    
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
    _fill = r.get("price", price) if retcode in RETCODE_OK else price  # sem slippage em falhas
    slippage    = round(abs(_fill - price) / point, 2) if retcode in RETCODE_OK else 0.0

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
    # FIX 29/04/2026: point*contract_size retorna em moeda-cotacao (JPY para pares JPY),
    # nao em USD. Usar trade_tick_value do MT5 que ja esta em moeda da conta (USD).
    tick_size = sym.trade_tick_size if sym.trade_tick_size > 0 else point
    pip_value_per_lot = sym.trade_tick_value * (point / tick_size)
    if pip_value_per_lot <= 0:  # fallback de seguranca
        pip_value_per_lot = point * contract_size

    risk_usd = equity * RISK_PER_TRADE_PCT
    stop_pts = 2.0 * margin_pts
    lot_raw  = risk_usd / max(stop_pts * pip_value_per_lot, 0.0001)
    min_lot  = sym.volume_min if hasattr(sym, 'volume_min') else 0.01
    if MIN_LOT_OVERRIDE > 0.0:  # CEO: lote mínimo forçado para cobertura de fee
        min_lot = max(min_lot, MIN_LOT_OVERRIDE)
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
        "sym_vol_min":    sym.volume_min if hasattr(sym, 'volume_min') else 0.01,
    }



# ─── A1+: MULTI-TF TREND BIAS (D1→H4→H1→M15) ─────────────────────────────────────
MTF_ALIGN_THR = float(os.getenv("OMEGA_MTF_ALIGN_THR", "0.75"))  # 75%=3/4 TFs alinhados

def get_multi_tf_bias(symbol: str) -> dict:
    """
    Calcula viés direcional alinhando D1 + H4 + H1 + M15.
    EMA8 vs EMA21 em cada TF. Score: BUY=+1, SELL=-1.
    CQO Spec 28/04/2026: confluência multi-TF para tomada de decisão.
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
    for tf_const, tf_name, n in TFS:
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, n)
            if rates is None or len(rates) < 22:
                detail[tf_name] = "no_data"
                continue
            closes = np.array([r['close'] for r in rates], dtype=float)
            ema8   = float(np.mean(closes[-8:]))
            ema21  = float(np.mean(closes[-21:]))
            s = 1 if ema8 > ema21 else -1
            scores.append(s)
            detail[tf_name] = "BUY" if s > 0 else "SELL"
        except Exception as _e:
            detail[tf_name] = f"err:{_e}"
    if not scores:
        return {"bias": "NEUTRAL", "score": 0, "alignment": 0.0, "detail": detail}
    net       = sum(scores)
    alignment = abs(net) / len(scores)
    bias      = "BUY" if net > 0 else ("SELL" if net < 0 else "NEUTRAL")
    return {"bias": bias, "score": net, "alignment": round(alignment, 2),
            "n_tfs": len(scores), "detail": detail}


def get_execution_tf_atr(symbol: str, confidence: float = 0.70) -> dict:
    """
    Seleciona TF de execução (M3 padrão, M1 se confidence >= 0.80).
    Calcula ATR para SL/TP tight no TF de execução.
    CQO Spec: M3 reduz ruído 67% vs M1, mantém antecipação de spikes.
    M1 reservado para sinais de alta confiança (>= 0.80).
    """
    import MetaTrader5 as mt5
    import numpy as np
    tf_const = mt5.TIMEFRAME_M1 if confidence >= 0.80 else mt5.TIMEFRAME_M3
    tf_name  = "M1"              if confidence >= 0.80 else "M3"
    try:
        rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, 40)
        if rates is None or len(rates) < 15:
            return {"tf": tf_name, "atr_pts": 0.0, "atr_pct": 0.0015, "error": "no_rates"}
        highs  = np.array([r['high']  for r in rates], dtype=float)
        lows   = np.array([r['low']   for r in rates], dtype=float)
        closes = np.array([r['close'] for r in rates], dtype=float)
        sym    = mt5.symbol_info(symbol)
        atr    = _atr_simple(highs, lows, closes, 14)
        pt     = sym.point if sym else 1e-5
        price  = float(closes[-1]) or 1.0
        return {"tf": tf_name, "atr_pts": round(atr / pt, 1),
                "atr_pct": round(atr / price, 6), "atr_abs": round(atr, 6)}
    except Exception as _e:
        return {"tf": tf_name, "atr_pts": 0.0, "atr_pct": 0.0015, "error": str(_e)}


# ─── JPY CLUSTER SIGNAL ──────────────────────────────────────────────────────
# USDJPY é o líder. Quando ele confirma direção com força (EMA alignment ≥75%),
# todas as crosses JPY entram na mesma direção do fluxo carry-trade.
# 500+ pips em tendência sustentada (BOJ intervenção, Fed pivot, risk-off).

def get_jpy_cluster_signal(min_alignment: float = 0.75) -> dict:
    """
    Lê USDJPY em D1+H4+H1+M15 e propaga sinal de cluster para todas as crosses.
    Retorna direção do JPY e se o cluster está ativo.
    Nota: direção=BUY significa USD fortalece (USDJPY sobe) →
          crosses JPY como EURJPY/GBPJPY também sobem (EUR/GBP vs JPY).
    """
    import MetaTrader5 as mt5
    import numpy as np
    usdjpy_bias = get_multi_tf_bias("USDJPY")
    if usdjpy_bias["alignment"] < min_alignment or usdjpy_bias["bias"] == "NEUTRAL":
        return {
            "active": False,
            "direction": "NEUTRAL",
            "alignment": usdjpy_bias["alignment"],
            "reason": f"usdjpy_align={usdjpy_bias['alignment']:.0%}<{min_alignment:.0%}",
            "crosses": []
        }
    # Estimar amplitude do movimento (ATR H4 × 24h)
    try:
        rates_h4 = mt5.copy_rates_from_pos("USDJPY", mt5.TIMEFRAME_H4, 0, 30)
        if rates_h4 and len(rates_h4) >= 14:
            highs  = np.array([r['high']  for r in rates_h4], dtype=float)
            lows   = np.array([r['low']   for r in rates_h4], dtype=float)
            closes = np.array([r['close'] for r in rates_h4], dtype=float)
            sym_u  = mt5.symbol_info("USDJPY")
            pt     = sym_u.point if sym_u else 0.001
            atr_h4 = _atr_simple(highs, lows, closes, 14)
            atr_pts = round(atr_h4 / pt, 0)
        else:
            atr_pts = 50.0
    except Exception:
        atr_pts = 50.0
    return {
        "active":      True,
        "direction":   usdjpy_bias["bias"],
        "alignment":   usdjpy_bias["alignment"],
        "atr_pts":     atr_pts,
        "estimated_move_pts": atr_pts * 3,  # 3×ATR H4 em tendência diária
        "crosses":     JPY_CROSSES,
        "reason":      f"usdjpy_bias={usdjpy_bias['bias']} align={usdjpy_bias['alignment']:.0%} atr={atr_pts:.0f}pts",
    }


# ─── TREND STRENGTH SCORE ────────────────────────────────────────────────────
# Score composto: EMA momentum + ATR expansão + volume + MTF alinhamento
# Escala: 0.0 (sem tendência) → 1.0 (tendência máxima confirmada em todos TFs)
TREND_MIN_SCORE  = float(os.getenv("OMEGA_TREND_MIN", "0.45"))   # min para operar
PYRAMID_MAX_LAYERS = int(os.getenv("OMEGA_PYRAMID_LAYERS", "3"))  # camadas máx
PYRAMID_TRIGGER_ATR = float(os.getenv("OMEGA_PYRAMID_ATR", "0.5"))  # ATR×0.5 de lucro p/ adicionar

def get_trend_strength(symbol: str, direction: str) -> dict:
    """
    Score de força de tendência para sizing institucional.
    Combina: velocidade EMA + ATR expansão + alinhamento multi-TF.
    CQO 28/04/2026: score >= 0.65 = tendência forte → pyramid permitido.
    """
    import MetaTrader5 as mt5
    import numpy as np
    score_parts = {}
    try:
        # 1. EMA velocity (M15): quanto EMA8 se afastou de EMA21 em %)
        rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
        if rates_m15 is not None and len(rates_m15) >= 22:
            closes = np.array([r['close'] for r in rates_m15], dtype=float)
            ema8   = float(np.mean(closes[-8:]))
            ema21  = float(np.mean(closes[-21:]))
            ema_sep = abs(ema8 - ema21) / (ema21 or 1)  # % separação
            ema_dir_ok = (ema8 > ema21 and direction == "BUY") or (ema8 < ema21 and direction == "SELL")
            score_parts["ema_sep"]    = min(ema_sep * 200, 1.0)   # 0.5% sep = score 1.0
            score_parts["ema_dir"]    = 1.0 if ema_dir_ok else 0.0
        # 2. ATR expansion (H1): ATR atual vs ATR médio — expansão = tendência
        rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 40)
        if rates_h1 is not None and len(rates_h1) >= 20:
            highs  = np.array([r['high']  for r in rates_h1], dtype=float)
            lows   = np.array([r['low']   for r in rates_h1], dtype=float)
            closes = np.array([r['close'] for r in rates_h1], dtype=float)
            atr_now = _atr_simple(highs[-14:], lows[-14:], closes[-14:], 14)
            atr_avg = _atr_simple(highs,       lows,       closes,       28)
            atr_ratio = (atr_now / atr_avg) if atr_avg > 0 else 1.0
            score_parts["atr_expansion"] = min((atr_ratio - 1.0) * 2, 1.0)  # 50% acima da média = 1.0
        # 3. Multi-TF bias alignment (reutiliza get_multi_tf_bias)
        bias = get_multi_tf_bias(symbol)
        mtf_aligned = (bias["bias"] == direction)
        score_parts["mtf_alignment"] = bias["alignment"] if mtf_aligned else (1.0 - bias["alignment"])
        # Composite score (ponderado)
        w = {"ema_sep": 0.25, "ema_dir": 0.30, "atr_expansion": 0.20, "mtf_alignment": 0.25}
        total = sum(score_parts.get(k, 0.5) * v for k, v in w.items())
    except Exception as _e:
        return {"score": 0.5, "parts": {}, "error": str(_e), "pyramid_ok": False}
    return {
        "score":      round(total, 3),
        "parts":      {k: round(v, 3) for k, v in score_parts.items()},
        "pyramid_ok": total >= float(os.getenv("OMEGA_PYRAMID_MIN_SCORE", "0.60")),
        "strong":     total >= 0.75,
    }


def check_pyramid_add(symbol: str, direction: str, open_positions: list,
                      pos_ledger: dict, prof: dict, exec_atr: dict,
                      equity: float) -> dict:
    """
    Motor de Pyramiding Institucional (CQO 28/04/2026).
    Regras para adicionar camada a uma posição lucrativa:
      1. Posição existente na mesma direção e lucro >= ATR×PYRAMID_TRIGGER_ATR
      2. Trend strength score >= OMEGA_PYRAMID_MIN_SCORE (default 0.60)
      3. Layers existentes < PYRAMID_MAX_LAYERS
      4. Lot da nova camada = base × 0.75^layer (progressivo regressivo)
    Retorna: {add: bool, lot: float, reason: str, layer: int}
    """
    if not open_positions:
        return {"add": False, "reason": "no_open_positions"}
    same_dir = [p for p in open_positions
                if p.get("symbol") == symbol and p.get("direction") == direction]
    if not same_dir:
        return {"add": False, "reason": "no_same_dir_position"}
    # Contar layers atuais para este símbolo+direção
    current_layers = len(same_dir)
    if current_layers >= PYRAMID_MAX_LAYERS:
        return {"add": False, "reason": f"max_layers={PYRAMID_MAX_LAYERS}", "layer": current_layers}
    # Verificar lucro acumulado da posição mais antiga
    best_pos = max(same_dir, key=lambda p: p.get("last_profit", 0))
    atr_pts   = exec_atr.get("atr_pts", 0)
    trigger   = atr_pts * PYRAMID_TRIGGER_ATR
    if best_pos.get("last_profit", 0) < trigger:
        return {"add": False, "reason": f"profit={best_pos.get('last_profit',0):.2f}<trigger={trigger:.1f}pts",
                "layer": current_layers}
    # Verificar tendência forte antes de pyramidar
    ts = get_trend_strength(symbol, direction)
    if not ts.get("pyramid_ok"):
        return {"add": False, "reason": f"trend_score={ts['score']:.2f}<min", "layer": current_layers}
    # Lote regressivo: cada camada é 75% da anterior (preserva capital)
    base_lot = prof.get("lot_cap", 0.10)
    layer_lot = round(base_lot * (0.75 ** current_layers), 2)
    sym_info  = None
    try:
        import MetaTrader5 as mt5
        sym_info = mt5.symbol_info(symbol)
    except Exception:
        pass
    min_lot = sym_info.volume_min if sym_info else 0.01
    layer_lot = max(layer_lot, min_lot)
    return {
        "add":           True,
        "lot":           layer_lot,
        "layer":         current_layers + 1,
        "trend_score":   ts["score"],
        "trigger_pts":   trigger,
        "profit_pts":    best_pos.get("last_profit", 0),
        "reason":        f"pyramid_layer{current_layers+1} score={ts['score']:.2f}",
    }


# ─── Build AnalysisReport ────────────────────────────────────────────────────────────
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
    def reset_session(self, equity: float) -> None:
        """Conselho 28/04/2026: reseta baseline por sessao para evitar
        falsos positivos por drawdown residual de runs anteriores.
        Ref: Two Sigma Model Risk Mgmt (2020) — session-scoped risk limits."""
        self.equity = equity; self.daily_pnl = 0.0
        self.consec_fail = 0; self.triggered = False; self.reason = ""
        log.info("KILL SWITCH reset: nova baseline equity=USD %.2f", equity)
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
    _pos_ledger: dict = {}  # ticket -> {entry details + last_known_profit}
    _realized_pnl: float = 0.0
    _realized_n:   int   = 0
    _lot_calc = LotCalculatorV2(LotCfgV2())  # CQO 28/04/2026: 4-factor adaptive sizing
    _risk_returns: list = []       # pnl/equity por trade fechado → Sharpe rolling
    _fractal_cache: dict = {}      # asset → {"ts": float, "regime": str, "hurst": float}
    _flow_state: dict = {}        # symbol → flow confluence score (0-100)

    # Conselho 28/04/2026: reset KS baseline com equity real do MT5 para evitar
    # falsos positivos por drawdown residual de runs anteriores.
    if mode == "paper" and mt5_connected:
        _acct = mt5.account_info()
        if _acct and _acct.equity > 0:
            ks.reset_session(_acct.equity)
            if _CIRCUIT_BREAKER is not None:
                _CIRCUIT_BREAKER.initialize_day(_acct.equity)
                log.info("[CIRCUIT_BREAKER] Inicializado: anchor=$%.2f DD_limit=%.1f%%",
                         _acct.equity, _CB_DD_LIMIT)
            if _TAIL_RISK_HALT is not None:
                _TAIL_RISK_HALT.set_starting_equity(_acct.equity)
                log.info("[TAIL_RISK_HALT] Inicializado: anchor=$%.2f limit=3.0%%", _acct.equity)

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

                # === CIRCUIT_BREAKER + TAIL_RISK_HALT: P1 intraday gates ===
                if mode == "paper" and mt5_connected and (
                    _CIRCUIT_BREAKER is not None or _TAIL_RISK_HALT is not None
                ):
                    _live_acct = mt5.account_info()
                    if _live_acct:
                        if _CIRCUIT_BREAKER is not None:
                            _cb_ok, _cb_msg, _cb_st = _CIRCUIT_BREAKER.update_equity(_live_acct.equity)
                            if not _cb_ok:
                                log.critical("[%s %s] [CIRCUIT_BREAKER] TRIP %s | DD=%.2f%%",
                                             asset, tf, _cb_msg,
                                             _cb_st.get("gross_loss_intraday_pct", 0))
                                ks.triggered = True; ks.reason = f"CB:{_cb_msg}"; break
                        if _TAIL_RISK_HALT is not None:
                            _tr_halt, _tr_info = _TAIL_RISK_HALT.check_tail_risk(_live_acct.equity)
                            if _tr_halt:
                                log.critical("[%s %s] [TAIL_RISK] HALT DD=%.2f%%",
                                             asset, tf, _tr_info.get("drawdown", 0))
                                ks.triggered = True; ks.reason = "TAIL_RISK_HALT"; break

                if ks.triggered:
                    log.critical("[%s %s] KS ativo — abortando.", asset, tf); break

                log.info("[%s %s] ── Ciclo ──", asset, tf)

                # === FLOW CONFLUENCE: institutional flow scoring (awakened modules) ===
                # MOVIDO antes de guardrails para sempre logar estado do fluxo
                _flow_conf = 50.0  # default neutro
                _flow_details = {}
                try:
                    _rates_flow = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_M1, 0, 1)
                    if _rates_flow is not None and len(_rates_flow) > 0:
                        _bar_flow = {
                            "close": float(_rates_flow[0]["close"]),
                            "high": float(_rates_flow[0]["high"]),
                            "low": float(_rates_flow[0]["low"]),
                            "volume": float(_rates_flow[0]["tick_volume"])
                        }
                        # Usar direção neutra (0) para scoring sem viés
                        _flow_conf, _flow_details = compute_flow_confluence(_bar_flow, asset, 0)
                        _flow_state[asset] = _flow_conf
                        log.info("[%s %s] [FLOW] confluence=%.1f v_flow=%.0f vol_physics=%.0f vol_profile=%.0f anomaly=%.0f momentum=%.0f",
                                 asset, tf, _flow_conf,
                                 _flow_details.get("v_flow", 50),
                                 _flow_details.get("vol_physics", 50),
                                 _flow_details.get("vol_profile", 50),
                                 _flow_details.get("anomaly", 50),
                                 _flow_details.get("momentum", 50))
                    else:
                        log.warning("[%s %s] [FLOW] sem dados M1", asset, tf)
                except Exception as _flow_err:
                    log.error("[%s %s] [FLOW] erro: %s", asset, tf, _flow_err)

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

                # Flow scorer já foi chamado antes de guardrails (linha ~1329)
                # Aqui usamos o valor em cache se houver sinal
                _flow_conf = _flow_state.get(asset, 50.0)

                if mode == "paper" and open_pos >= MAX_POSITIONS:
                    log.warning("[%s %s] MAX_POSITIONS=%d atingido.", asset, tf, MAX_POSITIONS); continue

                # Motor Harmônico V3
                out_dir  = AUDIT_PAPER / f"{asset}_{tf}"
                harmonic = run_harmonic(asset, tf, guard["margin_used"], out_dir)
                if harmonic is None:
                    # SKIP_HARMONIC: Motor V3 sem dados (ativo fechado/sem CSV) — NÃO conta como falha de execução para KS
                    results.append({"asset": asset, "timeframe": tf, "status": "SKIP_HARMONIC"}); continue

                # Guardrail final
                s134    = (harmonic.get("engines", {}).get("harmonic", {})
                           .get("metrics", {}).get("134_stats", {}))
                hr_real = s134.get("hit_rate", 0.0)
                guard   = check_guardrails(asset, tf, hr_real, 1.0, dm)

                # Execução e Preços (PSA FIX - Zero Initialization)
                lot_info = exec_result = None
                eff_lot  = None           # LotCalcV2: lote adaptativo final
                _lot_v2_factors: dict = {}
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
                        # === REGIME_GATE: Hurst exponent (fractal_hurst — nebular phase-1) ===
                        if _FRACTAL_ENGINE is not None:
                            _now_ts = time.time()
                            _fc = _fractal_cache.get(asset)
                            if _fc is None or (_now_ts - _fc["ts"]) > 60.0:
                                try:
                                    _rg_rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_M15, 0, 150)
                                    if _rg_rates is not None and len(_rg_rates) >= 50:
                                        import numpy as _np_rg
                                        _rg_cls = _np_rg.array([r["close"] for r in _rg_rates], dtype=_np_rg.float64)
                                        _rg_st = _FRACTAL_ENGINE.analyze_series(_rg_cls)
                                        _fractal_cache[asset] = {
                                            "ts": _now_ts,
                                            "regime": _rg_st.regime.name,
                                            "hurst": round(_rg_st.hurst_exponent, 4),
                                        }
                                except Exception as _rge:
                                    log.debug("[%s %s] [REGIME_GATE] erro: %s", asset, tf, _rge)
                            _fc = _fractal_cache.get(asset)
                            if _fc:
                                if _fc["regime"] == "STRONG_MEAN_REVERTING":
                                    log.info("[%s %s] [REGIME_GATE] BLOCKED H=%.3f regime=%s",
                                             asset, tf, _fc["hurst"], _fc["regime"])
                                    results.append({"asset": asset, "timeframe": tf,
                                                    "status": "SKIP_REGIME_GATE",
                                                    "hurst": _fc["hurst"],
                                                    "regime": _fc["regime"]})
                                    continue
                                log.info("[%s %s] [REGIME_GATE] OK H=%.3f regime=%s",
                                         asset, tf, _fc["hurst"], _fc["regime"])

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

                    # === MULTI-TF BIAS CHECK (CQO 28/04/2026: D1+H4+H1+M15 confluência) ===
                    # Bloquear sinal oposto à direção macro quando alinhamento >= MTF_ALIGN_THR.
                    # Permite entrar apenas com o vento — maior probabilidade de movimento sustentado.
                    if signal_dir:
                        try:
                            _tf_bias = get_multi_tf_bias(asset)
                            if (_tf_bias["alignment"] >= MTF_ALIGN_THR
                                    and _tf_bias["bias"] != "NEUTRAL"
                                    and _tf_bias["bias"] != signal_dir):
                                log.info("[%s %s] [MTF_BIAS] BLOCK macro=%s≠signal=%s align=%.0f%% | %s",
                                         asset, tf, _tf_bias["bias"], signal_dir,
                                         _tf_bias["alignment"] * 100, _tf_bias["detail"])
                                results.append({"asset": asset, "timeframe": tf,
                                               "status": "SKIP_MTF_BIAS",
                                               "macro_bias": _tf_bias["bias"],
                                               "signal_dir": signal_dir,
                                               "alignment": _tf_bias["alignment"]})
                                continue
                            log.info("[%s %s] [MTF_BIAS] ok bias=%s align=%.0f%% %s",
                                     asset, tf, _tf_bias["bias"],
                                     _tf_bias["alignment"] * 100, _tf_bias["detail"])
                        except Exception as _mte:
                            log.warning("[%s %s] [MTF_BIAS] erro (não bloqueia): %s", asset, tf, _mte)

                    current_positions = []
                    all_open_positions = []
                    if mt5_connected:
                        pos_list = mt5.positions_get(symbol=asset)
                        if pos_list:
                            current_positions = [p._asdict() for p in pos_list]
                        _omega_all = mt5.positions_get(magic=OMEGA_MAGIC) or []
                        all_open_positions = [p._asdict() for p in _omega_all]
                        # Ledger: detectar fechamentos por SL/TP em tempo real
                        _live_tickets = {p.ticket for p in _omega_all}
                        for _lp_profit in _omega_all:  # atualiza last_profit
                            if _lp_profit.ticket in _pos_ledger:
                                _pos_ledger[_lp_profit.ticket]["last_profit"] = _lp_profit.profit
                        for _tk, _entry in list(_pos_ledger.items()):
                            if _entry["status"] == "open" and _tk not in _live_tickets:
                                _entry["status"] = "closed"
                                _entry["exit_time"] = datetime.now(timezone.utc).isoformat()
                                _realized_pnl += _entry.get("last_profit", 0.0)
                                _realized_n   += 1
                                _lot_calc.update_performance(_entry.get("last_profit", 0.0))
                                _risk_returns.append(_entry.get("last_profit", 0.0) / max(equity, 1.0))
                                log.info("[LEDGER] FECHADA %s #%d pnl=%.4f | total_realiz=%.4f n=%d",
                                         _entry["symbol"], _tk, _entry.get("last_profit", 0),
                                         _realized_pnl, _realized_n)

                    # Flow scorer já foi chamado antes do sinal generation (linha ~1489)
                    # Aqui usamos o valor em cache se houver sinal
                    _flow_conf = _flow_state.get(asset, 50.0)

                    _jpy_cluster_active = asset.upper() in JPY_CROSSES or asset.upper() == "USDJPY"
                    _corr_ok = correlation_filter.should_trade(
                        asset, all_open_positions,
                        direction=signal_dir,
                        cluster_allowed=_jpy_cluster_active,
                    )
                    if not _corr_ok:
                        log.info("[%s %s] [CORR] SKIP_CORRELATION dir=%s", asset, tf, signal_dir)
                        results.append({"asset": asset, "timeframe": tf, "status": "SKIP_CORRELATION",
                                        "direction": signal_dir})
                        continue
                    if _corr_ok:
                        # === ASSET PROFILE (CQO 28/04/2026) ===
                        _prof = ASSET_PROFILES.get(asset, _PROFILE_DEFAULT)

                        # === LotCalculator V2 — CQO 28/04/2026 ===
                        # 4 fatores: volatilidade ATR + confiança IA + desempenho + kelly(off)
                        _conf_score = float(ia_signal.get('confidence', 0.70) if ia_signal else 0.70)
                        # BONUS: flow_confidence aumenta confiança para lot sizing
                        _conf_score = min(_conf_score + (_flow_conf - 50) * 0.005, 1.0)  # até +0.25 bonus
                        # Gate de confiança mínima por ativo (crypto > forex)
                        if _conf_score < _prof["min_conf"]:
                            log.info("[%s %s] [PROFILE] SKIP conf=%.2f < min_conf=%.2f regime=%s",
                                     asset, tf, _conf_score, _prof["min_conf"], _prof["regime"])
                            results.append({"asset": asset, "timeframe": tf,
                                           "status": "SKIP_MIN_CONF_PROFILE",
                                           "conf": _conf_score, "min_conf": _prof["min_conf"]})
                            continue
                        _exec_atr   = get_execution_tf_atr(asset, _conf_score)
                        _atr_avg    = _lot_calc.update_atr(asset, _exec_atr.get("atr_pct", 0.0015))

                        # ── SL/TP calculado ANTES do lote (FIX 29/04/2026) ──────────────
                        # SL deve ser passado ao LotCalcV2 para que o risco em USD
                        # reflita o stop REAL (ATR × mult), não o ATR bruto.
                        _exec_atr_pts_pre = _exec_atr.get("atr_pts", 0.0)
                        _sl_mult_pre = _prof["sl_atr_mult"]
                        _tp_mult_pre = _prof["tp_atr_mult"]
                        _min_pts_pre = max(float(_prof["cost_pts"]) * 2.0, 8.0)
                        _max_sl_pre  = _MAX_SL_PTS.get(_prof["regime"], _MAX_SL_PTS["generic"])
                        if _exec_atr_pts_pre > 0:
                            _pre_sl = _exec_atr_pts_pre * _sl_mult_pre
                            _pre_tp = _exec_atr_pts_pre * _tp_mult_pre
                        else:
                            _pre_sl = float(_prof["cost_pts"]) * 3.0
                            _pre_tp = float(_prof["cost_pts"]) * 6.5
                        # Aplicar CAP máximo de SL por classe — impede stop demasiado largo
                        _pre_sl = min(max(_pre_sl, _min_pts_pre), _max_sl_pre)
                        _pre_tp = max(_pre_tp, _pre_sl * (_tp_mult_pre / _sl_mult_pre))
                        # ─────────────────────────────────────────────────────────────────

                        _lot_v2     = _lot_calc.calculate(
                            equity            = equity,
                            atr_pct           = _exec_atr.get("atr_pct", 0.0015),
                            atr_avg_pct       = _atr_avg,
                            confidence        = _conf_score,
                            expected_pts      = _pre_sl,   # SL real (com mult+cap)
                            pip_value_per_lot = lot_info.get("pip_value_lot", 0.01),
                            sym_min_lot       = lot_info.get("sym_vol_min", 0.01),
                        )
                        if _lot_v2.get("skip"):
                            log.info("[%s %s] [COST_BARRIER] %s", asset, tf, _lot_v2.get("skip_reason"))
                            results.append({"asset": asset, "timeframe": tf,
                                           "status": "SKIP_COST_BARRIER",
                                           "reason": _lot_v2.get("skip_reason")})
                            continue
                        eff_lot = _lot_v2["lot"]
                        _lot_v2_factors = {k: _lot_v2[k] for k in
                                           ("vol_f","conf_f","perf_f","kelly_f","base_lot","risk_usd")
                                           if k in _lot_v2}
                        # Per-asset lot cap (crypto menor, forex maior)
                        eff_lot = min(eff_lot, _prof["lot_cap"])
                        # IA override: respeita sugestão IA se for menor (conservador)
                        if ia_lot_override is not None:
                            try:
                                eff_lot = min(eff_lot, float(ia_lot_override))
                                eff_lot = max(lot_info.get("sym_vol_min", 0.01), eff_lot)
                            except Exception:
                                pass
                        # Concentração por ativo (Fix 5): >CONCENTRATION_MAX → reduz 50%
                        try:
                            same_asset = sum(1 for p in (mt5.positions_get(magic=OMEGA_MAGIC) or []) if p.symbol == asset)
                            total_omega = len(mt5.positions_get(magic=OMEGA_MAGIC) or [])
                            if total_omega > 0 and (same_asset / total_omega) > CONCENTRATION_MAX:
                                eff_lot = max(lot_info.get("sym_vol_min", 0.01), round(eff_lot * 0.5, 2))
                                log.info("[%s %s] FASE4 concentration>40%% → lot reduzido a %.2f", asset, tf, eff_lot)
                        except Exception:
                            pass
                        # SL/TP: valores já calculados acima (com cap + mult)
                        # SL: IA pode fornecer valor mais apertado, respeitamos
                        # TP: IA pode sugerir alvo, mas NUNCA abaixo do R:R mínimo do perfil
                        eff_sl = float(ia_sl_pts) if ia_sl_pts is not None else _pre_sl
                        _tp_rr_floor = eff_sl * (_tp_mult_pre / max(_sl_mult_pre, 0.01))
                        if ia_tp_pts is not None:
                            eff_tp = max(float(ia_tp_pts), _tp_rr_floor)
                        else:
                            eff_tp = max(_pre_tp, _tp_rr_floor)
                        # Risco efetivo em USD para log
                        _risk_usd_eff = eff_sl * lot_info.get("pip_value_lot", 0.01) * (eff_lot or 0.01)
                        log.info("[%s %s] [%s] lot=%.2f execTF=%s atr=%.1f SL=%.0fpts($%.2f) TP=%.0fpts RR=1:%.2f conf=%.2f",
                                 asset, tf, _prof["regime"].upper(), eff_lot,
                                 _exec_atr["tf"], _exec_atr.get("atr_pts", 0),
                                 eff_sl, _risk_usd_eff, eff_tp,
                                 eff_tp / max(eff_sl, 1), _conf_score)

                        # === RISK_GATE: Sharpe rolling institucional (risk_metrics — nebular phase-1) ===
                        if _RISK_ENGINE is not None and _pd_risk is not None and len(_risk_returns) >= 30:
                            _rg_sharpe = _RISK_ENGINE.sharpe_ratio(_pd_risk.Series(_risk_returns[-60:]))
                            if _rg_sharpe < 0.3:
                                log.warning("[%s %s] [RISK_GATE] BLOCKED sharpe=%.3f < 0.3 (n=%d)",
                                            asset, tf, _rg_sharpe, len(_risk_returns))
                                results.append({"asset": asset, "timeframe": tf,
                                               "status": "SKIP_RISK_GATE",
                                               "sharpe": round(_rg_sharpe, 4)})
                                continue
                            log.info("[%s %s] [RISK_GATE] OK sharpe=%.3f n=%d",
                                     asset, tf, _rg_sharpe, len(_risk_returns))

                        # === KALMAN PULLBACK: entry timing scorer (nebular phase-1, log-only) ===
                        if _KALMAN_ENGINE is not None:
                            try:
                                _kal_rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_M5, 0, 60)
                                if _kal_rates is not None and len(_kal_rates) >= 20:
                                    import numpy as _np_kal
                                    _kal_arr = _np_kal.array(
                                        [[r["open"], r["high"], r["low"], r["close"], float(r.get("tick_volume", 100))]
                                         for r in _kal_rates], dtype=_np_kal.float64
                                    )
                                    _kal_res = _KALMAN_ENGINE.execute(_kal_arr)
                                    _kal_score = round(float(_kal_res.get("pullback_confidence", 0)), 4)
                                    _kal_is_pb  = bool(_kal_res.get("is_kalman_pullback", False))
                                    _kal_break  = bool(_kal_res.get("is_structural_break", False))
                                    log.info("[%s %s] [KALMAN] pullback=%s score=%.4f vel=%.4f break=%s",
                                             asset, tf, _kal_is_pb, _kal_score,
                                             float(_kal_res.get("velocity", 0)), _kal_break)
                            except Exception as _ke:
                                log.debug("[%s %s] [KALMAN] scorer falhou: %s", asset, tf, _ke)

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
                            # Ledger: registra posicao aberta para rastrear P&L
                            try:
                                _new_pos = mt5.positions_get(symbol=asset) or []
                                for _np in _new_pos:
                                    if _np.magic == OMEGA_MAGIC and _np.ticket not in _pos_ledger:
                                        # Custo de entrada: spread × contrato × lote (estimativa fee round-trip)
                                        try:
                                            _sym_i = mt5.symbol_info(asset)
                                            _tick_i = mt5.symbol_info_tick(asset)
                                            _spr = (_tick_i.ask - _tick_i.bid) if _tick_i else 0
                                            _cs  = _sym_i.trade_contract_size if _sym_i else 1
                                            _spread_cost = round(_spr * _cs * eff_lot, 4)
                                        except Exception:
                                            _spread_cost = 0.0
                                        _pos_ledger[_np.ticket] = {
                                            "symbol": asset, "direction": signal_dir,
                                            "lot": eff_lot, "entry_price": exec_result.get("fill_price", 0),
                                            "sl": exec_result.get("sl_price", 0),
                                            "tp": exec_result.get("tp_price", 0),
                                            "entry_deal": deal_id,
                                            "entry_time": datetime.now(timezone.utc).isoformat(),
                                            "last_profit": _np.profit, "status": "open",
                                            "spread_cost_usd": _spread_cost,
                                            "slippage_pts": exec_result.get("slippage_pts", 0),
                                        }
                                        log.info("[LEDGER] entry=%s #%d lot=%.2f spread_cost=$%.4f slip_pts=%.1f",
                                                 asset, _np.ticket, eff_lot, _spread_cost,
                                                 exec_result.get("slippage_pts", 0))
                                        log.info("[LEDGER] Posicao aberta: %s #%d entry=%.5f",
                                                 asset, _np.ticket, _np.price_open)
                            except Exception as _le:
                                log.warning("[LEDGER] Erro ao registrar posicao: %s", _le)
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
                    _lot_disp = eff_lot if eff_lot is not None else (lot_info["lot"] if lot_info else 0)
                    log.info("[%s %s] %s | hr134=%.2f%% IC=%s lotV2=%.2f slip=%.2f lat=%dms | SHA3=%s...",
                             asset, tf, action, hr_real,
                             report["binomial_ic_95"]["interval"],
                             _lot_disp,
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
                    "lot": eff_lot if eff_lot is not None else (lot_info["lot"] if lot_info else None),
                    "lot_v2": _lot_v2_factors if _lot_v2_factors else None,
                    "retcode": exec_result.get("retcode") if exec_result else None,
                    "slippage_pts": exec_result.get("slippage_pts") if exec_result else None,
                    "checksum": report["checksum"][:24],
                })
    finally:
        if mt5_connected:
            # Ledger: snapshot P&L final de todas as posicoes OMEGA antes de desconectar
            try:
                _all_open = mt5.positions_get(magic=OMEGA_MAGIC) or []
                for _p in _all_open:
                    if _p.ticket in _pos_ledger:
                        _pos_ledger[_p.ticket]["last_profit"] = _p.profit
                    else:
                        _pos_ledger[_p.ticket] = {
                            "symbol": _p.symbol, "direction": "BUY" if _p.type == 0 else "SELL",
                            "lot": _p.volume, "entry_price": _p.price_open,
                            "entry_time": datetime.fromtimestamp(_p.time, tz=timezone.utc).isoformat(),
                            "last_profit": _p.profit, "status": "open",
                        }
                _ledger_pnl = sum(v.get("last_profit", 0) for v in _pos_ledger.values())
                _ledger_n   = len(_pos_ledger)
                log.info("[LEDGER] %d posicoes | realized=%d pnl_realizd=%.4f | float=%.4f",
                         _ledger_n, _realized_n, _realized_pnl, _ledger_pnl)
                _ledger_path = AUDIT_PAPER / "positions_ledger.json"
                _ledger_data = {"generated": datetime.now(timezone.utc).isoformat(),
                                "positions": _pos_ledger,
                                "total_pnl_snapshot": round(_ledger_pnl, 4),
                                "realized_pnl": round(_realized_pnl, 4),
                                "realized_n": _realized_n,
                                "n_positions": _ledger_n}
                with open(_ledger_path, "w", encoding="utf-8") as _lf:
                    json.dump(_ledger_data, _lf, indent=2)
            except Exception as _le:
                log.warning("[LEDGER] Erro no snapshot final: %s", _le)
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
    _ledger_sum = {"n": len(_pos_ledger),
                   "total_pnl": round(sum(v.get("last_profit", 0) for v in _pos_ledger.values()), 4),
                   "realized_pnl": round(_realized_pnl, 4),
                   "realized_n": _realized_n,
                   "positions": {str(k): v for k, v in _pos_ledger.items()}}
    summary = {
        "mode": mode, "generated": now, "equity_demo": equity,
        "total_cycles": len(results),
        "kill_switch": ks.triggered, "ks_reason": ks.reason,
        "online_stats": stat_sum, "results": results,
        "log_file": str(log_file),
        "positions_ledger": _ledger_sum,
        "lot_calc_v2": _lot_calc.diagnostics(),
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
