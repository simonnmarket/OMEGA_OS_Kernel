# Especificação técnica — prova de conclusão PSA (TIER-0)

**ID de pacote:** `DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414`  
**Script de orquestração:** `PSA_PROTOCOL_DEPLOY.ps1`  
**Versão SPEC:** 1.1.0  

---

## 0. Esclarecimento crítico — **três raízes diferentes** (evitar o erro anterior)

| Conceito | Significado | Exemplo típico (não universal) |
|----------|-------------|--------------------------------|
| **Árvore de auditoria PARR-F** (`PARRF_AUDIT_TREE_ROOT`) | Pasta que contém **`Conselho\`** e a zona de provas. Parâmetro `-ParrfRoot` do script. **Não** é, por si só, a “raiz do repositório da aplicação” nem a árvore de módulos em execução. | `...\nebular-kuiper\Auditoria PARR-F\` |
| **Raiz do repositório / aplicação** (`APP_REPO_ROOT`) | Onde o **vosso sistema** já definiu pastas de módulos, *build*, *runtime*. **Nunca** alterar por causa de auditoria. | Pode ser `...\nebular-kuiper\` (nível acima de `Auditoria PARR-F`) ou outro caminho **definido pelo vosso SSOT** |
| **Zona de provas efémeras** (`AUDIT_EVIDENCE_ZONE`) | **Única** área onde scripts PSA gravam *runs*. Pode ser apagada após análise. **Não** integra código no sistema principal. | `PARRF_AUDIT_TREE_ROOT\00_PROVAS_AUDITORIA\` |

**Erro que causou desintegração:** tratar `PARRF_AUDIT_TREE_ROOT` como se fosse a raiz de deploy da aplicação, ou gravar provas / rascunhos em pastas onde o **runtime** espera módulos — ficheiros ficaram **fora** do caminho de integração.

**Regra de ouro:** provas de auditoria **só** em `00_PROVAS_AUDITORIA\` (filho de `PARRF_AUDIT_TREE_ROOT`). Código e módulos **só** onde o projecto já documentou.

---

## 1. Objectivo normativo

Garantir que **nenhum artefacto** do pacote PSA seja gravado fora de **`PARRF_AUDIT_TREE_ROOT\00_PROVAS_AUDITORIA\`**, e que a **conclusão** só seja considerada **VÁLIDA** com **prova criptográfica** (SHA-256), **manifesto imutável** e **checklist binária** sem itens `PENDENTE`.

---

## 2. Hierarquia de pastas (única fonte de verdade operacional)

```
<PARRF_AUDIT_TREE_ROOT>\                    # pasta que contém Conselho (parâmetro -ParrfRoot)
├── Conselho\                               # CANÓNICO — documentos aprovados (leitura para o PSA)
│   ├── DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414.md
│   ├── GATES_NUMERICOS_V1.yaml
│   ├── ARBITRO_MULTITF_V1.py
│   └── AUDIT_JSON_SCHEMA_V1.0.json
├── 00_PROVAS_AUDITORIA\                    # ZONA EFÉMERA — provas geradas (pode apagar após arquivo)
│   └── PSA\<DOC_ID>\<RUN_ID>\
│       ├── MANIFEST.json
│       ├── MANIFEST.sha256
│       ├── mirror\
│       ├── logs\
│       ├── COMPLETION_PROOF.json
│       └── COMPLETION_PROOF.md
└── protocol\PSA\                           # scripts e SPEC (opcional nesta árvore)
```

**Proibições absolutas**

- **Não** gravar provas PSA em pastas de **módulos**, **src**, **lib**, **runtime**, ou qualquer caminho que o sistema principal use para **DEMO / LIVE**, salvo ordem escrita do Tech Lead com **ID** distinto.
- **Não** gravar em `Desktop`, `Downloads`, `temp` genérico.
- **Não** renomear ficheiros canónicos em `Conselho\` durante o *run* (apenas leitura + cópia para `mirror\`).

---

## 3. `MANIFEST.json` — schema lógico (campos obrigatórios)

| Campo | Tipo | Regra |
|--------|------|--------|
| `doc_id` | string | Const: `DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414` |
| `run_id` | string | Único global (ex.: `20260414T153045Z_a1b2c3d4`) |
| `utc_completed` | string | ISO-8601 UTC |
| `parrf_audit_tree_root` | string | Caminho absoluto de `PARRF_AUDIT_TREE_ROOT` (parâmetro `-ParrfRoot`) |
| `audit_evidence_zone` | string | Caminho absoluto de `...\00_PROVAS_AUDITORIA\` |
| `git_head` | string \| null | Saída de `git rev-parse HEAD` se `.git` existir; senão `null` com `git_head_note` |
| `files` | array | Cada elemento: `role`, `canonical_relative_path`, `mirror_relative_path`, `size_bytes`, `sha256` |
| `manifest_sha256` | string | SHA-256 do ficheiro `MANIFEST.json` **sem** este campo (opcional: calcular em duas passagens; o script grava primeiro e depois anexa `manifest_sha256` num ficheiro `MANIFEST.sha256` de uma linha) |

**Regra de integridade:** o verificador independente recalcula SHA-256 de cada ficheiro em `mirror\` e compara com `files[].sha256`. Qualquer divergência → **FALHA GRAVE**.

---

## 4. `COMPLETION_PROOF.json` — gates obrigatórios (todos `true`)

| Chave | Significado |
|--------|-------------|
| `gate_paths_within_audit_zone` | Todas as escritas ocorreram sob `PARRF_AUDIT_TREE_ROOT\00_PROVAS_AUDITORIA\` |
| `gate_four_files_present` | Quatro ficheiros existem em `mirror\` com tamanho > 0 |
| `gate_manifest_matches_mirror` | Hashes batem com `MANIFEST.json` |
| `gate_python_arbiter_selftest` | `python ARBITRO_MULTITF_V1.py` exit code 0 |
| `gate_json_schema_parseable` | `AUDIT_JSON_SCHEMA_V1.0.json` é JSON válido |
| `gate_yaml_parseable` | `GATES_NUMERICOS_V1.yaml` parseável (YAML 1.1) |
| `gate_completion_artifacts_present` | Existem `COMPLETION_PROOF.json` e `.md` e `logs\deploy.log` |

**Conclusão:** `outcome` ∈ { `"PASS"`, `"FAIL"` } — **PASS** só se **todas** as chaves `gate_*` forem `true`.

---

## 5. `COMPLETION_PROOF.md` — requisitos de apresentação humana

1. Cabeçalho com **DOC_ID**, **RUN_ID**, **operador** (conta Windows ou ID PSA), **hostname**, **UTC**.  
2. Tabela Markdown com cada `gate_*` e coluna **PASS/FAIL**.  
3. Bloco de código com os **quatro** SHA-256 (um por linha, formato `sha256  filename`).  
4. Referência ao caminho absoluto da pasta `...\00_PROVAS_AUDITORIA\PSA\<DOC_ID>\<RUN_ID>\`.  
5. Assinaturas de papel (opcional): PSA executor + verificador independente — ou assinatura PGP conforme política interna.

---

## 6. Procedimento de verificação independente (re-execução)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File PSA_PROTOCOL_DEPLOY.ps1 `
  -ParrfRoot "<OMEGA_PARRF_ROOT>" `
  -VerifyOnly `
  -RunId "<RUN_ID>"
```

**PASS** na verificação: todos os hashes recalculados iguais ao `MANIFEST.json` e todos os `gate_*` true no `COMPLETION_PROOF.json` existente (ou regenerado com mesmo conteúdo).

---

## 7. Entrega ao Conselho / arquivo

- **ZIP** (recomendado): raiz do ZIP = `<RUN_ID>\` com toda a subárvore `00_PROVAS_AUDITORIA\PSA\...`.  
- Nome sugerido: `EVIDENCE_PSA_<DOC_ID>_<RUN_ID>.zip`  
- **Não** incluir segredos (DSN, `.env`). Se logs contiverem dados sensíveis, **redigir** antes do ZIP.

---

**Fim da SPEC** — cumprir integralmente para aceitar a tarefa como concluída.
