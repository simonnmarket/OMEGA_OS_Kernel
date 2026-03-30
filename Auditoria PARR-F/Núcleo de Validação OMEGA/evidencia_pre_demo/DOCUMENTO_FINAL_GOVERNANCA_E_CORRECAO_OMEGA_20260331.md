# Documento final — Governança, correção OMEGA V10.4 e protocolo anti-fraude  
**Versão consolidada alinhada ao Conselho (CKO + COO atualizados)**  

| Campo | Valor |
|--------|--------|
| **ID** | DFG-OMEGA-20260331 |
| **Versão** | 1.1 |
| **Data** | 31 de março de 2026 |
| **Alteração v1.1** | Inclusão obrigatória do **Gate pré-stress** (histórico completo) — ver Parte IX. |
| **Status** | Mandatório para PSA, Tech Lead e auditoria |
| **Base legal interna** | ATF-OMEGA-V10.4-20260330 · RCV-OMEGA-20260330 · PAF-PSA-20260330 · **PAF-PSA v1.1 (COO)** · **Parecer CKO / Red Team** |

---

## Parte I — Leitura dos documentos do Conselho (atualizados)

### I.1 CKO / Red Team (`CKO - Red Team.txt`)

| Ponto | Conteúdo | Posição integrada neste documento |
|--------|-----------|-------------------------------------|
| **Veredicto** | PAF-PSA-20260330 é defesa necessária contra fraude técnica e narrativa sem evidência; **aprovado para implementação imediata**. | Adotado. |
| **Hierarquia de verdade** | Código/output prevalece sobre relatório (“se o código diz que não entrou, o relatório de excelência é nulo”). | Reforçado na Parte III. |
| **Stress do protocolo** | (1) Risco de burocracia — RT por subtarefa pode atrasar; (2) Métrica com fórmula “certa” mas implementação errada (ex. Sharpe); (3) Placeholder explícito que nunca expira. | Parte IV (mitigações e lacunas). |
| **Recomendações CKO** | Sanções mais duras: **rollback de commit / branch** em caso de fraude técnica comprovada; validação cruzada de métricas (dois métodos); CI que **falha** se placeholder existir após data. | Parte IV e secção **Lacunas de implementação**. |
| **Ligação V10.5** | Bateria de testes (incl. sensibilidade λ) para não repetir cegueira. | Parte V. |
| **Mandato imediato** | **Antes de qualquer código V10.5:** completar **RT-A (Fase A — Custódia)** com inventário, `verify_tier0_psa.py` sem erros, assinatura na declaração; **sem RT-A assinado, nenhum commit V10.5 aceito**. | Parte V, tarefa bloqueante. |

### I.2 COO — Protocolo Anti-Fraude PSA v1.1 (`COO - Chief Operating Officer.txt`)

| Ponto | Conteúdo | Nota de integração |
|--------|-----------|---------------------|
| **ID** | PAF-PSA-20260331-v1.1 | Coexiste com PAF-PSA-20260330; **v1.1 é a revisão operacional aprovada pelo COO** (31/03/2026). |
| **Novidades v1.1** | Linguagem executável; **schema RT fixo**; **metrics_registry.csv**; placeholder com formato `[PLACEHOLDER:owner:YYYY-MM-DD:critério]`; checklist auto-aprovável; scripts referenciados (`rt_validator.py`, `placeholder_expiry.py`, `checklist_validator.py`). | Ver **Parte IV — Lacunas**: vários itens são **especificação alvo**; nem todos existem no repositório à data deste documento. |
| **Princípios** | Número crítico com hash da fonte; métrica nova só com linha no registry; sem avanço de fase sem RT anterior; divergência narrativa vs ficheiro = incidente bloqueante. | Adotado integralmente. |
| **Pipeline** | Fases A–E com gates (Custódia → Histórico → Parâmetros → QA → Demo). | Igual ao RCV; mantido. |
| **Memorando Conselho** | Próximos passos: PSA inicia Fase A sob v1.1; primeiro RT em 48h (referência COO). | Ajustar datas ao plano real; mandato RT-A permanece prioritário. |

---

## Parte II — Síntese técnica estável (auditoria + convergência)

### II.1 Achados quantitativos (stress 2Y nos artefactos medidos)

Nos CSVs em `evidencia_pre_demo/02_logs_execucao/` (**100k linhas por perfil**), as contagens de `signal_fired` True foram **402 / 197 / 375** (SWING / DAY / SCALPING), **coincidindo** com `|z| ≥ 3.75`. Isto **contradiz** relatórios que alegam **zero** sinais nos **mesmos** ficheiros — exige **reconciliação de custódia** (RT-A).

### II.2 Causa raiz consensual (desenho, não “motor MT5”)

- Desalinhamento plausível entre **λ (RLS)**, **`ewma_span`** e **limiar |Z|** face ao regime de trading pretendido.  
- **Tier-0** (integridade, hash) **≠** validação de edge ou volumetria.  
- **Cegueira noturna / parâmetros distorcidos:** metáfora aceite — calibração sem âncora em histórico longo e métricas acordadas.

### II.3 Direção de correção

- Histórico **≥ 2 anos** versionado; grelhas de λ, span e Z₀; QA mandatório; demo só após gates.  
- Nenhuma homologação baseada só em “0 exceções” ou drawdown 0 sem interpretação de **silêncio de sinais**.

---

## Parte III — Princípios não negociáveis (fusão PAF 20260330 + PAF v1.1 + CKO)

1. **Hierarquia de verdade:** código executável + ficheiros + outputs de comando **prevalecem** sobre narrativa e slides.  
2. **Número comprovado:** toda métrica crítica liga-se a ficheiro (e idealmente hash) e a script ou comando reprodutível.  
3. **Métrica admitida:** entrada em **`05_metrics_registry.csv`** (v1.1) com ID único, fórmula, script, teste — **antes** do primeiro uso em relatório oficial.  
4. **Relatório de tarefa (RT):** obrigatório **ao fim de cada tarefa**; **RT-A (Custódia)** é **pré-requisito** antes de commits V10.5 (mandato CKO).  
5. **Placeholder:** apenas formato **`[PLACEHOLDER:owner:YYYY-MM-DD:critério]`** (v1.1); proibido em campos numéricos críticos; expiração acionável (ver Parte IV).  
6. **Incidente bloqueante:** qualquer divergência documentada entre relatório e disco **antes** de nova comunicação externa.

---

## Parte IV — Schema de RT, registry e automação

### IV.1 Nome e local dos RTs

- **COO v1.1:** `RT_<FASE>_<TASKID>_<YYYYMMDD>.md` (ex.: `RT_A_001_20260331.md`).  
- **PAF 20260330:** `RT_PSA_<FASE>_<TAREFA_ID>_<YYYYMMDD>.md`.  

**Regra única para o repo:** usar **um** padrão por deliberação do Tech Lead; até lá, **aceitar ambos** desde que a pasta seja `evidencia_pre_demo/04_relatorios_tarefa/`.

### IV.2 Conteúdo mínimo do RT (schema unificado)

1. Identificação (tarefa, responsável, datas, commits inicial/final).  
2. Comandos executados e outputs **completos** (ou anexo `.txt` referenciado).  
3. Tabela de evidências: ficheiro, bytes, SHA3-256, propósito.  
4. Números críticos com **Metric ID** (M001, …) apontando para o registry.  
5. Checklist de conformidade (hash, registry, verify, trades > 0 quando aplicável).  
6. Declaração de conformidade assinada.  
7. Gate: APROVADO / BLOQUEADO para próxima fase.

### IV.3 `05_metrics_registry.csv` (novo artefacto obrigatório v1.1)

Colunas mínimas: `ID`, `Nome`, `Fórmula`, `Script`, `Unidade`, `Teste`, `Status`.  
Exemplos piloto no COO (M001–M003) devem ser **copiados** para o primeiro ficheiro real e **estendidos** quando novas métricas forem usadas.

### IV.4 Lacunas de implementação (transparência obrigatória)

O COO v1.1 referencia mecanismos que **podem ainda não existir** no repositório. Até implementação:

| Item especificado v1.1 | Estado típico no repo | Mitigação imediata |
|-------------------------|-------------------------|---------------------|
| `python verify_tier0_psa.py --manifesto …` | O script actual **não** aceita `--manifesto`; usa `MANIFEST_RUN_20260329.json` fixo. | Executar `python verify_tier0_psa.py` sem flags; alinhar manifesto ao `HEAD`; documentar no RT-A. |
| `rt_validator.py` | Pode não existir. | Checklist **manual** conforme secção IV.2 até script existir. |
| `placeholder_expiry.py` | Pode não existir. | grep/CI manual por `[PLACEHOLDER:` e datas; CKO pede CI — abrir tarefa de implementação. |
| `manifesto_atual.json` vs `MANIFEST_RUN_*.json` | Nome canónico variável. | Uma entrada no RT-A define o **nome oficial** do manifesto da sprint. |

**Regra:** ausência de automação **não** suspende o protocolo; **aumenta** a responsabilidade de revisão humana e a exigência de anexos completos no RT.

### IV.5 Endurecimento CKO (sanções)

Para alinhar ao Red Team:

- Proposta: em caso de **fraude técnica** (número contradito por ficheiro anexo no mesmo RT): **reverter** commit associado, **bloquear** *merge* até RT corrigido — processo a formalizar com gestão de repositório.  
- Proposta: métricas de alto risco (ex. Sharpe): **validação cruzada** (segundo método ou biblioteca) registada no RT.

---

## Parte V — Plano de execução unificado (ordem CKO + fases COO)

| Ordem | Entrega | Gate |
|-------|---------|------|
| **0** | Ler DFG-OMEGA + PAF v1.1 + CKO | — |
| **1** | **RT-A (Custódia)** — inventário artefactos V10.4; `verify_tier0_psa.py` OK; reconciliar contagem `signal_fired` vs alegações “zero”; lista de ficheiros “mortos” ou substituídos; assinatura | **BLOQUEIO** em commits V10.5 até aprovado (CKO) |
| **2** | RT-B — dataset 2Y+; hashes; nota de merge | verify + registry |
| **3** | RT-C — grelas λ / Z / span; escolha documentada | métricas + sensibilidade |
| **4** | RT-D — QA (`audit_trade_count`, percentis Z, etc.) | checklist PASS |
| **5** | RT-E — Demo; paridade com backtest | logs + conclusão |
| **6** | Relatório pós-correção — bateria de testes (ATF/RCV secção 8 + PAF secção 8) | descobrir o que ainda estava incoberto |
| **7** | **Gate pré-stress (histórico completo)** — checklist **GATE-PRE-STRESS-20260331** com PASS documentado **antes** de autorizar stress longo | ver **Parte IX**; **bloqueante** face a risco de fraude técnica / placeholders |

---

## Parte VI — Declaração de vigência

1. **PAF-PSA-20260330** permanece válido como fundamento; **PAF-PSA v1.1 (COO)** é a **revisão operacional** com schema, registry e placeholders endurecidos.  
2. O **parecer CKO** é incorporado como **mandato de pré-requisito (RT-A)** e **recomendações de sanção e validação cruzada**.  
3. Este **DFG-OMEGA-20260331** é o **único ponto de entrada** para o Conselho e o PSA nesta fase, até nova versão numerada.  
4. A **Parte IX** (gate pré-stress) é **vinculante** para autorização de stress em histórico completo.

---

## Parte VII — Anexos lógicos (ficheiros no repositório)

| Documento | Caminho relativo (sugerido) |
|-----------|-----------------------------|
| Auditoria técnica forense V10.4 | `evidencia_pre_demo/AUDITORIA_TECNICA_FORENSE_OMEGA_V10_4_20260330.md` |
| Relatório de convergência | `evidencia_pre_demo/RELATORIO_CONVERGENCIA_RESOLUCAO_OMEGA_V10_4_20260330.md` |
| Protocolo anti-fraude (PAF original) | `evidencia_pre_demo/PROTOCOLO_ANTI_FRAUDE_PSA_FASE_CORRECAO_20260330.md` |
| Verificador Tier-0 | `evidencia_pre_demo/verify_tier0_psa.py` |
| Pareceres Conselho | `Auditoria PARR-F/Auditoria Conselho/CKO - Red Team.txt`, `COO - Chief Operating Officer.txt` |
| RTs | `evidencia_pre_demo/04_relatorios_tarefa/` |
| Gate pré-stress (histórico completo) | `evidencia_pre_demo/GATE_PRE_STRESS_HISTORICO_COMPLETO_20260331.md` |

---

## Parte VIII — Próximo passo obrigatório (síntese CKO)

**Preencher e assinar RT-A (Fase A — Custódia)** antes de qualquer implementação V10.5.

Incluir:

- Inventário de artefactos e versões.  
- Output de `python verify_tier0_psa.py` (cópia integral).  
- Tabela de métricas iniciais no `05_metrics_registry.csv` (criar ficheiro se ainda não existir).  
- Declaração de conformidade (schema §IV.2).

**Após RT-A e Fases B–D conforme pipeline:** antes de autorizar **stress em histórico completo**, cumprir **Parte IX** e o ficheiro **GATE_PRE_STRESS_HISTORICO_COMPLETO_20260331.md**.

---

## Parte IX — Gate pré-stress (histórico completo)

Antecedente: entregas com **números não comprovados**, **placeholders** ou **omissões** implicam que **stress em histórico completo** não pode ser autorizado só por pedido verbal.

**Obrigatório:** o Conselho / Tech Lead cumpre integralmente o documento:

`evidencia_pre_demo/GATE_PRE_STRESS_HISTORICO_COMPLETO_20260331.md` (**ID: GATE-PRE-STRESS-20260331**)

até obter **PASS** em todos os itens obrigatórios (integridade `verify_tier0_psa.py`, manifesto, caça a placeholders, motor canónico, **stdout integral** do gridsearch, definição de métricas, cobertura e merge dos RAW, registry alinhado).

**Regra:** Nenhum pedido de **stress MP / histórico completo** ao PSA sem **registo datado** de que o gate pré-stress foi verificado (responsável + anexos listados no próprio ficheiro GATE).

---

**Fim do documento DFG-OMEGA-20260331 (v1.1)**

*Documento gerado para consolidar auditoria independente, relatório de convergência, protocolos anti-fraude e atualizações formais do Conselho (CKO + COO v1.1), com lacunas de implementação explicitadas para evitar falsa sensação de automação completa. A v1.1 incorpora o gate pré-stress obrigatório face a risco de fraude técnica e placeholders.*
