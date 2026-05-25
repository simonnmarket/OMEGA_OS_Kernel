# PSA — Mandato de Execução Obrigatório (P0 ABC)

---

## AUTORIZAÇÃO CEO (literal — vigência imediata)

> **“PSA autorizado a executar Sec. 5–8 deste mandato (versão 2.0), incluindo todas as tarefas T-D* e T-P* listadas como OBRIGATÓRIAS. Não é permitido marcar DEFERRED salvo excepção escrita do CEO. Após conclusão, validação AIC + CEO.”**
>
> — CEO, 2026-05-22  
> — AIC Tech Lead (emissão técnica do mandato)

---

| Campo | Valor |
|-------|--------|
| **Documento** | PSA-MANDATO-P0-ABC-20260522 |
| **Versão** | **2.0** (pacote completo — sem P1/F “para depois”) |
| **Classificação** | EXECUTÁVEL — sem margem de interpretação |
| **Emitente** | CEO + AIC Tech Lead |
| **Executor único** | PSA (Production Systems Agent) |
| **Repositório** | `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE` |
| **Branch obrigatória** | `fix/cicc-remediation-p0-abc-20260522` (criar a partir de `fix/cicc-remediation-magic-mutex-20260520` ou `HEAD` documentado) |
| **Motor em escopo** | **`core_engines/shadow_loop.py` (v1) APENAS** para produção 24×7 |
| **Validação pós-execução** | CEO + AIC (read-only) — **não** auto-validar como “concluído” |

---

## 0. Declaração de conformidade (PSA deve aceitar antes de codar)

Ao iniciar, PSA declara por escrito (no relatório final, Sec. 1):

1. Li este mandato **na íntegra**.
2. **Não** alterarei escopo sem aprovação CEO.
3. **Não** considerarei a tarefa concluída se **qualquer** critério **OBRIGATÓRIO** da Sec. 8 estiver em FAIL.
4. Entregarei **todos** os artefactos da Sec. 7 — sem excepção.
5. Pararei runner 24×7 e `omega_v550` antes de testes (Sec. 4).

**Proibido:** marcar “feito” com base em intenção, plano, ou self-test Tier-0 (26/26) — **inactivo** no pipeline de trading (inventário C-07).

---

## 1. Objetivo mensurável

Corrigir **100%** dos itens **OBRIGATÓRIOS** abaixo, de forma que um **smoke test** objetivo (Sec. 8) passe **sem FAIL**, e o relatório PSA (Sec. 7) permita auditoria AIC/CEO sem ambiguidade.

| Meta | Critério de sucesso global |
|------|---------------------------|
| Visibilidade de posição | ≤1 posição OMEGA por `(symbol, direction)` após 1 ciclo smoke |
| Execução real | 0 ordens com `fill_price≤0` ou `ticket≤0` registadas como sucesso |
| Breakeven | SL após BE ≠ `entry` exacto (buffer ≥ 1.5× spread) |
| PnL governance | G5 reconcile PASS OU campo alinhado documentado |
| Rastreio | Commit + diff + relatório + logs de prova |

---

## 2. Escopo IN / OUT

### 2.1 IN (obrigatório)

| ID inventário | Tarefa mandato |
|---------------|----------------|
| A-01, A-02, A-03, A-04, A-05 | **T-D1** |
| B-01, B-02 | **T-D2** |
| B-03, B-04 | **T-D3** |
| B-09 | **T-D4** |
| B-11 | **T-D4b** (ligar PositionManager) |
| B-05, B-07 | **T-P1a** + **T-D5** (XAUUSD SL/TP + partial TP) |
| X-03 | **T-P1b** (cache guardrail) |
| X-02 | **T-P1c** (anti_hedge em qualquer posição no símbolo) |
| X-01 | **T-P2c** (tabela reconciliação PnL) |
| C-01 | **T-P2b** (runner só v1; v2 bloqueado) |
| — | **T-P2a** (smoke 3 ativos após smoke unitário) |
| B-06 | **T-P2b** espelho D3 em `shadow_loop_v2.py` (sem activar runner) |

### 2.2 OUT (proibido neste mandato)

| Item | Motivo |
|------|--------|
| Refactor geral `shadow_loop.py` | Minimizar diff |
| Activar `shadow_loop_v2` no runner 24×7 | C-03 inactivo |
| Alterar `main.py` BAU | Fora do caminho madrugada |
| “Resolver” apenas em `shadow_loop_v2` | Não é produção |
| Novo ciclo portfolio 32 ativos **antes** Sec. 8 PASS | Gera ruído |
| Merge para `main` sem assinatura CEO+AIC | Processo |
| Marcar **DEFERRED** em qualquer tarefa Sec. 5–8 | **PROIBIDO** (salvo email CEO) |
| Investigar/implementar `omega_quantum_brain` / harmonic neste mandato | Relatório **T-E0** só 1 página diagnóstico (Sec. 7.9) |

### 2.3 Política “zero pendente”

| Regra | Texto |
|-------|--------|
| Obrigatoriedade | **Todas** as tarefas Sec. 5 (T-D* + T-P*) são **OBRIGATÓRIAS** |
| DEFERRED | **Proibido** por omissão. Só com **excepção escrita CEO** citada no relatório Sec. 7.10 |
| Conclusão PSA | Só válida se Sec. 8 **100% PASS** (inclui UT-5..8, SM-6..8, P2a, P2c) |

---

## 3. Mapa de ficheiros (única fonte de verdade)

| Ficheiro | Alteração permitida |
|----------|---------------------|
| `core_engines/shadow_loop.py` | **SIM** — principal |
| `modules/mt5_position_tag.py` | **SIM** — tracking paper |
| `core_engines/position_manager.py` | **SIM** — wiring D4b |
| `scripts/psa_position_pnl_reconcile.py` | **SIM** — só se opção B em D4 |
| `state/omega_open_tickets.json` | **CRIAR** — persistência D1 |
| `tests/test_p0_abc_20260522.py` | **CRIAR** — UT-1..7 |
| `tests/test_runner_targets_v1_only.py` | **CRIAR** — T-P2b |
| `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` | **PREENCHER** — modelo em Desktop Auditoria |
| `core_engines/shadow_loop_v2.py` | **SIM** — só D3 espelho; runner **inactivo** |

---

## 4. Pré-condições (gate — todos PASS antes de editar código)

| # | Acção | Comando / verificação | Evidência no relatório |
|---|--------|----------------------|------------------------|
| P1 | Parar runner 24×7 | Ver script Sec. 4.1 — PSA **pode** executar PowerShell | Output `Get-CimInstance` antes/depois |
| P2 | **omega_v550 OFF** | Idem Sec. 4.1 | Idem |
| P4 | Branch | PSA **cria** `fix/cicc-remediation-p0-abc-20260522` a partir do branch actual | `git branch --show-current` |
| P3 | MT5 terminal aberto, conta paper | `mt5.account_info()` login | Log |
| P4 | Branch criada | `git branch --show-current` | Nome branch |
| P5 | Baseline commit | `git rev-parse HEAD` | Hash |
| P6 | Backup estado | Copiar `audit/paper/trade_feedback.jsonl` → `audit/paper/backup_pre_p0abc_*` | Path |

**FAIL em qualquer P1–P6 → STOP. Não commitar.**

### 4.1 Script PowerShell — PSA pode executar (P1 + P2)

```powershell
# Listar processos OMEGA antes de parar
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'shadow_loop|omega_paper_loop|omega_v550' } |
  Select-Object ProcessId, @{N='Cmd';E={$_.CommandLine.Substring(0,[Math]::Min(120,$_.CommandLine.Length))}}

# Parar (confirmar lista antes; CEO pode ter janela PS1 aberta — fechar CTRL+C também)
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'shadow_loop\.py|omega_paper_loop_24x7|omega_v550' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Verificar zero
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'shadow_loop|omega_paper_loop|omega_v550' }
# (deve retornar vazio)

# Branch P4
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout -b fix/cicc-remediation-p0-abc-20260522
git branch --show-current
```

Se `Stop-Process` falhar (permissão): CEO fecha janela `run_omega_24x7.ps1` manualmente; PSA regista no relatório e **não** inicia smoke até P1/P2 PASS.

---

## 5. Tarefas técnicas — especificação não subjetiva

### T-D1 — 1POS / visibilidade (OBRIGATÓRIO) — fecha A-*

**Problema:** `is_omega_tracked_position()` retorna False quando `comment="Request executed"` e `magic=None` em `positions_get()`.

**Implementação mínima obrigatória (duas camadas — ambas):**

#### D1-A — Persistência de tickets entre ciclos

| Requisito | Especificação |
|-----------|---------------|
| Ficheiro | `state/omega_open_tickets.json` |
| Formato | `{ "<ticket>": { "symbol": str, "direction": "BUY"\|"SELL", "opened_at_utc": iso, "entry_deal": int\|null } }` |
| Escrever | Após `mt5_send_order` **sucesso** com `deal>0` e `fill_price>0` |
| Remover | Quando posição fechada (ledger close ou `ticket` ausente em `positions_get`) |
| Carregar | Início de cada `run_loop` / ciclo |

#### D1-B — Função `has_omega_exposure(symbol, direction)` (ou equivalente)

| Requisito | Especificação |
|-----------|---------------|
| Entrada | `symbol`, `direction` |
| True se | (1) existe posição MT5 no símbolo+direção **OU** (2) ticket em `omega_open_tickets.json` para mesmo símbolo+direção **validado** contra MT5 |
| Uso | Substituir / complementar contagens que usam **só** `filter_omega_tracked_positions` em: ~L2778 `MAX_POS_PER_ASSET`, ~L3403 pyramid gate, ~L3564 antes de ordem |

#### D1-C — `mt5_position_tag.py` — fallback paper

| Requisito | Especificação |
|-----------|---------------|
| Se | `comment` contém `"Request executed"` **e** `ticket in load_open_tickets()` |
| Então | `is_omega_tracked_position` → **True** |
| Alternativa aceite | Tratar `magic==234001` em `positions_get` se broker passar magic — **testar e documentar** |

**Proibido:** apenas comentar código sem alterar comportamento.

**Teste unitário obrigatório:** mock position `comment="Request executed", magic=None` + ticket no state → `has_omega_exposure` True.

---

### T-D2 — Breakeven buffer (OBRIGATÓRIO) — fecha B-01, B-02

**Local:** `shadow_loop.py` ~L4324-4332 (`MOVE_SL_TO_ENTRY`).

| Requisito | Especificação |
|-----------|---------------|
| Antes | `_entry_be = entry_price` (exacto) |
| Depois | `buffer = symbol_spread_points * point * 1.5` (mínimo 2× point se spread=0) |
| BUY | `sl_new = entry - buffer` (SL abaixo entry — lucro mínimo garantido) |
| SELL | `sl_new = entry + buffer` |
| Log | `[BREAKEVEN] ticket=… old_sl=… new_sl=… buffer_pts=…` |

**Critério:** `abs(new_sl - entry) >= buffer` — nunca igual a entry.

---

### T-D3 — Ghost orders (OBRIGATÓRIO) — fecha B-03, B-04

**Locais:** `mt5_send_order` retorno; bloco ~L4044-4055; gravação `PaperReport_*` ~L4197.

| Requisito | Especificação |
|-----------|---------------|
| `success=True` **apenas se** | `deal`/`order` ticket **> 0** **e** `fill_price` **> 0** **e** `retcode` em conjunto OK existente |
| Se fail | `success=False`, `reason_for_skip` ou `error_code` = `FILL_ZERO` ou `TRADE_DISABLED` |
| PaperReport | **Não** gravar `status: EXEC` se D3 fail |
| Retcode 10027 | Tratar como FAIL; opcional: blacklist símbolo no ciclo |

**Teste unitário:** simular `{success: True, fill_price: 0, deal: 0}` → deve normalizar para FAIL.

---

### T-D4 — Schema G5 PnL (OBRIGATÓRIO) — fecha B-09

**Escolher UMA opção — declarar no relatório:**

| Opção | Acção | Critério |
|-------|-------|----------|
| **D4-A (preferida)** | Em `trade_feedback_append` payload fecho: adicionar `"total_realized_pnl": <float>` igual a soma realizada da posição | G5 script PASS |
| **D4-B** | Alterar `psa_position_pnl_reconcile.py` a usar `pnl` se `total_realized_pnl` ausente | G5 PASS + teste |

**Proibido:** deixar reconcile a ler campo sempre 0 sem documentar.

---

### T-D4b — PositionManager wiring (OBRIGATÓRIO) — fecha B-11

| Requisito | Especificação |
|-----------|---------------|
| Importar | `PositionManager` de `core_engines/position_manager.py` |
| OPEN | Após entrada confirmada D3 |
| PARTIAL / CLOSE | Nos mesmos pontos que `trade_feedback_append` hoje |
| Feedback | Uma linha por `position_ticket` com `total_realized_pnl` (alinha D4) |

**Critério:** teste existente `tests/test_order_magic_propagation.py` continua PASS; adicionar teste mínimo open→close→feedback.

---

### T-P1a — XAUUSD SL/TP (OBRIGATÓRIO) — fecha B-05

| Requisito | Especificação |
|-----------|---------------|
| Perfil | `ASSET_PROFILES["XAUUSD"]` — alterar `sl_pts_min`: **150 → 1500** (L571) |
| `sanitize_sl_tp` + ordem | `eff_sl = max(sl_pts, atr_pts * MIN_SL_ATR_MULT, profile["sl_pts_min"])` no **TF da ordem** |
| ATR | Usar **mesmo TF** da ordem (H1/M15/H4) — **proibido** ATR M5 para sinal H4 sem log WARNING |
| TP mínimo | `eff_tp / eff_sl >= 2.0` para XAUUSD |
| Distância mínima USD | `eff_sl * point >= 15.0` USD (1500 pts × 0.01) — log `[XAUUSD_SL_FLOOR]` |

> **Nota CEO/AIC (v2.0 erratum):** 150 pts = ~$1.50 — insuficiente (auditoria deep). **1500 pts ≈ $15** alinha com escala v2 e range intraday.

**Teste UT-5:** mock XAUUSD com ATR baixo → `eff_sl >= 1500`.

**Smoke SM-6:** 1 ciclo paper `XAUUSD` H1 — PaperReport regista `sl_pts >= 1500` (ou distância USD ≥ $15).

---

### T-D5 — Partial take-profit 50% (OBRIGATÓRIO) — fecha B-07

| Requisito | Especificação |
|-----------|---------------|
| Função | **`mt5_close_partial` já existe** — `shadow_loop.py` ~L1520; wiring ~L4304–4320 |
| Engine | `ProgressivePartialCloseComplete` — `modules/risk_valves_v31.py` (1º nível **0.7×ATR**, 50%) |
| Tarefa PSA | Garantir engine inicializado por ticket; 1º `CLOSE_PARTIAL` executa; `partial_taken` no `_pos_ledger` |
| Log | `[PARTIAL_CLOSE]` ou `[PARTIAL_TP50] ticket=… vol=…` |
| BE | T-D2 corrige `MOVE_SL_TO_ENTRY` (buffer spread) — não duplicar com entry exacto |

**Teste UT-6:** mock `check_partials` com `move_atr >= 0.7` → ordem `CLOSE_PARTIAL` 50%.

---

### T-P1b — Cache guardrail (OBRIGATÓRIO) — fecha X-03

| Requisito | Especificação |
|-----------|---------------|
| Local | `check_guardrails` / loop ~L2742 |
| TTL | **60s** por chave `{asset}_{tf}_{skip_reason_hash}` |
| Critério | Em 2 ciclos seguidos BTCUSD M15 mesmo skip → **1** avaliação completa + N-1 cache hits logados |
| Log | `[GUARDRAIL_CACHE_HIT]` |

**Teste UT-7:** duas chamadas <60s → segunda retorna cache.

---

### T-P1c — Anti-hedge real (OBRIGATÓRIO) — fecha X-02

| Requisito | Especificação |
|-----------|---------------|
| Escopo **paper/smoke** | `mt5.positions_get(symbol=asset)` — **qualquer** posição no símbolo (já ~L3095–3419) |
| 1POS (T-D1) | Usa `state/omega_open_tickets.json` + exposure — **camada separada** |
| Produção manual | Fora do smoke; em conta com trades manuais, CEO pode activar depois `OMEGA_ANTI_HEDGE_OMEGA_ONLY=1` — **não** neste P0 |
| Log | `[ANTI_HEDGE] symbol=… existing=… new=…` |

**Smoke SM-7:** com BUY aberto em EURUSD (paper), tentativa SELL → `SKIP_ANTI_HEDGE`.

---

### T-P2a — Smoke portfolio reduzido (OBRIGATÓRIO)

Após SM-1..SM-7 PASS, executar **1 ciclo** cada:

```powershell
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD GBPJPY XAUUSD --timeframes H1 --equity 10000
```

| ID | PASS se |
|----|---------|
| P2a-1 | exit 0 |
| P2a-2 | 0 hedges nos 3 ativos (BUY+SELL simultâneo) |
| P2a-3 | ≤1 posição por (ativo, direcção) |

---

### T-P2b — Lock v1 / v2 (OBRIGATÓRIO)

| Requisito | Especificação |
|-----------|---------------|
| Confirmar | `omega_paper_loop_24x7.py` aponta só para `shadow_loop.py` |
| Teste | `tests/test_runner_targets_v1_only.py` — falha se runner referenciar v2 |
| v2 | Aplicar **mesmo** fix D3 (fill validation) em `shadow_loop_v2.py` L627 — **sem** activar no runner |
| CI/doc | Comentário em `run_omega_madrugada_pos_p0.ps1`: `# OMEGA_USE_V2=0 — PROIBIDO` |

---

### T-P2c — Tabela reconciliação PnL (OBRIGATÓRIO) — fecha X-01

No relatório PSA Sec. 7.8, preencher **na mesma janela UTC** do smoke:

| Métrica | Valor | Fonte |
|---------|-------|-------|
| Δ Equity | | `omega_v550_realtime.log` ou account |
| Σ deals.profit | | export MT5 ou API |
| Σ feedback.pnl / total_realized_pnl | | `trade_feedback.jsonl` |
| Explicação divergência | | 1 parágrafo objetivo |

**PASS:** tabela preenchida — não precisa ser um único número, precisa **explicar** diferenças.

---

## 6. Ordem de execução (obrigatória)

```text
P1–P6 pré-condições
  → T-D1 → T-D3 → T-D2 → T-D4 → T-D4b
  → T-P1a → T-D5 → T-P1b → T-P1c
  → testes UT-1..7 (Sec. 8.1)
  → smoke SM-1..7 (Sec. 8.2)
  → T-P2a (smoke 3 ativos)
  → reconcile + T-P2c tabela (Sec. 8.3)
  → T-P2b teste runner
  → relatório PSA preenchido (Sec. 7)
  → commit(s) + cópia relatório para Desktop Auditoria
```

**Proibido:** portfolio 32 ativos (`run_omega_madrugada_pos_p0.ps1`) antes de **100%** Sec. 8 PASS.

---

## 7. Entregáveis obrigatórios (PSA)

Ficheiro: `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md`

### 7.1 Secções obrigatórias

| Sec | Título | Conteúdo mínimo |
|-----|--------|-----------------|
| 1 | Declaração conformidade | Sec. 0 deste mandato |
| 2 | Git | branch, commits (hash), ficheiros tocados |
| 3 | Diff resumo | Uma linha por T-D* |
| 4 | Tabela critérios | Sec. 8 — cada linha PASS/FAIL + evidência |
| 5 | Logs smoke | Colar últimas 50 linhas relevantes |
| 6 | Reconcile G3-G5 | Output completo comando Sec. 8.3 |
| 7.8 | Tabela PnL T-P2c | Preenchida |
| 7.9 | Diagnóstico 1 página | Quantum/harmonic **não alterados** — impacto em entradas (read-only) |
| 7.10 | Excepções CEO | Só se houver DEFERRED autorizado (senão “Nenhuma”) |
| 8 | Pedido validação AIC+CEO | |

### 7.2 Artefactos adicionais

| Artefacto | Path |
|-----------|------|
| Testes | `tests/test_p0_abc_20260522.py` |
| Estado exemplo | `state/omega_open_tickets.json` (pode estar vazio `{}`) |
| Backup | `audit/paper/backup_pre_p0abc_*` |

---

## 8. Critérios de aceitação — checklist objetivo (100% OBRIGATÓRIO = PASS)

AIC/CEO marcam PASS/FAIL — PSA **não** auto-assina.

### 8.1 Testes automáticos (todos devem PASS)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = "utf-8"
python -m pytest tests/test_p0_abc_20260522.py -v
python -m pytest tests/test_order_magic_propagation.py -v
```

| ID | Teste mínimo |
|----|----------------|
| UT-1 | `Request executed` + ticket em state → exposure True |
| UT-2 | fill_zero → not success |
| UT-3 | breakeven buffer ≠ entry |
| UT-4 | feedback contém `total_realized_pnl` em close |
| UT-5 | XAUUSD `eff_sl >= sl_pts_min` (1500) |
| UT-6 | partial TP50 trigger |
| UT-7 | guardrail cache 60s |

**FAIL em qualquer UT → mandato INCOMPLETO.**

### 8.2 Smoke MT5 (OBRIGATÓRIO)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000
```

| ID | Critério | PASS se |
|----|----------|---------|
| SM-1 | 1 ciclo completa | exit code 0 |
| SM-2 | Máximo 1 posição EURUSD por direção | `positions_get` + state |
| SM-3 | Segundo ciclo imediato mesma direção | SKIP log contém `1pos` ou `MAX_POS` ou `already` — **não** segunda ordem |
| SM-4 | Nenhum PaperReport EXEC com fill=0 | grep relatório JSON |
| SM-5 | Se BE aplicado | SL ≠ entry em log |

| SM-6 | XAUUSD H1 1 ciclo | `sl` distance ≥ floor (UT-5) |
| SM-7 | anti_hedge | SELL bloqueado com BUY aberto (setup manual ou ciclo prévio) |

### 8.2b Smoke portfolio (OBRIGATÓRIO — T-P2a)

| ID | Critério | PASS se |
|----|----------|---------|
| P2a-1 | EURUSD+GBPJPY+XAUUSD 1 ciclo H1 | exit 0 |
| P2a-2 | Sem hedges | 0 símbolos com BUY e SELL |
| P2a-3 | 1POS efectivo | ≤1 posição/(ativo,direcção) |

### 8.3 Reconcile (OBRIGATÓRIO após smoke com ≥1 fecho)

```powershell
$env:PYTHONIOENCODING = "utf-8"
python scripts/psa_position_pnl_reconcile.py --since "YYYY-MM-DD HH:MM:SS"
```

| Gate | PASS |
|------|------|
| G3 magic | 0 bad magic OUT |
| G4 UNKNOWN | 0 UNKNOWN |
| G5 PnL diff | 0 positions diff > 0.01 USD |
| P0-8 R | ≥ 0.98 |

Se smoke não fechar posição: documentar + G5 “N/A smoke” com plano de fecho manual — **requer aprovação AIC**.

### 8.4 Regressão magic (OBRIGATÓRIO — não regredir B-10)

| ID | Critério |
|----|----------|
| REG-1 | Ordens novas usam `OMEGA_MAGIC` 234001 e comment `OV2|…` em **order_send** (já P0) |
| REG-2 | Deals OUT mantêm magic 234001 |

---

## 9. Proibições explícitas (violação = mandato falhado)

1. Declarar concluído com G5 FAIL sem aprovação escrita CEO.  
2. Correr `run_omega_madrugada_pos_p0.ps1` portfolio completo antes Sec. 8 PASS.  
3. Deixar `omega_v550` a correr durante smoke.  
4. Mudar runner para `shadow_loop_v2.py`.  
5. Apagar `trade_feedback.jsonl` sem backup P6.  
6. Commit secrets ou `.env` credenciais.  
7. “Fix” que só altera logs sem alterar comportamento.  

---

## 10. Validação CEO + AIC (pós-PSA)

AIC executará **apenas leitura**:

| Passo | Acção AIC |
|-------|-----------|
| V1 | Verificar branch + diff vs este mandato |
| V2 | Re-correr UT-1..7 + `test_runner_targets_v1_only` |
| V3 | Verificar SM-1..7 + P2a-1..3 (log ou smoke repetido) |
| V4 | Re-correr reconcile + Sec. 7.8 PnL |
| V5 | Atualizar `OMEGA_INVENTARIO_CONSOLIDADO_ABC` coluna **Resolvido** |
| V6 | Veredito: **APROVADO** / **REPROVADO** (sem “APROVADO COM DEFERRED” salvo excepção CEO Sec. 7.10) |

**Documento AIC:** `AIC_VALIDACAO_PSA_P0_ABC_20260522.md` (AIC gera após PSA).

**Cópia obrigatória do relatório preenchido para:**  
`C:\Users\Lenovo\Desktop\File Desktop\Arquivos Pendentes Auditoria\Pendente\Auditoria\PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md`

---

## 12. Matriz inventário → tarefa → evidência (completa)

| ID | Tarefa | Evidência de fecho |
|----|--------|-------------------|
| A-01..05 | T-D1 | UT-1, SM-2, SM-3, P2a-3 |
| B-01, B-02 | T-D2 | UT-3, SM-5 |
| B-03, B-04 | T-D3 | UT-2, SM-4 |
| B-09 | T-D4 | UT-4, G5 |
| B-11 | T-D4b | UT-4 + PM |
| B-10 | REG | REG-1, REG-2 |
| B-05 | T-P1a | UT-5, SM-6 |
| B-07 | T-D5 | UT-6 |
| X-03 | T-P1b | UT-7 |
| X-02 | T-P1c | SM-7 |
| X-01 | T-P2c | Sec. 7.8 tabela |
| C-01, C-03 | T-P2b | teste runner + doc |
| — | T-P2a | P2a-1..3 |

---

## 13. Frase de encerramento (PSA)

> “Mandato PSA-MANDATO-P0-ABC-20260522: todos os critérios **OBRIGATÓRIOS** Sec. 8 em **PASS**. Artefactos Sec. 7 entregues. Aguardando validação AIC/CEO.”

Qualquer outra formulação (“pronto para produção”, “100% operacional”) **sem** tabela Sec. 8 = **inválido**.

---

*Documento emitido por AIC Tech Lead sob direcção CEO — 2026-05-22*
