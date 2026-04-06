# Pacote DOS_MODULE — nota para auditoria do Conselho

**Versão:** 2.0.0 (`omega-dos`) — **HARDENED**
**Especificação de referência:** `DOC-OFC-DOS-TRADING-V1.0-20260405-001` — *DATA OPERATING SYSTEM - DOS* (documento final, 05/04/2026, utilizador Desktop).
**Data de referência implementação:** 2026-03-27
**Data de hardening:** 2026-04-06
**Repositório:** `nebular-kuiper` (módulos `DOS_MODULE` + `FIN_SENSE_DATA_MODULE`)
**Status:** ✅ **HARDENED** — Aprovado condicional para pesquisa e backtesting; hardening institucional aplicado.

## 1. Objectivo do pacote

1. **FIN-SENSE** — ingestão lógica e métricas sobre `bronze.demo_log_swing_trade` (`run_dos_pipeline`, proveniência SHA-256).
2. **DOS-TRADING V2.0** — replicação fiél do *blueprint* Conselho: camadas 1–4 sobre OHLC MT5, sinais com precisão Decimal, diagnóstico de falsos negativos, backtest sem look-ahead com custos variáveis.
3. **Métricas Tier-0** — classe `Tier0Metrics` alinhada ao anexo `metrics_tier0.py` do documento (VaR/CVaR/RAROC/Sortino/Omega/Sharpe/Calmar).
4. **Backtrader** — módulo opcional `backtrader_dos` (extra `[backtrader]`), sem dependência obrigatória no núcleo.

## 2. Hardening aplicado (Sprint 1-4 vs. auditoria AUDIT-DOS-MODULE-CONSELHO-20260406-001)

| #  | Pendência | Severidade | Estado |
|----|-----------|-----------|--------|
| C1 | Float → Decimal para preços/SL/TP | CRÍTICA | ✅ Resolvido (TradingSignal com Decimal, quantize 5 casas) |
| C2 | Backtest look-ahead bias | CRÍTICA | ✅ Resolvido (bar-a-bar SL/TP, custos variáveis) |
| C3 | SQL concatenação / segurança Postgres | CRÍTICA | ✅ Resolvido (SQL parametrizado, retry backoff, conn.close) |
| C4 | PnL sintético sem rotulagem | CRÍTICA | ✅ Resolvido (PNL_DISCLAIMER, pnl_type=HYPOTHETICAL) |
| H1 | Logging JSON estruturado | ALTA | ✅ Resolvido (_JSONFormatter, trace_id, correlation_id, masking) |
| H2 | Vetorização de sinais (iterrows) | ALTA | ✅ Resolvido (arrays numpy pré-computados) |
| H3 | Validação rígida schema MT5 | ALTA | ✅ Resolvido (dtypes, NaN/inf/outliers, OHLC consistência) |
| H4 | Retry/backoff Postgres telemetria | ALTA | ✅ Resolvido (_connect_with_retry, logging de falhas) |
| M1 | Digest OOM em datasets grandes | MÉDIA | ✅ Resolvido (digest incremental chunked) |
| M2 | Bins de volatilidade fixos | MÉDIA | ✅ Resolvido (VolatilityBins configurável) |
| M3 | Sanitização entrada MT5 | MÉDIA | ✅ Resolvido (price_floor/ceil, OHLC consistency check) |
| M4 | Backtrader chunking | MÉDIA | ⚠️ Nota: warning sugerido para séries > 500k |
| L1 | Masking credenciais em logs | BAIXA | ✅ Resolvido (regex _SENSITIVE em _JSONFormatter) |
| L2 | Wording divergente documentação | BAIXA | ✅ Resolvido (unificado para HARDENED) |
| L3 | sklearn clustering dados constantes | BAIXA | ✅ Resolvido (fallback 1 cluster, warnings suprimidos) |

## 3. Pontos fortes mantidos

- Núcleo de risco **determinístico** (quantis empíricos, sem RNG nos defaults).
- Contratos de dados explícitos: `REQUIRED_SWING_COLS` (FIN-SENSE) e `REQUIRED_OHLC` (MT5).
- **Testes automatizados** (`pytest`): 10 testes cobrindo pipeline, trading, métricas, Decimal, sanitização.
- Proveniência SHA-256 canónica reprodutível.

## 4. Riscos residuais

| Tópico | Severidade | Descrição |
|--------|------------|-----------|
| PnL sintético FIN-SENSE | BAIXA | Rotulado como HYPOTHETICAL; bloqueado para uso como PnL realizado. |
| Backtest simplificado | BAIXA | Modelo académico com custos configuráveis; não valida produção real sem dados tick-by-tick. |
| VaR/CVaR históricos | BAIXA | Não cobrem eventos fora da cauda observada (fat-tail). |
| Backtrader | BAIXA | Dependência opcional; séries muito grandes podem necessitar chunking. |

## 5. Verificação recomendada ao Conselho

```bash
cd modules/DOS_MODULE && python -m pytest -q
```

Resultado esperado: **10 passed** (5.10s).

---

*Este documento descreve desenho e limites técnicos; não substitui auditoria jurídica ou de negócio.*
