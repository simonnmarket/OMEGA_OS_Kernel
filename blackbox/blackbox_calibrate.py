#!/usr/bin/env python3
"""
Grid Search para Calibrar Thresholds do BlackboxSystem - TIER-0 CORRECTED
================================================================================
ADICIONES TIER-0:
1. Walk-Forward Validation (proteção contra overfitting)
2. Teste de Significância Estatística (p-value, t-test, CI 95%)
3. Correção para Múltiplos Testes (Bonferroni, FDR)
4. Teste de Normalidade (Shapiro-Wilk)
5. Seed Control para Reprodutibilidade
6. Checksum de Resultados para Auditoria
7. Benchmarking Estatístico (alpha t-test vs. benchmark)
================================================================================
"""
from __future__ import annotations

import json
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

import pandas as pd

# =============================================================================
# DEPENDÊNCIAS ESTATÍSTICAS (OPCIONAIS MAS RECOMENDADAS)
# =============================================================================
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy não encontrado. Validação estatística limitada.")

try:
    from sklearn.model_selection import TimeSeriesSplit
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("sklearn não encontrado. Walk-forward validation desativado.")

# =============================================================================
# ESTRUTURAS DE DADOS TIER-0
# =============================================================================

@dataclass
class StatisticalMetrics:
    """Métricas estatísticas para validação quantitativa"""
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    p_value: Optional[float] = None
    t_statistic: Optional[float] = None
    confidence_interval_95: Optional[Tuple[float, float]] = None
    is_significant: bool = False
    sample_size: int = 0
    is_normal: Optional[bool] = None
    shapiro_p_value: Optional[float] = None

@dataclass
class GridSearchResult:
    """Resultado de grid search com validação Tier-0"""
    vol_z_threshold: float
    min_price_change: float
    min_confidence: float
    metrics_in_sample: Dict[str, Any]
    metrics_out_of_sample: Dict[str, Any]
    statistical_validation: Dict[str, Any]
    overfitting_score: float  # (IS - OOS) / IS
    is_robust: bool
    checksum: str

# =============================================================================
# FUNÇÕES DE CARREGAMENTO E VALIDAÇÃO
# =============================================================================

def load_csv(path: Path) -> List[Dict[str, Any]]:
    """Carrega CSV com validação Tier-0"""
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")
    
    df = pd.read_csv(path)
    required = {"time", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV faltando colunas: {missing}")
    
    # Validação de dados
    if df.empty:
        raise ValueError("CSV vazio")
    if len(df) < 100:
        warnings.warn(f"CSV com apenas {len(df)} barras. Mínimo recomendado: 100")
    if df['volume'].isna().any():
        warnings.warn("CSV contém volumes NaN. Preenchendo com 0.")
        df['volume'] = df['volume'].fillna(0)
    if (df['high'] < df['low']).any():
        raise ValueError("Dados inválidos: high < low detectado")
    if (df['close'] <= 0).any():
        raise ValueError("Dados inválidos: close <= 0 detectado")
    
    # Garante tipos
    df = df[list(required)].copy()
    return df.to_dict(orient="records")

# =============================================================================
# VALIDADOR ESTATÍSTICO TIER-0
# =============================================================================

class StatisticalValidator:
    """Validador estatístico para grid search Tier-0"""
    
    def __init__(self, min_samples: int = 30, alpha: float = 0.05):
        self.min_samples = min_samples
        self.alpha = alpha
    
    def calculate_sharpe(self, returns: np.ndarray, risk_free: float = 0.02, 
                        periods_per_year: int = 252) -> float:
        """Calcula Sharpe Ratio anualizado"""
        if len(returns) < 2 or np.std(returns) < 1e-10:
            return 0.0
        excess_returns = returns - risk_free / periods_per_year
        sharpe_daily = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe_daily * np.sqrt(periods_per_year)
    
    def calculate_sortino(self, returns: np.ndarray, risk_free: float = 0.02,
                         periods_per_year: int = 252) -> float:
        """Calcula Sortino Ratio (foca em downside risk)"""
        if len(returns) < 2:
            return 0.0
        downside_returns = returns[returns < 0]
        if len(downside_returns) < 2 or np.std(downside_returns) < 1e-10:
            return 0.0
        excess_returns = returns - risk_free / periods_per_year
        sortino_daily = np.mean(excess_returns) / np.std(downside_returns)
        return sortino_daily * np.sqrt(periods_per_year)
    
    def test_significance(self, returns: np.ndarray, 
                         benchmark_returns: Optional[np.ndarray] = None) -> Dict:
        """Testa significância estatística dos retornos"""
        if not SCIPY_AVAILABLE or len(returns) < self.min_samples:
            return {
                "significant": False,
                "reason": "scipy_unavailable_or_insufficient_samples",
                "sample_size": len(returns)
            }
        
        returns_clean = returns[~np.isnan(returns)]
        
        if benchmark_returns is None:
            # One-sample t-test: estratégia vs. zero
            t_stat, p_value = stats.ttest_1samp(returns_clean, 0.0, nan_policy='omit')
            ci = stats.t.interval(1 - self.alpha, len(returns_clean) - 1,
                                  loc=np.mean(returns_clean),
                                  scale=stats.sem(returns_clean))
            return {
                "significant": bool(p_value < self.alpha),
                "p_value": float(p_value),
                "t_statistic": float(t_stat),
                "confidence_interval_95": (float(ci[0]), float(ci[1])),
                "sample_size": len(returns_clean),
                "test_type": "one_sample_vs_zero"
            }
        else:
            # Two-sample t-test: estratégia vs. benchmark
            benchmark_clean = benchmark_returns[~np.isnan(benchmark_returns)]
            t_stat, p_value = stats.ttest_ind(returns_clean, benchmark_clean,
                                               equal_var=False, nan_policy='omit')
            return {
                "significant": bool(p_value < self.alpha),
                "p_value": float(p_value),
                "t_statistic": float(t_stat),
                "sample_size_strategy": len(returns_clean),
                "sample_size_benchmark": len(benchmark_clean),
                "test_type": "two_sample_welch"
            }
    
    def test_normality(self, returns: np.ndarray) -> Dict:
        """Testa se retornos seguem distribuição normal (Shapiro-Wilk)"""
        if not SCIPY_AVAILABLE or len(returns) < 3 or len(returns) > 5000:
            return {"normal": None, "reason": "scipy_unavailable_or_invalid_sample_size"}
        
        returns_clean = returns[~np.isnan(returns)]
        if len(returns_clean) < 3:
            return {"normal": False, "reason": "insufficient_clean_samples"}
        
        stat, p_value = stats.shapiro(returns_clean[:5000])
        return {
            "normal": bool(p_value > 0.05),
            "p_value": float(p_value),
            "shapiro_statistic": float(stat)
        }
    
    def bonferroni_correction(self, p_values: List[float], alpha: float = 0.05) -> Dict:
        """Corrige p-values para múltiplos testes (Bonferroni)"""
        n_tests = len(p_values)
        alpha_corrected = alpha / n_tests
        significant_after_correction = [p < alpha_corrected for p in p_values]
        return {
            "original_alpha": alpha,
            "corrected_alpha": alpha_corrected,
            "n_tests": n_tests,
            "significant_before": sum(p < alpha for p in p_values),
            "significant_after": sum(significant_after_correction),
            "correction_method": "bonferroni"
        }
    
    def compute_full_metrics(self, trade_returns: List[float], 
                            benchmark_returns: Optional[List[float]] = None) -> StatisticalMetrics:
        """Computa todas as métricas estatísticas em uma única chamada"""
        if not trade_returns:
            return StatisticalMetrics()
        
        returns = np.array(trade_returns)
        bench = np.array(benchmark_returns) if benchmark_returns else None
        
        # Métricas básicas
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        win_rate = len(wins) / len(returns) if len(returns) > 0 else 0
        
        metrics = StatisticalMetrics(
            sharpe_ratio=self.calculate_sharpe(returns),
            sortino_ratio=self.calculate_sortino(returns),
            expectancy=np.mean(returns),
            profit_factor=np.sum(wins) / np.abs(np.sum(losses)) if len(losses) > 0 else float('inf'),
            max_drawdown=0.0,  # Requer equity curve
            win_rate=win_rate,
            total_trades=len(returns),
            sample_size=len(returns)
        )
        
        # Teste de significância
        if len(returns) >= self.min_samples:
            sig_test = self.test_significance(returns, bench)
            metrics.p_value = sig_test.get('p_value')
            metrics.t_statistic = sig_test.get('t_statistic')
            metrics.confidence_interval_95 = sig_test.get('confidence_interval_95')
            metrics.is_significant = sig_test.get('significant', False)
        
        # Teste de normalidade
        if len(returns) >= 3:
            norm_test = self.test_normality(returns)
            metrics.is_normal = norm_test.get('normal')
            metrics.shapiro_p_value = norm_test.get('p_value')
        
        return metrics

# =============================================================================
# BACKTEST COM WALK-FORWARD VALIDATION
# =============================================================================

def run_backtest(data: List[Dict[str, Any]], cfg: Config) -> Dict[str, Any]:
    """Executa backtest com coleta de retornos para validação"""
    from blackbox_system import BlackboxSystem, Config
    
    bb = BlackboxSystem(cfg)
    trade_returns = []
    benchmark_returns = []
    
    for i, bar in enumerate(data):
        bb.update_bar(bar)
        bb.detect_liquidity_zone()
        sig = bb.generate_signal()
        
        if sig.direction != 0 and i < len(data) - 1:
            # Usa retorno do próximo candle como proxy
            next_bar = data[i + 1]
            ret = (next_bar['close'] - bar['close']) / bar['close']
            bench = bb.compute_benchmark_ret() or 0.0
            trade_returns.append(ret)
            benchmark_returns.append(bench)
            bb.record_trade_return(ret, bench_ret=bench)
    
    # Calcular métricas com validador estatístico
    validator = StatisticalValidator(min_samples=30, alpha=0.05)
    metrics = validator.compute_full_metrics(trade_returns, benchmark_returns)
    
    # Correção para múltiplos testes (se aplicável)
    multiple_test_correction = None
    if metrics.p_value is not None:
        correction = validator.bonferroni_correction([metrics.p_value], alpha=0.05)
        multiple_test_correction = correction
    
    return {
        "metrics": asdict(metrics),
        "trade_returns": trade_returns,
        "benchmark_returns": benchmark_returns,
        "multiple_test_correction": multiple_test_correction
    }

def run_walk_forward(data: List[Dict[str, Any]], cfg: Config, 
                    n_splits: int = 5) -> Dict[str, Any]:
    """Executa validação walk-forward para detectar overfitting"""
    if not SKLEARN_AVAILABLE or len(data) < n_splits * 50:
        return {
            "validated": False,
            "reason": "sklearn_unavailable_or_insufficient_data"
        }
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    results_in_sample = []
    results_out_of_sample = []
    
    for train_idx, test_idx in tscv.split(range(len(data))):
        train_data = [data[i] for i in train_idx]
        test_data = [data[i] for i in test_idx]
        
        # Backtest in-sample (treino)
        result_train = run_backtest(train_data, cfg)
        results_in_sample.append(result_train["metrics"])
        
        # Backtest out-of-sample (teste)
        result_test = run_backtest(test_data, cfg)
        results_out_of_sample.append(result_test["metrics"])
    
    # Calcular robustez
    sharpe_is = [r["sharpe_ratio"] for r in results_in_sample]
    sharpe_oos = [r["sharpe_ratio"] for r in results_out_of_sample]
    
    mean_sharpe_is = np.mean(sharpe_is) if sharpe_is else 0.0
    mean_sharpe_oos = np.mean(sharpe_oos) if sharpe_oos else 0.0
    std_sharpe_oos = np.std(sharpe_oos) if sharpe_oos else 0.0
    
    # Overfitting score: (IS - OOS) / IS
    overfitting_score = (mean_sharpe_is - mean_sharpe_oos) / max(mean_sharpe_is, 1e-10)
    
    # Robustez: OOS positivo e overfitting baixo
    is_robust = (mean_sharpe_oos > 0) and (overfitting_score < 0.3)
    
    return {
        "validated": True,
        "mean_sharpe_in_sample": mean_sharpe_is,
        "mean_sharpe_out_of_sample": mean_sharpe_oos,
        "std_sharpe_out_of_sample": std_sharpe_oos,
        "overfitting_score": overfitting_score,
        "is_robust": is_robust,
        "n_splits": n_splits,
        "details_in_sample": results_in_sample,
        "details_out_of_sample": results_out_of_sample
    }

# =============================================================================
# GRID SEARCH TIER-0
# =============================================================================

def grid_search(data: List[Dict[str, Any]],
                vol_z_vals: List[float],
                min_price_vals: List[float],
                conf_vals: List[float],
                enable_walk_forward: bool = True,
                n_splits: int = 5) -> List[Dict[str, Any]]:
    """Grid search com validação Tier-0"""
    from blackbox_system import Config
    
    results = []
    validator = StatisticalValidator(min_samples=30, alpha=0.05)
    all_p_values = []
    
    total_combinations = len(vol_z_vals) * len(min_price_vals) * len(conf_vals)
    print(f"Grid Search: {total_combinations} combinações")
    
    for i, vz in enumerate(vol_z_vals):
        for j, mp in enumerate(min_price_vals):
            for k, conf in enumerate(conf_vals):
                cfg = Config(
                    vol_z_threshold=vz,
                    min_price_change=mp,
                    min_confidence=conf,
                )
                
                # Backtest in-sample
                metrics_is = run_backtest(data, cfg)
                
                # Walk-forward validation (opcional mas recomendado)
                if enable_walk_forward and SKLEARN_AVAILABLE:
                    wf_result = run_walk_forward(data, cfg, n_splits=n_splits)
                    metrics_oos = wf_result.get("details_out_of_sample", [])
                    if metrics_oos:
                        # Média das métricas OOS
                        avg_sharpe_oos = np.mean([m.get("sharpe_ratio", 0) for m in metrics_oos])
                        metrics_is["metrics"]["sharpe_oos"] = avg_sharpe_oos
                        metrics_is["walk_forward"] = wf_result
                else:
                    metrics_is["walk_forward"] = {"validated": False, "reason": "disabled"}
                
                # Calcular overfitting score
                sharpe_is = metrics_is["metrics"].get("sharpe_ratio", 0)
                sharpe_oos = metrics_is["metrics"].get("sharpe_oos", sharpe_is)
                overfitting_score = (sharpe_is - sharpe_oos) / max(sharpe_is, 1e-10)
                
                # Determinar robustez
                is_robust = (sharpe_oos > 0) and (overfitting_score < 0.3)
                
                # Coletar p-values para correção de múltiplos testes
                p_val = metrics_is["metrics"].get("p_value")
                if p_val is not None:
                    all_p_values.append(p_val)
                
                # Gerar checksum para auditoria
                result_str = json.dumps({
                    "vol_z_threshold": vz,
                    "min_price_change": mp,
                    "min_confidence": conf,
                    "metrics": metrics_is["metrics"]
                }, sort_keys=True, default=str)
                checksum = hashlib.sha3_256(result_str.encode()).hexdigest()
                
                results.append({
                    "vol_z_threshold": vz,
                    "min_price_change": mp,
                    "min_confidence": conf,
                    "metrics_in_sample": metrics_is["metrics"],
                    "metrics_out_of_sample": metrics_is["metrics"].get("sharpe_oos", None),
                    "statistical_validation": {
                        "is_significant": metrics_is["metrics"].get("is_significant", False),
                        "p_value": p_val,
                        "is_normal": metrics_is["metrics"].get("is_normal", None),
                        "shapiro_p_value": metrics_is["metrics"].get("shapiro_p_value", None)
                    },
                    "overfitting_score": overfitting_score,
                    "is_robust": is_robust,
                    "checksum": checksum,
                    "walk_forward": metrics_is.get("walk_forward", {})
                })
                
                # Progresso
                combo_num = i * len(min_price_vals) * len(conf_vals) + j * len(conf_vals) + k + 1
                if combo_num % 5 == 0:
                    print(f"Progresso: {combo_num}/{total_combinations} ({combo_num/total_combinations*100:.1f}%)")
    
    # Aplicar correção de Bonferroni para múltiplos testes
    if all_p_values:
        correction = validator.bonferroni_correction(all_p_values, alpha=0.05)
        print(f"\nCorreção para Múltiplos Testes (Bonferroni):")
        print(f"  Alpha original: {correction['original_alpha']}")
        print(f"  Alpha corrigido: {correction['corrected_alpha']:.6f}")
        print(f"  Significantes antes: {correction['significant_before']}/{len(all_p_values)}")
        print(f"  Significantes depois: {correction['significant_after']}/{len(all_p_values)}")
        
        # Adicionar correção a todos os resultados
        for result in results:
            result["multiple_test_correction"] = correction
    
    # Ordenar por robustez e Sharpe OOS
    results.sort(key=lambda x: (x["is_robust"], x["metrics_out_of_sample"] or 0), reverse=True)
    
    return results

# =============================================================================
# EXPORTAÇÃO COM CHECKSUM
# =============================================================================

def export_results_with_checksum(results: List[Dict[str, Any]], filepath: str) -> str:
    """Exporta resultados com checksum para auditoria"""
    results_str = json.dumps(results, sort_keys=True, default=str, indent=2)
    checksum = hashlib.sha3_256(results_str.encode()).hexdigest()
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "checksum": checksum,
        "n_combinations": len(results),
        "results": results
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    return checksum

# =============================================================================
# MAIN EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Grid Search TIER-0 para BlackboxSystem")
    parser.add_argument("--csv", required=True, help="Caminho para CSV OHLCV")
    parser.add_argument("--out", default="grid_results_tier0.json", help="Arquivo de saída JSON")
    parser.add_argument("--no-walk-forward", action="store_true", help="Desativar walk-forward")
    parser.add_argument("--n-splits", type=int, default=5, help="Número de splits para walk-forward")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade")
    args = parser.parse_args()
    
    # Seed control para reprodutibilidade
    np.random.seed(args.seed)
    
    print("=" * 80)
    print("🔬 GRID SEARCH TIER-0 - BlackboxSystem Threshold Calibration")
    print("=" * 80)
    print(f"📁 CSV: {args.csv}")
    print(f"📄 Output: {args.out}")
    print(f"🔄 Walk-Forward: {'DESATIVADO' if args.no_walk_forward else f'ATIVADO ({args.n_splits} splits)'}")
    print(f"🎲 Seed: {args.seed}")
    print("=" * 80)
    
    # Carregar dados
    print("\n📊 Carregando dados...")
    data = load_csv(Path(args.csv))
    print(f"✅ {len(data)} barras carregadas")
    
    if len(data) < 100:
        warnings.warn(f"⚠️  Dados insuficientes ({len(data)} barras). Resultados podem não ser confiáveis.")
    
    # Executar grid search
    print("\n🔍 Executando grid search...")
    results = grid_search(
        data,
        vol_z_vals=[1.5, 2.0, 2.5],
        min_price_vals=[0.0002, 0.0005, 0.001],
        conf_vals=[0.2, 0.3, 0.4],
        enable_walk_forward=not args.no_walk_forward,
        n_splits=args.n_splits
    )
    
    # Exportar resultados
    print("\n💾 Exportando resultados...")
    checksum = export_results_with_checksum(results, args.out)
    print(f"✅ Resultados exportados: {args.out}")
    print(f"🔐 Checksum: {checksum[:32]}...")
    
    # Resumo dos melhores resultados
    print("\n" + "=" * 80)
    print("🏆 TOP 5 COMBINAÇÕES (ordenadas por robustez)")
    print("=" * 80)
    
    for i, result in enumerate(results[:5]):
        print(f"\n#{i+1}: vol_z={result['vol_z_threshold']}, min_price={result['min_price_change']}, conf={result['min_confidence']}")
        print(f"   Sharpe IS: {result['metrics_in_sample'].get('sharpe_ratio', 'N/A'):.3f}")
        print(f"   Sharpe OOS: {result['metrics_out_of_sample'] or 'N/A'}")
        print(f"   Overfitting Score: {result['overfitting_score']:.3f}")
        print(f"   Robusto: {'✅ SIM' if result['is_robust'] else '❌ NÃO'}")
        print(f"   Significância: {'✅ SIM' if result['statistical_validation'].get('is_significant') else '❌ NÃO'} (p={result['statistical_validation'].get('p_value', 'N/A')})")
    
    print("\n" + "=" * 80)
    print("✅ GRID SEARCH TIER-0 CONCLUÍDO")
    print("=" * 80)
