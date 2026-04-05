# DOC-TESTES — Fase 2, Fatia 1 (evidências de execução)

**Estado:** `FECHADO_CODIGO` — testes abaixo **executados com sucesso** nesta máquina; **E2E PostgreSQL** (ingestão + `COUNT`) fica **fechado no ambiente** onde existirem Postgres, DDL aplicada e `PGPASS` (comandos na § Gate DB).

**Contrato:** `governance/DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412.md`

## Ambiente (máquina de evidência)

| Campo | Valor |
|--------|--------|
| OS | Windows-10-10.0.26200-SP0 |
| RAM | *(não medido nesta execução)* |
| CPU | 12 cores (lógicos) |
| Postgres | **Não ligado nesta sessão** — ingestão DB não executada |
| Commit Git | `19cc9acaa0b86f6de0dc20b564c2c0c5d27bee93` |
| Python | 3.11.9 |

## A1–A5 (resultado)

| ID | Pass / Fail | Evidência (comando + excerto) |
|----|-------------|-------------------------------|
| A1 | **PARCIAL** | CSV real: `count_rows_in_csv` = **73** linhas (`tests/validate_a1_a5.py`, demo `DEMO_LOG_SWING_TRADE_20260401_T0046.csv`). **COUNT DB = linhas CSV** só após `RUN_DB_COUNT=1` + `PGPASS` + tabela criada. |
| A2 | **PASS** | `python tests/validate_a1_a5.py` → `A2 (reprodutibilidade SHA3): OK em todas as 73 linhas (amostra completa)` |
| A3 | **MANUAL** | Medir com `ingest_pipeline.py` + `time` quando DB disponível. |
| A4 | **MANUAL** | `errors.log` após ingestão real. |
| A5 | **SKIP** (sem credencial) | Script: `A5 (PGPASS definido): SKIP — defina PGPASS`. Com `PGPASS`, repetir para **PASS**. |

## Stress SHA3 (10k linhas sintéticas)

| Critério | Resultado |
|----------|-----------|
| 10k linhas + verificação linha a linha | **PASS** |
| Comando | `python tests/stress_test_10k.py` |
| Excerto | `OK: 10000 linhas sintéticas com SHA3 válido` → `SKIP DB: defina PGPASS para teste de ingestão completo.` |

## Hub (23 tabelas)

| Critério | Resultado |
|----------|-----------|
| Integridade schema | **PASS** |
| Comando | `python modules/FIN_SENSE_DATA_MODULE/scripts/validate_hub_integrity.py` |
| Excerto | `GATE_GLOBAL: PASS` (23 tabelas, schema v1.2) |

## Métricas §5 (relatório)

1. Throughput: *medir na ingestão real*  
2. Erro commit: *medir na ingestão real*  
3. Latência P99 COPY: *medir na ingestão real*  
4. Integridade sha3_line: **100%** nas amostras acima (73 linhas reais + 10k stress)  
5. CPU single-core: *medir na ingestão real*  

## Gate DB (fechar E2E Postgres — uma vez por ambiente)

1. Aplicar `modules/FIN_SENSE_DATA_MODULE/sql/ddl_bronze_demo_log.sql`  
2. `pip install -e modules/FIN_SENSE_DATA_MODULE[ingest]`  
3. Definir `PGPASS` (e variáveis `PG*` conforme `get_connection_dsn` em `demo_log_swing_ingest.py`)  
4. `python tests/stress_test_10k.py` → esperado `OK: COUNT(DB)=10000`  
5. Opcional: `RUN_DB_COUNT=1 python tests/validate_a1_a5.py` com CSV real  

---

## Anexos

- Stress + validação: saída de consola copiada nas células acima (execução documentada em **2026** com commit indicado).  
- CSV demo: `Auditoria PARR-F/omega_core_validation/evidencia_demo_20260401/DEMO_LOG_SWING_TRADE_20260401_T0046.csv`

---

*Última actualização: fecho de módulo FIN_SENSE_DATA_MODULE (código + testes automatizados); módulo futuro de métricas/relatórios deve consumir este pacote como fonte.*
