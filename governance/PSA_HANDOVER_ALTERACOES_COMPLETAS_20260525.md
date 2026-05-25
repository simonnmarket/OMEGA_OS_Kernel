# PSA — Handover completo de alterações (AIC + commits 2026-05-25)

| Campo | Valor |
|-------|--------|
| **Para** | PSA (Devin) |
| **De** | AIC Tech Lead + CEO mandato |
| **Branch** | `feat/execution-router-atr-20260523` |
| **Commits chave** | `ac153e4` (Chave Ouro) → `818f627` (demo T-W2) → **próximo** (discovery full) |
| **Regra** | **NÃO reimplementar** itens marcados ✅ abaixo |

---

## 0. Mensagem CEO (obrigatória)

CEO exige **zero pendências operacionais** e **portfolio discovery completo** antes de colher lucro em DEMO.  
Todas as alterações deste documento já estão no repositório local/remoto — PSA deve **ler, não duplicar**.

---

## 1. Inventário de commits (cronologia)

| Commit | Autor/contexto | Conteúdo |
|--------|----------------|----------|
| `c5f0f25` … `80ba4f2` | PSA | P0-ABC (13 tarefas, smoke, UT-9 comment) |
| `37ec0b4` | PSA | T-F1a `partial_taken` + T-R1 `get_execution_tf_atr` |
| `796bded` / `ac153e4` | PSA | Chave de Ouro F2-F6 |
| `818f627` | AIC | T-W2 re-resolve schedule; `omega_demo_go_live.ps1`; EDGE_METAL; doc CEO |
| **HEAD+1** | AIC | Portfolio discovery 16 símbolos; `OMEGA_ASSET_PROFILE`; PSA handover |

**PRs abertos (CEO merge):**

- https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/1 — P0 → main  
- https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/2 — Router → main  

---

## 2. Alterações por ficheiro (NÃO repetir)

### 2.1 Core / execução (PSA — já em branch)

| Ficheiro | Alteração | ID |
|----------|-----------|-----|
| `core_engines/shadow_loop.py` | `get_execution_tf_atr(symbol, signal_tf, confidence)` — ATR do TF do sinal, não M1 | T-R1 |
| `core_engines/shadow_loop.py` | `_pos_ledger` + `partial_taken` (4 inits + True após partial close) | T-F1a |
| `core_engines/shadow_loop.py` | Call sites L3628, L4266, L4401; `sanitize_sl_tp` usa ATR sinal | T-R1 |
| `core_engines/shadow_loop.py` | Comment MT5 ≤31 chars (`511e230`) | UT-9 |
| `core_engines/shadow_loop.py` | `is_market_open` antes de fechos | T-W3 |
| `modules/mt5_position_tag.py` | Magic 234001, tag `OV2\|` | P0 |

### 2.2 Runner 24×7 (AIC — 818f627 + discovery)

| Ficheiro | Alteração | ID |
|----------|-----------|-----|
| `scripts/omega_paper_loop_24x7.py` | Cada ciclo: `resolve_shadow_loop_assets(None)` → log `[SCHEDULE]` | **T-W2** ✅ |
| `scripts/run_omega_24x7.ps1` | `OMEGA_USE_V2=0`, `OMEGA_EDGE_METAL_ATR=0.0005`, equity MT5 | DEMO |
| `scripts/run_omega_24x7.ps1` | `OMEGA_ASSET_PROFILE=ceo_discovery_full` — 16 símbolos | **CEO discovery** ✅ |
| `config/omega_asset_schedule.json` | v2: perfil `ceo_discovery_full` + weekday 16 símbolos | **CEO discovery** ✅ |
| `modules/omega_asset_schedule.py` | Suporte `OMEGA_ASSET_PROFILE` + meta `profile` | **CEO discovery** ✅ |
| `scripts/restart_full_portfolio.ps1` | Delega para `run_omega_24x7.ps1` (sem env fixo) | **Alinhado T-W1** ✅ |
| `scripts/omega_demo_go_live.ps1` | Pré-voo: pytest 34/34 + smokes + reconcile | GO-LIVE |

### 2.3 Governança / testes

| Ficheiro | Estado |
|----------|--------|
| `tests/test_p0_abc_20260522.py` | 29 testes P0 |
| `tests/test_router_atr_20260523.py` | 5 testes Router |
| `governance/CEO_GO_LIVE_DEMO_ZERO_CONFLITO_20260525.md` | Procedimento DEMO |
| `governance/AIC_VALIDACAO_*_20260525.md` | Validações AIC |
| `governance/PSA_HANDOVER_ALTERACOES_COMPLETAS_20260525.md` | **Este documento** |

---

## 3. O que PSA NÃO deve fazer (causa conflito)

| Acção proibida | Motivo |
|----------------|--------|
| Re-adicionar `$env:OMEGA_24X7_ATIVOS` fixo nos PS1 | Bypassa T-W1/T-W2 |
| Activar `OMEGA_USE_V2=1` no runner | P0 T-P2b |
| Reverter `get_execution_tf_atr` para ATR M1 | Falha A regressão |
| Reimplementar T-W2 “porque falta” | Já em `818f627` |
| Correr `restart_full_portfolio` **versão antiga** com lista env | Substituída por delegação |

---

## 4. Portfolio discovery — lista oficial (16)

```
EURUSD GBPUSD USDJPY AUDUSD USDCAD XAUUSD US500 US100
BTCUSD ETHUSD SOLUSD XRPUSD AVAXUSD ADAUSD LTCUSD BNBUSD
```

Fonte: broker Hantec DEMO (DOC-OMEGA-ECOSISTEMA C-01).  
US100 = NAS100 no broker.

---

## 5. Arranque CEO (único caminho alinhado)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git pull origin feat/execution-router-atr-20260523
& .\scripts\run_omega_24x7.ps1
# ou equivalente:
& .\scripts\restart_full_portfolio.ps1
```

Monitor: `audit/paper/omega_24x7_runner.log`  
Esperar: `[SCHEDULE]`, `profile=ceo_discovery_full` ou `class=discovery_full`, `magic=234001`, sem `Invalid comment`.

---

## 6. Fecho de “pendências” (estado para CEO)

| Item | Responsável | Estado 2026-05-25 |
|------|-------------|-------------------|
| P0-ABC código | PSA | ✅ Fechado |
| Fase 1 Router/ATR | PSA | ✅ Fechado |
| Chave de Ouro | PSA | ✅ `ac153e4` |
| T-W2 + pré-voo DEMO | AIC | ✅ `818f627` |
| Portfolio discovery 16 | AIC | ✅ commit discovery |
| Merge PR #1 #2 | **CEO** | Aberto — `gh pr merge` |
| Fase 2 cascata/M1-GATE | — | **Mandato novo** — não reabrir sem CEO |
| TRE | — | **Fora de escopo** |
| SM-R2 ordem vivo SL≥$20 | Mercado | Discovery 24×7 gera quando gates passam |

---

## 7. Lucro / profit — expectativa realista

O sistema **não garante** lucro por segundo. Gates (EDGE, MTF, IA HOLD, KS) **reduzem** frequência de ordens para proteger capital.  
CEO modo discovery: mais símbolos → mais scans → mais eventos em `decision_trace.jsonl` e log; lucro depende de mercado + gates, não só de arranque.

---

*PSA: qualquer dúvida, comparar diff `818f627..HEAD` antes de editar.*
