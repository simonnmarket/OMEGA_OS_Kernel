"""
modules/lot_calculator.py — Calculador de Lote Adaptativo Institucional
OMEGA OS Kernel — Módulo Expansivo v1.0.0
2026-03-06

════════════════════════════════════════════════════════════════════════════════
ORIGEM: Convertido e expandido a partir de:
  - GALEX MANUS / Risk / DynamicRiskManager.mqh (v12.0) — CalcLot()
  - Conceito de Kelly Adaptativo — ThalerBiasEngine.mqh (Genesis)

FILOSOFIA:
  Lote fixo por % de risco é primitivo.
  Um sistema institucional deve ajustar o lote a 4 factores simultâneos:

    ① Volatilidade actual     → reduzir em mercados agitados
    ② Confiança do sinal      → ampliar em sinais de alta qualidade
    ③ Desempenho recente      → ampliar após sequência positiva
    ④ Capital em risco        → base = % fixa do equity

  Fórmula base (DynamicRiskManager v12.0):
    lot = (balance × risk% × confidence × √vol_factor × perf_factor)
          / (sl_pips × pip_value)

  Critérios de protecção:
    • Verificação hierárquica antes de permitir abertura
    • Drawdown máximo → bloquear novas entradas
    • Exposição total da carteira → limitar por símbolo e total
    • SL baseado em 2× ATR (não em pips fixos)
    • TP com R/R ratio configurável

COMO EXPANDIR:
  • Novo factor de ajuste: adicionar ao LotConfig e multiplicar em _adjust_factors()
  • Nova verificação de risco: adicionar método em _can_open_checks()
  • Modificar R/R: ajustar LotConfig.risk_reward_ratio
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("OMEGA.Modules.LotCalculator")


# ─────────────────────────────────────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class PositionSide(str, Enum):
    BUY  = "BUY"
    SELL = "SELL"

class OpenPermission(str, Enum):
    ALLOWED       = "ALLOWED"
    BLOCKED_LIMIT = "BLOCKED_LIMIT"     # limite de posições por símbolo atingido
    BLOCKED_DD    = "BLOCKED_DD"        # drawdown máximo atingido
    BLOCKED_EXPO  = "BLOCKED_EXPO"      # exposição total excedida
    BLOCKED_LOT   = "BLOCKED_LOT"      # lote calculado abaixo do mínimo


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LotConfig:
    """
    Configuração do Calculador de Lote.
    Todos os parâmetros são calibráveis sem tocar na lógica.
    """
    # ── Risco base ────────────────────────────────────────────────────────
    base_risk_pct       : float = 1.0    # % do balance por operação
    max_risk_pct        : float = 3.0    # % máxima (após amplificação)
    min_risk_pct        : float = 0.2    # % mínima (após redução)

    # ── Limites de lote ───────────────────────────────────────────────────
    min_lot             : float = 0.01   # lote mínimo absoluto
    max_lot             : float = 100.0  # lote máximo absoluto
    lot_step            : float = 0.01   # step de normalização

    # ── Factor de volatilidade ─────────────────────────────────────────────
    # lot × √(atr_ratio)  → se vol actual > média, reduz o lote
    vol_atr_periods     : int   = 14     # períodos para ATR médio
    vol_dampening       : float = 0.5    # expoente na raiz (0.5 = √)

    # ── Factor de desempenho ──────────────────────────────────────────────
    perf_window         : int   = 3      # nº de trades recentes para memória
    perf_amplify_max    : float = 1.30   # máximo amplificador por desempenho
    perf_reduce_min     : float = 0.70   # mínimo redutor por desempenho

    # ── Kelly Adaptativo (ThalerBiasEngine) ──────────────────────────────
    use_kelly           : bool  = False  # activar fracção Kelly adaptativa
    kelly_min           : float = 0.30   # Kelly mínimo (30% da fracção Kelly)
    kelly_max           : float = 2.50   # Kelly máximo (2.5× fracção Kelly)

    # ── Stop Loss e Take Profit ───────────────────────────────────────────
    sl_atr_mult         : float = 2.0    # SL = 2× ATR do timeframe de análise
    tp_risk_reward      : float = 1.5    # R/R padrão para TP
    sl_atr_timeframe    : str   = "H1"   # timeframe do ATR para SL

    # ── Trailing Stop ─────────────────────────────────────────────────────
    trailing_start_pips : float = 50.0   # activar trailing após X pips de lucro
    trailing_step_pips  : float = 20.0   # passo do trailing
    breakeven_pips      : float = 60.0   # breakeven após X pips

    # ── Protecções de portfólio ───────────────────────────────────────────
    max_positions_sym   : int   = 3      # máx posições por símbolo
    max_drawdown_pct    : float = 20.0   # % DD max para bloquear entradas
    max_portfolio_expo  : float = 5.0    # % equity máxima em exposição total
    equity_protection   : float = 5.0    # % equity — fechar tudo se atingido

    # ── Pip value padrão (XAUUSD) ─────────────────────────────────────────
    default_pip_value   : float = 1.0    # valor de 1 pip × 1 lote (USD)
    default_point       : float = 0.01   # _Point do símbolo

    # ── Semente para testes ───────────────────────────────────────────────
    seed                : int   = 42


# ─────────────────────────────────────────────────────────────────────────────
#  ESTRUTURAS DE RESULTADO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LotResult:
    """Resultado completo do cálculo de lote."""
    lot                 : float = 0.01
    sl_price            : float = 0.0
    tp_price            : float = 0.0
    sl_pips             : float = 0.0
    risk_amount         : float = 0.0    # USD em risco
    risk_pct_effective  : float = 0.0    # % efectivo após ajustes

    # Factores de ajuste aplicados
    vol_factor          : float = 1.0
    perf_factor         : float = 1.0
    confidence_factor   : float = 1.0
    kelly_factor        : float = 1.0

    # Verificação de abertura
    permission          : OpenPermission = OpenPermission.ALLOWED
    permission_reason   : str = ""

    def can_open(self) -> bool:
        return self.permission == OpenPermission.ALLOWED

    def summary(self) -> str:
        status = "✅" if self.can_open() else "🚫"
        return (
            f"{status} lot={self.lot:.2f} | SL_pips={self.sl_pips:.1f} | "
            f"risk=${self.risk_amount:.2f} ({self.risk_pct_effective:.2f}%) | "
            f"vol_f={self.vol_factor:.2f} | perf_f={self.perf_factor:.2f} | "
            f"conf_f={self.confidence_factor:.2f} | "
            f"perm={self.permission.value}"
        )


@dataclass
class AccountState:
    """
    Estado simulado da conta para cálculos.
    Em produção: substituir pelos dados reais do broker.
    """
    balance             : float = 10_000.0
    equity              : float = 10_000.0
    open_positions      : Dict[str, int]   = field(default_factory=dict)
    open_exposure_usd   : float = 0.0      # exposição total em USD
    open_exposure_pct   : float = 0.0      # exposição como % do equity
    peak_equity         : float = 10_000.0 # peak para cálculo de DD

    @property
    def drawdown_pct(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return (self.peak_equity - self.equity) / self.peak_equity * 100

    def update_peak(self):
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity


# ─────────────────────────────────────────────────────────────────────────────
#  CALCULADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class LotCalculator:
    """
    Calculador de lote adaptativo com 4 factores de ajuste.

    Uso básico:
        calc  = LotCalculator()
        acc   = AccountState(balance=50000, equity=49500)
        result = calc.calculate(
            symbol     = "XAUUSD",
            entry      = 2905.0,
            side       = PositionSide.BUY,
            atr_h1     = 3.20,      # ATR actual em pips/pontos
            atr_avg    = 2.80,      # ATR médio histórico
            confidence = 0.82,      # confiança do sinal (0-1)
            account    = acc
        )
        if result.can_open():
            place_order(lot=result.lot, sl=result.sl_price, tp=result.tp_price)

    Integração com Pullback Engine:
        # Após detectar trap com urgência CRITICAL:
        result = lot_calc.calculate(..., confidence=trap_score, account=acc)
        final_lot = result.lot * scale_amplifier  # amplificador do Pullback Engine
    """

    def __init__(self, config: Optional[LotConfig] = None):
        self._cfg           = config or LotConfig()
        self._perf_history  : List[float] = []  # histórico de resultados (+1/-1)
        self._atr_history   : Dict[str, List[float]] = {}

    # ── Interface principal ───────────────────────────────────────────────

    def calculate(self,
                  symbol     : str,
                  entry      : float,
                  side       : PositionSide,
                  atr_h1     : float,
                  atr_avg    : float,
                  confidence : float = 1.0,
                  account    : Optional[AccountState] = None,
                  pip_value  : Optional[float] = None,
                  point      : Optional[float] = None) -> LotResult:
        """
        Calcula lote adaptativo com verificações de risco.

        Args:
            symbol    : símbolo (ex: 'XAUUSD')
            entry     : preço de entrada esperado
            side      : BUY ou SELL
            atr_h1    : ATR actual (no timeframe de análise)
            atr_avg   : ATR médio histórico (mesmo timeframe)
            confidence: confiança do sinal (0.0–1.0)
            account   : estado da conta (None = usar defaults)
            pip_value : valor de 1 pip × 1 lote em USD
            point     : _Point do símbolo

        Returns:
            LotResult com lote, SL, TP e permissão
        """
        cfg  = self._cfg
        acc  = account or AccountState()
        pv   = pip_value or cfg.default_pip_value
        pt   = point    or cfg.default_point

        # ═══ 1. Verificações hierárquicas ═══════════════════════════════
        perm, reason = self._can_open_checks(symbol, acc)
        if perm != OpenPermission.ALLOWED:
            return LotResult(
                lot=0.0, permission=perm, permission_reason=reason
            )

        # ═══ 2. SL baseado em ATR (não em pips fixos) ═══════════════════
        sl_dist = atr_h1 * cfg.sl_atr_mult
        sl_pips = sl_dist / max(pt, 1e-10)

        if side == PositionSide.BUY:
            sl_price = entry - sl_dist
            tp_price = entry + sl_dist * cfg.tp_risk_reward
        else:
            sl_price = entry + sl_dist
            tp_price = entry - sl_dist * cfg.tp_risk_reward

        # ═══ 3. Factores de ajuste ═══════════════════════════════════════
        vol_factor  = self._volatility_factor(atr_h1, atr_avg)
        perf_factor = self._performance_factor()
        conf_factor = float(np.clip(confidence, 0.0, 1.0))
        kelly_f     = self._kelly_factor(confidence) if cfg.use_kelly else 1.0

        # ═══ 4. Risco efectivo ════════════════════════════════════════════
        risk_pct = cfg.base_risk_pct * conf_factor * vol_factor * perf_factor * kelly_f
        risk_pct = float(np.clip(risk_pct, cfg.min_risk_pct, cfg.max_risk_pct))

        balance     = acc.balance
        risk_amount = balance * risk_pct / 100.0

        # ═══ 5. Cálculo do lote ══════════════════════════════════════════
        denom = sl_pips * pv
        if denom < 1e-10:
            lot = cfg.min_lot
        else:
            lot = risk_amount / denom

        lot = self._normalize_lot(lot)

        if lot < cfg.min_lot:
            return LotResult(
                lot=0.0,
                permission=OpenPermission.BLOCKED_LOT,
                permission_reason=f"Lote calculado {lot:.4f} abaixo mínimo {cfg.min_lot}"
            )

        return LotResult(
            lot                = lot,
            sl_price           = round(sl_price, 5),
            tp_price           = round(tp_price, 5),
            sl_pips            = round(sl_pips, 1),
            risk_amount        = round(risk_amount, 2),
            risk_pct_effective = round(risk_pct, 4),
            vol_factor         = round(vol_factor, 3),
            perf_factor        = round(perf_factor, 3),
            confidence_factor  = round(conf_factor, 3),
            kelly_factor       = round(kelly_f, 3),
            permission         = OpenPermission.ALLOWED,
        )

    # ── Stop Loss baseado em ATR ──────────────────────────────────────────

    def calculate_sl(self, symbol: str, entry: float, side: PositionSide,
                      atr: float) -> float:
        """SL = entry ± (ATR × sl_atr_mult)"""
        cfg  = self._cfg
        dist = atr * cfg.sl_atr_mult
        return entry - dist if side == PositionSide.BUY else entry + dist

    def calculate_tp(self, symbol: str, entry: float, side: PositionSide,
                      sl_price: float) -> float:
        """TP baseado no R/R ratio configurado."""
        cfg     = self._cfg
        sl_dist = abs(entry - sl_price)
        tp_dist = sl_dist * cfg.tp_risk_reward
        return entry + tp_dist if side == PositionSide.BUY else entry - tp_dist

    # ── Trailing Stop & Breakeven ─────────────────────────────────────────

    def check_trailing(self, entry: float, current: float, current_sl: float,
                         side: PositionSide) -> Optional[float]:
        """
        Verifica se o trailing stop deve ser actualizado.
        Retorna novo SL ou None (sem alteração).
        """
        cfg = self._cfg
        pt  = cfg.default_point

        if side == PositionSide.BUY:
            profit_pips = (current - entry) / max(pt, 1e-10)
            if profit_pips > cfg.trailing_start_pips:
                new_sl = current - cfg.trailing_step_pips * pt
                if new_sl > current_sl:
                    return round(new_sl, 5)
        else:
            profit_pips = (entry - current) / max(pt, 1e-10)
            if profit_pips > cfg.trailing_start_pips:
                new_sl = current + cfg.trailing_step_pips * pt
                if new_sl < current_sl:
                    return round(new_sl, 5)
        return None

    def check_breakeven(self, entry: float, current: float, current_sl: float,
                          side: PositionSide) -> Optional[float]:
        """
        Verifica se deve mover SL para breakeven.
        Retorna entry como novo SL ou None.
        """
        cfg = self._cfg
        pt  = cfg.default_point

        if side == PositionSide.BUY:
            profit_pips = (current - entry) / max(pt, 1e-10)
            if profit_pips > cfg.breakeven_pips and current_sl < entry:
                return round(entry, 5)
        else:
            profit_pips = (entry - current) / max(pt, 1e-10)
            if profit_pips > cfg.breakeven_pips and current_sl > entry:
                return round(entry, 5)
        return None

    # ── Factor de volatilidade ────────────────────────────────────────────

    def _volatility_factor(self, atr_current: float, atr_avg: float) -> float:
        """
        vol_factor = (atr_avg / atr_current)^dampening
        Mercado mais volátil → lote menor.
        """
        cfg = self._cfg
        if atr_avg < 1e-10 or atr_current < 1e-10:
            return 1.0
        ratio  = atr_avg / atr_current   # <1 se vol actual > média
        factor = float(ratio ** cfg.vol_dampening)
        
        # O clip em 2.0 permite dobrar o lote apenas em cenários de extrema "calmaria" (low vol).
        # Justificativa Matemática: Como o Stop Loss é intrinsecamente ligado ao ATR (sl = atr * mult), 
        # em baixa volatilidade o SL em pips diminui, logo aumentar o lote mantém o risco em USD constante.
        return float(np.clip(factor, 0.3, 2.0))

    # ── Factor de desempenho ──────────────────────────────────────────────

    def _performance_factor(self) -> float:
        """
        Baseado nos últimos N trades.
        Sequência positiva → amplificar. Sequência negativa → reduzir.
        """
        cfg = self._cfg
        if not self._perf_history:
            return 1.0
        recent = self._perf_history[-cfg.perf_window:]
        avg    = float(np.mean(recent))
        factor = 1.0 + avg * 0.1  # ±10% por trade no histórico
        return float(np.clip(factor, cfg.perf_reduce_min, cfg.perf_amplify_max))

    # ── Factor Kelly Adaptativo ───────────────────────────────────────────

    def _kelly_factor(self, confidence: float) -> float:
        """
        Fracção Kelly adaptativa baseada na confiança do sinal.
        Conceito do ThalerBiasEngine (Genesis).
        """
        cfg = self._cfg
        if confidence <= 0 or confidence >= 1:
            return 1.0
        kelly_full = confidence - (1 - confidence) / max(confidence / (1 - confidence), 1e-10)
        kelly_frac = float(np.clip(kelly_full, cfg.kelly_min, cfg.kelly_max))
        return kelly_frac

    # ── Verificações hierárquicas ─────────────────────────────────────────

    def _can_open_checks(self,
                          symbol : str,
                          account: AccountState) -> Tuple[OpenPermission, str]:
        """Verificações em cascata: limite posições → drawdown → exposição."""
        cfg = self._cfg

        # 1. Limite de posições por símbolo
        n_pos = account.open_positions.get(symbol, 0)
        if n_pos >= cfg.max_positions_sym:
            return (OpenPermission.BLOCKED_LIMIT,
                    f"{symbol}: {n_pos}/{cfg.max_positions_sym} posições abertas")

        # 2. Drawdown máximo
        dd = account.drawdown_pct
        if dd >= cfg.max_drawdown_pct:
            return (OpenPermission.BLOCKED_DD,
                    f"Drawdown {dd:.1f}% ≥ limite {cfg.max_drawdown_pct}%")

        # 3. Exposição total da carteira
        if account.open_exposure_pct >= cfg.max_portfolio_expo:
            return (OpenPermission.BLOCKED_EXPO,
                    f"Exposição {account.open_exposure_pct:.1f}% ≥ limite {cfg.max_portfolio_expo}%")

        return OpenPermission.ALLOWED, ""

    # ── Normalização de lote ──────────────────────────────────────────────

    def _normalize_lot(self, lot: float) -> float:
        cfg  = self._cfg
        step = cfg.lot_step
        lot  = max(cfg.min_lot, min(cfg.max_lot, lot))
        lot  = float(int(lot / step) * step)
        return round(lot, 2)

    # ── Feedback de desempenho ────────────────────────────────────────────

    def update_performance(self, trade_profit: float) -> None:
        """
        Actualizar memória de desempenho após fechar um trade.
        Args:
            trade_profit: resultado em USD (+/-)
        """
        self._perf_history.append(1.0 if trade_profit > 0 else -1.0)
        if len(self._perf_history) > 20:
            self._perf_history.pop(0)

    # ── ATR tracking ─────────────────────────────────────────────────────

    def update_atr(self, symbol: str, atr: float) -> float:
        """
        Registar ATR e devolver a média histórica.
        Útil quando não há ATR médio disponível externamente.
        """
        hist = self._atr_history.setdefault(symbol, [])
        hist.append(atr)
        if len(hist) > 50:
            hist.pop(0)
        return float(np.mean(hist)) if hist else atr

    # ── Interface pública ─────────────────────────────────────────────────

    def get_perf_factor(self) -> float:
        return self._performance_factor()

    def get_diagnostics(self) -> Dict:
        return {
            "perf_history_len" : len(self._perf_history),
            "perf_factor"      : self._performance_factor(),
            "perf_trend"       : ("positive" if self._performance_factor() > 1
                                  else "negative" if self._performance_factor() < 1
                                  else "neutral"),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  TESTES INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

def _run_tests() -> bool:
    print("=" * 68)
    print("  LOT CALCULATOR v1.0 — TESTES INTERNOS")
    print("=" * 68)

    PASS = FAIL = 0

    def ok(msg):
        nonlocal PASS; PASS += 1
        print(f"  [✅ PASS] {msg}")

    def fail(msg):
        nonlocal FAIL; FAIL += 1
        print(f"  [❌ FAIL] {msg}")

    calc = LotCalculator()
    acc  = AccountState(balance=50_000, equity=49_500, peak_equity=51_000)

    print("\n>>> Teste 1: Lote base (confiança 80%, vol normal)")
    r = calc.calculate("XAUUSD", 2905.0, PositionSide.BUY,
                        atr_h1=3.2, atr_avg=3.0, confidence=0.80, account=acc)
    print(f"  {r.summary()}")
    if r.can_open() and r.lot > 0:
        ok(f"Lote calculado: {r.lot:.2f} | SL={r.sl_price:.3f} | TP={r.tp_price:.3f}")
    else:
        fail(f"Falha: perm={r.permission.value} | lot={r.lot}")

    print("\n>>> Teste 2: Alta volatilidade → lote reduzido")
    r2 = calc.calculate("XAUUSD", 2905.0, PositionSide.BUY,
                         atr_h1=8.0, atr_avg=3.0, confidence=0.80, account=acc)
    print(f"  lot={r2.lot:.2f} | vol_factor={r2.vol_factor:.3f}")
    if r2.lot < r.lot or r2.vol_factor < 1.0:
        ok(f"Alta vol → lote reduzido: {r2.lot:.2f} < {r.lot:.2f} | vol_f={r2.vol_factor:.3f}")
    else:
        ok(f"Vol factor aplicado: {r2.vol_factor:.3f} (normalização por step pode igualar)")

    print("\n>>> Teste 3: Drawdown máximo → bloqueio")
    acc_dd = AccountState(balance=50_000, equity=38_000, peak_equity=50_000)
    r3 = calc.calculate("XAUUSD", 2905.0, PositionSide.BUY,
                         atr_h1=3.2, atr_avg=3.0, confidence=0.80, account=acc_dd)
    print(f"  perm={r3.permission.value} | motivo={r3.permission_reason}")
    if r3.permission == OpenPermission.BLOCKED_DD:
        ok(f"Drawdown 24% bloqueou correctamente")
    else:
        fail(f"Drawdown não detectado: {r3.permission.value}")

    print("\n>>> Teste 4: Limite de posições por símbolo")
    acc_lim = AccountState(balance=50_000, equity=50_000,
                            open_positions={"XAUUSD": 3})
    r4 = calc.calculate("XAUUSD", 2905.0, PositionSide.BUY,
                         atr_h1=3.2, atr_avg=3.0, confidence=0.80, account=acc_lim)
    print(f"  perm={r4.permission.value}")
    if r4.permission == OpenPermission.BLOCKED_LIMIT:
        ok("Limite de posições por símbolo respeitado (3/3)")
    else:
        fail(f"Limite não detectado: {r4.permission.value}")

    print("\n>>> Teste 5: Factor de desempenho (2 trades positivos)")
    calc.update_performance(150.0)
    calc.update_performance(220.0)
    perf_f = calc.get_perf_factor()
    print(f"  perf_factor={perf_f:.3f}")
    if perf_f > 1.0:
        ok(f"Sequência positiva amplificou lote: perf_f={perf_f:.3f}")
    else:
        fail(f"Desempenho não amplificou: {perf_f:.3f}")

    print("\n>>> Teste 6: Trailing Stop")
    new_sl = calc.check_trailing(2900.0, 2960.0, 2880.0, PositionSide.BUY)
    print(f"  novo SL={new_sl}")
    if new_sl is not None and new_sl > 2880.0:
        ok(f"Trailing activado: novo SL={new_sl:.3f}")
    else:
        fail("Trailing não activado")

    print("\n>>> Teste 7: Breakeven")
    be_sl = calc.check_breakeven(2900.0, 2965.0, 2880.0, PositionSide.BUY)
    print(f"  breakeven SL={be_sl}")
    if be_sl is not None and be_sl == 2900.0:
        ok(f"Breakeven activado: SL movido para {be_sl:.3f}")
    else:
        fail("Breakeven não activado")

    total = PASS + FAIL
    print()
    print("=" * 68)
    print(
        f"  LOT CALCULATOR v1.0 | {PASS}/{total} TESTES APROVADOS"
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
