# CEO MANDATO C+A — OBSERVABILIDADE 2026-05-29

## 1. MANDATO

| Item | Decisão CEO |
|------|-------------|
| C | Janela PowerShell visível com logs em tempo real |
| A | MIN_CONFIDENCE=0.62 efectivo (era 0.65 hardcoded) |
| DECISION_TRACE | Mantido = 1 |
| USFE | Auditoria amanhã (2026-05-30) |

## 2. ALTERAÇÕES APLICADAS

### 2.1 shadow_loop.py
- Linha 488: `MIN_CONFIDENCE = float(os.getenv("OMEGA_MIN_CONFIDENCE", "0.62"))`
- Permite override via env var; fallback 0.62 (era 0.65)

### 2.2 run_omega_24x7.ps1
- `$env:OMEGA_MIN_CONFIDENCE = "0.62"` (linha 32)
- `$env:OMEGA_MAX_SAME_DIR_PER_CYCLE = "1"` (linha 36)
- `$env:OMEGA_MAX_TP_SL_RATIO_INDEX = "10.0"` (linha 63)
- `$env:OMEGA_MAX_POS_PER_ASSET = "1"` (linha 65)

### 2.3 omega_asset_schedule.json
- Adicionados: GER40, UKOIL+, XAGUSD (19 ativos total)

## 3. ESTADO RUNNER (T+0)

| Métrica | Valor |
|---------|-------|
| Ciclo actual | 1 (reiniciado 01:03 UTC) |
| Python PIDs | 10560 (runner), 35080 (export OHLCV) |
| MT5 PID | 25220 (terminal64.exe) |
| Equity MT5 | $11,019.50 |
| ENTRIES_FROZEN=1 pós 23:01 | **0** (cache .pyc stale resolvido) |
| model_dump errors | 0 |
| MTF_CONFLUENCE | 56+ |
| GER40 eval | 1505+ linhas |
| pyramid_eval | 6105+ |
| position_opened (log) | 0 (mercado calmo / gates actuam) |

## 4. GATE T+0 — RESULTADO

| Gate | Critério | Resultado |
|------|----------|-----------|
| py_compile | exit 0 | **PASS** |
| model_dump | 0 erros | **PASS** |
| MTF_CONFLUENCE | >= 0 | **PASS** (56) |
| ENTRIES_FROZEN=1 | 0 após marcador | **PASS** (0) |
| GER40 eval | >= 1 linha | **PASS** (1505) |
| swap JSONL | pendente (nenhuma position_opened nova) | **PENDING** |
| Duplicata | max 1 posição nova em 5 min | **PENDING** |

## 5. RELATÓRIO HORÁRIO §5

### 5.1 Ciclo Hora 01:00–02:00 UTC
- Runner reiniciado com janela PowerShell visível
- MIN_CONFIDENCE=0.62 aplicado
- 19 ativos no portfolio (incl. GER40/UKOIL+/XAGUSD)
- MT5 conectado, equity real $11,019.50
- 8 posições existentes em trailing (ETHUSD, BNBUSD, GBPUSD, etc.)
- Nenhuma nova entrada (mercado calmo / gates)

### 5.2 Observações
- Janela PowerShell visível aberta via `Start-Process powershell`
- DECISION_TRACE=1 activo → `audit/paper/decision_trace.jsonl`
- Cache .pyc stale foi root cause do ENTRIES_FROZEN=1 falso; resolvido
- Próximo gate T+30 aguardado

## 6. CHECKLIST CEO

- [x] C — Janela PowerShell visível
- [x] A — MIN_CONFIDENCE=0.62
- [x] DECISION_TRACE=1
- [ ] E — Pack evidências final (após gates 2h)
- [ ] USFE — Auditoria amanhã

---
*Documento gerado por PSA. Commit: `3403109`.*
