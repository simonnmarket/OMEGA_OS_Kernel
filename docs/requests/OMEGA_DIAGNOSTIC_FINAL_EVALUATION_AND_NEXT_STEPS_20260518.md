# Avaliação final — Script + Pacote `OMEGA_DIAGNOSTIC_DATA_20260518` e próximos passos

> **Supersedido por:** `OMEGA_TRADING_SYSTEM_FINAL_EVALUATION_AND_NEXT_STEPS_v2.0_20260518.md` (documento CEO v2.0 em inglês + checklist PSA).

**Data:** 2026-05-18  
**Contexto:** Pós-execução de `scripts/build_omega_diagnostic_package_20260518.py` (CEO v2.0 + review de script).

---

## Resumo executivo

O script foi **executado com sucesso** e gera o pacote sob `audit/psa_inbound/OMEGA_DIAGNOSTIC_DATA_20260518/` com:

- Filtro FlowSignal alargado (`MOMENTUM`, `SEM_FONTE`, `SYNC_RECOVERY` no `src`).
- Ajuste opcional de relógio nos logs: `--flow-signal-local-offset-hours`.
- Proxy **SEM_FONTE** a partir de `trade_feedback` com `signal_source` nulo (dedupe por `position_ticket`), desligável com `--no-sem-fonte-null-proxy`.
- **SYNC_RECOVERY** a partir de `trade_feedback` (neste dataset, **sem** linhas FlowSignal com esse `src` nos ficheiros analisados).
- Backfill de `exit_reason=UNKNOWN`, reconciliação `position_ticket` ↔ `position_id`, agregados e `README.md` automático.

A completude **“95% / 5%”** é uma **ordem de grandeza narrativa**: em volume de linhas o pacote está quase completo; em **dimensões de risco** (série KS, `risk_config` total, EOD fiável) continuam **lacunas P0/P1** documentadas no `README.md` do pacote.

---

## Contagens verificadas (build em disco, 2026-05-18)

Valores obtidos por contagem directa dos ficheiros gerados (dados = linhas − cabeçalho para CSV; `cycle_exit` = comprimento do array JSON).

| Ficheiro | Linhas / registos de dados | Notas |
| --- | ---: | --- |
| `raw/OMEGA_DIAGNOSTIC_mt5_deals_raw_20260518.csv` | 3 562 | +1 linha cabeçalho |
| `raw/OMEGA_DIAGNOSTIC_mt5_orders_raw_20260518.csv` | 3 561 | +1 cabeçalho |
| `raw/OMEGA_DIAGNOSTIC_trade_feedback_20260518.jsonl` | 1 040 | Janela filtrada |
| `raw/OMEGA_DIAGNOSTIC_ks_daily_state_20260518.json` | **1** elemento no array | Snapshot apenas |
| `raw/OMEGA_DIAGNOSTIC_cycle_exit_20260518.json` | **50** eventos `run_end` | *Não* ~178 — corrigir relatórios que citam 178 |
| `raw/signals/OMEGA_DIAGNOSTIC_MOMENTUM_MT5_logs_20260518.csv` | 69 591 | FlowSignal |
| `raw/signals/OMEGA_DIAGNOSTIC_SEM_FONTE_logs_20260518.csv` | 507 | Neste build: proxy `trade_feedback`; FlowSignal `SEM_FONTE` = 0 |
| `raw/signals/OMEGA_DIAGNOSTIC_SYNC_RECOVERY_logs_20260518.csv` | 22 | Neste build: só `trade_feedback` dedupe; FlowSignal = 0 |
| `aggregated/..._win_rate_by_signal_20260518.csv` | **104** | ~100 ✓ |
| `aggregated/..._profit_factor_by_asset_20260518.csv` | **26** | ~30 (próximo) |
| `aggregated/..._sl_tp_trigger_frequency_20260518.csv` | **73** | ~50 (subestimado no rascunho) |
| `aggregated/..._execution_quality_metrics_20260518.csv` | **10** | `rejection_rate` = NaN |
| `aggregated/..._asset_correlation_matrix_20260518.csv` | **728** | 27×27 aprox.; *não* ~900 |
| `aggregated/..._pnl_distribution_20260518.csv` | **11** | ~15 (próximo) |

---

## Gaps restantes (PSA / follow-up)

| Item | Prioridade | Acção |
| --- | --- | --- |
| `ks_daily_state` série diária | P0 | Export PSA ou manter gap assinado no `README.md` |
| `risk_config` (`sl_pct`, `tp_pct`, kill switch, circuit breaker) | P0 | Valores efectivos (shadow/env) |
| `account_equity_eod` | P1 | Corrigir captura ou manter `reliability_flag` + nota |
| Fuso FlowSignal vs UTC | P1 | Se broker UTC+3: `--flow-signal-local-offset-hours 3` e republicar |
| `rejection_rate` | P2 | Só após padrão de log acordado |
| `dd_pct_inferred` em `cycle_exit` | P1 | Cruzar com KS / texto quando houver série KS |

---

## Pergunta ao PSA (para resposta explícita)

**Os gaps críticos (`ks_daily_state` histórico, `risk_config` completo, validação/correcção de EOD) podem ser fechados até 2026-05-20 12:00 UTC?**

- **Se sim:** republicar o pacote (ou delta) com ficheiros substituídos e actualizar o `README.md` com método e validação.
- **Se não:** manter limitações documentadas no `README.md` (já previsto no pedido CEO v2.0) e o Red Team prossegue diagnóstico **parcial** com incerteza explícita nas camadas Risk/Portfolio.

---

## Checklist de entrega

| Item | Estado |
| --- | --- |
| Pacote `OMEGA_DIAGNOSTIC_DATA_20260518/` gerado | Feito (engineering) |
| `README.md` com gaps | Feito |
| Série KS + `risk_config` completo + EOD | PSA / pendente |
| Assinaturas v2.0 | Pendente |

---

## Comunicação

- **PSA:** local seguro do pacote + lista de gaps remanescentes (espelhada no `README.md`).
- **Red Team:** validação pós-entrega e relatório de decay quando P0 estiver fechado ou aceite como parcial.
