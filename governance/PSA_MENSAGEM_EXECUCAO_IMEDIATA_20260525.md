# Mensagem para PSA — Execução imediata (copiar e enviar)

> **⚠️ SUPERSEDED (2026-05-25):** Usar **`PSA_COMANDO_DEFINITIVO_ECOSISTEMA_20260525.md`** + **`PSA_MENSAGEM_ENVIO_CEO_20260525.md`**.  
> Este ficheiro mantém-se só como referência P0/discovery; **não** fecha integração ecossistema.

**Assunto:** OMEGA DEMO — Handover completo v2.0 — NÃO reimplementar — seguir instruções abaixo

**Para:** PSA (Devin)  
**De:** CEO / AIC Tech Lead  
**Data:** 2026-05-25  
**Prioridade:** Alta

---

## 1. Documento mestre (ler primeiro)

| O quê | Caminho |
|-------|---------|
| **Handover completo v2.0** | `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\governance\PSA_HANDOVER_ALTERACOES_COMPLETAS_20260525.md` |
| **Cópia Desktop** | `C:\Users\Lenovo\Desktop\File Desktop\Arquivos Pendentes Auditoria\Pendente\Auditoria\PSA_HANDOVER_ALTERACOES_COMPLETAS_20260525.md` |
| **Procedimento CEO DEMO** | `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\governance\CEO_GO_LIVE_DEMO_ZERO_CONFLITO_20260525.md` |

**GitHub:** repositório `OMEGA_OS_Kernel` — branch `feat/execution-router-atr-20260523` — HEAD mínimo `161be96` (ou superior).

**Regra:** Tudo no handover **já está feito**. A tua tarefa é **sincronizar, validar e não duplicar** trabalho.

---

## 2. Passo 1 — Sincronizar repositório

Abrir PowerShell e executar **na ordem**:

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git fetch origin
git checkout feat/execution-router-atr-20260523
git pull origin feat/execution-router-atr-20260523
git log -1 --oneline
```

**Validação esperada:** último commit inclui `161be96` ou `2517c8b` (handover / discovery).

Se estiveres noutra branch ou commit antigo, **não editar código** até estar alinhado.

---

## 3. Passo 2 — Gate de testes (obrigatório)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py tests/test_router_atr_20260523.py -q --tb=short
```

**PASS esperado:** `34 passed`

Se falhar → reportar CEO com log completo; **não** fazer merge nem alterar shadow_loop sem mandato.

---

## 4. Passo 3 — Pré-voo DEMO (recomendado)

**Pré-requisito:** MT5 aberto, conta DEMO ligada, Algo Trading ON, **0** posições OMEGA abertas.

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
& .\scripts\omega_demo_go_live.ps1
```

**PASS esperado:**

- pytest 34/34
- Ciclos EURUSD H1 (×2) e XAUUSD H4 com `exit=0`
- Reconcile: `ALL PASS`
- 0 posições órfãs magic `234001` / `OV2|`

**Relatório gerado em:** `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\demo_go_live\GO_LIVE_REPORT_*.txt`

---

## 5. Passo 4 — Arranque 24×7 (se CEO pedir reinício)

**Usar apenas um destes** (equivalentes após `2517c8b`):

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
& .\scripts\run_omega_24x7.ps1
```

ou:

```powershell
& .\scripts\restart_full_portfolio.ps1
```

(Ambos delegam para o mesmo runner — **sem** lista fixa `OMEGA_24X7_ATIVOS`.)

**NÃO fazer:**

- Definir `$env:OMEGA_24X7_ATIVOS = "..."` manualmente nos PS1
- Activar `OMEGA_USE_V2=1`
- Correr duas instâncias 24×7 em paralelo

---

## 6. Passo 5 — Monitorização (30 min após arranque)

**Log principal:**

`C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log`

**Confirmar no log:**

| Marcador | Significado |
|----------|-------------|
| `[SCHEDULE]` | T-W2 OK — 16 ativos por ciclo |
| `legacy_magic=234001` | Magic P0 OK |
| Ausência de `Invalid comment` | UT-9 OK |
| `ciclo N OK` | Runner saudável |

**Rastreio decisões:** `audit\paper\decision_trace.jsonl` (se activo)

**Schedule telemetria:** `audit\paper\asset_schedule.jsonl`

---

## 7. O que já está implementado (NÃO repetir)

| ID | Ficheiro / tema | Estado |
|----|-----------------|--------|
| P0-ABC | shadow_loop, magic, comments, market open | ✅ PSA (`80ba4f2`…) |
| T-R1 | `get_execution_tf_atr(signal_tf)` | ✅ PSA `37ec0b4` |
| T-F1a | `partial_taken` ledger | ✅ PSA `37ec0b4` |
| T-W2 | Re-resolve schedule cada ciclo | ✅ AIC `818f627` |
| Discovery 16 | `omega_asset_schedule.json` + profile | ✅ AIC `2517c8b` |
| Pré-voo | `omega_demo_go_live.ps1` | ✅ AIC `818f627` |

**Portfolio discovery (16 símbolos):**

```
EURUSD GBPUSD USDJPY AUDUSD USDCAD XAUUSD US500 US100
BTCUSD ETHUSD SOLUSD XRPUSD AVAXUSD ADAUSD LTCUSD BNBUSD
```

---

## 8. Proibições explícitas (evitar conflito com CEO/AIC)

1. Não re-adicionar lista fixa `OMEGA_24X7_ATIVOS` em `run_omega_24x7.ps1` ou `restart_full_portfolio.ps1`
2. Não reverter ATR para M1 em SL/TP
3. Não reimplementar T-W2 em `omega_paper_loop_24x7.py`
4. Não activar v2 no runner produção
5. Não fechar posições em massa sem ordem CEO

---

## 9. PRs e merge

| PR | URL | Acção |
|----|-----|-------|
| #1 P0 | https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/1 | Merge = **CEO** |
| #2 Router+DEMO | https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/2 | Merge = **CEO** |

PSA: após merge CEO, validar em `main` com pytest 34/34 + opcional `omega_demo_go_live.ps1`.

---

## 10. Entregável PSA (resposta esperada ao CEO)

Enviar **um** relatório curto com:

1. `git log -1 --oneline` após pull  
2. Resultado pytest (34/34 sim/não)  
3. Resultado `omega_demo_go_live.ps1` (se corrido)  
4. Runner activo? (sim/não) + últimas 5 linhas com `[SCHEDULE]` do log  
5. Confirmação: **não alterou** ficheiros listados na secção 7 sem mandato novo  

---

## 11. Escopo fora deste handover (novo mandato CEO)

- Fase 2 (cascata / M1-GATE)
- TRE (Temporal Resonance Engine)
- Alterações em `main` sem passar por PR #1 / #2

---

*Fim da mensagem — PSA_MENSAGEM_EXECUCAO_IMEDIATA_20260525.md*
