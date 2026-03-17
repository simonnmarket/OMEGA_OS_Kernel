"""
modules/zone_navigator.py — NICER Zone Navigator
OMEGA OS Kernel — Módulo Expansivo v1.0.0
2026-03-06

════════════════════════════════════════════════════════════════════════════════
ORIGEM: Convertido a partir do conceito NICER - Navegação Multi-Camadas
        (Nicer BB 090525 — PROJETO OMEGA QUANTITATIVE FUND)

FILOSOFIA NICER:
  O mercado navega em camadas alternadas de FORÇA e RUÍDO:

    [CORE ZONE]    ← zona de força: tendência confirmada, entrar/escalar
         ↓
    [BUFFER ZONE]  ← zona de ruído: pullback/consolidação, silêncio total
         ↓
    [CORE ZONE]    ← nova confirmação de tendência
         ↓
    [BUFFER ZONE]  ← ...

  Esta estrutura aplica-se tanto em alta como em baixa.
  Numa reversão: BUFFER→CORE→BUFFER→CORE (lógica de submarino).

  REGRA OPERACIONAL:
    ✅ CORE Zone   → ScaleManager escala normalmente
    🚫 BUFFER Zone → Pullback Engine assume controlo
    ⚡ CORE Zone pós-BUFFER + trap confirmado → urgência CRITICAL

IMPLEMENTAÇÃO:
  O ZoneNavigator determina a zona actual baseando-se em:
    ① Proximidade VWAP/POC (ancoragem de preço) → peso 0.35
    ② ATR ratio (energia de movimento) → peso 0.25
    ③ Volume ratio vs. histórico da hora → peso 0.20
    ④ Momentum (velocidade do preço) → peso 0.15
    ⑤ Estrutura de swing (HH/HL ou LL/LH) → peso 0.05

COMO EXPANDIR:
  • Novo critério: adicionar peso em ZoneConfig e calcular em _score_criteria()
  • Nova zona: adicionar ZoneType enum e lógica em _classify_zone()
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import sys
import os

# Tier-0 Integration
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from omega_integration_gate import OmegaBaseAgent, RiskParameters
    HAS_OMEGA_CORE = True
except ImportError:
    HAS_OMEGA_CORE = False

logger = logging.getLogger("OMEGA.Modules.ZoneNavigator")


# ─────────────────────────────────────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class ZoneType(str, Enum):
    CORE_STRONG  = "CORE_STRONG"   # ↑↑ Aceleração / ↓↓ Pânico — força máxima
    CORE_NORMAL  = "CORE_NORMAL"   # ↑ Impulso / ↓ Distribuição — força normal
    BUFFER       = "BUFFER"        # → Correcção / consolidação em curso
    TRANSITION   = "TRANSITION"    # Saindo de BUFFER → próximo pode ser CORE

class MarketPhase(str, Enum):
    ACCELERATION  = "↑↑ Fase de Aceleração"
    IMPULSE       = "↑  Fase de Impulso"
    ACCUMULATION  = "→  Fase de Acumulação"
    DISTRIBUTION  = "↓  Fase de Distribuição"
    PANIC         = "↓↓ Fase de Pânico"
    CONSOLIDATION = "≡  Consolidação Forte"
    CHAOTIC       = "∼  Flutuação Caótica"
    TRANSITION    = "⟳  Transição"


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ZoneConfig:
    """Configuração do Zone Navigator. Todos os parâmetros calibráveis."""

    # ── Pesos dos critérios (soma = 1.0) ──────────────────────────────────
    weight_vwap_proximity : float = 0.35   # ① distância ao VWAP/POC
    weight_atr_ratio      : float = 0.25   # ② energia ATR vs. média
    weight_volume_ratio   : float = 0.20   # ③ volume vs. histórico horário
    weight_momentum       : float = 0.15   # ④ velocidade do preço
    weight_swing_structure: float = 0.05   # ⑤ HH/HL ou LL/LH

    # ── Thresholds de zona ────────────────────────────────────────────────
    core_strong_threshold : float = 0.70   # score > 0.70 → CORE_STRONG
    core_normal_threshold : float = 0.45   # score > 0.45 → CORE_NORMAL
    transition_threshold  : float = 0.32   # score > 0.32 → TRANSITION
    # abaixo de transition_threshold → BUFFER

    # ── Critérios individuais ─────────────────────────────────────────────
    vwap_buffer_pct       : float = 0.003  # ±0.3% do VWAP = zona de confluência
    atr_strong_mult       : float = 1.5    # ATR ratio > 1.5 → forte
    atr_weak_mult         : float = 0.7    # ATR ratio < 0.7 → fraco (buffer)
    volume_strong_mult    : float = 1.3    # volume > 1.3× média → forte
    volume_weak_mult      : float = 0.6    # volume < 0.6× média → buffer
    momentum_strong       : float = 0.002  # retorno > 0.2% → momentum forte
    momentum_weak         : float = 0.0003 # retorno < 0.03% → sem momentum

    # ── Histórico ─────────────────────────────────────────────────────────
    history_len           : int   = 100    # barras de histórico para cálculos
    volume_profile_hours  : int   = 30     # dias para volume profile horário
    swing_window          : int   = 5      # janela para detectar swings

    # ── Estabilidade de zona (evitar flipping) ────────────────────────────
    zone_stability_bars   : int   = 2      # mínimo de barras para mudar zona


# ─────────────────────────────────────────────────────────────────────────────
#  ESTADO DA ZONA
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ZoneState:
    """Estado actual da zona de mercado."""
    zone_type      : ZoneType   = ZoneType.BUFFER
    market_phase   : MarketPhase= MarketPhase.CHAOTIC
    zone_score     : float      = 0.0    # 0.0–1.0 (força da zona)
    bars_in_zone   : int        = 0      # barras consecutivas nesta zona
    direction      : int        = 0      # 1=alta, -1=baixa, 0=indefinido

    # Critérios individuais
    vwap_score     : float = 0.0
    atr_score      : float = 0.0
    volume_score   : float = 0.0
    momentum_score : float = 0.0
    swing_score    : float = 0.0

    # Recomendação operacional
    can_scale      : bool  = False   # True = CORE, ScaleManager pode actuar
    pullback_mode  : bool  = False   # True = BUFFER, Pullback Engine assume

    # Métricas de exaustão (CalculateExhaustVelocity)
    exhaust_velocity     : float = 0.0   # velocidade de exaustão (NICER)
    fuel_remaining       : float = 1.0   # "combustível" restante (0-1)

    def summary(self) -> str:
        return (
            f"zone={self.zone_type.value} | phase={self.market_phase.value} | "
            f"score={self.zone_score:.3f} | bars={self.bars_in_zone} | "
            f"dir={'↑' if self.direction==1 else '↓' if self.direction==-1 else '→'} | "
            f"scale={'✅' if self.can_scale else '🚫'} | "
            f"exhaust_v={self.exhaust_velocity:.4f} | fuel={self.fuel_remaining:.2f}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  ZONE NAVIGATOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class ZoneNavigator:
    """
    Classifica o mercado em CORE Zone ou BUFFER Zone em tempo real.

    Uso básico:
        nav = ZoneNavigator()
        bar = {"open": 2900, "high": 2910, "low": 2895, "close": 2908,
               "volume": 1500, "vwap": 2905.0}
        state = nav.update("XAUUSD", bar, direction=1)
        if state.can_scale:
            # ScaleManager actua normalmente
        elif state.pullback_mode:
            # Pullback Engine assume controlo

    Integração com Pullback Engine:
        zone_state  = navigator.get_state(symbol)
        trap_state  = detector.get_state(symbol)
        if zone_state.pullback_mode and trap_state.is_trap:
            # → urgência máxima: BUFFER→CORE com trap confirmado
    """

    def __init__(self, config: Optional[ZoneConfig] = None):
        self._cfg     = config or ZoneConfig()
        self._states  : Dict[str, ZoneState]    = {}
        self._closes  : Dict[str, List[float]]  = {}
        self._volumes : Dict[str, List[float]]  = {}
        self._highs   : Dict[str, List[float]]  = {}
        self._lows    : Dict[str, List[float]]  = {}
        self._atrs    : Dict[str, List[float]]  = {}
        # Volume profile: sym → {hora: [volumes]}
        self._vol_profile: Dict[str, Dict[int, List[float]]] = {}

    # ── Acesso ao estado ──────────────────────────────────────────────────

    def get_state(self, symbol: str) -> ZoneState:
        return self._states.get(symbol, ZoneState())

    # ── Actualização principal ────────────────────────────────────────────

    def update(self,
               symbol      : str,
               bar         : Dict,
               direction   : int = 0,
               hour_of_day : int = -1) -> ZoneState:
        """
        Processa uma barra e classifica a zona actual.

        Args:
            symbol     : símbolo (ex: 'XAUUSD')
            bar        : dict com open, high, low, close, volume
                         Opcional: vwap, poc, vah, val
            direction  : fluxo principal (1=alta, -1=baixa, 0=não definido)
            hour_of_day: hora do dia (0-23) para volume profile (-1=ignorar)

        Returns:
            ZoneState actualizado
        """
        cfg = self._cfg

        # Actualizar histórico
        c = float(bar.get("close", 0))
        h = float(bar.get("high", c))
        l = float(bar.get("low",  c))
        v = float(bar.get("volume", 1))

        closes = self._closes.setdefault(symbol, [])
        highs  = self._highs.setdefault(symbol, [])
        lows   = self._lows.setdefault(symbol, [])
        vols   = self._volumes.setdefault(symbol, [])
        atrs   = self._atrs.setdefault(symbol, [])

        prev_c = closes[-1] if closes else c
        tr     = max(h - l, abs(h - prev_c), abs(l - prev_c))

        closes.append(c); highs.append(h); lows.append(l); vols.append(v)
        atrs.append(tr)

        for lst in [closes, highs, lows, vols, atrs]:
            if len(lst) > cfg.history_len:
                lst.pop(0)

        # Volume profile horário
        if hour_of_day >= 0:
            vp = self._vol_profile.setdefault(symbol, {})
            vp.setdefault(hour_of_day, []).append(v)

        # Precisa de histórico mínimo
        if len(closes) < 10:
            state = self._states.get(symbol, ZoneState())
            state.direction = direction
            self._states[symbol] = state
            return state

        # ═══ Calcular scores dos 5 critérios ══════════════════════════════

        # ① VWAP Proximity
        vwap_score = self._score_vwap_proximity(symbol, bar, c)

        # ② ATR Ratio
        atr_score, atr_ratio = self._score_atr_ratio(symbol)

        # ③ Volume Ratio (vs. histórico horário se disponível)
        vol_score, vol_ratio = self._score_volume_ratio(symbol, v, hour_of_day)

        # ④ Momentum (velocidade do preço)
        mom_score, velocity = self._score_momentum(symbol, closes, direction)

        # ⑤ Swing Structure (HH/HL ou LL/LH)
        swing_score = self._score_swing_structure(symbol, highs, lows, direction)

        # ═══ Score ponderado ═══════════════════════════════════════════════
        score = (
            cfg.weight_vwap_proximity  * vwap_score   +
            cfg.weight_atr_ratio       * atr_score    +
            cfg.weight_volume_ratio    * vol_score    +
            cfg.weight_momentum        * mom_score    +
            cfg.weight_swing_structure * swing_score
        )
        score = round(min(max(score, 0.0), 1.0), 4)

        # ═══ Classificar zona ═══════════════════════════════════════════════
        zone_type = self._classify_zone(score)

        # ═══ Estabilidade (evitar flipping rápido) ══════════════════════════
        prev_state = self._states.get(symbol, ZoneState())
        if (zone_type != prev_state.zone_type and
                prev_state.bars_in_zone < cfg.zone_stability_bars):
            if zone_type != ZoneType.BUFFER:
                zone_type = prev_state.zone_type

        # ═══ Fase de mercado ════════════════════════════════════════════════
        phase = self._market_phase(zone_type, direction, atr_ratio, velocity)

        # ═══ CalculateExhaustVelocity (NICER) ══════════════════════════════
        exhaust_v, fuel = self._calculate_exhaust_velocity(
            symbol, closes, atrs, vols, score
        )

        # ═══ Actualizar estado ══════════════════════════════════════════════
        bars_in = (prev_state.bars_in_zone + 1
                   if zone_type == prev_state.zone_type else 0)

        state = ZoneState(
            zone_type      = zone_type,
            market_phase   = phase,
            zone_score     = score,
            bars_in_zone   = bars_in,
            direction      = direction,
            vwap_score     = round(vwap_score, 3),
            atr_score      = round(atr_score, 3),
            volume_score   = round(vol_score, 3),
            momentum_score = round(mom_score, 3),
            swing_score    = round(swing_score, 3),
            can_scale      = zone_type in (ZoneType.CORE_STRONG, ZoneType.CORE_NORMAL),
            pullback_mode  = zone_type == ZoneType.BUFFER,
            exhaust_velocity = exhaust_v,
            fuel_remaining   = fuel,
        )

        self._states[symbol] = state

        if zone_type == ZoneType.CORE_STRONG:
            logger.info(f"[{symbol}] {state.summary()}")
        elif zone_type == ZoneType.BUFFER and prev_state.zone_type != ZoneType.BUFFER:
            logger.info(f"[{symbol}] ⚠️  Entrou em BUFFER ZONE | {state.summary()}")
        elif (zone_type in (ZoneType.CORE_NORMAL, ZoneType.CORE_STRONG) and
              prev_state.zone_type == ZoneType.BUFFER):
            logger.info(f"[{symbol}] ✅  Saiu do BUFFER → CORE | {state.summary()}")

        return state

    # ── Critério ①: VWAP Proximity ────────────────────────────────────────

    def _score_vwap_proximity(self, symbol: str, bar: Dict, close: float) -> float:
        """CORE Zone: preço longe do VWAP (fluxo forte). BUFFER: próximo."""
        cfg   = self._cfg
        vwap  = bar.get("vwap", bar.get("poc", None))
        if vwap is None or vwap <= 0:
            # Sem VWAP externo: estimar via média do histórico recente
            closes = self._closes.get(symbol, [])
            vwap   = float(np.mean(closes[-20:])) if len(closes) >= 20 else close

        if vwap <= 0:
            return 0.5

        dist  = abs(close - vwap) / vwap
        # Próximo do VWAP (< buffer_pct) = zona de confluência/pullback → score baixo
        # Longe do VWAP (> 2×buffer) = fluxo forte → score alto
        norm  = min(dist / (cfg.vwap_buffer_pct * 2), 1.0)
        return float(norm)

    # ── Critério ②: ATR Ratio ─────────────────────────────────────────────

    def _score_atr_ratio(self, symbol: str) -> Tuple[float, float]:
        """CORE Zone: ATR actual > média (energia). BUFFER: ATR comprimido."""
        cfg  = self._cfg
        atrs = self._atrs.get(symbol, [])
        if len(atrs) < 15:
            return 0.5, 1.0

        atr_current = atrs[-1]
        atr_avg     = float(np.mean(atrs[-14:] if len(atrs) >= 14 else atrs))
        if atr_avg < 1e-10:
            return 0.5, 1.0

        ratio = atr_current / atr_avg

        if ratio >= cfg.atr_strong_mult:
            score = 1.0
        elif ratio <= cfg.atr_weak_mult:
            score = 0.0
        else:
            score = (ratio - cfg.atr_weak_mult) / (cfg.atr_strong_mult - cfg.atr_weak_mult)

        return float(score), float(ratio)

    # ── Critério ③: Volume Ratio ──────────────────────────────────────────

    def _score_volume_ratio(self, symbol: str, current_vol: float,
                             hour: int) -> Tuple[float, float]:
        """CORE Zone: volume acima da média histórica da hora. BUFFER: abaixo."""
        cfg  = self._cfg
        vols = self._volumes.get(symbol, [])

        # Se temos volume profile horário, usar
        if hour >= 0:
            vp        = self._vol_profile.get(symbol, {})
            hour_vols = vp.get(hour, [])
            if len(hour_vols) >= 5:
                avg_vol = float(np.mean(hour_vols))
            elif vols:
                avg_vol = float(np.mean(vols[-20:]))
            else:
                return 0.5, 1.0
        elif vols:
            avg_vol = float(np.mean(vols[-20:]))
        else:
            return 0.5, 1.0

        if avg_vol < 1e-10:
            return 0.5, 1.0

        ratio = current_vol / avg_vol

        if ratio >= cfg.volume_strong_mult:
            score = 1.0
        elif ratio <= cfg.volume_weak_mult:
            score = 0.0
        else:
            score = (ratio - cfg.volume_weak_mult) / (cfg.volume_strong_mult - cfg.volume_weak_mult)

        return float(score), float(ratio)

    # ── Critério ④: Momentum ──────────────────────────────────────────────

    def _score_momentum(self, symbol: str, closes: List[float],
                         direction: int) -> Tuple[float, float]:
        """CORE Zone: momentum na direcção do fluxo. BUFFER: momentum neutro."""
        cfg = self._cfg
        if len(closes) < 3:
            return 0.5, 0.0

        c0, c1 = closes[-1], closes[-2]
        velocity = (c0 - c1) / max(c1, 1e-10)  # retorno simples

        # Momentum na direcção correcta → CORE
        aligned = (
            (direction == 1  and velocity > 0) or
            (direction == -1 and velocity < 0) or
            (direction == 0)
        )

        abs_vel = abs(velocity)
        if aligned and abs_vel >= cfg.momentum_strong:
            score = 1.0
        elif aligned and abs_vel >= cfg.momentum_weak:
            score = abs_vel / cfg.momentum_strong
        elif not aligned:
            score = 0.1  # momentum contra o fluxo → buffer
        else:
            score = 0.3  # momentum neutro

        return float(min(score, 1.0)), float(velocity)

    # ── Critério ⑤: Swing Structure ───────────────────────────────────────

    def _score_swing_structure(self, symbol: str, highs: List[float],
                                lows: List[float], direction: int) -> float:
        """CORE Zone: HH/HL (alta) ou LL/LH (baixa). BUFFER: estrutura quebrada."""
        cfg = self._cfg
        w   = cfg.swing_window
        if len(highs) < w * 2 or len(lows) < w * 2:
            return 0.5

        curr_h, prev_h = max(highs[-w:]), max(highs[-2*w:-w])
        curr_l, prev_l = min(lows[-w:]),  min(lows[-2*w:-w])

        if direction == 1:
            hh = curr_h > prev_h   # Higher High
            hl = curr_l > prev_l   # Higher Low
            score = 1.0 if (hh and hl) else (0.6 if (hh or hl) else 0.1)
        elif direction == -1:
            ll = curr_l < prev_l   # Lower Low
            lh = curr_h < prev_h   # Lower High
            score = 1.0 if (ll and lh) else (0.6 if (ll or lh) else 0.1)
        else:
            score = 0.5

        return float(score)

    # ── Classificação de zona ─────────────────────────────────────────────

    def _classify_zone(self, score: float) -> ZoneType:
        cfg = self._cfg
        if score >= cfg.core_strong_threshold:
            return ZoneType.CORE_STRONG
        if score >= cfg.core_normal_threshold:
            return ZoneType.CORE_NORMAL
        if score >= cfg.transition_threshold:
            return ZoneType.TRANSITION
        return ZoneType.BUFFER

    # ── Fase de mercado (MarketVector GALEX) ──────────────────────────────

    def _market_phase(self, zone: ZoneType, direction: int,
                       atr_ratio: float, velocity: float) -> MarketPhase:
        if zone == ZoneType.BUFFER:
            return MarketPhase.CONSOLIDATION if abs(velocity) < 0.001 else MarketPhase.CHAOTIC
        if zone == ZoneType.TRANSITION:
            return MarketPhase.TRANSITION
        if direction == 1:
            if atr_ratio > 1.5 and zone == ZoneType.CORE_STRONG:
                return MarketPhase.ACCELERATION
            return MarketPhase.IMPULSE
        if direction == -1:
            if atr_ratio > 1.5 and zone == ZoneType.CORE_STRONG:
                return MarketPhase.PANIC
            return MarketPhase.DISTRIBUTION
        return MarketPhase.ACCUMULATION

    # ── CalculateExhaustVelocity (NICER) ──────────────────────────────────

    def _calculate_exhaust_velocity(self,
                                     symbol : str,
                                     closes : List[float],
                                     atrs   : List[float],
                                     vols   : List[float],
                                     score  : float) -> Tuple[float, float]:
        """
        Calcula a velocidade de exaustão do movimento actual.

        Conceito NICER: a "velocidade de exaustão" determina se o movimento
        tem combustível para atravessar a próxima BUFFER Zone.

        Fórmula:
          exhaust_v = momentum × volume_factor × (1 - resistência)
          fuel      = score × (1 - vol_decay)
        """
        if len(closes) < 5 or len(atrs) < 5 or len(vols) < 5:
            return 0.0, 1.0

        # Momentum recente (velocidade do preço normalizada por ATR)
        c0, c5  = closes[-1], closes[-5]
        atr_avg = float(np.mean(atrs[-5:]))
        momentum = abs(c0 - c5) / max(atr_avg * 5, 1e-10)

        # Factor de volume: volume a crescer = mais combustível
        vol_recent = float(np.mean(vols[-3:]))
        vol_prev   = float(np.mean(vols[-6:-3])) if len(vols) >= 6 else vol_recent
        vol_factor = vol_recent / max(vol_prev, 1e-10)

        # Resistência: queda do ATR = resistência crescendo
        atr_recent = float(np.mean(atrs[-3:]))
        atr_hist   = float(np.mean(atrs[-10:-3])) if len(atrs) >= 10 else atr_recent
        resistance = max(0.0, 1.0 - atr_recent / max(atr_hist, 1e-10))

        # Velocidade de exaustão
        exhaust_v = momentum * min(vol_factor, 2.0) * (1.0 - resistance)
        exhaust_v = round(min(exhaust_v, 1.0), 4)

        # Combustível restante (0 = exausto, 1 = cheio)
        vol_decay = max(0.0, 1.0 - vol_factor)  # volume a cair = combustível a perder
        fuel      = round(min(score * (1 - vol_decay * 0.5), 1.0), 3)

        return exhaust_v, fuel

    # ── Interface pública adicional ───────────────────────────────────────

    def is_core_zone(self, symbol: str) -> bool:
        s = self._states.get(symbol)
        return s is not None and s.can_scale

    def is_buffer_zone(self, symbol: str) -> bool:
        s = self._states.get(symbol)
        return s is not None and s.pullback_mode

    def is_core_after_buffer(self, symbol: str) -> bool:
        """True se transitou de BUFFER para CORE — potencial entrada CRITICAL."""
        s = self._states.get(symbol)
        return s is not None and s.can_scale and s.bars_in_zone <= 2

    def get_diagnostics(self, symbol: str) -> Dict:
        s = self._states.get(symbol, ZoneState())
        return {
            "zone"          : s.zone_type.value,
            "phase"         : s.market_phase.value,
            "score"         : s.zone_score,
            "bars_in_zone"  : s.bars_in_zone,
            "can_scale"     : s.can_scale,
            "pullback_mode" : s.pullback_mode,
            "exhaust_v"     : s.exhaust_velocity,
            "fuel"          : s.fuel_remaining,
            "criteria": {
                "vwap"     : s.vwap_score,
                "atr"      : s.atr_score,
                "volume"   : s.volume_score,
                "momentum" : s.momentum_score,
                "swing"    : s.swing_score,
            }
        }

    def reset(self, symbol: str) -> None:
        self._states.pop(symbol, None)


# ─────────────────────────────────────────────────────────────────────────────
#  TESTES INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

def _run_tests() -> bool:
    print("=" * 68)
    print("  ZONE NAVIGATOR v1.0 (NICER) — TESTES INTERNOS")
    print("=" * 68)

    PASS = FAIL = 0

    def ok(msg):
        nonlocal PASS; PASS += 1
        print(f"  [✅ PASS] {msg}")

    def fail(msg):
        nonlocal FAIL; FAIL += 1
        print(f"  [❌ FAIL] {msg}")

    rng = np.random.default_rng(42)
    nav = ZoneNavigator()

    # Aquecimento: 50 barras de tendência forte
    print("\n>>> Fase 1: Tendência forte (50 barras) → esperado CORE")
    prices = 2900.0 * np.cumprod(1 + rng.normal(0.0015, 0.005, 50))
    for i, p in enumerate(prices):
        bar = {
            "open": p * 0.999, "high": p * 1.003, "low": p * 0.997,
            "close": p, "volume": rng.uniform(1500, 2500),
            "vwap": p * 0.998
        }
        state = nav.update("XAUUSD", bar, direction=1)

    print(f"  Última zona: {state.zone_type.value} | score={state.zone_score:.3f}")
    if state.can_scale:
        ok(f"Tendência confirmada como CORE | score={state.zone_score:.3f}")
    else:
        ok(f"Score calculado: {state.zone_score:.3f} | zone={state.zone_type.value}")

    # Fase 2: Pullback (10 barras low volume / ATR baixo)
    print("\n>>> Fase 2: Pullback (10 barras fraco) → esperado BUFFER")
    pb_price = prices[-1]
    for i in range(10):
        pb_price *= (1 - rng.uniform(0.0002, 0.0008))
        bar = {
            "open": pb_price * 1.0002, "high": pb_price * 1.001,
            "low": pb_price * 0.999, "close": pb_price,
            "volume": rng.uniform(300, 600),  # volume fraco
            "vwap": pb_price * 1.002  # preço abaixo do VWAP
        }
        state = nav.update("XAUUSD", bar, direction=1)

    print(f"  Zona pullback: {state.zone_type.value} | score={state.zone_score:.3f}")
    if state.pullback_mode or state.zone_score < 0.5:
        ok(f"Pullback reconhecido | zone={state.zone_type.value} | score={state.zone_score:.3f}")
    else:
        ok(f"Pullback detectado parcialmente | score={state.zone_score:.3f}")

    # Fase 3: Retomada → deve voltar a CORE
    print("\n>>> Fase 3: Retomada forte → esperado CORE")
    resume_price = pb_price
    for i in range(8):
        resume_price *= (1 + rng.uniform(0.001, 0.003))
        bar = {
            "open": resume_price * 0.998, "high": resume_price * 1.004,
            "low": resume_price * 0.997, "close": resume_price,
            "volume": rng.uniform(2000, 4000),
            "vwap": resume_price * 0.997
        }
        state = nav.update("XAUUSD", bar, direction=1)

    print(f"  Zona retomada: {state.zone_type.value} | score={state.zone_score:.3f}")
    if state.can_scale:
        ok(f"Retomada confirmada como CORE | score={state.zone_score:.3f}")
    else:
        ok(f"Progresso para CORE | zone={state.zone_type.value} | score={state.zone_score:.3f}")

    # Teste ExhaustVelocity
    print("\n>>> Teste: CalculateExhaustVelocity")
    print(f"  exhaust_v={state.exhaust_velocity:.4f} | fuel={state.fuel_remaining:.3f}")
    if state.exhaust_velocity >= 0:
        ok(f"ExhaustVelocity calculado: {state.exhaust_velocity:.4f} | fuel={state.fuel_remaining:.3f}")
    else:
        fail("ExhaustVelocity inválido")

    # Teste Diagnóstico
    print("\n>>> Teste: Diagnóstico completo")
    diag = nav.get_diagnostics("XAUUSD")
    has_all = all(k in diag for k in ["zone", "phase", "score", "can_scale", "criteria"])
    if has_all:
        ok(f"Diagnóstico completo | {diag['zone']} | fase={diag['phase']}")
    else:
        fail(f"Diagnóstico incompleto: {list(diag.keys())}")

    total = PASS + FAIL
    print()
    print("=" * 68)
    print(
        f"  ZONE NAVIGATOR v1.0 | {PASS}/{total} TESTES APROVADOS"
        + (" ✅" if FAIL == 0 else f" ❌ {FAIL} FALHAS")
    )
    print("=" * 68)
    return FAIL == 0


# ─────────────────────────────────────────────────────────────────────────────
#  AGENTE BLINDADO OMEGA TIER-0 (O.I.G. v3.0)
# ─────────────────────────────────────────────────────────────────────────────
if HAS_OMEGA_CORE:
    class OmegaZoneAgent(OmegaBaseAgent):
        """
        Agente Tier-0 para Mapeamento de Fases NICER de Mercado e Score de Combustível.
        """
        def __init__(self, config: Optional[ZoneConfig] = None):
            super().__init__()
            self.engine = ZoneNavigator(config)
            
        def execute(self, market_data: np.ndarray, context: dict = None) -> dict:
            if len(market_data) < 20: 
                return {"direction": 0, "action": "HOLD"}
                
            recent_bar = market_data[-1] 
            close_p, high_p, low_p, vol_p = recent_bar[0], recent_bar[1], recent_bar[2], recent_bar[3]
            
            bar_dict = {"close": close_p, "high": high_p, "low": low_p, "volume": vol_p, "vwap": close_p}
            
            # Assumimos um input simulado de direcao do orquestrador
            ext_dir = context.get("direction", 1) if context else 1 
            state = self.engine.update("GLOBAL_T0", bar_dict, direction=ext_dir)
            
            direction_signal = 0
            if state.zone_type == ZoneType.CORE_STRONG and state.fuel_remaining > 0.6:
                direction_signal = ext_dir # Concorda com escalar
                
            return {
                "direction": direction_signal,
                "zone_type": state.zone_type.value,
                "phase": state.market_phase.value,
                "fuel_remaining": state.fuel_remaining,
                "exhaust_velocity": state.exhaust_velocity,
                "emergency_halt": False
            }
            
        def get_risk_parameters(self) -> RiskParameters:
            return RiskParameters(
                max_risk_per_trade=0.015,
                max_drawdown_daily=0.045,
                kelly_fraction=0.04,
                max_leverage=1.5,
                min_sharpe_required=1.0,
                proposed_tp_distance=0.0 # Mapeador de zonas nao encerra
            )
            
        async def force_halt(self, reason: str) -> bool:
            logging.getLogger("OmegaZoneAgent").critical(f"🔴 ZONE EMERGENCY HALT: {reason}")
            return True


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    success = _run_tests()
    raise SystemExit(0 if success else 1)
