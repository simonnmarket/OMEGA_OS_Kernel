#!/usr/bin/env python3
"""
OMEGA — Matriz de saúde de componentes (import + gate no shadow_loop + telemetria).

Uso:
  python scripts/omega_component_health_matrix.py
  python scripts/omega_component_health_matrix.py --json audit/component_health/latest.json
  python scripts/omega_component_health_matrix.py --md docs/conselho_arquivo/COMPONENT_HEALTH_MATRIX.md

Gera tabela no formato Conselho: Componente | Fonte | Status | Evidência
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Componente → (módulo Python, classe/atributo shadow_loop, gate no loop)
COMPONENT_REGISTRY: List[Dict[str, str]] = [
    {
        "component": "Weis Wave Engine",
        "source": "modules.weis_wave_tracker (WeisWaveAnalyzer 1+2)",
        "shadow_flag": "_KERNEL_MODULE_MAP:weis_wave",
        "module": "modules.weis_wave_tracker",
        "class": "ComponentEngine",
    },
    {
        "component": "Volume Order Flow / Delta",
        "source": "modules.volume_order_flow",
        "shadow_flag": "_KERNEL_MODULE_MAP:vof",
        "module": "modules.volume_order_flow",
        "class": "ComponentEngine",
    },
    {
        "component": "PVSRA",
        "source": "modules.pvsra_analyzer",
        "shadow_flag": "_KERNEL_MODULE_MAP:pvsra",
        "module": "modules.pvsra_analyzer",
        "class": "ComponentEngine",
    },
    {
        "component": "VWAP",
        "source": "modules.vwap_engine",
        "shadow_flag": "_KERNEL_MODULE_MAP:vwap",
        "module": "modules.vwap_engine",
        "class": "ComponentEngine",
    },
    {
        "component": "Volume Footprint",
        "source": "modules.volume_footprint_engine",
        "shadow_flag": "_KERNEL_MODULE_MAP:footprint",
        "module": "modules.volume_footprint_engine",
        "class": "ComponentEngine",
    },
    {
        "component": "STO Institutional Player",
        "source": "modules.sto_institutional_detector",
        "shadow_flag": "_KERNEL_MODULE_MAP:sto_inst",
        "module": "modules.sto_institutional_detector",
        "class": "ComponentEngine",
    },
    {
        "component": "STO Fused Microstructure",
        "source": "modules.sto_fused_microstructure_engine",
        "shadow_flag": "_KERNEL_MODULE_MAP:sto_fused",
        "module": "modules.sto_fused_microstructure_engine",
        "class": "ComponentEngine",
    },
    {
        "component": "Pullback Re-Entry (Kalman)",
        "source": "modules.kalman_pullback_engine",
        "shadow_flag": "_KALMAN_ENGINE",
        "module": "modules.kalman_pullback_engine",
        "class": "OmegaKalmanPullbackEngine",
    },
    {
        "component": "Market Profile (TPO)",
        "source": "modules.omega_market_profile_engine",
        "shadow_flag": "_MP_AVAIL / MP-GATE",
        "module": "modules.omega_market_profile_engine",
        "class": "ComponentEngine",
    },
    {
        "component": "Wyckoff Analyzer",
        "source": "modules.wyckoff_analyzer + WyckoffMarlin synapse",
        "shadow_flag": "_KERNEL_MODULE_MAP:wyckoff",
        "module": "modules.wyckoff_analyzer",
        "class": "ComponentEngine",
    },
    {
        "component": "Liquidity Mining / Absorption",
        "source": "modules.liquidity_absorption_engine",
        "shadow_flag": "_KERNEL_MODULE_MAP:liq_abs",
        "module": "modules.liquidity_absorption_engine",
        "class": "ComponentEngine",
    },
    {
        "component": "Zone Navigator v3",
        "source": "modules.omega_zone_navigator",
        "shadow_flag": "_ZONE_NAV_AVAIL",
        "module": "modules.omega_zone_navigator",
        "class": "ZoneNavigatorV3",
    },
    {
        "component": "Tesseract Sniper (XAUUSD)",
        "source": "modules.tesseract_sniper",
        "shadow_flag": "_TESSERACT_AVAIL",
        "module": "modules.tesseract_sniper",
        "class": "TesseractSniperV1",
    },
    {
        "component": "Micro Entry Filter (M1)",
        "source": "modules.micro_entry_filter",
        "shadow_flag": "_MICRO_FILTER_AVAIL",
        "module": "modules.micro_entry_filter",
        "class": "MicroEntryFilter",
    },
    {
        "component": "ZAK Guardrail",
        "source": "modules.zak_guardrail",
        "shadow_flag": "_ZAK_GUARDRAIL_AVAIL",
        "module": "modules.zak_guardrail",
        "class": "ZakMirGuardrailV1",
    },
    {
        "component": "Agent IA (FASE4)",
        "source": "agent_ia / OMEGA_USE_AGENT_IA",
        "shadow_flag": "USE_AGENT_IA",
        "module": "agent_ia",
        "class": "",
    },
    {
        "component": "Sensory Synapse Hub",
        "source": "modules.omega_sensory_synapse",
        "shadow_flag": "_KERNEL_MODULE_MAP:synapse",
        "module": "modules.omega_sensory_synapse",
        "class": "ComponentEngine",
    },
    {
        "component": "RCV P0 Execution Gates",
        "source": "shadow_loop.pre_execution_safety_check",
        "shadow_flag": "Mandatos 1-4 2026-05-20",
        "module": "core_engines.shadow_loop",
        "class": "pre_execution_safety_check",
    },
]

STATUS_EMOJI = {
    "ACTIVE": "🟢",
    "INTEGRATED": "🟡",
    "STUB": "🟠",
    "OFF": "🔴",
    "ERROR": "⛔",
}


def _probe_import(module_path: str, class_name: str) -> Tuple[str, str]:
    try:
        mod = importlib.import_module(module_path)
        if class_name:
            if not hasattr(mod, class_name):
                return "STUB", f"module OK, sem {class_name}"
            getattr(mod, class_name)
        return "INTEGRATED", "import OK"
    except Exception as e:
        return "OFF", str(e)[:120]


def _probe_shadow_flags() -> Dict[str, Any]:
    try:
        import core_engines.shadow_loop as sl
        return {
            "MICRO_FILTER": getattr(sl, "_MICRO_FILTER_AVAIL", False),
            "ZONE_NAV": getattr(sl, "_ZONE_NAV_AVAIL", False),
            "ZAK": getattr(sl, "_ZAK_GUARDRAIL_AVAIL", False),
            "TESSERACT": getattr(sl, "_TESSERACT_AVAIL", False),
            "MP": getattr(sl, "_MP_AVAIL", False),
            "KALMAN": getattr(sl, "_KALMAN_ENGINE", None) is not None,
            "USE_AGENT_IA": getattr(sl, "USE_AGENT_IA", False),
            "AGENT_IA_AVAILABLE": getattr(sl, "AGENT_IA_AVAILABLE", False),
            "RCV_GATE": hasattr(sl, "pre_execution_safety_check"),
        }
    except Exception as e:
        return {"_error": str(e)}


def _count_decision_trace_skips(trace_path: Path) -> Dict[str, int]:
    if not trace_path.is_file():
        return {}
    counts: Dict[str, int] = {}
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        st = o.get("status") or o.get("signal_action") or ""
        if st:
            counts[str(st)] = counts.get(str(st), 0) + 1
    return counts


def build_matrix() -> Dict[str, Any]:
    rows = []
    for spec in COMPONENT_REGISTRY:
        st, detail = _probe_import(spec["module"], spec.get("class", ""))
        # Agent IA special case
        if spec["component"].startswith("Agent IA"):
            flags = _probe_shadow_flags()
            if flags.get("USE_AGENT_IA") and flags.get("AGENT_IA_AVAILABLE"):
                st, detail = "ACTIVE", "USE_AGENT_IA=1 e import OK"
            elif flags.get("AGENT_IA_AVAILABLE"):
                st, detail = "INTEGRATED", "disponível; USE_AGENT_IA pode estar off"
            else:
                st, detail = "OFF", "AGENT_IA não disponível no arranque"
        if spec["component"].startswith("RCV P0"):
            flags = _probe_shadow_flags()
            st = "ACTIVE" if flags.get("RCV_GATE") else "OFF"
            detail = "pre_execution_safety_check + mt5_send_order 10016 guard"
        rows.append({
            **spec,
            "status": st,
            "evidence": detail,
            "emoji": STATUS_EMOJI.get(st, "⚪"),
        })

    trace = ROOT / "audit" / "paper" / "decision_trace.jsonl"
    telemetry = {
        "decision_trace_path": str(trace),
        "skip_counts": _count_decision_trace_skips(trace),
        "env": {
            "OMEGA_DISABLE_MOMENTUM_FALLBACK": os.getenv("OMEGA_DISABLE_MOMENTUM_FALLBACK"),
            "OMEGA_DECISION_TRACE": os.getenv("OMEGA_DECISION_TRACE"),
            "OMEGA_USE_AGENT_IA": os.getenv("OMEGA_USE_AGENT_IA"),
        },
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "shadow_loop_flags": _probe_shadow_flags(),
        "components": rows,
        "telemetry": telemetry,
    }


def to_markdown(data: Dict[str, Any]) -> str:
    lines = [
        "# OMEGA — Matriz de Saúde de Componentes",
        f"**Gerado:** {data['generated_at_utc']}",
        "",
        "| Componente | Fonte principal | Gate shadow_loop | Status | Evidência |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in data["components"]:
        lines.append(
            f"| {r['component']} | {r['source']} | {r['shadow_flag']} | "
            f"{r['emoji']} {r['status']} | {r['evidence']} |"
        )
    lines.extend([
        "",
        "## Flags shadow_loop (arranque)",
        "```json",
        json.dumps(data.get("shadow_loop_flags", {}), indent=2),
        "```",
        "",
        "## Telemetria decision_trace (skips)",
        "```json",
        json.dumps(data.get("telemetry", {}), indent=2),
        "```",
        "",
        "### Como medir em produção",
        "1. Correr este script antes e depois de cada sessão 24h.",
        "2. No log: `[MOMENTUM_FALLBACK] DISABLED`, `[EQUITY] Equity MT5 real`.",
        "3. Contar `SKIP_*` em `decision_trace.jsonl` (gates activos).",
        "4. `trade_feedback.jsonl`: `signal_source` deve ser AGENT_IA ou MOMENTUM_MT5 (não NULL).",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=str, default="")
    ap.add_argument("--md", type=str, default="")
    args = ap.parse_args()
    data = build_matrix()
    if args.json:
        p = Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"JSON: {p}")
    if args.md:
        p = Path(args.md)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(to_markdown(data), encoding="utf-8")
        print(f"MD: {p}")
    if not args.json and not args.md:
        print(to_markdown(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
