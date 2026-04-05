# Documento Oficial — Registo de falha no índice (DOC-003), correção e medidas preventivas (PSA)

| Campo | Valor |
|--------|--------|
| **ID completo** | `DOC-OFC-REGISTO-FALHA-INDICE-DOC003-CORRECAO-PREVENTIVA-PSA-20260403-012` |
| **Referência curta** | `DOC-OFC-012` |
| **Versão** | 1.0 |
| **Data** | 3 de abril de 2026 |
| **Classificação** | **Registo obrigatório** — transparência institucional; **não** atribui culpa individual sem processo formal |
| **Destinatário** | PSA e revisores do índice `governance/README.md` |

---

## 1. Resumo executivo

Foi detectada e **corrigida** uma **falha factual** na **tabela de IDs** do ficheiro **`governance/README.md`**: o identificador do **DOC-003** foi escrito com erro ortográfico no token do nome de ficheiro (**`ARQUICO`** em vez de **`ARQUIVO`**), **desalinhado** do ficheiro real em disco.

Este tipo de erro **já ocorreu anteriormente** no projecto (padrão de **desvio entre índice e filesystem**). O presente documento **regista a falha**, **o motivo provável**, a **correcção** e **medidas para não repetir**.

---

## 2. Descrição da falha

| Campo | Detalhe |
|--------|---------|
| **Onde** | Tabela de documentos no **`governance/README.md`** (coluna ID, linha do DOC-003). |
| **Errado** | `DOC-OFC-CIENCIA-ARQUICO-HISTORICO-PSA-FINSENSE-20260404-003` |
| **Correcto** | `DOC-OFC-CIENCIA-ARQUIVO-HISTORICO-PSA-FINSENSE-20260404-003` |
| **Ficheiro real no repositório** | `governance/DOC-OFC-CIENCIA-ARQUIVO-HISTORICO-PSA-FINSENSE-20260404-003.md` |
| **Impacto** | Referência **incorrecta** no índice mestre; risco de **falha de auditoria** (cópia do ID para tickets, buscas, hiperligações); **não** altera o conteúdo do DOC-003 em si. |

---

## 3. Correcção aplicada (evidência Git)

| Campo | Valor |
|--------|--------|
| **Commit de correcção (referência)** | `21eae3d` — mensagem: *governance: README corrige ID DOC-003 (ARQUIVO); DOC-011 v1.1 bloco arquivo final* |
| **Branch** | `main` |
| **Estado** | Índice **alinhado** ao nome físico do ficheiro. |

*Nota:* se o histórico local divergir, usar `git log --oneline -- governance/README.md` para confirmar.

---

## 4. Análise de causa (motivo da falha)

| # | Causa provável | Explicação |
|---|----------------|------------|
| C1 | **Transcrição manual** | O ID na tabela foi **copiado ou reescrito** sem confronto directo com `dir` / listagem de ficheiros em `governance/`. |
| C2 | **Erro ortográfico num token composto** | Confusão fonética/visual **ARQUIVO** ↔ **ARQUICO** (inexistência de “ARQUICO” no português; erro de digitação). |
| C3 | **Ausência de verificação obrigatória pré-commit** | Não havia **checklist** nem **script** que exigisse: “cada ID na tabela = ficheiro existente no disco”. |
| C4 | **Padrão recorrente** | Não é a **primeira** vez que o índice documental diverge da verdade do repositório — indica **fragilidade de processo**, não um evento isolado. |

**O que não se infere sem investigação formal:** intenção negligente de um indivíduo nomeado. O registo foca **processo** e **controlo**.

---

## 5. Medidas correctivas (já aplicadas)

1. **Correção do ID** no `README.md` para coincidir com o nome de ficheiro real (**ARQUIVO**).  
2. **Publicação** em `main` com mensagem de commit explícita.

---

## 6. Medidas preventivas (obrigatórias para futuras edições do índice)

O **PSA** (ou revisor designado) deve **antes** de `git push` de qualquer alteração à tabela de IDs:

| # | Verificação |
|---|-------------|
| P1 | Listar ficheiros reais: `governance/DOC-OFC-*.md` (ou equivalente no SO). |
| P2 | Para **cada** linha nova ou alterada na tabela do `README`, confirmar que o **ID** corresponde **byte-a-byte** ao **nome do ficheiro** (sem o `.md` na coluna ID, conforme convenção do índice). |
| P3 | Procurar tokens frequentemente confundidos: **ARQUIVO**, **REALINHAMENTO**, datas **20260404**, etc. |
| P4 | Opcional (recomendado): script de validação — comparar IDs extraídos do README com `glob` de ficheiros (pode ser tarefa de engenharia **Fase 2**). |

---

## 7. Instrução ao PSA

1. **Arquivar** este **DOC-012** como prova de **governança de qualidade documental**.  
2. **Incorporar** as verificações **P1–P4** no **fluxo de revisão** de qualquer PR/commit que toque no **`governance/README.md`**.  
3. **Reconhecer** que desvios índice ↔ disco **minam a credibilidade** da trilha **DOC-001–011** junto de auditores externos.

---

## 8. Ciência e compromisso (PSA)

**Declaro ter tomado conhecimento do registo de falha, da correcção e das medidas preventivas.**

**Nome / função:** _____________________________________________  

**Data:** ____ / ____ / ______  

**Assinatura / registo interno:** _____________________________________________  

---

## Encerramento do Ciclo de Correção Preventiva

**Documento de Qualidade Governamental — Padrão OMEGA.**

---

**Fim do documento `DOC-OFC-REGISTO-FALHA-INDICE-DOC003-CORRECAO-PREVENTIVA-PSA-20260403-012`.**
