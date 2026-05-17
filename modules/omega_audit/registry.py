"""system_registry.json — estado e versões de componentes auditáveis."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_registry_path(source_root: Path) -> Path:
    return source_root / "audit" / "omega_audit" / "system_registry.json"


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_registry(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def register_component(
    path: Path,
    name: str,
    version: str,
    logic_hash: str,
    params: dict[str, Any] | None = None,
) -> None:
    reg = load_registry(path)
    reg[name] = {
        "version": version,
        "hash": logic_hash,
        "params": params or {},
        "last_audit": datetime.now(timezone.utc).isoformat(),
    }
    save_registry(path, reg)
