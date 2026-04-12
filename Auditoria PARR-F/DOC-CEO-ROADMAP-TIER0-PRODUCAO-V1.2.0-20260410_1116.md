# Roadmap oficial TIER-0 produção — especificação completa

**ID oficial (completo):** `DOC-CEO-ROADMAP-TIER0-PRODUCAO-V1.2.0-20260410_1116`  

**Timestamp:** 2026-04-10 11:16 CEST  
**Classificação:** contrato técnico / roadmap executivo (CEO Auditoria)  
**Versão de referência do pacote:** TIER-0 **v1.2.0** (`omega_orquestador_tier0_v120.py`)  

**Documentos correlatos (IDs completos):**

| ID | Função |
|----|--------|
| `REQ-PARRF-DIRETRIZES-CRITICAS-CODIGO-TIER0-V120-20260411` | Diretrizes — separação DOS vs Executor; sem `order_send` na Ponte/DOS |
| `DOC-PARRF-REGISTO-OFICIAL-CONSOLIDADO-PSA-COO-FASE6-L1-FIN-SENSE-V120-20260410` | Encerramento Fase 6 documental; âncoras Git |
| `REQ-PARRF-COO-APRESENTACAO-FASE6-L1-FIN-SENSE-SSOT-V120-20260406` | Apresentação COO / SSOT |

---

## Objetivo

Definir o caminho **L1 → L4** até sistema **operacional** com **monitoramento**, com dependências explícitas e critérios de PASS auditáveis — **sem** confundir estado de código com estado de infraestrutura em produção (evidência = logs + JSON + commits).

---

## Matriz completa — 12 fases TIER-0 v1.2.0

| Fase | Componente | PASS (critério resumido) | Integração | Status declarado |
|------|-------------|---------------------------|------------|------------------|
| **1–6** | Base orquestrador | 4 camadas L1→L4 + auditoria JSON + `trace_id`; SHA canónico documentado (`5cae0a9dda67cc2652c11f86bd117146dcd65300`) | Independente do Postgres real | Concluído (âmbito PARR-F Fase 6) |
| **7** | L1 FIN-SENSE DB | `layers.dos.errors == []`, `provenance_sha256` 64 hex, métricas numéricas coerentes para **XAUUSD** com dados reais | VIEW Postgres + DSN staging/prod homologado | Pendente |
| **8** | Núcleo L2 | `direction` BUY/SELL (ou HOLD quando bloqueado), `confidence` &gt; 0.6 quando não HOLD, `regime` alinhado a L1 | Depende de L1 com dados reais | Planeado |
| **9** | Válvulas L3 | `risk.cleared` conforme matriz de testes; `reasons` curtos e auditáveis | Depende de L2 | Planeado |
| **10** | L4 MT5 ao vivo | `order_id` real MT5, `status` ≠ dry-run **apenas** com ordem escrita + ambiente live | L3 cleared + MT5 + conta | Pendente (alto risco) |
| **11** | Prometheus | Métricas expostas; latência p95 alvo &lt; 500 ms (ajustar por ambiente) | Depende de pipeline L1–L4 instrumentado | Não configurado |
| **12** | Conselho | Aprovação final produção | Fases 1–11 com evidência | Aguardando |

---

## Especificações por fase (detalhe)

### Fase 7 — Banco de dados L1 FIN-SENSE

**Componente:** `FinSenseL1Layer` → Postgres, VIEW por defeito `v_omega_l1_features_by_symbol` (`FIN_SENSE_L1_VIEW`).

**Contrato alvo (alinhado ao código `fin_sense_l1_esqueleto_v120.py`):** `regime_data` é **string** na saída Python (a VIEW pode devolver texto ou enum coercível a string).

**PASS (métricas — alvo de homologação):**

```text
layers.dos (exemplo de forma alvo para homologação):
  symbol: "XAUUSD"
  var_95_usd: float finito e > 0 (quando dados válidos)
  cvar_95_usd: float finito; regra de negócio: tipicamente ≥ var_95 (cauda esquerda)
  regime_data: string não vazia (ex.: CHOPPY_NOISE, TREND_MOMENTUM)
  momentum_1m_pct: float em banda acordada (ex. [-0.05, 0.05] — ajustar com Conselho)
  effective_spread: float > 0 quando aplicável
  provenance_sha256: 64 caracteres hex (hash do registo canónico lido)
  errors: []   ← obrigatório vazio para PASS Fase 7
```

**Estado bloqueante atual (exemplo):** `errors: ["FIN_SENSE_DSN_NOT_SET"]` ou `POSTGRES_ERROR:*` → **Fase 7 bloqueada** até DSN + VIEW + linha de dados.

**DDL / SQL (rascunho ilustrativo — não executar sem DBA):**

O SQL abaixo é **esboço conceitual**. `percentile_cont`, agregações e janelas devem ser validadas contra o schema real de `tbl_market_ticks_raw` (ou equivalente). **Não** copiar para produção sem revisão.

```sql
-- ILUSTRATIVO — VIEW canónica (nome alvo: v_omega_l1_features_by_symbol)
-- Validar: colunas, timezones, granularidade de tick, e definição de "1m" momentum.
CREATE OR REPLACE VIEW v_omega_l1_features_by_symbol AS
SELECT
  symbol,
  computed_at,
  var_95_usd,
  cvar_95_usd,
  regime_data,
  momentum_1m_pct,
  effective_spread,
  source_batch_id
FROM (
  -- placeholder: substituir por agregações reais acordadas com DBA
  SELECT
    'XAUUSD'::text AS symbol,
    NOW() AS computed_at,
    NULL::double precision AS var_95_usd,
    NULL::double precision AS cvar_95_usd,
    'UNKNOWN'::text AS regime_data,
    0::double precision AS momentum_1m_pct,
    NULL::double precision AS effective_spread,
    NULL::text AS source_batch_id
) AS q
WHERE false;  -- forçar falha até DDL real estar pronto
```

**Dependências:** tabela de ticks (ou fonte oficial), DSN (`FIN_SENSE_DSN`), `psycopg2-binary` (ou driver aprovado).

**Impactos:** L2 recebe métricas reais; L3 usa `var_95_usd` para políticas (`OMEGA_VAR_BLOCK_USD`); L4 só indirectamente (tamanho / confiança).

---

### Fase 8 — Núcleo L2 (`KernelDecisionLayer.make_decision`)

**Critério:** decisões coerentes com entrada L1; em stub, matriz de cenários já suportada via env (`OMEGA_DEMO_*`). Com L1 real, thresholds (`OMEGA_MOMENTUM_THRESHOLD`, `MIN_CONFIDENCE`) aplicam-se a dados reais.

**Dependência:** Fase 7 com `errors: []` para o símbolo de teste.

---

### Fase 9 — Válvulas L3 (`RiskValveLayer.validate_trade`)

**Critério:** `cleared` / `reasons` auditáveis; percentagens (“80% cenários”) exigem **conjunto de testes** e relatório — não afirmar sem colar resultados.

**Dependências:** L1 + L2; variáveis como `OMEGA_VAR_BLOCK_USD`.

---

### Fase 10 — L4 MT5 execução ao vivo (`MQL5ExecutorLayer`)

**Critério alvo:** ordem real apenas com **gating** explícito (conta, símbolo, margem, flags de live).

**Recado PARR-F:** `order_send` / execução real pertence ao **Executor (L4)**, não ao DOS/Ponte. Qualquer código live deve vir acompanhado de documento + aprovação e de ambiente controlado.

**Dependências:** Fase 9 (`risk.cleared`), terminal MT5, símbolo ativo, política de margem.

---

### Fase 11 — Monitoramento (Prometheus)

**Critério alvo (exemplos):** `tier0_pipeline_latency_ms` p95; contadores de bloqueio; erros L1; ordens MT5 (se aplicável). **Implementação:** instrumentação no orquestrador + export — a definir com DevOps.

---

### Fase 12 — Conselho

Aprovação formal de **produção** com pacote de evidências (JSON, logs, SHAs, DSN não em repositório).

---

## Inventário de módulos (referência)

| Módulo | Fases | Estado declarado | Pronto produção |
|--------|-------|------------------|-----------------|
| `omega_orquestador_tier0_v120.py` | 1–6 | OK referência | Sim (dry-run / condicional L1) |
| `fin_sense_l1_esqueleto_v120.py` | 6–7 | OK código; falta VIEW + dados | Não até Fase 7 PASS |
| `DOSMetricsLayer` | 1–6 | Stub | Sim (modo stub) |
| `KernelDecisionLayer` | 8 | Implementado; L1 real pendente | Não até Fase 7 |
| `RiskValveLayer` | 9 | Implementado | Não até cadeia L1–L2 validada |
| `MQL5ExecutorLayer` | 10 | Dry-run | Não (live pendente) |
| VIEW Postgres | 7 | DDL pendente DBA | Não |
| Prometheus | 11 | Não configurado | Não |

---

## PSA — Fase 7 (execução imediata)

1. **CEO / DBA:** DSN staging (secretos fora do Git) + DDL da VIEW assinado.  
2. **PSA:** criar VIEW + correr **5× E2E** `python omega_orquestador_tier0_v120.py` com `OMEGA_USE_FIN_SENSE_L1=1`.  
3. **Evidência:** colar JSONs com `errors: []` e `provenance_sha256` preenchido.  
4. **Git:** commit convencional sugerido: `feat(fase7): L1 Postgres real` (após revisão).

---

## Limitações deste roadmap

- Não afirma serviços em execução nem “produção” sem evidência.  
- Percentagens (p95, 80%, 5%) são **metas** — medir no ambiente real.  
- SQL exemplificativo é **placeholder** até DDL aprovado.

---

**Citação oficial:** `DOC-CEO-ROADMAP-TIER0-PRODUCAO-V1.2.0-20260410_1116`

*Registo: COO / CEO Auditoria — Roadmap TIER-0 v1.2.0*
