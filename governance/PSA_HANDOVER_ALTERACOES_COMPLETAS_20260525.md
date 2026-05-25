# PSA — DOCUMENTO OFICIAL HANDOVER COMPLETO E ATUALIZADO

| Campo | Valor |
|-------|--------|
| **Documento** | `PSA_HANDOVER_ALTERACOES_COMPLETAS_20260525.md` |
| **Versão** | v2.0 — 2026-05-25 21:15 UTC |
| **Para** | PSA (Devin) |
| **De** | AIC Tech Lead (execução CEO) |
| **Branch activa** | `feat/execution-router-atr-20260523` |
| **HEAD remoto** | `2517c8b` |
| **Regra de ouro** | **LER ESTE FICHEIRO ANTES DE EDITAR CÓDIGO** — não reimplementar itens ✅ |

---

## LOCALIZAÇÃO (caminhos absolutos)

| Cópia | Caminho |
|-------|---------|
| **Repositório (fonte)** | `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\governance\PSA_HANDOVER_ALTERACOES_COMPLETAS_20260525.md` |
| **Desktop Auditoria** | `C:\Users\Lenovo\Desktop\File Desktop\Arquivos Pendentes Auditoria\Pendente\Auditoria\PSA_HANDOVER_ALTERACOES_COMPLETAS_20260525.md` |
| **GitHub** | Branch `feat/execution-router-atr-20260523` — commit `2517c8b` |

**Comando PSA para sincronizar:**

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git fetch origin
git checkout feat/execution-router-atr-20260523
git pull origin feat/execution-router-atr-20260523
# Deve mostrar HEAD: 2517c8b
```

---

## 0. Mensagem CEO (obrigatória para PSA)

CEO exige **zero conflitos** entre componentes e **portfolio discovery completo** (16 símbolos) em conta DEMO.

Tudo neste documento **já está implementado, commitado e pushed**.  
PSA: **não** voltar a corrigir T-W2, ATR router, partial_taken, schedule, nem reintroduzir listas fixas em env.

**Runner 24×7:** CEO/AIC arrancaram `run_omega_24x7.ps1` em 2026-05-25 — ver secção 8.

---

## 1. Cronologia de commits (atualizada)

| Commit | Quem | Resumo |
|--------|------|--------|
| `c5f0f25` … `80ba4f2` | PSA | P0-ABC (13 tarefas, smoke PSA, UT-9 comment MT5) |
| `37ec0b4` | PSA | T-F1a `partial_taken` + T-R1 `get_execution_tf_atr(signal_tf)` |
| `796bded` | PSA | Chave de Ouro F2-F6 |
| `ac153e4` | PSA | Chave de Ouro fecho + PRs #1 #2 abertos |
| `818f627` | AIC | T-W2 schedule por ciclo; `omega_demo_go_live.ps1`; EDGE_METAL; doc CEO |
| **`2517c8b`** | AIC | **Portfolio discovery 16 símbolos**; `OMEGA_ASSET_PROFILE`; este handover |

**PRs (merge = CEO, não PSA):**

| PR | URL | Conteúdo |
|----|-----|----------|
| #1 | https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/1 | P0-ABC → `main` |
| #2 | https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/2 | Router/ATR + demo → `main` |

---

## 2. Índice de documentação relacionada (não duplicar trabalho)

| Ficheiro | Conteúdo |
|----------|----------|
| **Este ficheiro** | Inventário total de alterações + proibições PSA |
| `governance/CEO_GO_LIVE_DEMO_ZERO_CONFLITO_20260525.md` | Procedimento CEO arranque DEMO |
| `governance/PSA_MANDATO_FECHO_DEFINITIVO_CHAVE_OURO_20260525.md` | Mandato Chave de Ouro (PSA) |
| `governance/OMEGA_SPRINT_P0_FASE1_FECHO_20260525.md` | Acta fecho sprint P0+Fase1 |
| `governance/P0_ABC_FECHO_20260525.md` | Fecho P0-ABC |
| `governance/AIC_VALIDACAO_PSA_P0_ABC_20260525.md` | AIC aprova P0 |
| `governance/AIC_VALIDACAO_ROUTER_ATR_FASE1_20260525.md` | AIC aprova Router/ATR |
| `governance/AIC_VALIDACAO_CHAVE_OURO_SPRINT_20260525.md` | AIC aprova Chave de Ouro |
| `governance/PSA_RELATORIO_ROUTER_ATR_20260523.md` | Relatório PSA Router |
| `governance/OMEGA_MANDATO_UNIFICADO_P0_ROUTER_WEEKEND_20260523.md` | Mandato unificado P0+Router |

---

## 3. Alterações por ficheiro — NÃO REIMPLEMENTAR

### 3.1 Core / execução (PSA — commits `37ec0b4` … `80ba4f2`)

| Ficheiro | Alteração | ID |
|----------|-----------|-----|
| `core_engines/shadow_loop.py` | `get_execution_tf_atr(symbol, signal_tf, confidence)` — ATR do TF do sinal, **não M1** | T-R1 |
| `core_engines/shadow_loop.py` | `_pos_ledger` + `partial_taken` (4 inits + True após partial close ~L4480) | T-F1a |
| `core_engines/shadow_loop.py` | Call sites L3628, L4266, L4401; `sanitize_sl_tp` usa ATR do sinal | T-R1 |
| `core_engines/shadow_loop.py` | Comment MT5 ≤31 caracteres | UT-9 / `511e230` |
| `core_engines/shadow_loop.py` | `is_market_open` antes de fechos MT5 | T-W3 |
| `modules/mt5_position_tag.py` | Magic `234001`, comment mark `OV2\|` | P0 |

### 3.2 Runner / schedule / DEMO (AIC — `818f627` + `2517c8b`)

| Ficheiro | Alteração | ID / commit |
|----------|-----------|-------------|
| `scripts/omega_paper_loop_24x7.py` | Cada ciclo: `resolve_shadow_loop_assets(None, ROOT)` + log `[SCHEDULE]` | T-W2 / `818f627` |
| `scripts/run_omega_24x7.ps1` | `OMEGA_USE_V2=0`, `OMEGA_EDGE_METAL_ATR=0.0005`, equity MT5 real | DEMO / `818f627` |
| `scripts/run_omega_24x7.ps1` | `$env:OMEGA_ASSET_PROFILE = "ceo_discovery_full"` | `2517c8b` |
| `config/omega_asset_schedule.json` | v2: perfil `ceo_discovery_full` + weekday 16 símbolos + weekend crypto | `2517c8b` |
| `modules/omega_asset_schedule.py` | Leitura `OMEGA_ASSET_PROFILE` + campo meta `profile` | `2517c8b` |
| `scripts/restart_full_portfolio.ps1` | **Delega** para `run_omega_24x7.ps1` (sem `OMEGA_24X7_ATIVOS` fixo) | `2517c8b` |
| `scripts/omega_demo_go_live.ps1` | Pré-voo: pytest 34/34 + smokes + reconcile | `818f627` |

### 3.3 Testes (gate obrigatório antes de qualquer PR PSA)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py tests/test_router_atr_20260523.py -q
# Esperado: 34 passed
```

| Ficheiro teste | Testes |
|----------------|--------|
| `tests/test_p0_abc_20260522.py` | 29 (P0) |
| `tests/test_router_atr_20260523.py` | 5 (Router) |
| `tests/test_runner_targets_v1_only.py` | incluído no gate |
| `tests/test_order_magic_propagation.py` | incluído no gate |

---

## 4. Variáveis de ambiente activas (`run_omega_24x7.ps1`)

| Variável | Valor | Notas |
|----------|-------|-------|
| `OMEGA_ASSET_PROFILE` | `ceo_discovery_full` | 16 símbolos via schedule |
| `OMEGA_USE_V2` | `0` | P0 T-P2b — v2 proibido no runner |
| `OMEGA_EDGE_METAL_ATR` | `0.0005` | XAU passa EDGE em baixa vol DEMO |
| `OMEGA_MAGIC_NUMBER` | `234001` | (shadow_loop default) |
| `OMEGA_MAX_POS_PER_ASSET` | `1` | CEO fix |
| `OMEGA_MAX_POSITIONS` | `8` | DEMO |
| `OMEGA_24X7_MODE` | `paper` | |
| `OMEGA_DECISION_TRACE` | `1` | `audit/paper/decision_trace.jsonl` |
| `OMEGA_LOOP_INTERVAL_SEC` | `20` | |
| **`OMEGA_24X7_ATIVOS`** | **(não definir)** | Lista fixa = conflito T-W1 |

---

## 5. Portfolio discovery — 16 símbolos oficiais

```
EURUSD GBPUSD USDJPY AUDUSD USDCAD XAUUSD US500 US100
BTCUSD ETHUSD SOLUSD XRPUSD AVAXUSD ADAUSD LTCUSD BNBUSD
```

- Broker: Hantec DEMO (`US100` = NAS100).  
- Timeframes runner: `H1 M15 H4`.  
- OHLCV: 16 × 3 TFs por ciclo (~48 exports).

---

## 6. O que PSA NÃO deve fazer

| Acção proibida | Motivo |
|----------------|--------|
| Re-adicionar `$env:OMEGA_24X7_ATIVOS` fixo em PS1 | Bypassa T-W1/T-W2 |
| Activar `OMEGA_USE_V2=1` no runner | Regressão P0 |
| Reverter ATR para M1 em SL/TP | Regressão Falha A (T-R1) |
| Reimplementar T-W2 | Já em `818f627` |
| Restaurar `restart_full_portfolio` com lista env antiga | Substituído em `2517c8b` |
| Segunda instância 24×7 sem parar a primeira | Lock singleton `omega_runner.lock` |

---

## 7. Arranque e monitorização (CEO / PSA verificação)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git pull origin feat/execution-router-atr-20260523
& .\scripts\run_omega_24x7.ps1
# Equivalente CEO:
& .\scripts\restart_full_portfolio.ps1
```

**Pré-voo (opcional, recomendado após pull):**

```powershell
& .\scripts\omega_demo_go_live.ps1
```

**Log:** `audit\paper\omega_24x7_runner.log`  
**Marcadores OK:** `[SCHEDULE]`, 16 ativos, `legacy_magic=234001`, **sem** `Invalid comment`.

---

## 8. Evidências de validação (2026-05-25)

| Verificação | Resultado |
|-------------|-----------|
| pytest 34/34 | PASS |
| `omega_demo_go_live.ps1` | PASS (EURUSD H1×2, XAUUSD H4, reconcile ALL PASS) |
| MT5 DEMO | `510075151` / HantecMarketsMU-MT5 |
| Posições órfãs OMEGA | 0 |
| Runner ciclo 1 discovery | OK — 16 símbolos, export 48/48, shadow_rc=0 |
| Relatório pré-voo | `audit/demo_go_live/GO_LIVE_REPORT_20260525_204139.txt` |

---

## 9. Estado de fecho (para CEO e PSA)

| Item | Estado |
|------|--------|
| P0-ABC código | ✅ Fechado (PSA) |
| Fase 1 Router/ATR | ✅ Fechado (PSA) |
| Chave de Ouro | ✅ `ac153e4` |
| T-W2 + pré-voo | ✅ `818f627` |
| Portfolio discovery 16 | ✅ `2517c8b` |
| Handover PSA | ✅ **Este documento v2.0** |
| Merge PR #1 #2 | ⏳ CEO (GitHub) |
| Fase 2 / TRE | Mandato futuro — não reabrir sem CEO |
| SM-R2 ordem vivo SL≥$20 | Mercado/gates — discovery activo |

---

## 10. Diff útil para PSA (antes de editar)

```powershell
git diff 818f627..2517c8b --stat
git diff 818f627..2517c8b -- config/ modules/omega_asset_schedule.py scripts/
```

---

## 11. Contacto / escalamento

- Conflito com código deste handover → **não alterar**; reportar CEO com diff.  
- Novo feature (Fase 2, TRE) → **novo mandato** separado.  
- Bug novo com evidência log → branch fix a partir de `2517c8b`, pytest 34/34 obrigatório.

---

*PSA HANDOVER v2.0 — AIC — 2026-05-25 — HEAD `2517c8b` — documento completo e atualizado.*
