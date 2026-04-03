Documento oficial — Blindagem e encerramento da etapa Tier-0 / FIN-SENSE MVP (PSA)

| Campo | Valor |
|--------|--------|
| **ID do documento** | `GOV-PSA-BLIND-20260327-001` |
| **Versão** | **1.0 FINAL** |
| **Data UTC** | 2026-03-27 |
| **Emitente** | Governança executiva (CEO) + Núcleo de Validação (PSA) — co-assinatura lógica |
| **Âmbito** | Encerramento blindado da etapa **pré-demo FIN-SENSE MVP** e mandato permanente de verificação |
| **SHA de referência homologável** | 405565eafd12bdadadaced9a50cc00b98ead0bb0 (ajustado ao commit atual) |
| **Documentos de governação vinculados** | `DOCUMENTO_OFICIAL_PSA_MANDATO_EXECUCAO_PERMANENTE_E_ENCERRAMENTO_CEO.md` (A); `DOCUMENTO_OFC_CEO_FECHO_AUDITORIA_PSA.md` (B) |

---

## 1. Finalidade

Este documento fixa **instruções executivas e verificáveis** para **blindar** (travar em evidência) e **finalizar** a presente etapa, sem deixar dependência de narrativa ou de “PASS” informal. Complementa os documentos A e B: **A e B definem o quê**; **este documento define o como fechar o ciclo** no repositório e no processo.

---

## 2. O que fica blindado ao concluir este checklist

- Mandato PSA de **execução exclusiva** da cadeia automatizada (sync → verify → gate → PRFs conforme B).
- Encerramento da fase **pré-demo FIN-SENSE MVP** ao nível de **governança de evidências** no repositório, desde que os comandos abaixo tenham **exit 0** no momento da homologação.
- Regra permanente: **nenhuma alteração** em ficheiros manifestados ou novo commit **sem** nova corrida da cadeia = **não** se declara conformidade.

---

## 3. Checklist obrigatório — executar na ordem (PSA ou operador designado)

**Diretório de trabalho dos scripts:**  
`Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo`  
**Raiz do repositório:** `nebular-kuiper` (variável `NEBULAR_KUIPER_ROOT` se necessário).

| # | Acção | Critério de sucesso |
|---|--------|---------------------|
| **BL-01** | Garantir que os documentos **A** e **B** e o presente ficheiro (`DOC_GOV_BLINDAGEM_ENCERRAMENTO_TIER0_PSA_20260327_FINAL.md`) existem na pasta `04_relatorios_tarefa/` e estão **commitados** no Git (ou prestes a ser no mesmo pacote de commit final desta etapa). | Ficheiros presentes e no controlo de versão. |
| **BL-02** | `python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head` | Exit **0**; `git_commit_sha` alinhado ao `git rev-parse HEAD`. |
| **BL-03** | `python verify_tier0_psa.py` | Exit **0**; linha **ESTADO: OK**. |
| **BL-04** | `python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt` | Exit **0**; **`GATE_GLOBAL: PASS`**. |
| **BL-05** | Se o passo **BL-04** regravou o gate: repetir **BL-02** e **BL-03** (obrigatório). | **verify** continua **OK** após sync. |
| **BL-06** | Validar PRFs Fin Sense: `python psa_refutation_checklist.py --validate` em cada `prova_PRF-PHFS0x-20260403-001.json` em `templates_auditoria_psa/` | Exit **0** e **PASS** por ficheiro. |
| **BL-07** | `python psa_gate_conselho_tier0.py` **sem** `--out-relatorio` | Exit **0**; **GATE_GLOBAL: PASS** (confirmação sem alterar ficheiro manifestado). |
| **BL-08** | **Push** do branch para o remoto acordado (se aplicável). | Histórico remoto = cópia do commit homologado. |
| **BL-09** | (Opcional e recomendado) Criar **tag** anotada no commit homologado, ex.: `psa-tier0-fecho-fin-sense-mvp-20260327`. | Tag aponta para o mesmo SHA que passou em **BL-03**. |

---

## 4. Alinhamento do SHA no cabeçalho deste documento

O valor **SHA de referência homologável** no quadro inicial deve coincidir com o output de:

```text
git rev-parse HEAD
```

no commit em que a homologação foi obtida (**BL-03** OK). **Depois de cada novo commit** que inclua alterações a ficheiros listados no manifesto ou a este documento: repetir **BL-02** → **BL-03** (e **BL-05** se o gate tiver sido regravado). Atualizar manualmente o quadro do **SHA** neste `.md` se o processo exigir leitura humana imediata; o **manifesto** é a fonte de verdade para bytes/SHA3 dos ficheiros.

---

## 5. Declaração de encerramento da etapa (para minuta interna)

Preencher quando **BL-01** a **BL-07** tiverem passado no mesmo estado de árvore Git:

- **Etapa blindada:** Pré-demo **FIN-SENSE MVP** (governança Tier-0 PSA) **encerrada** ao nível de evidência automatizada, com referência ao SHA: `________________` (copiar de `git rev-parse HEAD`).
- **Homologação PSA:** Rececção e homologação dos documentos **A** e **B** e adesão ao protocolo de execução — **registada**.
- **Próximas metas** (Alpha, sinais, HFT, submódulos): **fora do âmbito** deste ID; exigem novo pacote de requisitos e nova corrida de verificação quando aplicável.

---

## 6. Invalidação automática (sem novo processo formal)

A homologação desta etapa **deixa de ser invocável** como prova actual se:

- qualquer ficheiro listado no `MANIFEST_RUN_20260329.json` for alterado **sem** nova sequência **BL-02**–**BL-07** com exit 0; ou  
- o `git_commit_sha` do manifesto divergir do `HEAD` após commit; ou  
- se declarar “PASS” apenas por narrativa **sem** saídas de comando arquivadas.

---

## 7. Fim do documento

**ID:** `GOV-PSA-BLIND-20260327-001` · **Versão:** 1.0 FINAL  

*Única fonte de verdade operacional para “blindar” esta etapa: checklist **BL-01**–**BL-09** + documentos A e B.*
