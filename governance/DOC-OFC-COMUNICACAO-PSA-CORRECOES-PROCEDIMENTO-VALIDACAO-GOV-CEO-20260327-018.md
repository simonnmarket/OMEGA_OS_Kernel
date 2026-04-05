# Documento Oficial — Comunicação ao PSA: conclusão de correcções no índice + procedimento de validação automática

| Campo | Valor |
|--------|--------|
| **ID completo** | `DOC-OFC-COMUNICACAO-PSA-CORRECOES-PROCEDIMENTO-VALIDACAO-GOV-CEO-20260327-018` |
| **Referência curta** | **DOC-018** |
| **Versão** | 1.0 |
| **Data** | 27 de março de 2026 |
| **Emitido por** | Presidência / **CEO** (OMEGA) |
| **Destinatário** | Principal Solution Architect (**PSA**) + **Arquivo** |
| **Relação com DOC-017** | **Não** altera mandato, roteiro nem **§8** (congelamento). **Comunicação de transparência** + **SOP** técnico-documental. |

---

## 1. Finalidade

Informar o **PSA**, de forma **única e completa**, de:

1. **Que** correcções foram aplicadas ao **`governance/README.md`** e entradas relacionadas (para evitar referências a ficheiros inexistentes ou desalinhadas).  
2. **Que** novo **procedimento obrigatório** passa a existir para **padronização** antes de `git push` em documentação de governança.  
3. Que a equipa pode dar **sequência aos trabalhos de engenharia** (ex.: novo módulo de métricas/relatórios) **sem** reabrir o ciclo de encerramento institucional já formalizado no **DOC-017**.

---

## 2. Conclusão das correcções (o que foi corrigido e porquê)

| # | Assunto | Conclusão |
|---|---------|-----------|
| 1 | Nome do **DOC-008** no índice | Corrigida grafia **`ENVIO-IMEDIATO`** (existia **`ENVIO-IMEDIATE`**, incompatível com o nome real do ficheiro `.md`). |
| 2 | Redirecionamentos **013** e **014** | Tabela do README actualizada: passam a apontar explicitamente para **017** (antes ainda referiam **015**, desactualizado após unificação). |
| 3 | Linha «Fase 2 Fatia 2 (futuro)» | Removido placeholder entre backticks que **simulava** um `DOC-OFC-…` inexistente e **falhava** validação automática; substituído por texto sem ID fictício. |
| 4 | **Manifesto** de documentos | Criado **`governance/MANIFESTO_DOCUMENTOS.json`** — lista canónica dos `DOC-OFC-*.md` presentes em disco (regenerável). |
| 5 | Script de verificação | Criado **`scripts/verify_governance_refs.py`** — confirma que **cada** `DOC-OFC-…` citado no **README** existe como ficheiro. |

**Referência Git (pacote de padronização):** commit **`1ce69b5`** (`main`) — *script + manifesto + README*.

**Causa raiz (lição):** duplicação manual de **nomes de ficheiros** no índice; **mitigação:** validação automática + manifesto.

---

## 3. Novo procedimento (obrigatório para quem edita `governance/`)

**Quem:** Engenharia / CEO / PSA ao propor merge que altere ficheiros sob **`governance/`**.

**O quê:** Na **raiz do repositório**, antes de `git push`:

```text
python scripts/verify_governance_refs.py
```

- **Exit 0:** referências no README alinham com ficheiros existentes.  
- **Exit 1:** há referência a `DOC-OFC-…` **sem** `.md` correspondente — **corrigir antes do push**.

**Opcional** (após adicionar/remover documentos oficiais):

```text
python scripts/verify_governance_refs.py --write-manifest
```

Actualiza **`MANIFESTO_DOCUMENTOS.json`**.

**Avisos (não bloqueantes):** o script reporta **sufixos numéricos repetidos** (ex.: dois ficheiros `*-014.md`) — **dívida técnica** conhecida; não impede o passo de validação principal.

---

## 4. Ciência PSA

O PSA **toma conhecimento** destas correcções e do **procedimento** acima para **arquivo**, **auditoria** e **alinhamento** com o roteiro já mandatado no **DOC-017** (execução **008→011** inalterada).

**Nome / função PSA:** _____________________________________________  

**Data:** ____ / ____ / ______  

**Ref. arquivo:** _____________________________________________  

**Assinatura / registo:** _____________________________________________  

---

## 5. Declaração CEO (sequência de trabalhos)

**Autorizo** a prosseguir com **integração técnica** dos próximos módulos (ex.: métricas e relatórios sobre **`FIN_SENSE_DATA_MODULE`**) **após** o fluxo habitual de merge e testes, **sem** novo documento de **encerramento** FIN-SENSE **salvo** **§8** do **DOC-017**.

**Nome / função CEO:** _____________________________________________  

**Data:** ____ / ____ / ______  

**Assinatura:** _____________________________________________  

---

**Fim do documento `DOC-OFC-COMUNICACAO-PSA-CORRECOES-PROCEDIMENTO-VALIDACAO-GOV-CEO-20260327-018`.**
