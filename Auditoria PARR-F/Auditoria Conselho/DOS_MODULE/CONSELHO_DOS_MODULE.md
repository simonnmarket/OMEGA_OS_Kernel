# Pacote DOS_MODULE — nota para auditoria do Conselho

**Versão:** 1.1.0 (`omega-dos`)  
**Especificação de referência:** `DOC-OFC-DOS-TRADING-V1.0-20260405-001` — *DATA OPERATING SYSTEM - DOS* (documento final, 05/04/2026, utilizador Desktop).  
**Data de referência implementação:** 2026-03-27  
**Repositório:** `nebular-kuiper` (módulos `DOS_MODULE` + `FIN_SENSE_DATA_MODULE`)

## 1. Objectivo do pacote

1. **FIN-SENSE** — ingestão lógica e métricas sobre `bronze.demo_log_swing_trade` (`run_dos_pipeline`, proveniência SHA-256).
2. **DOS-TRADING V1.0** — replicação fiél do *blueprint* Conselho: camadas 1–4 sobre OHLC MT5, sinais, diagnóstico de falsos negativos, backtest simplificado; campo `spec_id` no relatório.
3. **Métricas Tier-0** — classe `Tier0Metrics` alinhada ao anexo `metrics_tier0.py` do documento (VaR/CVaR/RAROC/Sortino/Omega/Sharpe/Calmar).
4. **Backtrader** — módulo opcional `backtrader_dos` (extra `[backtrader]`), sem dependência obrigatória no núcleo.

## 2. Correcções aplicadas relativamente ao texto-base PDF/TXT

| Item | Acção |
|------|--------|
| `adaptive_filters` vs `vol_regime` | Mapeamento explícito `low`/`medium`/`high` → `low_vol`/`medium_vol`/`high_vol`. |
| `TradingSignal` | Inclusão de `direction` e `vol_regime`; `symbol` passado explicitamente (não `row.name`). |
| `inputs_sha256` | Cálculo via `sha256_canonical` sobre OHLC (evita hash frágil). |
| Logging | Ficheiro apenas se `DOS_LOG_FILE` estiver definido (evita falhas de permissão). |
| Quantil spread | Protecção quando `quantile(0.3)` é NaN. |

## 3. Pontos fortes (auditoria)

- Núcleo de risco **determinístico** (quantis empíricos, sem RNG nos defaults de `Tier0Metrics` / `risk.py`).
- Contratos de dados explícitos: `REQUIRED_SWING_COLS` (FIN-SENSE) e `time/open/high/low/close` (MT5).
- **Testes automatizados** (`pytest`): pipeline FIN-SENSE, DOS-TRADING com CSV sintético, `Tier0Metrics`.

## 4. Riscos e limitações

| Tópico | Severidade | Descrição |
|--------|------------|-----------|
| PnL sintético FIN-SENSE | Média | Ramo sintético até existir livro real. |
| Backtest DOS-TRADING | Média | Modelo académico simplificado (slippage fixo, saída por janela); não valida produção. |
| VaR/CVaR | Média | Históricos sobre amostra; não cobrem eventos fora da cauda observada. |
| Backtrader | Baixa | Dependência opcional; versão fixada em `pyproject` — validar ambiente antes de CI. |
| Digest JSON | Baixa | Séries gigantes: custo de memória/CPU no `sha256_canonical` de OHLC completo. |

## 5. Conflitos potenciais

- Schemas: DDL DOS em `dos.*` não altera `bronze` FIN-SENSE.
- Dois “pipelines” (FIN-SENSE vs MT5) partilham apenas dependências (`pandas`/`numpy`); não há escrita cruzada em tabelas sem código explícito do utilizador.

## 6. Verificação recomendada ao Conselho

- `python -m pytest -q` em `modules/DOS_MODULE`.
- Revisão: `omega_dos/trading/dos_trading_v1.py`, `omega_dos/metrics/institutional.py`, `omega_dos/pipeline.py`, `omega_dos/bridge_fin_sense.py`.
- Paridade `PGPASS` se usar Postgres.

---

*Este documento descreve desenho e limites técnicos; não substitui auditoria jurídica ou de negócio.*
