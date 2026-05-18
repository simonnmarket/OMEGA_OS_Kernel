# OMEGA TRADING SYSTEM — SCRIPT REVIEW AND NEXT STEPS

**Document Version:** 1.0  
**Date:** 2026-05-18  
**Requester:** Red Team Architect (Le Chat)  
**Status:** Ready for Execution  

---

## 1. Overview

The Python script `scripts/build_omega_diagnostic_package_20260518.py` targets the **CEO v2.0** diagnostic data package (`OMEGA_DIAGNOSTIC_DATA_20260518/`). This memo records review findings, PSA tasks, and optional hardening.

---

## 2. Script Review

### 2.1 Strengths

- Enriches **MT5 deals/orders** with `sl`, `tp`, and UTC-oriented timestamps.
- Backfills **`exit_reason=UNKNOWN`** in filtered `trade_feedback` using the last OUT deal per `position_id`.
- Builds **aggregated** CSVs (win rate, profit factor, SL/TP frequency, execution sample, correlation matrix, daily PnL).
- Outputs the **folder layout** required by v2.0 and a generated **`README.md`** (methods, issues, validation counters).
- **Risk snapshot** JSON includes CEO field names with `null` where values are not sourced from `shadow_loop`/env.

### 2.2 Gaps (PSA / source data)

| Topic | Risk | PSA / follow-up |
| --- | --- | --- |
| `ks_daily_state` | Only snapshot on disk | Export daily history or keep README gap |
| Full **risk_config** (`sl_pct`, `tp_pct`, kill switch, circuit breaker) | `null` in engineering build | Export from runtime config |
| **`account_equity_eod`** | Repeated values | Fix capture or confirm unreliable |
| **FlowSignal clock** | Naive log prefix may be local broker time | Confirm offset; script supports `--flow-signal-local-offset-hours` |
| **`dd_pct` on cycle exits** | Regex inference | Validate vs KS / timeline text |

### 2.3 Engineering updates (post-review, same day)

Implemented in `build_omega_diagnostic_package_20260518.py`:

1. **FlowSignal `src` filter** — accepts any of `MOMENTUM`, `SEM_FONTE`, `SYNC_RECOVERY` in `src` (not only MOMENTUM).
2. **`--flow-signal-local-offset-hours`** — subtracts N hours from naive log timestamps before writing `timestamp_utc` (default `0`).
3. **`--no-sem-fonte-null-proxy`** — disables SEM_FONTE proxy rows inferred from empty `signal_source` in `trade_feedback`.
4. **SEM_FONTE CSV** — FlowSignal lines (if any) **plus** one row per unique `position_ticket` (or fallback key) for `position_closed` with null/empty/`SEM_FONTE` `signal_source` (**proxy**; documented in package `README.md`).
5. **SYNC_RECOVERY CSV** — FlowSignal lines (if any) **plus** deduped rows from `trade_feedback` where `signal_source=SYNC_RECOVERY`.
6. **Signal CSV columns** — `provenance`, `position_ticket`, `log_timestamp_offset_hours_applied`, unified schema across the three files.

---

## 3. Next Steps for PSA (before 2026-05-20 12:00 UTC)

| Task | Owner | Priority |
| --- | --- | --- |
| Run the builder; deliver `OMEGA_DIAGNOSTIC_DATA_20260518/` | PSA / Engineering | P0 |
| Confirm **log timezone** vs broker; re-run with `--flow-signal-local-offset-hours` if needed | PSA | P1 |
| Export **historical `ks_daily_state`** or sign off gap in `README.md` | PSA | P0 |
| Export full **risk parameters** into `risk_config` | PSA | P0 |
| Correct or formally accept **EOD equity** unreliability | PSA | P1 |

---

## 4. Post-delivery (Red Team)

- Reconcile `position_ticket` ↔ `position_id` (target: full match in window).
- Validate SL/TP / exit_reason consistency vs MT5.
- Produce the **systematic decay diagnostic report** after data sign-off.

---

## 5. Delivery confirmation

1. Upload `OMEGA_DIAGNOSTIC_DATA_20260518/` to the agreed secure location.
2. Notify Red Team with path + any residual gaps (mirrored in `README.md`).
3. Sign off in the v2.0 request approval table when satisfied.

---

## 6. Approval

| Role | Name | Date | Signature |
| --- | --- | --- | --- |
| PSA Team Lead | TBD | | |
| OMEGA Engineering Lead | TBD | | |

---

## 7. Support

- **Red Team Architect:** Le Chat (chat thread).  
- **Engineering:** OMEGA Engineering Lead (TBD).

---

**Note:** This memo is actionable alongside `OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v2.0_20260518.md`.
