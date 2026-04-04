"""FIN-SENSE DATA MODULE — contrato canónico v1.2 (23 tabelas)."""

from __future__ import annotations

from typing import Dict, List

SCHEMA_VERSION = "v1.2"

# Campos de linhagem exigidos pelo contrato CEO → Engenharia (merge aditivo em ingestão).
CANONICAL_LINEAGE_FIELDS: List[Dict[str, str]] = [
    {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
    {"name": "source", "type": "STRING", "mandatory": "YES"},
    {"name": "schema_version", "type": "STRING", "mandatory": "YES"},
    {"name": "file_hash", "type": "STRING", "mandatory": "YES"},
    {"name": "ingest_ts", "type": "TIMESTAMP", "mandatory": "YES"},
    {"name": "quality_status", "type": "STRING", "mandatory": "YES"},
    {"name": "operator", "type": "STRING", "mandatory": "YES"},
]

SCHEMAS: Dict[str, List[Dict[str, str]]] = {
    # --- MARKET DATA & MICROSTRUCTURE ---
    "TBL_MARKET_TICKS_RAW": [
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
        {"name": "source", "type": "STRING", "mandatory": "YES"},
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "exchange", "type": "STRING", "mandatory": "YES"},
        {"name": "figi", "type": "STRING", "mandatory": "YES"},
        {"name": "isin", "type": "STRING", "mandatory": "YES"},
        {"name": "timestamp_utc", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "seq_no", "type": "BIGINT", "mandatory": "YES"},
        {"name": "bid", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "ask", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "bid_size", "type": "BIGINT", "mandatory": "NO"},
        {"name": "ask_size", "type": "BIGINT", "mandatory": "NO"},
        {"name": "trade_price", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "trade_size", "type": "BIGINT", "mandatory": "NO"},
        {"name": "trade_id", "type": "STRING", "mandatory": "NO"},
        {"name": "side", "type": "STRING", "mandatory": "NO"},
        {"name": "liquidity_flag", "type": "STRING", "mandatory": "NO"},
        {"name": "recv_ts", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "checksum", "type": "STRING", "mandatory": "NO"},
    ],
    "TBL_ORDERBOOK_SNAPSHOT": [
        {"name": "snapshot_id", "type": "STRING", "mandatory": "YES"},
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "timestamp_utc", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "level", "type": "INT", "mandatory": "YES"},
        {"name": "bid_price", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "bid_size", "type": "BIGINT", "mandatory": "YES"},
        {"name": "ask_price", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "ask_size", "type": "BIGINT", "mandatory": "YES"},
        {"name": "book_depth", "type": "INT", "mandatory": "YES"},
        {"name": "checksum", "type": "STRING", "mandatory": "NO"},
    ],
    "TBL_VWAP_INTRADAY": [
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "interval", "type": "STRING", "mandatory": "YES"},
        {"name": "vwap", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "volume", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "start_ts", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "end_ts", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
    ],
    # --- EXECUTION & TRADING ---
    "TBL_ORDERS": [
        {"name": "order_id", "type": "STRING", "mandatory": "YES"},
        {"name": "parent_id", "type": "STRING", "mandatory": "NO"},
        {"name": "trader_id", "type": "STRING", "mandatory": "NO"},
        {"name": "strategy_id", "type": "STRING", "mandatory": "NO"},
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "qty", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "price", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "side", "type": "STRING", "mandatory": "YES"},
        {"name": "order_type", "type": "STRING", "mandatory": "YES"},
        {"name": "send_ts", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "venue", "type": "STRING", "mandatory": "NO"},
        {"name": "status", "type": "STRING", "mandatory": "YES"},
        {"name": "last_update_ts", "type": "TIMESTAMP", "mandatory": "YES"},
    ],
    "TBL_EXECUTIONS": [
        {"name": "exec_id", "type": "STRING", "mandatory": "YES"},
        {"name": "order_id", "type": "STRING", "mandatory": "YES"},
        {"name": "fill_price", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "fill_size", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "fee", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "liquidity_flag", "type": "STRING", "mandatory": "NO"},
        {"name": "exec_ts", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "venue", "type": "STRING", "mandatory": "NO"},
        {"name": "latency_ms", "type": "DOUBLE", "mandatory": "NO"},
    ],
    "TBL_TRANSACTION_COSTS": [
        {"name": "jurisdiction", "type": "STRING", "mandatory": "YES"},
        {"name": "asset_class", "type": "STRING", "mandatory": "YES"},
        {"name": "commission_rate", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "exchange_fee", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "clearing_fee", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "taxes", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
    ],
    # --- PORTFOLIO & MASTERS ---
    "TBL_POSITIONS_HISTORY": [
        {"name": "portfolio_id", "type": "STRING", "mandatory": "YES"},
        {"name": "position_date", "type": "DATE", "mandatory": "YES"},
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "qty", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "market_value", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "cost_basis", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "currency", "type": "STRING", "mandatory": "YES"},
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
    ],
    "TBL_SECURITIES_MASTER": [
        {"name": "internal_instrument_id", "type": "STRING", "mandatory": "YES"},
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "figi", "type": "STRING", "mandatory": "YES"},
        {"name": "isin", "type": "STRING", "mandatory": "YES"},
        {"name": "name", "type": "STRING", "mandatory": "YES"},
        {"name": "exchange", "type": "STRING", "mandatory": "YES"},
        {"name": "currency", "type": "STRING", "mandatory": "YES"},
        {"name": "sector", "type": "STRING", "mandatory": "NO"},
        {"name": "industry", "type": "STRING", "mandatory": "NO"},
        {"name": "lot_size", "type": "INT", "mandatory": "YES"},
        {"name": "tick_size", "type": "DOUBLE", "mandatory": "YES"},
    ],
    "TBL_BENCHMARKS": [
        {"name": "index_id", "type": "STRING", "mandatory": "YES"},
        {"name": "constituent_symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "weight", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "effective_date", "type": "DATE", "mandatory": "YES"},
        {"name": "source", "type": "STRING", "mandatory": "YES"},
    ],
    "TBL_CORP_ACTIONS": [
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "type", "type": "STRING", "mandatory": "YES"},
        {"name": "ex_date", "type": "DATE", "mandatory": "YES"},
        {"name": "record_date", "type": "DATE", "mandatory": "NO"},
        {"name": "payment_date", "type": "DATE", "mandatory": "NO"},
        {"name": "factor", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "cash_amount", "type": "DOUBLE", "mandatory": "NO"},
    ],
    "TBL_FUNDAMENTALS": [
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "metric_name", "type": "STRING", "mandatory": "YES"},
        {"name": "value", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "report_date", "type": "DATE", "mandatory": "YES"},
        {"name": "filing_date", "type": "DATE", "mandatory": "NO"},
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
    ],
    "TBL_SHORT_INTEREST": [
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "short_pct", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "borrow_availability", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "borrow_fee", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "date", "type": "DATE", "mandatory": "YES"},
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
    ],
    # --- DERIVATIVES & RATES ---
    "TBL_DERIVATIVES_CHAIN": [
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "option_symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "expiry", "type": "DATE", "mandatory": "YES"},
        {"name": "strike", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "option_type", "type": "STRING", "mandatory": "YES"},
        {"name": "implied_vol", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "delta", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "gamma", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "bid", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "ask", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "mid", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "oi", "type": "BIGINT", "mandatory": "NO"},
    ],
    "TBL_RATES_CURVES": [
        {"name": "curve_id", "type": "STRING", "mandatory": "YES"},
        {"name": "tenor", "type": "STRING", "mandatory": "YES"},
        {"name": "rate", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "source", "type": "STRING", "mandatory": "YES"},
        {"name": "date", "type": "DATE", "mandatory": "YES"},
    ],
    # --- MACRO & SOCIAL ---
    "TBL_MACRO_EVENTS": [
        {"name": "event_id", "type": "STRING", "mandatory": "YES"},
        {"name": "timestamp_utc", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "country", "type": "STRING", "mandatory": "YES"},
        {"name": "series", "type": "STRING", "mandatory": "YES"},
        {"name": "actual", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "forecast", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "prior", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "surprise", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "source", "type": "STRING", "mandatory": "YES"},
    ],
    "TBL_REGIME_LABELS": [
        {"name": "date", "type": "DATE", "mandatory": "YES"},
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "regime_type", "type": "STRING", "mandatory": "YES"},
        {"name": "confidence", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
    ],
    "TBL_SENTIMENT_SCORES": [
        {"name": "timestamp", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "source", "type": "STRING", "mandatory": "YES"},
        {"name": "symbol", "type": "STRING", "mandatory": "YES"},
        {"name": "sentiment_score", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "confidence", "type": "DOUBLE", "mandatory": "NO"},
    ],
    # --- GOVERNANCE, RISK & LEGAL ---
    "TBL_DATA_PROVENANCE": [
        {"name": "ingestion_id", "type": "STRING", "mandatory": "YES"},
        {"name": "source", "type": "STRING", "mandatory": "YES"},
        {"name": "schema_version", "type": "STRING", "mandatory": "YES"},
        {"name": "file_hash", "type": "STRING", "mandatory": "YES"},
        {"name": "ingest_ts", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "operator", "type": "STRING", "mandatory": "YES"},
    ],
    "TBL_DATA_QUALITY_FLAGS": [
        {"name": "row_id", "type": "STRING", "mandatory": "YES"},
        {"name": "table_name", "type": "STRING", "mandatory": "YES"},
        {"name": "issue_code", "type": "STRING", "mandatory": "YES"},
        {"name": "severity", "type": "STRING", "mandatory": "YES"},
        {"name": "resolved_flag", "type": "BOOLEAN", "mandatory": "YES"},
        {"name": "resolution_ts", "type": "TIMESTAMP", "mandatory": "NO"},
    ],
    "TBL_LEGAL_EVENTS": [
        {"name": "event_id", "type": "STRING", "mandatory": "YES"},
        {"name": "counterparty", "type": "STRING", "mandatory": "YES"},
        {"name": "description", "type": "STRING", "mandatory": "YES"},
        {"name": "date_reported", "type": "DATE", "mandatory": "YES"},
        {"name": "severity_score", "type": "INT", "mandatory": "YES"},
    ],
    "TBL_RISK_LIMITS_USAGE": [
        {"name": "date", "type": "DATE", "mandatory": "YES"},
        {"name": "desk_id", "type": "STRING", "mandatory": "YES"},
        {"name": "limit_type", "type": "STRING", "mandatory": "YES"},
        {"name": "limit_value", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "usage_value", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "breached_flag", "type": "BOOLEAN", "mandatory": "YES"},
    ],
    "TBL_COUNTERPARTY_EXPOSURES": [
        {"name": "date", "type": "DATE", "mandatory": "YES"},
        {"name": "counterparty_id", "type": "STRING", "mandatory": "YES"},
        {"name": "instrument", "type": "STRING", "mandatory": "YES"},
        {"name": "exposure_amount", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "collateral", "type": "DOUBLE", "mandatory": "NO"},
        {"name": "haircut", "type": "DOUBLE", "mandatory": "NO"},
    ],
    "TBL_SYSTEM_METRICS": [
        {"name": "record_ts", "type": "TIMESTAMP", "mandatory": "YES"},
        {"name": "host", "type": "STRING", "mandatory": "YES"},
        {"name": "cpu_pct", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "ram_mb", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "net_latency_ms", "type": "DOUBLE", "mandatory": "YES"},
        {"name": "time_sync_offset_ms", "type": "DOUBLE", "mandatory": "YES"},
    ],
}


def list_tables() -> List[str]:
    return sorted(SCHEMAS.keys())


def get_schema(table_name: str) -> List[Dict[str, str]]:
    return SCHEMAS.get(table_name, []).copy()


def get_schema_with_lineage(table_name: str) -> List[Dict[str, str]]:
    """Esquema lógico + campos de linhagem em falta (contrato Tier-0)."""
    base = SCHEMAS.get(table_name, [])
    names = {c["name"] for c in base}
    extra = [c.copy() for c in CANONICAL_LINEAGE_FIELDS if c["name"] not in names]
    return [*base, *extra]
