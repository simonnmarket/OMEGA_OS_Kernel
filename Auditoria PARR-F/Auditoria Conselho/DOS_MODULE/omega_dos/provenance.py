"""Proveniência e hashing canónico para relatórios auditáveis."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping


def sha256_canonical(obj: Any) -> str:
    """SHA-256 de representação JSON com chaves ordenadas (UTF-8)."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_json_default)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_default(o: Any) -> Any:
    if isinstance(o, (datetime,)):
        return o.isoformat()
    if hasattr(o, "item"):  # numpy scalar
        try:
            return o.item()
        except Exception:
            return str(o)
    raise TypeError(f"Object of type {type(o)} is not JSON serializable")


def build_provenance_record(
    *,
    inputs_digest: str,
    code_version: str,
    fin_sense_schema: str,
    extras: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Registo mínimo de proveniência para anexar a relatórios do Conselho."""
    rec: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dos_module_version": code_version,
        "fin_sense_schema_ref": fin_sense_schema,
        "inputs_digest_sha256": inputs_digest,
    }
    if extras:
        rec["extras"] = dict(extras)
    rec["record_digest_sha256"] = sha256_canonical({k: v for k, v in rec.items() if k != "record_digest_sha256"})
    return rec
