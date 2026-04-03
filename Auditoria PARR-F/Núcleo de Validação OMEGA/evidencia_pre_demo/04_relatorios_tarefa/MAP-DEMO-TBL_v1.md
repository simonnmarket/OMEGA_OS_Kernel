# Mapeamento DEMO_LOG para TBL_ORDERS / TBL_EXECUTIONS (v1.0 MVP)

| Metadado | Valor |
|---|---|
| **Fase** | PH-FS-03 |
| **Doc-ID** | `DOC-MAP-DEMO-TBL-20260403` |
| **Alvo** | Integração da telemetria `DEMO_LOG*.csv` à topologia `FIN-SENSE` (Tabelas canônicas) |

---

## Arquitetura de De-Normalização
A telemetria produzida no DEMO OMEGA V10 exibe natureza concatenada (sinal, entrada, stop e validação em linha única). O FIN-SENSE obriga a dissociação entre *Ordem Intenção* e *Execução Efetiva*.

### 1. Tabela Alvo: `TBL_ORDERS` (Intenção/Sinal)
| Campo FIN-SENSE `TBL_ORDERS` | Origem `DEMO_LOG` | Transformação/Fixação |
|---|---|---|
| `order_id` | Gerado estaticamente (hash) | Hashear: `ts_utc` + `symbol` + `action` |
| `ingestion_id` | UUID Batch | UUID Injetado no ato da extração |
| `symbol` | `symbol` | Mapeamento direto (ex: XAUUSD) |
| `created_at` | `timestamp` | Mapeamento direto (Parse DateTime) |
| `order_type` | Fixo (MARKET) | Inferido via comportamento Sniper V10 |
| `side` | `action` | BUY / SELL diretos |
| `status` | Fixo (FILLED) | Inferido no DEMO |

### 2. Tabela Alvo: `TBL_EXECUTIONS` (Confirmação Física)
| Campo FIN-SENSE `TBL_EXECUTIONS` | Origem `DEMO_LOG` | Transformação/Fixação |
|---|---|---|
| `exec_id` | Gerado estaticamente (hash) | Hashear: `order_id` + `price` |
| `order_id` | Derivado de `TBL_ORDERS` | Chave estrangeira (FK) |
| `ingestion_id` | UUID Batch | UUID Injetado no ato da extração |
| `exec_time` | `timestamp` | Mapeamento direto |
| `exec_price` | `price` | Mapeamento direto (Float) |
| `exec_qty` | Fixo (1.0 default) | O DEMO log atual não lista sizes literais; Fixo 1.0 ou buscar via logs do MetaTrader. |
| `commission` | NULL | Não persistido no DEMO |

### 3. Regra de Deduplicação
- `DEMO_LOG` deve ignorar linhas cujo `action` = `COOLDOWN_ACTIVATED` para a inserção das ordens de trade físico.
- Se o campo `price` contiver string vazia, a linha é de Telemetria de Falha, e não vira `order_id`. O Mapeamento é reservado a cruzamentos efetivos.
