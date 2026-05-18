# OMEGA_DIAGNOSTIC_DATA_20260518

**Gerado por:** `scripts/build_omega_diagnostic_package_20260518.py`  
**Data build UTC:** 2026-05-18T22:05:12.406550+00:00  
**Pedido CEO:** `docs/requests/OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v2.0_20260518.md`  
**Avaliação / gaps PSA:** `docs/requests/OMEGA_TRADING_SYSTEM_FINAL_EVALUATION_AND_NEXT_STEPS_v2.0_20260518.md`

## 1. Método de extracção

- **MT5 deals/orders:** cópia enriquecida a partir de `audit/psa_inbound/PSA_PACOTE_TIER0_20260518_204618Z/` com `timestamp_utc` (UTC naive `YYYY-MM-DD HH:MM:SS`), `sl`/`tp` via join `position_id` → `mt5_orders_raw` ou regex `\[sl …\]` no comentário.
- **trade_feedback:** filtro 2026-05-04–2026-05-18; `exit_reason` backfill a partir do **último** deal `entry=1` do mesmo `position_id` (mapeamento MT5 → etiqueta SL/TP/EXPERT/…).
- **cycle_exit:** **50** eventos `run_end` exportados de `audit/paper/evaluation_timeline.jsonl` com `generated` na janela **2026-05-04**–**2026-05-18** (ficheiro: `raw/OMEGA_DIAGNOSTIC_cycle_exit_20260518.json`). Campo `dd_pct_inferred` é regex sobre texto — validar com PSA quando existir série KS.
- **ks_daily_state:** apenas instantâneo disponível em `audit/risk/ks_daily_state.json` — exportado como **array JSON de 1 elemento** (série diária completa: **não disponível** sem novo export PSA).
- **Sinais (FlowSignal):** regex `FlowSignal` em `omega_24x7_runner.log` + `paper_loop_202605*.log`; aceita `src` contendo qualquer de MOMENTUM, SEM_FONTE, SYNC_RECOVERY. Coluna `timestamp_utc` = prefixo naive do log **menos** `--flow-signal-local-offset-hours` (neste build: **0.0** h). Ver coluna `provenance` / `log_time_assumption` nos CSVs.
- **SEM_FONTE:** linhas `FlowSignal` com `SEM_FONTE` no `src` (**0**) + proxy a partir de `trade_feedback` `position_closed` com `signal_source` vazio/`SEM_FONTE` (**507** posições únicas por `position_ticket`).
- **SYNC_RECOVERY:** linhas FlowSignal com `SYNC_RECOVERY` no `src` (**0**) + `trade_feedback` com `signal_source=SYNC_RECOVERY` (**22** posições únicas). Neste build: **22** linhas no CSV total; se `FlowSignal=0`, todas vêm de `trade_feedback` (dedupe por `position_ticket`).

## 1.1 Contagens verificadas (ficheiros gerados)

| Ficheiro (sob `OMEGA_DIAGNOSTIC_DATA_20260518/`) | Linhas / registos de dados |
| --- | ---: |
| `raw/OMEGA_DIAGNOSTIC_mt5_deals_raw_20260518.csv` | 3563 |
| `raw/OMEGA_DIAGNOSTIC_mt5_orders_raw_20260518.csv` | 3562 |
| `raw/OMEGA_DIAGNOSTIC_trade_feedback_20260518.jsonl` | 1040 |
| `raw/OMEGA_DIAGNOSTIC_ks_daily_state_20260518.json` | 1 elemento(s) no array JSON |
| `raw/OMEGA_DIAGNOSTIC_cycle_exit_20260518.json` | 50 |
| `raw/signals/OMEGA_DIAGNOSTIC_MOMENTUM_MT5_logs_20260518.csv` | 69591 |
| `raw/signals/OMEGA_DIAGNOSTIC_SEM_FONTE_logs_20260518.csv` | 507 |
| `raw/signals/OMEGA_DIAGNOSTIC_SYNC_RECOVERY_logs_20260518.csv` | 22 |
| `aggregated/OMEGA_DIAGNOSTIC_win_rate_by_signal_20260518.csv` | 105 |
| `aggregated/OMEGA_DIAGNOSTIC_profit_factor_by_asset_20260518.csv` | 27 |
| `aggregated/OMEGA_DIAGNOSTIC_sl_tp_trigger_frequency_20260518.csv` | 74 |
| `aggregated/OMEGA_DIAGNOSTIC_execution_quality_metrics_20260518.csv` | 11 |
| `aggregated/OMEGA_DIAGNOSTIC_asset_correlation_matrix_20260518.csv` | 729 |
| `aggregated/OMEGA_DIAGNOSTIC_pnl_distribution_20260518.csv` | 12 |

## 2. Issues conhecidos

- `account_equity_eod`: `reliability_flag=UNRELIABLE_REPEATED_VALUES` (valores repetidos no pacote PSA).
- `git_head`: ver `runtime_manifest` — dois campos (`git_head_at_package_export` vs `git_head_repo_HEAD_at_build`).
- **SEM_FONTE via `trade_feedback`:** `signal_source` nulo é tratado como **proxy SEM_FONTE** (convenção alinhada a scripts de auditoria internos); validar com PSA se algum fecho NULL não for SEM_FONTE.
- **`cycle_exit` `dd_pct_inferred`:** derivado por regex sobre `exit_detail` — pode falhar em formatos não previstos.
- **ks_daily_state série:** incompleta (1 snapshot).

## 3. Validação

- **Deals `ticket` duplicados:** 0 (lista: [])
- **trade_feedback backfill:** matched=1040, unmatched=0, unknown_before=1040, unknown_after=0
- **Ficheiros de log escaneados (FlowSignal):** 12835 ficheiros (`paper_loop_202605*.log` em `audit/paper/` + `omega_24x7_runner.log` quando existir).
- **Reconciliação `position_ticket` ↔ `position_id` em deals:** fechamentos em `trade_feedback` com ticket presente em `mt5_deals_raw.position_id`: 692 / 692 (amostra na janela filtrada).

## 4. Contacto

- **PSA / Operações:** [nome do lead — preencher].
- **Engenharia OMEGA / CTO:** ajustes ao script de build (`scripts/build_omega_diagnostic_package_20260518.py`).

