# Ordem oficial de execução — PSA | Núcleo de Validação OMEGA v1.1

| Campo | Valor |
|--------|--------|
| Documento | ORDEM_OFICIAL_EXECUCAO_PSA_NUCLEO_V1_1 |
| Versão | 1.0 |
| Data de emissão | 2026-03-27 |
| Emitido por | Engenharia / Governança OMEGA (Tech Lead) |
| Destinatário obrigatório | PSA (Principal Solution Architect) ou executor designado |
| Efeito | Execução **obrigatória**; conclusão apenas com **artefactos anexos** listados abaixo |

---

## 1. Finalidade

Esta ordem define **o que o PSA deve executar**, **como**, e **que ficheiros deve entregar**.  
A verificação pelo Conselho / Tech Lead limita-se a **conferir a existência e o conteúdo mínimo** desses artefactos — **não** a reexecutar trabalho interpretativo do PSA sobre o núcleo.

**Referências vinculativas:**

- Pasta de entrega: `Auditoria PARR-F/Núcleo de Validação OMEGA` (ou cópia homóloga acordada).
- `CHARTER_GOVERNANCA_PSA_ECOSISTEMA_TIER0.md` (Parte A — mandato Tier-0).
- `DEFINICOES_TECNICAS_OFICIAIS.md` — protocolo **OMEGA-DEFINICOES-v1.1.0**.
- `SCRIPT_INSTALACAO_E_DIRETRIZES_PSA.md` (mesma pasta do núcleo).

---

## 2. O que o PSA **não** precisa fazer nesta ordem

- Não alterar código do núcleo sem **ticket** e **revisão** prévios.
- Não declarar integração MT5, lucro ou produção — fora de âmbito.
- Não substituir esta ordem por relatório narrativo sem os artefactos da secção 4.

---

## 3. Execução obrigatória (sequência)

Executar na máquina ou VM **documentada** no relatório (SO, utilizador, caminho absoluto da pasta).

### 3.1. Ambiente

1. Python **3.10+** (registar versão exacta no artefacto A1).
2. Criar ambiente virtual **recomendado**; se não usar venv, declarar no A1.

### 3.2. Dependências

Na raiz da pasta do núcleo (onde existe `requirements.txt`):

```text
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3. Testes automatizados (critério duro)

```text
python -m pytest tests -v --tb=short
```

**Critério de aceitação:** linha final com **`15 passed`** (ou número actual indicado em `TECH_SPEC_OMEGA_CORE_VALIDATION.md` se futuramente alterado).  
**Qualquer falha, skip ou erro:** a ordem **não** se considera cumprida até nova execução com sucesso.

### 3.4. Congelamento de dependências (obrigatório)

```text
pip freeze > PSA_PIP_FREEZE_YYYYMMDD.txt
```

Substituir `YYYYMMDD` pela data UTC da execução.

---

## 4. Artefactos obrigatórios (entrega PSA)

Todos os ficheiros abaixo devem ser colocados **numa única pasta** (ex.: `PSA_ENTREGA_NUCLEO_YYYYMMDD/`) e enviados **zipados** ou via repositório acordado.

| ID | Nome sugerido | Conteúdo mínimo |
|----|----------------|-----------------|
| **A1** | `PSA_AMBIENTE_YYYYMMDD.txt` | Data/hora UTC; SO; caminho absoluto da pasta do núcleo; saída de `python --version`; indicação venv sim/não |
| **A2** | `PSA_PYTEST_LOG_YYYYMMDD.txt` | Output **completo** (copy-paste integral) de `python -m pytest tests -v --tb=short` |
| **A3** | `PSA_PIP_FREEZE_YYYYMMDD.txt` | Saída de `pip freeze` |
| **A4** | `PSA_DECLARACAO_CUMPRIMENTO_YYYYMMDD.md` ou `.txt` | Texto da secção 5, preenchido e assinado |

**Formato:** texto UTF-8; sem imagens no lugar de logs.

---

## 5. Declaração de cumprimento (modelo — PSA copia e preenche)

```
DECLARAÇÃO DE CUMPRIMENTO — ORDEM ORDEM_OFICIAL_EXECUCAO_PSA_NUCLEO_V1_1

Eu, _________________________________ (nome), na função de PSA / executor designado,
declaro que:

1. Executei os passos da secção 3 desta ordem na máquina documentada em A1.
2. Anexei os artefactos A1, A2, A3 e A4 completos e verídicos.
3. O pytest reportou sucesso conforme critério da secção 3.3.
4. Li o CHARTER_GOVERNANCA_PSA_ECOSISTEMA_TIER0.md (Parte A) e não ocultei placeholders
   nem omissões relativamente a esta execução.

Data UTC: ____/____/________  Assinatura: _______________________
```

---

## 6. Verificação pelo emitente (sem “re-auditoria” PSA)

Quem recebe a entrega **apenas** verifica:

| # | Verificação | Passa / Falha |
|---|-------------|----------------|
| V1 | Existem A1, A2, A3, A4 | |
| V2 | A2 contém `15 passed` (ou número oficial no TECH_SPEC) | |
| V3 | A2 não contém `FAILED`, `ERROR`, `warnings summary` com falhas de teste | |
| V4 | A1 identifica ambiente de forma a permitir reprodução opcional | |

Se V1–V4 passam, a **ordem de execução do núcleo** está **cumprida**.  
Questões de **integração MT5**, dados reais ou homologação comercial **não** fazem parte desta ordem.

---

## 7. Arquivamento

Guardar o ZIP ou pasta `PSA_ENTREGA_NUCLEO_*` no arquivo do projeto com a mesma data da declaração.

---

## 8. Assinatura do emitente (opcional, registo interno)

Emitente: _________________________  Data: ____/____/______

---

**Fim da ordem oficial v1.0**
