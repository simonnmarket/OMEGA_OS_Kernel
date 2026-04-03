# Catálogo OHLCV Unificado (Plano V1)
**Fase:** PH-FS-02
**ID:** DOC-PLAN-OHLCV-20260403

Este documento estabelece o plano formal para o Catálogo OHLCV unificado, conforme a arquitetura de armazenamento "Medallion" adotada no FIN-SENSE DATA MODULE (Tier-0 e MVP).

## 1. Regras de Árvore Canônica (Hive-style Partitioning)
Todos os dados OHLCV devem repousar sob:
`FIN_SENSE_DATA/bronze/market_data/ohlcv/symbol=<ID>/timeframe=<TF>/year=<YYYY>/month=<MM>/`

Exemplo de Caminho: 
`FIN_SENSE_DATA/bronze/market_data/ohlcv/symbol=XAUUSD/timeframe=M1/year=2026/month=03/part_00001.csv`

## 2. Índice Mestre (Catálogo)
O arquivo mestre atual `nebular-kuiper/OHLCV_DATA/_INDEX.csv` servirá de âncora até a migração, devendo incorporar as seguintes colunas obrigatórias:
- `ingestion_id` (UUID gerado durante o lote).
- `file_hash` (SHA3-256 do arquivo fatiado associado).

## 3. Depreciação Explícita
**FICA DEPRECADO** qualquer processo de ingestão novo utilizando a estrutura de nomeação temporal `Auditoria PARR-F/inputs/OHLCV_DATA/grafico_*`. Os arquivos existentes serão lidos sem alterações para fins de reprodução histórica, recebendo a flag `RISCO-AUDITORIA` se não migrarem no MVP.

## 4. Testabilidade (Gate PH-FS-02)
**Situação: KPI-06 PENDENTE.**
O plano não pode afirmar `KPI-06 = 1.0` sem medição quantitativa oficial gerada via script. A cobertura de 100% sobre o conjunto OHLCV citado permanece como meta, mas o indicador em si fica dependente da execução do validador (e da posterior geração de um `KPI_REPORT_*.json`). Fase PH-FS-02 marcada como PARCIAL_COM_PROVA.
