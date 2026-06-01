"""
LotCalculator V2.0 — OMEGA Position Sizing Engine
CQO-approved (Opção B) — 28/04/2026
Integra: Volatilidade ATR + Confiança IA + Fator Desempenho + Kelly (desativado).

Fórmula:
    lot = base_lot × vol_factor × confidence_factor × performance_factor × kelly_factor
    base_lot = (equity × RISK_PCT) / (expected_pts × pip_value_per_lot)

Limites CQO: base=0.10, min=0.05, max=0.10 (crypto CFD: muitos brokers rejeitam >0.10; forex: OMEGA_LOT_MAX)
Cost barrier: skip trade se expected_pts < OMEGA_COST_PTS (default 19).
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

log = logging.getLogger("OMEGA.LotCalcV2")


@dataclass
class LotCfgV2:
    base_lot:         float = float(os.getenv("OMEGA_LOT_BASE",  "0.10"))
    min_lot:          float = float(os.getenv("OMEGA_LOT_MIN",   "0.05"))
    max_lot:          float = float(os.getenv("OMEGA_LOT_MAX",   "0.10"))
    risk_pct:         float = float(os.getenv("OMEGA_RISK_PER_TRADE", "0.001"))
    vol_dampening:    float = 0.5          # CQO: √ raíz para suavizar
    atr_target_pct:   float = 0.0015      # 0.15% ref — vol neutral point
    perf_window:      int   = 10
    perf_boost_max:   float = 1.50
    perf_reduce_min:  float = 0.50
    conf_low:         float = 0.60
    conf_high:        float = 0.95
    cost_barrier_pts: float = float(os.getenv("OMEGA_COST_PTS", "19.0"))
    use_kelly:        bool  = os.getenv("OMEGA_USE_KELLY", "0") == "1"
    kelly_cap:        float = 0.25        # quarter-Kelly se ativado


class LotCalculatorV2:
    """
    4-factor adaptive position sizing para OMEGA.
    Instanciar 1 vez por run_loop (singleton por sessão).
    """

    def __init__(self, cfg: Optional[LotCfgV2] = None):
        self._cfg  = cfg or LotCfgV2()
        self._perf: List[float] = []            # +1 win / -1 loss
        self._atr_hist: Dict[str, List[float]] = {}  # symbol → ATR% history

    # ── public interface ──────────────────────────────────────────────────

    def calculate(self,
                  equity:            float,
                  atr_pct:           float,
                  atr_avg_pct:       float,
                  confidence:        float,
                  expected_pts:      float,
                  pip_value_per_lot: float,
                  sym_min_lot:       float = 0.01) -> Dict:
        """
        Calcula lote adaptativo.

        Args:
            equity:            equity real da conta (USD)
            atr_pct:           ATR% actual no execution TF (M3/M1)
            atr_avg_pct:       ATR% médio histórico do símbolo
            confidence:        confiança do sinal IA (0–1)
            expected_pts:      distância do SL em pontos (stop distance)
            pip_value_per_lot: valor de 1 ponto × 1 lote (USD) do contrato MT5
            sym_min_lot:       lote mínimo do símbolo (volume_min do MT5)

        Returns:
            dict com lot, fatores individuais, skip=True se cost_barrier atingida
        """
        cfg = self._cfg

        # ── Cost barrier: spread+slip+comm > expected move → não operar ──
        if expected_pts > 0 and expected_pts < cfg.cost_barrier_pts:
            reason = f"expected={expected_pts:.1f}pts < cost_barrier={cfg.cost_barrier_pts:.1f}pts"
            log.info("[LotCalcV2] COST_BARRIER %s", reason)
            return {"lot": 0.0, "skip": True, "skip_reason": reason}

        # ── Base lot: risco% equity ÷ SL valor USD ─────────────────────
        risk_usd  = equity * cfg.risk_pct
        sl_usd    = max(expected_pts * pip_value_per_lot, 1e-6)
        base_lot  = risk_usd / sl_usd

        # ── 4 fatores de ajuste ────────────────────────────────────────
        vol_f  = self._vol_factor(atr_pct, atr_avg_pct)
        conf_f = self._conf_factor(confidence)
        perf_f = self._perf_factor()
        kelly_f = self._kelly_factor(confidence) if cfg.use_kelly else 1.0

        raw_lot = base_lot * vol_f * conf_f * perf_f * kelly_f

        # ── Limites CQO: min=0.05, max=0.25 ───────────────────────────
        eff_min = max(cfg.min_lot, sym_min_lot)
        lot = float(max(eff_min, min(cfg.max_lot, round(raw_lot, 2))))

        log.info("[LotCalcV2] lot=%.2f base=%.4f vol_f=%.2f conf_f=%.2f perf_f=%.2f kelly_f=%.2f | risk=$%.2f",
                 lot, base_lot, vol_f, conf_f, perf_f, kelly_f, risk_usd)

        return {
            "lot":        lot,
            "base_lot":   round(base_lot, 4),
            "vol_f":      round(vol_f,    3),
            "conf_f":     round(conf_f,   3),
            "perf_f":     round(perf_f,   3),
            "kelly_f":    round(kelly_f,  3),
            "risk_usd":   round(risk_usd, 2),
            "skip":       False,
            "skip_reason": "",
        }

    def update_performance(self, pnl: float) -> None:
        """Alimenta o fator de desempenho após fechamento de posição."""
        self._perf.append(1.0 if pnl > 0 else -1.0)
        if len(self._perf) > self._cfg.perf_window:
            self._perf.pop(0)

    def update_atr(self, symbol: str, atr_pct: float) -> float:
        """Registra ATR% e devolve média histórica do símbolo."""
        hist = self._atr_hist.setdefault(symbol, [])
        hist.append(atr_pct)
        if len(hist) > 50:
            hist.pop(0)
        return float(sum(hist) / len(hist)) if hist else (atr_pct or self._cfg.atr_target_pct)

    def diagnostics(self) -> Dict:
        return {
            "perf_n":     len(self._perf),
            "perf_f":     round(self._perf_factor(), 3),
            "perf_trend": "pos" if self._perf_factor() > 1 else ("neg" if self._perf_factor() < 1 else "flat"),
            "lot_range":  f"{self._cfg.min_lot}–{self._cfg.max_lot}",
            "kelly_on":   self._cfg.use_kelly,
        }

    # ── private factors ───────────────────────────────────────────────────

    def _vol_factor(self, atr_pct: float, atr_avg_pct: float) -> float:
        """
        vol_factor = (atr_avg / atr_current)^dampening.
        Alta vol → fator < 1 (reduz lote).
        Baixa vol → fator > 1 (amplifica, pois SL em pts fica menor).
        """
        cfg = self._cfg
        if atr_pct <= 0 or atr_avg_pct <= 0:
            return 1.0
        ratio  = atr_avg_pct / atr_pct
        factor = ratio ** cfg.vol_dampening
        return float(max(0.30, min(2.0, factor)))

    def _conf_factor(self, confidence: float) -> float:
        """
        Interpolação linear: conf_low→0.50 | conf_high→1.50.
        Sinal de alta confiança amplifica lote, baixa confiança reduz.
        """
        cfg = self._cfg
        c   = float(max(0.0, min(1.0, confidence)))
        if c <= cfg.conf_low:
            return 0.50
        if c >= cfg.conf_high:
            return 1.50
        t = (c - cfg.conf_low) / max(cfg.conf_high - cfg.conf_low, 1e-9)
        return round(0.50 + t * 1.0, 4)

    def _perf_factor(self) -> float:
        """
        ±15% por trade recente. Win streak → amplifica. Loss streak → reduz.
        """
        cfg = self._cfg
        if not self._perf:
            return 1.0
        recent = self._perf[-cfg.perf_window:]
        avg    = sum(recent) / len(recent)
        factor = 1.0 + avg * 0.15
        return float(max(cfg.perf_reduce_min, min(cfg.perf_boost_max, factor)))

    def _kelly_factor(self, confidence: float) -> float:
        """Quarter-Kelly desativado por padrão (use_kelly=False)."""
        cfg = self._cfg
        if confidence <= 0 or confidence >= 1:
            return 1.0
        odds   = confidence / max(1.0 - confidence, 1e-9)
        kelly  = (confidence * odds - (1.0 - confidence)) / max(odds, 1e-9)
        kelly  = max(0.0, min(0.5, kelly)) * cfg.kelly_cap * 4
        return float(max(0.5, min(2.0, 1.0 + (kelly - 0.25) * 2)))
