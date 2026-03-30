# Gate pré-stress — histórico completo (anti-fraude / anti-placeholder)

| ID | GATE-PRE-STRESS-20260331 |
|----|---------------------------|
| **Versão** | 1.0 |
| **Data** | 31 de março de 2026 |
| **Finalidade** | **Não autorizar** stress em histórico completo (2Y+ / 100% do RAW) até o Conselho/Tech Lead cumprir **esta** lista. Complementa DFG-OMEGA-20260331 e PAF-PSA. |
| **Contexto** | Entregas anteriores com **números não comprovados**, **placeholders** e **omissões** exigem barreira objetiva **antes** de consumir CPU e de dar validade a novos relatórios. |

---

## 1. Princípio

**Stress histórico completo** não é “mais um run”: vira **prova institucional**. Se a entrada estiver errada, truncada, ou o motor for a **cópia errada** do código, o resultado **parece** científico e **não** é.

Por isso: **nenhum pedido de stress completo** ao PSA sem **PASS** em **todos** os itens obrigatórios abaixo (ou **excepção escrita** do CEO com ID de risco).

---

## 2. Checklist obrigatória (Conselho / Tech Lead — executar ou delegar com anexo)

### A. Integridade e mentira por omissão

| # | Verificação | Evidência exigida | Falha = |
|---|-------------|-------------------|---------|
| A1 | `verify_tier0_psa.py` **ESTADO: OK** no commit que servirá de base ao stress | Output textual completo anexado ao ticket | Bloqueio |
| A2 | Manifesto JSON com **todos** os ficheiros de entrada do stress (RAW, versão de código) | `git_commit_sha` = `HEAD`; hashes bytes/SHA3 | Bloqueio |
| A3 | Procura por **placeholder** no pacote de stress | `rg "\[PLACEHOLDER|TODO|TBD|FIXME|XXX\]"` nos paths do job + resultado **0** ou listagem **explícita** aceite | Bloqueio se crítico não etiquetado |

### B. Motor único e código canónico

| # | Verificação | Evidência exigida | Falha = |
|---|-------------|-------------------|---------|
| B1 | **Uma** fonte canónica para `OnlineRLSEWMACausalZ` / RLS usada no stress | Diff ou nota: `Núcleo de Validação OMEGA` vs `omega_core_validation` — **declarar qual é a canónica**; se houver duas cópias, **hash** ou diff anexo | Bloqueio até clarificação |
| B2 | Script de stress/grid **não** usa *paths absolutos* hardcoded a máquina de um developer | Revisão de PR ou grep `C:\\Users` no script | Correção obrigatória |
| B3 | Comando de stress é **reprodutível** a partir de README ou RT | Um paragrafo: variáveis de ambiente, `NEBULAR_KUIPER_ROOT`, versão Python | Bloqueio |

### C. Números já reclamados (anti “segunda fraude”)

| # | Verificação | Evidência exigida | Falha = |
|---|-------------|-------------------|---------|
| C1 | Contagens `signal_fired` / RT-A **repetidas** por terceiro ou CI | Novo ficheiro `RT_A_EVIDENCIAS_AUTO_*.md` ou script com **mesmos** resultados nos **mesmos** hashes | Investigação |
| C2 | Tabela do **RT-B** (gridsearch) **reproduzida** | Ficheiro `GRIDSEARCH_*_RUN_*.txt` (stdout **integral**) + mesmo commit do script | Bloqueio até anexar |
| C3 | Definição explícita: “Sinais” = barras acima do limiar **vs** cruzamentos — **uma** definição por relatório | Parágrafo no RT-B ou addendum | Bloqueio se ambíguo |

### D. Dados históricos “completos”

| # | Verificação | Evidência exigida | Falha = |
|---|-------------|-------------------|---------|
| D1 | **Intervalo temporal** do RAW documentado (primeira/última barra ou `time` min/max) | Query pandas ou `head`/`tail` anexo | Bloqueio |
| D2 | Política de **truncagem**: se o stress completo usar **tudo**, declarar **N** linhas e **porquê** se N < total | Uma linha no RT de stress | Documentar |
| D3 | Merge XAU/XAG: **quantas** linhas perdidas, **duplicados** `time` | Contagem `len` antes/depois merge | Obrigatório no RT |

### E. Métricas (registry)

| # | Verificação | Evidência exigida | Falha = |
|---|-------------|-------------------|---------|
| E1 | `05_metrics_registry.csv` — toda métrica citada no relatório de stress tem **ID** e **Status** ≠ vazio enganoso | Revisão linha a linha | Bloqueio |
| E2 | Nenhuma métrica de PnL/PF apresentada **sem** coluna de PnL real ou simulada definida | — | Rejeitar métrica até definir |

---

## 3. Ordem sugerida (não negociável)

1. Fechar **A + B** (integridade + motor único).  
2. Fechar **C** (reprodução RT-B + stdout gridsearch).  
3. Só então **pedir** ao PSA: stress histórico completo com **RT de stress** que inclua **D + E**.

---

## 4. Texto curto para mandar ao PSA (quando o gate **não** estiver verde)

> O stress histórico completo **não** está autorizado até: (1) anexar stdout integral do `gridsearch_v105.py`; (2) eliminar paths absolutos e declarar motor canónico; (3) manifesto/verify OK para o commit do job; (4) zero placeholders críticos não etiquetados. Conforme GATE-PRE-STRESS-20260331.

---

## 5. Registo

| Campo | Valor |
|--------|--------|
| **Responsável pela verificação** | __________________ |
| **Data PASS** | __________________ |
| **Anexos (lista)** | __________________ |

**Fim do gate pré-stress.**
