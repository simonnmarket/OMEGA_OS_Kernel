# Estado de cumprimento — pedido CEO *Systematic Decay Diagnosis* (P0)

**Pedido canónico (texto integral):**  
`docs/requests/OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v1.0_20260518.md`

**Deadline pedido:** 2026-05-20 12:00 UTC  
**Janela primária:** 2026-05-04 a 2026-05-18 (inclusive)

---

## Legenda

| Estado | Significado |
|--------|-------------|
| **OK** | Ficheiro existe, cobre a janela, formato utilizável |
| **PARCIAL** | Existe mas falham colunas, formato, ou histórico incompleto |
| **FALTA** | Ainda não entregue no layout `OMEGA_DIAGNOSTIC_DATA_20260518/` |
| **ENG** | Pode ser produzido por engenharia (script) a partir do repo |

---

## 3.1 Raw — mapeamento

| Ficheiro pedido | Estado actual | Evidência / notas |
|-----------------|---------------|-------------------|
| `raw/mt5_deals_raw.csv` | **PARCIAL → OK** | Entregue em `PSA_PACOTE_TIER0_20260518_204618Z/mt5_deals_raw.csv`. Tem `time` ISO com offset (não `YYYY-MM-DD HH:MM:SS` UTC puro); **não** tem colunas dedicadas `sl`, `tp` (SL/TP aparecem em `comment` tipo `[sl …]` ou em `mt5_orders_raw`: `sl`, `tp`). **PSA:** copiar para `OMEGA_DIAGNOSTIC_DATA_20260518/raw/` com prefixo de naming CEO **ou** export v2 com colunas pedidas + `timezone`. |
| `raw/mt5_orders_raw.csv` | **PARCIAL → OK** | Idem pacote Tier-0; inclui `sl`, `tp`, `time_done`. Renomear / tree CEO. |
| `raw/trade_feedback.jsonl` | **PARCIAL** | Existe `audit/paper/trade_feedback.jsonl` (janela tem eventos). **Gaps:** muitos `exit_reason=UNKNOWN`; `signal_source` por vezes `null` — viola critério 6.1.2 até backfill ou correcção do writer. |
| `raw/ks_daily_state.json` | **PARCIAL** | Existe `audit/risk/ks_daily_state.json` — **instantâneo** (último dia), não série diária com `timestamp` por dia. **PSA/ENG:** export histórico ou ficheiro por dia. |
| `raw/cycle_exit.json` | **PARCIAL** | Existe `audit/paper/cycle_exit.json` — típico **último ciclo**, não “all cycle exits”. **PSA:** `evaluation_timeline.jsonl` filtrado ou JSONL de todos os `cycle_exit`. |
| `raw/runtime_manifest.json` | **OK** | No pacote Tier-0. Corrigir `git_head` vs commit do repo (nota CEO 6.2). |
| `raw/account_equity_eod.jsonl` | **PARCIAL** | No pacote; valores repetidos — marcar **unreliable** no README ou corrigir captura. |
| `raw/signals/MOMENTUM_MT5_logs.csv` | **FALTA** | Não existe pasta `signals/` dedicada; sinais estão dispersos em logs `paper_loop_*.log` / `shadow_loop`. **PSA:** extrair para CSV conforme schema pedido. |
| `raw/signals/SEM_FONTE_logs.csv` | **FALTA** | Idem. |
| `raw/signals/SYNC_RECOVERY_logs.csv` | **FALTA** | Idem. |
| Risk configs (YAML/JSON) | **FALTA / ENG** | Parâmetros dispersos em `shadow_loop.py`, env, `paper_summary` skips — **ENG** pode gerar snapshot `risk_config_snapshot_*.json` a partir de valores efectivos no dia do export. |

---

## 3.2 Aggregated — mapeamento

| Artefacto pedido | Estado | Notas |
|------------------|--------|--------|
| `aggregated/win_rate_by_signal.csv` | **ENG** | Pode ser gerado cruzando `trade_feedback` + deals; ainda não entregue na pasta CEO. |
| `aggregated/profit_factor_by_asset.csv` | **ENG** | Idem (a partir de deals por `symbol`). |
| `aggregated/sl_tp_trigger_frequency.csv` | **ENG** | Idem (`reason` 4/5 em deals OUT + timeframe de `OV2|` comment). |
| `aggregated/execution_quality_metrics.csv` | **PARCIAL** | `paper_summary.json` / logs têm latência/slippage pontuais; falta agregação por símbolo/timezone no formato pedido. |
| `aggregated/asset_correlation_matrix.csv` | **ENG** | Requer série PnL diária por símbolo (construir a partir de deals). |
| `aggregated/pnl_distribution.csv` | **ENG** | Histograma diário de PnL. |

**Relatório já gerado (engenharia, não substitui o pacote CEO):**  
`audit/CEO_RELATORIO_OPERACOES_COMPLETO_20260504_20260518.md` — contém agregações e dados brutos anexados; pode ser **referenciado** no README do pacote diagnóstico até PSA reorganizar ficheiros.

---

## Naming e estrutura (secção 5.2)

A árvore `OMEGA_DIAGNOSTIC_DATA_20260518/` neste commit contém **apenas** este README de tracking.  
**PSA:** popular `raw/` e `aggregated/` conforme o pedido; renomear cópias para `OMEGA_DIAGNOSTIC_<TYPE>_<DATE>.ext` se o CEO exigir o prefixo literal.

---

## Validação (secção 4.4)

| Check | Estado |
|-------|--------|
| Duplicados `ticket` em deals | A verificar no próximo script PSA / eng. |
| `position_id` ↔ `position_ticket` | **Pendente** — script de reconciliação (próxima entrega ENG). |
| Timestamps 100% UTC `YYYY-MM-DD HH:MM:SS` | **PARCIAL** — actualmente ISO-8601 com offset; converter se necessário. |

---

## Próxima acção recomendada (ordem)

1. PSA: criar `README.md` no pacote final com extração + issues (EOD, git_head, UNKNOWN).  
2. PSA ou ENG: export v2 deals com colunas `sl`, `tp`, `timestamp_utc` normalizado.  
3. ENG: script de reconciliação + CSVs `aggregated/` mínimos para não bloquear P0.  
4. PSA: logs de sinal em `raw/signals/*.csv`.

---

*Documento de apoio — OMEGA Engineering.*
