# Documento Oficial — Envio imediato ao PSA: pacote de homologação (ciclo FIN-SENSE)

| Campo | Valor |
|--------|--------|
| **ID completo** | `DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008` |
| **Referência curta** | `DOC-OFC-008` |
| **Versão** | 1.0 |
| **Data de emissão** | 27 de março de 2026 |
| **Classificação** | Operacional — **instruções executáveis** (envio ao PSA, verificação, rubrica, commit único) |
| **Repositório** | `OMEGA_OS_Kernel` — remoto `origin` → `https://github.com/simonnmarket/OMEGA_OS_Kernel.git` |
| **Branch** | `main` |
| **Tag de arquivo do ciclo** | `finsense-psa-cycle-20260404` |

---

## Finalidade

Este documento consolida **num único sítio** tudo o que o **PSA** deve receber, executar e arquivar para:

1. **Confirmar** que o repositório e os caminhos canónicos estão alinhados com a governança.  
2. **Rubricar** o encerramento institucional (**DOC-005**, secção 5).  
3. **Actualizar o índice** (`governance/README.md`) **uma única vez** com o **Anexo A** do **DOC-007**.  
4. **Publicar** o **único commit pós-rubrica** em `main`.

**Documento normativo principal (não substituído por este):**  
`DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` (**DOC-007**).

**Crítico (gap de governança sem rubrica):**  
`DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006` (**DOC-006**).

---

## O que o PSA deve receber (checklist de envio)

Marque ao enviar / ao confirmar recepção:

| # | Artefacto | Caminho no repositório |
|---|-----------|-------------------------|
| 1 | **Guia único (procedimento)** | `governance/DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007.md` |
| 2 | **Confirmação e rubrica** | `governance/DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md` |
| 3 | **Índice a actualizar após rubrica** | `governance/README.md` |
| 4 | **Este pacote de instruções** | `governance/DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008.md` |

**Nota:** A **Fase 2 / Fatia 1** (`DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412`) é **iniciativa técnica separada** — pode ser anexada como **contexto**, mas **não** é condição para a rubrica do ciclo **DOC-001–007**.

---

## Instruções — ordem exacta (PSA)

### Passo 1 — Clone actualizado e verificação remota

**PowerShell (Windows):**

```powershell
cd "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
git fetch origin
git checkout main
git pull origin main
git tag -l "finsense*"
git rev-parse HEAD
git remote -v
```

**Critérios esperados:**

- `origin` aponta para `https://github.com/simonnmarket/OMEGA_OS_Kernel.git`.  
- Existe a tag `finsense-psa-cycle-20260404` (local e, após fetch, visível no histórico remoto).  
- `main` está alinhado com `origin/main`.

### Passo 2 — Verificação física dos caminhos canónicos

Confirmar no workspace que existem (relativamente à raiz do repo):

| Caminho | Função |
|---------|--------|
| `modules/FIN_SENSE_DATA_MODULE/` | Código SSOT do pacote `fin_sense_data_module` |
| `FIN_SENSE_DATA/` | Hub de dados (dados e manifestos) |
| `governance/` | Documentos `DOC-OFC-*` oficiais |

Listagem rápida:

```powershell
Test-Path "modules\FIN_SENSE_DATA_MODULE"
Test-Path "FIN_SENSE_DATA"
Test-Path "governance"
dir governance\DOC-OFC-*20260404*.md
```

### Passo 3 — Rubrica humana (DOC-005)

1. Abrir: `governance/DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md`  
2. Preencher **secção 5** — tabela: marcar **Sim** nas **cinco** linhas; **nome / função PSA**; **data**; **identificador interno** (opcional).  
3. **Arquivar** evidência institucional (acta, ticket, sistema de compliance) e guardar **referência** para o Anexo A (README).

### Passo 4 — Actualização única do README (Anexo A do DOC-007)

1. Abrir: `governance/README.md`  
2. **Substituir apenas** o bloco do **topo** que ainda indica **PENDENTE** / **Pronto para rubrica** pelo texto do **Anexo A** abaixo, preenchendo `[DATA_AAAA-MM-DD]`, `[NOME_PSA]`, `[REF_TICKET_OU_ACTA]`.  
3. **Não** refazer a tabela de IDs (001–007) nem a secção Fase 2 salvo erro factual.

### Passo 5 — Commit único pós-rubrica

```powershell
git add governance/README.md governance/DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md
git commit -m "governance: homologacao PSA concluida (DOC-005 sec.5); README estado final; ref DOC-007"
git push origin main
```

*Se o DOC-005 preenchido **não** puder ser commitado por política interna:* commitar só o `README.md` e na mensagem ou no corpo do commit indicar: `rubrica arquivada em [REF]`.*

### Passo 6 — Confirmação de que o remoto está actualizado

```powershell
git log -1 --oneline
git status -sb
```

---

## Anexo A — Texto exacto para colar no `governance/README.md` (substitui o bloco PENDENTE)

Substituir as linhas do topo que descrevem homologação pendente / “Pronto para rubrica” por:

```markdown
**Homologação PSA:** **CONCLUÍDA** em [DATA_AAAA-MM-DD] — rubrica em `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005` secção 5. Responsável: [NOME_PSA]. Arquivo institucional: [REF_TICKET_OU_ACTA].

**Estado operacional:** **Homologado** ao nível institucional para o ciclo FIN-SENSE (governança + estrutura + Git). Gap de governança **fechado**.

**Transição:** ver secção "Fase 2" no `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` (DOC-007) para integração de alta performance (fora do âmbito da rubrica).
```

**Manter** as linhas sobre ciclo técnico-documental **ENCERRADO** e **Tag Git** `finsense-psa-cycle-20260404`, salvo correcção factual.

---

## O que significa “operacional” neste contexto

| Nível | Significado |
|--------|-------------|
| **Governança + Git + estrutura** | Com README actualizado (Anexo A) e DOC-005 rubricado, o **gap institucional** descrito no DOC-006 fica **fechado** para este ciclo. |
| **Produto / Fase 2 técnica** | Continua a seguir **contratos próprios** (ex.: `DOC-OFC-FASE2-FATIA1-…`, código, testes). **Não** é exigência desta rubrica. |

---

## Referência rápida — IDs do ciclo (001–007)

| ID | Ficheiro |
|----|----------|
| 001 | `DOC-OFC-VIOLACAO-REGRA-CEO-INTEGRACAO-FINSENSE-PSA-20260327-001.md` |
| 002 | `DOC-OFC-DESVIO-PADRAO-ESTRUTURAL-MODULES-FINSENSE-20260404-002.md` / `DOC-OFC-RESOLUCAO-REALINHAMENTO-FINSENSE-20260404-002.md` |
| 003 | `DOC-OFC-CIENCIA-ARQUIVO-HISTORICO-PSA-FINSENSE-20260404-003.md` |
| 004 | `DOC-OFC-ENCERRAMENTO-DEFINITIVO-CICLO-FINSENSE-PSA-20260404-004.md` |
| 005 | `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md` |
| 006 | `DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006.md` |
| 007 | `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007.md` |

---

## Encerramento

Com a execução dos passos 1–6 e o arquivo da evidência da rubrica, o PSA pode declarar **concluído** o **envio imediato** e a **homologação institucional** do ciclo FIN-SENSE ao abrigo deste pacote, sem necessidade de novos documentos intermédios.

**Fim do documento `DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008`.**
