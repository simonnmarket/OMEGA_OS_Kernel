# PSA — Instruções de Execução: CEO Capture Matrix 2026-06-03
**Versão:** 1.0  
**Data:** 2026-06-03  
**Assinado por:** PSA — Principal Solution Architect  
**Mandato origem:** CEO Capture Matrix — fio morto PLUG→ACT, caso forense XAUUSD #193126680  

---

## 1. ORDEM CEO — SUMÁRIO EXECUTIVO

O CEO aplicou a **CEO Capture Matrix (2026-06-03)** para corrigir o fio morto entre energia SEL/USFE (PLUG) e execução MT5 (ACT). Quatro correcções estruturais foram implementadas em `core_engines/shadow_loop.py`:

| Fix | Problema | Solução |
|-----|----------|---------|
| **P0** | TP = ATR×mult (~12857pts XAU) ignorava `impact_tp=42` SEL | `OMEGA_USE_SEL_IMPACT_TP=1` → TP real via SEL |
| **P1** | 1º partial em 2.5×ATR (~1000+ pts) — metais nunca fechavam parcial | XAU/XAG: 1º nível = 0.3×ATR (~430pts) |
| **P2** | `trend_score≥0.60` bloqueava pyramid XAU com +753pts | XAU/XAG: limiar 0.35 quando `profit_pts ≥ trigger` |
| **P3** | `OMEGA_MIN_LOT_EXEC=1.0` (global) causava lote 1.00 em pyramid | Piso APENAS metais: `OMEGA_MIN_LOT_METAL=0.05` |
| **P4** | EDGE_GATE bloqueava scale-entry em posições já vencedoras | `OMEGA_EDGE_BYPASS_WINNER=1` + `OMEGA_ALLOW_SCALE_ENTRIES=1` |

---

## 2. COMANDO ÚNICO — ARRANQUE

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\psa_capture_session_go.ps1 -Background
```

**Pré-condições obrigatórias:**
- MT5 aberto e conectado à conta demo
- Nenhum outro runner OMEGA em execução
- `audit\paper\omega_runner.lock` deve ser removido automaticamente pelo script (FASE 0)

**O script executa automaticamente:**
1. **FASE 0** — Para todos os PIDs `omega_paper_loop|shadow_loop`, remove locks
2. **FASE 1** — `py_compile shadow_loop.py` + `pytest tests/test_sel_usfe_gate.py` + snapshot git
3. **FASE 2** — Lança `run_omega_24x7.ps1` em background (capture matrix envs activos)

---

## 3. RELATÓRIO INTERMÉDIO / MANHÃ

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\psa_capture_session_report.ps1
```

Output guardado em `audit\forensic\capture_report_YYYYMMDD_HHMMSS\metrics.json`.

---

## 4. PROIBIDOS — CEO 2026-06-03

| Proibido | Razão |
|----------|-------|
| `OMEGA_MIN_LOT_EXEC=1.0` | Piso global — risco ~30%/trade; revertido 2026-06-03 |
| `OMEGA_TEST_HARNESS=1` | Harness madrugada encerrou ~08:15 UTC 03/Jun; não reintroduzir |
| Dois runners simultâneos | Mutex + log corruption; runner singleton obrigatório |
| `OMEGA_USFE_BLOCK=1` com peso 0 | USFE agora contribui via `impact_tp_pts`; não bloquear |
| `OMEGA_24X7_MODE=shadow` | Modo paper obrigatório (MT5 demo aberto) |

---

## 5. ENVS ACTIVOS — CAPTURE MATRIX (resume)

Definidos em `scripts/run_omega_24x7.ps1` (secção "CEO CAPTURE MATRIX 2026-06-03"):

```
OMEGA_TEST_HARNESS           = 0    ← SEM harness
OMEGA_USE_SEL_IMPACT_TP      = 1    ← P0: TP real via SEL
OMEGA_PYRAMID_MIN_SCORE_METAL= 0.35 ← P2: pyramid metais desbloqueado
OMEGA_EDGE_BYPASS_WINNER     = 1    ← P4: EDGE bypass vencedores
OMEGA_ALLOW_SCALE_ENTRIES    = 1    ← P4: scale-entry activo
OMEGA_MIN_LOT_METAL          = 0.05 ← P3: piso 0.05 APENAS XAU/XAG
OMEGA_MAX_SAME_DIR_PER_CYCLE = 3    ← 3 ordens/dir/ciclo (era 1)
OMEGA_PYRAMID_LAYERS         = 4    ← até 4 camadas pyramid
OMEGA_24X7_MODE              = paper
OMEGA_SEL_ENABLED            = 1
OMEGA_ENFORCE_SEL_USFE_GATE  = 1
OMEGA_USFE_BLOCK             = 1
OMEGA_RUPTURE_CAPTURE        = 0    ← OFF (sem harness)
```

---

## 6. MONITORIZAÇÃO — MARCADORES DE SUCESSO NO LOG

```
audit\paper\omega_24x7_runner.log
```

| Marcador | Significado | Estado actual |
|----------|-------------|---------------|
| `[IMPACT_TP] SEL impact=Xpts → eff_tp=Y` | P0 activo — TP real calculado | ✅ 172 activações |
| `[IMPACT_TP] [RESYNC]` | TP corrigido em posições legadas no boot | Verificar por sessão |
| `[PARTIAL_CLOSE] [RESYNC]` | Metais: 0.3×ATR carregado para posições legadas | Verificar no boot |
| `[PYRAMID] EXEC OK order=... deal=...` | Pyramid executou no broker (não só EVAL) | Aguarda MT5 ligado |
| `[EDGE_GATE] BYPASS` | P4 activo — EDGE bypass em posição vencedora | Próxima entrada |
| `[DEDUP] BYPASS scale-entry` | Scale-entry bypass DEDUP na mesma direção | Próxima entrada |
| `FATAL\|CRITICAL` | Erro grave — verificar imediatamente | Deve ser zero |

**Alerta MT5:**
```
ERRO: MT5 não conectado → shadow_loop SUSPENSO
```
Quando este erro aparece, o runner mantém o lock e retry automático a cada ciclo. Abrir/reconectar MT5 resolve sem reiniciar o runner.

---

## 7. RUNNER ACTUAL — ESTADO (03/Jun 16:06 UTC)

| Item | Estado |
|------|--------|
| PID | **37648** |
| Ciclo actual | 28 |
| TEST_HARNESS | INACTIVO (expirou ~08:15 UTC) |
| IMPACT_TP activações | **172** |
| MT5 | ⚠️ **Não conectado** — OHLCV suspended |
| Ação necessária | Reconectar MT5 → runner retoma automaticamente |

---

## 8. ROLLBACK DE EMERGÊNCIA

```powershell
# 1. Parar runner
Get-CimInstance Win32_Process -Filter "name='python.exe'" |
  Where-Object { $_.CommandLine -match "omega_paper_loop" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# 2. Remover locks
Remove-Item -Force "audit\paper\omega_runner.lock" -ErrorAction SilentlyContinue
Remove-Item -Force "audit\.omega_system.lock" -ErrorAction SilentlyContinue

# 3. Reverter envs no run_omega_24x7.ps1 (secção CEO CAPTURE MATRIX):
#    OMEGA_USE_SEL_IMPACT_TP = 0
#    OMEGA_EDGE_BYPASS_WINNER = 0
#    OMEGA_ALLOW_SCALE_ENTRIES = 0
#    OMEGA_PYRAMID_MIN_SCORE_METAL = 0.60
#    OMEGA_MIN_LOT_METAL = 0.01

# 4. Reiniciar
powershell -ExecutionPolicy Bypass -File scripts\run_omega_24x7.ps1
```

---

## 9. COMMIT — APÓS SESSÃO ESTÁVEL

Após veredito matinal com evidências no log:

```bash
git add -A
git commit -m "feat(capture): CEO Capture Matrix P0-P4 — PLUG→ACT wiring + TP real SEL

P0: OMEGA_USE_SEL_IMPACT_TP=1 (TP via sel_impact_tp_pts, não ATR×mult)
P1: partial_close_levels_for — metais 0.3xATR no 1o nivel
P2: pyramid_min_score_for — XAU/XAG 0.35 (era 0.60 global)
P3: exec_min_lot_floor — piso 0.05 so metais (sem OMEGA_MIN_LOT_EXEC global)
P4: EDGE_BYPASS_WINNER + ALLOW_SCALE_ENTRIES activos
Scripts: psa_capture_session_go.ps1 + psa_capture_session_report.ps1
Caso forensico: XAUUSD #193126680 (TP 12857pts, partial tardio, micro-lotes)

Generated with [Devin](https://cli.devin.ai/docs)

Co-Authored-By: Devin <158243242+devin-ai-integration[bot]@users.noreply.github.com>"
```

---

*PSA — handoff imediato | ver PSA_MEMORIA_CAPTURE_CEO_20260603.md para memória técnica completa*
