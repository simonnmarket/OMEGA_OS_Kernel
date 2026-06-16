# OMEGA — Mandato Técnico Unificado

## P0-ABC · Weekend 24×7 · Revisão Arquitectural ATR/Router

| Campo | Valor |
|-------|--------|
| **Documento** | OMEGA-MANDATO-UNIFICADO-20260523 |
| **Versão** | 1.0 |
| **Data** | 2026-05-23 |
| **De** | CEO |
| **Para** | Tech Lead (AIC) + Equipe PSA |
| **Repositório** | `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE` |
| **Branch P0** | `fix/cicc-remediation-p0-abc-20260522` |
| **Branch P1 Router** | `feat/execution-router-atr-20260523` (criar após P0 PASS) |
| **Status** | Validado contra código-fonte (AIC Review 2026-05-23) |
| **Prioridade global** | **Fase 0 (P0)** → **Fase 0b (Weekend)** → **Fase 1–3 (Router/ATR)** |

---

## AUTORIZAÇÃO CEO (literal)

> **“PSA autorizado a executar na ordem deste documento: (1) conclusão P0-ABC sem DEFERRED não autorizado; (2) suplemento weekend 24×7; (3) patch ATR e Router conforme Fases 1–3. Mercado fechado = ocorrência registada, processo continua. Validação final AIC + CEO antes de merge main ou portfolio completo.”**
>
> — CEO, 2026-05-23

---

## Índice

1. [Tese executiva](#1-tese-executiva)  
2. [Estado actual e pendências (snapshot 23/05)](#2-estado-actual-e-pendências-snapshot-2305)  
3. [Diagnóstico validado — 4 falhas (A–D)](#3-diagnóstico-validado--4-falhas-ad)  
4. [Triage — respostas aos 3 testes](#4-triage--respostas-aos-3-testes)  
5. [FASE 0 — P0-ABC (obrigatório, não parar)](#5-fase-0--p0-abc-obrigatório-não-parar)  
6. [FASE 0b — Weekend 24×7 (incorporado, não script isolado)](#6-fase-0b--weekend-24x7-incorporado-não-script-isolado)  
7. [FASE 1 — Patch ATR (emergência)](#7-fase-1--patch-atr-emergência)  
8. [FASE 2 — Router fase 1 (Swing XAUUSD)](#8-fase-2--router-fase-1-swing-xauusd)  
9. [FASE 3 — Router completo + isolamento v2](#9-fase-3--router-completo--isolamento-v2)  
10. [Arquitectura Router (especificação)](#10-arquitectura-router-especificação)  
11. [Critérios PASS/FAIL globais](#11-critérios-passfail-globais)  
12. [Ficheiros e referências](#12-ficheiros-e-referências)  
13. [Proibições e dependências](#13-proibições-e-dependências)  
14. [Entregáveis e assinaturas](#14-entregáveis-e-assinaturas)

---

## 1. Tese executiva

A distância entre o sucesso e o fracasso do OMEGA **não** está na inteligência preditiva da IA, mas na **física da execução**. O sistema prevê o fluxo direcional correctamente em muitos casos, mas:

1. **Stop Loss microscópico** — ATR calculado em M1/M3 para sinais H4/H1 (Falha A).  
2. **Atraso estrutural** — Cascata W1→M15 + M1-GATE (3 velas) empurra a entrada para o fim do ciclo (Falhas B + C).  
3. **Efeito visível em XAUUSD (22/05)** — Entradas correctas na direcção, stops de ~$2.50, perda do fluxo de centenas a milhares de pontos.

**Transição obrigatória:** modelo monolítico → **Router de perfis** (Swing / Day / Scalp) com ATR alinhado ao TF do sinal.

**Nota operacional (23/05):** Fecho manual USDJPY com `[Market closed]` no sábado é comportamento **normal do broker**; não implica paragem do OMEGA. O runner deve **registar e continuar**.

---

## 2. Estado actual e pendências (snapshot 23/05)

### 2.1 O que o PSA já entregou (código — nível 1–2)

| Item | Status | Evidência |
|------|--------|-----------|
| T-D1 1POS / state | Implementado | `mt5_position_tag.py`, `state/omega_open_tickets.json` |
| T-D2 Breakeven buffer | Implementado | `shadow_loop.py` ~L4362–4390 |
| T-D3 Ghost orders | Implementado | `shadow_loop.py` ~L1427–1433 |
| T-D4 Schema G5 | Implementado | `total_realized_pnl` ~L3357 |
| T-P1a XAUUSD sl_pts_min 1500 | Implementado | `ASSET_PROFILES` L571 |
| T-P1b Cache guardrail 60s | Implementado | ~L1673–1700 |
| T-P1c Anti-hedge | Implementado | ~L3462–3479 |
| T-P2b Runner só v1 | Implementado | `omega_paper_loop_24x7.py` → `shadow_loop.py` |
| T-D5 Partial TP | Pré-existente | `ProgressivePartialCloseComplete` + `mt5_close_partial` |
| UT-1..7 + runner test | **PASS** (8/8) | `tests/test_p0_abc_20260522.py` — AIC reproduziu |

### 2.2 Pendências P0-ABC (bloqueiam veredito AIC APROVADO)

| ID | Item | Status | Responsável |
|----|------|--------|-------------|
| **P0-1** | **T-D4b** PositionManager wired | **FAIL** — PSA marcou DEFERRED **sem** excepção CEO | PSA |
| **P0-2** | Smoke MT5 SM-1..7 | **PENDENTE** | CEO (MT5 paper) |
| **P0-3** | Smoke portfolio P2a-1..3 | **PENDENTE** | CEO |
| **P0-4** | Reconcile G3–G5 + REG | **PENDENTE** | CEO pós-smoke |
| **P0-5** | Tabela PnL T-P2c (Sec. 7.8) | **PENDENTE** | CEO/PSA |
| **P0-6** | Commit final P0 documentado | **PENDENTE** | PSA |
| **P0-7** | Relatório PSA Sec. 4–6 preenchido | **PENDENTE** | CEO + PSA |
| **P0-8** | Validação AIC `AIC_VALIDACAO_PSA_P0_ABC_20260523.md` | **PENDENTE** | AIC |

**Regra:** DEFERRED em T-D4b **viola** mandato v2.0 salvo email CEO na Sec. 7.10 do relatório.

### 2.3 Pendências operacionais (weekend / 24×7)

| ID | Item | Problema actual | Acção |
|----|------|-----------------|-------|
| **W-1** | `run_omega_24x7.ps1` define `OMEGA_24X7_ATIVOS` com 32 ativos | **Ignora** `config/omega_asset_schedule.json` no sábado | Remover ou condicionar por dia |
| **W-2** | `run_omega_madrugada_pos_p0.ps1` | Idem portfolio completo | Alinhar ao calendário |
| **W-3** | Fechos automáticos sem `is_market_open` | TIME_STOP/partial tentam fechar → spam Journal | Guard antes de `order_send` fecho |
| **W-4** | Re-resolver ativos por ciclo | Lista fixa no arranque do runner | Opcional recomendado: schedule por ciclo |

**Comportamento correcto já no código (entradas):** `SKIP_MARKET_CLOSED` + Kill Switch ignora retcode 10018 — **não parar o processo**.

### 2.4 Pendências Router/ATR (este documento — P1)

| ID | Item | Fase |
|----|------|------|
| **R-1** | `get_execution_tf_atr(symbol, signal_tf, confidence)` | Fase 1 |
| **R-2** | Router classificador por alignment + signal_tf | Fase 2–3 |
| **R-3** | Bypass M1-GATE em Swing (H4/H1, align ≥ 0.8) | Fase 2 |
| **R-4** | Isolar `shadow_loop_v2.py` | Fase 3 |
| **R-5** | Smoke 48h XAUUSD com SL ≥ $20 em H4 | Fase 1–2 |

### 2.5 Backlog (não bloqueia Fase 1 ATR, regista no inventário)

| ID | Item | Nota |
|----|------|------|
| B-10 | Magic P0 em deals OUT | Validado 147/147 — não regredir |
| F-C01 | Reconciliação PnL equity vs deals vs feedback | T-P2c no smoke |
| Quantum/harmonic | Diagnóstico 1 página (Sec. 7.9 relatório P0) | Read-only |

---

## 3. Diagnóstico validado — 4 falhas (A–D)

### FALHA A — SL com ATR do TF errado [ALTA CONFIANÇA]

| Campo | Detalhe |
|-------|---------|
| **Local** | `shadow_loop.py` — `get_execution_tf_atr()` ~L1977–2004; uso ~L3563–3587 |
| **Erro** | Função usa **M3** (conf &lt; 0.80) ou **M1** (conf ≥ 0.80), **ignora** `tf` do loop (H1/H4/M15) |
| **Impacto XAUUSD 22/05** | ATR M1 ~250 pts × `sl_atr_mult` 0.7 ≈ **$2.50** SL; TP ~$12.32 |
| **P0-ABC** | `sl_pts_min=1500` (~L3785–3787) = **piso ~$15** — mitiga, **não** corrige a base |
| **Evidência** | `OMEGA_DEEP_AUDIT_COMPORTAMENTO_20260522.md` — PaperReports 2.50/12.32 pts |

### FALHA B — Latência estrutural da cascata [MÉDIA-ALTA]

| Campo | Detalhe |
|-------|---------|
| **Local** | `get_multi_tf_bias()` ~L1868–1915; gate ~L3094–3120 |
| **Mecanismo real** | Bloqueia se align **&lt; 20%** ou se align **≥ 50%** com bias **≠** sinal |
| **Problema** | Quando W1→M15 **concordam** com o sinal, movimento muitas vezes **já avançado** |
| **Correcção conceptual** | Cascata = filtro binário, **não** router de perfil |

### FALHA C — Sobrecarga M1-GATE [ALTA]

| Campo | Detalhe |
|-------|---------|
| **Local** | `modules/micro_entry_filter.py` L59–67, L69–75; pipeline ~L3884–4041 |
| **Erro** | 3 velas M1 + body_ratio ≥ 0.40 + quality ≥ 0.50 **após** macro |
| **Impacto** | Entrada no **fim** do micro-ciclo, antes de reversão |

### FALHA D — shadow_loop_v2 [ALTA no código / BAIXA em 22/05]

| Campo | Detalhe |
|-------|---------|
| **Local** | `shadow_loop_v2.py` L512 (M5 fixo), L628–630 (SL 500 / TP 1500) |
| **Produção 24×7** | `omega_paper_loop_24x7.py` → **`shadow_loop.py` v1** |
| **v2 activo só se** | `OMEGA_USE_V2=true` + `agent_ia/tools/fase4_wrapper.py` |
| **Veredito 22/05** | Causa provável = **A + C no v1**; D = risco path experimental |

---

## 4. Triage — respostas aos 3 testes

| Teste | Pergunta | Resposta AIC | PASS/FAIL |
|-------|----------|--------------|-----------|
| **T1** | SL XAUUSD ~$2.50 em 22/05? | **SIM** — PaperReports deep audit | **CONFIRMA Falha A** |
| **T2** | v2 activo em 22/05? | **NÃO** no runner habitual — grep logs `shadow_loop_v2` / `fase4_wrapper` | **Falha D improvável nesse dia** |
| **T3** | Esforço desacoplamento ATR? | Patch mínimo **4–8 h**; Router completo **~1 semana** | Planeamento abaixo |

**Comandos T2 (PSA ou CEO):**

```powershell
Select-String -Path "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log" -Pattern "shadow_loop_v2|fase4_wrapper|OMEGA_USE_V2" | Select-Object -Last 20
```

---

## 5. FASE 0 — P0-ABC (obrigatório, não parar)

**Referência detalhada:** `PSA_MANDATO_EXECUCAO_P0_ABC_20260522.md` v2.0  
**Relatório:** `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md`

### 5.1 Ordem de execução

```text
P1–P6 pré-condições (parar runner — script Sec. 4.1 do mandato P0)
  → T-D4b (OBRIGATÓRIO — sem DEFERRED)
  → Confirmar T-D1..D5, P1a..P2b já no branch
  → pytest UT-1..7
  → Smoke CEO: SM-1..7, P2a, G3–G5
  → Preencher relatório + commit
  → AIC validação
```

### 5.2 T-D4b — especificação (pendente PSA)

| Requisito | Detalhe |
|-----------|---------|
| Import | `PositionManager` de `core_engines/position_manager.py` |
| OPEN | Após entrada confirmada (pós D3) |
| CLOSE/PARTIAL | Mesmos pontos que `trade_feedback_append` |
| Campo | `total_realized_pnl` alinhado com T-D4 |
| Teste | UT-8 mínimo: open → close → feedback com PM |

### 5.3 Smoke CEO (comandos)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:PYTHONIOENCODING = "utf-8"

python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD GBPJPY XAUUSD --timeframes H1 --equity 10000
python scripts/psa_position_pnl_reconcile.py --since "2026-05-23 00:00:00"
```

### 5.4 Critério PASS Fase 0

| Gate | PASS se |
|------|---------|
| T-D4b | PositionManager wired + UT-8 PASS |
| UT-1..7 | Todos PASS |
| SM-1..7, P2a, G3–G5 | Todos PASS no relatório |
| Veredito PSA | Não “APROVADO” sem smoke |
| Veredito AIC | **APROVADO** ou **REPROVADO** documentado |

**Proibido:** merge `main`, portfolio 32 ativos (`run_omega_madrugada_pos_p0.ps1`) antes Fase 0 PASS.

---

## 6. FASE 0b — Weekend 24×7 (incorporado, não script isolado)

**Não criar** runner paralelo só de fim-de-semana. **Alterar** scripts existentes + runner.

### 6.1 T-W1 — Calendário de ativos

**Ficheiro:** `config/omega_asset_schedule.json` (já existe)

| Dia | Classe | Símbolos (default) |
|-----|--------|-------------------|
| Seg–Sex | core | XAUUSD, EURUSD, BTCUSD (+ portfolio se CEO autorizar) |
| Sábado | crypto | BTCUSD, ETHUSD, SOLUSD, EURUSD, XAUUSD |
| Domingo | crypto | + DOGUSD |

**Acção PSA — `run_omega_24x7.ps1`:**

```powershell
# REMOVER ou comentar linha fixa:
# $env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD USDJPY ..."

# O runner resolve automaticamente via omega_asset_schedule.json quando OMEGA_24X7_ATIVOS não está definido
```

**Acção PSA — `run_omega_madrugada_pos_p0.ps1`:** mesma regra.

### 6.2 T-W2 — Re-resolver ativos por ciclo (recomendado)

Em `scripts/omega_paper_loop_24x7.py`, no início de cada ciclo `while True`:

```python
from modules.omega_asset_schedule import resolve_shadow_loop_assets
ativos, _meta = resolve_shadow_loop_assets(
    _parse_ativos_from_env() or None, ROOT
)
log.info("[ASSET_SCHEDULE] bucket=%s symbols=%s", _meta.get("bucket"), ativos)
```

**PASS:** `audit/paper/asset_schedule.jsonl` mostra `bucket=saturday` no sábado.

### 6.3 T-W3 — Mercado fechado em fechos automáticos

Antes de **qualquer** `order_send` de fecho (TIME_STOP ~L3198, ZAK ~L3246, `mt5_close_partial`, trailing):

```python
if not is_market_open(symbol):
    log.info("[MARKET_CLOSED] fecho adiado ticket=%d symbol=%s", ticket, symbol)
    continue  # NÃO incrementar kill switch; NÃO sys.exit
```

Se `retcode == 10018`: log `[MARKET_CLOSED] ocorrência` — **continuar** ciclo.

**PASS:** Sábado com forex fechado — zero tentativas de fecho USDJPY no Journal (ou só manual CEO).

### 6.4 T-W4 — Teste weekend

| ID | Critério | PASS |
|----|----------|------|
| W-S1 | Runner 24h sábado sem crash | Processo activo + log ciclos |
| W-S2 | Log contém `SKIP_MARKET_CLOSED` para EURUSD se fechado | Sim |
| W-S3 | BTCUSD (se aberto) pode gerar sinal ou SKIP explícito | Não hang |
| W-S4 | `asset_schedule.jsonl` bucket=saturday | Sim |

---

## 7. FASE 1 — Patch ATR (emergência)

**Estimativa:** 4–8 horas  
**Branch:** `feat/execution-router-atr-20260523` (após merge ou commit P0 PASS)

### 7.1 T-R1 — Alterar assinatura e lógica

**De:**

```python
def get_execution_tf_atr(symbol: str, confidence: float = 0.70) -> dict:
```

**Para:**

```python
def get_execution_tf_atr(
    symbol: str,
    signal_tf: str,
    confidence: float = 0.70,
) -> dict:
```

**Mapa signal_tf → MT5:**

| signal_tf | MT5 constant |
|-----------|--------------|
| M1 | TIMEFRAME_M1 |
| M3 | TIMEFRAME_M3 |
| M5 | TIMEFRAME_M5 |
| M15 | TIMEFRAME_M15 |
| H1 | TIMEFRAME_H1 |
| H4 | TIMEFRAME_H4 |
| D1 | TIMEFRAME_D1 |
| W1 | TIMEFRAME_W1 |

**Regra:** ATR para SL/TP usa **sempre `signal_tf`**. M1/M3 só para **timing de entrada** (se mantido), **não** para distância do stop.

**Call sites a actualizar:** ~L3563, ~L4181, ~L4315 (grep `get_execution_tf_atr`).

### 7.2 T-R1b — sanitize_sl_tp

Passar `atr_pts` do **signal_tf**, não do execution tf:

```python
eff_sl, eff_tp = sanitize_sl_tp(eff_sl, eff_tp, _signal_atr_pts, asset)
```

Manter `sl_pts_min` XAUUSD = **1500** como piso até Router completo.

### 7.3 Testes

| ID | Teste | PASS |
|----|-------|------|
| UT-R1 | Mock H4 ATR 3000 pts, M1 ATR 250 pts → eff_sl usa 3000 base | eff_sl ≥ max(3000×0.7, 1500) |
| UT-R2 | signal_tf M15 → copy_rates TIMEFRAME_M15 | Mock verificado |

### 7.4 Smoke Fase 1

| ID | Critério | PASS |
|----|----------|------|
| SM-R1 | 1 ordem paper XAUUSD **H4** (ou H1) | Log `atr_tf=H4` |
| SM-R2 | SL distância ≥ **$20** (≥ 2000 pts × 0.01) no PaperReport | Campo sl_pts ou USD |
| SM-R3 | TP ≥ 2× SL (T-P1a) | R:R ≥ 2 |

---

## 8. FASE 2 — Router fase 1 (Swing XAUUSD)

**Estimativa:** 2–3 dias

### 8.1 T-R2 — Classificador mínimo

Novo módulo: `modules/execution_profile_router.py`

```python
def classify_execution_profile(
    signal_tf: str,
    alignment: float,
    bias: str,
    signal_dir: str,
) -> str:
    """
    Retorna: SWING | DAY | SCALP
    """
```

**Regra Fase 2 (mínima):**

| Condição | Perfil |
|----------|--------|
| `signal_tf in ('H4','H1')` **e** `alignment >= 0.80` **e** `bias == signal_dir` | **SWING** |
| `signal_tf in ('M15',)` **e** `alignment >= 0.40` | **DAY** |
| resto | **SCALP** (comportamento actual) |

### 8.2 T-R3 — Bypass M1-GATE em Swing

Em `shadow_loop.py`, antes do bloco M1-GATE (~L4000):

```python
if _exec_profile == "SWING":
    log.info("[%s %s] [ROUTER] SWING — bypass M1-GATE", asset, tf)
else:
    # micro_entry_filter existente
```

**PASS:** Log `[ROUTER] SWING — bypass M1-GATE` + ordem H4 sem `SKIP_M1_GATE`.

### 8.3 T-R4 — SL por perfil (Fase 2)

| Perfil | ATR para SL |
|--------|-------------|
| SWING | H4 (fallback H1 se H4 sem dados) |
| DAY | M15 |
| SCALP | M1 ou M3 (actual) |

### 8.4 Critérios PASS Fase 2

| ID | PASS |
|----|------|
| SM-R4 | 3 ciclos XAUUSD H4 paper — nenhum `SKIP_M1_GATE` em SWING |
| SM-R5 | SL ≥ $20; sem SL baseado só em ATR M1 no log |
| UT-R3 | `classify_execution_profile` unit tests |

---

## 9. FASE 3 — Router completo + isolamento v2

**Estimativa:** ~1 semana

### 9.1 Três perfis completos

Ver Sec. 10. Implementar gates por perfil (W1 proibido em SCALP, etc.).

### 9.2 T-R5 — Isolar v2

| Acção | Detalhe |
|-------|---------|
| Mover | `core_engines/shadow_loop_v2.py` → `archive/deprecated/shadow_loop_v2.py` |
| CI | Teste falha se `omega_paper_loop_24x7` referenciar v2 |
| Doc | `OMEGA_USE_V2=0` em todos os PS1 |

### 9.3 Smoke 48h

| ID | PASS |
|----|------|
| SM-R6 | 48h paper crypto weekend + XAUUSD H4 em dia útil |
| SM-R7 | Zero import `shadow_loop_v2` em logs |
| SM-R8 | Distribuição SL: Scalp &lt; Day &lt; Swing em pts USD (amostra ≥ 5 trades) |

---

## 10. Arquitectura Router (especificação)

O `alignment_score` passa a **classificador de contexto**, não gatilho de volume.

### PERFIL SWING (W1→H4 alinhados com sinal)

| Campo | Regra |
|-------|-------|
| **Gatilho** | Pullback H1 alinhado com H4 |
| **SL** | ATR **H4** (XAUUSD target $30–$50) |
| **TP** | ≥ 2× SL |
| **M1-GATE** | **Bypass total** |
| **Cascata** | Usa bias; **não** exige novas confirmações M1 |

### PERFIL DAY (H4→M15)

| Campo | Regra |
|-------|-------|
| **Gatilho** | Fluxo M15, timing M5 |
| **SL** | ATR **M15** |
| **M1** | **Só veto** — bloqueia se vela M1 reversão extrema; **sem** 3 velas obrigatórias |

### PERFIL SCALP (micro)

| Campo | Regra |
|-------|-------|
| **Gatilho** | Impulso M1 |
| **SL** | ATR **M1** ($2.50 pode ser correcto aqui) |
| **Macro** | **Não** ler W1/D1 para decisão |

---

## 11. Critérios PASS/FAIL globais

| Fase | Veredito possível | Condição |
|------|-------------------|----------|
| 0 P0-ABC | **APROVADO** | T-D4b + smoke + G5 + AIC PASS |
| 0b Weekend | **APROVADO** | W-S1..S4 + T-W1..W3 |
| 1 ATR | **APROVADO** | SM-R1..R3 + UT-R1..R2 |
| 2 Router v1 | **APROVADO** | SM-R4..R5 + bypass M1-GATE |
| 3 Router full | **APROVADO** | SM-R6..R8 + v2 isolado |

**Veredito global OMEGA execução:** só **OPERACIONAL TIER-1** após Fase 0 + 1 + 2 mínimo PASS (CEO + AIC).

---

## 12. Ficheiros e referências

| Ficheiro | Papel |
|----------|-------|
| `core_engines/shadow_loop.py` | Motor produção — todas as fases |
| `modules/micro_entry_filter.py` | Fase 2 bypass |
| `modules/execution_profile_router.py` | **CRIAR** Fase 2 |
| `modules/omega_asset_schedule.py` | Fase 0b |
| `config/omega_asset_schedule.json` | Calendário weekend |
| `scripts/omega_paper_loop_24x7.py` | Runner 24×7 |
| `scripts/run_omega_24x7.ps1` | **EDITAR** T-W1 |
| `core_engines/position_manager.py` | T-D4b |
| `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` | Relatório P0 |
| `Pendente/Auditoria/OMEGA_DEEP_AUDIT_COMPORTAMENTO_20260522.md` | Evidência Falha A |
| `Pendente/Auditoria/OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260522.md` | Inventário |

---

## 13. Proibições e dependências

1. **Não** iniciar Fase 1 Router antes de T-D4b PASS ou excepção CEO escrita.  
2. **Não** DEFERRED em T-D4b sem email CEO.  
3. **Não** portfolio 32 ativos antes Fase 0 PASS.  
4. **Não** activar `shadow_loop_v2` no runner 24×7.  
5. **Não** `sys.exit` por `MARKET_CLOSED` — só SKIP/defer.  
6. Fase 0 e Fase 0b **podem** ser mesmo sprint PSA se smoke CEO agendado.  
7. Fase 1 **depende** de branch estável pós-P0.

---

## 14. Entregáveis e assinaturas

| # | Entregável | Responsável | Data alvo |
|---|------------|-------------|-----------|
| 1 | T-D4b + commit P0 | PSA | Imediato |
| 2 | Relatório P0 Sec. 4–6 | CEO + PSA | Após smoke |
| 3 | `AIC_VALIDACAO_PSA_P0_ABC_20260523.md` | AIC | Pós-relatório |
| 4 | PS1 weekend + T-W3 | PSA | Com P0 |
| 5 | Patch ATR + UT-R1/R2 | PSA | +1 dia pós P0 |
| 6 | `execution_profile_router.py` + bypass | PSA | +3–5 dias |
| 7 | Relatório Fase 1–2: `PSA_RELATORIO_ROUTER_ATR_20260523.md` | PSA | Fim sprint |
| 8 | Inventário ABC coluna Resolvido actualizada | AIC | Pós cada fase |

### Declaração PSA

- [ ] Li este mandato unificado na íntegra.  
- [ ] Entendo: P0 primeiro, Router depois.  
- [ ] Não marcarei DEFERRED sem excepção CEO.  
- [ ] Entregarei relatórios com PASS/FAIL por secção.

**PSA:** _______________ **Data:** ________

### Validação AIC

| Fase | PASS / FAIL | Notas |
|------|-------------|-------|
| 0 P0-ABC | | |
| 0b Weekend | | |
| 1 ATR | | |
| 2 Router v1 | | |
| 3 Router full | | |

**AIC Tech Lead:** _______________ **Data:** ________

---

## Anexo A — Mensagem tipo para enviar ao PSA

```
Assunto: OMEGA — Mandato Unificado P0 + Weekend + Router/ATR (20260523)

PSA,

Anexo: OMEGA_MANDATO_UNIFICADO_P0_ROUTER_WEEKEND_20260523.md

Ordem obrigatória:
1) Fechar T-D4b (sem DEFERRED) + smoke — relatório Sec. 4-6
2) Weekend: remover OMEGA_24X7_ATIVOS fixo nos PS1; guard is_market_open em fechos
3) Após AIC APROVADO P0: branch feat/execution-router-atr-20260523 — patch get_execution_tf_atr(signal_tf)
4) Router Fase 2: bypass M1-GATE em Swing H4/H1

Foco CEO: "corrigir a física da entrada, não a IA."

Aguardamos planeamento de sprint com datas por fase.
```

---

*Documento emitido por AIC Tech Lead sob direcção CEO — 2026-05-23. Consolida: memorando Router CEO, validação código, pendências P0-ABC, suplemento weekend 24×7, inventário e deep audit 22/05.*
