# DOC-PARRF-PSA-ADENDO-HOMOLOGACAO-RESSALVAS-V120-20260415

| Campo | Valor |
|--------|--------|
| **ID oficial** | `DOC-PARRF-PSA-ADENDO-HOMOLOGACAO-RESSALVAS-V120-20260415` |
| **Versão** | 1.0.0 |
| **Data** | 2026-04-15 |
| **Estado** | **OBRIGATÓRIO** — leitura conjunta com o runbook `DOC-PARRF-PSA-RUNBOOK-EXECUCAO-L04-L06-L07-FASE8-V120-20260415` |
| **Destinatário** | **PSA**, Tech Lead, Conselho |
| **Classificação** | Uso interno — TIER-0 PARR-F |

---

## 1. Finalidade

Este documento **oficializa as ressalvas** técnicas à homologação narrativa dos gates L-06, L-04, L-07 e Fase 8, para que o PSA **execute e arquive** o estado real sem extrapolação: o que está **PASS**, o que está **CONDICIONAL** e o que está **PENDENTE**.

**Instrução:** enviar este ficheiro **em anexo** a qualquer comunicação de “missão concluída” relacionada com o runbook de 2026-04-15.

---

## 2. Ressalvas por gate (vinculativas)

### 2.1 L-06 — Paridade Git

| Afirmação permitida | Afirmação **não** permitida sem prova adicional |
|---------------------|--------------------------------------------------|
| “Foi executado `git_parity_check.py` e existe `ssot_parity_report_*.json`.” | “L-06 PASS / clones alinhados” se `parity_match` for **false** (drift). |

**Se existir assimetria entre clones:** o gate L-06 está **CONDICIONAL**. Conclusão só é **PASS** após:

- `HEAD` idêntico nos dois repositórios referidos no relatório, **ou**
- **Ata** assinada (COO/Tech Lead) com política explícita (ex.: “Desktop canónico; nebular-kuiper é espelho com lag aceite até data X”) e SHA de referência registado.

**Ação PSA:** anexar o JSON de paridade à pasta de provas e **marcar na ata** “L-06: PASS” ou “L-06: DRIFT — pendente alinhamento / excepção”.

---

### 2.2 L-04 — Validação jsonschema em lote

| Afirmação permitida | Ressalva |
|---------------------|----------|
| “`validate_audit_batch.py` exit 0 e `pass_rate = 1.0` no conjunto validado.” | O PASS aplica-se **ao glob e ao `max` utilizados**; não implica todos os JSONs históricos do disco. |

**Ação PSA:** conservar `l04_validation_summary.json` e, se gerado, o CSV.

---

### 2.3 L-07 — Smoke do orquestrador

| Afirmação permitida | Ressalva |
|---------------------|----------|
| “10/10 runs com exit 0 do script e `status != ERROR` nos audits associados.” | Não confundir com execução **MQL5 live** nem com **PnL**. |

**Ação PSA:** conservar `l07_smoke_summary_*.json` e logs na pasta oficial.

---

### 2.4 Fase 8 — Spike Postgres

| Afirmação permitida | Afirmação **não** permitida |
|---------------------|-----------------------------|
| “Spike **não** foi executado com sucesso L3: ausência de DSN / aborto por configuração.” | “Fase 8 homologada” ou “Postgres L3 PASS” **sem** ficheiro `spike_phase8_*.json` com `phase8_pass: true`. |

**Travão de segurança** (sem DSN): conta como **controlo**, não como **conclusão** da Fase 8.

**Ação PSA:** quando existir DSN aprovado e ambiente autorizado, reexecutar `postgres_spike_phase8.py` e arquivar o JSON/TXT com `phase8_pass: true`. Até lá, checklist runbook item Fase 8 = **PENDENTE** ou **N/A (sem DSN)** — **nunca** “verde” como sucesso de conectividade.

---

## 3. Repositório / GitHub

- Referências a commit (ex.: `7efa1f2`) devem ser **verificáveis** com `git show <hash>` no remoto.  
- **Não** versionar DSN, passwords ou `.env` com segredos.  
- Evidências em `00_PROVAS_AUDITORIA\` sujeitas a revisão manual antes de `git push`.

---

## 4. Texto mínimo para ata (copiar se adequado)

> Homologação parcial runbook `DOC-PARRF-PSA-RUNBOOK-EXECUCAO-L04-L06-L07-FASE8-V120-20260415`, com adendo `DOC-PARRF-PSA-ADENDO-HOMOLOGACAO-RESSALVAS-V120-20260415`: **L-04 e L-07 conforme métricas em ficheiros anexos**. **L-06:** conforme `ssot_parity_report_*.json` — paridade global apenas com `parity_match: true` ou excepção escrita. **Fase 8:** pendente execução com DSN aprovado até existir `phase8_pass: true` em relatório JSON oficial.

---

## 5. Registo de versões

| Versão | Data | Notas |
|--------|------|--------|
| 1.0.0 | 2026-04-15 | Adendo inicial de ressalvas para PSA. |

---

**Fim do documento** — `DOC-PARRF-PSA-ADENDO-HOMOLOGACAO-RESSALVAS-V120-20260415`
