# -*- coding: utf-8 -*-
"""
FIN-SENSE DATA MODULE — kit de validação e métricas (referência)

Objetivo: comprovar integridade de dados e manifests sem embutir métricas de
negócio (VaR, PnL attribution, etc.). Uso: pipelines de QA, auditorias Tier-0.

Requisitos: Python 3.10+
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


# ---------------------------------------------------------------------------
# KPIs documentados em CEO_DEFESA_FIN_SENSE_DATA_MODULE_CONSELHO_20260327.md
# ---------------------------------------------------------------------------


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    """Hash SHA-256 do conteúdo binário do ficheiro (FIPS 180-4)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _truthy(x: Any) -> bool:
    if x is None:
        return False
    if isinstance(x, str) and x.strip() == "":
        return False
    return True


def provenance_attach_rate(rows: Iterable[Mapping[str, Any]]) -> float:
    """
    KPI-01 PAR: fração de linhas com ingestion_id não nulo/vazio.
    """
    rows = list(rows)
    if not rows:
        return math.nan
    ok = sum(1 for r in rows if _truthy(r.get("ingestion_id")))
    return ok / len(rows)


def identifier_completeness(rows: Iterable[Mapping[str, Any]]) -> float:
    """
    KPI-02 IC: FIGI ou ISIN ou (symbol AND exchange).
    Ajuste os nomes das chaves ao seu schema real.
    """
    rows = list(rows)
    if not rows:
        return math.nan

    def has_id(r: Mapping[str, Any]) -> bool:
        if _truthy(r.get("figi")) or _truthy(r.get("isin")):
            return True
        return _truthy(r.get("symbol")) and _truthy(r.get("exchange"))

    ok = sum(1 for r in rows if has_id(r))
    return ok / len(rows)


def time_consistency_rate(
    rows: Iterable[Mapping[str, Any]],
    allowed_skew_seconds: float = 300.0,
) -> float:
    """
    KPI-03 TCR: source_ts <= recv_ts + allowed_skew (ambos devem ser comparáveis).
    Aceita valores como datetime ou strings ISO8601 (parse simples não incluído:
    passe datetime normalizado pelo caller se necessário).
    """
    from datetime import datetime

    rows = list(rows)
    if not rows:
        return math.nan

    def to_dt(v: Any) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # ISO8601 básico
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return None

    ok = 0
    n = 0
    for r in rows:
        s, e = to_dt(r.get("source_ts")), to_dt(r.get("recv_ts"))
        if s is None or e is None:
            continue
        n += 1
        delta = (e - s).total_seconds()
        if delta + allowed_skew_seconds >= 0:
            ok += 1
    if n == 0:
        return math.nan
    return ok / n


def manifest_hash_match(manifest: Mapping[str, Any], files_root: Path) -> bool:
    """
    KPI-04 MHM simplificado: manifest deve conter file_path -> file_hash esperado;
    verifica cada ficheiro relativo a files_root.
    """
    files = manifest.get("files")
    if not isinstance(files, list):
        return False
    for item in files:
        if not isinstance(item, dict):
            return False
        rel = item.get("path") or item.get("file_path")
        expected = item.get("file_hash") or item.get("sha256")
        if not rel or not expected:
            return False
        p = files_root / str(rel)
        if not p.is_file():
            return False
        if sha256_file(p).lower() != str(expected).lower():
            return False
    return True


def catalog_coverage(
    report_symbols_timeframes: set[tuple[str, str]],
    catalog: set[tuple[str, str]],
) -> float:
    """
    KPI-06 CC: |S ∩ C| / |S|
    """
    if not report_symbols_timeframes:
        return math.nan
    hit = report_symbols_timeframes & catalog
    return len(hit) / len(report_symbols_timeframes)


@dataclass
class KPIReport:
    par: float
    ic: float
    tcr: float
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "KPI-01_PAR": self.par,
            "KPI-02_IC": self.ic,
            "KPI-03_TCR": self.tcr,
            "notes": self.notes,
        }


def evaluate_batch(rows: list[dict[str, Any]], allowed_skew_seconds: float = 300.0) -> KPIReport:
    """Avalia PAR, IC, TCR sobre um lote homogéneo."""
    return KPIReport(
        par=provenance_attach_rate(rows),
        ic=identifier_completeness(rows),
        tcr=time_consistency_rate(rows, allowed_skew_seconds=allowed_skew_seconds),
        notes="Valores NaN indicam conjunto vazio ou colunas em falta para TCR.",
    )


def validate_manifest_minimal(manifest: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """
    Validação estrutural mínima (não criptográfica) de um manifest de ingestão.
    """
    errs: list[str] = []
    for key in ("ingest_id", "source", "schema_version"):
        if not _truthy(manifest.get(key)):
            errs.append(f"missing_or_empty:{key}")
    if "record_count" in manifest and manifest["record_count"] is not None:
        try:
            int(manifest["record_count"])
        except (TypeError, ValueError):
            errs.append("record_count_not_int")
    return (len(errs) == 0, errs)


def report_lines(report: KPIReport) -> list[str]:
    lines = [
        "=== FIN-SENSE DATA MODULE — KPI batch ===",
        f"KPI-01 PAR (provenance attach rate): {report.par:.6f}",
        f"KPI-02 IC (identifier completeness):  {report.ic:.6f}",
        f"KPI-03 TCR (time consistency rate):   {report.tcr:.6f}",
        report.notes,
    ]
    return lines


if __name__ == "__main__":
    demo = [
        {
            "ingestion_id": "550e8400-e29b-41d4-a716-446655440000",
            "figi": "BBG000B9XRY4",
            "source_ts": "2026-03-27T12:00:00+00:00",
            "recv_ts": "2026-03-27T12:00:01+00:00",
        },
        {
            "ingestion_id": "550e8400-e29b-41d4-a716-446655440000",
            "symbol": "XAUUSD",
            "exchange": "META",
            "source_ts": "2026-03-27T12:05:00+00:00",
            "recv_ts": "2026-03-27T12:05:02+00:00",
        },
    ]
    r = evaluate_batch(demo)
    print("\n".join(report_lines(r)))
    ok, err = validate_manifest_minimal(
        {
            "ingest_id": "u1",
            "source": "demo",
            "schema_version": "v1",
            "record_count": 2,
        }
    )
    print("manifest_ok:", ok, err)
