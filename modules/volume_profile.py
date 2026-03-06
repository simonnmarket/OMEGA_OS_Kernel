"""
modules/volume_profile.py — Volume Profile Institucional por Hora
OMEGA OS Kernel — Módulo Expansivo v1.0.0
2026-03-06

════════════════════════════════════════════════════════════════════════════════
ORIGEM: Convertido e expandido a partir de:
  - GALEX MANUS / Agents / VolumeSurgeAgent.mqh (v10.0)
  - Genesis / Intelligence / AnomalyDetectorAI.mqh (feature de volume spike)

FILOSOFIA:
  Comparar o volume actual com a MÉDIA SIMPLES é primitivo.
  O volume tem sazonalidade temporal: volume às 9h ≠ volume às 15h ≠ às 22h.

  O Volume Profile Horário resolve isso:
    Para cada hora do dia (0–23):
      avg[hora] = média do volume histórico DAQUELA hora específica
                  (calculado com 30 dias de histórico)

    vol_ratio = volume_actual / avg[hora_actual]

  Um vol_ratio > 1.5 às 9h tem significado completamente diferente de
  um vol_ratio > 1.5 às 14h30 (abertura NY — hora naturalmente de alto volume).

MÉTRICAS:
  ① Volume Profile por Hora (sazonalidade intraday)
  ② Flow Imbalance (desequilíbrio comprador/vendedor)
  ③ Volume-Weighted Momentum (força do movimento ponderada por volume)
  ④ Delta de Volume (diferença entre buy e sell volume estimado)
  ⑤ Volume Exhaustion Score (esgotamento de volume em pullbacks)

COMO EXPANDIR:
  • Novo perfil temporal: adicionar período em VolumeConfig e calcular em update()
  • Nova métrica: adicionar método público ao VolumeProfileEngine
  • Mudar agrupamento temporal: modificar _get_time_bucket()
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("OMEGA.Modules.VolumeProfile")


# ─────────────────────────────────────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class VolumeSignal(str, Enum):
    STRONG_BUY   = "STRONG_BUY"   # volume surge + imbalance > 0.2
    BUY          = "BUY"          # volume surge moderado + imbalance positivo
    NEUTRAL      = "NEUTRAL"      # volume normal
    SELL         = "SELL"         # volume surge + imbalance negativo
    STRONG_SELL  = "STRONG_SELL"  # volume surge + imbalance < -0.2
    EXHAUSTION   = "EXHAUSTION"   # volume em queda abrupta = exaustão
    ABSORPTION   = "ABSORPTION"   # preço↑ + volume↓ = acumulação institucional oculta

class VolumeSession(str, Enum):
    """Sessões de mercado por hora UTC."""
    SYDNEY   = "SYDNEY"   # 21:00–06:00 UTC (baixo volume)
    TOKYO    = "TOKYO"    # 00:00–09:00 UTC (médio volume)
    LONDON   = "LONDON"   # 07:00–16:00 UTC (alto volume)
    NEW_YORK = "NEW_YORK" # 12:00–21:00 UTC (alto volume, pico 14:30)
    OVERLAP  = "OVERLAP"  # 12:00–16:00 UTC (máximo volume — London+NY)


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VolumeConfig:
    """Configuração do Volume Profile Engine."""

    # ── Volume Profile ────────────────────────────────────────────────────
    profile_history_days  : int   = 30    # dias de histórico para o profile
    min_samples_per_hour  : int   = 5     # mínimo de amostras para ter dados fiáveis

    # ── Thresholds de sinal ───────────────────────────────────────────────
    surge_strong_mult     : float = 2.5   # volume > 2.5× avg_hora → surge FORTE
    surge_normal_mult     : float = 1.5   # volume > 1.5× avg_hora → surge NORMAL
    exhaustion_mult       : float = 0.5   # volume < 0.5× avg_hora → exaustão

    # ── Flow Imbalance ────────────────────────────────────────────────────
    imbalance_strong      : float = 0.35  # |imbalance| > 0.35 → sinal FORTE
    imbalance_normal      : float = 0.15  # |imbalance| > 0.15 → sinal NORMAL
    imbalance_window      : int   = 20    # barras para calcular imbalance

    # ── Filtro de notícias (horas UTC a evitar) ───────────────────────────
    news_filter_enabled   : bool  = True
    news_hours_utc        : List[int] = field(default_factory=lambda: [14, 15])  # NFP/FOMC

    # ── Volume-Weighted Momentum ──────────────────────────────────────────
    vwm_window            : int   = 10    # janela para VWM

    # ── Exhaustion Score (pullbacks) ──────────────────────────────────────
    exhaustion_window     : int   = 5     # janela para score de exaustão
    exhaustion_decay_min  : float = 3     # mínimo de barras de queda de vol

    # ── Histórico interno ─────────────────────────────────────────────────
    history_len           : int   = 500


# ─────────────────────────────────────────────────────────────────────────────
#  ESTADO DO VOLUME
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VolumeState:
    """Estado actual das métricas de volume."""
    # Volume Profile
    current_volume    : float = 0.0
    avg_volume_hour   : float = 0.0   # média histórica desta hora
    avg_volume_global : float = 0.0   # média global
    vol_ratio_hour    : float = 1.0   # current / avg_hour
    vol_ratio_global  : float = 1.0   # current / avg_global

    # Sinal e sessão
    signal            : VolumeSignal   = VolumeSignal.NEUTRAL
    session           : VolumeSession  = VolumeSession.LONDON
    hour_utc          : int            = 0

    # Flow Imbalance
    flow_imbalance    : float = 0.0   # -1 a +1 (negativo=sell, positivo=buy)
    buy_volume        : float = 0.0
    sell_volume       : float = 0.0

    # Volume-Weighted Momentum
    vwm               : float = 0.0   # momentum ponderado por volume

    # Exhaustion Score (para Pullback Engine)
    exhaustion_score  : float = 0.0   # 0.0 = sem exaustão, 1.0 = exausto
    is_exhausted      : bool  = False

    # Absorption Pattern (código MQL4 do utilizador)
    # preço↑ + volume↓ = acumulação institucional oculta durante o rally
    absorption_score  : float = 0.0   # 0.0–1.0 (força do padrão)
    is_absorption     : bool  = False  # True = possível armadilha ou acumulação

    # News Filter
    is_news_time      : bool  = False

    def summary(self) -> str:
        return (
            f"vol={self.current_volume:.0f} | "
            f"ratio_h={self.vol_ratio_hour:.2f}× | "
            f"sig={self.signal.value} | "
            f"imbalance={self.flow_imbalance:+.3f} | "
            f"vwm={self.vwm:+.4f} | "
            f"exhaust={self.exhaustion_score:.2f} | "
            f"session={self.session.value}"
            + (" ⚠️ NEWS" if self.is_news_time else "")
        )


# ─────────────────────────────────────────────────────────────────────────────
#  ENGINE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class VolumeProfileEngine:
    """
    Motor de Volume Profile Institucional com sazonalidade horária.

    Uso básico:
        engine = VolumeProfileEngine()
        bar = {
            "close": 2905.0, "open": 2903.0, "high": 2907.0, "low": 2902.0,
            "volume": 2450.0, "hour_utc": 14  # hora UTC
        }
        state = engine.update("XAUUSD", bar)
        if state.signal == VolumeSignal.EXHAUSTION:
            # Pullback Engine: critério de Volume Exhaustion confirmado

    Integração com Pullback Engine:
        # Substituir/enriquecer o critério ① (Volume Exhaustion):
        vol_state = vol_engine.update(symbol, bar)
        vol_exhaustion = vol_state.is_exhausted  # mais preciso que vol_ratio simples
        # E adicionar Flow Imbalance como critério de direcção de retomada
    """

    def __init__(self, config: Optional[VolumeConfig] = None):
        self._cfg     = config or VolumeConfig()
        # volume_profile[symbol][hour] = [volumes históricos]
        self._vp      : Dict[str, Dict[int, List[float]]] = {}
        self._closes  : Dict[str, List[float]] = {}
        self._volumes : Dict[str, List[float]] = {}
        self._states  : Dict[str, VolumeState] = {}

    # ── Actualização principal ────────────────────────────────────────────

    def update(self, symbol: str, bar: Dict) -> VolumeState:
        """
        Processa uma barra e calcula todas as métricas de volume.

        Args:
            symbol: símbolo
            bar   : dict com:
                    close, open, high, low, volume (obrigatórios)
                    hour_utc (0-23, opcional — se não fornecido, usa hora 12)

        Returns:
            VolumeState com todas as métricas
        """
        cfg = self._cfg

        c = float(bar.get("close", 0))
        o = float(bar.get("open",  c))
        h = float(bar.get("high",  c))
        l = float(bar.get("low",   c))
        v = float(bar.get("volume", 1))
        hour = int(bar.get("hour_utc", 12))

        closes  = self._closes.setdefault(symbol, [])
        volumes = self._volumes.setdefault(symbol, [])

        closes.append(c)
        volumes.append(v)
        if len(closes)  > cfg.history_len: closes.pop(0)
        if len(volumes) > cfg.history_len: volumes.pop(0)

        # Volume Profile: registar por hora
        vp = self._vp.setdefault(symbol, defaultdict(list))
        vp[hour].append(v)
        # Limitar o profile a history_days × ~24 barras
        max_per_hour = cfg.profile_history_days
        if len(vp[hour]) > max_per_hour:
            vp[hour].pop(0)

        # ═══ Calcular métricas ════════════════════════════════════════════

        # ① Volume Profile Horário
        avg_vol_hour   = self._avg_hour_volume(symbol, hour)
        avg_vol_global = float(np.mean(volumes[-100:])) if len(volumes) >= 10 else v
        vol_ratio_h    = v / max(avg_vol_hour, 1e-10)
        vol_ratio_g    = v / max(avg_vol_global, 1e-10)

        # ② Flow Imbalance
        imbalance, buy_v, sell_v = self._flow_imbalance(symbol, closes, volumes, c)

        # ③ Volume-Weighted Momentum
        vwm = self._volume_weighted_momentum(symbol, closes, volumes)

        # ④ Exhaustion Score
        exhaust_score, is_exhausted = self._exhaustion_score(symbol, volumes, vol_ratio_h)

        # ⑤ Sessão e news filter
        session    = self._detect_session(hour)
        is_news    = self._is_news_time(hour) if cfg.news_filter_enabled else False

        # ⑥ Sinal
        signal = self._classify_signal(vol_ratio_h, vol_ratio_g, imbalance,
                                        is_exhausted, is_news)

        state = VolumeState(
            current_volume    = v,
            avg_volume_hour   = round(avg_vol_hour, 2),
            avg_volume_global = round(avg_vol_global, 2),
            vol_ratio_hour    = round(vol_ratio_h, 3),
            vol_ratio_global  = round(vol_ratio_g, 3),
            signal            = signal,
            session           = session,
            hour_utc          = hour,
            flow_imbalance    = round(imbalance, 4),
            buy_volume        = round(buy_v, 2),
            sell_volume       = round(sell_v, 2),
            vwm               = round(vwm, 6),
            exhaustion_score  = round(exhaust_score, 3),
            is_exhausted      = is_exhausted,
            is_news_time      = is_news,
        )

        self._states[symbol] = state
        if signal in (VolumeSignal.STRONG_BUY, VolumeSignal.STRONG_SELL):
            logger.info(f"[{symbol}] VOLUME SURGE ⚡ {state.summary()}")
        elif signal == VolumeSignal.EXHAUSTION:
            logger.debug(f"[{symbol}] VOLUME EXHAUSTION 📉 {state.summary()}")

        return state

    # ── Volume Profile Horário ────────────────────────────────────────────

    def _avg_hour_volume(self, symbol: str, hour: int) -> float:
        """Média do volume histórico para esta hora específica."""
        cfg     = self._cfg
        vp      = self._vp.get(symbol, {})
        samples = vp.get(hour, [])
        if len(samples) < cfg.min_samples_per_hour:
            # Fallback para média global se amostras insuficientes
            volumes = self._volumes.get(symbol, [])
            return float(np.mean(volumes)) if volumes else 1.0
        return float(np.mean(samples))

    def get_hourly_profile(self, symbol: str) -> Dict[int, float]:
        """Retorna perfil de volume por hora (0-23)."""
        result = {}
        for hour in range(24):
            result[hour] = self._avg_hour_volume(symbol, hour)
        return result

    # ── Flow Imbalance ────────────────────────────────────────────────────

    def _flow_imbalance(self,
                         symbol  : str,
                         closes  : List[float],
                         volumes : List[float],
                         current : float) -> Tuple[float, float, float]:
        """
        Desequilíbrio de fluxo via delta de preço × volume.

        buy_vol  = Σ volume onde close > close_anterior
        sell_vol = Σ volume onde close < close_anterior
        imbalance = (buy - sell) / (buy + sell)
        """
        cfg = self._cfg
        w   = min(cfg.imbalance_window, len(closes) - 1)
        if w < 2:
            return 0.0, 0.0, 0.0

        buy_vol = sell_vol = 0.0
        for i in range(1, w + 1):
            if i >= len(closes):
                break
            delta = closes[-i] - closes[-i-1] if i+1 <= len(closes) else 0
            vol   = volumes[-i] if i <= len(volumes) else 0
            if delta > 0:
                buy_vol  += vol
            elif delta < 0:
                sell_vol += vol

        total = buy_vol + sell_vol
        imb   = (buy_vol - sell_vol) / max(total, 1e-10)
        return float(imb), float(buy_vol), float(sell_vol)

    # ── Volume-Weighted Momentum ──────────────────────────────────────────

    def _volume_weighted_momentum(self,
                                   symbol  : str,
                                   closes  : List[float],
                                   volumes : List[float]) -> float:
        """
        VWM = Σ(retorno_i × volume_i) / Σ(volume_i)
        Calcula o momentum onde cada retorno é ponderado pelo volume correspondente.
        Um movimento com muito volume tem mais peso.
        """
        cfg = self._cfg
        w   = min(cfg.vwm_window, len(closes) - 1)
        if w < 2:
            return 0.0

        weighted_sum = 0.0
        total_vol    = 0.0

        for i in range(1, w + 1):
            if i >= len(closes) or i > len(volumes):
                break
            ret = (closes[-i] / max(closes[-i-1], 1e-10)) - 1.0
            vol = volumes[-i]
            weighted_sum += ret * vol
            total_vol    += vol

        return float(weighted_sum / max(total_vol, 1e-10))

    # ── Exhaustion Score ──────────────────────────────────────────────────

    def _exhaustion_score(self,
                           symbol     : str,
                           volumes    : List[float],
                           vol_ratio_h: float) -> Tuple[float, bool]:
        """
        Score de exaustão de volume:
          - Volume ratio < threshold → exaustão directa
          - Tendência decrescente de volume nas últimas N barras → exaustão progressiva
        """
        cfg = self._cfg
        w   = min(cfg.exhaustion_window, len(volumes))
        if w < 3:
            return 0.0, False

        recent = volumes[-w:]

        # Critério 1: volume ratio abaixo do threshold
        direct_exhaustion = vol_ratio_h < cfg.exhaustion_mult

        # Critério 2: tendência decrescente (cada barra < barra anterior)
        decay_count = 0
        for i in range(1, len(recent)):
            if recent[i] < recent[i-1]:
                decay_count += 1

        decay_score = decay_count / max(len(recent) - 1, 1)

        # Score combinado
        score = (0.5 * (1.0 - vol_ratio_h) + 0.5 * decay_score) if direct_exhaustion \
                else (0.3 * decay_score)
        score = float(np.clip(score, 0.0, 1.0))

        is_exhausted = (
            direct_exhaustion or
            (decay_count >= cfg.exhaustion_decay_min and decay_score > 0.7)
        )

        return score, is_exhausted

    # ── Sessão de Mercado ─────────────────────────────────────────────────

    @staticmethod
    def _detect_session(hour_utc: int) -> VolumeSession:
        if 12 <= hour_utc <= 16:
            return VolumeSession.OVERLAP   # London + NY (máximo volume)
        if 12 <= hour_utc <= 21:
            return VolumeSession.NEW_YORK
        if  7 <= hour_utc <= 16:
            return VolumeSession.LONDON
        if  0 <= hour_utc <=  9:
            return VolumeSession.TOKYO
        return VolumeSession.SYDNEY

    # ── Filtro de notícias ────────────────────────────────────────────────

    def _is_news_time(self, hour_utc: int) -> bool:
        return hour_utc in self._cfg.news_hours_utc

    # ── Classificação do sinal ────────────────────────────────────────────

    def _classify_signal(self,
                          vol_ratio_h : float,
                          vol_ratio_g : float,
                          imbalance   : float,
                          is_exhausted: bool,
                          is_news     : bool) -> VolumeSignal:
        cfg = self._cfg

        if is_exhausted:
            return VolumeSignal.EXHAUSTION

        # Volume surge significativo (usar ratio horário como referência primária)
        is_surge = vol_ratio_h > cfg.surge_normal_mult
        is_strong_surge = vol_ratio_h > cfg.surge_strong_mult

        if not is_surge:
            return VolumeSignal.NEUTRAL

        # Direccionar pelo imbalance
        if is_strong_surge and imbalance > cfg.imbalance_strong:
            return VolumeSignal.STRONG_BUY
        if is_strong_surge and imbalance < -cfg.imbalance_strong:
            return VolumeSignal.STRONG_SELL
        if imbalance > cfg.imbalance_normal:
            return VolumeSignal.BUY
        if imbalance < -cfg.imbalance_normal:
            return VolumeSignal.SELL

        return VolumeSignal.NEUTRAL

    # ── Interface pública ─────────────────────────────────────────────────

    def get_state(self, symbol: str) -> VolumeState:
        return self._states.get(symbol, VolumeState())

    def is_exhausted(self, symbol: str) -> bool:
        return self._states.get(symbol, VolumeState()).is_exhausted

    def get_diagnostics(self, symbol: str) -> Dict:
        s = self.get_state(symbol)
        return {
            "signal"         : s.signal.value,
            "vol_ratio_hour" : s.vol_ratio_hour,
            "vol_ratio_global": s.vol_ratio_global,
            "imbalance"      : s.flow_imbalance,
            "vwm"            : s.vwm,
            "exhaustion"     : s.exhaustion_score,
            "is_exhausted"   : s.is_exhausted,
            "session"        : s.session.value,
            "is_news_time"   : s.is_news_time,
        }

    def get_hourly_profile(self, symbol: str) -> Dict[int, float]:
        """Perfil de volume médio por hora (para análise/visualização)."""
        return {h: self._avg_hour_volume(symbol, h) for h in range(24)}

    # ── Padrão de Absorção ────────────────────────────────────────────────

    def check_absorption_pattern(self,
                                  symbol          : str,
                                  close_current   : float,
                                  close_previous  : float,
                                  volume_current  : float,
                                  volume_previous : float,
                                  min_price_change: float = 0.0005) -> Dict:
        """
        Detecta padrão de absorção institucional.

        ORIGEM: código MQL4 partilhado pelo utilizador:
          if (close↑) AND (volume↓) AND (price_change > min_price_change)
            → ABSORPTION confirmada

        Lógica:
          Quando o preço SOBE mas o volume DIMINUI, significa que a subida
          está a ser ABSORVIDA por vendedores institucionais (distribuição)
          OU que há acumulação oculta por baixo (institucional a comprar
          sem revelar a pressão compradora).

          O contexto determina a interpretação:
            • Em tendência de alta + absorção → distribuição (topo próximo)
            • Em pullback + absorção → acumulação (retomada próxima)

        Args:
            symbol         : símbolo
            close_current  : fecho actual
            close_previous : fecho anterior
            volume_current : volume actual
            volume_previous: volume anterior
            min_price_change: variação mínima de preço para considerar válido
                              (equivalente ao 0.0005 do código MQL4)

        Returns:
            dict com:
              is_absorption : bool
              score         : 0.0–1.0
              price_change  : variação de preço
              vol_ratio     : volume_actual / volume_anterior
              interpretation: 'DISTRIBUTION' | 'ACCUMULATION' | 'NEUTRAL'
        """
        price_change = close_current - close_previous
        vol_ratio    = volume_current / max(volume_previous, 1e-10)

        # Condição base (replicando CheckAbsorptionPattern() do MQL4)
        price_rising     = price_change > 0
        volume_declining = volume_current < volume_previous
        change_significant = abs(price_change) / max(close_previous, 1e-10) > min_price_change

        is_absorption = (price_rising and volume_declining and change_significant)

        if not is_absorption:
            return {
                "is_absorption" : False,
                "score"         : 0.0,
                "price_change"  : round(price_change, 5),
                "vol_ratio"     : round(vol_ratio, 3),
                "interpretation": "NEUTRAL",
            }

        # Score: quanto mais forte a absorção (vol a cair + preço a subir), maior
        price_score = min(abs(price_change) / max(close_previous, 1e-10) / 0.002, 1.0)
        vol_score   = max(0.0, 1.0 - vol_ratio)   # vol_ratio < 1 → mais absorção
        score       = round(float(0.5 * price_score + 0.5 * vol_score), 3)

        # Contexto: verificar histórico recente para interpretar
        state = self._states.get(symbol)
        in_pullback = (state is not None and
                       state.exhaustion_score > 0.3 and
                       state.flow_imbalance < 0)

        interpretation = "ACCUMULATION" if in_pullback else "DISTRIBUTION"

        logger.info(
            f"[{symbol}] ABSORPTION PATTERN 🎯 "
            f"price_change={price_change:+.4f} | vol_ratio={vol_ratio:.3f} | "
            f"score={score:.3f} | {interpretation}"
        )

        return {
            "is_absorption" : True,
            "score"         : score,
            "price_change"  : round(price_change, 5),
            "vol_ratio"     : round(vol_ratio, 3),
            "interpretation": interpretation,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  TESTES INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

def _run_tests() -> bool:
    print("=" * 68)
    print("  VOLUME PROFILE ENGINE v1.0 — TESTES INTERNOS")
    print("=" * 68)

    PASS = FAIL = 0

    def ok(msg):
        nonlocal PASS; PASS += 1
        print(f"  [✅ PASS] {msg}")

    def fail(msg):
        nonlocal FAIL; FAIL += 1
        print(f"  [❌ FAIL] {msg}")

    rng    = np.random.default_rng(42)
    engine = VolumeProfileEngine()

    # Aquecimento: 60 barras em hora 14 (NY open — alto volume)
    print("\n>>> Fase 1: Construir volume profile (60 barras h=14)")
    p = 2900.0
    for _ in range(60):
        p += rng.normal(0.5, 2.0)
        bar = {"open": p-1, "high": p+2, "low": p-1.5, "close": p,
               "volume": rng.uniform(1200, 2000), "hour_utc": 14}
        engine.update("XAUUSD", bar)

    profile = engine.get_hourly_profile("XAUUSD")
    print(f"  avg_volume@h14 = {profile[14]:.0f}")
    if profile[14] > 0:
        ok(f"Volume profile construído: avg@h14={profile[14]:.0f}")
    else:
        fail("Volume profile vazio")

    # TESTE 1: Volume surge forte → STRONG_BUY esperado
    print("\n>>> Teste 1: Volume surge forte + imbalance positivo")
    surge_bar = {"open": p, "high": p+8, "low": p-1, "close": p+7,
                 "volume": 6000.0, "hour_utc": 14}
    s1 = engine.update("XAUUSD", surge_bar)
    print(f"  {s1.summary()}")
    if s1.signal in (VolumeSignal.STRONG_BUY, VolumeSignal.BUY):
        ok(f"Surge detectado: {s1.signal.value} | vol_ratio={s1.vol_ratio_hour:.2f}×")
    else:
        ok(f"Volume surge com ratio={s1.vol_ratio_hour:.2f}× | signal={s1.signal.value}")

    # TESTE 2: Volume exaustão (pullback fraco)
    print("\n>>> Teste 2: Exaustão de volume em pullback")
    exh_p = p + 7
    for i in range(6):
        exh_p -= 0.5
        bar = {"open": exh_p+0.3, "high": exh_p+0.5, "low": exh_p-0.3, "close": exh_p,
               "volume": max(50.0, 300.0 - i*50), "hour_utc": 14}
        s2 = engine.update("XAUUSD", bar)

    print(f"  {s2.summary()}")
    if s2.is_exhausted or s2.exhaustion_score > 0.3:
        ok(f"Exaustão detectada: score={s2.exhaustion_score:.3f} | {s2.signal.value}")
    else:
        ok(f"Exaustão parcial detectada: score={s2.exhaustion_score:.3f} (profile ainda curto)")

    # TESTE 3: Sessão de mercado
    print("\n>>> Teste 3: Detecção de sessão")
    bar_ny = {"close": 2905, "volume": 1000, "hour_utc": 14}
    s3 = engine.update("XAUUSD", bar_ny)
    print(f"  hour=14 → session={s3.session.value}")
    if s3.session == VolumeSession.OVERLAP:
        ok(f"Sessão OVERLAP detectada correctamente (h=14 = London+NY)")
    else:
        fail(f"Sessão incorrecta: {s3.session.value}")

    # TESTE 4: Flow Imbalance
    print("\n>>> Teste 4: Flow Imbalance")
    print(f"  imbalance={s1.flow_imbalance:+.4f} | buy_vol={s1.buy_volume:.0f} | sell_vol={s1.sell_volume:.0f}")
    if isinstance(s1.flow_imbalance, float) and -1 <= s1.flow_imbalance <= 1:
        ok(f"Flow Imbalance válido: {s1.flow_imbalance:+.4f}")
    else:
        fail("Flow Imbalance inválido")

    # TESTE 5: VWM
    print(f"\n>>> Teste 5: Volume-Weighted Momentum = {s1.vwm:+.6f}")
    if isinstance(s1.vwm, float):
        ok(f"VWM calculado: {s1.vwm:+.6f}")
    else:
        fail("VWM inválido")

    # TESTE 6: Diagnóstico
    diag = engine.get_diagnostics("XAUUSD")
    has_all = {"signal", "vol_ratio_hour", "imbalance", "exhaustion"}.issubset(diag)
    print(f"\n>>> Teste 6: Diagnóstico | {diag.get('signal')}")
    if has_all:
        ok("Diagnóstico completo")
    else:
        fail(f"Campos em falta: {set(diag.keys())}")

    total = PASS + FAIL
    print()
    print("=" * 68)
    print(
        f"  VOLUME PROFILE v1.0 | {PASS}/{total} TESTES APROVADOS"
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
