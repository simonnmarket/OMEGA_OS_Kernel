"""FIN-SENSE DATA MODULE — hub canónico v1.2."""

from fin_sense_data_module.schemas import (
    CANONICAL_LINEAGE_FIELDS,
    SCHEMA_VERSION,
    SCHEMAS,
    get_schema,
    get_schema_with_lineage,
    list_tables,
)
from fin_sense_data_module.storage import FinSenseStorage, StorageLayout

__version__ = "1.2.0"

__all__ = [
    "CANONICAL_LINEAGE_FIELDS",
    "SCHEMA_VERSION",
    "SCHEMAS",
    "FinSenseStorage",
    "StorageLayout",
    "get_schema",
    "get_schema_with_lineage",
    "list_tables",
    "__version__",
]
