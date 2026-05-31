# CEO FORCE NOW — ALTA PERFORMANCE OMEGA (PSA EXECUTAR JÁ)

**ID:** `OMEGA-CEO-FORCE-NOW-20260601`  
**Prioridade:** MÁXIMA — **AGORA**  
**Autoridade:** CEO — **não negociável**  
**Objetivo:** O fundo **existe** em paper: lucro-alvo em **USD reais**, componentes a trabalhar, **zero migalhas**, **zero retrabalho** disperso. **Um único documento, uma execução, um pacote de prova.**

**Lab:** `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE`  
**Prazo entrega:** **≤ 4 horas** após receber esta ordem (relatório + log + MT5 screenshots).

---

## INTRODUÇÃO (obrigatória)

PSA,

O CEO investiu **milhares de horas** neste ecossistema. O potencial dos componentes (harmónico, flow, USFE, RiskBudget, FastLoop, parciais) **não aparece** enquanto o sistema abrir trades com TP de **$3** e deixar posições presas **horas** a bloquear GER40, US500 e XAGUSD nos movimentos direcionais.

**Isto não é mais um “teste”.** É **FORCE NOW — alta performance**: executar **esta lista completa**, reiniciar o runner, provar no MT5 e no log que o OMEGA opera como **fundo em paper**, não como catador de migalhas.

**Já executaste o MANDATO 20260601 (commit fcb2ecf).** Este documento **fecha o que falta** + **patch AIC já no código** que deves validar e completar.

**Não inventes scope.** Não declares 100%. **Entrega evidência.**

---

## REGRA DE OURO (fund-level)

Nenhuma **nova** ordem pode ser enviada se:

```
TP_usd_estimado < max(piso_classe, (spread + swap + comissão) × 1.35)
```

| Classe | Piso TP USD (mínimo) |
|--------|----------------------|
| index | **25** |
| forex / jpy | **10** |
| metal / commodity | **18** |
| crypto | **15** |
| crypto_alt | **8** |

Se não atingir o piso com lote permitido pelo risco → **SKIP** e log `[ECON_GATE]` — **nunca** enviar ordem ridícula.

---

## FASE 0 — CEO + PSA (30 min) — LIBERTAR O MOTOR

### 0.1 Posições legadas — STALE no runner **ou** Fase 2 no sistema (PSA)

**Nesta fase (FORCE NOW):** PSA pode usar `OMEGA_STALE_*` (runner) ou listar tickets para fecho.

**Após entregar `RELATORIO_FORCE_NOW_PSA.md`:** CEO manda **Fase 2** — PSA fecha no sistema com `scripts\psa_close_positions.py` (ver `governance\CEO_POS_FORCE_NOW_FASE2_PSA.md`). **CEO não precisa fechar manualmente no MT5.**

Rever tickets com lucro alvo irrisório ou presos &gt;2h:

| Símbolo | Tickets referência (ex.) | Motivo |
|---------|--------------------------|--------|
| US500 | #191051720 / #192074499 | TP ~$3, bloqueia slot |
| GER40 | #192105887 | Movimento perdido + cap |
| UKOIL+ | #191908751 | Alta/baixa sem nova entrada |

**Sem libertar slots, o sistema NÃO pode mostrar potencial em tendência** — não é falha de componente, é **portfólio cheio**.

### 0.2 Parar runner

```powershell
# Matar processo python do OMEGA (Task Manager ou):
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5
```

---

## FASE 1 — CÓDIGO (AIC patch + PSA validar) — 60 min

### 1.1 Pip value MT5 (CRÍTICO — causa US500 $3.15)

**AIC já aplicou** em `shadow_loop.py`:

- `pip_value_per_lot_mt5()` — usa `order_calc_profit` + cache
- `calc_lot()` usa essa função

**PSA DEVE:**

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python scripts\psa_calibrate_pip_value_mt5.py
python scripts\psa_export_pip_cache.py
```

Confirmar: `config\pip_value_cache.json` com ≥18 símbolos.

### 1.2 Log institucional `[ECON_OPEN]`

**AIC já aplicou.** Cada abertura aprovada deve logar:

```
[ECON_OPEN] lot=... SL=...pts($...) TP=...pts($...) spread=$... swap_est=$... comm=$... net_edge=$... pip_val=...
```

**Critério:** próximas 10 aberturas índice com **TP_usd ≥ 25** no log.

### 1.3 Atualizar pisos FORCE NOW

Editar `config\omega_trade_economics.json`:

```json
"min_tp_usd": {
  "index": 25.0,
  "forex": 10.0,
  "jpy_major": 10.0,
  "commodity": 18.0,
  "metal": 18.0,
  "crypto": 15.0,
  "crypto_alt": 8.0
}
```

Editar `scripts\run_omega_24x7.ps1` (alinhar env):

```powershell
$env:OMEGA_MIN_TP_USD_INDEX = "25"
$env:OMEGA_MIN_TP_USD_FOREX = "10"
$env:OMEGA_MIN_TP_USD_METAL = "18"
$env:OMEGA_MIN_TP_USD_CRYPTO = "15"
$env:OMEGA_MIN_TP_USD_CRYPTO_ALT = "8"
$env:OMEGA_FORCE_HIGH_PERFORMANCE = "1"
$env:OMEGA_STALE_PROFIT_USD = "3.0"
$env:OMEGA_STALE_HOURS = "2"
$env:OMEGA_STALE_ACTION = "CLOSE"
```

### 1.4 Confirmar P0-A (não reverter)

- **SEM** `OMEGA_MAX_POS_PER_ASSET=1` no PS1  
- `OMEGA_USE_RISK_BUDGET=1`  
- Gate FIX-DUPL só se RiskBudget OFF  

### 1.5 USFE (manter)

- v1.1.2, peso 0.05, `[USFE]` em log — **não subir peso** sem CEO.

---

## FASE 2 — REINÍCIO FORCE NOW (5 min)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python -c "from modules.omega_usfe_engine import self_test; self_test()"
.\scripts\run_omega_24x7.ps1
```

MT5 **aberto e ligado**. Uma instância só.

---

## FASE 3 — PROVA ALTA PERFORMANCE (4 horas)

### 3.1 Monitorização contínua

```powershell
Get-Content "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log" -Wait -Tail 40
```

### 3.2 O que DEVE aparecer no log

| Padrão | Mínimo em 4h |
|--------|----------------|
| `[ECON_OPEN]` | ≥5 (se mercado aberto) |
| `[ECON_GATE] SKIP` | pode existir (proteção) |
| `[USFE]` | contínuo |
| `[STALE_EXIT]` | ≥1 se posição legada ficou presa |
| `MAX_POS_PER_ASSET=1` | **0** após reinício |
| `UnboundLocalError` | **0** |

### 3.3 O que DEVE aparecer no MT5

- Nova ordem índice (se sinal): coluna Profit do TP ≥ **$25**  
- Nenhuma nova ordem com TP **&lt; $10** em qualquer classe  
- Posições legadas: fechadas ou STALE exit documentado  

### 3.4 Screenshots obrigatórios (MT5)

1. Tab Trade — lista posições após 4h  
2. Uma ordem **índice** aberta pós-FORCE — TP/SL em **USD**  
3. History — últimas 10 deals com profit column  

---

## FASE 4 — ENTREGÁVEL ÚNICO (zip ou pasta)

`audit\forensic\FORCE_NOW_20260601\`

| # | Ficheiro |
|---|----------|
| 1 | `RELATORIO_FORCE_NOW_PSA.md` — checklist abaixo |
| 2 | `config\pip_value_cache.json` |
| 3 | `psa_pip_calibration_*.json` (último) |
| 4 | `omega_trade_economics.json` (pisos 25/10/18/15/8) |
| 5 | `git diff --stat` ou lista de ficheiros |
| 6 | `log_snippet_4h.txt` — últimas 500 linhas com ECON/USFE/STALE |
| 7 | Screenshots MT5 (3 PNG) |
| 8 | Tabela: ordens novas pós-FORCE (symbol, lot, TP_usd, SL_usd, resultado) |

---

## CHECKLIST FORCE NOW (PSA marca PASS/FAIL)

### Bloqueadores (todos PASS ou NO-GO)

- [ ] F0 — Posições legadas tratadas (STALE log **ou** Fase 2 PSA no sistema)
- [ ] F1 — `pip_value_cache.json` gerado
- [ ] F2 — Runner reiniciado pós-patch
- [ ] F3 — Zero `MAX_POS_PER_ASSET=1` em 4h de log
- [ ] F4 — ≥1 `[ECON_OPEN]` com TP_usd ≥ piso classe
- [ ] F5 — Zero novas ordens índice TP_usd &lt; 25
- [ ] F6 — MT5 screenshot prova TP em USD
- [ ] F7 — USFE 1.1.2 activo

### Desejável (não bloqueia GO se F4–F6 PASS)

- [ ] F8 — `[STALE_EXIT]` ≥1
- [ ] F9 — PnL paper 4h positivo ou relatório honesto se negativo
- [ ] F10 — `psa_skip_forensics` atualizado pós-FORCE

---

## VEREDITO PSA (escolher um)

| Veredito | Condição |
|----------|----------|
| **FORCE NOW PASS** | F0–F7 todos PASS |
| **FORCE NOW FAIL** | Qualquer F0–F7 FAIL — listar causa + fix em 1 página |

**Proibido:** escrever “100% operacional” ou “fundo pronto live”.

**Permitido:** “Paper opera com economia de fundo; componentes demonstram sinais em log; CEO pode calibrar semana.”

---

## O QUE NÃO FAZER

- Não desligar `ECON_GATE` para “abrir mais”.  
- Não `MAX_POS_PER_ASSET=1`.  
- Não aumentar peso USFE &gt; 0.05.  
- Não novo refactor fora desta lista.  
- Não outro documento — **só este + pacote FORCE_NOW_20260601**.

---

## MENSAGEM CEO (copiar para PSA)

**ASSUNTO: FORCE NOW — ALTA PERFORMANCE — EXECUTAR AGORA**

PSA — ordem **FORCE NOW** em `governance\CEO_FORCE_NOW_PSA_20260601.md`. Prazo **4 horas**. Fechar legado MT5, validar patch pip/ECON_OPEN, pisos TP **25/10/18/15/8**, reiniciar runner, entregar pasta `FORCE_NOW_20260601` com screenshots MT5. O fundo tem que **existir em paper** esta semana — não mais migalhas. Dúvidas: máximo 3 bullets; não expandir scope.

CEO — FORCE NOW

---

*Consolida: MANDATO 20260601 + auditoria AIC + incidentes US500/USDJPY/GER40/XAGUSD.*
