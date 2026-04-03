# Documento oficial — Fecho de auditoria Tier-0 PSA (envio ao PSA)

| Campo | Valor |
|--------|--------|
| **Emitente** | CEO (mandato explícito) |
| **Destinatário** | PSA — Núcleo de Validação / Conselho |
| **Data do documento** | 2026-03-27 |
| **Repositório** | `nebular-kuiper` (raiz lógica de trabalho) |
| **HEAD Git (evidência de execução)** | `31e913c204817a94bc45b0fc1e8d71e6ce15e917` |

---

## 1. Resumo executivo

**Problema identificado (sessões anteriores):** Narrativa de “PASS” ou de conformidade PSA **não estava amarrada** a três provas objetivas ao mesmo tempo: (i) `verify_tier0_psa.py` com manifesto coerente com o disco e com `git rev-parse HEAD`; (ii) ficheiros listados no manifesto **existentes** com bytes e SHA3-256 coincidentes; (iii) `GATE_GLOBAL: PASS` no relatório do gate **após** alinhar o ficheiro `PSA_GATE_CONSELHO_ULTIMO.txt` ao manifesto. Situações concretas: `git_commit_sha` no manifesto desalinhado do HEAD; entrada no manifesto para `prova_TEMPLATE_PREENCHER.json` com **bytes 0** e hash vazio (omissão de artefacto); `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` com hash no manifesto **divergente** do ficheiro em disco; uso incorreto de `--out-relatorio` com caminho absoluto interno que gerou **cópia duplicada** do gate numa pasta aninhada (removida nesta sessão).

**O que foi feito agora:** Criação do ficheiro em falta, execução de `psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head`, regeneração do gate com caminho relativo correcto (`04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt`), segundo sync para incorporar o novo conteúdo do gate, validação das PRFs com `psa_refutation_checklist.py --validate`, e **verificação final** com `verify_tier0_psa.py` exit **0** e `psa_gate_conselho_tier0.py` com **GATE_GLOBAL: PASS**.

**Limitação explícita:** A palavra “fechado” aqui significa **fechado ao nível de evidência automática Tier-0 neste ambiente**, com os comandos abaixo e códigos de saída indicados. Qualquer ambiente que não contenha os mesmos bytes nos ficheiros do manifesto **não** pode reclamar PASS sem reexecutar a cadeia.

---

## 2. Classificação do que não estava comprovado (antes desta correção)

| ID | Natureza | Descrição |
|----|----------|-----------|
| **GAP-01** | **Falta de comprovação** | Manifesto com `git_commit_sha` ≠ `HEAD` do repositório → `verify_tier0_psa` falha no critério [1]. |
| **GAP-02** | **Omissão de artefacto** | `prova_TEMPLATE_PREENCHER.json` referido no manifesto mas inexistente no disco (ou entrada inválida com bytes 0). |
| **GAP-03** | **Desvio registo vs realidade** | `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` em disco não coincidia com bytes/SHA3 registados no manifesto. |
| **GAP-04** | **Risco de narrativa ≠ gate** | `PSA_GATE_CONSELHO_ULTIMO.txt` desatualizado em relação à última execução → possível `GATE_GLOBAL` em relatório antigo vs verificação actual. |
| **GAP-05** | **Erro operacional** | `--out-relatorio` com caminho que duplicou `evidencia_pre_demo` no caminho → ficheiro escrito fora do sítio esperado (corrigido: usar `04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt` relativo à pasta `evidencia_pre_demo`). |

*Não se classifica aqui “fraude” sem processo próprio; o quadro acima descreve apenas **falhas de comprovação e inconsistência artefacto/registo**.*

---

## 3. Plano executivo — passos, IDs e comprovação técnica

Cada passo deve ser **executado na raiz do repositório** `nebular-kuiper` (ou com `NEBULAR_KUIPER_ROOT` apontando para ela).

### STEP-01 — Criar template de prova em falta

| Campo | Conteúdo |
|--------|-----------|
| **ID** | STEP-01 |
| **Acção** | Garantir que existe `…/templates_auditoria_psa/prova_TEMPLATE_PREENCHER.json` com JSON válido segundo `PROVA_SCHEMA.json` (ficheiro modelo; `veredito` pode ser `FAIL` com `bloqueador` explicando que é template). |
| **Comprovação técnica** | Ficheiro presente no caminho: `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/templates_auditoria_psa/prova_TEMPLATE_PREENCHER.json`. |

### STEP-02 — Sincronizar manifesto com o disco e com o HEAD

| Campo | Conteúdo |
|--------|-----------|
| **ID** | STEP-02 |
| **Acção** | `python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head` |
| **CWD** | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo` |
| **Comprovação técnica** | Exit code **0**; saída inclui actualização de `git_commit_sha` e de entradas cujos bytes/SHA3 divergiam (ex.: `prova_TEMPLATE_PREENCHER.json`, `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv`). |

### STEP-03 — Verificação Tier-0 (bloqueador se falhar)

| Campo | Conteúdo |
|--------|-----------|
| **ID** | STEP-03 |
| **Acção** | `python verify_tier0_psa.py` |
| **CWD** | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo` |
| **Comprovação técnica** | Exit code **0**; linha final: `ESTADO: OK (Tier-0 verificação automática passou)`. |

### STEP-04 — Gate Conselho (métricas + verify embutido)

| Campo | Conteúdo |
|--------|-----------|
| **ID** | STEP-04 |
| **Acção** | `python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt` |
| **CWD** | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo` |
| **Comprovação técnica** | Exit code **0**; último bloco de resumo: `GATE_GLOBAL: PASS`. **Nota:** após gravar o relatório, o ficheiro `PSA_GATE_CONSELHO_ULTIMO.txt` muda de tamanho/hash → **repetir STEP-02** e **STEP-03** (ordem: sync → verify). |

### STEP-05 — Re-sincronizar após actualizar o relatório do gate

| Campo | Conteúdo |
|--------|-----------|
| **ID** | STEP-05 |
| **Acção** | Repetir STEP-02 (obrigatório se `PSA_GATE_CONSELHO_ULTIMO.txt` tiver sido reescrito). |
| **Comprovação técnica** | `verify_tier0_psa.py` exit **0** após o sync (manifesto inclui bytes **9095** e SHA3 actual do `PSA_GATE_CONSELHO_ULTIMO.txt` na execução registada). |

### STEP-06 — Validação das provas PRF (Fin Sense)

| Campo | Conteúdo |
|--------|-----------|
| **ID** | STEP-06 |
| **Acção** | Para cada ficheiro: `python psa_refutation_checklist.py --validate <caminho/prova_PRF-….json>` |
| **Comprovação técnica** | Exit **0** e linha `PASS proof file OK` para: `prova_PRF-PHFS02-20260403-001.json`, `prova_PRF-PHFS03-20260403-001.json`, `prova_PRF-PHFS04-20260403-001.json`. |

### STEP-07 — Verificação final do gate (sem regravar relatório)

| Campo | Conteúdo |
|--------|-----------|
| **ID** | STEP-07 |
| **Acção** | `python psa_gate_conselho_tier0.py` (sem `--out-relatorio`, para não alterar o ficheiro manifestado) |
| **Comprovação técnica** | Exit **0**; `GATE_GLOBAL: PASS`. |

---

## 4. Estado binário (para o PSA)

| Verificação | Critério | Resultado nesta sessão |
|-------------|----------|-------------------------|
| `verify_tier0_psa.py` | exit 0 | **PASS** |
| `psa_gate_conselho_tier0.py` | `GATE_GLOBAL: PASS` | **PASS** |
| PRFs PHFS02/03/04 | `psa_refutation_checklist.py --validate` | **PASS** (cada uma) |
| Manifesto | `git_commit_sha` = `git rev-parse HEAD` | **PASS** (`31e913c…`) |

---

## 5. Próximo passo obrigatório (governança Git)

Para que outro auditor reproduza **byte-a-byte** o mesmo manifesto em clone limpo, as alterações em `MANIFEST_RUN_20260329.json`, `prova_TEMPLATE_PREENCHER.json`, `PSA_GATE_CONSELHO_ULTIMO.txt`, e `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` devem ser **commitadas**; em seguida, se o `HEAD` mudar, executar **STEP-02** outra vez e confirmar **STEP-03** até exit 0.

---

## 6. Assinatura lógica do pacote

Este documento declara apenas o que foi **medido por comandos** acima. Omissões anteriores estão descritas na secção 2; a correcção operacional está nas secções 3–4.

**Fim do documento.**
