Script operacional — Fase PH-FS-01 (PSA: execução, persistência e métricas)

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-SCRIPT-OPS-PH-FS-01-20260403` |
| **Fase** | `PH-FS-01` — Inventário de fontes de dados |
| **Norma mãe** | `DOC-SCRIPT-EXEC-PSA-20260327` + `DOC-HANDOFF-PSA-20260403-UNIFIED` |
| **Executor único** | **PSA** (actualiza, grava e versiona no sistema; evita deriva por múltiplos autores sem coordenação) |

---

## 1. Princípio: uma fonte de verdade operacional

- **Toda** actualização desta fase **deve** ser **gravada** sob `evidencia_pre_demo/04_relatorios_tarefa/` (ou subpasta acordada abaixo), com **nome de ficheiro previsível** e **registo no log de runs**.  
- **Não** editar silenciosamente ficheiros “oficiais” (`STATUS_ANEXOS_CONSELHO.md`, `HANDOFF_...`, `SCRIPT_EXECUCAO_...`) **sem** entrada no **PSA_RUN_LOG** e, quando aplicável, **bump de versão** do inventário.  
- **Conflitos:** antes de `commit`, confirmar `git status` e que o **HEAD** no log coincide com `git rev-parse HEAD`.

---

## 2. Onde gravar (estrutura recomendada)

Base (relativa ao repositório `nebular-kuiper`):

```text
Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/
  INVENTARIO_FONTES_DADOS_v1.csv          # entrega principal PH-FS-01 (imutável após fecho; próximas versões = v2, v3)
  ph_fs01/                                 # pasta opcional: trabalhos intermedios do PSA
    README.md                              # quem altera, último run_id
  PSA_RUN_LOG.jsonl                        # log append-only (uma linha JSON por acção relevante)
  STATUS_ANEXOS_CONSELHO.md              # só actualizar se o estado dos anexos mudar (com nova entrada no RUN_LOG)
```

**Regra de versão:** `INVENTARIO_FONTES_DADOS_v1.*` **fechado** após gate verde da fase; correções posteriores → **novo ficheiro** `v2` ou anexo `INVENTARIO_FONTES_DADOS_v1_ERRATA_<date>.md` com referência cruzada.

---

## 3. Log obrigatório — `PSA_RUN_LOG.jsonl`

**Formato:** uma linha JSON por evento (append; **não** apagar linhas antigas).

Campos mínimos por linha:

| Campo | Descrição |
|-------|-----------|
| `ts_utc` | ISO8601 UTC |
| `run_id` | Ex.: `PS-20260403-PH-FS-01-<git_sha_7>` |
| `phase` | `PH-FS-01` |
| `git_head` | Saída actual de `git rev-parse HEAD` |
| `action` | Ex.: `inventario_row_added`, `file_saved`, `gate_check`, `tier0_verify`, `manual_note` |
| `artifact` | Path relativo do ficheiro tocado (ou `null`) |
| `metrics` | Objeto opcional: ex. `{"kpi06_preview": null, "rows_inventario": 42}` |
| `command` | Comando shell **exacto** (ou `null`) para reprodutibilidade |

**Exemplo de linha:**

```json
{"ts_utc":"2026-04-03T18:00:00Z","run_id":"PS-20260403-PH-FS-01-593fe793","phase":"PH-FS-01","git_head":"593fe7938abe058af8779745bbb55f2209586391","action":"file_saved","artifact":"04_relatorios_tarefa/INVENTARIO_FONTES_DADOS_v1.csv","metrics":{"rows":12},"command":null}
```

---

## 4. Esquema mínimo — `INVENTARIO_FONTES_DADOS_v1.csv`

Colunas **obrigatórias** (cabeçalho na primeira linha):

| Coluna | Conteúdo |
|--------|----------|
| `row_id` | `INV-001`, `INV-002`, … (estável após publicação) |
| `module_code` | `FS`, `OM`, `PS`, `TR`, `MD` (HANDOFF §2.1) |
| `asset_or_scope` | Símbolo, par, ou `GLOBAL` |
| `source_type` | `CSV`, `DEMO_LOG`, `OHLCV_INDEX`, `REPORT_MD`, `SCRIPT`, `OTHER` |
| `path_relative` | Caminho relativo ao repo ou `ABS:<path>` se inevitável |
| `schema_version` | Ex. `v1.0` ou `N/D` |
| `consumes_reports_or_runs` | IDs ou títulos de relatórios / runs que **usam** esta fonte |
| `last_known_git_head` | HEAD quando a linha foi validada |
| `dependency_status` | `OK` \| `PENDENTE-CTO` \| `RISCO-AUDITORIA` \| `file_not_found` |
| `notes` | Livre (curto) |

**Gate PH-FS-01:** não existe linha com `dependency_status` vazio; origem desconhecida → **`RISCO-AUDITORIA`** obrigatório.

---

## 5. Complemento — o que ainda não estava finalizado (explicitar no inventário)

Incluir **pelo menos uma linha por tema** abaixo (mesmo que `dependency_status=PENDENTE-CTO`):

| Tema pendente | O que registar |
|---------------|----------------|
| `Inventário Expandido...txt` | Ausência confirmada em `STATUS_ANEXOS_CONSELHO.md`; impacto: roadmap métricas institucionais **não** amarrado a ficheiro local |
| `DDL em estilo Parquet Delta.txt` | Idem; impacto: DDL físico **ainda** derivado só de `FIN‑SENSE DATA MODULE.txt` |
| `Scripts Spark SQL...txt` | Idem; impacto: receitas VaR/CVA **não** executáveis até ingestão + cluster |
| Duplicação `inputs/OHLCV_DATA/grafico_*` | Referenciar ambas as árvores se ainda em uso; marcar `RISCO-AUDITORIA` até PH-FS-02 |

Isto **fecha** lacunas sem simular ficheiros que não existem.

---

## 6. Script de execução — passos ordenados (PH-FS-01)

Executar **na ordem**; registar cada passo no `PSA_RUN_LOG.jsonl`.

| Passo | Acção | Verificação |
|-------|--------|-------------|
| **6.1** | `git rev-parse HEAD` → copiar para cabeçalho de trabalho e para primeira linha de log do dia | HEAD coerente com Fase 0 |
| **6.2** | Listar relatórios em `04_relatorios_tarefa/*.md` relevantes (stress, demo, auditoria) | Tabela preliminar no `ph_fs01/` ou directamente no CSV |
| **6.3** | Rastrear cada relatório → ficheiros de dados citados (CSV, DEMO_LOG, OHLCV) | Uma ou mais linhas `INV-*` por fonte |
| **6.4** | Incluir `nebular-kuiper/OHLCV_DATA/_INDEX.csv` e `Auditoria PARR-F/inputs/OHLCV_DATA/` se ainda referenciados | `dependency_status` correcto |
| **6.5** | Incluir scripts Python críticos (ex.: `finsense_validation_kit.py`, gate, verify) com `module_code=PS` ou `TR` | Linhas dedicadas |
| **6.6** | Preencher `INVENTARIO_FONTES_DADOS_v1.csv` e guardar | Encoding UTF-8 |
| **6.7** | (Opcional) `python finsense_validation_kit.py` num lote de teste — registar métricas no RUN_LOG | Métricas só ilustrativas até haver `ingestion_id` real |
| **6.8** | `verify_tier0_psa.py` / gate se alterou ficheiros rastreados | Se OK, log `gate_check` |
| **6.9** | Fecho: linha final no RUN_LOG com `action":"phase_complete"` e `metrics.rows_inventario` | Gate PH-FS-01 satisfeito |

---

## 7. Métricas e auditoria (esta fase)

| Métrica | Onde | Meta |
|---------|------|------|
| **Cobertura do inventário** | `#linhas com dependency_status != vazio` / `#linhas` | **1,0** |
| **Rastreio HEAD** | Cada linha ou nota global com `last_known_git_head` | **100%** das linhas “ativas” |
| **KPI-06 (prévia)** | Para um relatório piloto, conjunto S de símbolos citados vs catálogo | Registar valor no RUN_LOG (pode ser `null` até PH-FS-02) |

Referência completa de KPIs: HANDOFF §4.

---

## 8. Anti-conflito (resumo)

1. **Um executor de escrita:** preferir um único processo PSA por janela de edição do inventário.  
2. **Não sobrescrever v1 fechado** — usar nova versão ou errata.  
3. **Sincronizar** com `STATUS_ANEXOS_CONSELHO.md` apenas se os anexos mudarem (novo ficheiro no Conselho).  
4. **Commits** pequenos e mensagens com `PH-FS-01` + `run_id`.

---

## 9. Saída e transição para PH-FS-02

Quando o gate PH-FS-01 estiver **verde**:

1. Última linha em `PSA_RUN_LOG.jsonl` com `phase_complete`.  
2. Actualizar `SCRIPT_EXECUCAO_PSA_CAMINHO_PROPOSTA.md` com **Registo de execução — PH-FS-01 (CONCLUÍDA)** (mesmo padrão da Fase 0).  
3. Iniciar **PH-FS-02** apenas após inventário **aprovado internamente** (catálogo OHLCV unificado).

---

## 10. Referências rápidas

- `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` — IDs, KPIs, parâmetros.  
- `FIN‑SENSE DATA MODULE.txt` — modelo de dados alvo.  
- `STATUS_ANEXOS_CONSELHO.md` — estado dos anexos Conselho.  
- `finsense_validation_kit.py` — PAR/IC/TCR para lotes futuros.

---

*Fim — `DOC-SCRIPT-OPS-PH-FS-01-20260403` — execução exclusiva PSA; persistir sempre.*
