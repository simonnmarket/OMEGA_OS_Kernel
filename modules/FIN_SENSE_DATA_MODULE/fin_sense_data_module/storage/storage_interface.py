"""Armazenamento local em camadas (Bronze/Silver/Gold) com particionamento dinâmico."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Optional

Layer = Literal["bronze", "silver", "gold"]

_SAFE_SEGMENT = re.compile(r"[^A-Za-z0-9._+\-]+")


def _sanitize_segment(value: str) -> str:
    cleaned = _SAFE_SEGMENT.sub("_", value.strip())
    return cleaned or "UNKNOWN"


@dataclass
class FinSenseStorage:
    """
    Raiz do hub: cada layer contém tabelas particionadas por entidade e data.

    Partição canónica: entity=<id>/year=YYYY/month=MM/day=DD/
    Se não houver símbolo (macro, curvas), usar `entity_key` explícito (ex.: país, curve_id).
    """

    root: Path
    layer: Layer = "bronze"

    def layer_root(self) -> Path:
        return Path(self.root) / self.layer

    def partition_path(
        self,
        table_name: str,
        ref_time: datetime,
        *,
        entity_key: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> Path:
        """Caminho de diretório para um batch (sem extensão de ficheiro)."""
        t = ref_time.astimezone(timezone.utc)
        ent = entity_key if entity_key is not None else (symbol if symbol is not None else "GLOBAL")
        ent = _sanitize_segment(ent)
        rel = Path(_sanitize_segment(table_name)) / f"entity={ent}" / f"year={t.year:04d}" / f"month={t.month:02d}" / f"day={t.day:02d}"
        return self.layer_root() / rel

    def write_json_batch(
        self,
        table_name: str,
        rows: list[Mapping[str, Any]],
        *,
        ref_time: Optional[datetime] = None,
        entity_key: Optional[str] = None,
        symbol: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> Path:
        """Persiste um lote JSON (MVP). Parquet opcional em evolução."""
        rt = ref_time or datetime.now(timezone.utc)
        dest_dir = self.partition_path(table_name, rt, entity_key=entity_key, symbol=symbol)
        dest_dir.mkdir(parents=True, exist_ok=True)
        bid = batch_id or f"batch_{int(rt.timestamp())}"
        out = dest_dir / f"{bid}.json"
        out.write_text(json.dumps(list(rows), indent=2, default=str), encoding="utf-8")
        return out

    def write_manifest(
        self,
        payload: Mapping[str, Any],
        *,
        manifest_name: str = "manifest.json",
    ) -> Path:
        """Manifesto de proveniência sob `root/manifests/`."""
        man_dir = Path(self.root) / "manifests"
        man_dir.mkdir(parents=True, exist_ok=True)
        path = man_dir / manifest_name
        path.write_text(json.dumps(dict(payload), indent=2, default=str), encoding="utf-8")
        return path


@dataclass
class StorageLayout:
    """Metadados fixos do deployment local (ajustar para S3/EU em produção)."""

    hub_root: Path
    retention_bronze_years: int = 7
    retention_silver_gold_years: int = 2
    jurisdiction_note: str = "EU-only storage (configurar bucket/região em deploy)"
