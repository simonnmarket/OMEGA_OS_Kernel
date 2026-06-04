"""
OMEGA — MicroEntryFilter v1.0
=============================================================
Camada de precisão de entrada: M5 → M1 confirmation

Arquitectura de decisão:
  W1→D1→H4→H1→M15  → SINAL MACRO (get_multi_tf_bias, existente)
                    → MicroEntryFilter.evaluate()
                       ├── M5: alinhamento + pullback/consolidação
                       ├── M1: momentum + 3-velas de confirmação
                       └── Entry Quality Score (0.0 → 1.0)
                    → ORDEM ENVIADA (com SL ajustado à estrutura M1)

Integração no shadow_loop.py:
  Adicionar APÓS o bloco ANTI-HEDGE (L2649) e ANTES do if _corr_ok (L2690):

    from modules.micro_entry_filter import MicroEntryFilter
    _micro = MicroEntryFilter()   # instanciar uma vez fora do loop
    ...
    _micro_result = _micro.evaluate(asset, signal_dir, tf)
    if not _micro_result["execute"]:
        log.info("[%s %s] [MICRO] SKIP — %s (quality=%.2f)",
                 asset, tf, _micro_result["reason"], _micro_result["entry_quality"])
        results.append({"asset": asset, "timeframe": tf,
                        "status": "SKIP_MICRO_ENTRY",
                        "reason": _micro_result["reason"],
                        "entry_quality": _micro_result["entry_quality"]})
        continue
    # Ajuste opcional do SL com base na estrutura M1
    if _micro_result["sl_adj_pts"] > 0:
        log.info("[%s %s] [MICRO] SL ajustado +%.0f pts (estrutura M1)",
                 asset, tf, _micro_result["sl_adj_pts"])
    # _micro_result["entry_quality"] pode ser usado para escalar lot (opcional)

Referências:
  CEO Order 2026-05-12: "M5→M1/M3 micro execution precision layer"
  Fundamento: entrada ao nível M1 reduz slippage vs M15, melhora R:R real
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Literal

log = logging.getLogger("omega.micro_entry")


# ---------------------------------------------------------------------------
# Configuração (override via variáveis de ambiente no shadow_loop se necessário)
# ---------------------------------------------------------------------------
_CFG = {
    # M5 — alinhamento mínimo (EMA8 vs EMA21 na direcção certa)
    "M5_REQUIRED":          True,    # False = desactiva camada M5 (modo bypass)
    "M5_BARS":              60,      # barras M5 a carregar
    "M5_MAX_OVEREXTENSION": 1.8,     # ATR_M5 × este factor = zona "overextended" (skip)
    "M5_PULLBACK_ZONE":     0.6,     # distância máx ao EMA8_M5 em ATR_M5 para "bom entry"

    # M1 — confirmação de momentum (CEO 2026-05-12: M1 é gate obrigatório)
    "M1_REQUIRED":          True,    # NUNCA desactivar — regra CEO
    "M1_BARS":              30,      # barras M1 a carregar
    "M1_CONFIRM_CANDLES":   3,       # mínimo 3 velas M1 na direcção (era 2)
    "M1_MIN_BODY_RATIO":    0.40,    # corpo mínimo 40% (era 35%) — filtra dojis mais agressivo

    # Entry quality — limiares apertados para M1 gate
    "MIN_QUALITY_EXECUTE":  0.50,    # era 0.40 — exige qualidade mínima mais alta
    "MIN_QUALITY_FULL_LOT": 0.72,    # era 0.65 — lot completo só com confirmação forte

    # Timeframes secundários de execução (para cada signal_tf, que TF micro usar)
    "MICRO_TF_MAP": {
        "H4":  ("M5",  "M1"),   # sinal H4  → confirmar M5 + M1
        "H1":  ("M5",  "M1"),   # sinal H1  → confirmar M5 + M1
        "M15": ("M5",  "M1"),   # sinal M15 → confirmar M5 + M1
        "M5":  (None,  "M1"),   # sinal M5  → confirmar só M1
    },
}


# ---------------------------------------------------------------------------
# Resultado do filtro
# ---------------------------------------------------------------------------
@dataclass
class MicroEntryResult:
    execute:        bool  = False
    entry_quality:  float = 0.0         # 0.0 → 1.0
    lot_multiplier: float = 1.0         # 1.0 = lot completo, 0.5 = metade
    sl_adj_pts:     float = 0.0         # ajuste ao SL sugerido (positivo = alargar)
    reason:         str   = ""
    detail:         dict  = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Utilitários de cálculo
# ---------------------------------------------------------------------------

def _ema(values: list[float], period: int) -> float:
    """EMA simples (última barra)."""
    if len(values) < period:
        return float("nan")
    k = 2.0 / (period + 1)
    val = sum(values[:period]) / period
    for v in values[period:]:
        val = v * k + val * (1 - k)
    return val


def _atr_simple(highs: list[float], lows: list[float],
                closes: list[float], period: int = 14) -> float:
    """ATR simples (sem pandas)."""
    if len(highs) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    trs = trs[-period:]
    return sum(trs) / len(trs) if trs else 0.0


def _candles_in_direction(opens: list[float], closes: list[float],
                          direction: str, n: int = 3) -> int:
    """Conta quantas das últimas n velas fecharam na direcção correcta."""
    count = 0
    for i in range(-min(n, len(opens)), 0):
        if direction == "BUY"  and closes[i] > opens[i]:
            count += 1
        elif direction == "SELL" and closes[i] < opens[i]:
            count += 1
    return count


def _body_ratio(open_: float, close_: float,
                high: float, low: float) -> float:
    """Rácio corpo/range — 1.0 = vela perfeita, 0.0 = doji."""
    rng = high - low
    if rng <= 0:
        return 0.0
    return abs(close_ - open_) / rng


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class MicroEntryFilter:
    """
    Filtro de precisão de entrada M5 → M1.

    Uso:
        _micro = MicroEntryFilter()   # instanciar UMA VEZ fora do loop
        result = _micro.evaluate("EURUSD", "BUY", "H1")
        if result.execute:
            # enviar ordem
    """

    def __init__(self, cfg: dict | None = None):
        self._cfg = {**_CFG, **(cfg or {})}

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------

    def evaluate(
        self,
        symbol:     str,
        direction:  Literal["BUY", "SELL"],
        signal_tf:  str = "H1",
    ) -> MicroEntryResult:
        """
        Avalia se o momento de entrada é favorável nos TFs micro.

        Returns:
            MicroEntryResult com execute=True/False e métricas de qualidade.
        """
        try:
            import MetaTrader5 as mt5
        except ImportError:
            log.warning("[MICRO] MetaTrader5 não disponível — bypass activado")
            return MicroEntryResult(execute=True, entry_quality=0.5,
                                    reason="MT5_UNAVAILABLE_BYPASS")

        cfg        = self._cfg
        micro_tfs  = cfg["MICRO_TF_MAP"].get(signal_tf.upper(), ("M5", "M1"))
        tf_medium  = micro_tfs[0]   # "M5" ou None
        tf_micro   = micro_tfs[1]   # "M1"
        detail     = {}
        scores: list[float] = []

        # ── Camada M5 ────────────────────────────────────────────────
        if tf_medium and cfg["M5_REQUIRED"]:
            m5_score, m5_detail, m5_skip_reason = self._eval_m5(
                mt5, symbol, direction
            )
            detail["M5"] = m5_detail
            if m5_skip_reason:
                return MicroEntryResult(
                    execute=False,
                    entry_quality=m5_score,
                    reason=f"M5_BLOCK:{m5_skip_reason}",
                    detail=detail,
                )
            scores.append(m5_score)
            log.debug("[%s] [MICRO-M5] dir=%s score=%.2f %s",
                      symbol, direction, m5_score, m5_detail)

        # ── Camada M1 ────────────────────────────────────────────────
        if tf_micro and cfg["M1_REQUIRED"]:
            m1_score, m1_detail, m1_skip_reason = self._eval_m1(
                mt5, symbol, direction
            )
            detail["M1"] = m1_detail
            if m1_skip_reason:
                return MicroEntryResult(
                    execute=False,
                    entry_quality=m1_score,
                    reason=f"M1_BLOCK:{m1_skip_reason}",
                    detail=detail,
                )
            scores.append(m1_score)
            log.debug("[%s] [MICRO-M1] dir=%s score=%.2f %s",
                      symbol, direction, m1_score, m1_detail)

        # ── Quality Score composto ────────────────────────────────────
        if not scores:
            return MicroEntryResult(
                execute=True, entry_quality=0.6,
                reason="MICRO_BYPASS_NO_DATA", detail=detail,
            )

        quality   = sum(scores) / len(scores)
        min_exec  = cfg["MIN_QUALITY_EXECUTE"]
        min_full  = cfg["MIN_QUALITY_FULL_LOT"]

        if quality < min_exec:
            return MicroEntryResult(
                execute=False,
                entry_quality=round(quality, 3),
                reason=f"LOW_QUALITY:{quality:.2f}<{min_exec}",
                detail=detail,
            )

        lot_mult = 1.0 if quality >= min_full else round(quality / min_full, 2)

        # SL ajustado: se qualidade alta (>0.75) E M1 mostra estrutura clara,
        # podemos apertar o SL em 10% (melhorando R:R)
        sl_adj = 0.0
        if quality >= 0.75 and detail.get("M1", {}).get("atr_m1", 0) > 0:
            sl_adj = round(-detail["M1"]["atr_m1"] * 0.3, 1)  # apertar 0.3×ATR_M1

        return MicroEntryResult(
            execute=True,
            entry_quality=round(quality, 3),
            lot_multiplier=lot_mult,
            sl_adj_pts=sl_adj,
            reason=f"OK quality={quality:.2f}",
            detail=detail,
        )

    # ------------------------------------------------------------------
    # Avaliação M5
    # ------------------------------------------------------------------

    def _eval_m5(self, mt5, symbol: str, direction: str):
        """
        Critérios M5:
          1. EMA8 > EMA21 para BUY (ou <  para SELL)
          2. Preço actual perto do EMA8 (não overextended)
          3. ATR M5 dentro da banda normal (sem spike em curso)
        """
        cfg  = self._cfg
        bars = cfg["M5_BARS"]

        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, bars)
        except Exception as e:
            return 0.5, {"error": str(e)}, None   # bypass se MT5 falhar

        if rates is None or len(rates) < 25:
            return 0.5, {"bars": 0}, None          # dados insuficientes → bypass

        closes = [float(r["close"]) for r in rates]
        highs  = [float(r["high"])  for r in rates]
        lows   = [float(r["low"])   for r in rates]
        opens  = [float(r["open"])  for r in rates]

        ema8  = _ema(closes, 8)
        ema21 = _ema(closes, 21)
        atr   = _atr_simple(highs, lows, closes, 14)
        price = closes[-1]

        if atr <= 0:
            return 0.5, {"atr_m5": 0}, None

        # 1. Direcção EMA8/EMA21
        dir_ok = (ema8 > ema21) if direction == "BUY" else (ema8 < ema21)

        # 2. Overextension: distância do preço ao EMA8
        dist_to_ema8 = abs(price - ema8) / atr
        overextended = dist_to_ema8 > cfg["M5_MAX_OVEREXTENSION"]

        # 3. Pullback zone: idealmente price está perto do EMA8
        in_pullback_zone = dist_to_ema8 <= cfg["M5_PULLBACK_ZONE"]

        # 4. Velas M5 na direcção
        m5_candles_ok = _candles_in_direction(opens, closes, direction, n=2)

        # Compor score M5
        score = 0.0
        score += 0.40 if dir_ok          else 0.0
        score += 0.25 if in_pullback_zone else (0.10 if not overextended else 0.0)
        score += 0.20 if m5_candles_ok >= 1 else 0.0
        score += 0.15 if not overextended else 0.0

        d = {
            "ema8": round(ema8, 5), "ema21": round(ema21, 5),
            "atr_m5": round(atr, 5), "price": round(price, 5),
            "dist_to_ema8_atr": round(dist_to_ema8, 2),
            "dir_ok": dir_ok, "overextended": overextended,
            "in_pullback_zone": in_pullback_zone,
            "candles_ok": m5_candles_ok,
        }

        # Bloquear apenas se direcção M5 contradiz E overextended na direcção contrária
        if not dir_ok and overextended:
            return round(score, 3), d, "DIR_CONTRA_OVEREXTENDED"

        return round(score, 3), d, None

    # ------------------------------------------------------------------
    # Avaliação M1
    # ------------------------------------------------------------------

    def _eval_m1(self, mt5, symbol: str, direction: str):
        """
        Critérios M1:
          1. Últimas N velas M1 fecharam na direcção correcta (momentum)
          2. Corpo das velas > MIN_BODY_RATIO (confirma decisão, sem dojis)
          3. Vela actual não é spike (ATR dentro da normal)
        """
        cfg  = self._cfg
        bars = cfg["M1_BARS"]
        n    = cfg["M1_CONFIRM_CANDLES"]

        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, bars)
        except Exception as e:
            return 0.5, {"error": str(e)}, None

        if rates is None or len(rates) < n + 5:
            return 0.5, {"bars": 0}, None

        closes = [float(r["close"]) for r in rates]
        opens  = [float(r["open"])  for r in rates]
        highs  = [float(r["high"])  for r in rates]
        lows   = [float(r["low"])   for r in rates]

        atr = _atr_simple(highs, lows, closes, 14)
        if atr <= 0:
            return 0.5, {"atr_m1": 0}, None

        # 1. Contar velas na direcção
        confirmed = _candles_in_direction(opens, closes, direction, n=n)

        # 2. Qualidade das velas (corpo médio das últimas 3)
        avg_body = 0.0
        for i in range(-min(3, len(opens)), 0):
            avg_body += _body_ratio(opens[i], closes[i], highs[i], lows[i])
        avg_body /= min(3, len(opens))

        body_ok = avg_body >= cfg["M1_MIN_BODY_RATIO"]

        # 3. Spike check: ATR actual vs médio
        atr_last3  = _atr_simple(highs[-5:], lows[-5:], closes[-5:], 3)
        spike_mult = (atr_last3 / atr) if atr > 0 else 1.0
        spike_ok   = spike_mult < 2.5   # rejeitar se ATR_last3 > 2.5×ATR_normal

        # 4. EMA M1 na direcção
        ema8_m1  = _ema(closes, 8)
        ema21_m1 = _ema(closes, 21)
        dir_ok_m1 = (ema8_m1 > ema21_m1) if direction == "BUY" else (ema8_m1 < ema21_m1)

        # Compor score M1
        score = 0.0
        score += 0.35 * (confirmed / max(n, 1))
        score += 0.25 if body_ok  else 0.0
        score += 0.20 if spike_ok else 0.0
        score += 0.20 if dir_ok_m1 else 0.0

        d = {
            "confirmed_candles": confirmed,
            "required_candles": n,
            "avg_body_ratio": round(avg_body, 3),
            "body_ok": body_ok,
            "spike_mult": round(spike_mult, 2),
            "spike_ok": spike_ok,
            "atr_m1": round(atr, 5),
            "ema8_m1": round(ema8_m1, 5),
            "ema21_m1": round(ema21_m1, 5),
            "dir_ok_m1": dir_ok_m1,
        }

        # Bloquear se spike violento OU confirmacao M1 insuficiente
        if not spike_ok:
            return round(score, 3), d, "SPIKE_DETECTED"
        # CEO 2026-05-12: exige pelo menos 2 de N velas confirmadas (era: apenas 0)
        # Demo: OMEGA_M1_MIN_CONFIRMED=1 relaxa gate (default: n-1, ex. 2/3)
        # Fix Bug2 2026-06-04: OMEGA_M1_MIN_CONFIRMED=0 → bypass candle-count gate (paper mode)
        _m1_min_env = os.getenv("OMEGA_M1_MIN_CONFIRMED", "").strip()
        if _m1_min_env and int(_m1_min_env) == 0:
            min_confirmed = 0   # bypass explícito — paper/demo sem M1 candles reais
        elif _m1_min_env:
            min_confirmed = max(1, min(int(_m1_min_env), n))
        else:
            min_confirmed = max(1, n - 1)   # 3 requeridas → aceita 2; 2 requeridas → aceita 1
        if confirmed < min_confirmed:
            return round(score, 3), d, f"INSUF_M1_CANDLES:{confirmed}/{n}"

        return round(score, 3), d, None


# ---------------------------------------------------------------------------
# Actualização do get_multi_tf_bias — adicionar M5 à cascata
# ---------------------------------------------------------------------------
# Para actualizar o get_multi_tf_bias em shadow_loop.py (L1454):
# Substituir a lista TFS por:
#
#   TFS = [
#       (mt5.TIMEFRAME_W1,  "W1",  30, 3),
#       (mt5.TIMEFRAME_D1,  "D1",  50, 2),
#       (mt5.TIMEFRAME_H4,  "H4",  50, 2),
#       (mt5.TIMEFRAME_H1,  "H1",  50, 1),
#       (mt5.TIMEFRAME_M15, "M15", 50, 1),
#       (mt5.TIMEFRAME_M5,  "M5",  50, 1),   # ← ADICIONAR (total_weight passa de 9 → 10)
#   ]
#
# Isto adiciona M5 ao MTF cascade. Peso=1 (mesmo que M15).
# Total weight: 10 (era 9). Não altera a lógica — só adiciona granularidade.

# ---------------------------------------------------------------------------
# Testes rápidos (executar directamente: python modules/micro_entry_filter.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import MetaTrader5 as mt5
    mt5.initialize()

    filt = MicroEntryFilter()

    test_cases = [
        ("EURUSD", "BUY",  "H1"),
        ("EURUSD", "SELL", "H1"),
        ("BTCUSD", "BUY",  "M15"),
        ("XAUUSD", "SELL", "H1"),
        ("AUDJPY", "SELL", "H1"),
        ("EURJPY", "SELL", "H1"),
    ]

    print("\n" + "="*65)
    print("  OMEGA MicroEntryFilter v1.0 — Teste")
    print("="*65)
    for sym, d, tf in test_cases:
        r = filt.evaluate(sym, d, tf)
        exec_str = "✅ EXECUTE" if r.execute else "❌ SKIP   "
        lot_str  = f"lot×{r.lot_multiplier:.2f}" if r.execute else ""
        sl_str   = f"sl_adj={r.sl_adj_pts:+.1f}" if r.sl_adj_pts != 0 else ""
        print(f"  {exec_str} | {sym:8s} {d:4s} {tf:4s} | "
              f"quality={r.entry_quality:.2f} | {r.reason[:35]:35s} | {lot_str} {sl_str}")
        if r.detail:
            if "M5" in r.detail:
                m5 = r.detail["M5"]
                print(f"           M5: dir={m5.get('dir_ok')}, "
                      f"pullback={m5.get('in_pullback_zone')}, "
                      f"overext={m5.get('overextended')}, "
                      f"candles={m5.get('candles_ok')}")
            if "M1" in r.detail:
                m1 = r.detail["M1"]
                print(f"           M1: confirmed={m1.get('confirmed_candles')}/{m1.get('required_candles')}, "
                      f"body={m1.get('avg_body_ratio'):.2f}, "
                      f"spike={not m1.get('spike_ok')}, "
                      f"dir={m1.get('dir_ok_m1')}")
    print("="*65)
    mt5.shutdown()
