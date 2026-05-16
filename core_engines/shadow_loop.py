#!/usr/bin/env python3
"""
OMEGA SHADOW / PAPER LOOP ENGINE v3.0 — MT5 REAL INTEGRADO
nebular-kuiper\core_engines\shadow_loop.py

SHADOW : gera sinais, loga, NÃO envia ordens (zero risco).
PAPER  : envia ordens reais para conta DEMO via MetaTrader5 API.
         Kill switch: DD diário ≥ limiar OU falhas consecutivas de execução (limiar configurável);
         retcode 10018 (MARKET_CLOSED) não incrementa o contador de falhas consecutivas.

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
from core_engines.kill_switch_persistent import PersistentKillSwitch

# ── ATOMIC ORDER LOCK — previne race condition entre ciclos paralelos ──────────
try:
    from modules.omega_order_lock import acquire as _lock_acquire, release as _lock_release
    _ORDER_LOCK_AVAILABLE = True
except Exception:
    _ORDER_LOCK_AVAILABLE = False
    def _lock_acquire(timeout: float = 3.0) -> bool:   # noqa
        return True
    def _lock_release() -> None:   # noqa
        pass

# ── MICRO ENTRY FILTER — M1 MANDATORY EXECUTION GATE (CEO 2026-05-12) ─────────
try:
    from modules.micro_entry_filter import MicroEntryFilter as _MicroEntryFilterCls
    _MICRO_FILTER       = _MicroEntryFilterCls()
    _MICRO_FILTER_AVAIL = True
except Exception as _mef_import_err:
    _MICRO_FILTER       = None
    _MICRO_FILTER_AVAIL = False

# ── ZONE NAVIGATOR — REGIME FILTER NICER v3.1 (CEO 2026-05-14) ──────────────────
# Primeira camada macro: CORE_STRONG/CORE_NORMAL = operar | BUFFER = bloquear
try:
    from modules.omega_zone_navigator import ZoneNavigatorV3 as _ZoneNavCls
    from modules.omega_zone_navigator import build_zone_df_from_mt5 as _zone_df_from_mt5
    _ZONE_NAV       = _ZoneNavCls()
    _ZONE_NAV_AVAIL = True
except Exception as _znav_import_err:
    _ZONE_NAV       = None
    _ZONE_NAV_AVAIL = False

# ── ZAK MIR GUARDRAIL — MACRO GEOMETRY FILTER (CEO 2026-05-13) ─────────────────
# Filtro de pré-gate: RSI50 + SMA50 + Trap Detection (antes do M1-GATE)
try:
    from modules.zak_guardrail import ZakMirGuardrailV1 as _ZakGuardrailCls
    _ZAK_GUARDRAIL       = _ZakGuardrailCls()
    _ZAK_GUARDRAIL_AVAIL = True
except Exception as _zak_import_err:
    _ZAK_GUARDRAIL       = None
    _ZAK_GUARDRAIL_AVAIL = False

# ── TESSERACT SNIPER — XAUUSD SPECIALIST ENGINE (CEO 2026-05-14) ─────────────
# Motor de tiro limpo: 3D confluência (Macro + Keltner/VWAP + Volume Surge)
# Actua APENAS em XAUUSD. Sem confluência = sem entrada.
try:
    from modules.tesseract_sniper import TesseractSniperV1 as _TesseractCls
    from modules.tesseract_sniper import build_sniper_df as _build_sniper_df
    _TESSERACT       = _TesseractCls()
    _TESSERACT_AVAIL = True
except Exception as _tess_import_err:
    _TESSERACT       = None
    _TESSERACT_AVAIL = False

# ── OMEGA MARKET PROFILE ENGINE — STRUCTURAL INTELLIGENCE (CEO 2026-05-14) ──────
# Motor = Black Market v4.0 (trilogia: OMEGA_BLACK_MARKET_PROFILE_FINAL_V4.py); deploy = modules.omega_market_profile_engine (CANON_SYNC).
# Camada 5: POC + Shark Absorption + rPOC + Gann — se o trade passar MTF (ex.: W1=2), o MP-GATE filtra Shark / boost TP.
try:
    from modules.omega_market_profile_engine import ComponentEngine as _MPEngineCls
    _MP_AVAIL = True
except Exception as _mp_import_err:
    _MPEngineCls = None  # type: ignore
    _MP_AVAIL    = False
_MP_ENGINES: dict = {}  # {asset: ComponentEngine} — lazy init por activo

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

# ── PARTIAL_CLOSE: trava de lucro progressiva (nebular integration phase-1) ─
# NOTA: uma instância POR posição (dict ticket → engine) para rastrear cada ordem independentemente
# RECALIBRADO PSA-WIND 30/04/2026: níveis menos agressivos para não matar posição cedo
try:
    from modules.risk_valves_v31 import ProgressivePartialCloseComplete as _ProgressivePartialCloseCompleteCls
    _PARTIAL_CLOSE_AVAILABLE = True
except Exception:
    _PARTIAL_CLOSE_AVAILABLE = False
    _ProgressivePartialCloseCompleteCls = None
# CEO 2026-05-14: TP1 reduzido de 1.5× para 1.0× ATR para capturar parciais antes do polling gap
# XAUUSD atingiu 1.67× ATR mas sistema só verificou a 1.03× ATR (gap de 30s) — TP1 nunca disparou
_PARTIAL_CLOSE_LEVELS_PSA = [
    {"atr": 1.0, "fraction": 0.25, "description": "TP1-1ATR",    "executed": False},  # era 1.5×
    {"atr": 2.5, "fraction": 0.25, "description": "TP2-2.5ATR",  "executed": False},  # era 3.0×
    {"atr": 4.0, "fraction": 0.25, "description": "TP3-4ATR",    "executed": False},  # era 5.0×
    {"atr": 6.0, "fraction": 0.15, "description": "TP4-6ATR",    "executed": False},  # era 8.0×
    # 10% residual sobrevive até TP final
]

# ── TRAILING STOP: geométrico por posição (PSA-WIND 30/04/2026) ──────────────
try:
    from modules.risk_valves_v31 import HardVolatilityTrailingStopGeometric as _TrailingStopCls
    _TRAILING_STOP_AVAILABLE = True
except Exception:
    _TRAILING_STOP_AVAILABLE = False
    _TrailingStopCls = None

# ── SPIKE DETECTION: bloquear entradas em anomalias (PSA-WIND 30/04/2026) ────
try:
    from modules.anomaly_detector import AnomalyDetector as _AnomalyDetectorCls
    _SPIKE_DETECTOR = _AnomalyDetectorCls()
    _SPIKE_DETECTION_AVAILABLE = True
except Exception:
    _SPIKE_DETECTOR = None
    _SPIKE_DETECTION_AVAILABLE = False

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

from datetime import datetime, timezone, timedelta
from math import floor, sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── OMEGA KERNEL v2.4.8 — ANALYSIS MODULES (compute_from_bars interface) ─────
import importlib as _importlib
_NEW_MODULE_ENGINES: Dict[str, Dict] = {}  # regime → {name: engine_instance}

_KERNEL_MODULE_MAP = [
    ("vof",        "modules.volume_order_flow"),
    ("footprint",  "modules.volume_footprint_engine"),
    ("sto_inst",   "modules.sto_institutional_detector"),
    ("sto_fused",  "modules.sto_fused_microstructure_engine"),
    ("pvsra",      "modules.pvsra_analyzer"),
    ("vwap",       "modules.vwap_engine"),
    ("pullback",   "modules.pullback_reentry_engine"),
    ("wyckoff",    "modules.wyckoff_analyzer"),
    ("liq_abs",    "modules.liquidity_absorption_engine"),
    ("elliott",    "modules.elliott_impulse_tracker_engine"),
    ("gap",        "modules.gap_analysis_tracker"),
    ("weis_wave",  "modules.weis_wave_tracker"),
    ("fimathe",    "modules.fimathe_breakout_engine"),
    ("pattern",    "modules.pattern_detector_engine"),
    ("micro",      "modules.microstructure_tracker"),
]

def _get_analysis_engines(regime: str) -> Dict:
    """Retorna (ou cria) instâncias dos módulos de análise para um dado regime."""
    if regime not in _NEW_MODULE_ENGINES:
        engs: Dict = {}
        for key, mod_path in _KERNEL_MODULE_MAP:
            try:
                mod = _importlib.import_module(mod_path)
                engs[key] = mod.ComponentEngine.from_config(regime=regime)
            except Exception:
                engs[key] = None
        _NEW_MODULE_ENGINES[regime] = engs
    return _NEW_MODULE_ENGINES[regime]

def _asset_regime(symbol: str) -> str:
    """Mapeia símbolo MT5 para regime OMEGA (forex/metal/crypto/index)."""
    s = symbol.upper()
    if any(c in s for c in ("XAU", "XAG", "OIL", "BRENT", "WTI")):
        return "commodity"
    if any(c in s for c in ("BTC", "ETH", "SOL", "DOG", "ADA", "XRP", "LTC", "BNB")):
        return "crypto"
    if any(c in s for c in ("US500", "NAS", "GER", "UK100", "JPN", "SP5", "DOW", "DAX")):
        return "index"
    return "forex"

# ─── Flow Confluence Scorer ───────────────────────────────────────────────────
def compute_flow_confluence(bar: Dict, symbol: str, direction: int, df=None) -> Tuple[float, Dict]:
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
                _score = float(vflow.score) if isinstance(vflow.score, (int, float)) else 50
                scores['v_flow'] = _score if vflow.direction == direction else 0
            else:
                scores['v_flow'] = 50
        else:
            scores['v_flow'] = 50
    except Exception as e:
        scores['v_flow'] = 50
    
    try:
        if _VOL_PHYSICS_ENGINE and hasattr(_VOL_PHYSICS_ENGINE, 'update'):
            # volume_physics: PhysicsState com trap_score, urgency
            state = _VOL_PHYSICS_ENGINE.update(bar.get('close', 0), bar.get('high', 0),
                                               bar.get('low', 0), bar.get('volume', 0))
            if hasattr(state, 'trap_score'):
                _trap = float(state.trap_score) if isinstance(state.trap_score, (int, float)) else 0.5
                # vol_phy semântica neutra (Auditoria IA 2026-05-09)
                # trap_score=0.0 → vol_phy=50 → neutro (sem pullback = sem opinião)
                # trap_score=0.5 → vol_phy=75 → sinal positivo moderado
                # trap_score=1.0 → vol_phy=100 → sinal máximo
                scores['vol_physics'] = 50.0 if _trap == 0.0 else min(50.0 + _trap * 50.0, 100.0)
            elif hasattr(state, 'urgency'):
                _urg = float(state.urgency.value) if isinstance(state.urgency.value, (int, float)) else 1.5
                scores['vol_physics'] = _urg * 33
            else:
                scores['vol_physics'] = 50
        else:
            scores['vol_physics'] = 50
    except Exception as e:
        scores['vol_physics'] = 50
    
    try:
        if _VOL_PROFILE_ENGINE and hasattr(_VOL_PROFILE_ENGINE, 'update'):
            # volume_profile: VolumeState com volume_ratio
            state = _VOL_PROFILE_ENGINE.update(symbol, bar)
            if hasattr(state, 'volume_ratio'):
                _ratio = float(state.volume_ratio) if isinstance(state.volume_ratio, (int, float)) else 1.0
                scores['vol_profile'] = min(_ratio * 50, 100)
            else:
                scores['vol_profile'] = 50
        else:
            scores['vol_profile'] = 50
    except Exception as e:
        scores['vol_profile'] = 50
    
    try:
        if _ANOMALY_ENGINE and hasattr(_ANOMALY_ENGINE, 'detect'):
            # anomaly_detector: AnomalyDetectionResult com severity
            result = _ANOMALY_ENGINE.detect(bar)
            if hasattr(result, 'severity'):
                _sev = float(result.severity) if isinstance(result.severity, (int, float)) else 0.5
                scores['anomaly'] = _sev * 100
            else:
                scores['anomaly'] = 50
        else:
            scores['anomaly'] = 50
    except Exception as e:
        scores['anomaly'] = 50
    
    try:
        if _MOMENTUM_ENGINE and hasattr(_MOMENTUM_ENGINE, 'update'):
            # momentum_physics: MomentumState com velocity
            state = _MOMENTUM_ENGINE.update(symbol, bar)
            if hasattr(state, 'velocity'):
                _vel = float(state.velocity) if isinstance(state.velocity, (int, float)) else 1.0
                scores['momentum'] = min(abs(_vel) * 50, 100)
            else:
                scores['momentum'] = 50
        else:
            scores['momentum'] = 50
    except Exception as e:
        scores['momentum'] = 50
    
    # Weighted confluence (legacy modules)
    confluence_legacy = sum(float(scores[k]) * weights[k] for k in weights)

    # ── MÓDULOS v2.4.8 — compute_from_bars(df) ──────────────────────────────
    if df is not None and not df.empty and len(df) >= 30:
        # Normalise MT5 OHLCV columns for microstructure_tracker compatibility
        _df_bars = df.copy()
        if "tick_volume" in _df_bars.columns and "volume" not in _df_bars.columns:
            _df_bars["volume"] = _df_bars["tick_volume"]
        if "is_buyer_maker" not in _df_bars.columns:
            _df_bars["is_buyer_maker"] = _df_bars["close"] >= _df_bars["open"]  # buyer bar = close >= open
        regime = _asset_regime(symbol)
        engines = _get_analysis_engines(regime)
        _new_weights = {
            "vof":       0.10, "footprint": 0.09,
            "sto_inst":  0.07, "sto_fused": 0.14, "pvsra":    0.07,
            "vwap":      0.11, "pullback":  0.10, "wyckoff":  0.08,
            "liq_abs":   0.09, "elliott":  0.15,
        }  # soma = 1.00
        for key, eng in engines.items():
            if eng is None:
                scores[key] = 50.0
                continue
            try:
                st = eng.compute_from_bars(_df_bars)
                if not st.is_valid:
                    scores[key] = 50.0
                else:
                    _dir = float(getattr(st, "direction", 0))
                    base = 50.0 + float(st.strength) * 50.0 * _dir
                    scores[key] = max(0.0, min(100.0, base))
            except Exception:
                scores[key] = 50.0
        new_conf = sum(scores[k] * _new_weights.get(k, 0.0) for k in _new_weights)
        # Blend: 30% módulos legados + 70% novos módulos
        confluence = 0.30 * confluence_legacy + 0.70 * new_conf
    else:
        confluence = confluence_legacy

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

# PSA v12 → dict para get_signal (MT5 + OHLCV; desligar: OMEGA_LOOP_PSA_V12=0)
_PSA_LOOP_FEED_AVAILABLE = False
compute_psa_decision_mt5 = None  # type: ignore[assignment]
if AGENT_IA_PATH.exists():
    try:
        from agent_ia.integration.shadow_loop_psa_feed import (
            compute_psa_decision_mt5 as _compute_psa_decision_mt5,
        )

        compute_psa_decision_mt5 = _compute_psa_decision_mt5
        _PSA_LOOP_FEED_AVAILABLE = True
    except Exception as _psa_feed_imp_err:
        print(f"[AVISO] PSA loop feed indisponível: {_psa_feed_imp_err}")

from modules.detection import SpoofIcebergDetector
from modules.portfolio import CorrelationFilter
from modules.mt5_position_tag import (
    build_v2_order_comment,
    filter_omega_tracked_positions,
    human_tag_line,
    is_omega_tracked_position,
)
from core_engines.intra_candle_executor import IntraCandleExecutor
from core_engines.omega_evaluation_context import build_evaluation_context, format_eval_log_line

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


def check_harmonic_ohlcv_inputs(asset: str, tf: str, base: Path) -> tuple[bool, list[str]]:
    """
    Ficheiros exigidos por omega_harmonic_engine_v3 (grafico_linha + grafico_candle).
    Evita subprocesso quando faltam CSVs; mensagens prontas para log/auditoria.
    """
    base = base.resolve()
    fname = f"{asset}_{tf}.csv"
    linha = base / "grafico_linha" / fname
    candle = base / "grafico_candle" / fname
    missing: list[str] = []
    if not linha.is_file():
        missing.append(f"Falta grafico_linha/{fname} → {linha}")
    if not candle.is_file():
        missing.append(f"Falta grafico_candle/{fname} → {candle}")
    return (len(missing) == 0, missing)


def _log_motor_v3_subprocess_failure(asset: str, tf: str, r: "subprocess.CompletedProcess[str]") -> None:
    err = (r.stderr or "").strip()
    out = (r.stdout or "").strip()
    max_chars = 12_000
    if len(err) > max_chars:
        err = err[:max_chars] + "\n... [stderr truncado — ver omega_harmonic_v3.log no CWD do motor]"
    if len(out) > max_chars:
        out = out[:max_chars] + "\n... [stdout truncado]"
    log.error("[%s %s] Motor V3 subprocess exit=%d", asset, tf, r.returncode)
    if err:
        log.error("[%s %s] Motor V3 stderr:\n%s", asset, tf, err)
    else:
        log.error("[%s %s] Motor V3 stderr: (vazio)", asset, tf)
    if out:
        log.warning("[%s %s] Motor V3 stdout:\n%s", asset, tf, out)

# ─── Configuração de Risco ───────────────────────────────────────────────────
DEMO_EQUITY_USD    = 10_000.0
RISK_PER_TRADE_PCT = float(os.getenv("OMEGA_RISK_PER_TRADE", "0.0100"))  # CEO 2026-05-14: 0.0025→0.0100 (0.25%→1.0% DEMO AGRESSIVO)
MIN_LOT_OVERRIDE   = float(os.getenv("OMEGA_MIN_LOT", "0.0"))            # CEO: lote mínimo (0=auto)
# 0 = sem limite (paper/testes). N>=1 = no máximo N posições OMEGA rastreadas (comment/mark).
MAX_POSITIONS      = int(os.getenv("OMEGA_MAX_POSITIONS", "0"))
MAX_POS_PER_ASSET  = int(os.getenv("OMEGA_MAX_POS_PER_ASSET", "0"))  # 0=ilimitado; 1=bloqueia duplicação por ativo
DD_DAILY_MAX       = float(os.getenv("OMEGA_DD_DAILY_MAX", "0.10"))       # CEO 2026-05-14: 0.01→0.10 (1%→10% DEMO AGRESSIVO)
CONCENTRATION_MAX  = float(os.getenv("OMEGA_CONCENTRATION_MAX", "0.40"))   # CQO/COO: max por ativo
MAX_CONSEC_FAIL    = 3
MAX_TP_SL_RATIO    = float(os.getenv("OMEGA_MAX_TP_SL_RATIO", "3.0"))  # C3 FIX: cap R:R máximo (era 59:1) | CEO 2026-05-14: 8.0→3.0 (US30 TP irrealista corrigido)
MIN_SL_ATR_MULT    = float(os.getenv("OMEGA_MIN_SL_ATR_MULT",  "1.0"))  # C3 FIX: SL mínimo em ATR

# ─── Perfis por Ativo (CQO 28/04/2026) ──────────────────────────────────────
# cost_pts    : spread+slippage+comissão mínimo para entrar (cost barrier)
# sl_atr_mult : SL = ATR × mult  (stop tighter em forex, wider em crypto)
# tp_atr_mult : TP = ATR × mult  (R/R: tp/sl)
# min_conf    : confiança mínima adicional por ativo (crypto exige mais)
# lot_cap     : lote máximo por ativo (independente do guardrail global)
# regime      : forex | commodity | index | crypto | crypto_alt
ASSET_PROFILES: dict = {
    # ── FOREX: spreads mínimos, session-bound, mean-reverting ──────────────
    "EURUSD": {"cost_pts":   3, "sl_atr_mult": 1.2, "tp_atr_mult": 2.5, "min_conf": 0.55, "lot_cap": 0.25, "sl_pts_min": 100, "regime": "forex"},
    "GBPUSD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 2.5, "min_conf": 0.55, "lot_cap": 0.25, "sl_pts_min": 150, "regime": "forex"},
    "AUDUSD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.55, "lot_cap": 0.20, "regime": "forex"},
    "USDCAD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.55, "lot_cap": 0.20, "regime": "forex"},
    "USDCHF": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.55, "lot_cap": 0.20, "regime": "forex"},
    "NZDUSD": {"cost_pts":   5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.0, "min_conf": 0.55, "lot_cap": 0.20, "regime": "forex"},
    # ── COMMODITIES: spreads médios, safe-haven/fluxos ──────────────────────
    "XAUUSD": {"cost_pts":  30, "sl_atr_mult": 0.7, "tp_atr_mult": 3.0, "min_conf": 0.58, "lot_cap": 0.30, "sl_pts_min": 150, "regime": "commodity"},  # CEO 2026-05-14: sl_atr_mult 1.2→0.7 (SL mais justo)
    "XAGUSD": {"cost_pts":  20, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.58, "lot_cap": 0.15, "regime": "commodity"},
    "UKOIL+": {"cost_pts":  30, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.58, "lot_cap": 0.10, "regime": "commodity"},
    "USOIL+": {"cost_pts":  30, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.58, "lot_cap": 0.10, "regime": "commodity"},
    # ── INDICES: gap risk, fluxos institucionais ─────────────────────────────
    "US500":  {"cost_pts":  10, "sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "min_conf": 0.58, "lot_cap": 0.50, "regime": "index"},   # CEO 2026-05-14: tp_mult 5→3, lot_cap 0.20→0.50
    "NAS100": {"cost_pts":  15, "sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "min_conf": 0.60, "lot_cap": 0.50, "regime": "index"},   # CEO 2026-05-14: tp_mult 5→3, lot_cap 0.15→0.50
    "US100":  {"cost_pts":  15, "sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "min_conf": 0.60, "lot_cap": 0.50, "regime": "index"},   # CEO 2026-05-14: tp_mult 5→3, lot_cap 0.15→0.50; Hantec alias NAS100
    "GER40":  {"cost_pts":  10, "sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "min_conf": 0.58, "lot_cap": 0.50, "regime": "index"},   # CEO 2026-05-14: tp_mult 5→3, lot_cap 0.20→0.50
    "UK100":  {"cost_pts":  12, "sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "min_conf": 0.58, "lot_cap": 0.50, "regime": "index"},   # CEO 2026-05-14: tp_mult 5→3, lot_cap 0.15→0.50
    "US30":   {"cost_pts":  10, "sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "min_conf": 0.58, "lot_cap": 0.50, "regime": "index"},   # CEO 2026-05-14: tp_mult 5→3, lot_cap 0.15→0.50
    # ── CRYPTO MAJOR: momentum, spread wide, 24/7 ───────────────────────────
    "BTCUSD": {"cost_pts": 100, "sl_atr_mult": 2.0, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.10, "sl_pts_min": 5000, "regime": "crypto"},  # BUG-3+C3 FIX 2026-05-11
    "ETHUSD": {"cost_pts":  50, "sl_atr_mult": 2.0, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.10, "sl_pts_min": 3000, "regime": "crypto"},  # BUG-3+C3 FIX 2026-05-11
    "SOLUSD": {"cost_pts":  30, "sl_atr_mult": 2.0, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.10, "regime": "crypto"},
    # ── CRYPTO ALT: alta volatilidade, spreads extremos ─────────────────────
    "DOGUSD": {"cost_pts": 200, "sl_atr_mult": 2.5, "tp_atr_mult": 8.0, "min_conf": 0.65, "lot_cap": 0.05, "regime": "crypto_alt"},
    # ── CRYPTO ALTS (ampliar leque; ajustar cost_pts ao broker real) ─────────
    "BNBUSD":   {"cost_pts":  80, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.15, "regime": "crypto_alt"},
    "LTCUSD":   {"cost_pts":  60, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.15, "regime": "crypto_alt"},
    # XRP: preço baixo → poucos USD por TP “em pontos”; TP mais longo em ATR (tp/sl) ou maior lote
    # (dentro do volume_max) compensa migalhas. cost_pts um pouco maior reduz entradas “ruidosas”.
    "XRPUSD":   {"cost_pts":  35, "sl_atr_mult": 2.0, "tp_atr_mult": 7.0, "min_conf": 0.65, "lot_cap": 0.10, "sl_pts_min": 200, "regime": "crypto_alt"},  # BUG-3+C3 FIX 2026-05-11 | CQO CAL 2026-05-12
    "ADAUSD":   {"cost_pts":  45, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.15, "regime": "crypto_alt"},
    "DOTUSD":   {"cost_pts":  45, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.12, "regime": "crypto_alt"},
    "AVAXUSD":  {"cost_pts":  55, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.12, "regime": "crypto_alt"},
    "LINKUSD":  {"cost_pts":  55, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.12, "regime": "crypto_alt"},
    "UNIUSD":   {"cost_pts":  70, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.10, "regime": "crypto_alt"},
    "ATOMUSD":  {"cost_pts":  55, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.10, "regime": "crypto_alt"},
    "NEARUSD":  {"cost_pts":  70, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "APTUSD":   {"cost_pts":  80, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "ARBUSD":   {"cost_pts":  70, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "OPUSD":    {"cost_pts":  70, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "FILUSD":   {"cost_pts":  80, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "MATICUSD": {"cost_pts":  70, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "POLUSD":   {"cost_pts":  70, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "TRXUSD":   {"cost_pts":  40, "sl_atr_mult": 2.1, "tp_atr_mult": 6.5, "min_conf": 0.58, "lot_cap": 0.20, "regime": "crypto_alt"},
    "XLMUSD":   {"cost_pts":  45, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.15, "regime": "crypto_alt"},
    "ETCUSD":   {"cost_pts":  60, "sl_atr_mult": 2.2, "tp_atr_mult": 7.0, "min_conf": 0.60, "lot_cap": 0.10, "regime": "crypto_alt"},
    "ALGOUSD":  {"cost_pts":  65, "sl_atr_mult": 2.3, "tp_atr_mult": 7.5, "min_conf": 0.62, "lot_cap": 0.08, "regime": "crypto_alt"},
    "VETUSD":   {"cost_pts":  90, "sl_atr_mult": 2.5, "tp_atr_mult": 8.0, "min_conf": 0.63, "lot_cap": 0.06, "regime": "crypto_alt"},
    # ── JPY MAJOR: carry-trade flow, direcional sem ruído ─────────────────────
    # Estratégia: USDJPY lidera → todas as crosses seguem a mesma direção JPY.
    # 500+ pips em movimento sustentado são comuns em eventos macro (BOJ/Fed).
    "USDJPY": {"cost_pts":  3, "sl_atr_mult": 1.2, "tp_atr_mult": 4.2, "min_conf": 0.55, "lot_cap": 0.25, "regime": "jpy_major"},
    # ── JPY CROSS: amplificam o movimento do USDJPY ────────────────────────────
    "EURJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.58, "lot_cap": 0.20, "sl_pts_min": 50, "regime": "forex"},
    "GBPJPY": {"cost_pts":  8, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.58, "lot_cap": 0.25, "regime": "jpy_cross"},
    "AUDJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.58, "lot_cap": 0.20, "sl_pts_min": 50, "regime": "forex"},
    "CADJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.58, "lot_cap": 0.25, "regime": "jpy_cross"},
    "CHFJPY": {"cost_pts":  5, "sl_atr_mult": 1.3, "tp_atr_mult": 4.5, "min_conf": 0.58, "lot_cap": 0.25, "regime": "jpy_cross"},
}
_PROFILE_DEFAULT = {"cost_pts": 19, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "min_conf": 0.55, "lot_cap": 0.10, "regime": "generic"}


def sanitize_sl_tp(sl_pts: float, tp_pts: float, atr_pts: float, asset: str) -> tuple:
    """
    C3 FIX: Garante SL/TP compatíveis com horizonte intraday.
    Previne R:R de 59:1 (harmonic swing vs intraday entry).
    """
    _sl_pts_min_atr = atr_pts * MIN_SL_ATR_MULT if atr_pts > 0 else sl_pts
    eff_sl = max(sl_pts, _sl_pts_min_atr)
    max_tp = eff_sl * MAX_TP_SL_RATIO
    eff_tp = min(tp_pts, max_tp)
    if tp_pts > max_tp:
        log.warning("[%s] TP CAP: harmónico %.0f → limitado a %.0f (R:R %.1f:1)",
                    asset, tp_pts, eff_tp, MAX_TP_SL_RATIO)
    if sl_pts < eff_sl and atr_pts > 0:
        log.warning("[%s] SL FLOOR: original %.0f → elevado a %.0f (min %.1fx ATR)",
                    asset, sl_pts, eff_sl, MIN_SL_ATR_MULT)
    return eff_sl, eff_tp


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

# ─── MARKET PROFILE: mapeamento shadow_regime → MP regime ───────────────────
# shadow_loop usa "commodity" para XAUUSD e Oil. MP usa "metal" para metais.
_MP_REGIME_MAP: dict = {
    "forex":      "forex",
    "jpy_major":  "jpy_major",
    "jpy_cross":  "jpy_cross",
    "commodity":  "commodity",   # XAUUSD/XAGUSD sobrescritos por função abaixo
    "metal":      "metal",
    "index":      "index",
    "crypto":     "crypto",
    "crypto_alt": "crypto_alt",
    "generic":    "forex",
}
_MP_METAL_ASSETS = {"XAUUSD", "XAGUSD"}

def _get_mp_regime(asset: str, shadow_regime: str) -> str:
    """Traduz regime shadow_loop → regime do Market Profile Engine."""
    if shadow_regime == "commodity" and asset in _MP_METAL_ASSETS:
        return "metal"
    return _MP_REGIME_MAP.get(shadow_regime, "forex")

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

# ─── CODE VERSION TRACKING (Forensic) ───────────────────────────────────────
# Cada ordem registra o SHA3 do código que a gerou para rastrear versão
import hashlib
import subprocess
def _get_code_sha3() -> str:
    """Calcula SHA3 do código atual para forensic tracking"""
    try:
        # SHA3 do shadow_loop.py (arquivo crítico)
        with open(__file__, "rb") as f:
            sha3 = hashlib.sha3_256(f.read()).hexdigest()
        return sha3[:12]  # Primeiros 12 caracteres
    except Exception:
        return "UNKNOWN"
CODE_SHA3 = _get_code_sha3()
print(f"[FORENSIC] CODE_SHA3={CODE_SHA3} — rastreamento de versão ativado")

# ─── Guardrails ─────────────────────────────────────────────────────────────
TIER1_ASSETS = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
                "XAUUSD", "XAGUSD", "UKOIL+", "USOIL+", "US500", "NAS100", "US100", "GER40", "UK100", "US30",
                "BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD",
                "BNBUSD", "LTCUSD", "XRPUSD", "ADAUSD", "DOTUSD", "AVAXUSD", "LINKUSD",
                "UNIUSD", "ATOMUSD", "NEARUSD", "APTUSD", "ARBUSD", "OPUSD", "FILUSD",
                "MATICUSD", "POLUSD", "TRXUSD", "XLMUSD", "ETCUSD", "ALGOUSD", "VETUSD",
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
    10004: "REQUOTE",
    10006: "REJECT",
    10007: "CANCEL",
    10009: "DONE",
    10010: "PLACED",
    10013: "INVALID_REQUEST",
    10014: "INVALID_VOLUME",
    10016: "INVALID_STOPS",
    10018: "MARKET_CLOSED",
    10019: "NO_MONEY",
    10024: "TOO_MANY_REQUESTS",
    10025: "NO_CHANGES",
    10030: "LIMIT_ORDERS",
}

# ─── Logging ─────────────────────────────────────────────────────────────────
# A-01 / D-04: não usar basicConfig — se o processo pai já configurou o root,
# basicConfig é no-op e o ficheiro fica 0 bytes. Handlers explícitos no logger "PAPER".
ts_str   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
log_file = AUDIT_PAPER / f"paper_loop_{ts_str}.log"
_log_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("PAPER")
log.setLevel(logging.INFO)
log.handlers.clear()
log.propagate = False
_fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
_fh.setFormatter(_log_fmt)
_sh = logging.StreamHandler()
_sh.setFormatter(_log_fmt)
log.addHandler(_fh)
log.addHandler(_sh)

# ── Startup: confirmar módulos carregados ao nível do módulo ────────────────
if _TESSERACT_AVAIL:
    log.info("[TESSERACT] Sniper v1.0 carregado — %s", _TESSERACT.version)
else:
    log.warning("[TESSERACT] Import falhou — módulo indisponível")


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
# Símbolos MT5 crypto — só uses os que existirem no teu broker (Market Watch).
_CRYPTO_ASSETS = {
    "BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD",
    "BNBUSD", "LTCUSD", "XRPUSD", "ADAUSD", "DOTUSD", "AVAXUSD", "LINKUSD",
    "UNIUSD", "ATOMUSD", "NEARUSD", "APTUSD", "ARBUSD", "OPUSD", "FILUSD",
    "MATICUSD", "POLUSD", "TRXUSD", "XLMUSD", "ETCUSD", "ALGOUSD", "VETUSD",
}
_METAL_ASSETS  = {"XAUUSD", "XAGUSD"}
_INDEX_ASSETS  = {"US500", "NAS100", "US100", "GER40", "UK100", "US30"}
# Calibrado 29/04/2026: dados reais mostram vol_ratio=0.19-0.28 na maior parte do tempo.
# 2026-05-03: crypto_alt em CFD (spread largo no M5) — atr/spr tipico 0.15-0.55 vs alvo antigo 2.85
# (bloqueava fallback em todos os ciclos). Defaults mais alinhados ao broker; endurecer via OMEGA_*.
_VOL_MIN_BY_CLASS = {
    "forex":      float(os.getenv("OMEGA_VOL_MIN_FOREX",       "0.10")),   # CEO 2026-05-14: 0.30→0.10 (dados reais: 0.19-0.28)
    "crypto":     float(os.getenv("OMEGA_VOL_MIN_CRYPTO",      "0.12")),   # CEO 2026-05-14: 0.18→0.12
    "crypto_alt": float(os.getenv("OMEGA_VOL_MIN_CRYPTO_ALT",  "0.08")),   # CEO 2026-05-14: 0.12→0.08
    "metal":      float(os.getenv("OMEGA_VOL_MIN_METAL",       "0.10")),   # CEO 2026-05-14: 0.30→0.10
    "index":      float(os.getenv("OMEGA_VOL_MIN_INDEX",       "0.10")),   # CEO 2026-05-14: 0.30→0.10
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
        "min_atr_pct":       float(os.getenv("OMEGA_EDGE_CRYPTO_ATR",    "0.00055")),
        "min_atr_over_spr":  float(os.getenv("OMEGA_EDGE_CRYPTO_SPR",    "2.5")),
        "min_adx":           float(os.getenv("OMEGA_EDGE_CRYPTO_ADX",    "15.0")),
    },
    "crypto_alt": {
        "min_atr_pct":       float(os.getenv("OMEGA_EDGE_CRYPTOALT_ATR", "0.00045")),
        "min_atr_over_spr":  float(os.getenv("OMEGA_EDGE_CRYPTOALT_SPR", "0.18")),
        "min_adx":           float(os.getenv("OMEGA_EDGE_CRYPTOALT_ADX", "14.0")),
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
        "min_atr_pct":       float(os.getenv("OMEGA_EDGE_INDEX_ATR",    "0.0005")),  # CEO 2026-05-14: 0.0008→0.0005 (GER40 bloqueado 0.076%<0.080%)
        "min_atr_over_spr":  float(os.getenv("OMEGA_EDGE_INDEX_SPR",    "2.0")),     # CEO 2026-05-14: 3.0→2.0
        "min_adx":           float(os.getenv("OMEGA_EDGE_INDEX_ADX",    "13.0")),    # CEO 2026-05-14: 15.0→13.0
    },
}

def classify_asset(symbol: str) -> str:
    """Classifica ativo para EDGE_GATE / volume (CTO spec + perfil ASSET_PROFILES)."""
    s = symbol.upper()
    prof = ASSET_PROFILES.get(s)
    if prof:
        r = str(prof.get("regime", "") or "").lower()
        if r in ("crypto", "crypto_alt"):
            return r
    if s in _CRYPTO_ASSETS:
        return "crypto"
    if s in _METAL_ASSETS:
        return "metal"
    if s in _INDEX_ASSETS:
        return "index"
    return "forex"


def min_expected_tp_usd_threshold(asset: str) -> float:
    """
    Lucro esperado mínimo (moeda da conta, tipicamente USD) se o TP for atingido,
    estimado linearmente como: TP_pts × pip_value_per_lot × lot (igual ao uso de _risk_usd_eff).
    0 = filtro desligado para essa camada.

    Defaults (2026-05): crypto_alt = 1.25 USD — evita cenário “6000 pts = $0.58” em CFD alts.
    Desligar: OMEGA_MIN_TP_USD_CRYPTO_ALT=0
    """
    g = float(os.getenv("OMEGA_MIN_TP_USD", "0") or 0)
    cls = classify_asset(asset)
    if cls == "crypto_alt":
        g = max(g, float(os.getenv("OMEGA_MIN_TP_USD_CRYPTO_ALT", "1.25") or 0))
    elif cls == "crypto":
        g = max(g, float(os.getenv("OMEGA_MIN_TP_USD_CRYPTO", "0") or 0))
    return float(g)


def min_lot_floor_for_regime(regime: str) -> float:
    """Piso de lote (0=desligado). crypto_alt típico 0.08–0.10 em CFD com TP realista mas USD baixo."""
    r = str(regime or "").lower()
    if r == "crypto_alt":
        return float(os.getenv("OMEGA_MIN_LOT_CRYPTO_ALT", "0") or 0)
    if r == "crypto":
        return float(os.getenv("OMEGA_MIN_LOT_CRYPTO", "0") or 0)
    return 0.0


def decision_trace_enabled() -> bool:
    return os.getenv("OMEGA_DECISION_TRACE", "0").strip().lower() in ("1", "true", "yes", "on")


def decision_trace_append(row: dict) -> None:
    """
    Uma linha JSON por evento em audit/paper/decision_trace.jsonl.
    Ativar: OMEGA_DECISION_TRACE=1 (PowerShell: $env:OMEGA_DECISION_TRACE='1')
    """
    if not decision_trace_enabled():
        return
    r = dict(row)
    r.setdefault("ts", datetime.now(timezone.utc).isoformat())
    try:
        with open(AUDIT_PAPER / "decision_trace.jsonl", "a", encoding="utf-8") as tf:
            tf.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        log.debug("decision_trace append failed: %s", e)


def trade_feedback_append(row: dict) -> None:
    """
    Uma linha JSON por trade fechado (ledger) em audit/paper/trade_feedback.jsonl.
    Fecho de loop mensurável: fonte do sinal, agent_id (se IA), PnL, R, duração —
    independente de OMEGA_DECISION_TRACE; use para auditar sync opens vs closes.
    """
    r = dict(row)
    r.setdefault("ts", datetime.now(timezone.utc).isoformat())
    try:
        with open(AUDIT_PAPER / "trade_feedback.jsonl", "a", encoding="utf-8") as tf:
            tf.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        log.debug("trade_feedback append failed: %s", e)


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
    Reutiliza sessão MT5 existente (run_loop já fez mt5.initialize()).
    Cripto: não exige `session_deals` — vários brokers deixam o campo vazio ao fim de
    semana mesmo com CFD crypto negociável 24/7."""
    import MetaTrader5 as mt5
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        return False
    tick = mt5.symbol_info_tick(symbol)
    if symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL or tick is None:
        return False
    if symbol in _CRYPTO_ASSETS:
        return True
    return symbol_info.session_deals is not None


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

    lot_norm, vol_note = normalize_mt5_volume(lot, sym, asset)
    if vol_note:
        log.warning("[%s %s] [VOLUME] %s", asset, tf, vol_note)
    if lot_norm <= 0 or lot_norm + 1e-12 < float(getattr(sym, "volume_min", 0.01) or 0.01):
        log.error(
            "[%s %s] volume inválido após normalização MT5: lot_in=%s lot_out=%s min=%s max=%s step=%s",
            asset,
            tf,
            lot,
            lot_norm,
            getattr(sym, "volume_min", None),
            getattr(sym, "volume_max", None),
            getattr(sym, "volume_step", None),
        )
        return {
            "retcode": -1,
            "retcode_str": "INVALID_VOLUME",
            "error": "volume fora dos limites do contrato (min/max/step)",
            "success": False,
        }
    lot = lot_norm

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
        "comment":      build_v2_order_comment(tf, direction),
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


# ─── MT5 — Modificar SL/TP de Posição Aberta ────────────────────────────────
def mt5_modify_position_sl(ticket: int, symbol: str, new_sl: float, new_tp: float = 0.0) -> dict:
    """
    Modifica SL (e opcionalmente TP) de uma posição aberta via TRADE_ACTION_SLTP.
    Chamado pelo trailing stop a cada actualização do peak price.
    Retorna dict com success, retcode, latency_ms.
    """
    import MetaTrader5 as mt5
    sym = mt5.symbol_info(symbol)
    if sym is None:
        log.error("[MT5_MODIFY_SL] %s symbol_info None", symbol)
        return {"success": False, "error": "symbol_info None"}

    digits = sym.digits
    new_sl_r = round(new_sl, digits)
    new_tp_r = round(new_tp, digits) if new_tp > 0 else 0.0

    # PSA Conselho 2026-05-15: evitar 620× TRADE_RETCODE_NO_CHANGES (10025) —
    # servidor rejeita SLTP idêntico ao já gravado; não é perda, é ruído/carga.
    _pos_list = mt5.positions_get(ticket=ticket)
    if _pos_list:
        _p0 = _pos_list[0]
        _cur_sl = round(float(_p0.sl), digits) if _p0.sl else 0.0
        _cur_tp = round(float(_p0.tp), digits) if _p0.tp else 0.0
        if new_sl_r == _cur_sl and new_tp_r == _cur_tp:
            return {
                "success": True,
                "retcode": 0,
                "new_sl": new_sl_r,
                "latency_ms": 0.0,
                "skipped_noop": True,
                "note": "SL/TP já iguais no servidor — order_send omitido",
            }

    request = {
        "action":   mt5.TRADE_ACTION_SLTP,
        "symbol":   symbol,
        "position": ticket,
        "sl":       new_sl_r,
        "tp":       new_tp_r,
    }

    t0     = time.perf_counter()
    result = mt5.order_send(request)
    lat_ms = round((time.perf_counter() - t0) * 1000, 1)

    if result is None:
        err = mt5.last_error()
        log.error("[MT5_MODIFY_SL] %s #%d order_send None: %s", symbol, ticket, err)
        return {"success": False, "error": str(err), "latency_ms": lat_ms}

    r       = result._asdict()
    retcode = r.get("retcode", -1)
    success = retcode in RETCODE_OK
    if success:
        log.info("[MT5_MODIFY_SL] %s #%d ✅ SL=%.5f (%.1fms)", symbol, ticket, new_sl_r, lat_ms)
    else:
        # 10025 = NO_CHANGES: não alarmar em INFO (CEO 2026-05-15); noop acima já filtra a maioria.
        if retcode == 10025:
            log.debug("[MT5_MODIFY_SL] %s #%d retcode=10025 NO_CHANGES (servidor) — %s",
                      symbol, ticket, RETCODE_DESC.get(retcode, ""))
        else:
            log.warning("[MT5_MODIFY_SL] %s #%d ❌ retcode=%d (%s)",
                        symbol, ticket, retcode, RETCODE_DESC.get(retcode, f"UNKNOWN_{retcode}"))
    return {"success": success, "retcode": retcode, "new_sl": new_sl_r, "latency_ms": lat_ms}


# ─── MT5 — Fechar Posição Parcial ou Total ───────────────────────────────────
def mt5_close_partial(ticket: int, symbol: str, lots: float, direction: str) -> dict:
    """
    Fecha parcialmente (ou totalmente) uma posição aberta via TRADE_ACTION_DEAL oposto.
    direction = "BUY" ou "SELL" (direcção da posição existente — a ordem de fecho é oposta).
    Retorna dict com success, retcode, fill_price, latency_ms.
    """
    import MetaTrader5 as mt5
    tick = mt5.symbol_info_tick(symbol)
    sym  = mt5.symbol_info(symbol)
    if tick is None or sym is None:
        log.error("[MT5_CLOSE_PARTIAL] %s symbol_info/tick None", symbol)
        return {"success": False, "error": "symbol_info None"}

    lot_norm, vol_note = normalize_mt5_volume(lots, sym, symbol)
    if vol_note:
        log.warning("[MT5_CLOSE_PARTIAL] %s #%d volume note: %s", symbol, ticket, vol_note)
    if lot_norm <= 0 or lot_norm + 1e-12 < float(getattr(sym, "volume_min", 0.01) or 0.01):
        log.error("[MT5_CLOSE_PARTIAL] %s #%d volume inválido após normalize: %.4f", symbol, ticket, lot_norm)
        return {"success": False, "error": "invalid volume after normalize"}

    if direction == "BUY":
        close_type = mt5.ORDER_TYPE_SELL
        price      = tick.bid
    else:
        close_type = mt5.ORDER_TYPE_BUY
        price      = tick.ask

    fm = sym.filling_mode if sym else 3
    if fm & 2:    filling = mt5.ORDER_FILLING_IOC
    elif fm & 1:  filling = mt5.ORDER_FILLING_FOK
    else:         filling = mt5.ORDER_FILLING_RETURN

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       lot_norm,
        "type":         close_type,
        "position":     ticket,
        "price":        price,
        "deviation":    20,
        "comment":      "OMEGA_PARTIAL_CLOSE",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": filling,
    }

    t0     = time.perf_counter()
    result = mt5.order_send(request)
    lat_ms = round((time.perf_counter() - t0) * 1000, 1)

    if result is None:
        err = mt5.last_error()
        log.error("[MT5_CLOSE_PARTIAL] %s #%d order_send None: %s", symbol, ticket, err)
        return {"success": False, "error": str(err), "latency_ms": lat_ms}

    r       = result._asdict()
    retcode = r.get("retcode", -1)
    success = retcode in RETCODE_OK
    if success:
        log.info("[MT5_CLOSE_PARTIAL] %s #%d ✅ %.2f lotes @ %.5f (%.1fms)",
                 symbol, ticket, lot_norm, r.get("price", price), lat_ms)
    else:
        log.warning("[MT5_CLOSE_PARTIAL] %s #%d ❌ retcode=%d (%s)",
                    symbol, ticket, retcode, RETCODE_DESC.get(retcode, f"UNKNOWN_{retcode}"))
    return {"success": success, "retcode": retcode,
            "fill_price": r.get("price", price), "volume": lot_norm, "latency_ms": lat_ms}


# ─── Rodar Motor Harmônico ────────────────────────────────────────────────────
def run_harmonic(asset: str, tf: str, margin: float, out_dir: Path) -> Optional[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ok_paths, missing_msgs = check_harmonic_ohlcv_inputs(asset, tf, OHLCV)
    if not ok_paths:
        log.error(
            "[%s %s] OHLCV Motor V3 — pré-checagem falhou (OMEGA_OHLCV_PATH=%s):\n  %s",
            asset,
            tf,
            OHLCV,
            "\n  ".join(missing_msgs),
        )
        log.error(
            "[%s %s] Correr: python scripts/export_ohlcv_mt5.py --symbols %s --timeframes %s",
            asset,
            tf,
            asset,
            tf,
        )
        return None
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
            _log_motor_v3_subprocess_failure(asset, tf, r)
            return None
        jf = out_dir / f"harmonic_events_{asset}_{tf}.json"
        if not jf.exists():
            log.error(
                "[%s %s] Motor V3 exit=0 mas JSON ausente: %s (verificar permissões/CWD)",
                asset,
                tf,
                jf,
            )
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
        "sym_vol_max":    resolve_mt5_volume_max(sym, asset),
        "sym_vol_step":   float(getattr(sym, "volume_step", 0) or 0.01),
    }


_VOLMAX_FALLBACK_LOGGED: set[str] = set()


def resolve_mt5_volume_max(sym, asset: str) -> float:
    """
    volume_max vindo do MT5; se <=0 em CFD crypto, muitos brokers não preenchem o campo
    mas o limite real é baixo — não usar 100.0 (isso reintroduz 0.25 → Invalid volume).
    """
    raw = float(getattr(sym, "volume_max", 0) or 0.0)
    if raw > 0:
        return raw
    a = (asset or "").upper()
    prof = ASSET_PROFILES.get(a) if a else None
    regime = str(prof.get("regime", "") if prof else "").lower()
    is_crypto = (a in _CRYPTO_ASSETS) or regime in ("crypto", "crypto_alt")
    if is_crypto:
        fb = float(os.getenv("OMEGA_CRYPTO_VOLUME_MAX_FALLBACK", "0.10"))
        if a and a not in _VOLMAX_FALLBACK_LOGGED:
            _VOLMAX_FALLBACK_LOGGED.add(a)
            log.warning(
                "[%s] MT5 volume_max<=0 — usar OMEGA_CRYPTO_VOLUME_MAX_FALLBACK=%.4f "
                "(ajuste o env se o broker permitir mais)",
                a,
                fb,
            )
        return fb
    return float(os.getenv("OMEGA_VOLUME_MAX_FALLBACK", "100.0"))


def _mt5_volume_decimals(volume_step: float) -> int:
    """Casas decimais coerentes com volume_step (evita 0.30000000004 no request)."""
    try:
        s = f"{float(volume_step):.12f}".rstrip("0").rstrip(".")
        return len(s.split(".")[1]) if "." in s else 0
    except Exception:
        return 2


def normalize_mt5_volume(lot: float, sym, asset: str = "") -> Tuple[float, str]:
    """
    Alinha volume a volume_min / volume_max / volume_step do símbolo MT5.
    Evita retcode 10014 / journal \"Invalid volume\" (ex.: ETHUSD max 0.10 com pedido 0.25).
    """
    if sym is None or not isinstance(lot, (int, float)):
        return 0.0, "sym_none_or_lot_invalid"
    raw = float(lot)
    if raw <= 0:
        return 0.0, "lot<=0"
    vmin = float(getattr(sym, "volume_min", 0.01) or 0.01)
    vmax = resolve_mt5_volume_max(sym, asset)
    vstep = float(getattr(sym, "volume_step", 0.01) or 0.01)
    if vmin <= 0:
        vmin = 0.01
    if vstep <= 0:
        vstep = 0.01
    if vmax < vmin:
        vmax = vmin

    clamped = max(vmin, min(raw, vmax))
    n = int(floor((clamped - vmin) / vstep + 1e-12))
    out = vmin + n * vstep
    if out > vmax + 1e-12:
        nmax = int(floor((vmax - vmin) / vstep + 1e-12))
        out = vmin + max(0, nmax) * vstep
    nd = min(8, max(0, _mt5_volume_decimals(vstep)))
    out = float(round(out, nd))
    adj = ""
    if abs(out - raw) > max(1e-9, 10 ** (-(nd + 2))):
        adj = (
            f"volume MT5 ajustado: pedido={raw} efetivo={out} "
            f"(min={vmin} max={vmax} step={vstep})"
        )
    return out, adj


# ─── CEO ORDER: CASCATA MACRO W1→D1→H4→H1→M15 ─────────────────────────────────
# CEO Decision (04/05/2026): sistema DEVE usar cascata completa semanal→diária→intraday.
# W1 = direcção macro da semana (peso 3), D1 = tendência do dia (peso 2),
# H4 = estrutura (peso 2), H1 = setup (peso 1), M15 = confirmação de entrada (peso 1).
# M15 confluência → executar em M3/M1.
MTF_ALIGN_THR = float(os.getenv("OMEGA_MTF_ALIGN_THR", "0.50"))  # 50% — bloqueia sinal OPOSTO a macro forte
# FIX #4-REV (CEO 2026-05-14 rev): alinhamento MINIMO para aceitar qualquer sinal.
# Formula: (peso_a_favor - peso_contra) / 9. W1=3,D1=2,H4=2,H1=1,M15=1.
# Com W1 oposto, maximo alcancavel = (2+2+1+1-3)/9 = 33%.
# 60% bloqueava TODOS os sinais intraday com W1 oposto (pullbacks legitimos).
# Novo threshold = 0.20: bloqueia 11% (2 TFs contra W1 pesado) mas permite 33% (4 TFs a favor).
MTF_ALIGN_MIN = float(os.getenv("OMEGA_MTF_ALIGN_MIN", "0.20"))  # 20% minimo — bloqueia so conflito grave


def effective_mtf_align_min(tf: str) -> float:
    """
    PSA/Conselho 2026-05-15: limiar MTF pode ser relaxado só em TFs intraday (ex.: M15)
    para reduzir SKIP_MTF_LOW_ALIGN dominante, sem afrouxar H4/D1 em todos os casos.
    OMEGA_MTF_ALIGN_MIN_INTRADAY — vazio = usar MTF_ALIGN_MIN para todos.
    OMEGA_MTF_RELAX_TFS — lista separada por vírgulas (default M15).
    """
    intra = os.getenv("OMEGA_MTF_ALIGN_MIN_INTRADAY", "").strip()
    if not intra:
        return MTF_ALIGN_MIN
    try:
        intra_f = float(intra)
    except ValueError:
        return MTF_ALIGN_MIN
    relax_raw = os.getenv("OMEGA_MTF_RELAX_TFS", "M15")
    relax_tfs = {x.strip().upper() for x in relax_raw.split(",") if x.strip()}
    if (tf or "").strip().upper() in relax_tfs:
        return max(0.0, min(1.0, intra_f))
    return MTF_ALIGN_MIN


def get_multi_tf_bias(symbol: str) -> dict:
    """
    CEO Order 04/05/2026: Cascata completa W1→D1→H4→H1→M15.
    Pesos default: W1=3, D1=2, H4=2, H1=1, M15=1 — sobrescrevíveis por env
    OMEGA_MTF_W1_WEIGHT, OMEGA_MTF_D1_WEIGHT, OMEGA_MTF_H4_WEIGHT,
    OMEGA_MTF_H1_WEIGHT, OMEGA_MTF_M15_WEIGHT (PSA/Conselho 2026-05-15).
    alignment = abs(weighted_score) / total_weight dos TFs com dados.
    """
    import MetaTrader5 as mt5
    import numpy as np
    # Pesos configuráveis (PSA/Conselho 2026-05-15): reduzir W1 (ex.: 3→2) aumenta alinhamento
    # quando só a semana opõe ao intraday — trade-off documentado em OMEGA-DOC-REGISTRY.
    _w_w1 = float(os.getenv("OMEGA_MTF_W1_WEIGHT", "3"))
    _w_d1 = float(os.getenv("OMEGA_MTF_D1_WEIGHT", "2"))
    _w_h4 = float(os.getenv("OMEGA_MTF_H4_WEIGHT", "2"))
    _w_h1 = float(os.getenv("OMEGA_MTF_H1_WEIGHT", "1"))
    _w_m15 = float(os.getenv("OMEGA_MTF_M15_WEIGHT", "1"))
    TFS = [
        (mt5.TIMEFRAME_W1,  "W1",  30, _w_w1),
        (mt5.TIMEFRAME_D1,  "D1",  50, _w_d1),
        (mt5.TIMEFRAME_H4,  "H4",  50, _w_h4),
        (mt5.TIMEFRAME_H1,  "H1",  50, _w_h1),
        (mt5.TIMEFRAME_M15, "M15", 50, _w_m15),
    ]
    weighted_score = 0
    total_weight   = 0
    detail = {}
    for tf_const, tf_name, n, weight in TFS:
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, n)
            if rates is None or len(rates) < 22:
                detail[tf_name] = "no_data"
                continue
            closes = np.array([r['close'] for r in rates], dtype=float)
            ema8   = float(np.mean(closes[-8:]))
            ema21  = float(np.mean(closes[-21:]))
            s = 1 if ema8 > ema21 else -1
            weighted_score += s * weight
            total_weight   += weight
            detail[tf_name] = "BUY" if s > 0 else "SELL"
        except Exception as _e:
            detail[tf_name] = f"err:{_e}"
    if total_weight == 0:
        return {"bias": "NEUTRAL", "score": 0, "alignment": 0.0, "detail": detail}
    alignment = abs(weighted_score) / total_weight
    bias      = "BUY" if weighted_score > 0 else ("SELL" if weighted_score < 0 else "NEUTRAL")
    return {"bias": bias, "score": weighted_score, "alignment": round(alignment, 2),
            "n_tfs": len([v for v in detail.values() if v in ("BUY", "SELL")]), "detail": detail}


def get_key_levels(symbol: str) -> dict:
    """
    CEO Order 04/05/2026: Calcula níveis-chave para preparar TP/SL no gráfico menor.
    Retorna:
      prev_week_high / prev_week_low   — extremos da semana anterior (W1 bars[1])
      prev_day_high / prev_day_low     — extremos do dia anterior (D1 bars[1])
      prev_day_close                   — fecho do dia anterior (âncora de defesa)
      today_open                       — abertura de hoje (D1 bars[0])
      gap_pts / gap_dir                — GAP entre abertura de hoje e fecho anterior
      gap_fill_level                   — nível de preço a atingir para fechar o GAP
      poc_price                        — POC da sessão actual (volume footprint)
    """
    import MetaTrader5 as mt5
    import numpy as np
    result = {
        "prev_week_high": None, "prev_week_low": None,
        "prev_day_high":  None, "prev_day_low":  None,
        "prev_day_close": None, "today_open":    None,
        "gap_pts": 0.0, "gap_dir": "NONE", "gap_fill_level": None,
        "poc_price": None,
    }
    try:
        sym_info = mt5.symbol_info(symbol)
        pt = sym_info.point if sym_info else 1e-5
        # W1: semana anterior (index 1 = barra anterior fechada)
        w1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_W1, 1, 1)
        if w1 is not None and len(w1) >= 1:
            result["prev_week_high"] = float(w1[0]["high"])
            result["prev_week_low"]  = float(w1[0]["low"])
        # D1: dia anterior (index 1) e hoje (index 0)
        d1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 2)
        if d1 is not None and len(d1) >= 2:
            result["today_open"]    = float(d1[0]["open"])
            result["prev_day_close"]= float(d1[1]["close"])
            result["prev_day_high"] = float(d1[1]["high"])
            result["prev_day_low"]  = float(d1[1]["low"])
            # GAP: diferença entre abertura de hoje e fecho de ontem
            gap_raw = result["today_open"] - result["prev_day_close"]
            result["gap_pts"] = round(gap_raw / pt, 1)
            if abs(result["gap_pts"]) > 5:  # GAP mínimo de 5 pts
                result["gap_dir"] = "UP" if gap_raw > 0 else "DOWN"
                result["gap_fill_level"] = result["prev_day_close"]  # preço-alvo de fecho do GAP
        # POC: do volume footprint se disponível
        try:
            h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 30)
            if h1_rates is not None and len(h1_rates) >= 10:
                closes_h1  = np.array([r["close"]       for r in h1_rates], dtype=float)
                volumes_h1 = np.array([r["tick_volume"] for r in h1_rates], dtype=float)
                bins = np.linspace(closes_h1.min(), closes_h1.max(), 20)
                counts, edges = np.histogram(closes_h1, bins=bins, weights=volumes_h1)
                poc_idx = int(np.argmax(counts))
                result["poc_price"] = round(float((edges[poc_idx] + edges[poc_idx + 1]) / 2), 5)
        except Exception:
            pass
    except Exception as _e:
        result["error"] = str(_e)
    return result


def get_execution_tf_atr(symbol: str, confidence: float = 0.70) -> dict:
    """
    Seleciona TF de execução (M3 padrão, M1 se confidence >= 0.80).
    Calcula ATR para SL/TP tight no TF de execução.
    CQO Spec: M3 reduz ruído 67% vs M1, mantém antecipação de spikes.
    M1 reservado para sinais de alta confiança (>= 0.80).
    MULTI-TIMEFRAME: D1 (macro) + H4 (estrutura) + H1 (setup) + M15 (confirmação)
    EXECUÇÃO: M3/M1 para S/L mais barato, várias entradas, gatilhos reais
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
# MULTI-TIMEFRAME: D1 (macro) + H4 (estrutura) + H1 (setup) + M15 (confirmação)
# EXECUÇÃO: M3/M1 para S/L mais barato, várias entradas, gatilhos reais

def get_jpy_cluster_signal(min_alignment: float = 0.75) -> dict:
    """
    Lê USDJPY em D1+H4+H1+M15 e propaga sinal de cluster para todas as crosses.
    Retorna direção do JPY e se o cluster está ativo.
    Nota: direção=BUY significa USD fortalece (USDJPY sobe) →
          crosses JPY como EURJPY/GBPJPY também sobem (EUR/GBP vs JPY).
    MULTI-TIMEFRAME INTEGRADO: D1 (macro visão) → H4 (estrutura) → H1 (setup) → M15 (confirmação)
    EXECUÇÃO: M3/M1 para entrada com S/L tight (conf >= 0.80 usa M1, senão M3)
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
# CEO 2026-05-14: Pyramid PROGRESSIVO — volume AUMENTA por camada (1.5x, 2.0x)
# Motivo: múltiplas ordens mesmo volume é ineficiente; confirmar direção → aumentar exposição
PYRAMID_LOT_SCALE = float(os.getenv("OMEGA_PYRAMID_LOT_SCALE", "1.5"))  # multiplicador por camada

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
    # Suporte a MT5 TradePosition (atributo) e dict (.get)
    def _attr(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    # Mapear direction MT5: type=0 → BUY, type=1 → SELL
    def _dir(obj):
        d = _attr(obj, "direction")
        if d is not None:
            return d
        t = _attr(obj, "type")
        if t is not None:
            return "BUY" if t == 0 else "SELL"
        return None
    same_dir = [p for p in open_positions
                if _attr(p, "symbol") == symbol and _dir(p) == direction]
    if not same_dir:
        return {"add": False, "reason": "no_same_dir_position"}
    # Contar layers atuais para este símbolo+direção
    current_layers = len(same_dir)
    if current_layers >= PYRAMID_MAX_LAYERS:
        return {"add": False, "reason": f"max_layers={PYRAMID_MAX_LAYERS}", "layer": current_layers}
    # Verificar lucro acumulado da posição mais antiga
    best_pos = max(same_dir, key=lambda p: _attr(p, "profit", _attr(p, "last_profit", 0)))
    atr_pts   = exec_atr.get("atr_pts", 0)
    trigger   = atr_pts * PYRAMID_TRIGGER_ATR
    _best_profit = _attr(best_pos, "profit", _attr(best_pos, "last_profit", 0))
    if _best_profit < trigger:
        return {"add": False, "reason": f"profit={_best_profit:.2f}<trigger={trigger:.1f}pts",
                "layer": current_layers}
    # Verificar tendência forte antes de pyramidar
    ts = get_trend_strength(symbol, direction)
    if not ts.get("pyramid_ok"):
        return {"add": False, "reason": f"trend_score={ts['score']:.2f}<min", "layer": current_layers}
    # Lote PROGRESSIVO: cada camada é PYRAMID_LOT_SCALE × a anterior (CEO 2026-05-14)
    # Antes: 0.75^layer (regressivo — camadas menores = ineficiente)
    # Agora: 1.5^layer (progressivo — confirmação direcional → maior exposição)
    # Teto: lot_cap do activo para não ultrapassar limite de risco
    base_lot = prof.get("lot_cap", 0.10)
    layer_lot = round(base_lot * (PYRAMID_LOT_SCALE ** current_layers), 2)
    sym_info  = None
    try:
        import MetaTrader5 as mt5
        sym_info = mt5.symbol_info(symbol)
    except Exception:
        pass
    min_lot = sym_info.volume_min if sym_info else 0.01
    max_lot = sym_info.volume_max if sym_info else base_lot * 3
    # Clampar entre min_lot e lot_cap (não exceder teto de risco do activo)
    layer_lot = max(min_lot, min(layer_lot, base_lot, max_lot))
    return {
        "add":           True,
        "lot":           layer_lot,
        "layer":         current_layers + 1,
        "trend_score":   ts["score"],
        "trigger_pts":   trigger,
        "profit_pts":    _best_profit,
        "reason":        f"pyramid_layer{current_layers+1}_LOT{layer_lot:.2f} score={ts['score']:.2f}",
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
    def update(self, success: bool, pnl_usd: float = 0.0, retcode: int | None = None) -> bool:
        if self.triggered: return True
        self.daily_pnl += pnl_usd
        if not success:
            # CEO OIS-20260517: MARKET_CLOSED (10018) não incrementa streak — KS não dispara por mercado fechado.
            if retcode == 10018:
                log.info(
                    "KILL SWITCH streak: ignorando falha MARKET_CLOSED (retcode=10018) — consec_fail=%d",
                    self.consec_fail,
                )
            else:
                self.consec_fail += 1
        else:
            self.consec_fail = 0
        if abs(self.daily_pnl) / self.equity >= DD_DAILY_MAX:
            self.reason = f"DD diário {abs(self.daily_pnl)/self.equity*100:.2f}% ≥ {DD_DAILY_MAX*100:.0f}%"
            self.triggered = True; log.critical("💀 KILL SWITCH: %s", self.reason)
        if self.consec_fail >= MAX_CONSEC_FAIL:
            self.reason = f"{self.consec_fail} falhas consecutivas"
            self.triggered = True; log.critical("💀 KILL SWITCH: %s", self.reason)
        return self.triggered


def classify_cycle_exit_reason(
    ks: KillSwitch,
    *,
    early_error: str | None = None,
    persistent_halt: bool = False,
    persistent_detail: str = "",
) -> tuple[str, str]:
    """Código estável de saída por ciclo/run (CEO OIS-20260517 — forensics vs Journal MT5)."""
    kr = (ks.reason or "").strip()
    if persistent_halt:
        return "PERSISTENT_DD_HALT", (persistent_detail or kr or "persistent kill-switch")
    if early_error:
        return "MT5_UNAVAILABLE", early_error
    if ks.triggered:
        if kr.startswith("CB:"):
            return "CIRCUIT_BREAKER_TRIP", kr
        if kr.upper() == "TAIL_RISK_HALT" or "TAIL_RISK" in kr.upper():
            return "TAIL_RISK_HALT", kr
        if "DD diário" in kr:
            return "KILL_SWITCH_DAILY_DD", kr
        if "falhas consecutivas" in kr:
            return "KILL_SWITCH_CONSECUTIVE_FAIL", kr
        return "KILL_SWITCH_OTHER", kr or "triggered_without_detail"
    return "NORMAL_COMPLETION", ""


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


def _append_evaluation_timeline_row(audit_dir: Path, row: dict) -> None:
    """Uma linha por evento de run — cruza data/dia/semana/peso com exit_reason (regra avaliação CIO)."""
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
        _p = audit_dir / "evaluation_timeline.jsonl"
        with open(_p, "a", encoding="utf-8") as _tf:
            _tf.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as _tl_err:
        log.warning("evaluation_timeline.jsonl: %s", _tl_err)


# ─── Loop Principal ───────────────────────────────────────────────────────────
def run_loop(ativos: List[str], timeframes: List[str], mode: str, equity: float):
    import MetaTrader5 as mt5
    _eval_ctx_run_start = build_evaluation_context()
    log.info("[EVAL_CONTEXT] run_start | %s", format_eval_log_line(_eval_ctx_run_start))

    log.info("=" * 72)
    log.info("OMEGA %s LOOP v3.0 | %d ativos × %d TFs | equity=USD %.2f",
             mode.upper(), len(ativos), len(timeframes), equity)
    log.info("Risk/trade=%.2f%% | MaxPos=%d | DD_max=%.0f%% | %s",
             RISK_PER_TRADE_PCT * 100, MAX_POSITIONS, DD_DAILY_MAX * 100, human_tag_line())
    log.info("=" * 72)

    mt5_connected = False
    if mode == "paper":
        mt5_connected = mt5_init()
        if not mt5_connected:
            log.critical("MT5 não disponível. Abortando modo paper.")
            _ev_now = build_evaluation_context()
            _erc, _erd = classify_cycle_exit_reason(
                KillSwitch(equity), early_error="MT5 não conectado"
            )
            try:
                AUDIT_PAPER.mkdir(parents=True, exist_ok=True)
                _ce_mt5 = {
                    "generated": datetime.now(timezone.utc).isoformat(),
                    "mode": mode,
                    "exit_reason": _erc,
                    "exit_detail": _erd,
                    "kill_switch": True,
                    "ks_reason": "",
                    "evaluation_calendar_run_start": _eval_ctx_run_start,
                    "evaluation_calendar_at_exit": _ev_now,
                }
                (AUDIT_PAPER / "cycle_exit.json").write_text(
                    json.dumps(_ce_mt5, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                _append_evaluation_timeline_row(
                    AUDIT_PAPER,
                    {
                        "generated": _ce_mt5["generated"],
                        "event": "run_end",
                        "exit_reason": _erc,
                        "exit_detail": _erd,
                        "kill_switch": True,
                        "evaluation_calendar_run_start": _eval_ctx_run_start,
                        "evaluation_calendar_at_exit": _ev_now,
                    },
                )
            except Exception:
                pass
            log.critical("[CYCLE_EXIT] reason=%s detail=%s", _erc, _erd)
            return {
                "error": "MT5 não conectado",
                "kill_switch": True,
                "exit_reason": _erc,
                "exit_detail": _erd,
                "evaluation_calendar_run_start": _eval_ctx_run_start,
                "evaluation_calendar_at_exit": _ev_now,
            }

    dm       = load_dynamic_margins()
    ks       = KillSwitch(equity)
    stats    = OnlineStats()
    _pos_ledger: dict = {}  # ticket -> {entry details + last_known_profit}
    _realized_pnl: float = 0.0
    _realized_n:   int   = 0
    _trade_feedback_n: int = 0  # linhas append em trade_feedback.jsonl (fechos)
    _agent_ia_open_ok: int = 0  # PN-06: record_trade_open com sucesso (AGENT_IA)
    _agent_ia_close_ok: int = 0
    _agent_ia_close_err: int = 0
    # PSA-015 2026-05-15: dedup feedback writer por ticket (previne eventos multi-TF)
    _feedback_written_tickets: set = set()
    _lot_calc = LotCalculatorV2(LotCfgV2())  # CQO 28/04/2026: 4-factor adaptive sizing
    _risk_returns: list = []       # pnl/equity por trade fechado → Sharpe rolling
    _fractal_cache: dict = {}      # asset → {"ts": float, "regime": str, "hurst": float}
    _sl_consec: dict = {}          # BUG-2 FIX: (asset, tf) → {"n": int, "until": float}
    _SL_MAX  = int(os.getenv("OMEGA_SL_CONSEC_MAX",      "3"))   # SL consecutivos → cooldown
    _SL_COOL = int(os.getenv("OMEGA_SL_COOLDOWN_CYCLES", "5"))   # ciclos de espera (~45s cada)
    _flow_state: dict = {}        # symbol → flow confluence score (0-100)
    _partial_close_engines: dict = {}  # ticket → ProgressivePartialCloseComplete (1 engine por posição)
    _trailing_stop_engines: dict = {}  # ticket → HardVolatilityTrailingStopGeometric (1 engine por posição)

    # BUG-1 FIX: PersistentKillSwitch com âncora diária persistente entre subprocesses.
    # reset_session() destruía daily_pnl a cada ciclo de 35s → protecção diária = ZERO.
    if mode == "paper" and mt5_connected:
        _acct = mt5.account_info()
        if _acct and _acct.equity > 0:
            _pks = PersistentKillSwitch(float(os.getenv("OMEGA_DD_DAILY_MAX", "0.02")))
            _is_safe, _ks_reason = _pks.update_and_check(_acct.equity)
            log.info(_ks_reason)
            if not _is_safe:
                log.critical("[HALT] Kill Switch diário disparou — sistema a parar.")
                try:
                    _erc_p, _erd_p = classify_cycle_exit_reason(
                        ks, persistent_halt=True, persistent_detail=_ks_reason
                    )
                    _ev_pks = build_evaluation_context()
                    AUDIT_PAPER.mkdir(parents=True, exist_ok=True)
                    _ce_pks = {
                        "generated": datetime.now(timezone.utc).isoformat(),
                        "mode": mode,
                        "exit_reason": _erc_p,
                        "exit_detail": _erd_p,
                        "kill_switch": True,
                        "ks_reason": _ks_reason,
                        "evaluation_calendar_run_start": _eval_ctx_run_start,
                        "evaluation_calendar_at_exit": _ev_pks,
                    }
                    (AUDIT_PAPER / "cycle_exit.json").write_text(
                        json.dumps(_ce_pks, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    _append_evaluation_timeline_row(
                        AUDIT_PAPER,
                        {
                            "generated": _ce_pks["generated"],
                            "event": "persistent_dd_halt",
                            "exit_reason": _erc_p,
                            "exit_detail": _erd_p,
                            "kill_switch": True,
                            "evaluation_calendar_run_start": _eval_ctx_run_start,
                            "evaluation_calendar_at_exit": _ev_pks,
                        },
                    )
                    log.critical("[CYCLE_EXIT] reason=%s detail=%s", _erc_p, _erd_p)
                except Exception:
                    pass
                sys.exit(1)
            if _CIRCUIT_BREAKER is not None:
                _CIRCUIT_BREAKER.initialize_day(_acct.equity)
                log.info("[CIRCUIT_BREAKER] Inicializado: anchor=$%.2f DD_limit=%.1f%%",
                         _acct.equity, _CB_DD_LIMIT)
            if _TAIL_RISK_HALT is not None:
                _TAIL_RISK_HALT.set_starting_equity(_acct.equity)
                log.info("[TAIL_RISK_HALT] Inicializado: anchor=$%.2f limit=3.0%%", _acct.equity)

    # Sincronização de Estado Real com o MT5 (PSA FIX - State Awareness)
    if mode == "paper" and mt5_connected:
        _rack = mt5.positions_get() or []
        real_pos = filter_omega_tracked_positions(list(_rack))
        open_pos = len(real_pos)
        log.info("MT5 State Sync: %d posicoes OMEGA (comment/mark) detectadas.", open_pos)

        # ── FIX 1: TRAILING STOP + PARTIAL CLOSE PERSISTENCE ──────────────────
        # Problema: engines sao criados por run e destruidos no fim. Posicoes abertas
        # em runs anteriores ficam sem gestao de saida. Solucao: re-inicializar engines
        # para cada posicao existente usando entry_price e peak_price reais do MT5.
        import copy as _copy_mod_boot
        _resynced_ts = 0
        _resynced_pc = 0
        for _rp in real_pos:
            _rp_ticket = _rp.ticket
            # Restaurar pos_ledger para posicoes ja abertas
            if _rp_ticket not in _pos_ledger:
                _pos_ledger[_rp_ticket] = {
                    "symbol": _rp.symbol,
                    "direction": "BUY" if _rp.type == 0 else "SELL",
                    "lot": _rp.volume,
                    "entry_price": _rp.price_open,
                    "sl": float(_rp.sl) if _rp.sl else None,
                    "tp": float(_rp.tp) if _rp.tp else None,
                    "entry_time": datetime.fromtimestamp(_rp.time, tz=timezone.utc).isoformat(),
                    "last_profit": _rp.profit,
                    "status": "open",
                }
            # Trailing stop engine
            if _rp_ticket not in _trailing_stop_engines and _TRAILING_STOP_AVAILABLE:
                try:
                    _ts_eng_boot = _TrailingStopCls(atr_multiplier=1.0, min_multiplier=0.5)  # CEO 2026-05-14 FIX: 1.5→1.0
                    _ts_eng_boot.entry_price = _rp.price_open
                    _rp_dir_ts = 1 if _rp.type == 0 else -1
                    # Peak: price_current se em lucro, senao entry (conservador)
                    _ts_eng_boot._peak_price = _rp.price_current if _rp.profit > 0 else _rp.price_open
                    _trailing_stop_engines[_rp_ticket] = _ts_eng_boot
                    _resynced_ts += 1
                    log.info("[TRAILING] [RESYNC] %s #%d | entry=%.5f peak=%.5f profit=%.2f",
                             _rp.symbol, _rp_ticket, _rp.price_open,
                             _ts_eng_boot._peak_price, _rp.profit)
                except Exception as _ts_boot_err:
                    log.warning("[TRAILING] [RESYNC] Erro #%d: %s", _rp_ticket, _ts_boot_err)
            # Partial close engine
            if _rp_ticket not in _partial_close_engines and _PARTIAL_CLOSE_AVAILABLE:
                try:
                    _pc_eng_boot = _ProgressivePartialCloseCompleteCls()
                    _pc_eng_boot.levels = _copy_mod_boot.deepcopy(_PARTIAL_CLOSE_LEVELS_PSA)
                    _rp_dir_int = 1 if _rp.type == 0 else -1
                    _pc_eng_boot.initialize_position(
                        entry_price=_rp.price_open,
                        lots=_rp.volume,
                        direction=_rp_dir_int,
                    )
                    _partial_close_engines[_rp_ticket] = _pc_eng_boot
                    _resynced_pc += 1
                    log.info("[PARTIAL_CLOSE] [RESYNC] %s #%d | entry=%.5f lot=%.2f dir=%s",
                             _rp.symbol, _rp_ticket, _rp.price_open, _rp.volume,
                             "BUY" if _rp.type == 0 else "SELL")
                except Exception as _pc_boot_err:
                    log.warning("[PARTIAL_CLOSE] [RESYNC] Erro #%d: %s", _rp_ticket, _pc_boot_err)
        if open_pos > 0:
            log.info("[FIX1] Engines re-sincronizados | trailing=%d partial=%d | %d posicoes",
                     _resynced_ts, _resynced_pc, open_pos)
        # ── FIM FIX 1 ─────────────────────────────────────────────────────────
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
    # com seed determinística por minuto (auditável). Com MAX_POSITIONS>0 o teto
    # de slots podia favorecer o primeiro ativo; shuffle reduz viés. MAX_POSITIONS=0
    # desliga esse teto (testes).
    import random as _rnd_fix5
    _rnd_fix5.seed(int(time.time()) // 60)
    ativos_scheduled = list(ativos)
    _rnd_fix5.shuffle(ativos_scheduled)
    log.info("[FIX5] Scheduler de-bias aplicado | ordem=%s", ativos_scheduled)
    _cycle_opened_assets: set = set()  # PSA-WIND Q1: dedup — 1 ordem por ativo por ciclo
    # ── PACING & DIVERSIFICATION — CEO aprovado 2026-05-12 ───────────────────
    _cycle_dir_count: dict = {"BUY": 0, "SELL": 0}   # reset a cada ciclo

    try:
        for asset in ativos_scheduled:
            for tf in timeframes:
                # ── BUG-2: SL Cooldown Gate ──────────────────────────────────
                _cd = _sl_consec.get((asset, tf), {})
                if _cd.get("until", 0.0) > time.time():
                    log.info("[%s %s] SKIP_SL_COOLDOWN — %d SL consec. cooldown activo",
                             asset, tf, _cd.get("n", 0))
                    results.append({"asset": asset, "timeframe": tf, "status": "SKIP_SL_COOLDOWN"})
                    continue
                # Guardrail de Janela — V9: 24/5 liberado (CQO/CTO)
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
                signal_source = None  # preenchido em paper + FASE4; usado em decision_trace

                # === FLOW CONFLUENCE: institutional flow scoring (awakened modules) ===
                # MOVIDO antes de guardrails para sempre logar estado do fluxo
                _flow_conf = 50.0  # default neutro
                _flow_details = {}
                try:
                    _rates_flow = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_M1, 0, 1)
                    _df_flow = None
                    try:
                        import pandas as _pd_flow
                        _rates_m5 = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_M5, 0, 100)
                        if _rates_m5 is not None and len(_rates_m5) >= 30:
                            _df_flow = _pd_flow.DataFrame(_rates_m5)[
                                ["open", "high", "low", "close", "tick_volume"]
                            ].copy()
                    except Exception:
                        _df_flow = None
                    if _rates_flow is not None and len(_rates_flow) > 0:
                        _bar_flow = {
                            "close": float(_rates_flow[0]["close"]),
                            "high": float(_rates_flow[0]["high"]),
                            "low": float(_rates_flow[0]["low"]),
                            "volume": float(_rates_flow[0]["tick_volume"])
                        }
                        # Usar direção neutra (0) para scoring sem viés
                        _flow_conf, _flow_details = compute_flow_confluence(_bar_flow, asset, 0, df=_df_flow)
                        _flow_state[asset] = _flow_conf
                        log.info(
                            "[%s %s] [FLOW] confluence=%.1f | legacy: v_flow=%.0f vol_phy=%.0f "
                            "| new: sto_fused=%.0f vof=%.0f vwap=%.0f pullback=%.0f "
                            "wyckoff=%.0f elliott=%.0f liq=%.0f weis=%.0f",
                            asset, tf, _flow_conf,
                            _flow_details.get("v_flow", 50),
                            _flow_details.get("vol_physics", 50),
                            _flow_details.get("sto_fused", 50),
                            _flow_details.get("vof", 50),
                            _flow_details.get("vwap", 50),
                            _flow_details.get("pullback", 50),
                            _flow_details.get("wyckoff", 50),
                            _flow_details.get("elliott", 50),
                            _flow_details.get("liq_abs", 50),
                            _flow_details.get("weis_wave", 50),
                        )
                    else:
                        log.warning("[%s %s] [FLOW] sem dados M1", asset, tf)
                except Exception as _flow_err:
                    log.error("[%s %s] [FLOW] erro: %s", asset, tf, _flow_err)

                # CONFLUENCE GATE v1.1 (Auditoria IA 2026-05-09)
                _MIN_CONF_GATE = float(os.getenv("OMEGA_MIN_CONFLUENCE", "40.0"))
                # Usar _flow_conf (variável local do passo actual) — mais seguro que
                # _flow_state.get(asset) que pode ter valores stale de iterações anteriores
                if _flow_conf < _MIN_CONF_GATE:
                    log.info(
                        "[%s %s] [CONFLUENCE_GATE] BLOCKED score=%.1f < min=%.1f",
                        asset, tf, _flow_conf, _MIN_CONF_GATE
                    )
                    continue

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
                                    "reasons": guard["skip_reasons"]})
                    decision_trace_append(
                        {
                            "asset": asset,
                            "timeframe": tf,
                            "phase": "pre_harmonic_guard",
                            "class": classify_asset(asset),
                            "status": "SKIP",
                            "skip_reasons": guard["skip_reasons"],
                            "hit_rate_prev": prev_hr,
                        }
                    )
                    continue

                # Flow scorer já foi chamado antes de guardrails (linha ~1329)
                # Aqui usamos o valor em cache se houver sinal
                _flow_conf = _flow_state.get(asset, 50.0)

                if mode == "paper" and MAX_POSITIONS > 0 and open_pos >= MAX_POSITIONS:
                    log.warning("[%s %s] MAX_POSITIONS=%d atingido.", asset, tf, MAX_POSITIONS); continue

                # FIX-DUPL: gate por ativo — bloqueia 2ª posição no mesmo ativo
                if MAX_POS_PER_ASSET > 0 and mode == "paper":
                    _asset_cnt = sum(1 for _p in real_pos if _p.symbol == asset)
                    if _asset_cnt >= MAX_POS_PER_ASSET:
                        log.warning("[%s %s] MAX_POS_PER_ASSET=%d atingido — bloqueia duplicação.",
                                    asset, tf, MAX_POS_PER_ASSET); continue

                # Motor Harmônico V3
                out_dir  = AUDIT_PAPER / f"{asset}_{tf}"
                harmonic = run_harmonic(asset, tf, guard["margin_used"], out_dir)
                if harmonic is None:
                    # SKIP_HARMONIC: Motor V3 sem dados (ativo fechado/sem CSV) — NÃO conta como falha de execução para KS
                    results.append({"asset": asset, "timeframe": tf, "status": "SKIP_HARMONIC"})
                    decision_trace_append(
                        {
                            "asset": asset,
                            "timeframe": tf,
                            "phase": "harmonic",
                            "class": classify_asset(asset),
                            "status": "SKIP_HARMONIC",
                        }
                    )
                    continue

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
                            psa_decision = None
                            if (
                                _PSA_LOOP_FEED_AVAILABLE
                                and compute_psa_decision_mt5 is not None
                                and mt5_connected
                                and os.getenv("OMEGA_LOOP_PSA_V12", "1").strip().lower()
                                not in ("0", "false", "no", "off")
                            ):
                                try:
                                    import MetaTrader5 as _mt5_psa
                                    _regime = ASSET_PROFILES.get(asset, {}).get("regime", "forex")
                                    psa_decision = compute_psa_decision_mt5(
                                        asset,
                                        tf,
                                        _regime,
                                        float(equity),
                                        mt5_module=_mt5_psa,
                                    )
                                    if isinstance(psa_decision, dict) and psa_decision.get("action"):
                                        log.info(
                                            "[%s %s] [PSA_FEED] action=%s conf=%.3f skill=%s",
                                            asset,
                                            tf,
                                            psa_decision.get("action"),
                                            float(psa_decision.get("confidence") or 0.0),
                                            psa_decision.get("skill_id"),
                                        )
                                except Exception as _psa_loop_err:
                                    log.warning("[%s %s] PSA_FEED: %s", asset, tf, _psa_loop_err)
                                    psa_decision = None
                            ia_signal = agent_ia.get_signal(
                                asset,
                                signature_scores=sig_scores or {},
                                psa_decision=psa_decision,
                            )
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
                            decision_trace_append(
                                {
                                    "asset": asset,
                                    "timeframe": tf,
                                    "phase": "edge_gate",
                                    "class": classify_asset(asset),
                                    "status": "SKIP_EDGE_GATE",
                                    "edge_metrics": edge_m,
                                }
                            )
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

                        # CEO ORDER 04/05/2026: Confirmação em M15 (cascata W1→D1→H4→H1→M15)
                        # M15 = último filtro de confluência antes de executar em M3/M1.
                        # Captura movimentos de 500-5000pts sem ser enganado por ruído M5.
                        _kl = get_key_levels(asset)
                        if _kl.get("gap_pts") and abs(_kl["gap_pts"]) > 5:
                            log.info("[%s %s] [KEY_LEVELS] GAP=%+.1fpts dir=%s fill=%.5f | PrevDay C=%.5f H=%.5f L=%.5f | PrevWeek H=%.5f L=%.5f | POC=%.5f",
                                     asset, tf, _kl["gap_pts"], _kl["gap_dir"],
                                     _kl.get("gap_fill_level") or 0,
                                     _kl.get("prev_day_close") or 0,
                                     _kl.get("prev_day_high") or 0,
                                     _kl.get("prev_day_low") or 0,
                                     _kl.get("prev_week_high") or 0,
                                     _kl.get("prev_week_low") or 0,
                                     _kl.get("poc_price") or 0)
                        else:
                            log.info("[%s %s] [KEY_LEVELS] PrevDay C=%.5f H=%.5f L=%.5f | PrevWeek H=%.5f L=%.5f | POC=%.5f | NoGAP",
                                     asset, tf,
                                     _kl.get("prev_day_close") or 0,
                                     _kl.get("prev_day_high") or 0,
                                     _kl.get("prev_day_low") or 0,
                                     _kl.get("prev_week_high") or 0,
                                     _kl.get("prev_week_low") or 0,
                                     _kl.get("poc_price") or 0)
                        # P2-B C4 FIX: TF dinâmico alinhado com a entrada (era M15 hardcoded)
                        _TF_MAP_FLOW = {
                            "M5":  mt5.TIMEFRAME_M5,  "M15": mt5.TIMEFRAME_M15,
                            "H1":  mt5.TIMEFRAME_H1,  "H4":  mt5.TIMEFRAME_H4,
                            "D1":  mt5.TIMEFRAME_D1,
                        }
                        _flow_tf_dyn = _TF_MAP_FLOW.get(tf, mt5.TIMEFRAME_M15)
                        rates = mt5.copy_rates_from_pos(asset, _flow_tf_dyn, 0, 50)
                        if rates is not None and len(rates) >= 21:
                            import numpy as _np_flow
                            tick_now = mt5.symbol_info_tick(asset)
                            c_price = tick_now.ask if tick_now else rates[-1]['close']
                            _closes = _np_flow.array([r['close'] for r in rates], dtype=_np_flow.float64)
                            _volumes = _np_flow.array([r['tick_volume'] for r in rates], dtype=_np_flow.float64)
                            # EMA-8 e EMA-21 para capturar tendência M5
                            def _ema(arr, span):
                                a = 2.0 / (span + 1)
                                out = _np_flow.empty_like(arr)
                                out[0] = arr[0]
                                for i in range(1, len(arr)):
                                    out[i] = a * arr[i] + (1 - a) * out[i - 1]
                                return out
                            _ema8 = _ema(_closes, 8)
                            _ema21 = _ema(_closes, 21)
                            # Slope das últimas 5 barras da EMA8 (inclinação do fluxo)
                            _slope = (_ema8[-1] - _ema8[-5]) / max(abs(_ema8[-5]), 1e-10) * 10000
                            # Volume imbalance: volume recente vs média (confirma participação)
                            _vol_recent = _np_flow.mean(_volumes[-5:])
                            _vol_avg = _np_flow.mean(_volumes)
                            _vol_ratio = _vol_recent / max(_vol_avg, 1.0)
                            # DECISÃO: EMA8 > EMA21 + slope positivo + volume ok = BUY
                            _ema_cross = _ema8[-1] > _ema21[-1]
                            _slope_min = float(os.getenv("OMEGA_FLOW_SLOPE_MIN", "0.5"))  # 0.5 = liberado, 1.0 = rigoroso
                            _slope_ok = abs(_slope) > _slope_min
                            if _ema_cross and _slope > _slope_min:
                                signal_dir = "BUY"
                            elif not _ema_cross and _slope < -_slope_min:
                                signal_dir = "SELL"
                            else:
                                log.info("[%s %s] [FLOW_SIGNAL] NO_TREND — ema_cross=%s slope=%.2f vol_ratio=%.2f — SKIP",
                                         asset, tf, _ema_cross, _slope, _vol_ratio)
                                results.append({"asset": asset, "timeframe": tf,
                                                "status": "SKIP_NO_FLOW_TREND",
                                                "slope": round(_slope, 2), "vol_ratio": round(_vol_ratio, 2)})
                                continue
                            log.info("[%s %s] FlowSignal: price=%.5f EMA8=%.5f EMA21=%.5f slope=%.2f vol_ratio=%.2f DIR=%s (src=%s) adx=%.1f",
                                     asset, tf, c_price, _ema8[-1], _ema21[-1], _slope, _vol_ratio,
                                     signal_dir, signal_source,
                                     edge_m.get("adx", 0))
                        else:
                            log.warning("[%s %s] Falha ao ler candles M15 para confirmação — SKIP", asset, tf)
                            results.append({"asset": asset, "timeframe": tf, "status": "SKIP_NO_RATES"})
                            continue

                    # === MULTI-TF BIAS CHECK (CEO 04/05/2026: W1+D1+H4+H1+M15 cascata ponderada) ===
                    # W1 tem peso 3x — se a semana é SELL, nenhum BUY passa.
                    # FIX #4-REV (CEO 2026-05-14): bloquear sinais com alinhamento < MTF_ALIGN_MIN (20%)
                    # Evita executar em 33%/11% — sinais de baixa qualidade nocturno.
                    if signal_dir:
                        try:
                            _tf_bias = get_multi_tf_bias(asset)
                            # FIX #4: rejeitar sinais abaixo do minimo de alinhamento (efectivo por TF)
                            _mtf_min_eff = effective_mtf_align_min(tf)
                            if _tf_bias["alignment"] < _mtf_min_eff:
                                log.info("[%s %s] [MTF_BIAS] SKIP_LOW_ALIGN align=%.0f%% < %.0f%% min_eff(tf=%s) | %s",
                                         asset, tf,
                                         _tf_bias["alignment"] * 100, _mtf_min_eff * 100, tf,
                                         _tf_bias["detail"])
                                results.append({"asset": asset, "timeframe": tf,
                                               "status": "SKIP_MTF_LOW_ALIGN",
                                               "alignment": _tf_bias["alignment"],
                                               "min_required": _mtf_min_eff})
                                continue
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
                        raw_all = mt5.positions_get() or []
                        _omega_all = filter_omega_tracked_positions(list(raw_all))
                        all_open_positions = [p._asdict() for p in _omega_all]
                        # Ledger: detectar fechamentos por SL/TP em tempo real
                        _live_tickets = {p.ticket for p in _omega_all}
                        for _lp_profit in _omega_all:  # atualiza last_profit
                            if _lp_profit.ticket in _pos_ledger:
                                _pos_ledger[_lp_profit.ticket]["last_profit"] = _lp_profit.profit
                        # LEDGER_SYNC — recuperar posicoes MT5 nao registadas no ledger (fix JSONL 2026-05-12)
                        for _live_p in _omega_all:
                            if _live_p.ticket not in _pos_ledger:
                                _pos_ledger[_live_p.ticket] = {
                                    "status": "open",
                                    "symbol": _live_p.symbol,
                                    "tf": tf,
                                    "signal_source": "SYNC_RECOVERY",
                                    "last_profit": _live_p.profit,
                                    "entry_time": datetime.now(timezone.utc).isoformat(),
                                    "sl_pts": 0,
                                    "risk_usd": 0,
                                }
                                log.info("[LEDGER_SYNC] Ticket %d (%s) recuperado para o ledger",
                                         _live_p.ticket, _live_p.symbol)
                        # ── TIME-STOP & STAGNATION-STOP (CEO 2026-05-12) ──────────────────
                        # Liberta slots presos em posicoes sem progresso.
                        # OMEGA_MAX_TRADE_MIN  : fechar se aberta ha > N min e em perda  (default 90)
                        # OMEGA_STAG_MIN       : fechar se ha > N min sem mover 20% para TP (default 45)
                        _TS_MAX_MIN  = int(os.getenv("OMEGA_MAX_TRADE_MIN",  "0"))   # 0=DESACTIVADO por defeito
                        _STAG_MIN    = int(os.getenv("OMEGA_STAG_MIN",       "0"))   # 0=DESACTIVADO por defeito
                        _now_ts      = time.time()
                        for _tp_live in list(_omega_all):
                            try:
                                _age_min = (_now_ts - _tp_live.time) / 60.0
                                _pnl     = _tp_live.profit
                                _dir_tp  = "BUY" if _tp_live.type == 0 else "SELL"
                                _entry_p = _tp_live.price_open
                                _sl_p    = _tp_live.sl
                                _tp_p    = _tp_live.tp
                                _close_reason = None

                                # 1. TIME-STOP: posicao em perda ha mais de OMEGA_MAX_TRADE_MIN (0=desactivado)
                                if _TS_MAX_MIN > 0 and _age_min > _TS_MAX_MIN and _pnl < 0:
                                    _close_reason = f"TIME_STOP age={_age_min:.0f}min pnl={_pnl:.2f}"

                                # 2. STAGNATION-STOP: posicao ha > OMEGA_STAG_MIN sem atingir 20% do caminho para TP (0=desactivado)
                                elif _STAG_MIN > 0 and _age_min > _STAG_MIN and _tp_p != 0 and _sl_p != 0:
                                    _range_total = abs(_tp_p - _entry_p)
                                    if _range_total > 0:
                                        if _dir_tp == "BUY":
                                            _progress = (_tp_live.price_current - _entry_p) / _range_total
                                        else:
                                            _progress = (_entry_p - _tp_live.price_current) / _range_total
                                        if _progress < 0.20:  # nao atingiu 20% do caminho para TP
                                            _close_reason = (
                                                f"STAGNATION age={_age_min:.0f}min "
                                                f"progress={_progress*100:.0f}%<20%"
                                            )

                                if _close_reason:
                                    log.warning(
                                        "[TIME_STOP] Fechando #%d %s %s pnl=%.2f — %s",
                                        _tp_live.ticket, _tp_live.symbol, _dir_tp,
                                        _pnl, _close_reason,
                                    )
                                    _ts_req = mt5.order_send(mt5.TradeRequest(
                                        action   = mt5.TRADE_ACTION_DEAL,
                                        position = _tp_live.ticket,
                                        symbol   = _tp_live.symbol,
                                        volume   = _tp_live.volume,
                                        type     = (mt5.ORDER_TYPE_SELL if _dir_tp == "BUY"
                                                    else mt5.ORDER_TYPE_BUY),
                                        price    = (mt5.symbol_info_tick(_tp_live.symbol).bid
                                                    if _dir_tp == "BUY"
                                                    else mt5.symbol_info_tick(_tp_live.symbol).ask),
                                        deviation = 30,
                                        magic    = 20260512,
                                        comment  = f"OMEGA_TIME_STOP",
                                        type_filling = mt5.ORDER_FILLING_IOC,
                                    ))
                                    if _ts_req and _ts_req.retcode == mt5.TRADE_RETCODE_DONE:
                                        log.info("[TIME_STOP] OK #%d fechado retcode=%d",
                                                 _tp_live.ticket, _ts_req.retcode)
                                    else:
                                        _rc = _ts_req.retcode if _ts_req else "N/A"
                                        log.warning("[TIME_STOP] FALHOU #%d retcode=%s",
                                                    _tp_live.ticket, _rc)
                            except Exception as _ts_err:
                                log.debug("[TIME_STOP] erro ticket=%s: %s",
                                          getattr(_tp_live, 'ticket', '?'), _ts_err)
                        # ── FIM TIME-STOP ─────────────────────────────────────────────────

                        # ── ZAK TRAP DETECTION — fechar armadilhas antes do SL (CEO 2026-05-13) ─
                        if _ZAK_GUARDRAIL_AVAIL and _ZAK_GUARDRAIL is not None:
                            for _trap_pos in list(_omega_all):
                                try:
                                    _trap_dir = "BUY" if _trap_pos.type == 0 else "SELL"
                                    _trap_sym = _trap_pos.symbol
                                    _zak_trap_rates = mt5.copy_rates_from_pos(_trap_sym, mt5.TIMEFRAME_H1, 0, 30)
                                    if _zak_trap_rates is None or len(_zak_trap_rates) < 5:
                                        continue
                                    import pandas as _pd_trap
                                    _zak_trap_df = _pd_trap.DataFrame(_zak_trap_rates)
                                    _is_trap = _ZAK_GUARDRAIL.detect_trap(
                                        direction=_trap_dir,
                                        entry_price=_trap_pos.price_open,
                                        current_price=_trap_pos.price_current,
                                        df=_zak_trap_df,
                                    )
                                    if _is_trap:
                                        _trap_tick = mt5.symbol_info_tick(_trap_sym)
                                        _trap_close_price = (_trap_tick.bid if _trap_dir == "BUY"
                                                             else _trap_tick.ask)
                                        _trap_req = mt5.order_send(mt5.TradeRequest(
                                            action   = mt5.TRADE_ACTION_DEAL,
                                            position = _trap_pos.ticket,
                                            symbol   = _trap_sym,
                                            volume   = _trap_pos.volume,
                                            type     = (mt5.ORDER_TYPE_SELL if _trap_dir == "BUY"
                                                        else mt5.ORDER_TYPE_BUY),
                                            price    = _trap_close_price,
                                            deviation = 30,
                                            magic    = 20260513,
                                            comment  = "OMEGA_ZAK_TRAP",
                                            type_filling = mt5.ORDER_FILLING_IOC,
                                        ))
                                        if _trap_req and _trap_req.retcode == mt5.TRADE_RETCODE_DONE:
                                            log.warning("[ZAK_TRAP] Fechado #%d %s %s pnl=%.2f — armadilha detectada",
                                                        _trap_pos.ticket, _trap_sym, _trap_dir,
                                                        _trap_pos.profit)
                                        else:
                                            _tr = _trap_req.retcode if _trap_req else "N/A"
                                            log.warning("[ZAK_TRAP] Falhou fechar #%d retcode=%s",
                                                        _trap_pos.ticket, _tr)
                                except Exception as _trap_err:
                                    log.debug("[ZAK_TRAP] erro ticket=%s: %s",
                                              getattr(_trap_pos, 'ticket', '?'), _trap_err)
                        # ── FIM ZAK TRAP DETECTION ─────────────────────────────────────────

                        for _tk, _entry in list(_pos_ledger.items()):
                            if _entry["status"] == "open" and _tk not in _live_tickets:
                                _entry["status"] = "closed"
                                _entry["exit_time"] = datetime.now(timezone.utc).isoformat()
                                # ── JSONL FIX 2026-05-13: usar PnL REALIZADO do histórico MT5 ──
                                # last_profit era o floating P&L da última leitura (não o realizado)
                                # → TP hits eram registados como LOSS pois floating podia ser negativo
                                _entry_pnl    = _entry.get("last_profit", 0.0)  # fallback
                                _exit_reason  = "UNKNOWN"
                                try:
                                    _hist_window = timedelta(minutes=90)
                                    _hist_deals  = mt5.history_deals_get(
                                        datetime.now(timezone.utc) - _hist_window,
                                        datetime.now(timezone.utc)
                                    ) or []
                                    for _hd in reversed(_hist_deals):
                                        # DEAL_ENTRY_OUT = 1 — fecho de posição
                                        if _hd.position_id == _tk and _hd.entry == 1:
                                            _entry_pnl   = _hd.profit
                                            if   _hd.reason == 4:   # DEAL_REASON_TP
                                                _exit_reason = "TP"
                                            elif _hd.reason == 5:   # DEAL_REASON_SL
                                                _exit_reason = "SL"
                                            elif _hd.reason == 6:   # DEAL_REASON_SO
                                                _exit_reason = "STOP_OUT"
                                            else:
                                                _exit_reason = "MANUAL"
                                            break
                                except Exception as _hist_e:
                                    log.debug("[LEDGER] history_deals fallback last_profit: %s", _hist_e)
                                _entry["exit_reason"] = _exit_reason
                                _entry_sl   = _entry.get("sl_pts", 0)
                                _entry_risk = _entry.get("risk_usd", 0)
                                if _entry_risk > 0:
                                    _entry["r_multiple"] = round(_entry_pnl / _entry_risk, 2)
                                _entry["result"] = "WIN" if _entry_pnl > 0 else ("LOSS" if _entry_pnl < 0 else "BE")
                                # BUG-2 FIX: registar SL/WIN para cooldown por (asset, tf)
                                _ck2 = (_entry.get("symbol"), tf)
                                if _entry_pnl < 0:
                                    _cc2 = _sl_consec.setdefault(_ck2, {"n": 0, "until": 0.0})
                                    _cc2["n"] += 1
                                    if _cc2["n"] >= _SL_MAX:
                                        _cc2["until"] = time.time() + _SL_COOL * 45
                                        log.warning("[%s %s] [SL_COOLDOWN] %d SL consecutivos — cooldown %ds",
                                                    _entry.get("symbol"), tf, _cc2["n"], _SL_COOL * 45)
                                else:
                                    _sl_consec.pop(_ck2, None)  # WIN: reset contador
                                # PSA-016 2026-05-15: fix duration_min UTC — normalizar ambos os timestamps para UTC
                                _entry_dt = datetime.fromisoformat(_entry.get("entry_time", datetime.now(timezone.utc).isoformat()))
                                if _entry_dt.tzinfo is None:
                                    _entry_dt = _entry_dt.replace(tzinfo=timezone.utc)
                                _entry["duration_min"] = round(
                                    (datetime.now(timezone.utc) - _entry_dt).total_seconds() / 60, 1
                                )
                                if _entry["duration_min"] < 0:
                                    log.warning("[LEDGER] duration_min negativo #%d: %.1f (UTC fix)", _tk, _entry["duration_min"])
                                    _entry["duration_min"] = 0.0  # fallback para não quebrar KPI
                                _realized_pnl += _entry_pnl
                                _realized_n   += 1
                                _lot_calc.update_performance(_entry_pnl)
                                _risk_returns.append(_entry_pnl / max(equity, 1.0))
                                log.info("[LEDGER] FECHADA %s #%d pnl=%.4f R=%.2f %s dur=%.0fmin | total_realiz=%.4f n=%d",
                                         _entry["symbol"], _tk, _entry_pnl,
                                         _entry.get("r_multiple", 0), _entry.get("result", "?"),
                                         _entry.get("duration_min", 0),
                                         _realized_pnl, _realized_n)
                                # Fecho de loop: artefato por trade (todas as fontes) + feedback IA
                                # PSA-015 2026-05-15: dedup feedback writer por (ticket, event_type)
                                _event_key = (int(_tk), "position_closed")
                                if _event_key not in _feedback_written_tickets:
                                    try:
                                        trade_feedback_append(
                                            {
                                                "event": "position_closed",
                                                "position_ticket": int(_tk),
                                                "symbol": _entry.get("symbol"),
                                                "timeframe": tf,
                                                "signal_source": _entry.get("signal_source"),
                                                "agent_id": _entry.get("agent_id"),
                                                "pnl": round(float(_entry_pnl), 6),
                                                "r_multiple": _entry.get("r_multiple"),
                                                "result": _entry.get("result"),
                                                "duration_min": _entry.get("duration_min"),
                                                "regime": _entry.get("regime"),
                                                "confidence": _entry.get("confidence"),
                                                "entry_deal": _entry.get("entry_deal"),
                                                "sl_pts": _entry.get("sl_pts"),
                                                "tp_pts": _entry.get("tp_pts"),
                                                "slippage_pts": _entry.get("slippage_pts"),
                                                "detected_at_utc": datetime.now(timezone.utc).isoformat(),
                                                # schema v1.2 (Auditoria IA 2026-05-09)
                                                "exit_reason":      _entry.get("exit_reason"),
                                                "confluence_score": _entry.get("confluence_score"),
                                                "components_fired": _entry.get("components_fired"),
                                                "modules_active":   _entry.get("modules_active"),
                                                "decision_id":      _entry.get("decision_id"),
                                            }
                                        )
                                        _feedback_written_tickets.add(_event_key)
                                        _trade_feedback_n += 1
                                    except Exception as _fb_e:
                                        log.debug("[LEDGER] trade_feedback_append: %s", _fb_e)
                                # Agent IA close record (if applicable)
                                if (
                                    agent_ia is not None
                                    and _entry.get("signal_source") == "AGENT_IA"
                                    and _entry.get("agent_id")
                                ):
                                    try:
                                        agent_ia.record_trade_close(
                                            str(_entry["symbol"]),
                                            str(_entry["agent_id"]),
                                            float(_entry_pnl),
                                            ticket=int(_tk),
                                        )
                                        _agent_ia_close_ok += 1
                                        log.info(
                                            "[AGENT_IA] record_trade_close OK #%s pnl=%.4f agent=%s",
                                            _tk,
                                            _entry_pnl,
                                            _entry.get("agent_id"),
                                        )
                                    except Exception as _ia_ce:
                                        _agent_ia_close_err += 1
                                        log.warning(
                                            "[AGENT_IA] record_trade_close falhou #%s: %s",
                                            _tk,
                                            _ia_ce,
                                        )

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

                    # === PSA-WIND Q1: DEDUP — apenas 1 ordem por ativo por ciclo ===
                    # H1 e H4 geram sinais idênticos (mesmo M5 EMA) → duplicata
                    if asset in _cycle_opened_assets:
                        log.info("[%s %s] [DEDUP] SKIP — já abriu ordem para %s neste ciclo",
                                 asset, tf, asset)
                        results.append({"asset": asset, "timeframe": tf,
                                        "status": "SKIP_DEDUP_CYCLE"})
                        continue  # FIX: sem este continue, caía no Q2 e abria posição duplicada
                    # === PSA-WIND Q2: 1 POSIÇÃO POR ATIVO (CEO 2026-05-14 FIX) ===
                    # Forçar MAX_POS_PER_ASSET=1 — 2ª posição só via check_pyramid_add()
                    # Previne 3× ordens idênticas mesmo volume; pyramid tem lot progressivo (1.5x)
                    _MAX_POS_PER_ASSET = int(os.getenv("OMEGA_MAX_POS_PER_ASSET", "1"))  # 1=padrão; pyramid path tem seu próprio check
                    _existing_omega_same = [p for p in current_positions if p.get("symbol") == asset]
                    if _existing_omega_same:
                        _n_exist = len(_existing_omega_same)
                        if _n_exist >= _MAX_POS_PER_ASSET:
                            _pnl_exist = sum(p.get("profit", 0) for p in _existing_omega_same)
                            log.info("[%s %s] [POS_RULE] SKIP — já tem %d/%d posições OMEGA (pnl=%.2f)",
                                     asset, tf, _n_exist, _MAX_POS_PER_ASSET, _pnl_exist)
                            results.append({"asset": asset, "timeframe": tf,
                                            "status": "SKIP_ALREADY_POSITIONED",
                                            "existing_count": _n_exist,
                                            "existing_pnl": round(_pnl_exist, 2)})
                            continue

                    # === PSA-WIND FIX 1: ANTI-HEDGE — bloquear BUY+SELL no mesmo ativo ===
                    _has_opposite = False
                    for _cp in current_positions:
                        _cp_dir = "BUY" if _cp.get("type") == 0 else "SELL"
                        if _cp_dir != signal_dir:
                            _has_opposite = True
                            break
                    if _has_opposite:
                        log.warning("[%s %s] [ANTI_HEDGE] BLOCKED — já existe posição %s, sinal=%s (hedge não intencional)",
                                    asset, tf, _cp_dir, signal_dir)
                        results.append({"asset": asset, "timeframe": tf,
                                        "status": "SKIP_ANTI_HEDGE",
                                        "existing_dir": _cp_dir, "signal_dir": signal_dir})
                        continue

                    # === PACING & DIVERSIFICATION — CEO 2026-05-12 ========================
                    _MAX_DIR_CYCLE = int(os.getenv("OMEGA_MAX_SAME_DIR_PER_CYCLE", "2"))   # CEO 2026-05-14: 1→2
                    _MAX_PER_CLASS = int(os.getenv("OMEGA_MAX_POS_PER_CLASS", "5"))        # CEO 2026-05-14: 2→5
                    # Guardrail 1: limitar ordens na mesma direção por ciclo
                    if _cycle_dir_count.get(signal_dir, 0) >= _MAX_DIR_CYCLE:
                        log.info("[%s %s] [P&D] SKIP — %s já abriu %d/%d neste ciclo",
                                 asset, tf, signal_dir,
                                 _cycle_dir_count.get(signal_dir, 0), _MAX_DIR_CYCLE)
                        results.append({"asset": asset, "timeframe": tf,
                                        "status": "SKIP_PACING_DIR",
                                        "dir": signal_dir})
                        continue
                    # Guardrail 2: limitar posições por classe de ativo
                    _asset_class = ASSET_PROFILES.get(asset, _PROFILE_DEFAULT).get("regime", "forex")
                    _class_count = sum(
                        1 for _p in current_positions
                        if ASSET_PROFILES.get(_p.get("symbol", ""), {}).get("regime") == _asset_class
                    )
                    if _class_count >= _MAX_PER_CLASS:
                        log.info("[%s %s] [P&D] SKIP — classe '%s' já tem %d/%d posições",
                                 asset, tf, _asset_class, _class_count, _MAX_PER_CLASS)
                        results.append({"asset": asset, "timeframe": tf,
                                        "status": "SKIP_PACING_CLASS",
                                        "class": _asset_class,
                                        "class_count": _class_count})
                        continue
                    # === PSA-WIND FIX 2: SPIKE DETECTION — bloquear entrada em anomalia ===
                    if _SPIKE_DETECTION_AVAILABLE and _SPIKE_DETECTOR is not None:
                        try:
                            _spike_rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_M1, 0, 30)
                            if _spike_rates is not None and len(_spike_rates) >= 5:
                                import numpy as _np_spike
                                _last_bar = {
                                    "open": float(_spike_rates[-1]["open"]),
                                    "high": float(_spike_rates[-1]["high"]),
                                    "low": float(_spike_rates[-1]["low"]),
                                    "close": float(_spike_rates[-1]["close"]),
                                    "volume": float(_spike_rates[-1]["tick_volume"]),
                                }
                                if not _SPIKE_DETECTOR.is_fitted():
                                    import pandas as _pd_spike
                                    _spike_df = _pd_spike.DataFrame([{
                                        "open": float(r["open"]), "high": float(r["high"]),
                                        "low": float(r["low"]), "close": float(r["close"]),
                                        "volume": float(r["tick_volume"])
                                    } for r in _spike_rates[:-1]])
                                    _SPIKE_DETECTOR.fit(_spike_df)
                                _spike_result = _SPIKE_DETECTOR.detect(_last_bar)
                                if _spike_result.has_anomaly and _spike_result.severity.value in ("HIGH", "CRITICAL"):
                                    log.warning("[%s %s] [SPIKE] BLOCKED — %s severity=%s conf=%.2f action=%s",
                                                asset, tf, _spike_result.anomaly_type.value,
                                                _spike_result.severity.value, _spike_result.confidence,
                                                _spike_result.recommended_action)
                                    results.append({"asset": asset, "timeframe": tf,
                                                    "status": "SKIP_SPIKE_ANOMALY",
                                                    "anomaly_type": _spike_result.anomaly_type.value,
                                                    "severity": _spike_result.severity.value})
                                    continue
                                elif _spike_result.has_anomaly:
                                    log.info("[%s %s] [SPIKE] MONITOR — %s severity=%s conf=%.2f (não bloqueia)",
                                             asset, tf, _spike_result.anomaly_type.value,
                                             _spike_result.severity.value, _spike_result.confidence)
                        except Exception as _spike_err:
                            log.debug("[%s %s] [SPIKE] Erro (não bloqueia): %s", asset, tf, _spike_err)

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
                        # Limite duro do contrato MT5 (evita pedir 0.25 quando max=0.10)
                        eff_lot = min(eff_lot, float(lot_info.get("sym_vol_max", 999.0) or 999.0))
                        # IA override: respeita sugestão IA se for menor (conservador)
                        if ia_lot_override is not None:
                            try:
                                eff_lot = min(eff_lot, float(ia_lot_override))
                                eff_lot = max(lot_info.get("sym_vol_min", 0.01), eff_lot)
                            except Exception:
                                pass
                        # Concentração por ativo (Fix 5): >CONCENTRATION_MAX → reduz 50%
                        try:
                            _tracked = filter_omega_tracked_positions(list(mt5.positions_get() or []))
                            same_asset = sum(1 for p in _tracked if p.symbol == asset)
                            total_omega = len(_tracked)
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
                        # ── Lote: piso por regime + opcional escala ao min TP USD + teto de risco/trade ──
                        _pip_val = float(lot_info.get("pip_value_lot", 0.01) or 0.01)
                        _reg_lot = str(_prof.get("regime", "") or "")
                        _smax = float(lot_info.get("sym_vol_max", 999.0) or 999.0)
                        _smin = float(lot_info.get("sym_vol_min", 0.01) or 0.01)
                        _lcap = float(_prof.get("lot_cap", 0.1))
                        _floor = min_lot_floor_for_regime(_reg_lot)
                        if _floor > 0:
                            eff_lot = max(float(eff_lot or 0), _floor)
                        eff_lot = min(float(eff_lot or 0), _lcap, _smax)
                        eff_lot = max(_smin, eff_lot)

                        _thr_tp_usd = min_expected_tp_usd_threshold(asset)
                        _scale_lot = os.getenv("OMEGA_SCALE_LOT_TO_MIN_TP_USD", "0").strip().lower() in (
                            "1", "true", "yes", "on",
                        )
                        if _scale_lot and _thr_tp_usd > 0 and eff_tp * _pip_val > 1e-12:
                            _need_lot = _thr_tp_usd / (float(eff_tp) * _pip_val)
                            eff_lot = max(float(eff_lot), _need_lot)
                            eff_lot = min(eff_lot, _lcap, _smax)
                            eff_lot = max(_smin, eff_lot)

                        _max_risk_usd = float(equity) * float(RISK_PER_TRADE_PCT)
                        _usd_per_lot_sl = float(eff_sl) * _pip_val
                        if _usd_per_lot_sl * eff_lot > _max_risk_usd > 0:
                            _lot_risk_cap = _max_risk_usd / max(_usd_per_lot_sl, 1e-12)
                            eff_lot = min(eff_lot, _lot_risk_cap)
                            eff_lot = max(_smin, eff_lot)

                        if _floor > 0 and float(eff_lot) + 1e-9 < _floor:
                            log.info(
                                "[%s %s] [LOT_GATE] SKIP — piso_lote=%.4f incompatível com risco máx "
                                "(%.2f%% equity ≈ $%.2f) ao SL=%.0fpts (sym_max=%.4f)",
                                asset,
                                tf,
                                _floor,
                                RISK_PER_TRADE_PCT * 100,
                                _max_risk_usd,
                                eff_sl,
                                _smax,
                            )
                            results.append(
                                {
                                    "asset": asset,
                                    "timeframe": tf,
                                    "status": "SKIP_LOT_FLOOR_RISK",
                                    "min_lot_floor": _floor,
                                    "max_risk_usd": round(_max_risk_usd, 2),
                                }
                            )
                            continue

                        # Risco efetivo em USD para log / agregados
                        _risk_usd_eff = eff_sl * _pip_val * (eff_lot or 0.01)
                        if _thr_tp_usd > 0:
                            _tp_usd_est = eff_tp * _pip_val * (eff_lot or 0.01)
                            if _tp_usd_est < _thr_tp_usd:
                                log.info(
                                    "[%s %s] [ECON_GATE] SKIP — TP_estimado=$%.2f < min=$%.2f "
                                    "(TP=%.0fpts lot=%.4f pip_val/lot=%.6f). "
                                    "Aumente OMEGA_LOT_MAX / lot_cap do ativo, ative "
                                    "OMEGA_SCALE_LOT_TO_MIN_TP_USD=1, ou baixe OMEGA_MIN_TP_USD_CRYPTO_ALT.",
                                    asset,
                                    tf,
                                    _tp_usd_est,
                                    _thr_tp_usd,
                                    eff_tp,
                                    eff_lot or 0,
                                    _pip_val,
                                )
                                results.append(
                                    {
                                        "asset": asset,
                                        "timeframe": tf,
                                        "status": "SKIP_MIN_TP_USD",
                                        "tp_usd_est": round(_tp_usd_est, 4),
                                        "min_tp_usd": _thr_tp_usd,
                                    }
                                )
                                continue
                        log.info("[%s %s] [%s] lot=%.2f execTF=%s atr=%.1f SL=%.0fpts($%.2f) TP=%.0fpts RR=1:%.2f conf=%.2f",
                                 asset, tf, _prof["regime"].upper(), eff_lot,
                                 _exec_atr["tf"], _exec_atr.get("atr_pts", 0),
                                 eff_sl, _risk_usd_eff, eff_tp,
                                 eff_tp / max(eff_sl, 1), _conf_score)

                        # === PSA-WIND Q4: AGGREGATE RISK CAP por ativo ===
                        # SL de um ativo NUNCA pode colocar em risco mais de 2% do equity total
                        # Soma risco existente (posições abertas do mesmo ativo) + proposta nova
                        _AGG_RISK_MAX_PCT = 0.02  # 2% do equity por ativo
                        try:
                            _existing_risk_usd = 0.0
                            for _el_v in _pos_ledger.values():
                                if _el_v.get("symbol") == asset and _el_v.get("status") == "open":
                                    _el_sl = _el_v.get("sl_pts", eff_sl)  # se não tem, assume o mesmo SL
                                    _el_lot = _el_v.get("lot", 0)
                                    _existing_risk_usd += _el_sl * _pip_val * _el_lot
                            _total_agg_risk = _existing_risk_usd + _risk_usd_eff
                            _max_agg_usd = equity * _AGG_RISK_MAX_PCT
                            if _total_agg_risk > _max_agg_usd:
                                log.warning("[%s %s] [AGG_RISK] BLOCKED — risco_agregado=$%.2f > max=$%.2f (%.1f%% equity) | existente=$%.2f + novo=$%.2f",
                                            asset, tf, _total_agg_risk, _max_agg_usd,
                                            _AGG_RISK_MAX_PCT * 100, _existing_risk_usd, _risk_usd_eff)
                                results.append({"asset": asset, "timeframe": tf,
                                               "status": "SKIP_AGG_RISK_CAP",
                                               "agg_risk_usd": round(_total_agg_risk, 2),
                                               "max_usd": round(_max_agg_usd, 2)})
                                continue
                            log.info("[%s %s] [AGG_RISK] OK — risco_total=$%.2f / max=$%.2f",
                                     asset, tf, _total_agg_risk, _max_agg_usd)
                        except Exception as _agg_err:
                            log.debug("[%s %s] [AGG_RISK] erro (não bloqueia): %s", asset, tf, _agg_err)

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

                        # C3 FIX: sl_pts_min de perfil + sanitize_sl_tp (cap R:R 59:1 → 8:1)
                        _sl_pts_min_prof = float(_prof.get("sl_pts_min", 0.0))
                        if _sl_pts_min_prof > 0:
                            eff_sl = max(eff_sl, _sl_pts_min_prof)
                        eff_sl, eff_tp = sanitize_sl_tp(eff_sl, eff_tp, _exec_atr.get("atr_pts", 0.0), asset)

                        # ── ZONE NAVIGATOR GATE (CEO 2026-05-14) ──────────────────────
                        # Camada 1: regime filter — bloqueia BUFFER e lateralidade
                        if _ZONE_NAV_AVAIL and _ZONE_NAV is not None:
                            try:
                                _tf_const_map_znav = {
                                    "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
                                    "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1,
                                    "H4": mt5.TIMEFRAME_H4, "D1": mt5.TIMEFRAME_D1,
                                }
                                _znav_rates = mt5.copy_rates_from_pos(
                                    asset, _tf_const_map_znav.get(tf, mt5.TIMEFRAME_H1), 0, 80
                                )
                                _znav_res = _ZONE_NAV.evaluate_for_shadow_loop(
                                    asset, tf, signal_dir, _znav_rates
                                )
                                if not _znav_res.get("can_trade", True):
                                    _znav_reason = _znav_res.get("reason", "ZONE_BLOCKED")
                                    log.info("[%s %s] [ZONE] BLOCKED — %s (score=%.3f fuel=%.3f)",
                                             asset, tf, _znav_reason,
                                             _znav_res.get("score", 0),
                                             _znav_res.get("fuel", 0))
                                    results.append({"asset": asset, "timeframe": tf,
                                                    "status": "SKIP_ZONE_GATE",
                                                    "reason": _znav_reason,
                                                    "zone":   _znav_res.get("zone", "?")})
                                    continue
                                log.debug("[%s %s] [ZONE] OK — %s score=%.3f bias=%s",
                                          asset, tf,
                                          _znav_res.get("zone", "?"),
                                          _znav_res.get("score", 0),
                                          "ok" if _znav_res.get("bias_ok") else "conflict")
                            except Exception as _znav_err:
                                log.debug("[%s %s] [ZONE] erro ignorado: %s", asset, tf, _znav_err)
                        # ── FIM ZONE NAVIGATOR GATE ────────────────────────────────────

                        # ── TESSERACT SNIPER GATE — XAUUSD M5 SPECIALIST (CEO 2026-05-14) ──
                        # Apenas para XAUUSD em M5. Nos outros activos/TFs passa transparente.
                        # Se activo: substitui signal_dir, eff_sl, eff_tp pelos valores do Sniper.
                        if _TESSERACT_AVAIL and _TESSERACT is not None \
                                and asset == "XAUUSD" and tf == "M5":
                            try:
                                _tess_h4 = _build_sniper_df(
                                    mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H4, 0, 80))
                                _tess_h1 = _build_sniper_df(
                                    mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 60))
                                _tess_m5 = _build_sniper_df(
                                    mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M5, 0, 60))
                                _tess_sig = _TESSERACT.evaluate(_tess_h4, _tess_h1, _tess_m5)

                                if not _tess_sig.execute:
                                    log.info(
                                        "[XAUUSD M5] [TESSERACT] BLOCKED — %s",
                                        _tess_sig.reason,
                                    )
                                    results.append({"asset": asset, "timeframe": tf,
                                                    "status": "SKIP_TESSERACT",
                                                    "reason": _tess_sig.reason})
                                    continue

                                # Confluência confirmada — sobrescrever direcção e risco
                                signal_dir = _tess_sig.direction
                                eff_sl     = _tess_sig.sl_pts
                                eff_tp     = _tess_sig.tp2_pts   # Linha Vetorial 1.618
                                log.info(
                                    "[XAUUSD M5] [TESSERACT] EXECUTE %s | conf=%.2f | "
                                    "entry=%s | vol_surge=%.2fx | SL=%.1f TP=%.1f",
                                    signal_dir, _tess_sig.confidence,
                                    _tess_sig.entry_type,
                                    _tess_sig.vol_surge_ratio,
                                    eff_sl, eff_tp,
                                )
                            except Exception as _tess_err:
                                log.debug("[XAUUSD M5] [TESSERACT] erro ignorado: %s", _tess_err)
                        # ── FIM TESSERACT SNIPER GATE ──────────────────────────────────────

                        # ── ZAK MIR GUARDRAIL — MACRO GEOMETRY GATE (CEO 2026-05-13) ──
                        # Ordem: ZAK (macro: RSI50+SMA50+Exaustão) → M1-GATE (micro) → Ordem
                        if _ZAK_GUARDRAIL_AVAIL and _ZAK_GUARDRAIL is not None:
                            try:
                                _tf_const_map = {
                                    "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
                                    "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1,
                                    "H4": mt5.TIMEFRAME_H4, "D1": mt5.TIMEFRAME_D1,
                                }
                                _zak_tf = _tf_const_map.get(tf, mt5.TIMEFRAME_H1)
                                _zak_rates = mt5.copy_rates_from_pos(asset, _zak_tf, 0, 250)
                                if _zak_rates is not None and len(_zak_rates) >= 50:
                                    import pandas as pd
                                    _zak_df = pd.DataFrame(_zak_rates)
                                    _zak_df.rename(columns={"open":"open","high":"high",
                                                            "low":"low","close":"close"}, inplace=True)
                                    _zak_df = _ZAK_GUARDRAIL.compute_indicators(_zak_df)
                                    _zak_res = _ZAK_GUARDRAIL.validate_entry(asset, tf, signal_dir, _zak_df)
                                    if not _zak_res.get("valid", True):
                                        _zak_reason = _zak_res.get("reason", "ZAK_BLOCKED")
                                        _zak_risk   = _zak_res.get("risk_level", "UNKNOWN")
                                        log.info("[%s %s] [ZAK] BLOCKED — %s (risk=%s)",
                                                 asset, tf, _zak_reason, _zak_risk)
                                        results.append({"asset": asset, "timeframe": tf,
                                                        "status": "SKIP_ZAK_GATE",
                                                        "reason": _zak_reason,
                                                        "risk_level": _zak_risk})
                                        continue
                                    log.info("[%s %s] [ZAK] OK — %s", asset, tf,
                                             _zak_res.get("reason", "ZAK_MIR_VALIDATED"))
                            except Exception as _zak_err:
                                # ZAK falha = não bloqueia (é filtro adicional, não obrigatório)
                                log.debug("[%s %s] [ZAK] erro ignorado: %s", asset, tf, _zak_err)

                        # ── OMEGA MARKET PROFILE GATE — STRUCTURAL LEVEL FILTER (CEO 2026-05-14) ──
                        # Ordem no pipeline: ZAK → [MP-GATE] → M1-GATE → Lock → Ordem
                        # Bloqueia se: shark_absorption >= 0.75 (absorção institucional activa)
                        # Boost TP se: rPOC resonance confirmado (POC alinhado com 3 dias)
                        # Falha = NÃO bloqueia (filtro adicional, não obrigatório)
                        if _MP_AVAIL and _MPEngineCls is not None:
                            try:
                                import pandas as _pd_mp
                                # Lazy engine init por activo (uma vez em memória)
                                if asset not in _MP_ENGINES:
                                    _mp_regime = _get_mp_regime(asset, _prof.get("regime", "forex"))
                                    _MP_ENGINES[asset] = _MPEngineCls.from_regime(_mp_regime)
                                _mp_eng = _MP_ENGINES[asset]

                                # Fetch H1 OHLCV (200 barras)
                                _mp_rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_H1, 0, 200)
                                if _mp_rates is not None and len(_mp_rates) >= 20:
                                    _mp_df = _pd_mp.DataFrame(_mp_rates)
                                    if "tick_volume" in _mp_df.columns and "volume" not in _mp_df.columns:
                                        _mp_df["volume"] = _mp_df["tick_volume"]

                                    # D1 closes (D-3, D-2, D-1)
                                    _d1_rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_D1, 0, 6)
                                    _prev_closes: list = []
                                    if _d1_rates is not None and len(_d1_rates) >= 4:
                                        _prev_closes = list(
                                            _pd_mp.DataFrame(_d1_rates)["close"].iloc[-4:-1].values
                                        )

                                    # Calcular perfil estrutural
                                    _mp_state = _mp_eng.compute_from_bars(
                                        _mp_df,
                                        prev_closes=_prev_closes,
                                        tf="H1",
                                    )

                                    if _mp_state.is_valid:
                                        _tick_mp     = mt5.symbol_info_tick(asset)
                                        _cur_price_mp = (
                                            _tick_mp.bid if signal_dir == "SELL" else _tick_mp.ask
                                        ) if _tick_mp else _mp_df["close"].iloc[-1]
                                        _mp_ctx = _mp_state.to_signal_context(float(_cur_price_mp))

                                        # ── BLOCK: absorção institucional activa ─────────
                                        if _mp_ctx.get("shark_signal") == "BLOCK":
                                            log.info(
                                                "[%s %s] [MP-GATE] BLOCKED shark=%.3f POC=%.5f VA=%s",
                                                asset, tf,
                                                _mp_state.shark_absorption,
                                                _mp_state.poc,
                                                _mp_ctx.get("price_vs_va", "?"),
                                            )
                                            results.append({
                                                "asset": asset, "timeframe": tf,
                                                "status": "SKIP_MP_SHARK",
                                                "shark_absorption": _mp_state.shark_absorption,
                                                "poc": _mp_state.poc,
                                            })
                                            continue

                                        # ── TP BOOST: rPOC resonance confirmado ──────────
                                        if _mp_state.is_resonance and _mp_ctx.get("shark_signal") == "CLEAR":
                                            _mp_tp_boost = float(os.getenv("OMEGA_MP_TP_BOOST", "1.15"))
                                            eff_tp = round(eff_tp * _mp_tp_boost, 1)
                                            log.info(
                                                "[%s %s] [MP-GATE] rPOC RESONANCE — TP boost x%.2f → %.1f pts",
                                                asset, tf, _mp_tp_boost, eff_tp,
                                            )

                                        log.info(
                                            "[%s %s] [MP-GATE] OK POC=%.5f VA=%s score=%.3f "
                                            "shark=%.3f resonance=%s gap_fill=%.3f",
                                            asset, tf,
                                            _mp_state.poc,
                                            _mp_ctx.get("price_vs_va", "?"),
                                            _mp_state.strength,
                                            _mp_state.shark_absorption,
                                            _mp_state.is_resonance,
                                            _mp_state.gap_fill_prob,
                                        )
                            except Exception as _mp_err:
                                # Falha do MP não bloqueia execução
                                log.debug("[%s %s] [MP-GATE] erro ignorado: %s", asset, tf, _mp_err)
                        # ── FIM MARKET PROFILE GATE ────────────────────────────────────────

                        # ── MICRO ENTRY FILTER — M1 MANDATORY GATE (CEO 2026-05-12) ────
                        # REGRA: ordens SÓ se M1 confirmar. Sem confirmação M1 = sem ordem.
                        if _MICRO_FILTER_AVAIL and _MICRO_FILTER is not None:
                            try:
                                _mef_res = _MICRO_FILTER.evaluate(asset, signal_dir, tf)
                                if not _mef_res.execute:
                                    log.info("[%s %s] [M1-GATE] BLOCKED — %s (quality=%.2f)",
                                             asset, tf, _mef_res.reason, _mef_res.entry_quality)
                                    results.append({"asset": asset, "timeframe": tf,
                                                    "status": "SKIP_M1_GATE",
                                                    "reason": _mef_res.reason,
                                                    "quality": _mef_res.entry_quality})
                                    continue
                                # Ajustar SL com estrutura M1 (apertar se qualidade alta)
                                if _mef_res.sl_adj_pts != 0.0:
                                    eff_sl = max(eff_sl + _mef_res.sl_adj_pts,
                                                 float(_prof.get("sl_pts_min", 50)))
                                    log.info("[%s %s] [M1-GATE] SL ajustado %.0f pts (quality=%.2f)",
                                             asset, tf, eff_sl, _mef_res.entry_quality)
                                # Ajustar lote com qualidade M1
                                if _mef_res.lot_multiplier < 1.0 and eff_lot is not None:
                                    eff_lot = max(
                                        round(eff_lot * _mef_res.lot_multiplier, 2),
                                        0.01
                                    )
                                    log.info("[%s %s] [M1-GATE] lot ajustado (mult=%.2f quality=%.2f)",
                                             asset, tf, _mef_res.lot_multiplier, _mef_res.entry_quality)
                                log.info("[%s %s] [M1-GATE] OK quality=%.2f lot_mult=%.2f",
                                         asset, tf, _mef_res.entry_quality, _mef_res.lot_multiplier)
                            except Exception as _mef_err:
                                # M1 indisponivel = NAO EXECUTAR (regra CEO)
                                log.warning("[%s %s] [M1-GATE] ERRO — skip por seguranca: %s",
                                            asset, tf, _mef_err)
                                results.append({"asset": asset, "timeframe": tf,
                                                "status": "SKIP_M1_ERROR",
                                                "error": str(_mef_err)})
                                continue
                        else:
                            # Modulo indisponivel = NAO EXECUTAR (regra CEO: M1 e obrigatorio)
                            log.error("[%s %s] [M1-GATE] MicroEntryFilter INDISPONIVEL — skip",
                                      asset, tf)
                            results.append({"asset": asset, "timeframe": tf,
                                            "status": "SKIP_M1_UNAVAILABLE"})
                            continue

                        # ── ATOMIC LOCK — previne race condition (CEO 2026-05-12) ───────
                        if not _lock_acquire(timeout=3.0):
                            log.warning("[%s %s] [LOCK] Timeout — ciclo paralelo a executar, skip",
                                        asset, tf)
                            results.append({"asset": asset, "timeframe": tf,
                                            "status": "SKIP_LOCK_TIMEOUT"})
                            continue
                        try:
                            exec_result = mt5_send_order(
                                asset, tf, eff_lot,
                                sl_pts=eff_sl,
                                tp_pts=eff_tp,
                                direction=signal_dir)
                        finally:
                            _lock_release()
                        success = exec_result.get("success", False)
                        # Idempotência / dedup ticket
                        deal_id = exec_result.get("deal")
                        # PSA-WIND Q1: marcar ativo no ciclo em QUALQUER fill com sucesso.
                        # Não acoplar ao dedup de deal: se deal já estiver em _processed_tickets (colisão
                        # rara / reenvio), o ativo ainda assim abriu posição neste ciclo — sem isto o
                        # próximo TF podia voltar a enviar (duplicata XAUUSD mesmo lote/preço).
                        if success:
                            _cycle_opened_assets.add(asset)
                        if success and deal_id is not None and deal_id not in _processed_tickets:
                            _processed_tickets.add(deal_id)
                            _cycle_dir_count[signal_dir] = _cycle_dir_count.get(signal_dir, 0) + 1  # P&D counter
                            # Ledger: registra APENAS a nova posição (1 ticket por deal)
                            try:
                                _new_pos = mt5.positions_get(symbol=asset) or []
                                _registered_this_deal = False
                                for _np in _new_pos:
                                    if _registered_this_deal:
                                        break  # 1 ticket por deal — evitar duplicação
                                    if is_omega_tracked_position(_np) and _np.ticket not in _pos_ledger:
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
                                            "sl_pts": eff_sl, "tp_pts": eff_tp,
                                            "entry_atr_pts": _exec_atr.get("atr_pts", 0),
                                            "entry_atr_tf": _exec_atr.get("tf", "M3"),
                                            "entry_deal": deal_id,
                                            "signal_source": signal_source,
                                            "agent_id": (
                                                ia_agent_id
                                                if signal_source == "AGENT_IA"
                                                else None
                                            ),
                                            "confidence": round(_conf_score, 4),
                                            "regime": _prof["regime"],
                                            "risk_usd": round(_risk_usd_eff, 4),
                                            "entry_time": datetime.now(timezone.utc).isoformat(),
                                            "last_profit": _np.profit, "status": "open",
                                            "spread_cost_usd": _spread_cost,
                                            "slippage_pts": exec_result.get("slippage_pts", 0),
                                        }
                                        _registered_this_deal = True
                                        log.info("[LEDGER] entry=%s #%d lot=%.2f spread_cost=$%.4f slip_pts=%.1f",
                                                 asset, _np.ticket, eff_lot, _spread_cost,
                                                 exec_result.get("slippage_pts", 0))
                                        log.info("[LEDGER] Posicao aberta: %s #%d entry=%.5f",
                                                 asset, _np.ticket, _np.price_open)
                                        if agent_ia is not None and signal_source == "AGENT_IA":
                                            try:
                                                agent_ia.record_trade_open(
                                                    asset,
                                                    int(_np.ticket),
                                                    float(exec_result.get("fill_price", 0) or 0),
                                                    float(eff_lot),
                                                    ia_agent_id,
                                                )
                                                _agent_ia_open_ok += 1
                                            except Exception as _re:
                                                log.warning("[%s %s] record_trade_open falhou: %s", asset, tf, _re)
                                        # === PYRAMIDING: verificar se deve adicionar camadas após posição aberta ===
                                        try:
                                            _syms = mt5.positions_get(symbol=asset) if mt5.positions_get else []
                                            _open_pos_list = [
                                                p for p in (_syms or [])
                                                if is_omega_tracked_position(p)
                                            ]
                                            _prof_dict = {"profit": float(_np.profit) if hasattr(_np, 'profit') else 0.0}
                                            _atr_info = get_execution_tf_atr(asset, 0.70)
                                            _exec_atr_dict = {"atr_pts": _atr_info.get("atr_pts", 0)}
                                            _pyramid_decision = check_pyramid_add(
                                                symbol=asset,
                                                direction=signal_dir,
                                                open_positions=_open_pos_list,
                                                pos_ledger=_pos_ledger,
                                                prof=_prof_dict,
                                                exec_atr=_exec_atr_dict,
                                                equity=equity
                                            )
                                            if _pyramid_decision.get("add"):
                                                log.info("[PYRAMID] %s %s: ADD LAYER %d | lot=%.2f | reason=%s",
                                                         asset, tf, _pyramid_decision.get("layer"),
                                                         _pyramid_decision.get("lot"), _pyramid_decision.get("reason"))
                                        except Exception as _py_err:
                                            log.warning("[PYRAMID] Erro ao verificar pyramiding: %s", _py_err)
                                        # === PARTIAL_CLOSE: inicializar trava de lucro POR POSIÇÃO (PSA-WIND recalibrado) ===
                                        try:
                                            if _PARTIAL_CLOSE_AVAILABLE:
                                                _entry_price = exec_result.get("fill_price", _np.price_open)
                                                _pc_engine = _ProgressivePartialCloseCompleteCls()
                                                _dir_int = 1 if signal_dir == "BUY" else -1
                                                # PSA-WIND FIX 4: sobrescrever níveis agressivos por conservadores
                                                import copy as _copy_mod
                                                _pc_engine.levels = _copy_mod.deepcopy(_PARTIAL_CLOSE_LEVELS_PSA)
                                                _pc_engine.initialize_position(
                                                    entry_price=_entry_price,
                                                    lots=eff_lot,
                                                    direction=_dir_int
                                                )
                                                _partial_close_engines[_np.ticket] = _pc_engine
                                                _pos_ledger[_np.ticket]["partial_close"] = True
                                                log.info("[PARTIAL_CLOSE] %s #%d inicializado PSA-WIND | entry=%.5f lot=%.2f dir=%s levels=[0.7/1.5/2.5/4.0]ATR",
                                                         asset, _np.ticket, _entry_price, eff_lot, signal_dir)
                                        except Exception as _pc_err:
                                            log.warning("[PARTIAL_CLOSE] Erro ao inicializar: %s", _pc_err)
                                        # === PSA-WIND FIX 3: TRAILING STOP geométrico POR POSIÇÃO ===
                                        try:
                                            if _TRAILING_STOP_AVAILABLE:
                                                # CEO 2026-05-14 FIX: 1.5→1.0 trailing mais justo
                                                # Motivo: 1.5×ATR XAUUSD = ~525pts slack = posição pode reverter $5+ antes de fechar
                                                _ts_engine = _TrailingStopCls(atr_multiplier=1.0, min_multiplier=0.5)
                                                _ts_engine.entry_price = exec_result.get("fill_price", _np.price_open)
                                                _ts_engine._peak_price = _ts_engine.entry_price
                                                _trailing_stop_engines[_np.ticket] = _ts_engine
                                                log.info("[TRAILING] %s #%d inicializado | entry=%.5f atr_mult=1.0",
                                                         asset, _np.ticket, _ts_engine.entry_price)
                                        except Exception as _ts_err:
                                            log.warning("[TRAILING] Erro ao inicializar: %s", _ts_err)
                            except Exception as _le:
                                log.warning("[LEDGER] Erro ao registrar posicao: %s", _le)
                        # Log de auditoria do source
                        log.info("[%s %s] FASE4 EXEC source=%s success=%s deal=%s",
                                 asset, tf, signal_source, success, deal_id)
                        if MAX_POSITIONS > 0:
                            open_pos = min(open_pos + (1 if success else 0), MAX_POSITIONS)
                        else:
                            open_pos = open_pos + (1 if success else 0)
                        _ks_rc = (exec_result or {}).get("retcode") if exec_result else None
                        ks.update(success, 0.0, _ks_rc)
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
                decision_trace_append(
                    {
                        "asset": asset,
                        "timeframe": tf,
                        "phase": "cycle_end",
                        "class": classify_asset(asset),
                        "mode": mode,
                        "signal_action": action,
                        "hit_rate_134": hr_real,
                        "guard_skip": bool(guard.get("skip")),
                        "skip_reasons": guard.get("skip_reasons") or [],
                        "margin_pts": guard.get("margin_used"),
                        "harmonic_latency_s": harmonic.get("_latency_s"),
                        "signal_source": signal_source,
                        "flow_confluence": _flow_details if _flow_details else None,
                        "retcode": (exec_result or {}).get("retcode"),
                        "report_path": str(out_f),
                    }
                )
    finally:
        if mt5_connected:
            # Ledger: snapshot P&L final de todas as posicoes OMEGA antes de desconectar
            try:
                _rack_fin = mt5.positions_get() or []
                _all_open = filter_omega_tracked_positions(list(_rack_fin))
                for _p in _all_open:
                    if _p.ticket in _pos_ledger:
                        _pos_ledger[_p.ticket]["last_profit"] = _p.profit
                        _atr_info = get_execution_tf_atr(_p.symbol, 0.70)
                        _current_price = _p.price_current if hasattr(_p, 'price_current') else (_p.bid if _p.type == 1 else _p.ask)
                        _atr_pts_val = _atr_info.get("atr_pts", 0)
                        # Converter ATR de pontos para unidades de preço (trailing stop opera em preço)
                        try:
                            _sym_point = mt5.symbol_info(_p.symbol).point if mt5.symbol_info(_p.symbol) else 0.0001
                        except Exception:
                            _sym_point = 0.0001
                        _atr_price = _atr_pts_val * _sym_point
                        # === PSA-WIND: TRAILING STOP — atualizar SL broker + fechar no EXIT_TRIGGER ===
                        try:
                            _ts_eng = _trailing_stop_engines.get(_p.ticket)
                            if _ts_eng is not None and _atr_price > 0:
                                _dir_int_ts = 1 if _p.type == 0 else -1
                                _new_sl_val, _exit_trigger = _ts_eng.update(_current_price, _atr_price, _dir_int_ts)
                                if _new_sl_val is not None:
                                    _old_sl = _pos_ledger[_p.ticket].get("trailing_sl")
                                    _sl_moved = (_old_sl is None or
                                                 abs(_new_sl_val - _old_sl) > _atr_pts_val * 0.01)
                                    if _sl_moved:
                                        _pos_ledger[_p.ticket]["trailing_sl"] = _new_sl_val
                                        log.info("[TRAILING] %s #%d | price=%.5f peak=%.5f trail_SL=%.5f exit=%s",
                                                 _p.symbol, _p.ticket, _current_price,
                                                 _ts_eng._peak_price, _new_sl_val, _exit_trigger)
                                        # WIRING BUG-4: Mover SL no broker via TRADE_ACTION_SLTP
                                        _cur_tp_ts = float(_p.tp) if _p.tp else 0.0
                                        _sl_mod = mt5_modify_position_sl(
                                            _p.ticket, _p.symbol, _new_sl_val, _cur_tp_ts)
                                        if not _sl_mod.get("success"):
                                            log.warning("[TRAILING] %s #%d SL broker modify falhou: %s",
                                                        _p.symbol, _p.ticket, _sl_mod.get("error"))
                                if _exit_trigger:
                                    log.warning("[TRAILING] %s #%d EXIT TRIGGER — trailing stop atingido price=%.5f SL=%.5f",
                                                _p.symbol, _p.ticket, _current_price, _new_sl_val)
                                    # WIRING BUG-4: Fechar posição completa quando trailing dispara
                                    _dir_str_ts = "BUY" if _p.type == 0 else "SELL"
                                    _ts_close = mt5_close_partial(
                                        _p.ticket, _p.symbol, _p.volume, _dir_str_ts)
                                    if _ts_close.get("success"):
                                        log.info("[TRAILING] %s #%d ✅ FECHADA trailing @ %.5f (%.1fms)",
                                                 _p.symbol, _p.ticket,
                                                 _ts_close.get("fill_price", 0), _ts_close.get("latency_ms", 0))
                                    else:
                                        log.error("[TRAILING] %s #%d ❌ close falhou: %s — SL broker já actualizado",
                                                  _p.symbol, _p.ticket, _ts_close.get("error"))
                        except Exception as _ts_check_err:
                            log.debug("[TRAILING] Erro ao verificar: %s", _ts_check_err)
                        # === PARTIAL_CLOSE: fechar parcialmente + breakeven via MT5 (BUG-4 FIX) ===
                        try:
                            _pc_eng = _partial_close_engines.get(_p.ticket)
                            if _pc_eng is not None and _atr_price > 0:
                                _dir_str_pc = "BUY" if _p.type == 0 else "SELL"
                                _partial_orders = _pc_eng.check_partials(
                                    current_price=_current_price,
                                    atr_value=_atr_price
                                )
                                for _order in _partial_orders:
                                    if _order["action"] == "CLOSE_PARTIAL":
                                        log.info("[PARTIAL_CLOSE] %s #%d: %.2f lotes | %s | move_atr=%.2f",
                                                 _p.symbol, _p.ticket, _order["lots"],
                                                 _order["reason"], _order.get("move_atr", 0))
                                        # WIRING BUG-4: Executar fecho parcial real via MT5
                                        _pc_res = mt5_close_partial(
                                            _p.ticket, _p.symbol, _order["lots"], _dir_str_pc)
                                        if not _pc_res.get("success"):
                                            log.error("[PARTIAL_CLOSE] %s #%d ❌ fecho parcial falhou: %s",
                                                      _p.symbol, _p.ticket, _pc_res.get("error"))
                                    elif _order["action"] == "MOVE_SL_TO_ENTRY":
                                        log.info("[PARTIAL_CLOSE] %s #%d: SL moved to breakeven | %s",
                                                 _p.symbol, _p.ticket, _order["reason"])
                                        # WIRING BUG-4: Mover SL para entry price (breakeven) via broker
                                        _entry_be = float(
                                            _pos_ledger[_p.ticket].get("entry_price", _p.price_open))
                                        _cur_tp_be = float(_p.tp) if _p.tp else 0.0
                                        _be_res = mt5_modify_position_sl(
                                            _p.ticket, _p.symbol, _entry_be, _cur_tp_be)
                                        if not _be_res.get("success"):
                                            log.error("[PARTIAL_CLOSE] %s #%d ❌ breakeven SL falhou: %s",
                                                      _p.symbol, _p.ticket, _be_res.get("error"))
                        except Exception as _pc_check_err:
                            log.warning("[PARTIAL_CLOSE] Erro ao verificar: %s", _pc_check_err)
                    else:
                        _pos_ledger[_p.ticket] = {
                            "symbol": _p.symbol, "direction": "BUY" if _p.type == 0 else "SELL",
                            "lot": _p.volume, "entry_price": _p.price_open,
                            "sl": float(_p.sl) if _p.sl else None,
                            "tp": float(_p.tp) if _p.tp else None,
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
    # P2-C C5 FIX: skip table acumulativa (era destruída a cada ciclo → zero visibilidade)
    skip_out  = AUDIT_PAPER / "skip_table.json"
    _existing_skips: list = []
    if skip_out.exists():
        try:
            _ex_data = json.loads(skip_out.read_text(encoding="utf-8"))
            _existing_skips = _ex_data.get("skips", [])
        except Exception:
            pass
    _merged_skips = _existing_skips + skip_tbl
    skip_data = {"generated": datetime.now(timezone.utc).isoformat(), "skips": _merged_skips[-5000:]}
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
    _exit_code, _exit_detail = classify_cycle_exit_reason(ks)
    _eval_ctx_run_end = build_evaluation_context()
    summary = {
        "mode": mode, "generated": now, "equity_demo": equity,
        "total_cycles": len(results),
        "kill_switch": ks.triggered, "ks_reason": ks.reason,
        "exit_reason": _exit_code,
        "exit_detail": _exit_detail,
        "evaluation_calendar_run_start": _eval_ctx_run_start,
        "evaluation_calendar_run_end": _eval_ctx_run_end,
        "online_stats": stat_sum, "results": results,
        "log_file": str(log_file),
        "positions_ledger": _ledger_sum,
        "lot_calc_v2": _lot_calc.diagnostics(),
        "trade_feedback_loop": {
            "trade_feedback_jsonl": str(AUDIT_PAPER / "trade_feedback.jsonl"),
            "closed_trades_logged": _trade_feedback_n,
            "agent_ia_record_trade_open_ok": _agent_ia_open_ok,
            "agent_ia_record_trade_close_ok": _agent_ia_close_ok,
            "agent_ia_record_trade_close_err": _agent_ia_close_err,
            "note": "Comparar closed_trades_logged com realized_n; IA: open_ok vs close_ok (posições ainda abertas no fim do run explicam diferença).",
        },
    }
    sb = json.dumps(summary, indent=2).encode("utf-8")
    summary["checksum"] = sha3(sb)
    sum_out = AUDIT_PAPER / "paper_summary.json"
    with open(sum_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    try:
        _cycle_exit_payload = {
            "generated": now,
            "mode": mode,
            "exit_reason": _exit_code,
            "exit_detail": _exit_detail,
            "kill_switch": ks.triggered,
            "ks_reason": ks.reason,
            "total_cycles": len(results),
            "paper_summary_checksum": summary["checksum"],
            "evaluation_calendar_run_start": _eval_ctx_run_start,
            "evaluation_calendar_run_end": _eval_ctx_run_end,
        }
        (AUDIT_PAPER / "cycle_exit.json").write_text(
            json.dumps(_cycle_exit_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _append_evaluation_timeline_row(
            AUDIT_PAPER,
            {
                "generated": now,
                "event": "run_end",
                "exit_reason": _exit_code,
                "exit_detail": _exit_detail,
                "kill_switch": ks.triggered,
                "evaluation_calendar_run_start": _eval_ctx_run_start,
                "evaluation_calendar_at_exit": _eval_ctx_run_end,
            },
        )
    except Exception as _ce_err:
        log.warning("cycle_exit.json: %s", _ce_err)
    if _exit_code != "NORMAL_COMPLETION" or ks.triggered:
        log.critical(
            "[CYCLE_EXIT] reason=%s detail=%s ks_triggered=%s",
            _exit_code,
            _exit_detail or "-",
            ks.triggered,
        )
    else:
        log.info("[CYCLE_EXIT] reason=%s (run concluído sem kill-switch intraday)", _exit_code)

    log.info("[EVAL_CONTEXT] run_end | %s", format_eval_log_line(_eval_ctx_run_end))

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
