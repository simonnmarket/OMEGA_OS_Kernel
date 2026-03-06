"""
modules/risk_metrics.py — Módulo de Métricas de Risco Institucional
OMEGA OS Kernel — Módulo Expansivo v1.0.0
2026-03-06

════════════════════════════════════════════════════════════════════════════════
ORIGEM: Convertido e expandido a partir de Genesis/Risk/RiskMetrics.mqh
        (Genesis Project — MQL5 → Python Tier-0)

FILOSOFIA DO MÓDULO:
  Este módulo é AUTÓNOMO e EXPANSÍVEL.
  Não depende de nenhum outro módulo do OMEGA além de numpy/pandas.
  Para adicionar novas métricas: criar nova subclasse de BaseRiskMetric
  ou adicionar métodos ao RiskMetricsEngine.

MÉTRICAS DISPONÍVEIS:
  ① VaR Histórico                 (percentil empírico dos retornos)
  ② VaR Paramétrico               (normal com z-score)
  ③ VaR Monte Carlo               (simulação com 10.000 paths)
  ④ VaR GARCH                     (volatilidade condicional GARCH(1,1))
  ⑤ VaR Híbrido                   (média ponderada dos acima)
  ⑥ CVaR / Expected Shortfall     (média do tail além do VaR)
  ⑦ MaxDrawdown                   (queda máxima de pico a vale)
  ⑧ Volatilidade Anualizada       (desvio padrão de log-returns × √252)
  ⑨ Sharpe Ratio                  (retorno excesso / volatilidade)
  ⑩ Calmar Ratio                  (CAGR / MaxDrawdown)

COMO EXPANDIR:
  • Para adicionar novo método VaR: adicionar case em VaRMethod e implementar
    método privado _calculate_<nome>_var()
  • Para adicionar nova métrica: adicionar método público ao RiskMetricsEngine
  • Para modificar thresholds de risco: ajustar RiskConfig
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("OMEGA.Modules.RiskMetrics")

warnings.filterwarnings("ignore", category=RuntimeWarning)


# ─────────────────────────────────────────────────────────────────────────────
#  ENUMS E CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

class VaRMethod(str, Enum):
    HISTORICAL  = "historical"   # ① percentil empírico
    PARAMETRIC  = "parametric"   # ② normal (z-score)
    MONTECARLO  = "montecarlo"   # ③ simulação
    GARCH       = "garch"        # ④ volatilidade condicional GARCH(1,1)
    HYBRID      = "hybrid"       # ⑤ média ponderada


class RiskLevel(str, Enum):
    LOW      = "LOW"      # VaR < 1% | DD < 5%
    MODERATE = "MODERATE" # VaR < 3% | DD < 10%
    HIGH     = "HIGH"     # VaR < 5% | DD < 15%
    CRITICAL = "CRITICAL" # VaR >= 5% ou DD >= 15%


@dataclass
class RiskConfig:
    """
    Configuração do módulo de risco.
    Modificar aqui para ajustar thresholds sem tocar na lógica.
    """
    # Nível de confiança padrão para VaR
    confidence_level     : float = 0.95   # 95%

    # Monte Carlo
    mc_simulations       : int   = 10_000 # número de simulações
    mc_horizon_days      : int   = 1      # horizonte em dias

    # GARCH(1,1) — parâmetros padrão calibrados para XAUUSD/FX
    garch_alpha          : float = 0.10   # peso do retorno ao quadrado (inovação)
    garch_beta           : float = 0.85   # peso da variância condicional anterior
    garch_omega          : float = 0.000001  # variância de longo prazo (mínimo)

    # Drawdown — janela de cálculo
    drawdown_window      : int   = 252    # 1 ano em dias de negociação

    # Volatilidade anualizada
    vol_annualize_factor : int   = 252    # 252 dias de negociação / ano

    # Thresholds de nível de risco
    var_moderate_thr     : float = 0.01   # VaR > 1% → MODERATE
    var_high_thr         : float = 0.03   # VaR > 3% → HIGH
    var_critical_thr     : float = 0.05   # VaR > 5% → CRITICAL
    dd_moderate_thr      : float = 0.05   # DD > 5%  → MODERATE
    dd_high_thr          : float = 0.10   # DD > 10% → HIGH
    dd_critical_thr      : float = 0.15   # DD > 15% → CRITICAL

    # Taxa livre de risco anual (para Sharpe)
    risk_free_rate       : float = 0.02   # 2% ao ano

    # Semente para reprodutibilidade Monte Carlo
    mc_seed              : Optional[int] = 42


# ─────────────────────────────────────────────────────────────────────────────
#  ESTRUTURAS DE RESULTADO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VaRResult:
    """Resultado completo de um cálculo de VaR."""
    method              : VaRMethod
    confidence_level    : float
    var                 : float          # Value at Risk (como fracção, ex: 0.023 = 2.3%)
    cvar                : float          # Expected Shortfall (CVaR)
    volatility_annual   : float          # volatilidade anualizada
    max_drawdown        : float          # drawdown máximo no período
    sharpe              : float          # Sharpe Ratio
    calmar              : float          # Calmar Ratio
    sample_size         : int            # número de retornos usados
    risk_level          : RiskLevel      # classificação de risco
    valid               : bool = True
    error_msg           : str  = ""

    def to_dict(self) -> Dict:
        return {
            "method"           : self.method.value,
            "confidence"       : self.confidence_level,
            "var_pct"          : round(self.var    * 100, 4),
            "cvar_pct"         : round(self.cvar   * 100, 4),
            "volatility_pct"   : round(self.volatility_annual * 100, 4),
            "max_drawdown_pct" : round(self.max_drawdown * 100, 4),
            "sharpe"           : round(self.sharpe, 4),
            "calmar"           : round(self.calmar, 4),
            "sample_size"      : self.sample_size,
            "risk_level"       : self.risk_level.value,
            "valid"            : self.valid,
        }

    def summary(self) -> str:
        return (
            f"[{self.method.value.upper()}] "
            f"VaR={self.var*100:.2f}% | CVaR={self.cvar*100:.2f}% | "
            f"Vol={self.volatility_annual*100:.2f}% | DD={self.max_drawdown*100:.2f}% | "
            f"Sharpe={self.sharpe:.2f} | Risco={self.risk_level.value}"
        )


@dataclass
class RiskSnapshot:
    """Snapshot completo de risco — todos os métodos em paralelo."""
    historical  : Optional[VaRResult] = None
    parametric  : Optional[VaRResult] = None
    montecarlo  : Optional[VaRResult] = None
    garch       : Optional[VaRResult] = None
    hybrid      : Optional[VaRResult] = None
    consensus_var       : float      = 0.0   # média ponderada de todos os VaR
    consensus_risk_level: RiskLevel  = RiskLevel.LOW

    def to_dict(self) -> Dict:
        results = {}
        for method in ["historical", "parametric", "montecarlo", "garch", "hybrid"]:
            r = getattr(self, method)
            if r:
                results[method] = r.to_dict()
        results["consensus_var_pct"]   = round(self.consensus_var * 100, 4)
        results["consensus_risk_level"] = self.consensus_risk_level.value
        return results


# ─────────────────────────────────────────────────────────────────────────────
#  ENGINE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class RiskMetricsEngine:
    """
    Motor de métricas de risco institucional.

    Uso básico:
        engine = RiskMetricsEngine()
        returns = pd.Series([0.001, -0.002, 0.003, ...])
        result = engine.calculate_var(returns, method=VaRMethod.HYBRID)
        snapshot = engine.full_snapshot(returns)

    Expansão:
        Para adicionar novo método VaR → adicionar case em calculate_var()
        Para nova métrica → novo método público
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self._cfg    = config or RiskConfig()
        self._history: List[VaRResult] = []

    # ── Utilitários internos ──────────────────────────────────────────────

    def _validate_returns(self, returns: pd.Series) -> Tuple[bool, str]:
        if returns is None or len(returns) == 0:
            return False, "série de retornos vazia"
        if len(returns) < 30:
            return False, f"amostra insuficiente: {len(returns)} < 30"
        if returns.isna().all():
            return False, "todos os retornos são NaN"
        return True, ""

    def _clean_returns(self, returns: pd.Series) -> np.ndarray:
        arr = returns.replace([np.inf, -np.inf], np.nan).dropna().values
        return arr.astype(float)

    def _risk_level(self, var: float, dd: float) -> RiskLevel:
        cfg = self._cfg
        if var >= cfg.var_critical_thr or dd >= cfg.dd_critical_thr:
            return RiskLevel.CRITICAL
        if var >= cfg.var_high_thr or dd >= cfg.dd_high_thr:
            return RiskLevel.HIGH
        if var >= cfg.var_moderate_thr or dd >= cfg.dd_moderate_thr:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    # ── Métricas base ─────────────────────────────────────────────────────

    def max_drawdown(self, returns: pd.Series) -> float:
        """Calcula MaxDrawdown a partir de série de retornos."""
        ok, msg = self._validate_returns(returns)
        if not ok:
            return 0.0
        arr      = self._clean_returns(returns)
        cum      = np.cumprod(1 + arr)
        peak     = np.maximum.accumulate(cum)
        drawdown = (cum - peak) / np.where(peak > 0, peak, 1)
        return float(abs(np.min(drawdown)))

    def annualized_volatility(self, returns: pd.Series) -> float:
        """Volatilidade anualizada via desvio padrão de log-returns."""
        ok, msg = self._validate_returns(returns)
        if not ok:
            return 0.0
        arr = self._clean_returns(returns)
        if len(arr) < 2:
            return 0.0
        log_ret = np.diff(np.log(np.abs(arr) + 1 + 1e-10))
        return float(np.std(log_ret) * np.sqrt(self._cfg.vol_annualize_factor))

    def sharpe_ratio(self, returns: pd.Series) -> float:
        """Sharpe Ratio anualizado."""
        ok, _ = self._validate_returns(returns)
        if not ok:
            return 0.0
        arr        = self._clean_returns(returns)
        rfr_daily  = self._cfg.risk_free_rate / self._cfg.vol_annualize_factor
        excess     = arr - rfr_daily
        std        = np.std(excess)
        if std < 1e-10:
            return 0.0
        return float((np.mean(excess) / std) * np.sqrt(self._cfg.vol_annualize_factor))

    def calmar_ratio(self, returns: pd.Series) -> float:
        """Calmar Ratio = CAGR / MaxDrawdown."""
        ok, _ = self._validate_returns(returns)
        if not ok:
            return 0.0
        arr  = self._clean_returns(returns)
        n    = len(arr)
        cagr = float((np.prod(1 + arr)) ** (self._cfg.vol_annualize_factor / n) - 1)
        dd   = self.max_drawdown(returns)
        return float(cagr / dd) if dd > 1e-10 else 0.0

    def expected_shortfall(self, returns: pd.Series,
                            var_value: float,
                            confidence: float) -> float:
        """CVaR / Expected Shortfall = média dos retornos além do VaR."""
        ok, _ = self._validate_returns(returns)
        if not ok:
            return var_value * 1.2
        arr    = self._clean_returns(returns)
        cutoff = np.percentile(arr, (1 - confidence) * 100)
        tail   = arr[arr <= cutoff]
        if len(tail) == 0:
            return var_value * 1.2
        return float(abs(np.mean(tail)))

    # ── Métodos VaR ───────────────────────────────────────────────────────

    def _historical_var(self, arr: np.ndarray, confidence: float) -> float:
        """VaR Histórico — percentil empírico dos retornos."""
        pct   = (1 - confidence) * 100
        return float(abs(np.percentile(arr, pct)))

    def _parametric_var(self, arr: np.ndarray, confidence: float) -> float:
        """VaR Paramétrico — assumindo distribuição normal."""
        from scipy import stats
        mu    = np.mean(arr)
        sigma = np.std(arr)
        z     = stats.norm.ppf(1 - confidence)
        return float(abs(mu + z * sigma))

    def _montecarlo_var(self, arr: np.ndarray, confidence: float) -> float:
        """VaR Monte Carlo — simulação de retornos via GBM."""
        cfg  = self._cfg
        rng  = np.random.default_rng(cfg.mc_seed)
        mu   = np.mean(arr)
        sigma = np.std(arr)
        simulated = rng.normal(mu, sigma, cfg.mc_simulations)
        pct       = (1 - confidence) * 100
        return float(abs(np.percentile(simulated, pct)))

    def _garch_var(self, arr: np.ndarray, confidence: float) -> float:
        """
        VaR GARCH(1,1) — volatilidade condicional.
        σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}
        """
        from scipy import stats
        cfg      = self._cfg
        omega    = cfg.garch_omega
        alpha    = cfg.garch_alpha
        beta     = cfg.garch_beta

        # Inicializar variância com variância da amostra
        sigma2   = np.var(arr)
        sigma2_t = sigma2

        # Filtrar σ² ao longo do tempo
        for r in arr:
            sigma2_t = omega + alpha * (r ** 2) + beta * sigma2_t
            sigma2_t = max(sigma2_t, 1e-10)  # estabilidade numérica

        # VaR com σ condicional actualizado
        sigma_t = np.sqrt(sigma2_t)
        mu      = np.mean(arr)
        z       = stats.norm.ppf(1 - confidence)
        return float(abs(mu + z * sigma_t))

    def _hybrid_var(self, arr: np.ndarray, confidence: float) -> float:
        """
        VaR Híbrido — média ponderada de Histórico, Paramétrico e GARCH.
        Pesos: Historical=0.40, Parametric=0.30, GARCH=0.30
        (Monte Carlo excluído do híbrido por custo computacional)
        """
        w_hist  = 0.40
        w_param = 0.30
        w_garch = 0.30

        var_h = self._historical_var(arr, confidence)
        var_p = self._parametric_var(arr, confidence)
        var_g = self._garch_var(arr, confidence)

        return float(w_hist * var_h + w_param * var_p + w_garch * var_g)

    # ── Interface pública ─────────────────────────────────────────────────

    def calculate_var(self,
                      returns    : pd.Series,
                      method     : VaRMethod = VaRMethod.HYBRID,
                      confidence : Optional[float] = None) -> VaRResult:
        """
        Calcula VaR, CVaR e métricas complementares.

        Args:
            returns   : pd.Series de retornos (ex: close pct_change())
            method    : método de cálculo (default: HYBRID)
            confidence: nível de confiança (default: cfg.confidence_level)

        Returns:
            VaRResult com todas as métricas
        """
        conf = confidence or self._cfg.confidence_level

        # Validar
        ok, msg = self._validate_returns(returns)
        if not ok:
            logger.warning(f"[RiskMetrics] Cálculo bloqueado: {msg}")
            return VaRResult(
                method=method, confidence_level=conf,
                var=0.0, cvar=0.0, volatility_annual=0.0,
                max_drawdown=0.0, sharpe=0.0, calmar=0.0,
                sample_size=len(returns) if returns is not None else 0,
                risk_level=RiskLevel.LOW, valid=False, error_msg=msg
            )

        arr = self._clean_returns(returns)

        # Calcular VaR pelo método escolhido
        try:
            if method == VaRMethod.HISTORICAL:
                var_val = self._historical_var(arr, conf)
            elif method == VaRMethod.PARAMETRIC:
                var_val = self._parametric_var(arr, conf)
            elif method == VaRMethod.MONTECARLO:
                var_val = self._montecarlo_var(arr, conf)
            elif method == VaRMethod.GARCH:
                var_val = self._garch_var(arr, conf)
            elif method == VaRMethod.HYBRID:
                var_val = self._hybrid_var(arr, conf)
            else:
                var_val = self._historical_var(arr, conf)
        except Exception as e:
            logger.error(f"[RiskMetrics] Erro em {method.value}: {e} — fallback para Historical")
            var_val = self._historical_var(arr, conf)

        # Métricas complementares
        cvar   = self.expected_shortfall(returns, var_val, conf)
        vol    = self.annualized_volatility(returns)
        dd     = self.max_drawdown(returns)
        sharpe = self.sharpe_ratio(returns)
        calmar = self.calmar_ratio(returns)
        rlevel = self._risk_level(var_val, dd)

        result = VaRResult(
            method            = method,
            confidence_level  = conf,
            var               = round(var_val, 6),
            cvar              = round(cvar, 6),
            volatility_annual = round(vol, 6),
            max_drawdown      = round(dd, 6),
            sharpe            = round(sharpe, 4),
            calmar            = round(calmar, 4),
            sample_size       = len(arr),
            risk_level        = rlevel,
        )

        self._history.append(result)
        logger.info(f"[RiskMetrics] {result.summary()}")
        return result

    def full_snapshot(self,
                      returns    : pd.Series,
                      confidence : Optional[float] = None) -> RiskSnapshot:
        """
        Calcula todos os 5 métodos VaR em paralelo.
        Retorna RiskSnapshot com consenso ponderado.

        Uso: para análise completa antes de decisões de risco críticas.
        """
        conf = confidence or self._cfg.confidence_level
        snap = RiskSnapshot()

        # Calcular todos os métodos
        methods_weights = [
            (VaRMethod.HISTORICAL,  0.30),
            (VaRMethod.PARAMETRIC,  0.20),
            (VaRMethod.MONTECARLO,  0.15),
            (VaRMethod.GARCH,       0.25),
            (VaRMethod.HYBRID,      0.10),
        ]

        valid_vars : List[Tuple[float, float]] = []  # (var, weight)

        for method, weight in methods_weights:
            result = self.calculate_var(returns, method, conf)
            setattr(snap, method.value, result)
            if result.valid:
                valid_vars.append((result.var, weight))

        # Consenso ponderado
        if valid_vars:
            total_w = sum(w for _, w in valid_vars)
            snap.consensus_var = sum(v * w for v, w in valid_vars) / total_w

            # Nível de risco do consenso
            dd = self.max_drawdown(returns)
            snap.consensus_risk_level = self._risk_level(snap.consensus_var, dd)

        logger.info(
            f"[RiskMetrics] SNAPSHOT COMPLETO | "
            f"Consenso VaR={snap.consensus_var*100:.2f}% | "
            f"Risco={snap.consensus_risk_level.value}"
        )
        return snap

    def get_history(self) -> List[VaRResult]:
        """Retorna histórico de todos os cálculos realizados."""
        return list(self._history)

    def export_history_df(self) -> pd.DataFrame:
        """Exporta histórico como DataFrame para análise."""
        if not self._history:
            return pd.DataFrame()
        rows = [r.to_dict() for r in self._history]
        return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO DE CONVENIÊNCIA — carregamento rápido a partir de OHLCV
# ─────────────────────────────────────────────────────────────────────────────

def returns_from_ohlcv(df: pd.DataFrame,
                        price_col: str = "close",
                        log_returns: bool = True) -> pd.Series:
    """
    Calcula série de retornos a partir de DataFrame OHLCV.

    Args:
        df         : DataFrame com coluna de preço
        price_col  : coluna de preço (default: 'close')
        log_returns: True = log-returns | False = retornos simples

    Returns:
        pd.Series de retornos (dropna aplicado)
    """
    if price_col not in df.columns:
        raise ValueError(f"Coluna '{price_col}' não encontrada. Colunas: {list(df.columns)}")

    prices = df[price_col].replace(0, np.nan).dropna()
    if log_returns:
        rets = np.log(prices / prices.shift(1)).dropna()
    else:
        rets = prices.pct_change().dropna()

    return rets


# ─────────────────────────────────────────────────────────────────────────────
#  TESTES INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

def _run_tests() -> bool:
    print("=" * 68)
    print("  RISK METRICS MODULE v1.0 — TESTES INTERNOS")
    print("=" * 68)

    PASS = FAIL = 0

    def ok(msg):
        nonlocal PASS; PASS += 1
        print(f"  [✅ PASS] {msg}")

    def fail(msg):
        nonlocal FAIL; FAIL += 1
        print(f"  [❌ FAIL] {msg}")

    # Dados sintéticos: 500 retornos diários (1% volatilidade)
    rng     = np.random.default_rng(42)
    returns = pd.Series(rng.normal(0.0003, 0.01, 500))
    engine  = RiskMetricsEngine()

    # TESTE 1: Volatilidade anualizada
    vol = engine.annualized_volatility(returns)
    print(f"\n>>> Teste 1: Volatilidade anualizada = {vol*100:.2f}%")
    if 0.10 < vol < 0.25:
        ok(f"Vol={vol*100:.2f}% dentro do range esperado (10%-25%)")
    else:
        fail(f"Vol={vol*100:.2f}% fora do range esperado")

    # TESTE 2: VaR Histórico
    r = engine.calculate_var(returns, VaRMethod.HISTORICAL)
    print(f">>> Teste 2: VaR Histórico = {r.var*100:.3f}%")
    if r.valid and r.var > 0:
        ok(f"VaR={r.var*100:.3f}% | CVaR={r.cvar*100:.3f}%")
    else:
        fail("VaR Histórico inválido")

    # TESTE 3: VaR GARCH
    r_g = engine.calculate_var(returns, VaRMethod.GARCH)
    print(f">>> Teste 3: VaR GARCH = {r_g.var*100:.3f}%")
    if r_g.valid and r_g.var > 0:
        ok(f"VaR GARCH={r_g.var*100:.3f}%")
    else:
        fail("VaR GARCH inválido")

    # TESTE 4: VaR Híbrido
    r_h = engine.calculate_var(returns, VaRMethod.HYBRID)
    print(f">>> Teste 4: VaR Híbrido = {r_h.var*100:.3f}%")
    if r_h.valid and r_h.var > 0:
        ok(f"VaR Híbrido={r_h.var*100:.3f}% | Risco={r_h.risk_level.value}")
    else:
        fail("VaR Híbrido inválido")

    # TESTE 5: Snapshot completo
    print("\n>>> Teste 5: Snapshot completo (5 métodos)")
    snap = engine.full_snapshot(returns)
    if snap.consensus_var > 0:
        ok(f"Consenso VaR={snap.consensus_var*100:.3f}% | Risco={snap.consensus_risk_level.value}")
    else:
        fail("Consenso inválido")

    # TESTE 6: MaxDrawdown
    dd = engine.max_drawdown(returns)
    print(f">>> Teste 6: MaxDrawdown = {dd*100:.2f}%")
    if dd > 0:
        ok(f"MaxDrawdown={dd*100:.2f}%")
    else:
        fail("MaxDrawdown inválido")

    # TESTE 7: Sharpe e Calmar
    sharpe = engine.sharpe_ratio(returns)
    calmar = engine.calmar_ratio(returns)
    print(f">>> Teste 7: Sharpe={sharpe:.3f} | Calmar={calmar:.3f}")
    if isinstance(sharpe, float) and isinstance(calmar, float):
        ok(f"Sharpe={sharpe:.3f} | Calmar={calmar:.3f}")
    else:
        fail("Sharpe/Calmar inválido")

    # TESTE 8: OHLCV helper
    df_test = pd.DataFrame({
        "close": 2900 * np.cumprod(1 + rng.normal(0.0003, 0.01, 100))
    })
    rets_test = returns_from_ohlcv(df_test)
    print(f">>> Teste 8: returns_from_ohlcv → {len(rets_test)} retornos")
    if len(rets_test) == 99:
        ok(f"OHLCV helper correcto: {len(rets_test)} retornos")
    else:
        fail(f"OHLCV helper incorrecte: {len(rets_test)} retornos")

    # Resumo
    total = PASS + FAIL
    print()
    print("=" * 68)
    print(
        f"  RISK METRICS v1.0 | {PASS}/{total} TESTES APROVADOS"
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
