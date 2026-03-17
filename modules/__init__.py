"""
OMEGA OS Kernel — Módulos Expansivos
=====================================
Princípio: cada módulo é AUTÓNOMO e EXPANSÍVEL.
  • Zero dependências entre módulos OMEGA
  • Só numpy / pandas como dependências externas
  • Cada módulo tem testes internos próprios
  • Para expandir: modificar Config ou adicionar métodos ao Engine

════════════════════════════════════════════════════════
MÓDULOS DISPONÍVEIS
════════════════════════════════════════════════════════

[RISCO]
  risk_metrics.py       VaR (5 métodos), CVaR, MaxDD, Sharpe, Calmar
                        → Integração: risk_engine.py

[DETECÇÃO DE ANOMALIAS]
  anomaly_detector.py   Isolation Forest + Autoencoder
                        Flash Crash, Black Swan, Liquidity Void
                        → Integração: antes do Pullback Engine (protecção)

[NAVEGAÇÃO DE ZONAS — NICER]
  zone_navigator.py     CORE Zone vs BUFFER Zone
                        CalculateExhaustVelocity, Volume Profile Horário
                        → Integração: ScaleManager + Pullback Engine

[FÍSICA DO MOMENTUM]
  momentum_physics.py   Velocidade + Aceleração + Jerk (3ª derivada)
                        Half-Life de reversão, Z-score ponderado
                        → Integração: Pullback Engine (confirmar retomada)

[ESTADO FRACTAL]
  fractal_hurst.py      Expoente de Hurst, Dimensão Fractal e Correlação
                        Mede persistência: Trending vs Mean-Reverting vs Random Walk
                        → Integração: Filtro principal do Pullback Engine

[CÁLCULO DE LOTE]
  lot_calculator.py     Lote adaptativo: vol + confiança + desempenho + Kelly
                        SL/TP por ATR, Trailing, Breakeven
                        Verificações hierárquicas de risco
                        → Integração: ScaleManager + execução de ordens

[VOLUME PROFILE]
  volume_profile.py     Volume Profile Horário (sazonalidade intraday)
                        Flow Imbalance, VWM, Exhaustion Score
                        Padrão de Absorção (preço↑ + volume↓)
                        → Integração: Pullback Engine (critério Volume Exhaustion)

════════════════════════════════════════════════════════
COMO ADICIONAR NOVO MÓDULO
════════════════════════════════════════════════════════
  1. Criar modules/nome_modulo.py
  2. Seguir o padrão: Config dataclass + Engine class + _run_tests()
  3. Adicionar entrada aqui em __all__
  4. Nenhuma dependência de outros módulos OMEGA

Versão: 2.0.0 — 2026-03-06
"""

__version__ = "2.0.0"
__all__ = [
    "risk_metrics",      # VaR institucional
    "anomaly_detector",  # Isolation Forest + Autoencoder
    "zone_navigator",    # NICER Core/Buffer zones
    "momentum_physics",  # Jerk + Half-Life
    "lot_calculator",    # Lote adaptativo
    "volume_profile",    # Volume profile horário + absorção
    "fractal_hurst",     # Expoente de Hurst e Estado Fractal
]
