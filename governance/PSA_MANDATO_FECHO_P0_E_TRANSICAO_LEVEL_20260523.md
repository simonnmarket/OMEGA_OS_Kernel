# PSA — Mandato de Fecho P0-ABC + Transição para Level 1 (Router/ATR)

| Campo | Valor |
|-------|--------|
| **Documento** | PSA-MANDATO-FECHO-P0-LEVEL-20260523 |
| **Emitido por** | AIC Tech Lead (para execução PSA) |
| **Aprovado por** | CEO — ordem USDJPY fechada; sequência autorizada |
| **Data** | 2026-05-23 (actualizar data de conclusão smoke quando aplicável) |
| **Branch P0** | `fix/cicc-remediation-p0-abc-20260522` |
| **HEAD esperado** | `ed6452e` ou posterior (inclui `511e230` comment fix) |
| **Branch Level 1** | `feat/execution-router-atr-20260523` — **criar só após AIC P0 APROVADO** |
| **TRE** | **FORA DE ESCOPO** deste mandato — documento separado depois |

---

## 0. Declaração CEO (pré-requisito operacional)

| Item | Estado |
|------|--------|
| Posição órfã USDJPY #189777509 | **FECHADA** (CEO) |
| Conta MT5 limpa para smoke | **Assumir SIM** — CEO confirmar 0 posições `magic=234001` / `OV2\|` |
| Alinhamento AIC ↔ PSA | **CONFIRMADO** (`CEO_DECISAO_ROTEIRO_P0_20260523.md`) |
| D1 `partial_taken` | **Fase 1** (não bloqueia fecho P0) |
| Fases 1–3 Router | **Proibidas** até veredito AIC P0 |

---

## 1. Mapa de fases (visão geral)

```text
[FASE A] CEO Smoke MT5 + relatório Sec. 4–7     ← BLOQUEIA AIC
[FASE B] PSA Suporte fecho (git, docs, scripts)  ← PARALELO / APÓS A
[FASE C] AIC Validação → APROVADO ou REPROVADO
[FASE D] PSA Merge P0 + inventário final
[FASE E] LEVEL 1 — Router ATR (branch nova)      ← SÓ APÓS FASE C APROVADO
[FUTURO] TRE — Motor Ressonância Temporal        ← OUTRO MANDATO
```

**Veredito P0 “APROVADO”** exige: FASE A completa + FASE C **APROVADO**.

---

## 2. O que está FEITO — NÃO reexecutar

| ID | Tarefa | Commit / evidência |
|----|--------|-------------------|
| T-D1..T-D4, T-D4b | P0 core | `4a80b0c`, UT-1..4, UT-8 |
| T-P1a, T-D5, T-P1b, T-P1c, T-P2b | P0 patches | UT-5..7, runner test |
| T-W1, T-W3 | Weekend | `94bbc64` |
| Comment fix | MT5 ≤31 chars | `511e230`, UT-9 |
| UT total | 10/10 PASS | `tests/test_p0_abc_20260522.py` + runner |

**Proibido:** reabrir T-D4b, refazer lista fixa PS1, reintroduzir timestamp em comments.

---

## 3. FASE A — CEO (obrigatório; PSA apenas suporta)

### 3.1 Pré-check MT5 (CEO — 2 min)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
python scripts/check_positions_now.py
```

**PASS:** zero posições OMEGA abertas (ou CEO documenta excepção no relatório).

### 3.2 Variáveis de ambiente (CEO — uma vez por sessão)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:PYTHONIOENCODING = "utf-8"
```

### 3.3 Smoke — um comando por linha (CEO)

**Regra:** Enter após **cada** linha; aguardar `PAPER LOOP CONCLUÍDO` antes da seguinte.

| Passo | Comando | Critério |
|-------|---------|----------|
| A1 | `python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000` | SM-1 exit 0 |
| A2 | Repetir A1 | SM-2, SM-3 |
| A3 | `python -u core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H1 --equity 10000` | SM-6 |
| A4 | `python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD GBPJPY XAUUSD --timeframes H1 --equity 10000` | P2a-1..3 |
| A5 | `python scripts/psa_position_pnl_reconcile.py --since "2026-05-23 00:00:00"` | G3–G5, REG |

**Mercado:** forex aberto (segunda ou sessão com EURUSD negociável). Fim-de-semana pode dar `NO_TREND` / PSA_FEED stale — **não conta como smoke PASS**.

### 3.4 Relatório (CEO preenche; PSA revisa)

**Ficheiro:** `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md`

| Secção | Conteúdo obrigatório |
|--------|---------------------|
| 4 | SM-1..7 PASS/FAIL + últimas 50 linhas log |
| 5 | P2a-1..3 PASS/FAIL |
| 6 | G3–G5, REG-1/2 + output reconcile |
| 7.8 | Tabela PnL (Δ equity, Σ deals, Σ feedback) |
| 7.9 | Quantum/harmonic: 1 pág ou N/A com justificação |
| 9 | Veredito PSA: **APROVADO** só se 4–6 todos PASS |

**Entrega:** CEO envia caminho do relatório + anexa logs ou confirma ficheiros em `audit/paper/`.

---

## 4. FASE B — PSA (executar agora; não depende de smoke)

### B1 — Git remoto (obrigatório)

A branch P0 **não existe** em `origin`. Publicar para backup e PR:

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git status -sb
git log -1 --oneline
git push -u origin fix/cicc-remediation-p0-abc-20260522
```

**PASS:** `git pull origin fix/cicc-remediation-p0-abc-20260522` funciona noutra máquina.

**Não fazer:** `git config` global; não `push --force` em `main`.

### B2 — Script smoke CEO (obrigatório)

**Criar:** `scripts/run_p0_smoke_ceo.ps1`

Requisitos:
- `Set-Location` para `SOURCE_CODE`
- Define `PYTHONPATH`, `OMEGA_MAGIC_NUMBER`, `OMEGA_MAX_POS_PER_ASSET`, `PYTHONIOENCODING`
- Executa A1→A5 **sequencialmente** (comentário entre passos)
- Grava log agregado: `audit/smoke/p0_smoke_ceo_YYYYMMDD_HHMMSS.log`
- Exit code ≠ 0 se qualquer passo falhar

**PASS:** CEO pode correr `.\scripts\run_p0_smoke_ceo.ps1` numa só invocação.

### B3 — Diagnóstico PS1 alinhado T-W1 (obrigatório)

**Ficheiro:** `scripts/run_omega_diagnostico_post_cicc.ps1` L18

**De:** lista fixa `$env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD ..."`

**Para:** comentar lista fixa; usar `config/omega_asset_schedule.json` ou `--ativos` explícito documentado no cabeçalho do script.

**PASS:** grep não mostra assign obrigatório de 32 ativos sem comentário.

### B4 — Inventário ABC actualizado (obrigatório)

**Criar:** `governance/OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260523.md`

Base: `INVENTARIO_ALINHAMENTO_20260523.md` + checklist 20260523.

Colunas mínimas: `ID | Descrição | Tarefa P0 | Resolvido (SIM/NÃO) | Commit | UT/Smoke`

**Itens Resolvido=SIM obrigatórios:** A-01..A-05, B-01..B-11 (incl. T-D4b), X-02, X-03, T-W1, T-W3, comment fix.

**Itens Resolvido=NÃO (Fase 1+):** Falha A, B, C, D, T-W2 opcional.

**PASS:** DOC-1 (inventário 22/05 obsoleto) deixa de ser referência primária.

### B5 — Template AIC (obrigatório)

**Criar:** `governance/AIC_VALIDACAO_PSA_P0_ABC_20260523_TEMPLATE.md`

Secções: evidências CEO, tabela SM/P2a/G/REG, veredito APROVADO/REPROVADO/CONDICIONAL, lista fixes se REPROVADO, autorização Fase 1 (sim/não).

AIC preenche após smoke; PSA só entrega o template.

### B6 — Actualizar checklist e reconciliação (obrigatório)

| Ficheiro | Acção |
|----------|--------|
| `CHECKLIST_EXECUCAO_20260523.md` | Sec. “Pós-fecho USDJPY” + referência a este mandato |
| `AIC_PSA_RECONCILIACAO_ALINHAMENTO_20260523.md` | D1/D2/D4 → **FECHADO** per CEO_DECISAO |
| `PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` | Sec. 2: commit final = hash após B1 push |

**Commit sugerido:** `docs: fecho P0 mandato transição level 1 (B2-B6)`

### B7 — pytest gate (obrigatório antes de qualquer commit PSA)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py -q
```

**PASS:** 10/10+ (mínimo 10 sem falhas nos ficheiros acima).

---

## 5. FASE C — AIC (após FASE A)

| ID | Acção | Responsável |
|----|--------|-------------|
| C1 | Ler relatório PSA Sec. 4–7 preenchido | AIC |
| C2 | Emitir `governance/AIC_VALIDACAO_PSA_P0_ABC_20260523.md` | AIC |
| C3 | Veredito: **APROVADO** / **REPROVADO** / **CONDICIONAL** | AIC |
| C4 | Se APROVADO: autorizar explicitamente início Fase E | AIC + CEO |

**PSA:** não iniciar Fase E até existir ficheiro C2 com **APROVADO**.

---

## 6. FASE D — PSA pós-AIC APROVADO

| ID | Tarefa | Critério PASS |
|----|--------|---------------|
| D1 | PR `fix/cicc-remediation-p0-abc-20260522` → `main` | CEO autoriza merge |
| D2 | Tag opcional: `p0-abc-20260523` | Anotado no relatório |
| D3 | Arquivar inventário 22/05 | README em governance aponta 23/05 como master |
| D4 | Memorando “P0 FECHADO” 1 página | `governance/P0_ABC_FECHO_20260523.md` |

---

## 7. FASE E — LEVEL 1 (Router/ATR) — só após C4

**Branch nova:**

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout fix/cicc-remediation-p0-abc-20260522
git pull origin fix/cicc-remediation-p0-abc-20260522
git checkout -b feat/execution-router-atr-20260523
```

### 7.1 Ordem de tarefas (mandato unificado Sec. 7)

| Ordem | ID | Tarefa | Detalhe |
|-------|-----|--------|---------|
| 1 | **T-F1a** | `partial_taken` em `_pos_ledger` | CEO Opção A — 1ª tarefa não-bloqueante |
| 2 | **T-R1** | `get_execution_tf_atr(symbol, signal_tf, confidence)` | Mapa TF Sec. 7.1 mandato unificado |
| 3 | **T-R1b** | `sanitize_sl_tp` usa ATR do `signal_tf` | |
| 4 | **UT-R1, UT-R2** | Testes mock ATR H4 vs M1 | |
| 5 | **SM-R1..R3** | Smoke XAUUSD H4/H1 SL ≥ $20 | CEO ou PSA com MT5 |
| 6 | **Relatório** | `governance/PSA_RELATORIO_ROUTER_ATR_20260523.md` | |

**Proibido na Fase E:** Fase 2 cascata, Fase 3 v2 archive, integração TRE.

### 7.2 Critério de sucesso Level 1

| Gate | PASS |
|------|------|
| UT-R1 | H4 ATR domina M1 para `eff_sl` |
| SM-R2 | XAUUSD paper SL ≥ $20 em sinal H4 (log `atr_tf=H4`) |
| AIC | Validação Router Fase 1 documentada |

---

## 8. Tabela de pendências — estado único

| Pendência | Responsável | Fase | Bloqueia P0 APROVADO? |
|-----------|-------------|------|------------------------|
| Smoke SM-1..7 | CEO | A | **SIM** |
| Smoke P2a | CEO | A | **SIM** |
| Reconcile G3–G5, REG | CEO | A | **SIM** |
| Relatório Sec. 4–7 | CEO | A | **SIM** |
| `git push` branch P0 | PSA | B | Não (mas obrigatório ops) |
| Script `run_p0_smoke_ceo.ps1` | PSA | B | Não |
| Diagnóstico PS1 T-W1 | PSA | B | Não |
| Inventário 20260523 | PSA | B | Não |
| AIC_VALIDACAO | AIC | C | **SIM** |
| Merge main | PSA | D | Não (pós-AIC) |
| Fase 1 Router | PSA | E | N/A até AIC P0 |
| TRE | — | Futuro | Não |

---

## 9. O que o PSA NÃO deve fazer neste mandato

1. Iniciar `feat/execution-router-atr-20260523` antes de AIC P0 **APROVADO**.
2. Alterar escopo P0 (reimplementar T-D*).
3. Activar `OMEGA_USE_V2` ou portfolio 32 ativos sem autorização CEO escrita.
4. Implementar TRE ou misturar variáveis TRS/DI no `shadow_loop`.
5. Declarar “sistema operacional em produção” sem smoke Sec. 4–6 PASS.
6. `git push --force` ou alterar `git config` global.

---

## 10. Mensagem tipo — CEO para PSA (copiar)

```text
PSA,

Ordem USDJPY fechada. Autorizado fecho P0 e transição Level 1 conforme mandato:

governance/PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md

Executar FASE B (B1–B7) já.
Aguardar meu smoke (FASE A) para relatório Sec. 4–7.
FASE E (Router ATR) só após AIC_VALIDACAO APROVADO.

TRE fica para mandato separado — não incluir neste sprint.
```

---

## 11. Referências

| Documento | Caminho |
|-----------|---------|
| Relatório PSA | `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` |
| Mandato unificado | `governance/OMEGA_MANDATO_UNIFICADO_P0_ROUTER_WEEKEND_20260523.md` |
| CEO decisões | `governance/CEO_DECISAO_ROTEIRO_P0_20260523.md` |
| Checklist 23/05 | `governance/CHECKLIST_EXECUCAO_20260523.md` |
| Reconciliação AIC-PSA | `governance/AIC_PSA_RECONCILIACAO_ALINHAMENTO_20260523.md` |

---

**Assinatura AIC:** Tech Lead — mandato emitido para execução PSA  
**Próxima acção PSA:** B1 → B7 (paralelo ao smoke CEO)  
**Próxima acção CEO:** FASE A quando mercado forex aberto  
**TRE:** aguardar novo documento / mandato dedicado
