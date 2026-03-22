# PSA — Briefing de Estado Atual & Fonte da Verdade Operacional

**Domínio**: SIMONNMARKET GROUP | **Projeto**: AURORA v8.0 | **Sistema**: OMEGA  
**Público-alvo**: PSA (Principal Solution Architect) — **uso obrigatório**  
**Tipo de documento**: **Living document** (deve ser atualizado a cada marco relevante)  
**Versão**: 1.2  
**Última atualização**: 2026-03-22 (UTC)  
**Responsável pela manutenção**: PSA + Tech Lead (CQO/CKO) — **PSA é dono do conteúdo técnico de execução**

> **Nota (cópia Cursor)**: O ficheiro **canónico** deve ser mantido em  
> `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Documentacao_Processo\PSA_BRIEFING_ESTADO_ATUAL.md`.  
> Após editar aqui, **copiar/commit** para o workspace `.gemini` para evitar divergência.

---

## 0. Fonte única de diretório (Tier-0) — **DECISÃO EXECUTIVA**

Para evitar conflitos de versão, hashes divergentes e “dois trabalhos paralelos”, o projeto adota **um único diretório canónico** para código, dados, outputs e documentação viva.

| Conceito | Valor |
|----------|--------|
| **Workspace oficial (fonte da verdade)** | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\` |
| **Pasta de auditoria PARR-F canónica** | `...\nebular-kuiper\Auditoria PARR-F\` |
| **Onde vive este `PSA_BRIEFING_ESTADO_ATUAL.md` (canónico)** | `...\Auditoria PARR-F\Documentacao_Processo\PSA_BRIEFING_ESTADO_ATUAL.md` |

**Regras obrigatórias**:

1. **Commits, stress tests, CSV/JSON, logs Camada 3 e edições do briefing** → apenas no workspace **`.gemini`** (caminho acima).
2. **`C:\Users\Lenovo\.cursor\nebular-kuiper\`** → **não** é segunda fonte de verdade; pode existir cópia de leitura ou rascunho, mas **não** deve ser atualizada em paralelo com conteúdo divergente. Ver ficheiro `FONTE_UNICA_WORKSPACE.md` na raiz dessa cópia.
3. Quem editar documentação no Cursor deve **sincronizar** (copiar/commit) para o repo sob **`.gemini`** ou trabalhar diretamente no repo oficial.
4. Qualquer relatório ao Conselho deve referenciar artefactos e hashes do path **canónico** (Secção 4).

**Estado do G-03**: **FECHADO** — decisão: **`.gemini` = única fonte da verdade**; `.cursor` = não manter como espelho ativo concorrente.

---

## 1. Propósito deste documento

Este arquivo existe **à parte** dos procedimentos (SOP, Checklist, Definições, Template, Protocolo de Auditoria) para cumprir um papel específico:

| Objetivo | Descrição |
|----------|-----------|
| **Fonte única de contexto** | O PSA sempre sabe *onde* está o código, *onde* estão os dados, *qual* é o estado da auditoria e *o que* falta. |
| **Separado dos procedimentos** | SOP/Checklist definem *como* fazer; **este documento** registra *o quê está feito agora* e *em que pasta*. |
| **Atualização contínua** | A cada stress test, correção de motor, nova homologação ou novo ativo, **este arquivo deve ser atualizado** no **diretório canónico** (Secção 0). |
| **Onboarding rápido** | Qualquer sessão futura (ou novo membro) lê **só este briefing** para alinhar com o trabalho real. |

**Regra**: Se algo mudou no repositório, nos outputs ou no motor de auditoria → **atualizar as Secções 4–6 e 9** deste documento no mesmo PR/commit (ou imediatamente após), **apenas no workspace canónico**.

---

## 2. Identidade do PSA no processo Tier-0

| Papel | Responsabilidade principal |
|-------|----------------------------|
| **PSA** | Executar stress tests, manter `psa_audit_engine.py`, garantir OHLCV/AMI alinhados, **executar Camada 3 (MT5/OHLCV)** quando exigido, corrigir gaps técnicos (ex.: métricas no `summary.json`). |
| **Tech Lead (IA)** | Documentação de processo, automação de Camadas 1–2 quando aplicável, consistência entre relatórios — **sem** substituir validação física no MT5. |
| **CFO / Conselho** | Homologação, auditoria independente, decisões de Demo/Live. |

**Local técnico (único)**:

| Função | Caminho |
|--------|---------|
| Código (`psa_audit_engine.py`), AMI, OHLCV, `outputs/`, `logs/`, **este briefing** | Workspace canónico — Secção 0 |
| Cópia em `.cursor` | Apenas referência; **não** duplicar atualizações concorrentes |

**Regra operacional**: Paths absolutos em scripts devem apontar para o disco/projeto canónico; alterações de máquina atualizam a Secção 0.

---

## 3. Estado do projeto (snapshot — 2026-03-22)

| Item | Estado |
|------|--------|
| **Demo Fase 0** | Pausada por decisão de governança (padronização antes de escalar). |
| **Documentação Tier-0 (5 docs)** | Criada e submetida à homologação; CFO recomendou homologação após Fase 2. |
| **Fase 2 (validação retrospectiva XAUUSD)** | **Concluída** com Camadas 1, 2 e **3** (Camada 3 validada pelo PSA no MT5/OHLCV). |
| **Motor de auditoria** | `psa_audit_engine.py` **v3.1_OHLCV_G01** — OHLCV-driven, bugs v2.0 corrigidos; **G-01** (Sharpe/Sortino/Calmar na equity no `summary.json`) homologado no marco 2026-03-22. |
| **Diretório único** | **`.gemini\...\nebular-kuiper`** — ver Secção 0. |

---

## 4. Resultados consolidados — XAUUSD (Stress Test v3.1_OHLCV_G01)

**Localização dos artefactos**: `Auditoria PARR-F\outputs\` **no workspace canónico** (Secção 0).

| Métrica | Valor referência (Dossiê Final 2026-03-22) | Observação |
|---------|------------------------------------------|------------|
| Total de trades | **88.049** | Base factual para transição Demo; critério ≥100k foi substituído por robustez + integridade (decisão Tier-0 documentada). |
| Winrate | **63,76%** | Conforme `stress_test_summary_XAUUSD.json` v3.1. |
| Sharpe (equity) | **-1,2172** | Ratios negativos documentados no Dossiê — ver interpretação trade-level vs benchmark anual (`DOSSIE_FINAL_HOMOLOGACAO_XAUUSD_20260322.md`). |
| Max drawdown | **1,4668%** | Sobre curva de equity conforme definições. |
| Total PnL (summary) | Conforme `stress_test_summary_XAUUSD.json` | **Verificar sempre o ficheiro** no path canónico. |
| Hashes SHA3-256 (summary) | `trades_csv`, `equity_csv` no JSON | Recalcular localmente após qualquer re-run **no workspace oficial**. |

**Hashes de referência (última execução validada — verificar no JSON canónico)**:

- `trades_XAUUSD.csv`: prefixo `7c4cd6ca...` (SHA3-256 completo no `stress_test_summary_XAUUSD.json`)
- `equity_curve_XAUUSD.csv`: prefixo `32e7701a...`
- `stress_test_summary_XAUUSD.json`: hash próprio se existir em anexo ao relatório

**Artefatos obrigatórios (nomes canónicos)**:

- `outputs/trades_XAUUSD.csv`
- `outputs/equity_curve_XAUUSD.csv`
- `outputs/stress_test_summary_XAUUSD.json`
- Opcional: `*.sha3` lado a lado, se o processo os gerar.

**Script fonte (canónico)**:

- `psa_audit_engine.py` na raiz do projeto `nebular-kuiper` **no workspace canónico**.

---

## 5. Auditoria em 3 camadas — status (XAUUSD)

| Camada | Conteúdo | Status (2026-03-22) | Responsável |
|--------|----------|---------------------|-------------|
| **1 — Técnica** | Hashes, colunas, JSON, IDs únicos, timestamps | Aprovada com ressalvas (ex.: Git no workspace certo) | Tech Lead / scripts |
| **2 — Estatística** | Winrate, DD, Sharpe/Sortino/Calmar (equity), consistência trades vs summary | **Aprovada** — métricas G-01 presentes no `summary.json` v3.1 | Tech Lead + CFO |
| **3 — Física** | 10 trades vs candles MT5/OHLCV | **Aprovada (10/10)** — PSA | **PSA** |

**Artefatos Camada 3 (referência)**:

- `logs/audit_layer3_XAUUSD_PSA.md` (ou equivalente no repo canónico)
- `logs/audit_layer3_sample_XAUUSD.csv`
- Checklist preenchido conforme `PROTOCOLO_AUDITORIA_INDEPENDENTE.md`

---

## 6. Gaps abertos e ações PSA (prioridade)

| ID | Gap | Severidade | Ação PSA / dono | Estado |
|----|-----|------------|-----------------|--------|
| **G-01** | Sharpe / Sortino / Calmar no `stress_test_summary_*.json` (equity) | Média | Motor **v3.1_OHLCV_G01**; blindagem `np.errstate` no cálculo. | **Fechado (2026-03-22)** |
| **G-02** | Rastreio Git / commit vs workspace | Baixa | SHA registado na Secção 9 (commit **939ffc1** — verificar no clone oficial). | **Fechado (2026-03-22)** |
| **G-03** | Duplicação .cursor vs .gemini | — | **FECHADO**: uma única fonte — Secção 0. | **Fechado (2026-03-22)** |

**Critério de encerramento G-01**: cumprido com `summary.json` v3.1 e Dossiê Final.

**Próximos passos PSA (prioridade)**:

1. **Demo / AMI**: Calibragem e validação operacional conforme roadmap (fora do âmbito deste briefing).
2. **Manutenção**: Após cada stress test ou novo ativo, atualizar **Secções 4–6 e 9** **somente** no ficheiro canónico (Secção 0).
3. Novos ativos: replicar processo Tier-0 (SOP + 3 camadas).

---

## 7. Documentos oficiais (referência cruzada)

**Caminho**: `Auditoria PARR-F\Documentacao_Processo\` no **workspace canónico**.

| # | Documento | Função |
|---|-----------|--------|
| **0** | **`INSTRUCOES_PSA_TIER0_COMPLETAS.md`** | **Instruções objetivas únicas** (paths, ordem de trabalho, gaps, proibições). |
| 1 | `SOP_VALIDACAO_ATIVO.md` | Processo por ativo |
| 2 | `CHECKLIST_VALIDACAO_OBRIGATORIA.md` | 50 itens |
| 3 | `DEFINICOES_TECNICAS_OFICIAIS.md` | Verdade matemática |
| 4 | `TEMPLATE_RELATORIO_ATIVO.md` | Relatório ao Conselho |
| 5 | `PROTOCOLO_AUDITORIA_INDEPENDENTE.md` | 3 camadas |

**Relatórios de projeto (contexto)** — mesma árvore canónica:

- `RELATORIO_FASE2_VALIDACAO_RETROSPECTIVA.md`
- `HOMOLOGACAO_DOCUMENTOS_TIER0.md`
- `DOCUMENTO_FINAL_CONSELHO_V3_APROVACAO.md`
- **`DOSSIE_FINAL_HOMOLOGACAO_XAUUSD_20260322.md`** — Dossiê Final de Homologação (XAUUSD, v3.1, Anexo A reconciliação)

---

## 8. Checklist de atualização (PSA — usar a cada mudança)

- [ ] Editar **apenas** a cópia canónica deste ficheiro (Secção 0).
- [ ] Atualizar **Secção 4** (métricas e hashes) após novo stress test.
- [ ] Atualizar **Secção 5** se mudar status de qualquer camada.
- [ ] Atualizar **Secção 6** ao fechar ou abrir gaps.
- [ ] Registrar **versão do motor** (`psa_audit_engine` vX.Y) e **data do último run**.
- [ ] Se mudar símbolo (ex. GBPUSD), adicionar subsecção “Estado — {SYMBOL}” mantendo histórico do XAUUSD.
- [ ] **Não** manter segundo ficheiro “oficial” em `.cursor` com conteúdo divergente.

---

## 9. Histórico de versões deste briefing

| Versão | Data | Autor | Alteração resumida |
|--------|------|-------|--------------------|
| 1.0 | 2026-03-22 | Tech Lead + alinhamento PSA | Criação: estado pós-Fase 2, Camada 3 PSA, gaps G-01–G-03, workspaces. |
| 1.1 | 2026-03-22 | Tech Lead + decisão projeto | **Diretório único**: `.gemini` = fonte da verdade; G-03 fechado; regras anti-conflito; hashes em Secção 4. |
| 1.2 | 2026-03-22 | PSA + CRO/CTO (marco homologação) | Motor **v3.1_OHLCV_G01**; G-01/G-02 **fechados**; métricas v3.1 no resumo; commit **939ffc1**; referência `DOSSIE_FINAL_HOMOLOGACAO_XAUUSD_20260322.md`. |

**Git / commit canónico (G-02)** — confirmar no clone oficial:

| Campo | Valor |
|-------|--------|
| Repositório | _(nome do repo interno)_ |
| Branch | _(ex.: main)_ |
| Commit SHA | **939ffc1** (prefixo; SHA completo no `git log`) |
| Data verificação | 2026-03-22 |

---

## 10. Assinatura de leitura (opcional, governança)

| Função | Nome | Data | Confirmo leitura |
|--------|------|------|------------------|
| PSA | _________________ | ____/____/______ | [ ] |
| Tech Lead | _________________ | ____/____/______ | [ ] |

---

**Fim do documento — `PSA_BRIEFING_ESTADO_ATUAL.md`**

*Transparência > Perfeição. Integridade > Velocidade. Qualidade > Quantidade.*
