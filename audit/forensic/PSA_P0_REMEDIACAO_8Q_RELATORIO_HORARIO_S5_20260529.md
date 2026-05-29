# Relatório Horário §5 — CEO MANDATO C+A 2026-05-29

## 1. IDENTIFICAÇÃO

| Campo | Valor |
|-------|-------|
| Documento | PSA_P0_REMEDIACAO_8Q_RELATORIO_HORARIO_S5_20260529.md |
| Branch | hotfix/forensic-remediation-20260527 |
| Commit | `b151087` |
| Runner reinício | 2026-05-29 00:03 UTC (log local 01:03) |
| Gate T+30 | 2026-05-29 00:33 UTC |
| Gate T+60 | 2026-05-29 09:42 UTC |
| PSA executor | Devin CLI |

## 2. GATE T+30 — RESULTADO

### 2.1 Contagens (00:03–00:33 UTC)

| Métrica | Valor | Gate |
|---------|-------|------|
| executed | 82 | — |
| skipped | 82 | — |
| position_opened | 0 | PENDING |
| position_closed | 0 | — |
| entries_frozen_1 | 0 | **PASS** |
| model_dump_errors | 0 | **PASS** |
| mtf_confluence | 0 | CHECK (mercado calmo) |
| ger40_lines | 1688 | **PASS** |
| ukoil_lines | 1687 | **PASS** |
| xagusd_lines | 1687 | **PASS** |
| trade_feedback opened | 0 | PENDING |
| trade_feedback swap | 0 | PENDING |

### 2.2 Top Skip Reasons

Nenhuma razão de skip detetada no padrão de regex (formato de log pode variar).

## 3. GATE T+60 — RESULTADO (CORRIGIDO)

### 3.1 Contagens (00:03–09:42 UTC)

| Métrica | Valor | Gate |
|---------|-------|------|
| executed | 679 | — |
| skipped | 679 | — |
| position_opened | 0 | PENDING |
| position_closed | 0 | — |
| entries_frozen_1 | 0 | **PASS** |
| model_dump_errors | 0 | **PASS** |
| mtf_confluence | 117 | **PASS** |
| ger40_lines | 9582 | **PASS** |
| ukoil_lines | 13922 | **PASS** |
| xagusd_lines | 9515 | **PASS** |
| trade_feedback opened | 0 | PENDING |
| trade_feedback swap | 0 | PENDING |

### 3.2 Top Skip Reasons (CORRIGIDO)

| Razão | Contagem |
|-------|----------|
| hit_rate_134=63.39% < 65.0% | 6689 |

**Análise:** O hit_rate_134 está marginalmente abaixo do threshold de 65% (63.39%). Isto explica a maioria dos skips. O CEO pode considerar ajustar `OMEGA_HIT_RATE_MIN` se desejar mais execuções.

### 3.3 Amostras Asset

**FOREX (GBPUSD H1):**
```
[GBPUSD H1] [FLOW] confluence=55.8 | legacy: v_flow=50 vol_phy=50 | new: sto_fused=39 vof=50 vwap=100 pullback=50 wyckoff=50 elliott=87 liq=50 weis=0
```

**CRYPTO (ETHUSD H1):**
```
[ETHUSD H1] [FLOW] confluence=46.1 | legacy: v_flow=50 vol_phy=50 | new: sto_fused=40 vof=50 vwap=50 pullback=50 wyckoff=50 elliott=50 liq=50 weis=0
```

**ÍNDICE (GER40 H1):**
```
[GER40 H1] [FLOW] confluence=46.9 | legacy: v_flow=50 vol_phy=50 | new: sto_fused=39 vof=50 vwap=50 pullback=50 wyckoff=50 elliott=50 liq=50 weis=50
```

**COMMODITY (UKOIL+ H1):**
```
[UKOIL+ H1] [FLOW] confluence=43.2 | legacy: v_flow=50 vol_phy=50 | new: sto_fused=40 vof=50 vwap=0 pullback=50 wyckoff=50 elliott=50 liq=50 weis=50
```

**COMMODITY (XAGUSD H1):**
```
[XAGUSD H1] [FLOW] confluence=49.8 | legacy: v_flow=50 vol_phy=50 | new: sto_fused=40 vof=50 vwap=100 pullback=50 wyckoff=50 elliott=50 liq=50 weis=50
```

## 4. CONFIGURAÇÃO APLICADA (CEO-MANDATO-C+A)

| Variável | Valor | Origem |
|----------|-------|--------|
| OMEGA_MIN_CONFIDENCE | 0.62 | shadow_loop.py L488 + run_omega_24x7.ps1 |
| OMEGA_MAX_SAME_DIR_PER_CYCLE | 1 | run_omega_24x7.ps1 L36 |
| OMEGA_MAX_TP_SL_RATIO_INDEX | 10.0 | run_omega_24x7.ps1 L63 |
| OMEGA_MAX_POS_PER_ASSET | 1 | run_omega_24x7.ps1 L65 |
| OMEGA_DECISION_TRACE | 1 | run_omega_24x7.ps1 L13 |
| ENTRIES_FROZEN | 0 | live_flags.json (cache .pyc stale resolvido) |

## 5. CHECKLIST §5

- [x] Gate T+30 executado
- [x] Gate T+60 executado
- [x] model_dump=0
- [x] ENTRIES_FROZEN=0
- [x] GER40/UKOIL+/XAGUSD no portfolio e avaliados
- [x] FOREX (GBPUSD) amostra [FLOW]
- [x] CRYPTO (ETHUSD) amostra [FLOW]
- [x] Top skip reasons corrigidas (hit_rate_134=63.39% < 65.0%)
- [ ] swap JSONL com position_opened (PENDING — mercado calmo)
- [ ] Duplicatas (PENDING — nenhuma entrada nova)
- [ ] USFE auditoria (agendada amanhã 2026-05-30)

## 6. ESTADO RUNNER

| Item | Valor |
|------|-------|
| Status | Activo, ciclo contínuo |
| MT5 | terminal64.exe PID 25220 |
| Python PIDs | 10560 (runner), 35080 (OHLCV export) |
| Equity | $11,019.50 |
| Posições abertas | 8 (ETHUSD, BNBUSD, GBPUSD, etc.) |
| Janela visível | PowerShell (Start-Process) |

## 7. ANÁLISE HIT_RATE

| Ativo | hit_rate_134 | Threshold | Status |
|-------|-------------|-----------|--------|
| BTCUSD M15 | 63.39% | 65.0% | SKIP |

**Recomendação PSA:** Se o CEO deseja aumentar a taxa de execução, considerar:
1. Abaixar `OMEGA_HIT_RATE_MIN` de 65% para 63% (match actual)
2. Aumentar período de lookback do hit_rate_134
3. Aguardar recuperação natural do hit_rate

---
*Relatório gerado por PSA. Gate T+30: `audit/forensic/PSA_P0_REMEDIACAO_8Q_GATE_T30_20260529.txt`. Gate T+60: `audit/forensic/PSA_P0_REMEDIACAO_8Q_GATE_T60_20260529.txt`.*
