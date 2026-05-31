# AUDITORIA CEO — FORCE NOW PARTIAL (2026-06-01)

**Base:** `RELATORIO_FORCE_NOW_PSA.md` + commit `935db24` + `omega_24x7_runner.log`  
**Veredito CEO:** **ACEITO — FORCE NOW PARTIAL (infra GO; prova operacional pendente)**

---

## O que está correto (alta confiança)

| Item | Avaliação |
|------|-----------|
| Commit `935db24` no branch forense | Confirmado |
| Pisos 25/10/18/15/8 + pip cache 21 símbolos | Pacote em `FORCE_NOW_20260601/` |
| F3 — sem `MAX_POS_PER_ASSET=1` pós-restart | Log 00:11+ sem o padrão (apenas histórico 23:35–23:42) |
| F7 — USFE 1.1.2 | Log `[USFE]` no restart |
| Gate economia | `[ECON_GATE] SKIP` com TP abaixo do piso — proteção activa |
| Linguagem PSA | Honesta — não declara live/100% |

**Conclusão infra:** O motor tem **economia de fundo em código e em log**. Isto responde ao pedido “não mais migalhas” no **envio** de novas ordens.

---

## Pontos a fechar (média confiança → PSA corrige)

### 1) F0 — fecho US500/GER40

PSA reporta retcode 10009. No log do runner, **00:15:53 UTC** ainda há `RESYNC` para `#192074499` e `#192105887`.

**PSA deve anexar (obrigatório na actualização 4h):**

- `reports/psa_close_positions_*.json` **ou** print MT5 History com OUT desses tickets
- `_check_magic_mt5.py` **depois** do fecho (snapshot sem US500/GER40)

Sem isso, F0 fica **PARTIAL documentado**, não PASS auditável.

### 2) F4–F6 — tempo e mercado

| Item | Janela |
|------|--------|
| Início runner FORCE | ~2026-06-01 00:11 UTC |
| **Relatório 4h** | Entregar até **~04:15 UTC** |
| F4 `[ECON_OPEN]` | Só com mercado aberto + sinal + lot ≥ piso |
| F5 | Automático se F4 PASS |
| F6 screenshots | **PSA** via MT5 (não só CEO) — 3 PNG no pacote |

### 3) Legado restante (6 + UKOIL)

Ainda ocupam slots / risco:

- `#192068976` USDCAD, `#192243746` AUDUSD, `#192243914` + `#192244227` USDJPY (duplicado), `#192248551` XRPUSD
- `#191908751` UKOIL+ — fechar quando mercado abrir

**Próximo mandato:** `governance/CEO_POS_FORCE_NOW_FASE2_PSA.md` (fecho no sistema, lista CEO aprova).

---

## Ordem CEO → PSA (agora)

```
FORCE NOW PARTIAL ACEITO (935db24). Manter runner.

1) Até 04:15 UTC: RELATORIO_FORCE_NOW_4H.md com F4–F6.
2) Anexar prova F0: psa_close JSON + snapshot MT5 pós-fecho US500/GER40.
3) F6: 3 screenshots MT5 no pacote (PSA captura).
4) UKOIL+ #191908751: fechar na abertura (psa_close_positions.py ou STALE).
5) Não alterar pisos/USFE peso sem ordem CEO.

Após 4H: CEO activa FASE 2 (legado restante) — aguardar ordem separada.
```

---

## O que o CEO pode esperar nas próximas 4h

- **Ver:** mais `[ECON_GATE] SKIP` — normal (protecção).
- **Ver (se mercado + sinal):** `[ECON_OPEN]` com TP_usd ≥ piso.
- **Ver (se legado >2h e profit baixo):** `[STALE_EXIT] CLOSE OK`.
- **Não exigir ainda:** PnL positivo garantido — é paper + weekend partial (log: `tier=WEEKEND_PARTIAL weight=0.38`).

---

*Auditoria AIC/CEO — não substitui relatório 4h do PSA.*
