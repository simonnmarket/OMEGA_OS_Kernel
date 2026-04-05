-- Referência: fin_sense_data_module.demo_log_swing_ingest.DDL_BRONZE_DEMO_LOG
-- Schema bronze — tabela demo swing (Fase 2 Fatia 1)

CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.demo_log_swing_trade (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  y DOUBLE PRECISION NOT NULL,
  x DOUBLE PRECISION NOT NULL,
  spread DOUBLE PRECISION NOT NULL,
  z DOUBLE PRECISION NOT NULL,
  beta DOUBLE PRECISION NOT NULL,
  signal_fired BOOLEAN NOT NULL,
  order_filled BOOLEAN NOT NULL,
  ram_mb DOUBLE PRECISION,
  cpu_pct DOUBLE PRECISION,
  proc_ms DOUBLE PRECISION,
  opp_cost DOUBLE PRECISION,
  sha3_line TEXT NOT NULL,
  source_file TEXT NOT NULL,
  ingestion_id TEXT NOT NULL,
  ingest_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_demo_log_swing_ingest ON bronze.demo_log_swing_trade (ingestion_id);
