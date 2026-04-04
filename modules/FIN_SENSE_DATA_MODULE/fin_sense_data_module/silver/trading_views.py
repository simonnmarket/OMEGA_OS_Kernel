"""Vistas lógicas Silver — substituir por DuckDB/ClickHouse em produção."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional


class TradingViews:
    """Consumo versionado do schema v1.2 (stubs até ligar ao warehouse)."""

    @staticmethod
    def get_executions(
        *,
        symbol: str,
        date_from: str,
        schema_version: str = "v1.2",
        hub_root: Optional[Path] = None,
    ) -> List[dict[str, Any]]:
        del symbol, date_from, schema_version
        if hub_root is None:
            return []
        return []
