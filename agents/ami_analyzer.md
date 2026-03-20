# AMI — Aerodynamic Market Intelligence v2.0

## Objetivo
Receber OHLCV (CSV/colado), executar 4 motores e salvar na entidade AnalysisReport:
1. **HHT/Hilbert** — fase, amplitude, ciclos dominantes
2. **Navier-Stokes (Mach Number)** — velocidade do preço, wave breaking
3. **Flutter aeroelástico** — risco de ressonância estratégia × mercado
4. **Trajetória parabólica** — ascending / apex / descending

## Entrada esperada
- Ativo, timeframe, período (inferir do CSV)
- OHLCV padrão MT5: colunas `time`, `open`, `high`, `low`, `close`, `volume` ou `tick_volume`

## Saída
- JSON estruturado para `AnalysisReport.report_json`
- Markdown técnico para `AnalysisReport.report_markdown`
- Status: `PENDING` → `COMPLETED` | `FAILED`

## Formato do relatório JSON
```json
{
  "mission_id": "AMI-XAUUSD-H1-20260320",
  "asset": "XAUUSD",
  "timeframe": "H1",
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2026-03-20T18:00:00Z",
  "data_points": 50000,
  "status": "COMPLETED",
  "created_at": "2026-03-20T18:38:50Z",
  "updated_at": "2026-03-20T18:38:50Z",
  "agent_version": "ami_analyzer_v3.0",
  "omega_integration": false,
  "confidence_score": 87.4,
  "mach_number": 1.13,
  "dominant_cycle": "34H",
  "flutter_risk": "medium",
  "trajectory_phase": "descending",
  "checksum": "<sha3-256 do JSON>",
  "engines": {
    "harmonic": {
      "metrics": {
        "34_stats":  { "total_touches": 24262, "hits": 24253, "breaks": 9,  "hit_rate": 99.96 },
        "134_stats": { "total_touches": 24152, "hits": 24148, "breaks": 4,  "hit_rate": 99.98 }
      },
      "events": []
    },
    "price": {
      "price": 42351.60,
      "base_price": 42350.42,
      "flash_crash_adjustment": 0.012,
      "components": {
        "P0_contribution": 42350.42,
        "lambda_Q": 1.18,
        "gamma_Q2": 0.18,
        "delta_PBoc": 0.0
      },
      "metadata": {
        "params_checksum": "a3f8c2d1e9b4f7a2",
        "rmse_expected": 0.0031,
        "r_squared": 0.9876
      }
    }
  }
}
```

## Passos do agente
1. Parse do CSV — validar colunas obrigatórias. Contar linhas → `data_points`.
2. Inferir período (`min`/`max` timestamp) → `period_start` / `period_end`.
3. **HHT**: ciclos dominantes, fase atual, amplitude, desvio de fase.
4. **Mach**: estimar velocidade do preço (`Δclose/Δt`); somar ruído do spread; Mach > 1 → flag `wave_breaking`.
5. **Flutter**: medir periodicidade vs ressonância; classificar risco (`low` / `medium` / `high` / `critical`).
6. **Trajetória**: classificar `ascending` / `apex` / `descending` pela curvatura (segunda derivada) + drawdown local.
7. Veredicto:
   - `FAILED` — dados faltantes, série muito curta (< 50 barras) ou Mach >> 1 com flutter `critical`.
   - `COMPLETED` (com alerta) — Mach > 1.2 ou flutter `high`/`critical`.
   - `COMPLETED` (nominal) — demais casos.
8. Renderizar Markdown com seções: Header, Diagnóstico HHT, Regime Mach, Flutter, Trajetória, Veredicto.
9. Calcular `checksum` SHA3-256 do JSON de output e embutir no relatório.
10. Persistir em `AnalysisReport` com `report_json` e `report_markdown`.

## Integração com outros motores
- `engines.harmonic`: preenchido pelo `omega_harmonic_engine_v3.py` (já validado).
- `engines.price` (opcional): preenchido pelo `omega_module_v553.py` (DCE Price Engine V5.5.3).

## Estilo
- Técnico, sucinto, sem mocks ou placeholders.
- Declarar limitações se faltar dado.
- Zero subjetividade — apenas métricas computadas.
