"""Leitura em lotes de ticks brutos (ligar a Kafka/Redis em produção)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, List, Optional

from fin_sense_data_module.storage.storage_interface import FinSenseStorage


class RawTicksStream:
    """Iterador de batches; por omissão não emite dados (integração posterior)."""

    def __init__(
        self,
        symbols: List[str],
        *,
        hub_root: Optional[Path] = None,
    ) -> None:
        self.symbols = symbols
        self.hub_root = hub_root

    def __iter__(self) -> Iterator[list[dict[str, Any]]]:
        if self.hub_root is None:
            yield from ()
            return
        store = FinSenseStorage(self.hub_root, layer="bronze")
        for sym in self.symbols:
            pattern = f"**/entity={sym}/**/*.json"
            for path in sorted(store.layer_root().glob(pattern)):
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    yield data
