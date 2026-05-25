# PSA — Mandato de Fecho Definitivo (“Chave de Ouro”) — Sprint P0 + Fase 1

| Campo | Valor |
|-------|--------|
| **Documento** | PSA-CHAVE-OURO-20260525 |
| **Emitido** | AIC Tech Lead — consolidação final para CEO e PSA |
| **Data** | 2026-05-25 |
| **Objectivo** | **Único documento operacional** — o que está fechado, o que falta, zero ambiguidade |
| **Substitui para execução** | Todos os mandatos parciais deste sprint (mantém-se como referência histórica) |

---

## 0. Mensagem CEO → PSA (copiar e enviar)

```text
PSA,

Sprint P0-ABC + Fase 1 código: fecho definitivo conforme chave de ouro:

governance/PSA_MANDATO_FECHO_DEFINITIVO_CHAVE_OURO_20260525.md

Resumo: P0 e Fase 1 CÓDIGO estão APROVADOS pela AIC. Falta apenas o bloco
FINAL (Sec. 5 deste doc): push branch Router, SM-R smoke, relatório Router,
correcções menores, PR/merge com OK CEO.

TRE = fora de escopo — aguarda novo mandato CEO.

Quando Sec. 5 estiver 100%, responder:
"CHAVE DE OURO COMPLETA — commit <hash> — SM-R PASS — PR <url>"

CEO / AIC
```

---

## 1. Mapa executivo (CEO — 1 página)

### 1.1 O que está FECHADO (não reabrir)

| Bloco | Veredito | Commit / evidência |
|-------|----------|-------------------|
| **P0-ABC código** (T-D*, T-P*, T-W1/W3, comment) | ✅ AIC APROVADO | `4a80b0c` … `511e230` |
| **Fase B governança** | ✅ COMPLETA | `54ee899` |
| **Smoke P0 MT5** (integração) | ✅ AIC APROVADO | `80ba4f2` + pacote `PSA_ENTREGA_SMOKE_20260525/` |
| **Validação AIC P0** | ✅ EMITIDA | `AIC_VALIDACAO_PSA_P0_ABC_20260525.md` |
| **Fase 1 código** (T-F1a, T-R1, T-R1b, UT-R1..R5) | ✅ AIC APROVADO | `37ec0b4` |
| **Validação AIC Fase 1 código** | ✅ EMITIDA | `AIC_VALIDACAO_ROUTER_ATR_FASE1_20260525.md` |
| **D1 partial_taken** | ✅ FECHADO | T-F1a em `37ec0b4` |
| **Falha A (ATR signal_tf)** | ✅ Código corrigido | UT-R1; smoke vivo = SM-R |

### 1.2 O que está ABERTO (só isto fecha o sprint)

| # | Item | Responsável | Bloqueia “chave de ouro”? |
|---|------|-------------|---------------------------|
| **F1** | `git push` branch `feat/execution-router-atr-20260523` | PSA | **SIM** |
| **F2** | Smoke **SM-R1..R3** (XAUUSD H4, SL ≥ $20) | PSA ou CEO + MT5 | **SIM** |
| **F3** | `PSA_RELATORIO_ROUTER_ATR_20260523.md` | PSA | **SIM** |
| **F4** | Correcções menores (Sec. 6) | PSA | Parcial |
| **F5** | PR P0 → `main` + merge (após OK CEO) | PSA + CEO | Operacional |
| **F6** | PR Fase 1 → `main` (após F2 PASS + OK CEO) | PSA + CEO | Operacional |

### 1.3 Fora de escopo (explícito)

| Item | Estado |
|------|--------|
| **TRE** Motor Ressonância Temporal | Novo mandato — **não iniciar** |
| **Fase 2** Router cascata / M1-GATE | Proibido até F2 SM-R PASS + AIC |
| **Fase 3** archive v2 | Proibido |
| **T-W2** schedule por ciclo | Opcional CEO — **não bloqueia** |
| **24×7 produção** / portfolio 32 | Proibido até SM-R + CEO |

---

## 2. Linha temporal — commits (referência única)

| Data | Hash | Conteúdo |
|------|------|----------|
| 2026-05-22 | c5f0f25 | Base magic 234001 + PositionManager |
| 2026-05-23 | 4a80b0c | T-D4b wiring |
| 2026-05-23 | 94bbc64 | Fase 0b weekend |
| 2026-05-23 | 511e230 | Comment ≤31 chars + UT-9 |
| 2026-05-23 | 5865df9 / 54ee899 | Checklist + docs fecho |
| 2026-05-25 | 80ba4f2 | **Smoke P0** Sec. 4–7 |
| 2026-05-25 | 37ec0b4 | **Fase 1** T-F1a + T-R1 + UT-R1..R5 |

**Branches:**

| Branch | HEAD actual | Remote `origin`? |
|--------|-------------|------------------|
| `fix/cicc-remediation-p0-abc-20260522` | 80ba4f2 | ✅ **SIM** (push feito) |
| `feat/execution-router-atr-20260523` | 37ec0b4 | ❌ **NÃO** — **F1 pendente** |

---

## 3. Índice documental (todos os ficheiros deste sprint)

### 3.1 Documentos “lei” (ler se dúvida)

| Prioridade | Documento | Função |
|------------|-------------|--------|
| ★★★ | **Este ficheiro** | Execução final PSA |
| ★★★ | `OMEGA_MANDATO_UNIFICADO_P0_ROUTER_WEEKEND_20260523.md` | Spec técnica P0 + Router |
| ★★ | `AIC_VALIDACAO_PSA_P0_ABC_20260525.md` | Veredito P0 |
| ★★ | `AIC_VALIDACAO_ROUTER_ATR_FASE1_20260525.md` | Veredito Fase 1 código |
| ★★ | `PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` | Relatório P0 (Sec. 4–9) |
| ★ | `P0_ABC_FECHO_20260525.md` | Declaração fecho P0 |
| ★ | `CHECKLIST_EXECUCAO_20260523.md` | Histórico PSA 23/05 |
| ★ | `OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260523.md` | Inventário master |
| ○ | `CEO_DECISAO_ROTEIRO_P0_20260523.md` | Decisões D1/T-W2 |
| ○ | `audit/smoke/PSA_ENTREGA_SMOKE_20260525/` | Evidências smoke P0 |

### 3.2 Mandatos parciais (histórico — não repetir trabalho)

| Documento | Estado |
|-----------|--------|
| `PSA_MANDATO_EXECUCAO_P0_ABC_20260522.md` | Concluído |
| `PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md` | Fase B completa |
| `PSA_MANDATO_SMOKE_MT5_EXECUCAO_IMEDIATA_20260525.md` | Smoke P0 completo |

---

## 4. Detalhes que faltavam no pacote (agora explícitos)

### 4.1 Limitações aceites (Tier-0 — CEO informado)

| Limitação | Porquê | Mitigação |
|-----------|--------|-----------|
| Smoke P0 com **0 ordens** (25/05) | Filtros NO_TREND / EDGE_GATE / Memorial Day | UT-1..9; SM-R com entrada |
| SM-3 (1pos) não stressado em vivo | Sem ordem EURUSD | UT-1 |
| SM-5/6/7 N/A no smoke P0 | Sem posição | UT + SM-R |
| Falha B/C/D | Fora P0/Fase 1 | Fases 2–3 |

### 4.2 Problemas conhecidos — backlog menor (PSA Sec. 6)

| ID | Problema | Acção PSA | Prioridade |
|----|----------|-----------|------------|
| BK-1 | Relatório P0 Sec. 7.8 typos (`bash.00`, vírgulas balance) | Corrigir no próximo commit docs | Baixa |
| BK-2 | `run_p0_smoke_ceo.ps1` — `--since` com quebra de linha no relatório | Script: usar `--since "2026-05-25 00:00:00"` numa linha; re-testar | Média |
| BK-3 | `scripts/restart_full_portfolio.ps1` ainda define `OMEGA_24X7_ATIVOS` fixo | Comentar lista (igual T-W1) ou documentar “só restart manual CEO” | Baixa |
| BK-4 | `run_p0_smoke_ceo.ps1` fix PowerShell stderr | Verificar commitado na branch P0 ou Router | Média |
| BK-5 | Inventário 23/05 em branch Router | Actualizar após SM-R (F-A smoke vivo) | Baixa |

### 4.3 Variáveis de ambiente obrigatórias (qualquer smoke)

```powershell
$env:PYTHONPATH = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:PYTHONIOENCODING = "utf-8"
```

### 4.4 Conta e risco (CEO — não alterar sem ordem)

| Parâmetro | Valor smoke |
|-----------|-------------|
| MT5 login referência | 510075151 (HantecMarketsMU-MT5) |
| Modo | `--mode paper` |
| Magic | 234001 |
| Comment mark | `OV2\|` |
| Equity smoke | 10000 (parâmetro CLI) |

### 4.5 Falhas diagnosticadas — mapa de fases (não re-investigar)

| ID | Sintoma | Fase responsável | Estado código |
|----|---------|------------------|---------------|
| Falha A | SL ~$2.50 XAUUSD (ATR M1) | Fase 1 T-R1 | ✅ Corrigido UT-R1 |
| Falha B | Cascata entrada tardia | Fase 2 | Pendente |
| Falha C | M1-GATE atraso | Fase 2 | Pendente |
| Falha D | v2 SL hard-coded | Fase 3 | v2 inactivo no runner |

---

## 5. BLOCO FINAL PSA — checklist executável (fechar sprint)

Marcar ☑ quando concluído. **Chave de ouro = todos F1–F3 + F4 críticos.**

### F1 — Git push Router (5 min)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout feat/execution-router-atr-20260523
git log -1 --oneline
git push -u origin feat/execution-router-atr-20260523
```

☐ Push OK — URL branch no GitHub confirmada

---

### F2 — Smoke SM-R1..R3 (30–90 min)

**Pré-condição:** MT5 aberto; **sessão com liquidez** (evitar feriado US); 0 posições OMEGA.

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout feat/execution-router-atr-20260523
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"

python scripts/check_positions_now.py

python -u core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H4 --equity 10000
```

| ID | PASS se |
|----|---------|
| SM-R1 | Log: `get_execution_tf_atr` / `tf=H4`; ciclo exit 0 |
| SM-R2 | Se ordem executar: `sl_pts` ≥ 2000 ou SL USD ≥ **$20** no PaperReport/log |
| SM-R3 | Se ordem: `tp_pts` ≥ 2 × `sl_pts` |

**Se EDGE_GATE bloquear de novo:** documentar no relatório; repetir em sessão Londres/NY normal; **não** marcar FAIL de código se UT-R1 PASS.

Criar pasta: `audit/smoke/PSA_ENTREGA_SMOKE_ROUTER_20260525/` com:
- `00_RESUMO_SM-R.md`
- `01_log_xauusd_h4.log`
- `02_positions_pre_pos.txt`

☐ SM-R1 PASS  
☐ SM-R2 PASS ou N/A documentado + data re-test  
☐ SM-R3 PASS ou N/A ligado a SM-R2  

---

### F3 — Relatório Router (15 min)

**Criar:** `governance/PSA_RELATORIO_ROUTER_ATR_20260523.md`

Secções mínimas:

1. Git (branch, HEAD, CODE_SHA3 do smoke)  
2. T-F1a / T-R1 / T-R1b — PASS + linha código  
3. UT-R1..R5 — tabela PASS  
4. SM-R1..R3 — tabela + log  
5. Veredito PSA: APROVADO / REPROVADO / CONDICIONAL  
6. Espaço AIC (vazio — AIC preenche após SM-R)

☐ Relatório criado e commitado  

---

### F4 — Correcções menores (10 min)

☐ BK-2: `run_p0_smoke_ceo.ps1` reconcile `--since "YYYY-MM-DD 00:00:00"`  
☐ BK-1: typos relatório P0 Sec. 7.8 (opcional mesmo commit)  
☐ pytest: `34/34 PASS` na branch Router após edits  

```powershell
python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py tests/test_router_atr_20260523.py -q
```

---

### F5 — Pull Requests (CEO autoriza merge)

| PR | Base | Head | Quando |
|----|------|------|--------|
| PR-1 P0 | `main` | `fix/cicc-remediation-p0-abc-20260522` | CEO OK — pode ser **agora** |
| PR-2 Router | `main` | `feat/execution-router-atr-20260523` | Após F2 SM-R PASS |

**Título sugerido PR-1:** `fix: P0-ABC CICC remediation (magic, 1pos, weekend, PositionManager)`  
**Título sugerido PR-2:** `feat: Router Fase 1 — ATR por signal_tf + partial_taken`

☐ PR-1 aberto — URL: _______________  
☐ PR-2 aberto — URL: _______________  
☐ Merge PR-1 — CEO autorizou em: ___/___/___  
☐ Merge PR-2 — CEO autorizou em: ___/___/___  

---

### F6 — Acta de fecho sprint (5 min)

**Criar:** `governance/OMEGA_SPRINT_P0_FASE1_FECHO_20260525.md`

Conteúdo: 10 linhas — datas, hashes, vereditos AIC, PRs, próximo sprint (Fase 2 ou TRE).

☐ Acta criada  

---

## 6. O que a AIC fará após PSA “CHAVE DE OURO COMPLETA”

| # | Entregável |
|---|------------|
| 1 | `AIC_VALIDACAO_ROUTER_ATR_FASE1_SMOKE_20260525.md` (se SM-R PASS) |
| 2 | Actualizar `P0_ABC_FECHO` + inventário com PR merged |
| 3 | Autorizar ou bloquear **Fase 2** |

---

## 7. pytest gate único (ambas as branches)

| Branch | Comando | Esperado |
|--------|---------|----------|
| P0 | `pytest tests/test_p0_abc_* tests/test_runner_* tests/test_order_magic_* -q` | 29 passed |
| Router | + `tests/test_router_atr_20260523.py` | **34 passed** |

---

## 8. Proibições finais (violação = rollback)

1. Merge Fase 2/3 sem mandato novo.  
2. `OMEGA_USE_V2=1` em produção.  
3. `run_omega_24x7.ps1` overnight sem SM-R PASS + CEO.  
4. Alterar magic ≠ 234001 sem documento CEO.  
5. Implementar TRE neste sprint.  
6. Declarar “produção Tier-0 operacional” sem SM-R.  

---

## 9. Veredito “Chave de Ouro” — critério

| Estado | Condição |
|--------|----------|
| **INCOMPLETO** | Falta F1, F2 ou F3 |
| **COMPLETO** | F1+F2+F3 ☑ + F4 pytest ☑ + PRs abertos (F5) |
| **INSTITUCIONAL** | COMPLETO + PR-1 merged + AIC smoke Router APROVADO |

---

## 10. Assinaturas (preencher no fecho)

| Papel | Nome | Data | OK |
|-------|------|------|-----|
| PSA executor | Devin | | |
| AIC Tech Lead | | 2026-05-25 | ☑ P0 + Fase1 código |
| CEO | | | |

---

*Documento único de fecho — Sprint OMEGA P0-ABC + Fase 1 Router/ATR — Chave de Ouro 2026-05-25*
