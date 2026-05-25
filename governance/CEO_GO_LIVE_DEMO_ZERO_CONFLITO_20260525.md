# CEO — Go-Live DEMO sem conflitos (resolução total antes de reiniciar)

| Campo | Valor |
|-------|--------|
| **Documento** | CEO-GO-LIVE-DEMO-20260525 |
| **Emitido** | AIC Tech Lead |
| **Objectivo** | Resolver **agora** todas as pendências que podem causar conflito entre componentes antes de ligar conta **DEMO** |
| **Não substitui** | Merge PRs (ainda necessário para `main` oficial) |

---

## 0. Resposta directa à sua pergunta

**Sim, podemos resolver agora** tudo o que é **código + config + validação local**.

O que **não** se resolve sem mercado aberto / liquidez:

- Uma ordem real XAUUSD H4 com SL ≥ $20 no log (SM-R2 vivo) — precisa de sessão com volatilidade ou aceitar validação UT-R1 + 1 ciclo com `OMEGA_EDGE_METAL_ATR` relaxado em **demo**.

**Merge dos PRs** continua necessário para operar a partir de `main`, mas **não precisa esperar** para correr DEMO na branch `feat/execution-router-atr-20260523` após o pré-voo abaixo.

---

## 1. Mapa de conflitos — antes vs agora

| Conflito / risco | Antes | Agora (2026-05-25) |
|------------------|-------|---------------------|
| ATR M1 em sinal H4 (Falha A) | SL ~$2.50 | **T-R1** `get_execution_tf_atr(asset, tf)` |
| Comment MT5 >31 chars | Fecho falha | **511e230** + UT-9 |
| Lista fixa 32 ativos no 24×7 | Ignora schedule | **T-W1** PS1 sem lista |
| Fechos com mercado fechado | Spam MT5 | **T-W3** `is_market_open` |
| v2 activo no runner | Risco path errado | **T-P2b** + `OMEGA_USE_V2=0` no PS1 |
| partial_taken ausente | Ledger incompleto | **T-F1a** |
| Schedule só no arranque | FDS desactualizado | **T-W2** re-resolve por ciclo (**aplicado hoje**) |
| `restart_full_portfolio.ps1` | 16 símbolos fixos | **AVISO** — não usar pós-P0 |
| EDGE_GATE bloqueia XAU em baixa vol | SM-R2 N/A | **OMEGA_EDGE_METAL_ATR=0.0005** em `run_omega_24x7.ps1` + pré-voo |
| Cascata / M1-GATE (Falhas B/C) | Entrada tardia | **Fase 2** — não bloqueia demo piloto |

---

## 2. O que foi aplicado AGORA (código local)

| ID | Alteração | Ficheiro |
|----|-----------|----------|
| **T-W2** | Re-resolver `ativos` cada ciclo do runner | `scripts/omega_paper_loop_24x7.py` |
| **DEMO-EDGE** | `OMEGA_EDGE_METAL_ATR=0.0005` + `OMEGA_USE_V2=0` | `scripts/run_omega_24x7.ps1` |
| **GO-LIVE** | Script pré-voo + smokes | `scripts/omega_demo_go_live.ps1` |
| **DOC** | Este documento | `governance/CEO_GO_LIVE_DEMO_ZERO_CONFLITO_20260525.md` |

**PSA:** commitar na branch Router: `feat(execution-router-atr-20260523` com mensagem `fix(demo): T-W2 schedule + go-live preflight`.

---

## 3. Procedimento CEO — AGORA (ordem obrigatória)

### Passo 1 — Branch correcta

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout feat/execution-router-atr-20260523
git pull origin feat/execution-router-atr-20260523
```

(Após merge PRs, usar `main`.)

### Passo 2 — Pré-voo automático (15–45 min)

```powershell
& .\scripts\omega_demo_go_live.ps1
```

**PASS se:**

- pytest **34/34**
- Ciclos EURUSD H1 (×2) e XAUUSD H4 **exit 0**
- Reconcile **ALL PASS**
- **0** posições órfãs magic `234001` / `OV2|`
- Log **sem** `Invalid "comment" argument`

Relatório: `audit/demo_go_live/GO_LIVE_REPORT_*.txt`

### Passo 3 — Merge PRs (recomendado antes de 24×7 longo)

| PR | URL |
|----|-----|
| P0 | https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/1 |
| Router | https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/2 |

### Passo 4 — Arrancar DEMO 24×7 (forma correcta)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
& .\scripts\run_omega_24x7.ps1
```

**Usar isto** — não `restart_full_portfolio.ps1`.

---

## 4. O que NÃO usar (conflito com P0)

| Script / acção | Motivo |
|----------------|--------|
| `restart_full_portfolio.ps1` | Lista fixa 16 símbolos — bypassa `omega_asset_schedule.json` |
| `OMEGA_24X7_ATIVOS` manual com 32 ativos | Conflito T-W1 |
| `OMEGA_USE_V2=1` | v2 proibido no runner produção |
| Portfolio 32 sem autorização CEO | Fora mandato P0 |
| Conta **live** sem smoke com ordens | Risco capital |

---

## 5. Checklist “zero conflito” — marcar antes de ligar

```text
☐ Branch feat/execution-router-atr ou main pós-merge
☐ omega_demo_go_live.ps1 PASS
☐ MT5: Algo Trading ON, conta DEMO
☐ 0 posições OMEGA abertas
☐ PR #1 merged (recomendado)
☐ PR #2 merged (recomendado)
☐ run_omega_24x7.ps1 arrancado (NÃO restart_full_portfolio)
☐ Primeiros 30 min: ler audit/paper/omega_24x7_runner.log
☐ Confirmar [SCHEDULE] e [CIO-VERIFY] magic=234001 no log
```

---

## 6. Pendências honestas (não são “conflito de componentes”)

| Item | Bloqueia DEMO piloto? | Quando |
|------|------------------------|--------|
| Fase 2 Falha B/C (cascata, M1-GATE) | **Não** — comportamento de estratégia | Novo mandato |
| TRE | **Não** | Mandato novo |
| SM-R2 ordem com SL $20 no log | **Não** se pré-voo XAU H4 passar com EDGE relaxado | Ou sessão Londres |
| Merge PRs | **Não** para teste na branch | Antes de `main` longo prazo |

---

## 7. Mensagem PSA (commit final demo)

```text
PSA,

CEO autoriza resolução total antes DEMO. Aplicar/commitar na branch Router:

1) T-W2 omega_paper_loop_24x7.py (re-resolve schedule por ciclo) — AIC já editou local
2) run_omega_24x7.ps1 OMEGA_EDGE_METAL_ATR + OMEGA_USE_V2=0
3) scripts/omega_demo_go_live.ps1
4) governance/CEO_GO_LIVE_DEMO_ZERO_CONFLITO_20260525.md

pytest 34/34. CEO corre omega_demo_go_live.ps1 antes de 24x7.

Não usar restart_full_portfolio.ps1 para P0.
```

---

## 8. Veredito AIC

| Pergunta | Resposta |
|----------|----------|
| Dá para resolver conflitos **agora**? | **Sim** — código + config + pré-voo |
| Pode reiniciar DEMO após Passo 2 PASS? | **Sim** — com `run_omega_24x7.ps1` |
| Merge é única pendência? | **Não** — merge + pré-voo; merge sozinho não valida runtime |
| Tier-0 pleno sem Fase 2? | **Não** — mas **demo piloto alinhado P0+Fase1** é aceitável |

---

*AIC — Go-live DEMO sem conflito de componentes — 2026-05-25*
