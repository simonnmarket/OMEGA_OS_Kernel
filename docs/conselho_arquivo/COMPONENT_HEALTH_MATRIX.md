# OMEGA — Matriz de Saúde de Componentes
**Gerado:** 2026-05-19T20:15:35.580254+00:00

| Componente | Fonte principal | Gate shadow_loop | Status | Evidência |
| --- | --- | --- | --- | --- |
| Weis Wave Engine | modules.weis_wave_tracker (WeisWaveAnalyzer 1+2) | _KERNEL_MODULE_MAP:weis_wave | 🟡 INTEGRATED | import OK |
| Volume Order Flow / Delta | modules.volume_order_flow | _KERNEL_MODULE_MAP:vof | 🟡 INTEGRATED | import OK |
| PVSRA | modules.pvsra_analyzer | _KERNEL_MODULE_MAP:pvsra | 🟡 INTEGRATED | import OK |
| VWAP | modules.vwap_engine | _KERNEL_MODULE_MAP:vwap | 🟡 INTEGRATED | import OK |
| Volume Footprint | modules.volume_footprint_engine | _KERNEL_MODULE_MAP:footprint | 🟡 INTEGRATED | import OK |
| STO Institutional Player | modules.sto_institutional_detector | _KERNEL_MODULE_MAP:sto_inst | 🟡 INTEGRATED | import OK |
| STO Fused Microstructure | modules.sto_fused_microstructure_engine | _KERNEL_MODULE_MAP:sto_fused | 🟡 INTEGRATED | import OK |
| Pullback Re-Entry (Kalman) | modules.kalman_pullback_engine | _KALMAN_ENGINE | 🟡 INTEGRATED | import OK |
| Market Profile (TPO) | modules.omega_market_profile_engine | _MP_AVAIL / MP-GATE | 🟡 INTEGRATED | import OK |
| Wyckoff Analyzer | modules.wyckoff_analyzer + WyckoffMarlin synapse | _KERNEL_MODULE_MAP:wyckoff | 🟡 INTEGRATED | import OK |
| Liquidity Mining / Absorption | modules.liquidity_absorption_engine | _KERNEL_MODULE_MAP:liq_abs | 🟡 INTEGRATED | import OK |
| Zone Navigator v3 | modules.omega_zone_navigator | _ZONE_NAV_AVAIL | 🟡 INTEGRATED | import OK |
| Tesseract Sniper (XAUUSD) | modules.tesseract_sniper | _TESSERACT_AVAIL | 🟡 INTEGRATED | import OK |
| Micro Entry Filter (M1) | modules.micro_entry_filter | _MICRO_FILTER_AVAIL | 🟡 INTEGRATED | import OK |
| ZAK Guardrail | modules.zak_guardrail | _ZAK_GUARDRAIL_AVAIL | 🟡 INTEGRATED | import OK |
| Agent IA (FASE4) | agent_ia / OMEGA_USE_AGENT_IA | USE_AGENT_IA | 🟢 ACTIVE | USE_AGENT_IA=1 e import OK |
| Sensory Synapse Hub | modules.omega_sensory_synapse | _KERNEL_MODULE_MAP:synapse | 🟡 INTEGRATED | import OK |
| RCV P0 Execution Gates | shadow_loop.pre_execution_safety_check | Mandatos 1-4 2026-05-20 | 🟢 ACTIVE | pre_execution_safety_check + mt5_send_order 10016 guard |

## Flags shadow_loop (arranque)
```json
{
  "MICRO_FILTER": true,
  "ZONE_NAV": true,
  "ZAK": true,
  "TESSERACT": true,
  "MP": true,
  "KALMAN": true,
  "USE_AGENT_IA": true,
  "AGENT_IA_AVAILABLE": true,
  "RCV_GATE": true
}
```

## Telemetria decision_trace (skips)
```json
{
  "decision_trace_path": "C:\\OMEGA_QUANTUM_LAB\\SOURCE_CODE\\audit\\paper\\decision_trace.jsonl",
  "skip_counts": {},
  "env": {
    "OMEGA_DISABLE_MOMENTUM_FALLBACK": null,
    "OMEGA_DECISION_TRACE": null,
    "OMEGA_USE_AGENT_IA": null
  }
}
```

### Como medir em produção
1. Correr este script antes e depois de cada sessão 24h.
2. No log: `[MOMENTUM_FALLBACK] DISABLED`, `[EQUITY] Equity MT5 real`.
3. Contar `SKIP_*` em `decision_trace.jsonl` (gates activos).
4. `trade_feedback.jsonl`: `signal_source` deve ser AGENT_IA ou MOMENTUM_MT5 (não NULL).
