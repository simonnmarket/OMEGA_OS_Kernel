# Memorando técnico denso — não conformidade, risco de modelo e veto de *deploy*

**Classificação:** INTERNO — Risco / Quant / Engenharia — **não** é parecer jurídico nem declaração regulatória  
**Referência normativa interna:** `MANIFESTO_EVIDENCIA_VETO_CIENTIFICO_TIER0.md`  
**Assunto:** Resposta formal às “Falhas Críticas #1–#3”, esclarecimento sobre **ausência de aprovação** de artefactos V8.2.6, e critérios de evidência para decisão  
**Data:** 2026-03-25  
**Versão:** 1.0  

---

## 0. Destinatários e propósito

Este texto serve para **elevar o nível de exigência** em revisões internas: linguagem **precisa**, **intimidante** apenas no sentido de **rigor lógico e exigência de prova**, não de retórica comercial.  
**Não** substitui assessoria legal, **não** invoca Basel III / FRTB como “certificação” de um *script* Python, e **não** qualifica **fraude** ou **violação regulatória** — categorias que exigem **facto jurídico**, **jurisdição** e **processo**. O que segue é **parecer técnico interno** com **poder de veto operacional** no âmbito do manifesto de evidência.

---

## 1. Esclarecimento directo (leitura obrigatória)

**Pergunta implícita:** *“O assistente aprovou o V8.2.6 com palavras bonitas?”*

**Resposta:** **Não.** Os pareceres anteriores **rejeitaram** homologação, assinalaram **não conformidade** entre narrativa e código, e classificaram múltiplas afirmações como **NP** (não provadas) ou **I** (inadmissíveis logicamente) ao abrigo do manifesto.  
Se algo soou “suave”, foi **precisão** (evitar acusações legais infundadas), **não** benevolência técnica.

**Pergunta:** *“Tenho certeza deste documento?”*

**Resposta:** Pode ter **certeza** apenas do que está **explicitamente** assente em **artefactos verificáveis** (hashes, *scripts*, *outputs* JSON, linhas de código citadas). O restante permanece **hipótese** ou **risco** até medição. Este memorando **fixa** o que está **provado no dossiê** e o que **não** o está.

---

## 2. Sobre o texto colado (“LEGAL DECLARATION”, fraude, Basel, *freeze* PSA)

| Afirmação no texto colado | Posição técnica deste memorando |
|-----------------------------|----------------------------------|
| “FRAUDE MATERIAL” | **Fora de competência** deste parecer. **Fraude** exige demonstração jurídica; aqui apenas se regista **discrepância documental** e **ausência de prova**. |
| “Basel FRTB COMPLIANT” | **Inadequado.** FRTB regula **Risco de Mercado** em instituições sujeitas a regulamentação prudencial; **não** se aplica a um *script* de *trading* por analogia retórica. |
| “GUARANTEED LOSS-MAKING” | **NP** como teorema. Perda **garantida** exigiria prova em **todos** os estados do mundo — inexistente. O que **é** sustentável: **ausência de evidência** de *edge* positivo **após custos** e **elevado risco de modelo**. |
| “FREEZE PERMANENTE / V9.0” | **Decisão de governação**, não consequência lógica única dos dados. O parecer técnico pode recomendar **suspensão de *deploy*** e **rebaselining**; não substitui acta do Conselho. |

**Recomendação redacional:** substituir linguagem penal/regulatória genérica por **“recomendação: não *deploy* até…”** com lista **numerada** de condições **mensuráveis**.

---

## 3. Falha crítica #1 — Arquitectura de *polling* e custo computacional

### 3.1 Tese

*Loop* `while True` com `time.sleep(1)` e, em cada iteração, chamadas `mt5.copy_rates_from_pos` e cálculo completo, constitui **amostragem por *polling***, não **orientada a eventos** (novo *tick* / nova barra no *callback*).

### 3.2 O que está **provado** (P)

- O padrão **bloqueia** o *thread* principal entre ciclos; a carga de CPU depende do trabalho **por ciclo** e da frequência efectiva.  
- **Sem** *profiling* (`cProfile`, `perf_counter` distribuído, contagem de chamadas MT5), **não** há número **P** para “gargalo” ou “P95 &lt; 20 ms” como propriedade do sistema — apenas **medição pontual** no `print` do código exemplo (não reproduzida aqui como log arquivado).

### 3.3 O que é **risco técnico** (PP → veto condicionado)

- **Latência de decisão** não é igual a “latência de cálculo interno”; inclui **fila** do SO, **spread** de *polling*, e atraso até **próxima barra** M1.  
- Em máquinas com CPU partilhada, *polling* 1 Hz pode ser aceitável ou não — **decisão exige perfil energético e histograma** (não adjetivos).

### 3.4 Condições de encerramento (para deixar de ser NP)

1. Registo **CSV** de `perf_counter` por função, **N ≥ 10⁴** ciclos, ambiente **fixo** (máquina, build MT5, conta).  
2. Comparação **A/B**: *polling* 1 s vs *Timer* MT5 / *OnTick* (se arquitectura suportar) com **mesma** lógica matemática.

### 3.5 Veto (manifesto)

Até existir **P** para consumo de CPU e latência **no alvo de execução**, afirmações do tipo “Peso-Pluma”, “92% menos RAM”, “10k eventos/s” permanecem **NP** → **Veto V1/V6** sobre qualquer *sign-off* de “arquitectura validada”.

---

## 4. Falha crítica #2 — Beta volátil e risco de modelo

### 4.1 Tese

O estimador de \(\beta\) **não** é um número estável: em OLS rolante verdadeiro, \(\hat\beta_t\) varia com a janela; numa variante **errada** (regressão **única** nos últimos 500 pontos aplicada a **toda** a série), o **objecto** muda — deixa de ser o motor V8.2.1 documentado.

### 4.2 O que está **provado** no código analisado (P sobre o texto)

- Foi identificado um padrão em que **um único** par \((\hat\alpha,\hat\beta)\) estimado no bloco terminal é aplicado a **todos** os pontos do *buffer* para formar `spreads`. Isso **diverge** da especificação causal **bar-a-bar** do relatório V8.2.1 (onde \(\hat\beta_t\) usa apenas dados **até** \(t-1\) para o **spread em** \(t\)).

### 4.3 Implicações (risco de modelo)

- **Viés de especificação:** decisões baseadas num **spread** que **não** é o mesmo definido em R&D.  
- **Instabilidade:** mesmo sob especificação correcta, \(\hat\beta_t\) pode variar abruptamente em **quebras de regime**; **sem** métricas de estabilidade (variância rolante de \(\hat\beta_t\), *CUSUM*, *half-life* do erro), o risco **não** está quantificado.

### 4.4 Métricas mínimas exigidas (antes de *deploy*)

| Métrica | Finalidade |
|---------|------------|
| Série \(\hat\beta_t\) (rolante) | Deteção de **saltos** e janelas de instabilidade |
| *Half-life* do spread (sob especificação escolhida) | Ligar estatística a horizonte de *hold* |
| Sensibilidade da decisão a \(w\) (janela OLS) | Robustez **V8** do manifesto |

### 4.5 Veto

Enquanto **paridade matemática** R&D ↔ produção **não** for demonstrada com **diff** fechado e teste de regressão numérico, **Veto V2** sobre “motor validado”.

---

## 5. Falha crítica #3 — Ausência de monitorização de “cointegration decay”

### 5.1 Definição operacional

“*Cointegration decay*” não é um único teste standard com esse nome em manuais; na prática exige **monitorização de relação de longo prazo** ao longo do tempo:

- **Johansen:** estatística de *trace* / *max-eigen* em **janela rolante** (com custo computacional e correcções múltiplas).  
- **Engle–Granger:** ADF (ou Phillips–Perron) em **resíduos** de regressão **rolante** ou **recursiva**.  
- **Spread OLS rolante:** ADF em sub-janelas — já observou-se, em **proxy** diário, **fração elevada** de janelas onde **não** se rejeita raiz unitária ao nível usual (ordem **85%** das janelas deslizantes em certa configuração documentada no dossiê `adf_results.json`).

### 5.2 O que o código de execução **não** implementa

- **Não** há módulo que calcule **trace** rolante ou **p-value** rolante com **armazenamento** e **alarme**.  
- **Não** há teste formal de **quebra estrutural** (ex.: suplementares *Quandt*/*Chow* documentados) no *gateway*.

### 5.3 Conclusão técnica

A ausência **não** “prova” que o par deixou de estar cointegrado em todos os instantes; **prova** que **não há telemetria** de *decay* — logo, **não há** base para afirmações de “detector de cisão de regime” baseadas em cointegração **fora** de \(Z\) e heurísticas.

### 5.4 Veto

**Veto V8** (regime): decisões de *ejeção* baseadas só em \(|Z|\) **sem** monitor de estabilidade da relação de longo prazo permanecem **PP** no melhor caso — **não** fecham o requisito de *model risk* para capital.

---

## 6. Síntese — estados de evidência (actualização 2026-03-25)

| Domínio | Estado | Consequência para decisão |
|---------|--------|---------------------------|
| Linhagem manifesto ↔ CSV | **NP** (última auditoria) | **V1** activo até novo manifesto |
| Paridade V8.2.1 ↔ V8.2.6 (estimador do spread) | **NP** / **RP** | **V2** activo |
| *Polling* vs latência documentada | **NP** | **V6** activo |
| *Cointegration decay* monitorizado | **NP** | **V8** activo |
| PnL líquido / PF após custos no pipeline *live* | **NP** | **V5** activo |

**Síntese numa linha:** o sistema **não** está **fechado** para decisão de *deploy* ao nível de **prova** exigida pelo manifesto; isso **não** equivale a “fraude” nem a “perda garantida” — equivale a **insuficiência de evidência** e **risco de modelo não quantificado**, o que em governança interna **justifica veto**.

---

## 7. Parecer final (índole de auditoria interna)

1. **Recomenda-se** tratar qualquer versão “SUPREME / PLUME / FINAL” como **protótipo de engenharia** até cumprimento de provas **P** nos domínios acima.  
2. **Recomenda-se** **não** autorizar *deploy* com capital real **enquanto** **V1–V2–V5–V6–V8** não forem desactivados por artefactos mensuráveis.  
3. **Recomenda-se** que comunicações internas **eliminem** termos de produto e **substituam** por referências a **ficheiros**, **hashes** e **IDs de teste**.

---

## 8. Assinaturas (preencher em versão PDF/acta)

| Função | Nome | Data | Visto |
|--------|------|------|-------|
| Risco quantitativo | | | |
| Engenharia | | | |
| Revisão independente | | | |

---

**FIM DO MEMORANDO**

*Documento técnico interno. Sem valor de auditoria externa nem efeito legal sem adoptado por órgão competente.*
