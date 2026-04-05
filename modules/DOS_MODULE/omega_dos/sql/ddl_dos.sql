-- DDL opcional: persistência de execuções DOS (schema configurável via DOS_PG_SCHEMA, default: dos)
-- Executar com permissões adequadas após FIN-SENSE bronze estar disponível.

CREATE SCHEMA IF NOT EXISTS dos;

CREATE TABLE IF NOT EXISTS dos.pipeline_run (
  id BIGSERIAL PRIMARY KEY,
  run_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  dos_version TEXT NOT NULL,
  fin_sense_schema_ref TEXT,
  source TEXT NOT NULL,
  rows_in INTEGER NOT NULL,
  inputs_digest_sha256 TEXT NOT NULL,
  record_digest_sha256 TEXT NOT NULL,
  summary_json JSONB NOT NULL,
  risk_json JSONB NOT NULL,
  market_quality_json JSONB,
  regimes_json JSONB,
  clustering_json JSONB,
  errors_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_dos_pipeline_run_ts ON dos.pipeline_run (run_ts DESC);
CREATE INDEX IF NOT EXISTS idx_dos_pipeline_inputs ON dos.pipeline_run (inputs_digest_sha256);
