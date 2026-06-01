# CEO — Manual de início de operações (só após OK da PSA)

**Quando usar:** Depois que a PSA confirmar por escrito:
- Commit/push GitHub feito (URL do PR/commit)
- Registo DOC-OFC / memória institucional
- Código P0 no branch que você vai usar localmente (`git pull` se necessário)

**Não iniciar antes** — risco de correr código antigo sem mandatos M1–M4.

---

## FASE A — Enviar à PSA agora (você só encaminha)

Ficheiro a encaminhar:

`C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\docs\requests\PSA_MEMORANDO_GITHUB_REGISTO_20260520.md`

Pedido em uma frase:

> “PSA: executar T1–T2 do memorando, commit/push, registo memória, e confirmar quando o CEO pode fazer pull e iniciar demo.”

Opcional: pedir que copiem também os 4 TXT de  
`docs/conselho_arquivo/desktop_originais_20260520/` no commit.

---

## FASE B — Você executa na sua máquina (PowerShell)

### Pré-requisitos (checklist 30 segundos)

- [ ] MetaTrader 5 **aberto**, conta **demo**, servidor ligado, `trade_allowed=True`
- [ ] Anotar equity actual no MT5 (ex.: ~$1 250)
- [ ] Nenhum outro `run_omega_24x7.ps1` já a correr (Task Manager → python)

### Passo 1 — Actualizar código (se PSA fez push)

```powershell
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
git pull
```

Se não usar git localmente, confirmar com PSA que os ficheiros em disco já são os do commit.

### Passo 2 — Backup e reset da âncora Kill Switch (Opção B CKO)

```powershell
$riskDir = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\risk"
if (Test-Path "$riskDir\ks_daily_anchor.json") {
  Copy-Item "$riskDir\ks_daily_anchor.json" "$riskDir\ks_daily_anchor_BACKUP_CEO_20260520.json" -Force
  Remove-Item "$riskDir\ks_daily_anchor.json" -Force
  Write-Host "OK: ancora removida (backup criado)."
} else {
  Write-Host "INFO: ks_daily_anchor.json ja nao existe — OK para continuar."
}
```

### Passo 3 — Iniciar runner (modo diagnóstico CKO)

Abrir **nova** janela PowerShell:

```powershell
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
.\scripts\run_omega_24x7.ps1
```

Deixar a janela aberta. O processo corre até você fechar ou HALT.

### Passo 4 — Validar primeiros 5 minutos (obrigatório)

Noutra janela PowerShell:

```powershell
Get-Content "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log" -Tail 80 -Wait
```

**Tem de aparecer** (valores reais):

| Linha no log | Significado |
| --- | --- |
| `[EQUITY] Equity MT5 real: $1250.xx` | Equity real (sem bug 10k) |
| `[MOMENTUM_FALLBACK] DISABLED` | Modo diagnóstico silencioso (fallback OFF) |
| `FASE4 DECISION=AGENT_IA` ou momentum + `ORDER DONE` | Modo **demo teste** (fallback ON) |
| (opcional) `SKIP_SPREAD_GUARD` / `SKIP_ROLLOVER_BLACKOUT` | Gates P0 activos |

**Se NÃO aparecer `[EQUITY] Equity MT5 real`:** parar (Ctrl+C na janela do runner), MT5 fechado/desligado — corrigir antes de continuar.

**Se HALT imediato com DD:** âncora ainda antiga ou equity não actualizado — repetir Passo 2 com PSA na linha.

### Passo 5 — Matriz de componentes (após 1h ou 24h)

```powershell
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
python scripts\omega_component_health_matrix.py --md docs\conselho_arquivo\COMPONENT_HEALTH_MATRIX.md
```

---

## O que você NÃO precisa fazer manualmente

| Tarefa | Quem |
| --- | --- |
| Commit / push GitHub | **PSA** |
| Registo memória DOC-OFC | **PSA** |
| GAP-02 risk_config JSON | **PSA** |
| Editar `shadow_loop.py` | Já feito na Engenharia |
| Apagar pasta Desktop | Opcional **depois** do commit PSA |

---

## Parar o sistema (emergência)

```powershell
# Na janela onde corre run_omega_24x7.ps1: Ctrl+C
# Ou fechar posicoes OMEGA (se necessario):
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
python scripts\kill_all_positions.py
```

---

## Resposta curta à pergunta “o que executo eu?”

1. **Agora:** só encaminhar memorando PSA e aguardar **“OK para start”**.  
2. **Depois do OK PSA:** Passos 1–4 acima (pull → âncora → `run_omega_24x7.ps1` → verificar log).  
3. **Nada mais** até validação 5 min estar verde.

Quando a PSA confirmar, diga aqui **“PSA OK”** e acompanho linha a linha o seu log se quiser.
