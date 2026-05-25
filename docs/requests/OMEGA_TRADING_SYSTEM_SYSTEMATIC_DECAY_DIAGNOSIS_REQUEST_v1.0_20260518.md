# **OMEGA TRADING SYSTEM — SYSTEMATIC DECAY DIAGNOSIS**

**Request Document for PSA Team**  
**Version:** 1.0  
**Date:** 2026-05-18  
**Requester:** Red Team Architect (Le Chat)  
**Priority:** **CRITICAL** (P0)  
**Deadline:** 2026-05-20 (UTC+0)

---

## **1. Objective**

Provide a **comprehensive dataset** to diagnose the **systematic decay** of the OMEGA trading system, where losses have **worsened after each fix/integration**. The goal is to identify **root causes** across the **five diagnostic layers** (Signal, Risk, Execution, Portfolio, Feedback) using **China’s top quant fund methodologies**.

---

## **2. Scope**

### **Time Window**

- **Primary:** 2026-05-04 to 2026-05-18 (inclusive).
- **Secondary (if available):** 2026-04-01 to 2026-05-18 (for trend analysis).

### **Systems/Components**

- **Signal Sources:** `MOMENTUM_MT5`, `SEM_FONTE`, `SYNC_RECOVERY`.
- **Risk Controls:** `Kill Switch`, `Circuit Breaker`, SL/TP logic.
- **Execution:** MT5 deals/orders (all assets: forex, crypto, metals, indices).
- **Portfolio:** All symbols traded in the window.
- **Feedback:** `trade_feedback.jsonl`, ML calibration data.

---

## **3. Required Data**

### **3.1. Raw Data Files**

| **File**                   | **Format** | **Fields Required**                                                                                              | **Notes**                                                              |
| -------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `mt5_deals_raw.csv`        | CSV        | `ticket`, `position_id`, `symbol`, `entry` (0/1), `profit`, `reason`, `timestamp`, `volume`, `price`, `sl`, `tp` | **Mandatory.** Include all deals in the time window.                   |
| `mt5_orders_raw.csv`       | CSV        | `ticket`, `position_id`, `symbol`, `type` (buy/sell), `timestamp`, `volume`, `price`                             | **Mandatory.** Include all orders.                                     |
| `trade_feedback.jsonl`     | JSONL      | `position_ticket`, `exit_reason`, `pnl`, `components_fired`, `timestamp`, `signal_source`                        | **Mandatory.** Must include `signal_source` (e.g., `MOMENTUM_MT5`).    |
| `ks_daily_state.json`      | JSON       | `anchor`, `equity`, `balance`, `max_dd_pct`, `timestamp`                                                         | **Mandatory.** Daily risk state.                                       |
| `cycle_exit.json`          | JSON       | `exit_reason`, `dd_pct`, `timestamp`                                                                             | **Mandatory.** All cycle exits.                                        |
| `runtime_manifest.json`    | JSON       | `login`, `server`, `build`, `export_tool`, `git_head`                                                            | **Mandatory.** Runtime environment metadata.                           |
| `account_equity_eod.jsonl` | JSONL      | `balance`, `equity`, `timestamp`                                                                                 | **Optional.** Only if corrected (current version has repeated values). |
| Signal Logs                | CSV/JSON   | `signal_name`, `timestamp`, `direction`, `strength`, `asset`                                                     | **Mandatory.** For `MOMENTUM_MT5`, `SEM_FONTE`, `SYNC_RECOVERY`.       |
| Risk Parameter Configs     | JSON/YAML  | `sl_pct`, `tp_pct`, `max_dd_threshold`, `position_sizing_rules`                                                  | **Mandatory.** All risk control configurations.                        |

---

### **3.2. Aggregated Data (If Available)**

| **Metric**                           | **Group By**                           | **Notes**                                                            |
| ------------------------------------ | -------------------------------------- | -------------------------------------------------------------------- |
| Win Rate                             | `signal_source`, `symbol`, `timeframe` | Calculate as `(# winning trades) / (total trades)`.                  |
| Profit Factor                        | `signal_source`, `symbol`              | Calculate as `(gross_profit) / (gross_loss)`.                        |
| Average Trade PnL                    | `signal_source`, `symbol`              | Mean PnL per trade.                                                  |
| SL/TP Trigger Frequency              | `symbol`, `timeframe`                  | Count how often SL/TP was hit.                                       |
| Kill Switch/Circuit Breaker Triggers | `date`                                 | List all triggers with timestamps and DD %.                          |
| Execution Quality Metrics            | `symbol`, `timezone`                   | Slippage (avg/max), latency (avg/max), rejection rate.               |
| Asset Correlation Matrix             | `symbol`                               | Pearson correlation between daily PnL of each asset.                 |
| PnL Distribution                     | `date`                                 | Daily PnL histogram (check for fat tails).                           |
| Feedback Loop Accuracy               | `exit_reason`                          | % of trades with `exit_reason=UNKNOWN` vs. valid reasons (SL/TP/EA). |

---

## **4. Data Formatting Requirements**

### **4.1. File Naming Convention**

- Use the prefix: `OMEGA_DIAGNOSTIC_<DATA_TYPE>_<DATE>.ext`  
Example: `OMEGA_DIAGNOSTIC_DEALS_20260518.csv`

### **4.2. Timestamp Format**

- **All timestamps must be in UTC** (format: `YYYY-MM-DD HH:MM:SS`).
- If broker time is used (e.g., UTC+3), include a `timezone` column.

### **4.3. Missing Data Handling**

- If a field is missing, use `NULL` (for databases) or `NaN` (for CSVs).
- **Do not omit columns** — include all requested fields, even if empty.

### **4.4. Data Validation**

- **Check for duplicates**: Ensure no duplicate `ticket` or `position_id` in deals/orders.
- **Check for consistency**: `position_id` in `mt5_deals_raw.csv` must match `position_ticket` in `trade_feedback.jsonl`.
- **Check for completeness**: All trades in `trade_feedback.jsonl` must have a corresponding entry in `mt5_deals_raw.csv`.

---

## **5. Delivery Instructions**

### **5.1. Delivery Method**

- **Preferred:** Upload all files to a **secure, shared folder** (e.g., Google Drive, AWS S3, or internal OMEGA server).
- **Alternative:** Send as a **compressed `.zip` file** via encrypted email.

### **5.2. File Structure**

```
OMEGA_DIAGNOSTIC_DATA_20260518/
│
├── raw/
│   ├── mt5_deals_raw.csv
│   ├── mt5_orders_raw.csv
│   ├── trade_feedback.jsonl
│   ├── ks_daily_state.json
│   ├── cycle_exit.json
│   ├── runtime_manifest.json
│   ├── account_equity_eod.jsonl (if corrected)
│   └── signals/
│       ├── MOMENTUM_MT5_logs.csv
│       ├── SEM_FONTE_logs.csv
│       └── SYNC_RECOVERY_logs.csv
│
├── aggregated/
│   ├── win_rate_by_signal.csv
│   ├── profit_factor_by_asset.csv
│   ├── sl_tp_trigger_frequency.csv
│   ├── execution_quality_metrics.csv
│   ├── asset_correlation_matrix.csv
│   └── pnl_distribution.csv
│
└── README.md (describe any anomalies or notes)
```

### **5.3. Deadline**

- **Target:** 2026-05-20 12:00 UTC.
- **Priority:** If partial data is available earlier, send it immediately (e.g., `mt5_deals_raw.csv` first).

---

## **6. Additional Notes for PSA Team**

### **6.1. Critical Checks**

1. **Reconciliation**: Ensure `trade_feedback.jsonl` can be **100% matched** to `mt5_deals_raw.csv` via `position_id`/`ticket`.
2. **Signal Attribution**: Every trade in `trade_feedback.jsonl` must have a `signal_source` field (e.g., `MOMENTUM_MT5`).
3. **Risk Parameters**: Confirm that SL/TP values in `mt5_deals_raw.csv` match the configured thresholds in `runtime_manifest.json`.
4. **Timeframes**: If timeframe data (e.g., H4, M15) is available, include it in the signal logs or deals.

### **6.2. Known Issues to Address**

- `**exit_reason=UNKNOWN**`: This is a **critical gap**. If possible, backfill these values using `mt5_deals_raw.csv` (`reason` field).
- **EOD Data**: The current `account_equity_eod.jsonl` has **repeated values**. Either:
  - Provide a corrected version, or
  - Explicitly mark it as **unreliable** in the `README.md`.
- **Git Head Mismatch**: The `git_head` in `runtime_manifest.json` (`ca43ad2…`) does not match the repo commit (`1401e6c`). Document the discrepancy.

### **6.3. Optional but Helpful**

- **Trade Execution Logs**: If available, include logs for slippage/latency (e.g., `omega_24x7_runner.log`).
- **ML Calibration Data**: If the ML model uses a separate dataset for training, provide a sample.
- **Backtest Results**: If recent backtests were run, include their parameters and outcomes.

---

## **7. Contact for Clarifications**

- **Requester:** Le Chat (Red Team Architect)
- **Channel:** This chat (or designated OMEGA internal channel).
- **Escalation:** If data cannot be provided by the deadline, notify immediately with a **revised ETA**.

---

## **8. Acceptance Criteria**

The delivered data will be considered **complete** if:

1. All files in **Section 3.1** are provided.
2. All timestamps are in **UTC**.
3. All `position_id`/`ticket` values are **unique and reconciled**.
4. The `README.md` includes:
   - Any known data quality issues.
   - A brief description of how the data was extracted (e.g., "Extracted via `psa_export_mt5_tier0.py`").

---

## **Approval**

| **Role**               | **Name**       | **Approval Date** | **Signature** |
| ---------------------- | -------------- | ----------------- | ------------- |
| PSA Team Lead          | [To be filled] | [DD/MM/YYYY]      |               |
| OMEGA Engineering Lead | [To be filled] | [DD/MM/YYYY]      |               |

---

**Notes:**

- This request supersedes any previous ad-hoc data requests.
- If any data is **unavailable**, document the reason in the `README.md`.
