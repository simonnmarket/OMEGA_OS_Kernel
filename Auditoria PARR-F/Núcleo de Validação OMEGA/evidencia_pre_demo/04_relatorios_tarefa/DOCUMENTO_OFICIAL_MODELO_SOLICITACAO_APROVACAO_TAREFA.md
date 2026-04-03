# MODELO — Documento oficial: solicitação, tarefa, prova e veredito

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-OFC-MODELO-TAR-20260403` |
| **Versão** | 1.0 |
| **Tipo** | Modelo normativo — **obrigatório** para qualquer envio ao PSA que implique trabalho rastreável |
| **Normas associadas** | `DOC-UNICO-PSA-MESTRE-20260403`, `DOC-OFC-PSA-PROVAS-AUD-20260403`, `DOC-SCRIPT-EXEC-PSA-20260327` |
| **Objetivo** | **Nunca confundir** o que foi **solicitado** com o que foi **aprovado** ou **reprovado**. Cada transição tem **ID próprio** e registo obrigatório. |

---

## 1. Princípio jurídico-operacional

| Conceito | Definição | Pode existir sem prova JSON? |
|----------|-----------|------------------------------|
| **Solicitação** | Pedido formal de trabalho ou de verificação | **Sim** (é o gatilho) |
| **Tarefa** | Unidade de execução alinhada a uma fase do roteiro (`PH-FS-xx`, etc.) | **Sim** (estado `ABERTA`) |
| **Prova (`PRF-`)** | Evidência objectiva do resultado | **Não**, se se pretende `APROVADO` |
| **Veredito** | Decisão binária sobre a tarefa **face à solicitação** | **Não** sem preenchimento da linha de decisão |

**Regra de ouro:** **`APROVADO` / `REPROVADO` / `PENDENTE`** só podem aparecer na coluna **veredito_tarefa** depois de existir **linha completa** na tabela §5 (ou CSV §6) com **`proof_id`** preenchido **ou** motivo **`PENDENTE`** explícito (uma linha).

---

## 2. Catálogo de identificadores (obrigatório)

### 2.1 Solicitação (pedido — não é aprovação)

| ID | Formato | Exemplo | Significado |
|----|---------|---------|-------------|
| **SOL** | `SOL-<YYYYMMDD>-<SEQ3>` | `SOL-20260403-001` | Pedido registado; **não** implica sucesso |

### 2.2 Tarefa (unidade de trabalho no roteiro)

| ID | Formato | Exemplo | Significado |
|----|---------|---------|-------------|
| **TAR** | `TAR-<FASE>-<SEQ3>` | `TAR-PHFS02-001` | Tarefa dentro da fase `PH-FS-02` (alinhado a `CHK-ITEM-030`…) |

*Nota:* `TAR-PHFS02-001` liga-se à fase **`PH-FS-02`** do script; o número **001** é o primeiro ticket de tarefa **dentro** dessa fase.

### 2.3 Requisito e prova (já normados)

| ID | Formato | Função |
|----|---------|--------|
| **REQ** | `REQ-<BLOCO>-<NNN>` | Critério verificável |
| **PRF** | `PRF-<FASE>-<YYYYMMDD>-<SEQ3>` | Ficheiro JSON de prova |

### 2.4 Veredito (decisão — separado da solicitação)

| ID | Formato | Exemplo | Uso |
|----|---------|---------|-----|
| **DEC** | `DEC-<YYYYMMDD>-<SEQ3>` | `DEC-20260403-001` | Registo formal de decisão sobre **um** `TAR-*` |

**Estados permitidos para `veredito_tarefa`:** `APROVADO` | `REPROVADO` | `PENDENTE` | `NAO_AVALIADO` (apenas antes da auditoria).

---

## 3. Fluxo obrigatório (máquina de estados)

```text
SOL-*  →  TAR-*  →  (execução PSA)  →  PRF-* + REQ-*  →  DEC-* (veredito)
                ↘                     ↘
                  PENDENTE (gap de prova)    REPROVADO (prova FAIL ou critério não atingido)
```

1. Abrir **SOL-*** com descrição do pedido.  
2. Criar **TAR-*** ligado a **SOL-*** e à fase (`PH-FS-02`, …).  
3. Produzir **PRF-*** por requisito ou por checklist.  
4. Emitir **DEC-*** com `veredito_tarefa` **único** por **TAR-***.

**Proibido:** marcar `APROVADO` em **SOL-***; a solicitação **nunca** “aprova-se a si mesma”.

---

## 4. Instruções ao PSA (execução)

1. Para cada novo pedido do Conselho/CEO: criar **`SOL-YYYYMMDD-SEQ`** no registo (tabela §5 ou CSV §6).  
2. Decompor em **`TAR-FASE-SEQ`** conforme roteiro (`DOC-SCRIPT-EXEC-PSA-20260327`).  
3. Preencher **provas** com `psa_refutation_checklist.py --emit-template` e validar com `--validate`.  
4. Só após **`PRF-*` PASS** (ou **FAIL** documentado): preencher **`DEC-*`** com veredito.  
5. Arquivar: CSV + JSONs + linha no `PSA_RUN_LOG.jsonl` com `action": "decision_recorded"`.

---

## 5. Tabela modelo (copiar para cada ciclo)

| sol_id | tar_id | fase_roteiro | descricao_solicitacao | req_id | proof_id | veredito_tarefa | dec_id | git_head | ts_utc_decisao | responsavel |
|--------|--------|--------------|------------------------|--------|----------|-----------------|--------|----------|----------------|-------------|
| SOL-… | TAR-… | PH-FS-02 | (texto do pedido) | REQ-… | PRF-… | PENDENTE | | | | PSA |

**Preenchimento:**
- **veredito_tarefa = APROVADO:** exige **PRF-* com `veredito":"PASS"`** para todos os REQ críticos da linha (ou documento de excepção com **SOL** novo).  
- **REPROVADO:** pelo menos um **PRF-* `FAIL`** ou critério não cumprido; **dec_id** obrigatório.  
- **PENDENTE:** falta prova ou gap declarado; **não** usar APROVADO.

---

## 6. Ficheiro CSV gabarito (nome oficial)

**Ficheiro:** `MATRIZ_SOL_TAR_REQ_PRF_DEC.csv`  
**Local sugerido:** `04_relatorios_tarefa/templates_auditoria_psa/` (cópia de trabalho em `04_relatorios_tarefa/` quando em uso)

**Cabeçalho obrigatório:**

```csv
sol_id,tar_id,fase_roteiro,descricao_solicitacao,req_id,proof_id,veredito_tarefa,dec_id,git_head,ts_utc_decisao,responsavel,notas
```

*(O template vazio será gerado em ficheiro separado — ver §8.)*

---

## 7. Tarefa corrente (snapshot — actualizar ao mudar de fase)

| Campo | Valor |
|-------|--------|
| **Fase activa** | `PH-FS-02` |
| **Próximo `tar_id` sugerido** | `TAR-PHFS02-001` |
| **Próximo `sol_id` sugerido** | `SOL-20260403-002` *(ajustar SEQ ao último SOL usado)* |
| **Próximo `dec_id`** | `DEC-20260403-001` *(após primeira decisão formal deste ciclo)* |

*Os SEQ são **globais por prefixo por dia** ou **sequenciais no repositório** — escolher uma regra e **não** misturar.*

---

## 8. Entregáveis no repositório (lista para envio ao PSA)

| Ficheiro | Doc-ID / função |
|----------|-----------------|
| Este modelo | `DOC-OFC-MODELO-TAR-20260403` |
| `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` | Contexto |
| `DOCUMENTO_OFICIAL_PSA_PROVAS_E_AUDITORIA.md` | Provas REQ/PRF |
| `psa_refutation_checklist.py` | Validação JSON |
| `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` | Gabarito (criado abaixo) |

---

## 9. Proibições

- Usar **“aprovado”** na descrição de **SOL-***.  
- Fechar **TAR-*** como **APROVADO** sem **PRF-*** ou com **PRF** em falta.  
- Misturar **opinião** com **veredito** (só **APROVADO/REPROVADO/PENDENTE/NAO_AVALIADO**).

---

*Fim do modelo oficial — `DOC-OFC-MODELO-TAR-20260403` — revisões: bump de versão e entrada em `PSA_RUN_LOG.jsonl`.*
