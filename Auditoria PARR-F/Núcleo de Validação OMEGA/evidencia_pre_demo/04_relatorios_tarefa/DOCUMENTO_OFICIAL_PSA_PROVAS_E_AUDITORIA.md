# Documento oficial — Provas rastreáveis e auditoria de refutação (PSA)

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-OFC-PSA-PROVAS-AUD-20260403` |
| **Versão** | 1.0 |
| **Data** | 3 de abril de 2026 |
| **Para** | PSA (execução, custódia, preenchimento de provas) |
| **Norma mãe** | `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` (`DOC-UNICO-PSA-MESTRE-20260403`) |
| **Objectivo** | **Eliminar subjetividade:** cada afirmação verificável tem **ID**, **artefacto**, **comando ou predicado**, **resultado actual** e **PASS/FAIL** binário. |

---

## 1. Princípios (não negociáveis)

1. **Prova sem ID = não existe** para efeitos de auditoria.  
2. **Subjetividade proibida** nos campos `resultado_actual` e `veredito`: só valores **observáveis** (saida de comando, hash, contagem, path existente, diff vazio) ou **`N/D`** com justificativa **uma linha** em `bloqueador`.  
3. **Rastreio:** toda prova referencia `git_head` e `ts_utc` ISO8601 UTC.  
4. **Encadeamento:** `req_id` → `proof_id` → ficheiros no disco; a matriz (CSV/JSON) é a vista consolidada.

---

## 2. Identificadores oficiais

| Tipo | Formato | Exemplo |
|------|---------|---------|
| **Requisito** | `REQ-<DOC>-<NNN>` | `REQ-UNICO-001` |
| **Prova** | `PRF-<FASE>-<YYYYMMDD>-<SEQ>` | `PRF-PHFS01-20260403-001` |
| **Pacote de auditoria** | `AUD-<YYYYMMDD>-<git_sha_7>` | `AUD-20260403-2b906ec` |
| **Run de checklist** | `CHK-<YYYYMMDD>-<HHMMSS>Z` | `CHK-20260403-143000Z` |

**Seq:** `001`…`999` por fase e dia; não reutilizar ID após publicação.

---

## 3. Modelo de prova (campos obrigatórios)

Cada prova é **um** ficheiro JSON (ou **uma** linha em `MATRIZ_PROVAS.csv`) com:

| Campo | Tipo | Regra |
|-------|------|--------|
| `proof_id` | string | Formato §2 |
| `req_id` | string | Liga a requisito na matriz |
| `doc_ref` | string | Doc-ID que impõe o requisito |
| `fase` | string | Ex.: `PH-FS-01`, `PH-FS-02`, `TIER0` |
| `titulo_curto` | string | Máx. 120 chars |
| `artefacto_obrigatorio` | string | Path relativo ao repo ou `MANIFEST:...` |
| `comando_ou_predicado` | string | Comando exacto **ou** descrição do teste automático |
| `resultado_esperado` | string | Predicado verificável (ex.: `exit_code==0`, `ficheiro existe`, `sha256==...`) |
| `resultado_actual` | string | Copiado **literal** da execução |
| `veredito` | string | **`PASS`** ou **`FAIL`** apenas |
| `bloqueador` | string \| null | Se `FAIL` ou `N/D`, uma linha; senão `null` |
| `git_head` | string | 40 hex |
| `ts_utc` | string | ISO8601 Z |

**FAIL permitido** com prova válida: documenta não-conformidade; **proibido** `veredito` vazio ou `MAYBE`.

---

## 4. Matriz de rastreio (obrigatória)

Ficheiro: `MATRIZ_RASTREIO_REQ_PROVA.csv` (template em `templates_auditoria_psa/`).

Colunas:

`req_id`, `req_texto_ou_citacao`, `proof_id`, `veredito_agregado`, `ultima_actualizacao_utc`, `responsavel`

- **veredito_agregado:** `PASS` só se **todas** as provas ligadas ao REQ forem `PASS`; senão `FAIL`.

---

## 5. Checklist de tarefas (blocos não subjectivos)

O script `psa_refutation_checklist.py` materializa a checklist com IDs `CHK-ITEM-NNN`. Cada item exige **uma prova** ou **isento** com `proof_id` = `PRF-EXEMPT-...` e `bloqueador` = justificativa aceite pelo DOC-OFC (ex.: “fora de âmbito declarado em §X”).

### Bloco A — Baseline de repositório

| ID | Tarefa verificável | Prova mínima |
|----|-------------------|--------------|
| CHK-ITEM-001 | `git rev-parse HEAD` registado | PRF com saida 40 hex |
| CHK-ITEM-002 | `PSA_RUN_LOG.jsonl` existe e é JSONL válido | PRF: parser linhas OK |
| CHK-ITEM-003 | `INVENTARIO_FONTES_DADOS_v1.csv` existe | PRF: ficheiro existe + ≥1 linha dados |

### Bloco B — FIN-SENSE / Handoff

| ID | Tarefa verificável | Prova mínima |
|----|-------------------|--------------|
| CHK-ITEM-010 | `FIN‑SENSE DATA MODULE.txt` presente no path Conselho | PRF: path existe |
| CHK-ITEM-011 | KPIs definidos (01–07) documentados no mestre | PRF: grep ou diff vs template |

### Bloco C — Tier-0

| ID | Tarefa verificável | Prova mínima |
|----|-------------------|--------------|
| CHK-ITEM-020 | Último `PSA_GATE_CONSELHO_ULTIMO.txt` existe | PRF: ficheiro existe |
| CHK-ITEM-021 | `verify_tier0_psa.py` exit 0 (quando aplicável ao scope) | PRF: log com exit_code |

### Bloco D — PH-FS-02 (quando iniciada)

| ID | Tarefa verificável | Prova mínima |
|----|-------------------|--------------|
| CHK-ITEM-030 | `CATALOGO_OHLCV_PLANO_v1.md` criado | PRF: existe |

*(O script inclui a lista completa como estrutura de dados.)*

---

## 6. Execução do script (PSA)

```bash
python psa_refutation_checklist.py --emit-template
python psa_refutation_checklist.py --validate ./templates_auditoria_psa/exemplo_prova.json
python psa_refutation_checklist.py --report
```

- `--emit-template`: gera/atualiza ficheiros modelo em `templates_auditoria_psa/`.  
- `--validate <ficheiro>`: valida um JSON de prova.  
- `--report`: imprime checklist com estado **PENDENTE** até existir `proof_id` ligado.

---

## 7. Relatório de auditoria (pacote final)

Nome: `RELATORIO_AUDITORIA_<AUD-ID>.md` contendo:

1. Tabela copy-paste da matriz (ou CSV anexo).  
2. Lista de `proof_id` com paths dos JSON.  
3. `git_head` e `CHK-...` do run.  
4. **Declaração:** “Nenhum requisito em âmbito ficou sem prova ou sem FAIL justificado.”

---

## 8. Submissão ao PSA (agora)

**Enviar:**  
- Este documento (`DOC-OFC-PSA-PROVAS-AUD-20260403`)  
- `templates_auditoria_psa/*`  
- `psa_refutation_checklist.py`  
- `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` (contexto normativo)

**Compromisso:** preencher provas **antes** de declarar conclusão de fase; auditoria de refutação só sobre pacote `AUD-*` fechado.

---

*Fim — `DOC-OFC-PSA-PROVAS-AUD-20260403`*
