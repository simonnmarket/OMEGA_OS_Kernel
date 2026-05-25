# OMEGA CHECKPOINT — PSA-WIND (30/04/2026 11:10 UTC)

## Diretriz: Mitigar risco primeiro, depois recuperar profit

### COMMITS
| Commit | Descrição |
|--------|-----------|
| `322e6fa` | Per-position partial_close engines + MT5 TradePosition compat in pyramiding |
| `e2eac8a` | PSA-WIND: 5 critical fixes (anti-hedge, spike, trailing, partial recalib, flow signal) |
| `76739e7` | FIX: ATR points-to-price conversion for trailing stop and partial close |

### 5 FIXES IMPLEMENTADOS

#### FIX 1: ANTI-HEDGE (Segurança)
- **Problema:** EURJPY abria BUY e SELL simultaneamente (hedge não intencional)
- **Fix:** Antes de abrir ordem, verifica se há posição oposta no mesmo ativo → BLOCK
- **Log tag:** `[ANTI_HEDGE] BLOCKED`
- **Evidência:** AUDJPY bloqueado (BUY existente vs sinal SELL)

#### FIX 2: SPIKE DETECTION (Segurança)
- **Problema:** `AnomalyDetector` existia mas não era chamado no loop
- **Fix:** Integrado pré-ordem: bloqueia entrada se severidade HIGH/CRITICAL (FLASH_CRASH, VOLATILITY_SPIKE, BLACK_SWAN)
- **Log tag:** `[SPIKE] BLOCKED` (HIGH/CRITICAL) ou `[SPIKE] MONITOR` (LOW/MODERATE)
- **Evidência:** QUANTUM_ENTROPY detectada em EURJPY/GBPJPY (LOW → monitor only)
- **Evidência:** VOLATILITY_SPIKE HIGH detectada no snapshot final

#### FIX 3: TRAILING STOP GEOMÉTRICO (Segurança + Profit)
- **Problema:** Zero trailing stop → posição parada até TP fixo ou SL hit
- **Fix:** `HardVolatilityTrailingStopGeometric` por posição (atr_mult=2.5, min=1.0)
- **Bug corrigido:** ATR era passado em pontos ao invés de preço (causava SL absurdo de 300+ unidades)
- **Log tag:** `[TRAILING]`
- **Evidência:** EURJPY trail_SL=186.508 (0.318 acima de peak=186.190) ← CORRECTO

#### FIX 4: PARTIAL CLOSE RECALIBRADO (Profit)
- **Problema anterior:** 50% fechado em 1×ATR, 80% em 2×ATR → matava posição antes do fluxo completar
- **Níveis PSA-WIND:**
  | Nível ATR | Fração | Descrição | Posição Restante |
  |-----------|--------|-----------|------------------|
  | 1.5×ATR | 20% | Leve | 80% |
  | 3.0×ATR | 25% | Médio | 55% |
  | 5.0×ATR | 25% | Forte | 30% |
  | 8.0×ATR | 20% | Extreme | 10% residual |
- **Resultado:** 50% da posição sobrevive até 3×ATR (vs 20% antes). 10% residual segue até TP.
- **Log tag:** `[PARTIAL_CLOSE] ... PSA-WIND ... levels=[1.5/3/5/8]ATR`

#### FIX 5: SINAL DE FLUXO ROBUSTO (Profit)
- **Problema:** Sinal baseado em média de 3 candles M1 (ruído puro, ~3 minutos de dados)
- **Fix:** EMA-8 vs EMA-21 em M5 (25 barras = 125 minutos) + slope mínimo ±1.0
- **Requisitos para sinal:**
  - EMA8 > EMA21 + slope > +1.0 → BUY
  - EMA8 < EMA21 + slope < -1.0 → SELL
  - Caso contrário → SKIP_NO_FLOW_TREND (sem tendência confirmada)
- **Log tag:** `FlowSignal:` (com EMA8, EMA21, slope, vol_ratio)
- **Resultado:** Filtra falsos positivos de 3-candle M1; só entra com tendência confirmada

### GUARDRAILS NÃO ALTERADOS
- DD_DAILY_MAX = 0.01 (1%)
- RISK_PER_TRADE = 0.001 (0.10%)
- MAX_POSITIONS = 20
- Edge Gate thresholds (ATR%, ADX por regime)
- Kill Switch
- Circuit Breaker

### ACEITE MÍNIMO (verificado nos logs)
- [x] Zero hedge (ANTI_HEDGE bloqueando AUDJPY BUY→SELL)
- [x] Spike detection acionando (QUANTUM_ENTROPY, VOLATILITY_SPIKE detectadas)
- [x] Trailing stop com valores correctos (186.508 vs peak 186.190)
- [x] Partial close PSA-WIND levels [1.5/3/5/8] ATR activos
- [x] FlowSignal com EMA/slope substituiu 3-candle M1
- [x] Nenhuma modificação de guardrails de risco

### BRANCH
`feature/nebular-integration-phase1`
