# FIN-SENSE DATA MODULE v1.2

Hub central (SSOT lógico) com **23 tabelas** e contrato canónico **v1.2**.

**Código (pacote):** `nebular-kuiper\modules\FIN_SENSE_DATA_MODULE\`  
**Dados / lake local:** `nebular-kuiper\FIN_SENSE_DATA\hub\`  
**Governança:** `nebular-kuiper\governance\`

## Instalação (editable)

```powershell
cd "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\modules\FIN_SENSE_DATA_MODULE"
pip install -e .
```

## Importação

```python
from fin_sense_data_module.schemas.schema_definitions import get_schema, SCHEMA_VERSION
from fin_sense_data_module.storage import FinSenseStorage
```

## Objectivo

Centralizar formatos de dados num **contrato único**; servir research, execução e relatórios (incl. CEO) com **schema versionado**; manter o módulo **expansível** e **desacoplado** de um único conector ou motor de análise.

## Nó canónico

- `TBL_SECURITIES_MASTER.internal_instrument_id` — mapeamento FIGI + ISIN + symbol + exchange + currency.

## Camadas

| Camada | Uso |
|--------|-----|
| `bronze/` | Raw normalizado + manifests |
| `silver/` | Curated / analytics |
| `gold/` | Agregados CEO |

## Scripts

- `scripts/validate_hub_integrity.py` — `GATE_GLOBAL: PASS` (23 tabelas)
- `scripts/ingest_demo_to_bronze.py` — demo Bronze em `FIN_SENSE_DATA\hub\`

## Governança

- `DOC-OFC-DESVIO-PADRAO-ESTRUTURAL-MODULES-FINSENSE-20260404-002`
- `DOC-OFC-RESOLUCAO-REALINHAMENTO-FINSENSE-20260404-002`
