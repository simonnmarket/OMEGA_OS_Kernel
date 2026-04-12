# DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414

| Campo | Valor |
|--------|--------|
| **ID do documento** | `DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414` |
| **Versão** | 1.1.0 |
| **Data** | 2026-04-14 |
| **Status** | **EM EXECUÇÃO (PSA)** |
| **Destinatário primário** | **PSA** — execução, validação e arquivo de evidências |
| **Cópia** | COO, CFO, CTO, CIO, CKO, CQO, Tech Lead |
| **Classificação** | Confidencial — uso interno / trilho TIER-0 |
| **Objetivo do projeto (preservado)** | Ecossistema **integrado**, **SSOT** de código e contrato, **evidência antes de aceleração**, progressão **staging → mercado real**, sem **módulos paralelos desalinhados**. |

---

## 1. Resumo executivo

Este documento consolida os **golden points** dos pareceres **COO** e **CFO/Red Team** para a **v1.2.0** do projeto OMEGA. Fecha lacunas estruturais (**RT-B1–B4**) com **gates numéricos**, **árbitro multi-TF**, **schema de auditoria v1.0** e **ordem de marcha** para o PSA. Não declara produção “fechada” sem **PASS** documentado em cada fase.

---

## 2. Gates de baseline (numéricos)

Referência: **RT-B1**. Valores de homologação (ajustar por símbolo/mercado apenas com **ata COO+CFO** + bump de versão do YAML):

| Métrica | Limite PASS | Severidade |
|---------|-------------|------------|
| Latência ingestão P99 | < 500 ms | Crítica |
| Slippage médio | < 2,0 pts (XAUUSD baseline) | Alta |
| Taxa de requotes | < 10 % | Alta |
| Drawdown diário máx. | < 3,5 % | Crítica |
| Integridade audit trail | **100 %** das operações com JSON **schema 1.0** válido | Crítica |

**Artefacto:** `GATES_NUMERICOS_V1.yaml` (mesma pasta que este documento).

---

## 3. Arbitragem multi-TF (regra de ouro)

Referência: **RT-B2**. O timeframe maior (ex.: H1/H4) **veta** sinais desalinhados em TFs menores (M1/M5).

- **Lógica (negócio):** se sinal em TF baixo contradiz tendência em TF alto → **HOLD** ou **VETO** conforme política; neutro no alto → **HOLD**.
- **Implementação de referência:** `ARBITRO_MULTITF_V1.py` — função `arbitrate_signal` → retorno `PASS` | `VETO` | `HOLD` (alinhar ao campo `arbitration_result` no JSON).

---

## 4. Schema de auditoria v1.0

Referência: **RT-B4**. Campos obrigatórios na **raiz** do audit (homologação M-F7 + extensão árbitro):

| Campo | Tipo / notas |
|--------|----------------|
| `schema_version` | `"1.0"` |
| `trace_id` | UUID v4 |
| `orchestrator_version` | `"1.2.0"` (const no schema até novo release) |
| `l1_integration_requested` | boolean |
| `l1_class` | string |
| `provenance_sha256` | 64 hex |
| `arbitration_result` | `PASS` \| `VETO` \| `HOLD` |
| `layers` | objeto (mínimo `dos`; opcional `kernel`, `risk`, `executor`) |

**Artefacto:** `AUDIT_JSON_SCHEMA_V1.0.json` — validação recomendada com `jsonschema` (PSA) em CI e pós-execução.

---

## 5. Instruções PSA (ordem de marcha)

1. **Fase A — Congelamento:** SSOT validado (`git rev-parse HEAD` registado); sem novas capacidades sem teste ponta-a-ponta; validador JSON contra `AUDIT_JSON_SCHEMA_V1.0.json`.
2. **Fase B — Mercado real progressivo:** em **read-only**, injectar falhas e **medir kill switch** (**RT-B3**); só depois **canary**; depois escalação de lotes. Métricas vs `GATES_NUMERICOS_V1.yaml`.
3. **Fase C — Calibração vs correção estrutural:** mudança de **contrato** de dados ou schema → **reinício** dos gates de segurança da fase afectada (**RT-B5**).
4. **Fase D — Go/No-Go:** ata COO + CFO com limites explícitos e pacote de evidências (JSONs, logs, métricas).

**Prova por execução:** cada *milestone* gera relatório `PSA_REPORT_<ID>_<FASE>_<YYYYMMDD>.md` + pasta `evidence/…`.

---

## 6. Anexos instrumentais (execução)

| Anexo | Ficheiro |
|--------|----------|
| A — Gates numéricos | `GATES_NUMERICOS_V1.yaml` |
| B — Árbitro multi-TF | `ARBITRO_MULTITF_V1.py` |
| C — JSON Schema audit | `AUDIT_JSON_SCHEMA_V1.0.json` |

---

## 7. Registo de sugestões aceites (síntese)

| Origem | IDs | Conteúdo |
|--------|-----|-----------|
| **COO** | COO-A1…A6 | Integração primeiro; SSOT; fases A–D; runbook + JSON obrigatório; matriz risco; transparência sem logs |
| **CFO / Red Team** | RT-B1…B6 | Gates numéricos; árbitro; ordem B com falhas antes do canary; schema versionado; critério calibração vs estrutural |
| **Auditoria** | AUD-C1…C3 | ID único PSA; clarificar ficheiro CFO vs Red Team; Fase 7 COO sem misturar com B até PASS em A |

---

## 8. Nota de versão (1.1.0)

- Conteúdo operacional da v1.0.0 **fundido** com o pacote PSA (**gates YAML**, **árbitro PY**, **schema JSON**).
- `AUDIT_JSON_SCHEMA_V1.0.json`: `provenance_sha256` e `arbitration_result` incluídos em **`required`** para alinhar à secção 4 deste ID.

---

**Assinado (processo):**  
*PSA — Execution & Governance Unit*  
*TIER-0 v1.2.0 Integrity Team*

---

**Fim do documento** — `DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414`
