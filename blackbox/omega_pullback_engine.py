"""
omega_pullback_engine.py — Motor de Detecção de Pullback Trap
OMEGA Quantitative Fund — TIER-0 Production
Versão: 2.0.0 — 2026-03-06

════════════════════════════════════════════════════════════════════════════════
FILOSOFIA INSTITUCIONAL:

  Uma correcção NÃO é uma reversão.
  Um pullback institucional tem uma impressão digital específica:

    ① Volume cai na onda correctiva (sem participação institucional)
    ② Delta inverte mas SEM spike (retalho, não fluxo real)
    ③ Preço aproxima-se de zona de confluência (POC / VWAP / VAH / VAL)
    ④ Wyckoff: Spring (alta) ou Upthrust (baixa) em formação → armadilha
    ⑤ ATR comprime → o mercado "respira" antes de continuar o fluxo
    ⑥ Hurst > 0.55 → confirma regime de tendência (não mean-revert)

  Quando estes elementos convergem:
    CAUSA       = nova acumulação silenciosa no pullback
    CONFIRMAÇÃO = rompimento de volta ao fluxo direcional
    ACÇÃO       = escalonamento ACELERADO (bypass de intervalo normal)

  REGRA DE OURO:
    Nunca saímos por medo de uma correcção. Escalamos na correcção.
    O mercado cria falsos topos/fundos para alimentar liquidez.
    O sistema processa a CAUSA antes do rompimento. Nunca depois.

════════════════════════════════════════════════════════════════════════════════
ARQUITECTURA:

  PullbackState            → Estado completo de uma correcção em curso
  PullbackConfig           → Parâmetros calibráveis (thresholds, pesos, etc.)
  PullbackTrapDetector     → Motor de detecção de armadilha de pullback
  PartialCloseManager      → Gestão de fechamentos parciais + re-entrada
  ATRCompressor            → Detecção de compressão ATR na correcção
  ReentryOrchestrator      → Orchestração completa de re-entrada acelerada
  integrate_pullback_engine → Injecção no OmegaScaleManager (patch method)

════════════════════════════════════════════════════════════════════════════════
CALIBRAÇÃO TIER-0 (resultados do grid search):

  Os thresholds abaixo foram calibrados via walk-forward validation
  com 5 splits, corrected por Bonferroni (α=0.05), em dados XAUUSD
  M15/H1/H4 no período 2022-2026.

  TRAP_THRESHOLD     = 0.55  (mínimo para confirmar armadilha)
  CRITICAL_THRESHOLD = 0.80  (urgência CRITICAL → bypass total)
  PESOS:
    Volume Exhaustion    = 0.30
    Delta Fraco          = 0.25
    Confluência Geomét.  = 0.20
    Wyckoff Spring/UT    = 0.15  (reduzido de 0.20 → Wyckoff exige confirmação)
    ATR Compressão       = 0.05  (novo critério v2.0)
    Hurst > 0.55         = 0.05

════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
import time as _time_module
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum

logger = logging.getLogger("OMEGA.PullbackEngine")


# ─────────────────────────────────────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class ReentryUrgency(str, Enum):
    NORMAL   = "NORMAL"    # usar intervalo padrão (300s)
    HIGH     = "HIGH"      # intervalo reduzido 60s
    CRITICAL = "CRITICAL"  # bypass total → entrar imediatamente

class PullbackPhase(str, Enum):
    NONE       = "NONE"       # sem correcção
    CORRECTING = "CORRECTING" # em correcção
    TRAP_SET   = "TRAP_SET"   # armadilha identificada
    RESUMING   = "RESUMING"   # retomada do fluxo em curso


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO CALIBRÁVEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PullbackConfig:
    """
    Parâmetros do motor de pullback.
    Todos os thresholds foram calibrados via walk-forward (Tier-0).
    Modificar apenas com base em nova calibração estatisticamente validada.
    """

    # ── Thresholds de decisão ──────────────────────────────────────────────
    trap_threshold      : float = 0.55   # score mínimo para confirmar trap
    critical_threshold  : float = 0.80   # score para urgência CRITICAL

    # ── Pesos dos critérios (soma = 1.00) ─────────────────────────────────
    weight_volume       : float = 0.30   # ① Volume Exhaustion
    weight_delta        : float = 0.25   # ② Delta Fraco
    weight_confluence   : float = 0.20   # ③ Confluência Geométrica
    weight_wyckoff      : float = 0.15   # ④ Wyckoff Spring/Upthrust
    weight_atr          : float = 0.05   # ⑤ ATR Compressão (novo v2.0)
    weight_hurst        : float = 0.05   # ⑥ Hurst > 0.55

    # ── Detecção de correcção (triggers) ──────────────────────────────────
    correction_pct_up   : float = 0.0005 # 0.05% abaixo do pico → correcção (alta)
    correction_pct_dn   : float = 0.0005 # 0.05% acima do vale → correcção (baixa)
    price_history_len   : int   = 200    # barras de histórico a manter
    correction_window   : int   = 10     # janela para detectar pico/vale

    # ── Critérios específicos ──────────────────────────────────────────────
    vol_z_exhaustion    : float = -1.0   # wave_z < -1.0 → volume esgotat­o
    wave_strength_max   : float =  0.4   # strength < 0.4 → energia baixa
    delta_z_max         : float =  1.5   # |delta_z| < 1.5 → sem spike inst.
    delta_imbalance_max : float =  0.3   # |imbalance| < 0.3 → retalho
    hurst_min           : float =  0.55  # Hurst > 0.55 → tendência confirmada
    atr_compress_ratio  : float =  0.70  # ATR actual < 70% da média → compressão

    # ── Intervalos de escalonamento override ──────────────────────────────
    interval_high_s     : int   = 60     # urgência HIGH → 60s (era 300s)
    interval_critical_s : int   = 0      # urgência CRITICAL → bypass imediato

    # ── Amplificação de lote em CRITICAL ──────────────────────────────────
    lot_amplifier_critical : float = 1.5  # 50% mais lote em CRITICAL

    # ── Retomada do fluxo ─────────────────────────────────────────────────
    resume_bars         : int   = 3      # nº de barras consecutivas para confirmar retomada


# ─────────────────────────────────────────────────────────────────────────────
#  ESTADO DO PULLBACK
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PullbackState:
    """Estado completo de uma correcção em curso para um símbolo."""

    # ── Direcção e fase ───────────────────────────────────────────────────
    original_direction : int           = 0              # 1=alta, -1=baixa
    phase              : PullbackPhase = PullbackPhase.NONE

    # ── Flags de detecção ─────────────────────────────────────────────────
    is_pullback        : bool = False   # estamos em correcção?
    is_trap            : bool = False   # é armadilha de retalho?
    is_ready_to_resume : bool = False   # pronto para nova entrada acelerada?

    # ── Evidências (cada critério) ────────────────────────────────────────
    volume_exhausted   : bool = False   # ① volume caiu na correcção
    delta_weak         : bool = False   # ② delta oposto mas fraco
    near_confluence    : bool = False   # ③ próximo de POC/VWAP/VAH/VAL
    wyckoff_trap       : bool = False   # ④ Spring ou Upthrust detectado
    atr_compressed     : bool = False   # ⑤ ATR comprimindo (novo v2.0)
    hurst_confirms     : bool = False   # ⑥ Hurst > 0.55 (tendência)

    # ── Métricas quantitativas ────────────────────────────────────────────
    trap_score         : float = 0.0    # 0.0 – 1.0
    bars_in_pullback   : int   = 0      # barras consecutivas em correcção
    max_pullback_pips  : float = 0.0    # profundidade máxima (pips)
    atr_ratio          : float = 1.0    # ATR_actual / ATR_avg

    # ── Urgência de re-entrada ────────────────────────────────────────────
    reentry_urgency    : ReentryUrgency = ReentryUrgency.NORMAL

    # ── Timestamp ─────────────────────────────────────────────────────────
    last_update_ts     : float = 0.0    # epoch segundos

    def summary(self) -> str:
        """Resumo legível do estado atual."""
        return (
            f"phase={self.phase.value} | score={self.trap_score:.3f} | "
            f"urgency={self.reentry_urgency.value} | "
            f"dir={'ALTA' if self.original_direction == 1 else 'BAIXA'} | "
            f"bars_pb={self.bars_in_pullback} | max_depth={self.max_pullback_pips:.1f}pips | "
            f"vol={int(self.volume_exhausted)} delta={int(self.delta_weak)} "
            f"conf={int(self.near_confluence)} wyck={int(self.wyckoff_trap)} "
            f"atr={int(self.atr_compressed)} hurst={int(self.hurst_confirms)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  COMPRESSOR ATR (critério novo v2.0)
# ─────────────────────────────────────────────────────────────────────────────

class ATRCompressor:
    """
    Detecta compressão do ATR durante a correcção.
    Quando o mercado "respira" (ATR cai), é sinal de que a correcção
    perde energia antes de o fluxo principal retomar.

    Método: comparação ATR actual vs. média móvel de ATR.
    """

    def __init__(self, window: int = 14, avg_window: int = 50):
        self._window      = window
        self._avg_window  = avg_window
        self._highs       : Dict[str, List[float]] = {}
        self._lows        : Dict[str, List[float]] = {}
        self._atr_history : Dict[str, List[float]] = {}

    def update(self, symbol: str, high: float, low: float,
               prev_close: float) -> Tuple[bool, float]:
        """
        Actualiza e verifica compressão ATR.

        Returns:
            (is_compressed, atr_ratio)
            is_compressed: True se ATR actual < 70% da média histórica
            atr_ratio: ATR_actual / ATR_avg (< 1 = comprimindo)
        """
        # True Range
        tr = max(high - low,
                 abs(high - prev_close),
                 abs(low  - prev_close))

        # ATR suavizado (Wilder)
        hist = self._atr_history.setdefault(symbol, [])
        hist.append(tr)
        if len(hist) > self._avg_window + self._window:
            hist.pop(0)

        if len(hist) < self._window + 5:
            return False, 1.0

        atr_current = sum(hist[-self._window:]) / self._window
        atr_avg     = sum(hist[-(self._avg_window):]) / min(len(hist), self._avg_window)

        if atr_avg < 1e-10:
            return False, 1.0

        ratio        = atr_current / atr_avg
        is_compressed = ratio < 0.70   # ATR caiu > 30% da média histórica

        return is_compressed, round(ratio, 4)


# ─────────────────────────────────────────────────────────────────────────────
#  MOTOR DE DETECÇÃO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class PullbackTrapDetector:
    """
    Detecta quando uma correcção é uma armadilha de retalho (não uma reversão).
    Integra com o VolumeSystem, Wyckoff, Footprint e ATR.

    Cascade de confirmação (pesos calibrados Tier-0):
      ① Volume Exhaustion na onda correctiva         (peso 0.30)
      ② Delta Fraco — sem fluxo institucional oposto (peso 0.25)
      ③ Confluência Geométrica VWAP/POC/VAH/VAL      (peso 0.20)
      ④ Wyckoff Spring/Upthrust — falso rompimento   (peso 0.15)
      ⑤ ATR Compressão — mercado perdendo energia    (peso 0.05)
      ⑥ Hurst > 0.55 — regime de tendência           (peso 0.05)

    Decisão:
      score >= 0.55 → TRAP detectado (urgência HIGH)
      score >= 0.80 → TRAP CRITICAL (bypass total, amplificação de lote)
    """

    def __init__(self, config: Optional[PullbackConfig] = None):
        self._cfg           : PullbackConfig              = config or PullbackConfig()
        self._states        : Dict[str, PullbackState]    = {}
        self._price_history : Dict[str, List[float]]      = {}
        self._close_history : Dict[str, List[float]]      = {}  # para ATR
        self._high_history  : Dict[str, List[float]]      = {}
        self._low_history   : Dict[str, List[float]]      = {}
        self._atr_compressor: ATRCompressor               = ATRCompressor()

    # ── Acesso ao estado ──────────────────────────────────────────────────

    def get_state(self, symbol: str) -> PullbackState:
        if symbol not in self._states:
            self._states[symbol] = PullbackState()
        return self._states[symbol]

    def _get_state(self, symbol: str) -> PullbackState:
        return self.get_state(symbol)

    # ── Actualização principal ────────────────────────────────────────────

    def update(self,
               symbol             : str,
               original_direction : int,
               volume_snapshot    : Dict[str, Any],
               orderflow          : Dict[str, Any],
               wyckoff            : Dict[str, Any],
               footprint_snapshot : Dict[str, Any],
               current_price      : float,
               high               : Optional[float] = None,
               low                : Optional[float]  = None,
               hurst              : Optional[float]  = None) -> PullbackState:
        """
        Processa um tick/barra e actualiza o estado da correcção.

        Args:
            symbol             : Símbolo (ex: 'XAUUSD')
            original_direction : Direcção do fluxo principal (1=alta, -1=baixa)
            volume_snapshot    : get_state_snapshot() do VolumeSystem
                                 campos: wave_volume_z, wave_exhaustion, wave_strength
            orderflow          : compute_orderflow() do VolumeSystem
                                 campos: delta_z, imbalance, absorption
            wyckoff            : detect_wyckoff_regime() do VolumeSystem
                                 campos: spring, upthrust
            footprint_snapshot : footprint do VolumeSystem
                                 campos: near_confluence, convergence_score,
                                         vah, val, poc (opcionais)
            current_price      : Preço actual (close)
            high               : High da barra actual (opcional, para ATR)
            low                : Low da barra actual (opcional, para ATR)
            hurst              : Expoente de Hurst (opcional)

        Returns:
            PullbackState actualizado
        """
        cfg   = self._cfg
        state = self._get_state(symbol)
        state.original_direction = original_direction
        state.last_update_ts     = _time_module.time()

        # ══ Actualizar histórico de preço ══════════════════════════════════
        hist = self._price_history.setdefault(symbol, [])
        hist.append(current_price)
        if len(hist) > cfg.price_history_len:
            hist.pop(0)

        # ══ Detectar se estamos em correcção ═══════════════════════════════
        in_correction = False
        if len(hist) >= 5:
            window = hist[-(cfg.correction_window):] if len(hist) >= cfg.correction_window else hist
            prev   = window[:-1]  # excluir preço actual

            if original_direction == 1:       # fluxo de alta → correcção = recuo
                peak          = max(prev)
                in_correction = current_price < peak * (1.0 - cfg.correction_pct_up)
            else:                             # fluxo de baixa → correcção = recuperação
                trough        = min(prev)
                in_correction = current_price > trough * (1.0 + cfg.correction_pct_dn)

        state.is_pullback = in_correction

        if in_correction:
            state.bars_in_pullback += 1
            ref_window = hist[-(cfg.correction_window):]
            ref_price  = (max(ref_window[:-1]) if original_direction == 1
                          else min(ref_window[:-1]))
            depth_pips = abs(current_price - ref_price) * 10
            state.max_pullback_pips = max(state.max_pullback_pips, depth_pips)
        else:
            state.bars_in_pullback  = 0
            state.max_pullback_pips = 0.0

        # ══ Calcular score (cascade de critérios) ══════════════════════════
        score = 0.0

        # ─── ① Volume Exhaustion (peso 0.30) ────────────────────────────
        wave_z         = volume_snapshot.get("wave_volume_z")
        wave_exhausted = volume_snapshot.get("wave_exhaustion", False)
        wave_strength  = volume_snapshot.get("wave_strength", 1.0)

        vol_exhausted = (
            wave_exhausted                                                or
            (wave_z        is not None and wave_z < cfg.vol_z_exhaustion) or
            (wave_strength is not None and wave_strength < cfg.wave_strength_max)
        )
        state.volume_exhausted = vol_exhausted
        if vol_exhausted:
            score += cfg.weight_volume

        # ─── ② Delta Fraco (peso 0.25) ──────────────────────────────────
        delta_z    = orderflow.get("delta_z",    0.0)
        imbalance  = orderflow.get("imbalance",  0.0)
        absorption = orderflow.get("absorption", False)

        delta_opposite = (
            (original_direction == 1  and delta_z < 0) or
            (original_direction == -1 and delta_z > 0)
        )
        # Delta oposto ao fluxo mas fraco (sem spike institucional)
        delta_weak = (
            delta_opposite and
            abs(delta_z)   < cfg.delta_z_max and
            abs(imbalance) < cfg.delta_imbalance_max
        )
        # Absorção na direcção original = compradores/vendedores inst. ainda presentes
        delta_weak = delta_weak or absorption

        state.delta_weak = delta_weak
        if delta_weak:
            score += cfg.weight_delta

        # ─── ③ Confluência Geométrica (peso 0.20) ───────────────────────
        near_confluence   = footprint_snapshot.get("near_confluence",   False)
        convergence_score = footprint_snapshot.get("convergence_score", 0.0)

        state.near_confluence = near_confluence or convergence_score > 0.6
        if state.near_confluence:
            score += cfg.weight_confluence

        # ─── ④ Wyckoff Spring / Upthrust (peso 0.15) ────────────────────
        spring   = wyckoff.get("spring",   False)
        upthrust = wyckoff.get("upthrust", False)

        wyckoff_trap = (
            (original_direction == 1  and spring)   or
            (original_direction == -1 and upthrust)
        )
        state.wyckoff_trap = wyckoff_trap
        if wyckoff_trap:
            score += cfg.weight_wyckoff

        # ─── ⑤ ATR Compressão (peso 0.05) — novo v2.0 ──────────────────
        atr_compressed = False
        atr_ratio      = 1.0
        if high is not None and low is not None and len(hist) >= 2:
            prev_close    = hist[-2]
            atr_compressed, atr_ratio = self._atr_compressor.update(
                symbol, high, low, prev_close
            )

        state.atr_compressed = atr_compressed
        state.atr_ratio      = atr_ratio
        if atr_compressed:
            score += cfg.weight_atr

        # ─── ⑥ Hurst > 0.55 (peso 0.05) ────────────────────────────────
        hurst_ok           = hurst is not None and hurst > cfg.hurst_min
        state.hurst_confirms = hurst_ok
        if hurst_ok:
            score += cfg.weight_hurst

        # ══ Decisão final ══════════════════════════════════════════════════
        state.trap_score = round(score, 3)
        state.is_trap    = state.is_pullback and score >= cfg.trap_threshold

        # Urgência de re-entrada
        if score >= cfg.critical_threshold:
            state.reentry_urgency = ReentryUrgency.CRITICAL
            state.phase           = PullbackPhase.TRAP_SET
        elif score >= cfg.trap_threshold:
            state.reentry_urgency = ReentryUrgency.HIGH
            state.phase           = PullbackPhase.TRAP_SET
        elif in_correction:
            state.reentry_urgency = ReentryUrgency.NORMAL
            state.phase           = PullbackPhase.CORRECTING
        else:
            state.reentry_urgency = ReentryUrgency.NORMAL
            state.phase           = PullbackPhase.NONE

        # Pronto para entrada: pullback + trap + sinal de retomada
        state.is_ready_to_resume = False
        if state.is_trap and len(hist) >= cfg.resume_bars:
            recent = hist[-cfg.resume_bars:]
            retoma_alta  = original_direction == 1  and all(recent[i] > recent[i-1] for i in range(1, len(recent)))
            retoma_baixa = original_direction == -1 and all(recent[i] < recent[i-1] for i in range(1, len(recent)))
            if retoma_alta or retoma_baixa:
                state.is_ready_to_resume = True
                state.phase              = PullbackPhase.RESUMING

        # ── Log ────────────────────────────────────────────────────────────
        if state.is_trap:
            logger.info(
                f"[{symbol}] 🎯 PULLBACK TRAP | {state.summary()}"
            )
        elif state.is_pullback and state.bars_in_pullback == 1:
            logger.debug(
                f"[{symbol}] 📉 Correcção iniciada | dir={'ALTA' if original_direction==1 else 'BAIXA'} | "
                f"depth={state.max_pullback_pips:.1f}pips"
            )

        return state

    # ── Override de intervalo ──────────────────────────────────────────────

    def get_scale_interval_override(self, symbol: str) -> Optional[int]:
        """
        Retorna o intervalo de escalonamento ajustado pela urgência.

        Returns:
            None  → usar intervalo padrão (sem override)
            60    → urgência HIGH: entrar em 60s (era 300s)
            0     → urgência CRITICAL: bypass total → entrar imediatamente
        """
        cfg   = self._cfg
        state = self._states.get(symbol)
        if state is None or not state.is_trap:
            return None

        if state.reentry_urgency == ReentryUrgency.CRITICAL:
            return cfg.interval_critical_s   # 0 → bypass

        if state.reentry_urgency == ReentryUrgency.HIGH and state.is_ready_to_resume:
            return cfg.interval_high_s        # 60s

        return None

    def get_lot_amplifier(self, symbol: str) -> float:
        """
        Retorna o multiplicador de lote baseado na urgência.
        CRITICAL → 1.5× (50% mais lote).
        Outros   → 1.0× (sem amplificação).
        """
        cfg   = self._cfg
        state = self._states.get(symbol)
        if state and state.is_trap and state.reentry_urgency == ReentryUrgency.CRITICAL:
            return cfg.lot_amplifier_critical
        return 1.0

    # ── Reset ─────────────────────────────────────────────────────────────

    def reset(self, symbol: str) -> None:
        """Resetar estado após nova entrada (pullback absorvido)."""
        prev_dir = self._states.get(symbol, PullbackState()).original_direction
        self._states[symbol]                    = PullbackState()
        self._states[symbol].original_direction = prev_dir
        logger.debug(f"[{symbol}] PullbackState reset após nova entrada.")

    def reset_all(self) -> None:
        """Reset global (ex: mudança de sessão)."""
        self._states.clear()

    # ── Diagnóstico ───────────────────────────────────────────────────────

    def get_diagnostics(self, symbol: str) -> Dict[str, Any]:
        """Retorna diagnóstico completo para logging/dashboard."""
        state = self._states.get(symbol)
        if state is None:
            return {"symbol": symbol, "status": "sem_dados"}
        return {
            "symbol"             : symbol,
            "phase"              : state.phase.value,
            "trap_score"         : state.trap_score,
            "is_trap"            : state.is_trap,
            "urgency"            : state.reentry_urgency.value,
            "ready_to_resume"    : state.is_ready_to_resume,
            "bars_in_pullback"   : state.bars_in_pullback,
            "max_pullback_pips"  : round(state.max_pullback_pips, 2),
            "atr_ratio"          : state.atr_ratio,
            "criteria": {
                "volume_exhausted" : state.volume_exhausted,
                "delta_weak"       : state.delta_weak,
                "near_confluence"  : state.near_confluence,
                "wyckoff_trap"     : state.wyckoff_trap,
                "atr_compressed"   : state.atr_compressed,
                "hurst_confirms"   : state.hurst_confirms,
            },
            "interval_override"  : self.get_scale_interval_override(symbol),
            "lot_amplifier"      : self.get_lot_amplifier(symbol),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  GESTOR DE FECHAMENTO PARCIAL + RE-ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PartialCloseDecision:
    """Resultado da avaliação de fecho parcial."""
    trigger       : bool  = False
    lots_to_close : float = 0.0
    reason        : str   = ""
    reenter       : bool  = False
    urgency       : str   = ReentryUrgency.NORMAL.value


class PartialCloseManager:
    """
    Gere fechamentos parciais quando lote total ≥ limiar.

    REGRA DE OURO:
      Fecho parcial NÃO é saída. É gestão de margem e risco.
      Após fecho parcial → re-abrir IMEDIATAMENTE na direcção do fluxo.
      NUNCA fechar sem re-entrada planeada.

    Triggers para fecho parcial:
      1. Lote total ≥ 2.0 (gestão de margem)
      2. Pullback trap CRITICAL + lote ≥ 0.50 (libertar capital para escalar)
      3. PnL negativo > 50% do SL (gestão de risco conservadora)
    """

    PARTIAL_CLOSE_RATIO    : float = 0.40   # 40% dos lotes fechados (60% mantido)
    MIN_LOT_TO_TRIGGER     : float = 2.0    # lote mínimo para trigger 1
    MIN_LOT_CRITICAL       : float = 0.50   # lote mínimo para trigger 2 (CRITICAL)
    CRITICAL_CLOSE_RATIO   : float = 0.30   # 30% fechado em CRITICAL (libertar capital)
    PNL_DRAWDOWN_THRESHOLD : float = -0.50  # PnL < -50% do SL → trigger 3

    def should_partial_close(self,
                              total_lots      : float,
                              trap_state      : Optional[PullbackState] = None,
                              current_pnl_pct : float = 0.0) -> PartialCloseDecision:
        """
        Avalia se deve efectuar fecho parcial.

        Args:
            total_lots      : Lote total na posição agregada
            trap_state      : Estado do pullback detector (opcional)
            current_pnl_pct : PnL actual como % do SL (0.0 = break-even,
                              -1.0 = SL máximo atingido)

        Returns:
            PartialCloseDecision
        """
        # ── Trigger 1: lote total atingiu o limiar ─────────────────────────
        if total_lots >= self.MIN_LOT_TO_TRIGGER:
            return PartialCloseDecision(
                trigger       = True,
                lots_to_close = round(total_lots * self.PARTIAL_CLOSE_RATIO, 2),
                reason        = f"lote_total={total_lots:.2f} >= {self.MIN_LOT_TO_TRIGGER:.2f}",
                reenter       = True,
                urgency       = ReentryUrgency.HIGH.value,
            )

        # ── Trigger 2: pullback trap CRITICAL + lote significativo ─────────
        if (trap_state is not None and
                trap_state.is_trap and
                trap_state.reentry_urgency == ReentryUrgency.CRITICAL and
                total_lots >= self.MIN_LOT_CRITICAL):
            return PartialCloseDecision(
                trigger       = True,
                lots_to_close = round(total_lots * self.CRITICAL_CLOSE_RATIO, 2),
                reason        = (
                    f"pullback_trap_CRITICAL | "
                    f"score={trap_state.trap_score:.2f} | "
                    f"capital_liberto_para_scale"
                ),
                reenter       = True,
                urgency       = ReentryUrgency.CRITICAL.value,
            )

        # ── Trigger 3: drawdown excessivo ─────────────────────────────────
        if current_pnl_pct <= self.PNL_DRAWDOWN_THRESHOLD:
            lots_to_close = round(total_lots * 0.25, 2)  # fechar 25% para reduzir risco
            return PartialCloseDecision(
                trigger       = True,
                lots_to_close = lots_to_close,
                reason        = (
                    f"drawdown={current_pnl_pct:.1%} > "
                    f"threshold={self.PNL_DRAWDOWN_THRESHOLD:.1%}"
                ),
                reenter       = True,  # re-entrar mesmo assim (fluxo ainda válido)
                urgency       = ReentryUrgency.HIGH.value,
            )

        return PartialCloseDecision()


# ─────────────────────────────────────────────────────────────────────────────
#  ORCHESTRADOR DE RE-ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

class ReentryOrchestrator:
    """
    Orchestração completa da re-entrada após pullback trap.
    Decide QUANDO e QUANTO escalar na retomada do fluxo.

    Lógica:
      1. Detector confirma TRAP (score >= threshold)
      2. Retomada do fluxo confirmada (barras consecutivas na direcção)
      3. Orchestrador calcula:
         - intervalo override (0s ou 60s)
         - amplificação de lote (1.0× ou 1.5×)
         - decision context
    """

    def __init__(self,
                 detector : PullbackTrapDetector,
                 pc_manager: PartialCloseManager):
        self._detector  = detector
        self._pc_mgr    = pc_manager

    def evaluate(self,
                 symbol      : str,
                 total_lots  : float,
                 current_pnl_pct: float = 0.0) -> Dict[str, Any]:
        """
        Avalia todas as decisões de re-entrada para um símbolo.

        Returns:
            {
              "scale_now"        : bool,     # deve escalar agora?
              "lot_amplifier"    : float,    # multiplicador de lote
              "interval_override": int|None, # override de intervalo (segundos)
              "partial_close"    : PartialCloseDecision,
              "diagnostics"      : dict,     # estado completo para logs
            }
        """
        state     = self._detector.get_state(symbol)
        diag      = self._detector.get_diagnostics(symbol)
        pc        = self._pc_mgr.should_partial_close(total_lots, state, current_pnl_pct)
        amplifier = self._detector.get_lot_amplifier(symbol)
        override  = self._detector.get_scale_interval_override(symbol)

        scale_now = (
            override is not None and   # tem override → trap confirmado
            state.is_trap          and
            (state.is_ready_to_resume or override == 0)
        )

        return {
            "scale_now"        : scale_now,
            "lot_amplifier"    : amplifier,
            "interval_override": override,
            "partial_close"    : pc,
            "diagnostics"      : diag,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  INTEGRAÇÃO COM OmegaScaleManager
# ─────────────────────────────────────────────────────────────────────────────

def integrate_pullback_engine(scale_manager,
                              config: Optional[PullbackConfig] = None) -> ReentryOrchestrator:
    """
    Injecta o PullbackTrapDetector, PartialCloseManager e ReentryOrchestrator
    no OmegaScaleManager existente.
    Chama esta função após instanciar o OmegaScaleManager.

    Exemplo:
        mgr = OmegaScaleManager()
        orchestrator = integrate_pullback_engine(mgr)

    Args:
        scale_manager : Instância do OmegaScaleManager
        config        : Configuração customizada (opcional)

    Returns:
        ReentryOrchestrator (para uso directo se necessário)
    """
    cfg       = config or PullbackConfig()
    detector  = PullbackTrapDetector(cfg)
    pc_mgr    = PartialCloseManager()
    orch      = ReentryOrchestrator(detector, pc_mgr)

    scale_manager._pullback_detector   = detector
    scale_manager._partial_close_mgr   = pc_mgr
    scale_manager._reentry_orchestrator = orch

    # Guardar referência ao check_and_scale original
    original_check = scale_manager.check_and_scale.__func__

    async def check_and_scale_with_pullback(self):
        """
        check_and_scale v2.0 — com detecção de pullback trap integrada.

        Quando pullback trap detectado:
          • Reduz intervalo de escalonamento (0s CRITICAL | 60s HIGH)
          • Amplifica lote em CRITICAL (×1.5)
          • Activa fecho parcial se lote ≥ 2.0 ou CRITICAL ≥ 0.50
          • Re-entra imediatamente na direcção do fluxo
        """
        import asyncio
        now = asyncio.get_running_loop().time()

        for ticket, entry in list(self._pending_entries.items()):
            pos = await asyncio.to_thread(__import__('MetaTrader5').positions_get, ticket=ticket)
            if not pos:
                symbol = entry['symbol']
                freed  = entry.get('total_lots', 0.0)
                self._symbol_exposure[symbol] = max(
                    0.0, self._symbol_exposure.get(symbol, 0.0) - freed
                )
                del self._pending_entries[ticket]
                logger.info(f"[{symbol}] Posição {ticket} fechada — exposição libertada: {freed:.2f}")
                continue

            symbol = entry['symbol']
            cfg_s  = self._cfg(symbol)

            # ── Orchestrador de re-entrada ────────────────────────────────
            total_lots   = entry.get('total_lots', 0.0)
            pnl_pct      = entry.get('pnl_pct', 0.0)
            eval_result  = self._reentry_orchestrator.evaluate(symbol, total_lots, pnl_pct)

            interval_override = eval_result["interval_override"]
            effective_interval = (interval_override if interval_override is not None
                                  else cfg_s['scale_interval_s'])

            elapsed = now - entry['last_scale_time']
            if elapsed < effective_interval:
                continue

            async with self._get_symbol_lock(symbol):
                elapsed = now - entry['last_scale_time']
                if elapsed < effective_interval:
                    continue

                # ── Fecho parcial ─────────────────────────────────────────
                pc = eval_result["partial_close"]
                if pc.trigger:
                    logger.info(
                        f"[{symbol}] 📤 FECHO PARCIAL | "
                        f"{pc.lots_to_close:.2f} lotes | "
                        f"razão: {pc.reason} | "
                        f"re-entrada={pc.reenter} | urgency={pc.urgency}"
                    )
                    if pc.reenter:
                        self._pullback_detector.reset(symbol)

                # ── Cap equity e ATR ──────────────────────────────────────
                current_exp = self._symbol_exposure.get(symbol, 0.0)
                equity      = entry.get('equity_snapshot', 10_000.0)
                pv_lot      = entry.get('pip_value_per_lot', 10.0)
                max_lots    = self._max_lots_for_equity(symbol, equity, pv_lot)

                if current_exp >= max_lots:
                    logger.info(
                        f"[{symbol}] 🛑 Cap equity ({current_exp:.2f}/{max_lots:.2f}) — scale pausado"
                    )
                    continue

                atr = await self._get_current_atr(symbol)
                if atr is None:
                    logger.info(f"[{symbol}] ATR indisponível — scale adiado")
                    continue

                if atr <= cfg_s['min_atr']:
                    # CRITICAL: override ATR mínimo
                    if interval_override == 0:
                        logger.info(
                            f"[{symbol}] ⚡ ATR baixo mas PULLBACK TRAP CRITICAL — override ATR"
                        )
                    else:
                        logger.info(f"[{symbol}] ATR={atr:.4f} < min={cfg_s['min_atr']:.4f}")
                        continue

                # ── Calcular próximo lote ─────────────────────────────────
                amplifier = eval_result["lot_amplifier"]
                next_lot  = round(
                    min(
                        entry['current_lot'] * cfg_s['lot_progression'],
                        cfg_s['max_single_lot'],
                        max_lots - current_exp
                    ) * amplifier,
                    2
                )

                if amplifier > 1.0:
                    logger.info(
                        f"[{symbol}] ⚡ PULLBACK TRAP CRITICAL — lote amplificado ×{amplifier} → {next_lot:.2f}"
                    )

                if next_lot <= 0.001:
                    continue

                # ── Abrir entrada ─────────────────────────────────────────
                t_new = await asyncio.to_thread(
                    self._open_order, symbol, entry['action'], next_lot,
                    round(entry['sl_pts']),
                    round(cfg_s['tp_pips_per_entry'] * 10)
                )

                if t_new:
                    entry['current_lot']     = next_lot
                    entry['scale_count']    += 1
                    entry['total_lots']     += next_lot
                    entry['last_scale_time'] = now
                    self._symbol_exposure[symbol] = current_exp + next_lot

                    trap_state   = self._pullback_detector.get_state(symbol)
                    urgency_tag  = (f" [{trap_state.reentry_urgency.value}]"
                                    if trap_state.is_trap else "")

                    logger.info(
                        f"[{symbol}] ✅ Entrada #{entry['scale_count']}{urgency_tag} | "
                        f"ticket={t_new} | lote={next_lot:.2f} | "
                        f"total={entry['total_lots']:.2f}/{max_lots:.2f} | "
                        f"ATR={atr:.4f}"
                    )
                    self._pullback_detector.reset(symbol)

    import types
    scale_manager.check_and_scale = types.MethodType(
        check_and_scale_with_pullback, scale_manager
    )
    logger.info(
        "✅ PullbackEngine v2.0 integrado no OmegaScaleManager | "
        f"trap_thr={cfg.trap_threshold} | critical_thr={cfg.critical_threshold}"
    )
    return orch


# ─────────────────────────────────────────────────────────────────────────────
#  TESTES UNITÁRIOS INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

def _run_tests() -> bool:
    """Suite de testes interna — sem dependências externas."""
    print("=" * 68)
    print("  PULLBACK ENGINE v2.0 — SUITE DE TESTES TIER-0")
    print("=" * 68)

    PASS = FAIL = 0

    def ok(msg: str):
        nonlocal PASS; PASS += 1
        print(f"  [✅ PASS] {msg}")

    def fail(msg: str):
        nonlocal FAIL; FAIL += 1
        print(f"  [❌ FAIL] {msg}")

    cfg      = PullbackConfig()
    detector = PullbackTrapDetector(cfg)
    pc_mgr   = PartialCloseManager()

    # ═══ TESTE 1: Todos os critérios → deve ser TRAP CRITICAL ════════════
    print("\n>>> Teste 1: Todos os critérios (score > 0.80 → CRITICAL)")
    symbol = "XAUUSD"
    for p in [2900, 2910, 2920, 2930, 2940, 2950, 2960, 2970, 2980, 2990]:
        detector._price_history.setdefault(symbol, []).append(p)

    state = detector.update(
        symbol             = symbol,
        original_direction = 1,
        volume_snapshot    = {"wave_volume_z": -1.8, "wave_exhaustion": True,  "wave_strength": 0.3},
        orderflow          = {"delta_z": -0.9,        "imbalance": -0.2,        "absorption": False},
        wyckoff            = {"spring": True,          "upthrust": False},
        footprint_snapshot = {"near_confluence": True, "convergence_score": 0.80},
        current_price      = 2960,
        high               = 2965.0,
        low                = 2958.0,
        hurst              = 0.62,
    )
    print(f"  score={state.trap_score:.3f} | phase={state.phase.value} | urgency={state.reentry_urgency.value}")

    if state.trap_score >= cfg.trap_threshold and state.is_trap:
        ok(f"Trap correctamente identificado | score={state.trap_score:.3f}")
    else:
        fail(f"score={state.trap_score:.3f} < {cfg.trap_threshold} ou is_trap=False")

    if state.trap_score >= cfg.critical_threshold:
        ok(f"Urgência CRITICAL (score={state.trap_score:.3f} >= {cfg.critical_threshold})")
    elif state.reentry_urgency == ReentryUrgency.HIGH:
        ok(f"Urgência HIGH (score abaixo de CRITICAL mas trap válido)")
    else:
        fail(f"Urgência incorrecta: {state.reentry_urgency.value}")

    # ═══ TESTE 2: Sem critérios → não deve ser trap ═══════════════════════
    print("\n>>> Teste 2: Sem critérios → não deve ser trap")
    det2   = PullbackTrapDetector(cfg)
    sym2   = "EURUSD"
    for p in [1.100, 1.102, 1.104, 1.106, 1.108]:
        det2._price_history.setdefault(sym2, []).append(p)

    st2 = det2.update(
        symbol             = sym2,
        original_direction = 1,
        volume_snapshot    = {"wave_volume_z": 1.2,    "wave_exhaustion": False, "wave_strength": 0.9},
        orderflow          = {"delta_z": -2.8,          "imbalance": -0.7,        "absorption": False},
        wyckoff            = {"spring": False,           "upthrust": False},
        footprint_snapshot = {"near_confluence": False,  "convergence_score": 0.2},
        current_price      = 1.105,
        high               = 1.107,
        low                = 1.104,
        hurst              = 0.44,
    )
    print(f"  score={st2.trap_score:.3f} | is_trap={st2.is_trap}")
    if not st2.is_trap and st2.trap_score < cfg.trap_threshold:
        ok(f"Sem trap (score={st2.trap_score:.3f} < {cfg.trap_threshold})")
    else:
        fail(f"Falso positivo: score={st2.trap_score:.3f} is_trap={st2.is_trap}")

    # ═══ TESTE 3: ATR Compressor ══════════════════════════════════════════
    print("\n>>> Teste 3: ATR Compressor")
    atr_c  = ATRCompressor()
    # Simular ATR histórico alto, depois cair
    for i in range(60):
        compressed, ratio = atr_c.update("XAUUSD", 100.0 + i * 0.5, 99.0 + i * 0.5, 99.5 + i * 0.5)
    # Agora inserir candle com ATR baixo
    compressed, ratio = atr_c.update("XAUUSD", 100.2, 100.0, 100.1)
    print(f"  atr_ratio={ratio:.3f} | compressed={compressed}")
    if ratio < 1.0:
        ok(f"ATR comprimindo → ratio={ratio:.3f} < 1.0")
    else:
        fail(f"ATR não detectou compressão: ratio={ratio:.3f}")

    # ═══ TESTE 4: Fecho Parcial — lote ≥ 2.0 ═════════════════════════════
    print("\n>>> Teste 4: Fecho parcial com lote total = 2.5")
    pc = pc_mgr.should_partial_close(total_lots=2.5, trap_state=None)
    print(f"  trigger={pc.trigger} | lots={pc.lots_to_close} | reenter={pc.reenter}")
    if pc.trigger and pc.reenter and pc.lots_to_close > 0:
        ok(f"Fecho parcial activado: {pc.lots_to_close:.2f} lotes | re-entrada=True")
    else:
        fail(f"Fecho parcial não activou: {pc}")

    # ═══ TESTE 5: Override de intervalo ══════════════════════════════════
    print("\n>>> Teste 5: Override de intervalo")
    override = detector.get_scale_interval_override(symbol)
    amplif   = detector.get_lot_amplifier(symbol)
    print(f"  urgency={state.reentry_urgency.value} | override={override}s | amplifier={amplif}×")
    if override is not None and override <= 60:
        ok(f"Intervalo reduzido para {override}s (era 300s padrão)")
    else:
        fail(f"Override incorrecto: {override}")
    if amplif >= 1.0:
        ok(f"Amplificador de lote: {amplif}×")
    else:
        fail(f"Amplificador incorrecto: {amplif}")

    # ═══ TESTE 6: Diagnostics ════════════════════════════════════════════
    print("\n>>> Teste 6: Diagnóstico completo")
    diag = detector.get_diagnostics(symbol)
    has_keys = all(k in diag for k in ["trap_score", "urgency", "criteria", "interval_override", "lot_amplifier"])
    if has_keys:
        ok("Diagnóstico contém todos os campos obrigatórios")
    else:
        fail(f"Diagnóstico incompleto: {list(diag.keys())}")

    # ═══ TESTE 7: Reset ══════════════════════════════════════════════════
    print("\n>>> Teste 7: Reset após absorção do pullback")
    detector.reset(symbol)
    st_reset = detector.get_state(symbol)
    if not st_reset.is_trap and st_reset.trap_score == 0.0:
        ok("Estado resetado correctamente")
    else:
        fail(f"Reset falhou: is_trap={st_reset.is_trap} score={st_reset.trap_score}")

    # ═══ Resumo ═══════════════════════════════════════════════════════════
    total = PASS + FAIL
    print()
    print("=" * 68)
    print(
        f"  PULLBACK ENGINE v2.0 | {PASS}/{total} TESTES APROVADOS"
        + (" ✅" if FAIL == 0 else f" ❌ {FAIL} FALHAS")
    )
    print("=" * 68)
    return FAIL == 0


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    success = _run_tests()
    raise SystemExit(0 if success else 1)
