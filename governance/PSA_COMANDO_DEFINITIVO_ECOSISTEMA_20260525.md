# PSA — Comando definitivo: ecossistema unificado + fecho incidente

| Campo | Valor |
|-------|--------|
| **Versão** | 3.0 — **substitui** mensagens/handover com HEAD mínimo `161be96`/`2517c8b` **para integração** |
| **Data** | 2026-05-25 |
| **Prioridade** | **CRÍTICA — execução única, sem reimplementar** |
| **Para** | PSA (Devin) |
| **De** | CEO / AIC Tech Lead |
| **Incidente** | `AIC_INCIDENTE_AUDITORIA_SCOPE_GAP_20260525.md` |
| **Gate** | `GATE_INTEGRACAO_ECOSISTEMA_OBRIGATORIO_20260525.md` |

---

## 0. Mensagem em uma frase

**Puxar código com ecossistema unificado → parar runner antigo → pré-voo → arrancar `run_omega_24x7.ps1` → gate integração → relatório 1h → só então dizer “resolvido” ao CEO.**

---

## 1. Documentos (ordem de leitura)

| # | Documento | Caminho |
|---|-----------|---------|
| 1 | **Este comando** | `governance/PSA_COMANDO_DEFINITIVO_ECOSISTEMA_20260525.md` |
| 2 | Acta incidente (porquê falhou auditoria) | `governance/AIC_INCIDENTE_AUDITORIA_SCOPE_GAP_20260525.md` |
| 3 | Gate obrigatório | `governance/GATE_INTEGRACAO_ECOSISTEMA_OBRIGATORIO_20260525.md` |
| 4 | CEO ecossistema (mapa motores) | `governance/CEO_ECOSISTEMA_UNIFICADO_20260525.md` |
| 5 | Handover P0/discovery (referência) | `governance/PSA_HANDOVER_ALTERACOES_COMPLETAS_20260525.md` |
| 6 | Go-live P0 (mantém) | `governance/CEO_GO_LIVE_DEMO_ZERO_CONFLITO_20260525.md` |

**Repositório:** `OMEGA_OS_Kernel`  
**Branch:** `feat/execution-router-atr-20260523`  
**Raiz local:** `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE`

---

## 2. HEAD mínimo (obrigatório)

O teu commit **deve** incluir o pacote ecossistema unificado. Validação:

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git fetch origin
git checkout feat/execution-router-atr-20260523
git pull origin feat/execution-router-atr-20260523
git log -3 --oneline
```

**PASS se:**

```powershell
Test-Path .\modules\omega_ecosystem_unified.py
Select-String -Path .\scripts\run_omega_24x7.ps1 -Pattern 'OMEGA_ECOSYSTEM_UNIFIED\s*=\s*"1"'
```

Se `omega_ecosystem_unified.py` **não existir** → **PARAR** e reportar CEO (código não sincronizado). **Não** patch local ad-hoc.

---

## 3. O que já está feito (NÃO duplicar)

| Área | Estado | Ficheiros-chave |
|------|--------|-----------------|
| P0-ABC | ✅ Fechado | tests P0, magic, comment, schedule |
| Fase 1 Router | ✅ Fechado | `get_execution_tf_atr`, `partial_taken` |
| Discovery 16 ativos | ✅ | `config/omega_asset_schedule.json`, T-W2 |
| **Ecossistema unificado** | ✅ no Git | `modules/omega_ecosystem_unified.py`, calibrador, orquestrador, fusão |
| Envs runner | ✅ | `scripts/run_omega_24x7.ps1` linhas unified |

**A tua tarefa:** sincronizar, reiniciar, validar integração, reportar.

---

## 4. Procedimento completo (copiar e executar por fases)

### FASE 0 — Parar runner antigo (obrigatório)

O processo em memória **não** carrega código novo até reinício.

```powershell
# Ver processos Python OMEGA (ajustar se tiveres PID conhecido)
Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, StartTime

# Se runner 24x7 estiver na consola: CTRL+C
# Ou (só se CEO/PSA confirmarem PID do omega_paper_loop):
# Stop-Process -Id <PID> -Force
```

**Confirmação:** não deve haver `omega_paper_loop_24x7.py` activo antes do FASE 4.

---

### FASE 1 — Gate código (preflight)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path

python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py tests/test_router_atr_20260523.py -q --tb=short
```

**Esperado:** `34 passed`  
Se falhar → reportar CEO; **não** arrancar runner.

```powershell
& .\scripts\omega_integration_gate.ps1 -Phase preflight
```

**Esperado:** `PREFLIGHT PASS`

---

### FASE 2 — Pré-voo DEMO (P0 — mantém)

**Pré-requisitos:** MT5 DEMO aberto, Algo Trading ON, **0** posições OMEGA órfãs (ou documentar existentes).

```powershell
& .\scripts\omega_demo_go_live.ps1
```

Rever: `audit\demo_go_live\GO_LIVE_REPORT_*.txt` — smokes exit=0.

> Nota: go-live **não** substitui gate integração; corre **antes** do runner longo.

---

### FASE 3 — Gate env alinhado (verificação manual rápida)

Confirmar que **só** `run_omega_24x7.ps1` define o DEMO (não editar à mão salvo mandato CEO):

| Variável | Valor obrigatório |
|----------|-------------------|
| `OMEGA_ECOSYSTEM_UNIFIED` | `1` |
| `OMEGA_USE_SIGNAL_FUSION` | `1` |
| `PSA_SHADOW_MODE` | `0` |
| `FUSION_MIN_CONFIDENCE` | `0.55` |
| `OMEGA_LOOP_PSA_V12` | `1` |
| `OMEGA_MAX_POSITIONS` | `8` |
| `OMEGA_ASSET_PROFILE` | `ceo_discovery_full` |
| `OMEGA_DISABLE_MOMENTUM_FALLBACK` | `0` (fallback **reserva**, não bússola) |
| `OMEGA_MAGIC_NUMBER` | `234001` (via código/config) |

**Proibido nesta fase:**

- Remover `OMEGA_ECOSYSTEM_UNIFIED`
- Definir `OMEGA_24X7_ATIVOS` (lista fixa) — usar schedule
- `PSA_SHADOW_MODE=1`

---

### FASE 4 — Arrancar runner (único comando de produção DEMO)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
& .\scripts\run_omega_24x7.ps1
```

**Alternativa** (delega ao mesmo script):

```powershell
& .\scripts\restart_full_portfolio.ps1
```

Aguardar **≥3 ciclos** (~12–20 min com interval 20s + scan 16×3 TF).

---

### FASE 5 — Gate runtime (obrigatório antes de dizer OK ao CEO)

Noutra janela PowerShell:

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
& .\scripts\omega_integration_gate.ps1 -Phase runtime
```

**PASS esperado:**

- Manifesto: `audit\paper\ecosystem_unified_manifest.json`
- Log: `[ECOSYSTEM_UNIFIED] manifesto=`
- 16 ativos no manifesto; `max_positions`: 8

Se **FAIL** → capturar últimas 200 linhas do log + manifesto (se existir) → reportar CEO. **Não** declarar resolvido.

---

### FASE 6 — KPI 1 hora (fecho incidente)

Deixar runner **60 minutos**. Depois:

```powershell
& .\scripts\omega_integration_gate.ps1 -Phase kpi -LogHours 1
```

Preencher template de relatório (secção 6) com contagens.

---

## 5. Validações no log (referência rápida)

```powershell
$log = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log"

# Deve aparecer após reinício
Select-String -Path $log -Pattern '\[ECOSYSTEM_UNIFIED\]' | Select-Object -Last 3

# Manifesto no disco
Get-Content .\audit\paper\ecosystem_unified_manifest.json | ConvertFrom-Json | Format-List

# KPI (última hora — ajustar se necessário)
Select-String -Path $log -Pattern 'PSA_FEED' | Measure-Object
Select-String -Path $log -Pattern 'Sinal aprovado|DECISION=AGENT_IA|source=AGENT_IA' | Measure-Object
Select-String -Path $log -Pattern 'MOMENTUM_MT5|FASE4 EXEC' | Measure-Object
Select-String -Path $log -Pattern 'Invalid comment' | Measure-Object
```

---

## 6. Relatório obrigatório PSA (criar este ficheiro)

**Caminho:** `governance/PSA_RELATORIO_INTEGRACAO_ECOSISTEMA_20260525.md`

**Template:**

```markdown
# PSA — Relatório integração ecossistema

| Campo | Valor |
|-------|--------|
| Data/hora fim | YYYY-MM-DD HH:MM |
| HEAD | `git log -1 --oneline` |
| Runner reiniciado | Sim/Não — hora |

## Gates
| Gate | Resultado |
|------|-----------|
| pytest 34/34 | PASS/FAIL |
| omega_demo_go_live | PASS/FAIL |
| integration_gate preflight | PASS/FAIL |
| integration_gate runtime | PASS/FAIL |
| integration_gate kpi 1h | PASS/FAIL/CONDICIONAL |

## Manifesto
- unified: true/false
- portfolio count: N
- max_positions: N

## KPI 1h (contagens)
| Métrica | Valor |
|---------|-------|
| PSA_FEED BUY/SELL | |
| IA Sinal aprovado / AGENT_IA | |
| MOMENTUM_MT5 exec | |
| EDGE_GATE skips | |
| Invalid comment | 0 obrigatório |

## Posições MT5
- Abertas: ...
- Magic 234001: Sim/Não

## Veredito
- [ ] INTEGRAÇÃO PASS — incidente INC-AUDIT-20260525-001 pode fechar
- [ ] INTEGRAÇÃO FAIL — motivo: ...

## Evidências
- audit/paper/ecosystem_unified_manifest.json
- audit/paper/omega_24x7_runner.log (trecho)
- audit/integration_gate/ (se gerado)
```

Enviar caminho do relatório ao CEO quando completo.

---

## 7. Rollback (só com ordem CEO)

Se unified causar crash loop:

```powershell
# Parar runner
$env:OMEGA_ECOSYSTEM_UNIFIED = "0"
# Reportar CEO ANTES de deixar em produção
```

**Não** fazer rollback silencioso. Documentar motivo na acta.

---

## 8. PRs GitHub (CEO — não bloqueia reinício)

| PR | Conteúdo | Merge |
|----|----------|-------|
| #1 | P0-ABC | CEO |
| #2 | Router Fase 1 | CEO |

PSA: **não** precisa de merge para executar branch `feat/execution-router-atr-20260523`.

---

## 9. Checklist final (marcar tudo antes de “resolvido”)

- [ ] FASE 0 — Runner antigo parado  
- [ ] FASE 1 — pytest 34/34 + integration_gate preflight PASS  
- [ ] FASE 2 — omega_demo_go_live PASS  
- [ ] FASE 4 — `run_omega_24x7.ps1` activo  
- [ ] FASE 5 — integration_gate runtime PASS  
- [ ] FASE 6 — KPI 1h documentado  
- [ ] Relatório `PSA_RELATORIO_INTEGRACAO_ECOSISTEMA_20260525.md` criado  
- [ ] CEO informado com veredito **INTEGRAÇÃO PASS** ou FAIL explícito  

---

## 10. Suporte AIC

Se gate FAIL sem causa óbvia: colar no chat CEO

1. `git log -1 --oneline`  
2. Saída `omega_integration_gate.ps1`  
3. `ecosystem_unified_manifest.json` (se existir)  
4. Últimas 100 linhas `omega_24x7_runner.log`  

---

*PSA Comando definitivo v3.0 — AIC 2026-05-25 — Execução única para fechar incidente e evitar re-trabalho P0.*
