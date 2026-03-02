## Blackbox – Consolidação (Liquidez, Armadilhas, Absorção)

### Fontes
- `Zonas de Liquidez e Armadilhas.txt`: detecção de zonas por volume alto, rejeição na zona, varredura de liquidez e armadilhas (break/fake).
- `Padrão de Absorção.txt`: padrão de absorção (preço sobe com volume caindo), execução de compra.

### Problemas dos originais (MQL)
- Thresholds fixos (volume 1000, priceChange 0.0005) sem normalização.
- Sem gestão de risco (lot fixo, SL/TP fixos em pips).
- Sem checagem de spread/sessão e sem métricas de performance.

### Consolidação proposta (Python scaffold)
- Arquivo: `blackbox_system.py`
- Componentes:
  - `detect_liquidity_zones`: marca zonas por volume z-score ou percentil.
  - `check_rejection`: candle toca a zona e fecha dentro do range.
  - `check_sweep`: movimento significativo entre fechamentos.
  - `check_trap`: quebra e retorno rápido (fake breakout).
  - `check_absorption`: preço sobe com volume caindo e mudança mínima de preço.
  - `generate_signal`: combina absorção + armadilha/rejeição → sinal BUY/SELL com confiança.
- Configurável: lookback, z-score/percentil, min_price_change, volume_threshold, min_confidence.
- Métricas básicas: registra retornos e benchmark (buy&hold), exporta métricas (Sharpe/Sortino/expectancy/PF/DD/alpha).

### Próximos passos
- Substituir heurísticas por calibração via dados (grid/estatística).
- Normalizar thresholds por ativo/timeframe e validar com backtest.
- Conectar executor/risco externo (MT5/Exchange) e registrar PnL incremental.
