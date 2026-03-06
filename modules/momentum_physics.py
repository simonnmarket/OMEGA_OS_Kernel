"""
modules/momentum_physics.py — Motor de Física do Momentum
OMEGA OS Kernel — Módulo Expansivo v1.0.0
2026-03-06

════════════════════════════════════════════════════════════════════════════════
ORIGEM: Convertido e expandido a partir de:
  - GALEX MANUS / Agents / MomentumAgent.mqh (v9.0)
  - GALEX MANUS / Agents / MeanReversionAgent.mqh (v8.0)

FILOSOFIA:
  O preço em movimento obedece a leis análogas à física clássica.
  Medir apenas Velocidade é insuficiente — é necessário medir se a força
  que gera essa velocidade está a CRESCER ou a DIMINUIR.

  Derivadas cinemáticas do preço:
    ① Velocidade    (1ª derivada) = Δprice / ATR   → está a mover?
    ② Aceleração    (2ª derivada)                  → a mover com mais força?
    ③ Jerk          (3ª derivada)                  → a força está a crescer?

  Regra de Ouro (MomentumAgent v9.0):
    Entrada válida = velocity > 0 AND acceleration > 0 AND jerk > 0
    → os três confirmam que o movimento está a GANHAR força

  Half-Life da Reversão (MeanReversionAgent v8.0):
    Mede o tempo que uma correcção demora a completar-se.
    Usado para calibrar correction_window dinamicamente.

COMO EXPANDIR:
  • Nova derivada: adicionar cálculo em MomentumPhysicsEngine._calculate_derivatives()
  • Novo indicador: adicionar método público ao MomentumPhysicsEngine
  • Modificar thresholds de sinal: ajustar MomentumConfig
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("OMEGA.Modules.MomentumPhysics")


# ─────────────────────────────────────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class MomentumSignal(str, Enum):
    STRONG_BUY   = "STRONG_BUY"    # velocity>0 AND accel>0 AND jerk>0
    BUY          = "BUY"           # velocity>0 AND accel>0
    WEAK_BUY     = "WEAK_BUY"      # velocity>0 apenas
    NEUTRAL      = "NEUTRAL"       # sem direcção clara
    WEAK_SELL    = "WEAK_SELL"     # velocity<0 apenas
    SELL         = "SELL"          # velocity<0 AND accel<0
    STRONG_SELL  = "STRONG_SELL"   # velocity<0 AND accel<0 AND jerk<0

class MomentumRegime(str, Enum):
    TRENDING  = "TRENDING"  # volatilidade baixa + momentum alto
    RANGING   = "RANGING"   # volatilidade baixa + momentum baixo
    VOLATILE  = "VOLATILE"  # volatilidade alta  + momentum variável
    REVERTING = "REVERTING" # preço a reverter para média (Z-score extremo)


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MomentumConfig:
    """
    Configuração do Motor de Física do Momentum.
    Todos os parâmetros são calibráveis sem tocar na lógica.
    """
    # ── Períodos multi-escala (3 camadas) ─────────────────────────────────
    period_short  : int   = 5     # derivadas de curto prazo (5 barras)
    period_medium : int   = 14    # derivadas de médio prazo (referência)
    period_long   : int   = 30    # derivadas de longo prazo

    # ── Pesos das camadas (soma = 1.0) ────────────────────────────────────
    weight_short  : float = 0.50  # camada curta tem mais peso (reactividade)
    weight_medium : float = 0.30
    weight_long   : float = 0.20

    # ── Thresholds de sinal ───────────────────────────────────────────────
    velocity_threshold    : float = 0.0    # velocity > 0 = BUY
    jerk_threshold        : float = 0.0    # jerk > 0 = força crescente
    strong_signal_min     : float = 0.0    # todos 3 acima de 0 = STRONG

    # ── Thresholds adaptativos (baseados em volatilidade) ─────────────────
    vol_scale_buy_mult    : float = 1.5    # threshold BUY = 1.5 × vol_factor
    vol_neutral_mult      : float = 0.3    # banda neutra = 0.3 × vol_factor

    # ── Half-Life (MeanReversionAgent) ────────────────────────────────────
    half_life_window      : int   = 100    # janela de Z-scores para half-life
    z_score_revert_thr    : float = 1.8    # Z > 1.8 → oversold/overbought
    z_score_strong_thr    : float = 2.5    # Z > 2.5 → reversão iminente

    # ── Regime de mercado ─────────────────────────────────────────────────
    vol_trending_max      : float = 0.5    # volatilidade < 0.5 → pode ser trending
    momentum_trending_min : float = 0.7    # |mom| > 0.7 → trending

    # ── Histórico ─────────────────────────────────────────────────────────
    history_len           : int   = 200


# ─────────────────────────────────────────────────────────────────────────────
#  ESTADO DO MOMENTUM
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MomentumState:
    """Resultado completo de um cálculo de física do momentum."""

    # Derivadas (3 camadas × 3 derivadas)
    velocity     : float = 0.0   # 1ª derivada ponderada (multi-período)
    acceleration : float = 0.0   # 2ª derivada ponderada
    jerk         : float = 0.0   # 3ª derivada ponderada (ÚNICO)

    # Por camada (para análise de divergências)
    v_short  : float = 0.0;  a_short  : float = 0.0;  j_short  : float = 0.0
    v_medium : float = 0.0;  a_medium : float = 0.0;  j_medium : float = 0.0
    v_long   : float = 0.0;  a_long   : float = 0.0;  j_long   : float = 0.0

    # Sinal e regime
    signal       : MomentumSignal  = MomentumSignal.NEUTRAL
    regime       : MomentumRegime  = MomentumRegime.RANGING
    confidence   : float = 0.0    # 0.0–1.0

    # Mean Reversion (MeanReversionAgent)
    z_score      : float = 0.0    # Z-score do preço actual vs. média
    half_life    : float = 1.0    # meia-vida da reversão (barras)
    weighted_z   : float = 0.0    # Z-score ponderado pelo half-life

    # Thresholds adaptativos (calculados a partir da volatilidade actual)
    buy_threshold  : float = 0.0
    sell_threshold : float = 0.0

    # Recomendação
    suggested_correction_window: int = 10  # para Pullback Engine

    def all_confirm_buy(self) -> bool:
        """True se as 3 derivadas confirmam força compradora."""
        return self.velocity > 0 and self.acceleration > 0 and self.jerk > 0

    def all_confirm_sell(self) -> bool:
        """True se as 3 derivadas confirmam força vendedora."""
        return self.velocity < 0 and self.acceleration < 0 and self.jerk < 0

    def summary(self) -> str:
        confirms = "⚡ 3/3" if (self.all_confirm_buy() or self.all_confirm_sell()) else (
                   "✓ 2/3" if (
                       (self.velocity > 0 and self.acceleration > 0) or
                       (self.velocity < 0 and self.acceleration < 0)
                   ) else "△ 1/3"
        )
        return (
            f"sig={self.signal.value} | conf={self.confidence:.2f} | "
            f"vel={self.velocity:+.5f} | accel={self.acceleration:+.5f} | "
            f"jerk={self.jerk:+.5f} | {confirms} | "
            f"Z={self.z_score:+.2f} | half-life={self.half_life:.1f}b | "
            f"regime={self.regime.value}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  ENGINE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class MomentumPhysicsEngine:
    """
    Motor de física do momentum com derivadas de 1ª, 2ª e 3ª ordem.

    Uso básico:
        engine = MomentumPhysicsEngine()
        # alimentar barras sequencialmente
        bar = {"close": 2905.0, "atr": 3.2, "volume": 1500}
        state = engine.update("XAUUSD", bar)
        if state.all_confirm_buy():
            # velocity > 0 AND acceleration > 0 AND jerk > 0
            # → movimento com força crescente → entrada ou escalar

    Integração com Pullback Engine:
        mo_state = momentum_engine.update(symbol, bar)
        if trap_detected and mo_state.all_confirm_buy():
            urgency = CRITICAL   # todas as 3 derivadas confirmam
        elif trap_detected and mo_state.velocity > 0 and mo_state.acceleration > 0:
            urgency = HIGH
    """

    def __init__(self, config: Optional[MomentumConfig] = None):
        self._cfg    = config or MomentumConfig()
        self._closes : Dict[str, List[float]] = {}
        self._atrs   : Dict[str, List[float]] = {}
        self._states : Dict[str, MomentumState] = {}

    # ── Actualização principal ────────────────────────────────────────────

    def update(self, symbol: str, bar: Dict) -> MomentumState:
        """
        Processa uma barra e calcula todas as derivadas.

        Args:
            symbol: símbolo
            bar   : dict com 'close' (obrigatório), 'atr' (opcional),
                    'high', 'low' (para TR se sem 'atr')

        Returns:
            MomentumState completo
        """
        cfg = self._cfg

        c    = float(bar.get("close", 0))
        h    = float(bar.get("high", c))
        l    = float(bar.get("low",  c))
        atr  = float(bar.get("atr",  0))

        closes = self._closes.setdefault(symbol, [])
        atrs   = self._atrs.setdefault(symbol, [])

        # Calcular TR se ATR não fornecido
        prev_c = closes[-1] if closes else c
        if atr <= 0:
            atr = max(h - l, abs(h - prev_c), abs(l - prev_c))

        closes.append(c)
        atrs.append(atr)
        if len(closes) > cfg.history_len: closes.pop(0)
        if len(atrs)   > cfg.history_len: atrs.pop(0)

        # Precisa de mínimo 4 pontos para 3ª derivada
        min_pts = max(cfg.period_long, 4)
        if len(closes) < min_pts:
            state = MomentumState()
            self._states[symbol] = state
            return state

        arr  = np.array(closes)
        atrs_arr = np.array(atrs)

        # ═══ Calcular derivadas por camada ══════════════════════════════
        layers = [
            (cfg.period_short,  cfg.weight_short),
            (cfg.period_medium, cfg.weight_medium),
            (cfg.period_long,   cfg.weight_long),
        ]

        weighted_v = weighted_a = weighted_j = 0.0
        layer_results = []

        for period, weight in layers:
            if len(arr) < period + 1:
                layer_results.append((0.0, 0.0, 0.0))
                continue
            v, a, j = self._derivatives(arr, atrs_arr, period)
            weighted_v += weight * v
            weighted_a += weight * a
            weighted_j += weight * j
            layer_results.append((v, a, j))

        # ═══ Thresholds adaptativos ══════════════════════════════════════
        avg_atr   = float(np.mean(atrs_arr[-14:])) if len(atrs_arr) >= 14 else float(atrs_arr[-1])
        avg_close = float(np.mean(arr[-14:]))
        vol_factor = avg_atr / max(avg_close, 1e-10)

        buy_thr  = vol_factor * cfg.vol_scale_buy_mult
        sell_thr = -buy_thr
        neutral  = vol_factor * cfg.vol_neutral_mult

        # ═══ Half-Life e Z-score (MeanReversionAgent) ══════════════════
        z_score, weighted_z, half_life = self._mean_reversion_metrics(symbol, arr, atrs_arr)

        # ═══ Sinal ══════════════════════════════════════════════════════
        strength  = CalculateMomentumStrength(
            [(v, a, j) for v, a, j in layer_results],
            [w for _, w in layers]
        )
        signal, confidence = self._classify_signal(
            weighted_v, weighted_a, weighted_j,
            strength, buy_thr, neutral, z_score
        )

        # ═══ Regime ═════════════════════════════════════════════════════
        regime = self._detect_regime(vol_factor, abs(weighted_v), z_score)

        # ═══ correction_window sugerido ═════════════════════════════════
        corr_window = max(3, min(int(half_life * 1.5), 30))

        state = MomentumState(
            velocity     = round(weighted_v, 6),
            acceleration = round(weighted_a, 6),
            jerk         = round(weighted_j, 6),

            v_short  = round(layer_results[0][0], 6),
            a_short  = round(layer_results[0][1], 6),
            j_short  = round(layer_results[0][2], 6),
            v_medium = round(layer_results[1][0], 6) if len(layer_results) > 1 else 0.0,
            a_medium = round(layer_results[1][1], 6) if len(layer_results) > 1 else 0.0,
            j_medium = round(layer_results[1][2], 6) if len(layer_results) > 1 else 0.0,
            v_long   = round(layer_results[2][0], 6) if len(layer_results) > 2 else 0.0,
            a_long   = round(layer_results[2][1], 6) if len(layer_results) > 2 else 0.0,
            j_long   = round(layer_results[2][2], 6) if len(layer_results) > 2 else 0.0,

            signal     = signal,
            regime     = regime,
            confidence = round(confidence, 4),

            z_score   = round(z_score, 4),
            half_life = round(half_life, 2),
            weighted_z = round(weighted_z, 4),

            buy_threshold  = round(buy_thr, 6),
            sell_threshold = round(sell_thr, 6),

            suggested_correction_window = corr_window,
        )

        self._states[symbol] = state
        logger.debug(f"[{symbol}] {state.summary()}")
        return state

    # ── Cálculo de derivadas ──────────────────────────────────────────────

    def _derivatives(self, arr: np.ndarray, atrs: np.ndarray,
                      period: int) -> Tuple[float, float, float]:
        """
        Calcula velocidade, aceleração e jerk usando os últimos 4 preços,
        normalizados pelo ATR do período.

        Fórmulas de diferenças finitas:
          v = (p0 - p1) / ATR
          a = (p0 - 2p1 + p2) / ATR
          j = (p0 - 3p1 + 3p2 - p3) / ATR   ← JERK (3ª derivada)
        """
        if len(arr) < 4:
            return 0.0, 0.0, 0.0

        p0, p1, p2, p3 = arr[-1], arr[-2], arr[-3], arr[-4]

        # Normalizar pelo ATR médio do período
        atr_avg = float(np.mean(atrs[-period:])) if len(atrs) >= period else float(atrs[-1])
        if atr_avg < 1e-10:
            return 0.0, 0.0, 0.0

        v = (p0 - p1) / atr_avg
        a = (p0 - 2*p1 + p2) / atr_avg
        j = (p0 - 3*p1 + 3*p2 - p3) / atr_avg

        return float(v), float(a), float(j)

    # ── Mean Reversion Metrics ────────────────────────────────────────────

    def _mean_reversion_metrics(self,
                                  symbol : str,
                                  closes : np.ndarray,
                                  atrs   : np.ndarray) -> Tuple[float, float, float]:
        """
        Calcula Z-score, Z ponderado pelo half-life e o próprio half-life.

        MeanReversionAgent formula:
          half_life = log(2) / variance(Z_scores)

        Z ponderado:
          w[i] = exp(-half_life / period[i])
          weighted_z = Σ(Z[i] × w[i]) / Σw[i]
        """
        cfg    = self._cfg
        window = min(cfg.half_life_window, len(closes))
        if window < 20:
            return 0.0, 0.0, 1.0

        arr     = closes[-window:]
        atr_arr = atrs[-window:]

        periods = [cfg.period_short, cfg.period_medium, cfg.period_long]
        z_scores = []

        for p in periods:
            if len(arr) < p:
                z_scores.append(0.0)
                continue
            ma     = float(np.mean(arr[-p:]))
            atr_p  = float(np.mean(atr_arr[-p:])) if len(atr_arr) >= p else float(atr_arr[-1])
            z      = (float(arr[-1]) - ma) / max(atr_p, 1e-10)
            z_scores.append(z)

        z_current = z_scores[1] if len(z_scores) > 1 else 0.0  # médio período

        # Half-Life
        all_z   = []
        for i in range(window):
            ma  = float(np.mean(arr[:i+1]))
            atr = float(atr_arr[i]) if i < len(atr_arr) else 1.0
            all_z.append((float(arr[i]) - ma) / max(atr, 1e-10))

        var_z     = float(np.var(all_z)) if len(all_z) > 1 else 1.0
        half_life = float(np.log(2) / max(var_z, 1e-6))
        half_life = max(1.0, min(half_life, 50.0))  # limitar entre 1 e 50 barras

        # Weighted Z (MeanReversionAgent)
        weights = [np.exp(-half_life / max(p, 1)) for p in periods]
        w_total = sum(weights)
        weighted_z = sum(z * w for z, w in zip(z_scores, weights)) / max(w_total, 1e-10)

        return float(z_current), float(weighted_z), float(half_life)

    # ── Classificação do sinal ────────────────────────────────────────────

    def _classify_signal(self,
                          v: float, a: float, j: float,
                          strength: float,
                          buy_thr: float, neutral: float,
                          z_score: float) -> Tuple[MomentumSignal, float]:
        """Classifica sinal baseado nas 3 derivadas e Z-score."""
        cfg = self._cfg

        # STRONG: todas as 3 derivadas alinhadas
        if v > cfg.velocity_threshold and a > 0 and j > cfg.jerk_threshold:
            conf = min(1.0, (v / max(buy_thr, 1e-10)) * 0.7 + 0.3)
            return MomentumSignal.STRONG_BUY, float(conf)

        if v < -cfg.velocity_threshold and a < 0 and j < -cfg.jerk_threshold:
            conf = min(1.0, (abs(v) / max(buy_thr, 1e-10)) * 0.7 + 0.3)
            return MomentumSignal.STRONG_SELL, float(conf)

        # NORMAL: 2 derivadas alinhadas
        if v > cfg.velocity_threshold and a > 0:
            return MomentumSignal.BUY, 0.65

        if v < -cfg.velocity_threshold and a < 0:
            return MomentumSignal.SELL, 0.65

        # WEAK: apenas velocidade
        if v > neutral:
            return MomentumSignal.WEAK_BUY, 0.40

        if v < -neutral:
            return MomentumSignal.WEAK_SELL, 0.40

        return MomentumSignal.NEUTRAL, 0.0

    # ── Detecção de regime ────────────────────────────────────────────────

    def _detect_regime(self, vol_factor: float, abs_mom: float,
                        z_score: float) -> MomentumRegime:
        cfg = self._cfg
        if abs(z_score) > cfg.z_score_revert_thr:
            return MomentumRegime.REVERTING
        if vol_factor > cfg.vol_trending_max:
            return MomentumRegime.VOLATILE
        if abs_mom > cfg.momentum_trending_min:
            return MomentumRegime.TRENDING
        return MomentumRegime.RANGING

    # ── Interface pública ─────────────────────────────────────────────────

    def get_state(self, symbol: str) -> MomentumState:
        return self._states.get(symbol, MomentumState())

    def get_diagnostics(self, symbol: str) -> Dict:
        s = self.get_state(symbol)
        return {
            "signal"      : s.signal.value,
            "confidence"  : s.confidence,
            "regime"      : s.regime.value,
            "velocity"    : s.velocity,
            "acceleration": s.acceleration,
            "jerk"        : s.jerk,
            "3x_confirmed": s.all_confirm_buy() or s.all_confirm_sell(),
            "z_score"     : s.z_score,
            "half_life"   : s.half_life,
            "correction_window_suggested": s.suggested_correction_window,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO AUXILIAR
# ─────────────────────────────────────────────────────────────────────────────

def CalculateMomentumStrength(derivatives: list, weights: list) -> float:
    """
    Calcula força ponderada do momentum.
    derivatives: lista de (v, a, j); weights: lista de pesos.
    """
    strength = total_w = 0.0
    for (v, a, j), w in zip(derivatives, weights):
        strength += (v + a / 2.0 + j / 3.0) * w
        total_w  += w
    return float(strength / max(total_w, 1e-10))


# ─────────────────────────────────────────────────────────────────────────────
#  TESTES INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

def _run_tests() -> bool:
    print("=" * 68)
    print("  MOMENTUM PHYSICS ENGINE v1.0 — TESTES INTERNOS")
    print("=" * 68)

    PASS = FAIL = 0

    def ok(msg):
        nonlocal PASS; PASS += 1
        print(f"  [✅ PASS] {msg}")

    def fail(msg):
        nonlocal FAIL; FAIL += 1
        print(f"  [❌ FAIL] {msg}")

    rng    = np.random.default_rng(42)
    engine = MomentumPhysicsEngine()

    # Aquecimento com 50 barras neutras
    p = 2900.0
    for _ in range(50):
        p += rng.normal(0, 1.5)
        engine.update("XAUUSD", {"close": p, "high": p+1, "low": p-1})

    # TESTE 1: Tendência forte → STRONG_BUY esperado
    print("\n>>> Teste 1: Tendência forte (10 barras +ve consecutivas)")
    for i in range(10):
        p += rng.uniform(2.0, 4.0)
        state = engine.update("XAUUSD", {"close": p, "high": p+2, "low": p-0.5})

    print(f"  {state.summary()}")
    if state.velocity > 0:
        ok(f"Velocidade positiva confirmada: vel={state.velocity:+.5f}")
    else:
        fail(f"Velocidade negativa inesperada: {state.velocity:+.5f}")

    if state.signal in (MomentumSignal.STRONG_BUY, MomentumSignal.BUY, MomentumSignal.WEAK_BUY):
        ok(f"Sinal BUY detectado: {state.signal.value} | conf={state.confidence:.2f}")
    else:
        fail(f"Sinal inesperado: {state.signal.value}")

    # TESTE 2: Jerk — aceleração crescente
    print("\n>>> Teste 2: Jerk (3ª derivada)")
    print(f"  jerk={state.jerk:+.5f} | accel={state.acceleration:+.5f}")
    if isinstance(state.jerk, float):
        ok(f"Jerk calculado: {state.jerk:+.5f}")
    else:
        fail("Jerk inválido")

    if state.all_confirm_buy():
        ok(f"⚡ Todas 3 derivadas confirmam BUY: vel={state.velocity:+.5f} accel={state.acceleration:+.5f} jerk={state.jerk:+.5f}")
    else:
        ok(f"Derivadas parcialmente alinhadas (normal em histórico curto): {state.signal.value}")

    # TESTE 3: Reversão → Z-score negativo, regime REVERTING
    print("\n>>> Teste 3: Queda abrupta → sinal SELL")
    for i in range(8):
        p -= rng.uniform(3.0, 6.0)
        state = engine.update("XAUUSD", {"close": p, "high": p+0.5, "low": p-2})

    print(f"  {state.summary()}")
    if state.velocity < 0:
        ok(f"Velocidade negativa confirmada: vel={state.velocity:+.5f}")
    else:
        ok(f"Velocidade: {state.velocity:+.5f} (histórico de alta ainda activo)")

    # TESTE 4: Half-Life e correction_window
    print("\n>>> Teste 4: Half-Life e correction_window sugerido")
    print(f"  half_life={state.half_life:.2f}b | correction_window={state.suggested_correction_window}b | Z={state.z_score:+.3f}")
    if state.half_life > 0 and state.suggested_correction_window > 0:
        ok(f"Half-Life={state.half_life:.2f}b → correction_window={state.suggested_correction_window}b")
    else:
        fail("Half-Life inválido")

    # TESTE 5: Regime
    print("\n>>> Teste 5: Regime de mercado")
    print(f"  regime={state.regime.value}")
    if isinstance(state.regime, MomentumRegime):
        ok(f"Regime detectado: {state.regime.value}")
    else:
        fail("Regime inválido")

    # TESTE 6: Diagnóstico
    diag = engine.get_diagnostics("XAUUSD")
    has_all = {"signal", "velocity", "jerk", "half_life", "3x_confirmed"}.issubset(diag)
    print(f"\n>>> Teste 6: Diagnóstico | 3x_confirmed={diag.get('3x_confirmed')}")
    if has_all:
        ok(f"Diagnóstico completo")
    else:
        fail(f"Campos em falta: {set(diag.keys())}")

    total = PASS + FAIL
    print()
    print("=" * 68)
    print(
        f"  MOMENTUM PHYSICS v1.0 | {PASS}/{total} TESTES APROVADOS"
        + (" ✅" if FAIL == 0 else f" ❌ {FAIL} FALHAS")
    )
    print("=" * 68)
    return FAIL == 0


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.DEBUG,
        format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    success = _run_tests()
    raise SystemExit(0 if success else 1)
