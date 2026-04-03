Documento oficial — Mandato de execução PSA e encerramento do processo (CEO → PSA)

| Campo | Valor |
|--------|--------|
| **De** | CEO |
| **Para** | PSA (Núcleo de Validação) |
| **Assunto** | Responsabilidade de execução das verificações; encerramento da fase corrente |
| **Data** | 2026-03-27 |
| **Referência técnica** | `DOCUMENTO_OFC_CEO_FECHO_AUDITORIA_PSA.md` (mesma pasta) |
| **HEAD de referência (repositório `nebular-kuiper`)** | `8a3fbcb589ea1f65880208118cdc07d8f9272662` |

---

## 1. Decisão de governação: quem executa

**O PSA é sempre o órgão responsável por executar** a cadeia de verificação Tier-0 no repositório — isto é, correr os scripts, confirmar códigos de saída e registar o resultado em artefactos auditáveis. Não cabe inferir conformidade apenas a partir de narrativa, relatório intermédio ou “PASS” verbal sem **saída de comando reprodutível** e **manifesto alinhado ao disco e ao `HEAD`**.

A preparação de artefactos e a correcção de inconsistências (manifesto, templates, gate) podem ser feitas em colaboração; **a validação final objectiva é sempre obtida pela execução PSA** (ou sob controlo PSA) dos passos técnicos documentados.

---

## 2. Encerramento do processo (lado CEO)

Com base nos artefactos existentes e no documento de fecho técnico referenciado acima, **a fase corrente de auditoria preparatória e alinhamento de evidências é dada por encerrada do ponto de vista de entrega de pacote** ao PSA.

Isto significa:

- O CEO deixa de tratar como pendente a **lista de lacunas** identificadas anteriormente (manifesto desalinhado, ficheiro em falta, gate desatualizado), na medida em que foram **objecto de correcção e de verificação automática** conforme o outro documento.
- Qualquer **nova** alteração no repositório (commits, ficheiros listados no manifesto) obriga a **nova** execução da cadeia pelo PSA, antes de se declarar conformidade.

---

## 3. O que o PSA deve executar em cada ciclo (mínimo)

Na raiz do repositório `nebular-kuiper`, com `NEBULAR_KUIPER_ROOT` definido se aplicável:

1. **`python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head`**  
   Pasta de trabalho: `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo`  
   *Finalidade:* alinhar `git_commit_sha` e hashes a ficheiros em disco.

2. **`python verify_tier0_psa.py`** (mesma pasta `evidencia_pre_demo`)  
   *Critério:* código de saída **0** e resumo **ESTADO: OK**.

3. **`python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt`** (mesma pasta)  
   *Critério:* código **0** e **`GATE_GLOBAL: PASS`**.  
   *Se o relatório do gate for regravado:* repetir o passo 1 e o 2.

4. **Validação das provas PRF** (ficheiros indicados no pacote Fin Sense), por exemplo:  
   `python psa_refutation_checklist.py --validate <caminho/prova_PRF-….json>`  
   *Critério:* **PASS** por ficheiro.

O detalhe por ID de passo está em `DOCUMENTO_OFC_CEO_FECHO_AUDITORIA_PSA.md`.

---

## 4. Envio e arquivo

- **Este documento** serve de **carta de encerramento** e de **mandato de execução permanente** para o PSA.  
- **Anexo lógico obrigatório:** `DOCUMENTO_OFC_CEO_FECHO_AUDITORIA_PSA.md` (provas e passos).  
- O PSA deve arquivar ambos e associar ao **HEAD** (secção de cabeçalho) ou ao tag de release que homologar.

---

## 5. Declaração final

O CEO considera **concluída** a entrega do pacote de fecho e o reforço de que **a execução verificável das etapas acima é e continuará a ser responsabilidade do PSA** em todos os ciclos subsequentes.

**Fim do documento.**
