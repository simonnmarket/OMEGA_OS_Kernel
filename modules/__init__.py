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

[VWAP ENGINE]
  vwap_engine.py        VWAP = Σ(typical_price × volume) / Σ(volume)  [Bloomberg standard]
                        σ volume-ponderada (volume-weighted std dev)
                        Z-score: (close - VWAP) / σ_vw  (adimensional)
                        band_position ∈ [-1,+1] + vwap_pct_dist (%)
                        Fallback: typical_price → close, tick_volume → volume
                        → Integração: filtro de tendência e gate de entrada (shadow_loop)

[PVSRA — PRICE VOLUME SUPPORT RESISTANCE ANALYSIS]
  pvsra_analyzer.py     Local extremum order-2 em High/Low com volume
                        Touch counting vectorizado numpy (O(n) broadcasting)
                        Level dataclass: price, volume_norm, strength, touch_count, recency
                        Score = f(volume_ratio, touches, recency) ∈ [0,1]
                        nearest_sup_dist / nearest_res_dist normalizados por ATR
                        → Integração: compute_flow_confluence (shadow_loop)

[VOLUME ORDER FLOW]
  volume_order_flow.py  Delta imbalance por barra (close>=open=buy aggressor)
                        Z-score Welford (Bessel) + pressure_ratio + absorption_strength
                        Kernel Numba-accelerated + fallback numpy vectorizado
                        → Integração: compute_flow_confluence (shadow_loop)

[PULLBACK RE-ENTRY — B1]
  pullback_reentry_engine.py  EMA8/21 + ATR, profundidade multi-lookback, volume score, from_config(4 regimes)
                        Self-test 4 regimes + benchmark 10k (hot path numpy) ≤500 µs; sem MT5/execução
                        → Integração: gate de re-entry pós-pullback (shadow_loop / regime engine)

[VOLUME FOOTPRINT — A4]
  volume_footprint_engine.py  VA/POC via histograma NumPy; delta_ratio OHLCV
                        Z-score vs distribuição volume-ponderada; telemetria adimensional
                        tick_volume → volume; self-test 4 regimes + benchmark 10k
                        → Integração: compute_flow_confluence (shadow_loop) [pendente wiring]

[STO INSTITUTIONAL — A5]
  sto_institutional_detector.py  Microstructure: rolling delta z + volume z (edition 2 base)
                        Welford Bessel alinhado ao Pandas; from_config(regime); fail-operational
                        → Integração: compute_flow_confluence (shadow_loop) [pendente wiring]

[STO FORCE HISTOGRAM — swings + volume]
  sto_force_histogram_engine.py  Swings ATR + histograma de força por perna (edition 2)
                        Filtros MA + percentil; z-scores vs histórico de swings; fail-operational
                        → Integração: compute_flow_confluence (shadow_loop) [pendente wiring]

[STO FUSED — bar + swing + logística]
  sto_fused_microstructure_engine.py  Fusão volume-z + delta proxy + swing volumes + score logístico
                        from_config(regime); fail-operational; benchmark self-test threshold 2000 µs
                        → Integração: compute_flow_confluence (shadow_loop) [pendente wiring]

[WEIS WAVE + MICROSTRUCTURE]
  weis_wave_engine.py   Weis Wave (volume acumulado por onda direcional)
                        Kalman 1D + Ring Buffer NumPy (zero-allocation hot path)
                        WelfordStats (variância Bessel + merge Chan)
                        Z-threshold adaptativo via EWMA (adimensional)
                        SymbolConstraintsManager (TTL cache, fail-operational)
                        → Integração: compute_flow_confluence (shadow_loop)

[LIQUIDITY ABSORPTION — C1]
  liquidity_absorption_engine.py  Volume z-score Welford (janela local) + body_ratio + close_location
                        Regra de absorção: corpo < limiar + close na metade + volume_z >= limiar
                        strength = sqrt(volume_z^2 + (1-body_ratio)^2); from_config(4 regimes)
                        Hot path ~26 µs/call; sem MT5, sem pandas no núcleo
                        → Integração: proxy absorção / pressão de candle (shadow_loop)

[ELLIOTT IMPULSE TRACKER — D1]
  elliott_impulse_tracker_engine.py  ATR Wilder + detecção de swings + varredura 6 pivots (5 ondas)
                        Regras: W2 retracement Fib, W3 não mais curta, W4 sem overlap W1, alternância
                        strength = 0.4·w2 + 0.3·w3 + 0.2·w4 + 0.1·alt; from_config(4 regimes)
                        Hot path ~53 µs/call (Numba); sem MT5
                        → Integração: gate de impulso Elliott (shadow_loop / regime engine)

[WYCKOFF ANALYZER — B3]
  wyckoff_analyzer.py   6 fases Wyckoff (Accumulation→Markdown) via SMA20/50 + ATR
                        Spring / UTAD detection normalizado por ATR (substitui % preço MQL5)
                        Markup/Markdown Advanced: 3 HH+volume / 3 LL+volume vectorizado
                        ComponentState: phase, spring_score, utad_score, strength, direction
                        → Integração: gate de fase Wyckoff (shadow_loop / regime engine)

[SESSION CLOCK — TIER-0]
  omega_session_clock.py  Relógio canónico: UTC, OMEGA_BERLIN, BROKER, TERMINAL_LOCAL; sessões OMEGA (UTC)
                        NYSE/LSE venue status + overrides opcionais em config/omega_session_clock.json
                        ID: MOD-SESSION-CLOCK-001 | register_module() + run_self_test() T01–T07
                        Env: OMEGA_POLICY_TZ, OMEGA_BROKER_TZ, OMEGA_BROKER_OFFSET_MINUTES, OMEGA_TERMINAL_TZ, OMEGA_SOURCE_ROOT
                        → Integração: carimbos temporais e audit_bundle em pipelines/JSONL (sem MT5)

[EXECUTION BRIDGE — FILE JSON ↔ MT5]
  omega_execution_bridge_v2_2.py  Ponte JSON atómica Python → MT5 Common Files
                        VERSÃO DO COMPONENTE: v2.2 (PSA-EXEC-BRIDGE-v2.2 | 2026-05-14)
                        VERSÃO DO PACOTE modules: v2.5.1 — numerações independentes
                        Escreve AIRequest.SYMBOL.json (tmp+os.replace) e faz poll AIResponse
                        Kill Switch via ks_daily_state.json; regimes forex/crypto/metal/default
                        strength = w_conf × confidence + w_volt × voltage_norm (pesos normalizados)
                        Bloqueante síncrono — adequado a chamada após decisão final
                        Sem ZMQ; sem pandas/numba obrigatórios (optional com fallback)
                        → DECISÃO CONSELHO (17/05/2026): Opção B — runner dedicado
                          scripts/omega_bridge_runner.py executa fora do hot path do shadow_loop
                          Opção A (hub integrado) condicionada a: desenho aprovado +
                          OMEGA_FILE_BRIDGE_AFTER_DECISION=1 + regra anti-duplicação mt5_send_order
                          NÃO integrar directamente no shadow_loop sem desenho assinado pelo Conselho

════════════════════════════════════════════════════════
COMO ADICIONAR NOVO MÓDULO
════════════════════════════════════════════════════════
  1. Criar modules/nome_modulo.py
  2. Seguir o padrão: Config dataclass + Engine class + _run_tests()
  3. Adicionar entrada aqui em __all__
  4. Nenhuma dependência de outros módulos OMEGA

Versão: 2.5.1 — 2026-05-17
"""

__version__ = "2.5.1"
__all__ = [
    "risk_metrics",        # VaR institucional
    "anomaly_detector",    # Isolation Forest + Autoencoder
    "zone_navigator",      # NICER Core/Buffer zones
    "momentum_physics",    # Jerk + Half-Life
    "lot_calculator",      # Lote adaptativo
    "volume_profile",      # Volume profile horário + absorção
    "fractal_hurst",       # Expoente de Hurst e Estado Fractal
    "weis_wave_engine",    # Weis Wave + Kalman Delta + Microstructure
    "volume_order_flow",   # Delta imbalance + Z-score + Absorção
    "volume_footprint_engine",  # VA/POC + delta_ratio + z vs perfil (A4)
    "sto_institutional_detector",  # STO / microstructure delta_z + volume_z (A5)
    "sto_force_histogram_engine",  # STO swing-force volume + delta z (histogram)
    "sto_fused_microstructure_engine",  # STO fused bar + swing + logistic
    "pvsra_analyzer",      # S/R por volume + touch count + force score
    "vwap_engine",         # VWAP volume-ponderado + bandas + z-score
    "pullback_reentry_engine",  # B1: EMA + multi-lookback pullback + re-entry hint
    "wyckoff_analyzer",    # B3: 6 fases Wyckoff + Spring/UTAD ATR-normalizado
    "liquidity_absorption_engine",  # C1: volume_z Welford + body_ratio + close_location
    "elliott_impulse_tracker_engine",  # D1: 5-wave impulse ATR swings + Fib rules
    "gap_analysis_tracker",            # GAP: Breakaway/Exhaustion/Runaway + VSA (CEO Order 04/05/2026)
    "weis_wave_tracker",               # Weis Wave: same-dir wave z-score + trend confirmation
    "fimathe_breakout_engine",         # FIMATHE: channel breakout + ATR risk sizing
    "pattern_detector_engine",         # Institutional Pattern Detector: ZigZag + multi-pattern
    "microstructure_tracker",          # Microstructure: tick delta imbalance + Welford z-score
    "omega_execution_bridge_v2_2",      # FILE BRIDGE: AIRequest/AIResponse JSON atómico ↔ MT5 Common Files
    "omega_session_clock",              # TIER-0: relógio canónico + sessões UTC + venues NYSE/LSE
]
