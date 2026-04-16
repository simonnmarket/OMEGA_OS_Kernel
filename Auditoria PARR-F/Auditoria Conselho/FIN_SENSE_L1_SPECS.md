# DADOS L1 (FIN_SENSE/DOS) - ESPECIFICAÇÃO DE ENTREGA

## 1. Conexividade (DSN)
- **Status Atual:** A variável `FIN_SENSE_DSN` é injetada via ambiente orquestrado (Vault/ENV) e não deve constar em texto limpo no repositório.
- **Formato:** `postgresql://[USER]:[PASS]@[HOST]:[PORT]/[DB]`

## 2. Estrutura de Dados (L1 Schema)
Para processamento via CSV/DF, utilizar o seguinte layout canônico:

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `symbol` | STRING | ID do Ativo (ex: XAUUSD) |
| `var_95_usd` | FLOAT | Valor em Risco (95% conf) |
| `cvar_95_usd` | FLOAT | Expected Shortfall |
| `regime_data` | STRING | Estado do mercado (CHOPPY, TREND, etc) |
| `momentum_1m_pct` | FLOAT | Var. percentual 1 minuto |
| `effective_spread` | FLOAT | Fricção real medida no terminal |
| `source_batch_id` | STRING | Lineage ID do lote de dados |
| `computed_at` | TIMESTAMP | Data/Hora da computação (UTC) |

## 3. Timezone e SSOT
- **Timezone:** UTC (Strict). Todas as comparações de `trace_id` e auditoria são baseadas em relógios atômicos sincronizados via NTP e normalizados para UTC.
- **SSOT (Single Source of Truth):** View `v_omega_l1_features_by_symbol`.

---
*Gerado por PSA - Auditoria de Integridade Tier-0*
