# PSA — Memória Completa: CEO Capture Matrix 2026-06-03
**Versão:** 1.0  
**Data:** 2026-06-03  
**Assinado por:** PSA — Principal Solution Architect  
**Branch:** hotfix/forensic-remediation-20260527  
**Commit HEAD:** 354b5d5 (docs: OMEGA-PSA-AUDIT-CLOSE-20260602 — ENT-01 a ENT-05)  
**Ficheiro central:** `core_engines/shadow_loop.py`

---

## 1. CASO FORENSE — XAUUSD #193126680

### Sintomas observados (sessão 02/Jun)
| Sintoma | Medição | Causa raiz |
|---------|---------|-----------|
| TP na ordem MT5 | **4347.14** (~12857 pts) | TP = ATR×mult; `sel_impact_tp_pts=42.48` ignorado |
| TP correcto calculado | **~4475.29** (~42 pts) | SEL produzia `sel_impact_tp_pts` mas wire inexistente |
| Pyramid no log | `[PYRAMID_EVAL] add=True` apenas | `PYRAMID EXEC OK` = zero — wire broker absent |
| Partial close | 1 × 0.01 lot @ 4461.92 | Tardio; 1º nível = 2.5×ATR nunca atingido |
| Lote pyramid | `LOT1.00` (se executado) | `OMEGA_MIN_LOT_EXEC=1.0` global — risco ~30%/trade |
| Edge gate | Bloqueou novas entradas | Vol baixo + posição lucrativa = bloqueio absurdo |

### Linha do tempo
```
H4 entrada           → sel_impact_tp_pts=42.48 calculado, IGNORADO
TP MT5               → 4347.14 (legacy ATR×mult = 12857pts)
Partial 1x 0.01lot   → @ 4461.92 (0.3×ATR via P1 fix, executou)
Pyramid              → EVAL True mas ZERO exec broker (wire ausente)
Posição fechada      → ~15:03 UTC 02/Jun
```

---

## 2. P0 — IMPACT_TP: SEL → TP real

### Antes / depois
| | Antes | Depois |
|-|-------|--------|
| TP | `_pre_tp = ATR × mult` (~12857pts XAU) | `sel_impact_tp_pts` quando > 0 |
| Env | (sem env) | `OMEGA_USE_SEL_IMPACT_TP=1` |
| Log | silêncio | `[IMPACT_TP] SEL impact=42pts → eff_tp=42 (ATR_tp=12857)` |

### Código — shadow_loop.py L4454–4466
```python
_use_sel_impact_tp = False
_sel_impact_tp = float((_flow_details or {}).get("sel_impact_tp_pts", 0) or 0)
if (
    _sel_impact_tp > 0
    and os.getenv("OMEGA_USE_SEL_IMPACT_TP", "1").strip().lower()
    in ("1", "true", "yes", "on")
):
    eff_tp = max(_sel_impact_tp, float(_min_pts_pre))
    _use_sel_impact_tp = True
    log.info(
        "[%s %s] [IMPACT_TP] SEL impact=%.0fpts → eff_tp=%.0f (ATR_tp=%.0f)",
        asset, tf, _sel_impact_tp, eff_tp, _pre_tp,
    )
```

### Resync boot — posições legadas (shadow_loop.py L1309–1358)
```python
def resync_impact_tp_for_position(pos, pos_ledger: dict | None = None) -> dict:
    # Aplica TP dinâmico a posição já aberta — só altera se TP actual >> impact (2×)
    if os.getenv("OMEGA_USE_SEL_IMPACT_TP", "1").strip().lower() not in ("1","true","yes","on"):
        return {"applied": False, "reason": "IMPACT_TP disabled"}
    ...
    cur_tp_pts = abs(entry - cur_tp) / pt if cur_tp > 0 else 99999.0
    if cur_tp_pts <= impact_pts * 2.0:
        return {"applied": False, "reason": "already_aligned"}
    new_tp = entry + impact_pts * pt  # BUY
    mod = mt5_modify_position_sl(ticket, symbol, cur_sl, new_tp)
```

**Nota:** TP por impacto NÃO passa por `sanitize_sl_tp` R:R cap. SL continua capado por regime.

### Activações sessão capture (03/Jun)
```
172 × [IMPACT_TP] SEL impact=Xpts → eff_tp=Y (ATR_tp=Z)
```
Exemplos confirmados:
- `[XAUUSD H4] [IMPACT_TP] SEL impact=32pts → eff_tp=60 (ATR_tp=9064)`
- `[US100 H1] [IMPACT_TP] SEL impact=95pts → eff_tp=95 (ATR_tp=15321)`
- `[BTCUSD H4] [IMPACT_TP] SEL impact=...`

---

## 3. P1 — PARTIAL CLOSE METAIS 0.3×ATR

### Função shadow_loop.py L1226–1231
```python
def partial_close_levels_for(symbol: str) -> list:
    """Níveis de partial close por classe — metais usam 0.3×ATR no 1º nível (CEO 2026-06-03)."""
    import copy as _copy_mod
    if str(symbol or "").upper() in _METAL_ASSETS:
        return _copy_mod.deepcopy(_PARTIAL_CLOSE_LEVELS_METAL_CEO)
    return _copy_mod.deepcopy(_PARTIAL_CLOSE_LEVELS_PSA)
```

### Constantes
```python
_PARTIAL_CLOSE_LEVELS_METAL_CEO = [0.3, 1.5, 2.5, 4.0]  # XAU/XAG: 0.3×ATR no 1º nível
_PARTIAL_CLOSE_LEVELS_PSA       = [1.0, 2.0, 3.0, 4.0]   # outros activos
```

### Resync boot para posições legadas
- L2953: `_pc_eng_boot.levels = partial_close_levels_for(_rp.symbol)`
- Log: `[PARTIAL_CLOSE] [RESYNC] XAUUSD #TICKET levels=[0.3, 1.5, 2.5, 4.0]ATR`

### XAUUSD H4 ATR típico: ~2924 pts/lot
→ 1º nível 0.3×ATR ≈ **877 pts** (era 2.5×ATR ≈ **7310 pts** — impossível em sessão normal)

---

## 4. P2 — PYRAMID GATE METAIS 0.35

### Função shadow_loop.py L1234–1239
```python
def pyramid_min_score_for(symbol: str, profit_pts: float, trigger_pts: float) -> float:
    """Limiar pyramid: 0.35 em XAU/XAG quando profit >= trigger (CEO 2026-06-03)."""
    default = float(os.getenv("OMEGA_PYRAMID_MIN_SCORE", "0.60"))
    if str(symbol or "").upper() in _METAL_ASSETS and profit_pts >= trigger_pts:
        return float(os.getenv("OMEGA_PYRAMID_MIN_SCORE_METAL", "0.35"))
    return default
```

### Envs activos
```
OMEGA_PYRAMID_MIN_SCORE_METAL = 0.35  (era 0.60 global)
OMEGA_PYRAMID_LAYERS          = 4     (era 2)
OMEGA_PYRAMID_LOT_SCALE       = 1.5   (2ª camada = 1.5× âncora)
OMEGA_PYRAMID_ATR             = 0.5   (trigger = 0.5×ATR)
```

### Caso forense #193126680
- `trend_score=0.20 < 0.60` → pyramid bloqueado com +753 pts
- Com P2: `trend_score=0.20` mas `profit_pts ≥ trigger` → `min_score=0.35` → **ainda bloqueado**
- Bypass total: `profit_pts ≥ trigger` → skip trend_score check completamente (metal bypass)

---

## 5. P3 — PISO DE LOTE + ESCALA

### Função shadow_loop.py L1242–1246
```python
def exec_min_lot_floor(asset: str, regime: str) -> float:
    """Piso de lote — CEO 2026-06-03: 0.05 apenas XAU/XAG; restantes = LotCalc (sem piso global)."""
    if str(asset or "").upper() in _METAL_ASSETS:
        return float(os.getenv("OMEGA_MIN_LOT_METAL", "0.05") or 0)
    return min_lot_floor_for_regime(regime)
```

### Regras efectivas
| Activo | Piso lote | Env |
|--------|-----------|-----|
| XAUUSD / XAGUSD | `max(LotCalc, 0.05)` | `OMEGA_MIN_LOT_METAL=0.05` |
| Forex / Index / Crypto | `LotCalc` puro | sem piso global |
| **PROIBIDO** | ~~0.01~~ → 1.00~~ | ~~`OMEGA_MIN_LOT_EXEC=1.0`~~ revertido |

### Pyramid lote
```python
# L2581: pyramid usa o mesmo exec_min_lot_floor
_py_floor = exec_min_lot_floor(symbol, str(prof.get("regime","") or ""))
# Lote pyramid = max(LotCalc_pyramid, _py_floor)
# XAU pyramid correcto: max(0.03, 0.05) = 0.05 (era 1.00 com OMEGA_MIN_LOT_EXEC)
```

---

## 6. P4 — EDGE_GATE BYPASS VENCEDORES + MULTI-ENTRADA

### EDGE bypass (shadow_loop.py ~L3611)
```python
and os.getenv("OMEGA_EDGE_BYPASS_WINNER", "1").strip().lower()
# Se posição OMEGA lucrativa no activo → EDGE_GATE bypassed
# Log: [EDGE_GATE] BYPASS — posicao lucrativa {symbol} profit={X}
```

### Scale-entry bypass DEDUP (shadow_loop.py ~L4165)
```python
if os.getenv("OMEGA_ALLOW_SCALE_ENTRIES", "1").strip().lower() in ("1","true","yes","on"):
    # Bypass [DEDUP] para scale-entry na mesma direcção vencedora
    # Log: [DEDUP] BYPASS scale-entry {symbol} {direction}
```

### Envs activos
```
OMEGA_EDGE_BYPASS_WINNER     = 1
OMEGA_ALLOW_SCALE_ENTRIES    = 1
OMEGA_MAX_SAME_DIR_PER_CYCLE = 3  (era 1)
```

---

## 7. TIMELINE DA SESSÃO CAPTURE 2026-06-03

```
00:10 UTC   Test Harness madrugada arrancou (USFE=0.05, RUPTURE=0, BLOCKLIST=UKOIL+)
00:15 UTC   TEST_HARNESS=1 confirmado no log — runner anterior parado, locks limpos
00:17 UTC   Ciclo 1 capture madrugada — NIGHT_PASS ATIVO — IMPACT_TP activo
08:00 UTC   TEST_HARNESS ACTIVO (último marcador)
08:15 UTC   TEST_HARNESS EXPIROU (~expires=2026-06-03T08:15:56Z)
~08:20 UTC  Runner reiniciou sem harness (run_omega_24x7.ps1 capture matrix)
15:35 UTC   Último IMPACT_TP confirmado no log (ciclo com MT5 ligado)
16:04 UTC   MT5 desconectado → [OHLCV] Export falhou — shadow_loop SUSPENSO
16:06 UTC   Ciclo 28 em curso — PID 37648 activo — aguarda reconexão MT5
```

---

## 8. ENVS COMPLETOS — run_omega_24x7.ps1 (secção Capture Matrix)

```powershell
# CEO CAPTURE MATRIX 2026-06-03 — fio morto ACT→PLUG corrigido
$env:OMEGA_TEST_HARNESS             = "0"
$env:OMEGA_USE_SEL_IMPACT_TP        = "1"
$env:OMEGA_PYRAMID_MIN_SCORE_METAL  = "0.35"
$env:OMEGA_EDGE_BYPASS_WINNER       = "1"
$env:OMEGA_ALLOW_SCALE_ENTRIES      = "1"
$env:OMEGA_MIN_LOT_METAL            = "0.05"
$env:OMEGA_MAX_SAME_DIR_PER_CYCLE   = "3"
$env:OMEGA_PYRAMID_LAYERS           = "4"

# Envs de sessão (pré-existentes, mantidos)
$env:OMEGA_24X7_MODE                = "paper"
$env:OMEGA_SEL_ENABLED              = "1"
$env:OMEGA_ENFORCE_SEL_USFE_GATE    = "1"
$env:OMEGA_USFE_BLOCK               = "1"
$env:OMEGA_RUPTURE_CAPTURE          = "0"   # OFF sem harness
$env:OMEGA_SEL_SLOT_RP              = "0.8"
$env:OMEGA_RISK_PER_TRADE           = "0.005"
$env:OMEGA_MAX_POSITIONS            = "8"
$env:OMEGA_MIN_CONFLUENCE           = "35"
$env:OMEGA_MIN_CONFIDENCE           = "0.62"
$env:OMEGA_DD_DAILY_MAX             = "0.10"
$env:OMEGA_USE_RISK_BUDGET          = "1"
$env:OMEGA_LOT_MAX                  = "0.50"
$env:OMEGA_LOOP_INTERVAL_SEC        = "20"  # 20s (sem harness)
$env:OMEGA_FORCE_HIGH_PERFORMANCE   = "1"
```

---

## 9. SCRIPTS DE SESSÃO

### psa_capture_session_go.ps1 — `scripts/psa_capture_session_go.ps1`
**Fases:**
1. FASE 0 — Stop PIDs `omega_paper_loop|shadow_loop`, remove `omega_runner.lock` e `.omega_system.lock`
2. FASE 1 — `py_compile shadow_loop.py`, `pytest tests/test_sel_usfe_gate.py`, snapshot forensic
3. FASE 2 — `run_omega_24x7.ps1 -Background` (ou foreground sem `-Background`)

**Snapshot forensic:** `audit/forensic/capture_session_YYYYMMDD_HHMMSS/`
- `py_compile_shadow_loop.txt`
- `pytest_sel_usfe.txt`
- `git_head.txt`
- `pre_counters.json`

### psa_capture_session_report.ps1 — `scripts/psa_capture_session_report.ps1`
**Métricas extraídas do log:**
```
impact_tp_new        → [IMPACT_TP] SEL impact=
impact_tp_resync     → [IMPACT_TP] [RESYNC]
partial_03atr        → TP1-0.3ATR | 0.3x ATR
partial_broker_ok    → [MT5_CLOSE_PARTIAL] ✅
pyramid_eval_add     → [PYRAMID_EVAL] add=True
pyramid_broker_ok    → [PYRAMID] EXEC OK
pyramid_broker_fail  → [PYRAMID] EXEC FAIL
edge_bypass          → [EDGE_GATE] BYPASS
dedup_scale_bypass   → [DEDUP] BYPASS scale-entry
lot_metal_floor      → LOT0.05 | min_lot 0.05
trace_executes       → MT5_PAPER_EXECUTE
feedback_opens       → position_opened
feedback_closes      → position_closed
```

---

## 10. HEURÍSTICA DE VEREDITO MATINAL

**PASS** (sessão capture saudável) se todos os critérios verificados:

| # | Critério | Limiar |
|---|----------|--------|
| 1 | `impact_tp_new` | ≥ 1 (novas entradas com TP SEL) |
| 2 | `impact_tp_resync` | ≥ 1 (posições legadas corrigidas no boot) |
| 3 | `pyramid_broker_ok` | ≥ 1 (pyramid executou no broker, não só EVAL) |
| 4 | `partial_broker_ok` | ≥ 1 (0.3×ATR fechou parcial no metal) |
| 5 | Nenhum `LOT1.00` pyramid metal | Zero |
| 6 | Runner lock activo | `audit/paper/omega_runner.lock` presente |
| 7 | Nenhum `FATAL\|CRITICAL` | Zero |

**Estado actual (16:06 UTC 03/Jun):**
- ✅ impact_tp_new = 172
- ⏳ pyramid_broker_ok = 0 (aguarda MT5 reconectado + oportunidade)
- ⚠️ MT5 desconectado desde ~16:04 UTC — runner em standby/retry

---

## 11. ROLLBACK COMPLETO

### Reversão P0-P4 (se anomalia detectada)
```powershell
# run_omega_24x7.ps1 — alterar secção CEO CAPTURE MATRIX:
$env:OMEGA_USE_SEL_IMPACT_TP        = "0"
$env:OMEGA_EDGE_BYPASS_WINNER       = "0"
$env:OMEGA_ALLOW_SCALE_ENTRIES      = "0"
$env:OMEGA_PYRAMID_MIN_SCORE_METAL  = "0.60"
$env:OMEGA_MIN_LOT_METAL            = "0.01"
$env:OMEGA_MAX_SAME_DIR_PER_CYCLE   = "1"
$env:OMEGA_PYRAMID_LAYERS           = "2"
```

### Reversão urgente (parar imediatamente)
```powershell
Get-CimInstance Win32_Process -Filter "name='python.exe'" |
  Where-Object { $_.CommandLine -match "omega_paper_loop" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Remove-Item -Force "audit\paper\omega_runner.lock" -ErrorAction SilentlyContinue
Remove-Item -Force "audit\.omega_system.lock" -ErrorAction SilentlyContinue
```

### Reversão `OMEGA_MIN_LOT_EXEC=1.0` (PROIBIDA — apenas se CEO autorizar)
```powershell
# NÃO adicionar. Risco ~30%/trade em XAU H4 (ATR=$2924, SL=1× ATR → $2924/lot × 1 lot)
# CEO reverteu em 2026-06-03 — ver AIC_LOG_CORRECAO_CEO_CAPTURE_20260603.md
```

---

## 12. COMMIT TEMPLATE — APÓS SESSÃO ESTÁVEL

```bash
git add -A
git commit -m "feat(capture): CEO Capture Matrix P0-P4 — PLUG→ACT wiring

Caso forensico: XAUUSD #193126680
- TP 12857pts ignorava sel_impact_tp_pts=42.48 (SEL vivo, wire morto)
- Pyramid bloqueado em trend_score=0.20 com +753pts lucro
- Partial 1x micro-lote tardio (2.5xATR nunca atingido)
- OMEGA_MIN_LOT_EXEC=1.0 revertido (risco ~30%/trade)

P0: OMEGA_USE_SEL_IMPACT_TP=1 (TP via sel_impact_tp_pts)
    shadow_loop.py L4454-4466 + resync_impact_tp_for_position L1309
P1: partial_close_levels_for L1226 — metais 0.3xATR no 1o nivel
P2: pyramid_min_score_for L1234 — XAU/XAG min=0.35 (era 0.60)
P3: exec_min_lot_floor L1242 — piso 0.05 so metais
    PROIBIDO: OMEGA_MIN_LOT_EXEC=1.0 global revertido
P4: EDGE_BYPASS_WINNER L3611 + ALLOW_SCALE_ENTRIES L4165
Scripts: psa_capture_session_go.ps1 + psa_capture_session_report.ps1
Evidencia: 172x [IMPACT_TP] activacoes sessao 03/Jun

Generated with [Devin](https://cli.devin.ai/docs)

Co-Authored-By: Devin <158243242+devin-ai-integration[bot]@users.noreply.github.com>"
```

---

## 13. FICHEIROS RELEVANTES

| Ficheiro | Papel |
|----------|-------|
| `core_engines/shadow_loop.py` | Motor principal — P0-P4 implementados |
| `scripts/run_omega_24x7.ps1` | Envs capture matrix + arranque runner |
| `scripts/psa_capture_session_go.ps1` | Handoff script — FASE 0/1/2 |
| `scripts/psa_capture_session_report.ps1` | Métricas sessão capture |
| `governance/AIC_LOG_CORRECAO_CEO_CAPTURE_20260603.md` | Log AIC das correcções |
| `governance/PSA_INSTRUCOES_EXECUCAO_CAPTURE_CEO_20260603.md` | Instruções handoff |
| `audit/paper/omega_24x7_runner.log` | Log principal (513K+ linhas) |
| `audit/paper/decision_trace.jsonl` | Rastreio por componente |
| `audit/paper/omega_runner.lock` | PID runner (actualmente 37648) |
| `audit/forensic/capture_session_*/` | Snapshots por sessão |

---

*PSA — memória completa técnica | AIC_TIER0_RULES_v4 | branch: hotfix/forensic-remediation-20260527*
