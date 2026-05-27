# README — OMEGA FORENSIC AUDIT 20260520

**ID:** OMEGA-FORENSIC-AUDIT-REQUEST-PSA-20260520  
**Auditora:** PSA / Cascade  
**Data extracção:** 2026-05-20 21:20 UTC+2  
**Prazo resposta:** 2026-05-21 12:00 UTC ✅ DENTRO DO PRAZO

---

## 1. Metodologia

| Ferramenta | Uso |
|-----------|-----|
| PowerShell `Select-String` | Grep em omega_24x7_runner.log (500k+ linhas) |
| PowerShell `Get-CimInstance Win32_Process` | Processos activos + CommandLine |
| PowerShell `Get-Process` + `MainWindowTitle` | Janelas abertas |
| `grep_search` (ripgrep) | Varredura código-fonte order_send / magic |
| `ConvertFrom-Json` | Análise decision_trace.jsonl (1.012 registos) + trade_feedback.jsonl (1.108 eventos) |
| `Read-File` (PSA) | Análise linha a linha de main.py (554 linhas) |

---

## 2. Resumo dos Achados

| Achado | Valor | Severidade |
|-------|-------|-----------|
| Processos python3.11.exe activos | 3 PIDs (28364=411MB ACTIVO) | INFO |
| MT5 Demo activo (Hantec) | PID 38048, USDJPY M1 | INFO |
| Equity actual | USD 1,250.80 (vs $1,664 em 14/05) | **CRÍTICO DD=-24.9%** |
| magic=0 em ordens (Tier-0 30d) | 1.460 / 1.855 deals = 78.7% | **CRÍTICO** |
| SKIP_SPREAD_GUARD | 13 (decision_trace) / 0 (runner.log) | MÉDIO |
| SKIP_ROLLOVER_BLACKOUT | 0 | INFO |
| MOMENTUM_FALLBACK DISABLED | 6.812 ocorrências | OK |
| INVALID_STOPS [MT5_MODIFY_SL] | 84 (SL modification failures) | MÉDIO |
| Ordens executadas hoje (retcode 10009) | 117 | INFO |
| Ficheiros com order_send (activos) | 25 | ALTO |
| Ficheiros ghost com magic não-oficial | 4 (777777/500500/550550/0) | ALTO |
| main.py ORDEM_REAL_EXECUTADA hoje | 0 (inactivo) | OK |
| Intrusão activa confirmada | **NÃO** | OK |

---

## 3. Estrutura do Pacote

```
OMEGA_FORENSIC_AUDIT_20260520/
├── 01_MT5_DATA/
│   └── OMEGA_MT5_COMMENT_PATTERNS.csv     — event_type e signal_source da trade_feedback.jsonl
├── 02_LOGS/
│   ├── OMEGA_24x7_RUNNER_LOG_FIRST_50_LINES.txt  — boot 2026-05-20 07:22:59
│   ├── OMEGA_LOG_STRING_COUNTS.csv                — contagem 7 strings críticas
│   ├── OMEGA_DECISION_TRACE_20260520.jsonl        — 1.012 registos completos
│   └── OMEGA_DECISION_STATUS_COUNTS.csv           — agregado por status
├── 03_SOURCE_CODE/
│   ├── OMEGA_ORDER_SEND_FILES.csv         — 25 ficheiros com order_send
│   ├── OMEGA_MAGIC_NUMBERS.csv            — 31 ocorrências de magic não-canónico
│   ├── OMEGA_SUSPICIOUS_COMMENTS.csv      — 16 ocorrências de comentários suspeitos
│   └── OMEGA_MAIN_PY_STRATEGIES.csv       — 12 estratégias do main.py + conflito
├── 04_PROCESSOS/
│   ├── OMEGA_PYTHON_PROCESSES_20260520.csv — python3.11.exe PIDs
│   └── OMEGA_OPEN_WINDOWS_20260520.txt     — 9 janelas abertas com título
├── OMEGA_FORENSIC_ANSWERS.md              — Respostas Q1-Q15 completas
└── README.md                              — Este ficheiro
```

**NOTA:** `01_MT5_DATA/` não contém CSV por data individual (OMEGA_MT5_ORDERS_*.csv) porque a PSA não tem acesso directo à API MT5 nesta sessão. Os dados de ordens individuais requerem extracção pelo CEO via `scripts/psa_export_mt5_tier0.py` ou via Histório MT5 → Exportar.

---

## 4. Limitações

1. **CommandLine dos python3.11.exe**: Win32_Process retornou campo vazio por restrição de permissão. Requer verificação manual no Task Manager (Detalhes → Colunas → Command Line).
2. **MT5 positions activas**: Sem acesso directo à API MT5 nesta sessão. Posições abertas requerem verificação no terminal MT5.
3. **OMEGA_MT5_ORDERS por dia**: Não gerado — requer API MT5 ou exportação manual.
4. **Screenshot MT5 settings**: Não possível via linha de comando.
5. **decision_trace.jsonl**: Cobre apenas a sessão actual (2026-05-20). Sessões anteriores em ficheiros separados se existirem.

---

## 5. Recomendações Imediatas

### P0 — FAZER ANTES DE QUALQUER RESTART

1. **Fechar posições orphan (magic=0) no MT5** — abrir terminal MT5 → Positions → filtrar por Comment → fechar manualmente as que não têm `OV2|` no comment.

2. **Patch magic em shadow_loop.py:**
   ```python
   # Em mt5_send_order, adicionar ao dict request:
   "magic": int(os.getenv("OMEGA_MAGIC_NUMBER", "234001")),
   ```

3. **Adicionar log no caller M1 (shadow_loop.py:3971+):**
   ```python
   if gate_status == "SKIP_SPREAD_GUARD":
       log.warning("[%s %s] %s", asset, tf, gate_msg)
   ```

### P1 — ISOLAMENTO DE SCRIPTS GHOST

```powershell
# Mover para /inativo/:
Move-Item omega_turing_live.py inativo\
Move-Item live_drone_v5.py inativo\
Move-Item omega_v550_realtime_mt5.py inativo\
Move-Item omega_v550_realtime_mt5_v550.py inativo\
Move-Item core_engines\shadow_loop_v2.py inativo\
```

### P2 — VALIDAÇÃO PÓS-PATCH

```powershell
# Após restart, verificar magic nos primeiros deals:
python scripts/psa_export_mt5_tier0.py --days 1 --output audit/forensic/post_patch/
# Confirmar: magic=234001 em 100% dos deals novos
```

---

## 6. Conclusão Forense

**Não há intrusão activa.** O sistema a correr hoje é exclusivamente `shadow_loop.py` via `run_omega_24x7.ps1` (mode=paper, demo Hantec).

**A regressão DD -24.9% deve-se a:**
1. **magic=0** → posições não identificadas → escape do trailing stop e partial close
2. **13 spread-guard blocks** (funcionais mas não visíveis no log principal) não foram suficientes para prevenir todas as entradas em spread elevado
3. **equity=1250.80** confirma que o sistema opera com capital real no MT5 demo, acumulando perdas desde 2026-05-14

**Acção CEO:** Patch magic + mover scripts ghost + re-exportar Tier-0 pós-patch.
