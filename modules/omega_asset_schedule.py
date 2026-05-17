"""
Resolução de lista de ativos por calendário (24/7 sem interrupção + classes).

Usado pelo main.py quando --ativos não é fornecido. Telemetria em
audit/paper/asset_schedule.jsonl (append JSONL).
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

_DEFAULT_CONFIG = Path("config") / "omega_asset_schedule.json"


def _now_in_tz(tz_name: str) -> datetime:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now()


def _day_bucket(weekday: int) -> str:
    """weekday ISO: Monday=0 .. Sunday=6."""
    if weekday < 5:
        return "weekday_mon_fri"
    if weekday == 5:
        return "saturday"
    return "sunday"


def resolve_shadow_loop_assets(
    cli_ativos: list[str] | None,
    source_root: Path,
    *,
    config_path: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Retorna (symbols, meta).

    - Se cli_ativos não vazio: devolve-o (fonte CLI).
    - Senão: lê config/omega_asset_schedule.json; se ausente ou inválido, fallback XAUUSD.
    """
    meta: dict[str, Any] = {"source": "cli", "class": None}

    root = source_root.resolve()

    if cli_ativos:
        meta["symbols"] = list(cli_ativos)
        meta["class"] = "explicit_cli"
        _append_telemetry(root, meta)
        return list(cli_ativos), meta

    if os.getenv("OMEGA_ASSET_SCHEDULE", "1").strip().lower() in ("0", "false", "off"):
        meta.update({"source": "schedule_disabled", "symbols": ["XAUUSD"], "class": "fallback"})
        _append_telemetry(root, meta)
        return ["XAUUSD"], meta

    cfg_p = config_path or (root / _DEFAULT_CONFIG)

    if not cfg_p.is_file():
        meta.update({"source": "missing_config", "symbols": ["XAUUSD"], "class": "fallback"})
        _append_telemetry(root, meta)
        return ["XAUUSD"], meta

    try:
        cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        meta.update({"source": "bad_config", "error": str(e), "symbols": ["XAUUSD"], "class": "fallback"})
        _append_telemetry(root, meta)
        return ["XAUUSD"], meta

    tz = str(cfg.get("timezone") or "Europe/Lisbon")
    now = _now_in_tz(tz)
    bucket = _day_bucket(now.weekday())
    block = (cfg.get("no_cli") or {}).get(bucket) or {}
    syms = block.get("symbols") or ["XAUUSD"]
    if not isinstance(syms, list) or not all(isinstance(s, str) for s in syms):
        syms = ["XAUUSD"]
    klass = block.get("class") or bucket

    meta.update(
        {
            "source": "schedule",
            "timezone": tz,
            "local_iso": now.isoformat(timespec="seconds"),
            "weekday_iso_0_mon": now.weekday(),
            "bucket": bucket,
            "class": klass,
            "symbols": list(syms),
            "config_path": str(cfg_p),
        }
    )
    _append_telemetry(root, meta)
    return list(syms), meta


def _append_telemetry(root: Path, meta: dict[str, Any]) -> None:
    try:
        logf = root / "audit" / "paper" / "asset_schedule.jsonl"
        logf.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(meta, ensure_ascii=False)
        with logf.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
