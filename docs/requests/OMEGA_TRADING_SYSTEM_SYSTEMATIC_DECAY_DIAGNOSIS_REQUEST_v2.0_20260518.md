# OMEGA TRADING SYSTEM — SYSTEMATIC DECAY DIAGNOSIS

**Final Data Request for PSA Team**  
**Version:** 2.0  
**Date:** 2026-05-18  
**Requester:** Red Team Architect (Le Chat)  
**Priority:** CRITICAL (P0)  
**Deadline:** 2026-05-20 12:00 UTC  

This document **supersedes all previous requests** and is the actionable checklist for PSA to deliver data diagnosing **systematic decay** across five layers: **Signal, Risk, Execution, Portfolio, Feedback** (methodologies aligned with institutional quant practice).

---

## 1. Objective

Identify **root causes** of decay using reproducible exports, UTC-normalised timestamps, and reconciled joins between MT5 deals, orders, paper feedback, and evaluation timeline.

---

## 2. Scope and context

### 2.1 Time window

- **Primary:** 2026-05-04 to 2026-05-18 (inclusive).
- **Secondary (if available):** 2026-04-01 to 2026-05-18 (trend context).

### 2.2 Prior PSA tracking

Gaps listed in `docs/requests/OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v1.0_20260518.md` and `audit/psa_inbound/OMEGA_DIAGNOSTIC_DATA_20260518/README_STATUS_vs_CEO_REQUEST_v1.md` are **closed in v2.0** by either delivery or explicit documentation in package `README.md`.

### 2.3 Key issues (v2 resolution path)

| Issue | Impact | Action |
| --- | --- | --- |
| `exit_reason=UNKNOWN` in `trade_feedback.jsonl` | Feedback layer | Backfill from `mt5_deals_raw.csv` `reason` (match `position_id`) |
| Missing `sl`, `tp` on deals | Risk layer | Parse `comment` and/or join `mt5_orders_raw.csv` |
| `ks_daily_state.json` snapshot only | Risk trends | Export historical daily states or document unavailability |
| `cycle_exit` partial | Risk layer | Export all cycle exits from `evaluation_timeline.jsonl` |
| Missing signal logs (`MOMENTUM_MT5`, `SEM_FONTE`, `SYNC_RECOVERY`) | Signal layer | Extract from `paper_loop_*.log` / shadow runner logs |
| Missing risk configs | Risk layer | `risk_config_snapshot_*.json` from effective runtime values |
| `account_equity_eod.jsonl` repeated values | Portfolio layer | Mark unreliable in `README.md` or correct source |
| `git_head` mismatch in `runtime_manifest.json` | Provenance | Document in `README.md` |

---

## 3. Final data request

### 3.1 Raw tree (mandatory)

```
OMEGA_DIAGNOSTIC_DATA_20260518/
├── raw/
│   ├── OMEGA_DIAGNOSTIC_mt5_deals_raw_20260518.csv
│   ├── OMEGA_DIAGNOSTIC_mt5_orders_raw_20260518.csv
│   ├── OMEGA_DIAGNOSTIC_trade_feedback_20260518.jsonl
│   ├── OMEGA_DIAGNOSTIC_ks_daily_state_20260518.json
│   ├── OMEGA_DIAGNOSTIC_cycle_exit_20260518.json
│   ├── OMEGA_DIAGNOSTIC_runtime_manifest_20260518.json
│   ├── OMEGA_DIAGNOSTIC_account_equity_eod_20260518.jsonl
│   ├── OMEGA_DIAGNOSTIC_risk_config_20260518.json
│   └── signals/
│       ├── OMEGA_DIAGNOSTIC_MOMENTUM_MT5_logs_20260518.csv
│       ├── OMEGA_DIAGNOSTIC_SEM_FONTE_logs_20260518.csv
│       └── OMEGA_DIAGNOSTIC_SYNC_RECOVERY_logs_20260518.csv
├── aggregated/
│   ├── OMEGA_DIAGNOSTIC_win_rate_by_signal_20260518.csv
│   ├── OMEGA_DIAGNOSTIC_profit_factor_by_asset_20260518.csv
│   ├── OMEGA_DIAGNOSTIC_sl_tp_trigger_frequency_20260518.csv
│   ├── OMEGA_DIAGNOSTIC_execution_quality_metrics_20260518.csv
│   ├── OMEGA_DIAGNOSTIC_asset_correlation_matrix_20260518.csv
│   └── OMEGA_DIAGNOSTIC_pnl_distribution_20260518.csv
└── README.md
```

### 3.2 Raw file specifications (summary)

| File | Source (indicative) | Required fields / notes |
| --- | --- | --- |
| `mt5_deals_raw` | PSA Tier0 pack | `ticket`, `position_id`, `symbol`, `entry`, `profit`, `reason`, `timestamp_utc`, `volume`, `price`, **`sl`, `tp`**; UTC; SL/TP from comment or orders join |
| `mt5_orders_raw` | PSA Tier0 pack | `ticket`, `position_id`, `symbol`, `type`, `timestamp_utc`, `volume`, `price`, `sl`, `tp` |
| `trade_feedback` | `audit/paper/trade_feedback.jsonl` | Backfill `UNKNOWN` from deals; `signal_source` populated where possible |
| `ks_daily_state` | New export | **Time series:** one row per day with `anchor`, `equity`, `balance`, `max_dd_pct`, `timestamp_utc` — or document gap |
| `cycle_exit` | `evaluation_timeline.jsonl` | **All** `run_end` / cycle exits in window |
| `runtime_manifest` | PSA pack | Include `git_head`; mismatch documented in `README.md` |
| `account_equity_eod` | PSA pack | Mark repeated-value series as unreliable if not corrected |
| Signal CSVs | Logs | `signal_name`, `timestamp_utc`, `direction`, `strength`, `asset`, `timeframe` |
| `risk_config` | Engineering / env | `sl_pct`, `tp_pct`, `max_dd_threshold`, `position_sizing_rules`, `kill_switch_threshold`, `circuit_breaker_threshold` |

### 3.3 Aggregated files (mandatory)

| File | Group by | Metrics |
| --- | --- | --- |
| `win_rate_by_signal` | `signal_source`, `symbol`, `timeframe` | counts, `win_rate`, `profit_factor`, `avg_pnl` |
| `profit_factor_by_asset` | `symbol` | gross profit/loss, `profit_factor`, `total_trades` |
| `sl_tp_trigger_frequency` | `symbol`, `timeframe` | SL/TP counts and rates from deal `reason` (e.g. 4=SL, 5=TP) |
| `execution_quality_metrics` | `symbol`, `timezone` | slippage/latency/rejection where available |
| `asset_correlation_matrix` | symbols | Pearson on **daily** PnL per pair |
| `pnl_distribution` | `date` | `daily_pnl`; histogram bins or documented placeholder |

---

## 4. Formatting rules

- Timestamps: **UTC**, `YYYY-MM-DD HH:MM:SS`. If broker time used in conversion, document offset in `README.md` (and optional `timezone` column).
- Missing values: `null` (JSON) / empty or `NaN` (CSV) per team convention — **do not drop columns**.
- Encoding: UTF-8. CSV comma-separated with headers.

---

## 5. Delivery

- **Preferred:** secure shared storage (internal server, S3, etc.).
- **Alternative:** encrypted `.zip` email.
- **Partial delivery:** encouraged if raw files are ready before aggregates.

---

## 6. Post-delivery validation (requester)

1. Reconciliation: `trade_feedback` ↔ `mt5_deals_raw` on `position_id` / `position_ticket`.
2. Timestamp consistency (UTC).
3. Field completeness vs §3.

---

## 7. Sign-off

| Role | Name | Date | Signature |
| --- | --- | --- | --- |
| PSA Team Lead | TBD | | |
| OMEGA Engineering Lead | TBD | | |

---

## 8. Engineering build (2026-05-18)

An automated first pass is generated by:

`python scripts/build_omega_diagnostic_package_20260518.py`

Output directory: `audit/psa_inbound/OMEGA_DIAGNOSTIC_DATA_20260518/`.

That package’s `README.md` records **known gaps** (e.g. `ks_daily_state` history, log timestamp timezone assumption, empty `SEM_FONTE` / `SYNC_RECOVERY` if strings absent in scanned logs). PSA remains accountable for **source-of-truth** exports and any corrections to EOD equity series.

---

## 9. Note

If any mandatory item is **unavailable**, document the reason and **ETA** in `README.md`. This v2.0 memo **replaces** prior PSA data requests for the same diagnostic programme.
