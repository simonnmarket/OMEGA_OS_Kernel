"""Validação de linhas contra o contrato v1.2 e enriquecimento de linhagem."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, List, Mapping, MutableMapping, Tuple

from fin_sense_data_module.schemas.schema_definitions import (
    SCHEMA_VERSION,
    get_schema,
    get_schema_with_lineage,
)


class IngestionError(ValueError):
    pass


def _canonical_payload(row: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(row), sort_keys=True, default=str).encode("utf-8")


def row_checksum(row: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_payload(row)).hexdigest()


def validate_mandatory_fields(
    table_name: str,
    row: Mapping[str, Any],
    *,
    use_lineage: bool = False,
) -> Tuple[bool, List[str]]:
    schema = get_schema_with_lineage(table_name) if use_lineage else get_schema(table_name)
    errors: List[str] = []
    for col in schema:
        if col.get("mandatory") == "YES" and (col["name"] not in row or row[col["name"]] is None):
            errors.append(f"missing_mandatory:{col['name']}")
    return (len(errors) == 0, errors)


def enrich_lineage(
    row: MutableMapping[str, Any],
    *,
    source: str,
    operator: str,
    file_hash: str,
    quality_status: str = "OK",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    row.setdefault("ingestion_id", str(uuid.uuid4()))
    row.setdefault("source", source)
    row.setdefault("schema_version", SCHEMA_VERSION)
    row.setdefault("file_hash", file_hash)
    row.setdefault("ingest_ts", now)
    row.setdefault("quality_status", quality_status)
    row.setdefault("operator", operator)


def ingest_row_validated(
    table_name: str,
    row: MutableMapping[str, Any],
    *,
    source: str,
    operator: str,
    file_hash: str,
    quality_status: str = "OK",
) -> MutableMapping[str, Any]:
    enrich_lineage(row, source=source, operator=operator, file_hash=file_hash, quality_status=quality_status)
    ok, errs = validate_mandatory_fields(table_name, row, use_lineage=True)
    if not ok:
        raise IngestionError("; ".join(errs))
    if table_name == "TBL_MARKET_TICKS_RAW" and "checksum" in row and row["checksum"]:
        pass
    elif table_name == "TBL_MARKET_TICKS_RAW":
        row["checksum"] = row_checksum({k: v for k, v in row.items() if k != "checksum"})
    return row
