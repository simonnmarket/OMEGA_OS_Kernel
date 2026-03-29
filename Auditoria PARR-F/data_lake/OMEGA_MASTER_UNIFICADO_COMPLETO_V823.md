# OMEGA — Documento mestre unificado (V8.2.x → V8.2.3)

**Versão do mestre:** 1.0 · **Data:** 2026-03-24 · **Código:** `OMEGA-MASTER-UNIFIED-V823-20260324`

Este ficheiro consolida **num único documento**: (i) Protocolo REV3, (ii) Relatório V8.2.1 auditado, (iii) Relatório de confronto do *data lake*, (iv) evidências numéricas (JSON/MANIFEST), (v) especificação e auditoria do gateway V8.2.2/V8.2.3, (vi) matriz de decisão e reproducibilidade.

**Classificação:** INTERNO — Conselho / CQO / CFO / CTO / Engenharia.

**Nota:** não substitui parecer jurídico-regulatório externo. Números estatísticos dependem dos **ficheiros e scripts** citados no [§11](#11-índice-de-ficheiros-comandos-de-reproducibilidade-e-hashes).

---

## Índice

| § | Conteúdo |
|---|----------|
| [0](#0-ficha-e-âmbito) | Ficha e âmbito |
| [1](#1-síntese-executiva-global) | Síntese executiva global |
| [2](#2-protocolo-de-pesquisa-científica-e-modelagem-quantitativa--omega-v82--rev3-texto-integral) | Protocolo V8.2 REV3 (integral) |
| [3](#3-omega-v821--relatório-unificado-final-auditado-texto-integral) | Relatório V8.2.1 (integral) |
| [4](#4-relatório-de-confronto--data-lake-métricas-integridade-e-decisão-texto-integral) | Confronto *data lake* (integral) |
| [5](#5-evidências-numéricas-consolidadas) | Evidências numéricas consolidadas |
| [6](#6-motor-de-execução-mt5-v822--v823-supreme) | Gateway V8.2.2 / V8.2.3 |
| [7](#7-confronto-métricas-declaradas-vs-evidência-reproduzida) | Métricas declaradas vs evidência |
| [8](#8-gates-g-a-a-g-d-e-matriz-de-decisão) | Gates e matriz de decisão |
| [9](#9-limitações-globais) | Limitações globais |
| [10](#10-homologação-tabela) | Homologação (tabela) |
| [11](#11-índice-de-ficheiros-comandos-de-reproducibilidade-e-hashes) | Ficheiros, comandos, hashes |

---

## 0. Ficha e âmbito

| Origem consolidada | Ficheiro de origem (referência) |
|--------------------|----------------------------------|
| Protocolo científico REV3 | `OMEGA_PROTOCOL_V8.2_MASTER_PROPOSAL_REV3_FINAL.md` |
| Relatório causal V8.2.1 | `OMEGA_V821_RELATORIO_UNIFICADO_FINAL_AUDITADO_20260324.md` |
| Confronto *data lake* | `RELATORIO_CONFRONTO_METRICAS_DATA_LAKE_V823.md` |
| Métricas MT5 *slice* | `data_lake/data_lake_metrics.json` |
| Proxy Yahoo (ADF) | `evidence_runs/ADF_EVIDENCE_20260324/adf_results.json`, `MANIFEST.json` |

**Caminhos base:**

- *Data lake:* `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\data_lake`
- *Documentação (espelho Cursor):* `…\nebular-kuiper\Auditoria PARR-F\Documentacao_Processo`

---

## 1. Síntese executiva global

1. **Integridade de dados:** o manifesto `data_manifest_v82.json` referencia **50 000 barras** e **SHA-256** específicos; os CSV actuais em `live_feed/` tinham **478 barras** e **hashes diferentes** no momento da auditoria — *data lineage* **não fechado** até alinhar ficheiros ao manifesto ou actualizar o manifesto.
2. **Johansen:** `johansen_m1_results.json` declara **cointegração** com *trace* ≈ **32,96** (50 k barras). Recomputação *statsmodels* nas **478** barras do *slice* presente: *trace* ≈ **11,13** \< crítico **15,49** → **não** cointegração a 95% **nessa amostra**; o resultado em 50 k **não foi** reproduzido com os ficheiros actuais do *live_feed*.
3. **ADF:** no *slice* 478 (janelas OLS/EWMA **adaptativas**), **EG residual** *p* ≈ **0,071**; **spread OLS rolante** *p* ≈ **0,016**. Objetos estatísticos **distintos** — ambos devem constar em qualquer *sign-off*.
4. **Proxy Yahoo (GC=F/SI=F, diário):** EG full-sample *p* elevado; spread rolante agregado *p* muito baixo; **~87,5%** dos chunks anuais e **~85%** das janelas deslizantes (252) com *p* \> 0,05 em testes locais — **risco de regime** não resumível num único *p-value*.
5. **Protocolo REV3** mantém **Bloqueador 1** em proxies Yahoo (Johansen base **não** aprova GC/SI a 95% na janela documentada no anexo C) e exige **MT5 M1** para decisões finais de cointegração.
6. **V8.2.1** formaliza **causalidade** na normalização (EWMA com informação até *t−1*) e **não** aprova escala de **capital** até Gates e PnL líquido.
7. **Gateway V8.2.3:** parâmetros documentados (Z 3,75, timeout 30 barras, ejeção \|Z\|\>5, CB −3,5%); **auditoria de código:** versões duplicadas, **ATR/trailing** mencionado num cabeçalho mas **ausente** no código analisado, execução em **duas pernas** não atómica, `BASE_DIR` hardcoded em variante, logs de auditoria **sem** ENTRY em variante.
8. **Decisão:** *homologação final* e *sign-off* de capital **condicionados** a *dataset* com hash correcto, paridade código–dados, unidades de custo fechadas e demo instrumentada.

---

## 2. Protocolo de pesquisa científica e modelagem quantitativa — OMEGA V8.2 — REV3 (texto integral)

# PROTOCOLO DE PESQUISA CIENTÍFICA E MODELAGEM QUANTITATIVA  
## OMEGA V8.2 — TRANSIÇÃO ARQUITETURAL PARA ARBITRAGEM ESTATÍSTICA E PAIRS TRADING

| Campo | Valor |
|--------|--------|
| **Código do protocolo** | `OMEGA-PROTOCOL-2026-03-24-TIER0-V8.2-PROPOSAL-REV3` |
| **Classificação** | Académica — Diretriz estratégica fundacional |
| **Data** | 2026-03-24 |
| **Estado** | **Retificação de integridade — Bloqueador 1 ABERTO** |
| **Autoria** | Engenharia Quantitativa Tier-0, OMEGA Foundation |
| **Nota de arquivo** | Documento consolidado para continuidade; revisão humana do Conselho recomendada |

---

## Destinatários (internos)

Conselho Executivo OMEGA (CEO, CFO, CTO, CQO, CKO, COO) — **aguardando aprovação condicional da Fase 1** (dados/custos apenas).

*Referências académicas externas podem ser listadas em anexo institucional separado, se aplicável.*

---

## 1. Declaração de integridade e retratação científica (Bloqueador 1: ABERTO)

O presente documento actualiza a revisão **REV2**, na qual ocorreu falha grave de interpretação: reportou-se *«Bloqueador 1 Resolvido»* perante output de **Johansen** que **rejeitava** cointegração a **95%** para pares com proxies Yahoo diários (2020–2026).

**Padrão Tier-0:** *Dados reais > afirmações.*

**Assunção pública da falha:**

> Executámos teste de Johansen (proxies Yahoo, diário, 2020–2026) com especificação base (`det_order=0`, `k_ar_diff=1`). **Não** se verificou cointegração ao nível 95% para GC=F vs SI=F (**12,70 < 15,49**) nem GC=F vs DX-Y.NYB (**4,17 < 15,49**) segundo o critério *trace* vs valor crítico. **Bloqueador 1 permanece aberto** até robustez (especificação alternativa, **dados MT5 M1 nativos**, ou novo desenho). O protocolo REV3 actualiza método; **não** autoriza *sign-off* de capital baseado em cointegração com artefactos actuais da Fase 0.

---

## 2. Sumário executivo e Hurst (retificado)

A análise empírica do XAUUSD em M1 registrou **H ≈ 0,5517** (estimador/janela conforme relatório de auditoria).

| Região (convenção usual) | Interpretação |
|--------------------------|----------------|
| H < 0,45 | Anti-persistente (tende reversão) |
| H ≈ 0,50 | Semelhante a passeio aleatório |
| H > 0,55 | Persistência (tendência fraca) |

**Nota de prudência:** **0,5517** situa-se **no limiar**; evitar conclusões peremptórias sem intervalo de confiança do estimador.

**Implicação para V8.2:** reversão à média **directa** no preço univariado M1 **não** é o caminho principal; **mean reversion** exige **spread** bivariado **estacionário** (pairs), sujeito a **prova** (Engle–Granger / Johansen em **séries correctas**).

---

## 3. Metodologia V8.2 — Pairs Trading (síntese)

### 3.1 Bloqueador #1 (Asset_B) — estado para o Conselho

Sob especificação base em proxies diários, **não** há cointegração a 95% para os pares testados inicialmente. **Pesquisa continua** com:

- Pares alternativos (ex.: platina/paládio como **hipótese**, não conclusão);
- **Engle–Granger** (dois passos) **e** Johansen **lado a lado**;
- Segmentação por **regime** (stress documentado);
- **Obrigatoriedade** de transição para **MT5 M1 real** (reduzir *basis risk*).

### 3.2 Custos e modelo de impacto (condicional)

Modelo basilar `transaction_cost_model` (CFO): *spread*, *slippage*, comissão, *fill rate*, latência assimétrica — ver **Anexo A (JSON)**.

**Thresholds de trabalho (proposta interna, sujeita a calibragem):**

- \(PF_{\text{Net}} \ge 1{,}50\) (pós-custos)
- \(PF_{\text{Gross}} \ge 2{,}25\) (antes de custos, coerente com penalização agregada)
- Razão MAE/MFE calibrada empiricamente (meta indicativa **1,50**)

---

## 4. Gates G-A a G-D (portas não negociáveis)

| Gate | Conteúdo |
|------|----------|
| **G-A** | Reprodutibilidade: `DATA_MANIFEST` + SHA-256 + commits |
| **G-B** | Inferência: Johansen / Engle–Granger documentados; testes de média **correctamente especificados** (evitar Welch degenerado); pré-registo quando aplicável |
| **G-C** | Microestrutura: conformidade com `transaction_cost_model` (HFT) |
| **G-D** | Risco OOS: MaxDD ≤ limite CFO; critérios MAE/MFE conforme política |

**Trading live** permanece **travado** até cruzamento documentado dos gates.

---

## 5. Roadmap reconstruído

### Fase 1 (autorização moral/financeira limitada — dados)

- Parar dependência de **proxy Yahoo** para decisões de cointegração finais;
- Mineração **MT5 M1** via `TickRecorderAgent.py` (ou pipeline equivalente versionado);
- Activo: XAUUSD, XAGUSD, XPTUSD, XPDUSD (e correlatos aprovados);
- Manifestos, hashes, particionamento, regimes de stress (COVID, Fed 2022, SVB, contemporâneo).

### Fase 2–3

- OLS + **Kalman** para \(\beta\) dinâmico (hipótese de engenharia);
- GARCH(1,1) para volatilidade (selecção AIC/BIC documentada);
- Walk-forward OOS + auditoria independente.

---

## 6. Declaração final

A OMEGA Foundation **não** avança com *claims* contraditórios aos testes (**trace < valor crítico**). Rejeita-se publicamente a leitura «aprovada» quando `cointegrated = false`.

**Desenvolvimento de execução** permanece **travado** até `cointegrated = true` (ou critério equivalente pré-registado e auditável) em **dados MT5** nas condições definidas.

**FIM DO PROTOCOLO REV3 (RETIFICADO)** — *secção integral incluída no mestre.*

---

### Anexo A — `transaction_cost_model` (referência)

```json
{
  "transaction_cost_model": {
    "asset_class": "XAUUSD (M1 High Frequency)",
    "execution_model": "Pairs Trading / Contraction",
    "avg_spread_bid_ask_pts": 12.0,
    "avg_slippage_pts": 5.0,
    "commission_per_lot_usd": 7.0,
    "total_cost_per_round_trip_pts": 19.0,
    "market_impact_penalty": {
      "fill_rate_estimated": 85.0,
      "partial_fill_factor": 0.6,
      "asymmetric_latency_ms": 50,
      "z_score_edge_decay_percent": 15.0
    },
    "recalculated_thresholds": {
      "gross_pf_required": 2.25,
      "net_pf_after_costs_target": 1.50,
      "mae_mfe_ratio_calibrated": 1.50
    }
  }
}
```

### Anexo B — Script de pesquisa alternativa (PROTÓTIPO PROXY — não substitui MT5)

*Uso apenas para exploração até Fase 1 com dados nativos.*

```python
# SCRIPT DE PESQUISA ALTERNATIVA TIER-0: JOHANSEN MULTI-PAR (PROTOTYPE_PROXY_ONLY)
import json
import yfinance as yf
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import coint_johansen

print("[*] TESTANDO PARES ALTERNATIVOS PARA COINTEGRAÇÃO V8.2 (PROXY)")

data = yf.download(
    "GC=F SI=F PA=F PL=F DX-Y.NYB",
    start="2020-01-01",
    end="2026-03-24",
    progress=False,
)["Close"].dropna()

pairs_to_test = [
    ("GC=F", "SI=F", "Ouro vs Prata"),
    ("GC=F", "PA=F", "Ouro vs Paládio"),
    ("GC=F", "PL=F", "Ouro vs Platina"),
    ("GC=F", "DX-Y.NYB", "Ouro vs DXY"),
]

resultados = []
for asset_a, asset_b, nome in pairs_to_test:
    df_pair = data[[asset_a, asset_b]]
    coint_test = coint_johansen(df_pair, det_order=0, k_ar_diff=1)
    trace = coint_test.lr1[0]
    cv_95 = coint_test.cvt[0, 1]
    resultados.append({
        "pair": nome,
        "asset_A": asset_a,
        "asset_B": asset_b,
        "trace_statistic": float(trace),
        "critical_value_95%": float(cv_95),
        "cointegrated": bool(trace > cv_95),
        "difference": float(trace - cv_95),
    })

out = {
    "pairs_tested": resultados,
    "status": "REQUIRES_MT5_M1_CONFIRMATION",
    "note": "Proxies Yahoo != série de execução MT5",
}
with open("johansen_test_alternativos.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=4)
```

### Anexo C — Output de referência (falha sob especificação base Ouro/Prata global)

```json
{
  "protocol": "Johansen_Test_Unlock_CFO",
  "pairs_tested": [
    {
      "asset_A": "XAUUSD (Proxy: GC=F)",
      "asset_B": "XAGUSD (Proxy: SI=F)",
      "trace_statistic": 12.704077799022413,
      "critical_value_95%": 15.4943,
      "cointegrated": false,
      "interpretation": "Par Ouro/Prata falhou o threshold de 95% nesta janela e especificação."
    }
  ],
  "status": "COINTEGRATION_NOT_FOUND_AT_95_UNDER_BASE_SPEC",
  "conclusion": "Bloqueador 1 ABERTO. Próximo passo: regimes, especificações alternativas, dados MT5 M1."
}
```

---

## 3. OMEGA V8.2.1 — Relatório unificado final (auditado) (texto integral)

# OMEGA V8.2.1 — RELATÓRIO UNIFICADO FINAL (AUDITADO)
## Prova matemática causal, defesa perante CQO/CFO e encaminhamento Fase 3

| Campo | Valor |
|--------|--------|
| **Código do documento** | `OMEGA-UNIFIED-V821-FINAL-AUDIT-20260324` |
| **Versão** | 1.0 — Consolidado pós-auditoria independente |
| **Data** | 2026-03-24 |
| **Classificação** | INTERNO — CONSELHO / CQO / CFO / CKO |
| **Estado do programa** | **Fase 2 (motor matemático causal): concluída para R&D** · **Fase 3 (execução): autorizada como engenharia** · **Capital: não escalado** |

---

## Declaração de responsabilidade

Este relatório integra o trabalho de **Engenharia Quantitativa** e o **parecer de auditoria** (CQO/CFO) sobre consistência causal, linguagem estatística e risco de decisão. **Não** substitui parecer jurídico-regulatório externo. Métricas numéricas (PF, ADF, etc.) dependem dos **ficheiros Parquet MT5** e da **versão exacta** do código referenciada.

---

## 1. Sumário executivo (para o Conselho)

1. **V8.2.1** corrige o *look-ahead* na **normalização** do spread: **média e desvio EWMA** usados em \(t\) são os calculados com informação até **\(t-1\)** (`shift(1)`).  
2. O **PnL** deixa de usar `shift(-h)`; passa a um **backtester por eventos** (*state machine*) **bar-a-bar**, alinhado à lógica de decisão causal.  
3. **ADF** sobre o **spread residual** (OLS rolante) rejeita raiz unitária nos relatórios internos (p.ex. **p ≈ 8,46e-27**, estatística fortemente negativa) — interpretação correta: **spread estacionário** *sob esta construção*, não substitui por si só **teste de cointegração clássico** (Engle–Granger / Johansen) nos **níveis** dos dois activos.  
4. **Custos** (modelo **19 pts** agregado) estão incorporados na simulação; **unificar dimensionalmente** spread vs pontos de custo permanece **pendência técnica** antes de decisão de capital.  
5. **PF líquido** inicial com custos agressivos em M1 pode ser **baixo** (ex. ordem **0,06** nos testes internos) — isso é **compatível com honestidade** do modelo; **não** constitui aprovação de *edge* comercial.  
6. **Fase 3** (**motor de execução / gateway MT5**) está **autorizada como desenvolvimento de software** e instrumentação; **não** como aumento de alocação de capital até **Gates** completos e **unidades de PnL** fechadas.

---

## 2. Resposta à auditoria REV4 (CQO / CFO)

### 2.1 Look-ahead na normalização (Z-Score)

| Questão | Resolução V8.2.1 |
|---------|-------------------|
| EWMA de \(S_t\) a incluir \(S_t\) na média/desvio do mesmo instante | **Substituído** por `EWMA.mean().shift(1)` e `EWMA.std().shift(1)` antes de formar \(Z_t\). |
| Decisão em \(t\) | Utiliza apenas parâmetros de volatilidade/memória **até \(t-1\)** para normalizar \(S_t\). |

### 2.2 Look-ahead no PnL

| Questão | Resolução V8.2.1 |
|---------|-------------------|
| Uso de `shift(-horizon)` no lucro | **Eliminado.** |
| Simulação | **Máquina de estados**: entradas/saídas por limiares de \(Z\) e evolução **causal** bar-a-bar. |

### 2.3 ADF e linguagem institucional

- **Afirmação segura:** *“O teste ADF aplicado à série do spread residual (definição OLS rolante) rejeita a hipótese nula de raiz unitária ao nível convencional (ex. 5%), com estatística e p-value registados no JSON de auditoria.”*  
- **Evitar** como única base: *“cointegração I(0) do par”* sem **Engle–Granger** ou **Johansen** nos **preços** (ou log-preços) na **mesma** amostra MT5, em **paralelo** ao motor rolling.

### 2.4 Modelo de custos (19 pts)

- Componentes de referência interna: **spread**, **slippage**, **comissão** (total agregado **19** unidades no modelo CFO).  
- **Pendência:** converter **movimento do spread** e **custos** para a **mesma unidade económica** (USD por lote ou por unidade de exposição) antes de **PF** definitivo para o Conselho.

---

## 3. Especificações técnicas — Motor V8.2.1

| Parâmetro | Especificação | Notas |
|-----------|----------------|--------|
| **Par** | XAUUSD (**Y**) vs XAGUSD (**X**) | Dados M1 MT5 alinhados |
| **Regressão** | OLS rolante, janela **500** | \(\alpha_t,\beta_t\) estimados só com barras **anteriores** a \(t\) |
| **Spread** | \(S_t = Y_t - \alpha_t - \beta_t X_t\) | Após `dropna` inicial |
| **Normalização** | EWMA span **100**, **μ** e **σ** com **`shift(1)`** | \(Z_t = (S_t - \mu_{t|t-1})/(\sigma_{t|t-1}+\epsilon)\) |
| **Gatilhos (exemplo)** | Entrada: \(\|Z\| \ge 2{,}0\); saída: \(Z\) cruza **0** | Fase 3 pode elevar para **\(\ge 3{,}0\)** |
| **Custos** | **19** pts (modelo agregado) | Sujeito a harmonização dimensional |
| **Paradigma dual** | Sinal: **Close** alinhado; risco Fase 3: **High/Low** | Documento de execução separado |

---

## 4. Lógica do backtester causal (resumo)

- **Estado 0:** fora do mercado.  
- **Entrada long spread** (ex.): \(Z_t \le -Z_{entry}\).  
- **Entrada short spread** (ex.): \(Z_t \ge +Z_{entry}\).  
- **Saída:** retorno de \(Z\) ao patamar de saída (ex. **0**), com PnL a partir da diferença de **spread** menos custo agregado.

**Pendências de engenharia (auditoria):**

1. **Fechar** posições abertas no **fim** da amostra (mark-to-market ou regra explícita).  
2. **`merge` inner** por `time` entre séries, com relatório de **gaps**.  
3. **Time stop** / **stop em spread** (opcional mas recomendado para paridade com produção).

---

## 5. Resultados típicos reportados internamente (ilustrativos)

*Valores dependem dos Parquet reais; coluna “ilustrativo” serve apenas para estrutura de relatório.*

| Métrica | Ordem de grandeza interna (exemplo) | Interpretação |
|---------|--------------------------------------|----------------|
| **ADF p-value (spread)** | Muito baixo (ex. **~1e-26**) | Rejeição H0 de raiz unitária no spread construído |
| **\(\beta\) médio** | ~**20,8** | Depende de unidades; validar estabilidade |
| **Nº de trades** | Centenas (ex. **381**) | Sensível a limiares e oscilação de \(Z\) |
| **PF líquido (simulação)** | Pode ser **≪ 1** (ex. **0,06**) | Compatível com custos altos vs movimento de spread em M1 |
| **Custo aplicado** | 19 pts (modelo) | Sujeito a conversão dimensional |

**Análise de risco:** PF baixo **não** “invalida” o Tier-0 — **reforça** a necessidade de **filtros**, **limiares** mais altos em **Z**, **timeframe** de execução ou **dois pares** de pernas com custo realista.

---

## 6. Gates G-A a G-D — estado realista

| Gate | Conteúdo | Estado |
|------|------------|--------|
| **G-A** | Reprodutibilidade: hash Parquet + commit do código | **Condicional** — exige artefactos anexados |
| **G-B** | Estacionariedade do spread (ADF) + testes de cointegração **complementares** nos preços | **Parcial** — ADF OK no spread; **EG/Johansen** recomendado |
| **G-C** | Microestrutura e custos | **Parcial** — modelo 19 pts; **unificar** unidades |
| **G-D** | Risco e viabilidade (PF, DD, limites CFO) | **Não aprovado** para capital até métricas **líquidas** e **OOS** aceitáveis |

**Conclusão:** **Não** declarar “todos os gates destravados” para **alocação de capital**. Declarar **destravado** o **avanço para Fase 3** como **projeto de engenharia**.

---

## 7. Código de referência — `OmegaCausalEngineV821` (resumo)

O motor:

1. Alinha `close` de XAU e XAG.  
2. Estima **OLS rolante** (500) e forma **Spread**.  
3. Calcula **Z** com **EWMA** e **`shift(1)`**.  
4. Executa **loop** de estados para PnL agregado e lista de trades.  
5. Corre **ADF** no **Spread** e exporta **JSON** de auditoria.

*O código integral deve residir no repositório versionado (ex. `09_ols_math_block_REV4.py` / `omega_causal_engine_v821.py`) com hash de commit.*

---

## 8. Próximos passos oficiais

1. **Conselho:** homologar **este** relatório como **quadro de verdade** para V8.2.1 (método causal + limitações).  
2. **Fase 3:** implementar **Execution Gateway** MT5 (ordens, *dual-mode* linhas/velas, reconciliação com custo real).  
3. **Quant:** completar **cointegração** clássica nos preços + **PnL** em **USD** (ou unidade aprovada pelo CFO).  
4. **Moratória de capital** até novo parecer após **DEMO** instrumentada e **G-D** satisfeito.

---

## 9. Limitações e não-afirmações

- O documento **não** garante lucro futuro nem **edge** populacional.  
- **“Aprovado”** no título deste ficheiro refere-se a **conclusão da Fase 2 como etapa de método**, salvo acta divergente do Conselho.  
- Resultados **ADF/PF** citados são **condicionais** aos dados e versão do código.

---

## 10. Homologação (preencher)

| Função | Nome | Data | Assinatura |
|--------|------|------|------------|
| CQO | | | |
| CFO | | | |
| CTO | | | |
| CKO | | | |
| CEO | | | |

---

## Anexo A — Frase única para acta do Conselho

> *“Aprovamos o relatório unificado OMEGA V8.2.1 como definição do **método causal** e dos **requisitos pendentes** (unidades, cointegração complementar, fechos de posição). Autorizamos o **início da Fase 3 — engenharia de execução**, sem liberação de capital para escala até cumprimento dos Gates G–D e demonstração OOS.”*

---

## Anexo B — Referência de ficheiros sugeridos

| Ficheiro | Conteúdo |
|----------|-----------|
| `data_lake/XAUUSD_M1_HISTORICO.parquet` | Série M1 |
| `data_lake/XAGUSD_M1_HISTORICO.parquet` | Série M1 |
| `audit_blocks/V821_FINAL_CAUSAL_PROOF.json` | ADF, PF, trades (versão reprodutível) |

---

**FIM DA SECÇÃO V8.2.1** — *texto integral incluído no mestre.*

---

## 4. Relatório de confronto — Data Lake (métricas, integridade e decisão) (texto integral)

*Segue o conteúdo completo de `RELATORIO_CONFRONTO_METRICAS_DATA_LAKE_V823.md`.*

# Relatório de confronto — Data Lake OMEGA (métricas, integridade e decisão)

| Campo | Valor |
|--------|--------|
| **Documento** | `RELATORIO_CONFRONTO_METRICAS_DATA_LAKE_V823` |
| **Versão** | 1.0 |
| **Data (UTC)** | 2026-03-24 |
| **Âmbito** | Confrontar afirmações de protocolo (V8.2.1–V8.2.3) com **ficheiros reais** em `data_lake`, métricas **recomputadas** e evidência **proxy** reprodutível |
| **Classificação** | INTERNO — Conselho / CQO / CFO / Engenharia |

---

## 1. Sumário executivo (leitura obrigatória)

1. **Integridade de dados:** o ficheiro `data_manifest_v82.json` declara **50 000 barras** e **hashes SHA-256** por ativo; os CSV actuais em `live_feed/` contêm **478 barras** cada e **hashes diferentes**. **Conclusão:** o *slice* em `live_feed` **não** é o mesmo objecto binário que o manifesto descreve — qualquer métrica que dependa de 50 k barras **não pode** ser validada apenas com estes ficheiros.
2. **Johansen:** o ficheiro `johansen_m1_results.json` afirma **cointegração** com *trace* ≈ **32,96** (50 000 barras). Uma **recomputação** *statsmodels* sobre o **merge actual** (478 barras alinhadas) produz *trace* (r=0) ≈ **11,13** vs crítico 95% **15,49** → **não** rejeição da hipótese de **nenhuma** relação de cointegração ao nível 95% **nesta amostra curta**. Isto **não invalida** o resultado em 50 k barras; **exige** alinhar ficheiro de 50 k com o manifesto.
3. **ADF / spread OLS rolante:** sobre as **478** barras, com janelas **adaptativas** (porque \(n < 610\)), o ADF do **spread rolante** (definição alinhada ao motor) obtém **p ≈ 0,016** (rejeição de raiz unitária a 5% **nesta construção**). O ADF dos resíduos **Engle–Granger** em níveis obtém **p ≈ 0,071** (**não** rejeita a 5%). A divergência entre os dois testes é **esperada** e deve ser explicada em qualquer *sign-off* (objeto estatístico diferente).
4. **Proxy Yahoo (GC=F/SI=F, diário):** evidência separada (reprodutível) mostra que **EG residual full-sample** pode ter **p elevado**, enquanto o **spread OLS rolante agregado** pode ter **p muito baixo** — ou seja, **não** há um único “número ADF” que resuma o risco de regime.
5. **Decisão:** **não** declarar “homologação final” até: (i) *dataset* de 50 k barras **com hash igual ao manifesto** OU actualização do manifesto ao *slice* real; (ii) *script* de Johansen/ADF com **mesmos** parâmetros (`k_ar_diff`, `det_order`, amostra); (iii) critérios de **PnL** e **custos** em unidades fechadas.

---

## 2. Inventário do *data lake* (caminho base)

**Base:** `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\data_lake`

| Artefacto | Descrição |
|-----------|-----------|
| `live_feed\XAUUSD_MADRUGADA_M1.csv` | Export M1 (formato literal MT5 por linha) |
| `live_feed\XAGUSD_MADRUGADA_M1.csv` | Idem |
| `data_manifest_v82.json` | Manifesto (barras, intervalo temporal, SHA-256) |
| `johansen_m1_results.json` | Resultado declarado do teste de Johansen (M1) |
| `run_data_lake_evidence.py` | Script de recomputação (ADF, spread rolante, Johansen) |
| `data_lake_metrics.json` | **Saída** gerada pelo script (métricas confrontáveis) |

---

## 3. Confronto: manifesto vs ficheiros *live_feed*

| Campo | `data_manifest_v82.json` | Ficheiros `live_feed` (parseados 2026-03-24) |
|--------|---------------------------|-----------------------------------------------|
| Barras declaradas | 50 000 por ativo | **478** linhas válidas por ficheiro |
| SHA-256 XAUUSD | `10f440df95188780106cb7bd624e546438ab76179d6b79d1757ccc0865ab6695` | `3904b90e6de9b65e04b78a48688a298f34ef6a2d46b2db984257f9d3c97c807d` |
| SHA-256 XAGUSD | `7eae7a5ab4f8273db6078632e50491dbd36d3270294eb97144b971d68f764000` | `35d3700dd69bee9f5c1805f4eb93e84f33756f4fd52fa6d8e63f1927c3280488` |
| Alinhamento temporal (inner join `time`) | — | **478** linhas, **100%** das chaves presentes em ambos |

**Interpretação (alta confiança):** o *slice* `MADRUGADA` **não** corresponde ao objecto de 50 000 barras referido no manifesto. Para auditoria, ou se **actualiza** o manifesto para este *slice*, ou se **substituem** os CSV por ficheiros cujo **hash** coincida com o manifesto.

---

## 4. Confronto: `johansen_m1_results.json` vs recomputação *statsmodels*

| Métrica | Ficheiro JSON (declarado) | Recomputação (478 barras, `det_order=0`, `k_ar_diff=1`) |
|---------|---------------------------|----------------------------------------------------------|
| Barras | 50 000 | **478** |
| *Trace* (r=0) | **32,955729** | **11,130500** |
| Crítico 95% (r=0) | 15,4943 | 15,4943 |
| Decisão “cointegrado” | `true` | **`false`** (nesta amostra) |

**Nota metodológica:** o teste de Johansen é **sensível ao tamanho da amostra** e à especificação VAR/VECM. O resultado **32,96** pode ser **consistente** com 50 k barras; a recomputação em **478** barras **não** replica esse valor — o que é **esperado**. O problema de governação é **a lacuna** entre o JSON arquivado e o ficheiro **actualmente** versionado no *data lake*.

---

## 5. Métricas ADF / spread (motor V8.2.x) — *data_lake_metrics.json*

**Parâmetros efectivos** (porque \(n = 478 < 610\)): janela OLS **159**, EWMA span **39** (adaptação documentada; **não** é o motor de produção 500/100 sem ajuste de amostra).

| Teste | Resultado (478 barras alinhadas) |
|--------|----------------------------------|
| **Engle–Granger** (Y~const+X, níveis), ADF resíduos | ADF ≈ **-2,716**, **p ≈ 0,071** (nobs 477) |
| **Spread OLS rolante** (mesma lógica causal de estimação *in-sample*), ADF série completa do spread | ADF ≈ **-3,275**, **p ≈ 0,016** (nobs 318) |
| **Z causal (última barra)** estilo motor (μ,σ EWMA em \(t-1\)) | **Z ≈ 1,76** |

**Confronto com gatilho V8.2.3 SUPREME (`MIN_Z_ENTRY = 3,75`):** na última barra deste *slice*, **\(|Z| < 3,75\)** → **entrada não seria disparada** — coerente com um mercado “não extremo” ao fim do extracto.

---

## 6. Evidência proxy Yahoo (GC=F / SI=F, diário) — referência cruzada

**Origem:** `…\.cursor\nebular-kuiper\Auditoria PARR-F\evidence_runs\ADF_EVIDENCE_20260324\` (execução separada; **não** substitui MT5).

| Indicador | Valor de referência (proxy diário, 2010→) |
|-----------|-------------------------------------------|
| Linhas merge | 4 079 |
| ADF resíduos EG (níveis, amostra completa) | **p ≈ 0,191** |
| ADF série **spread OLS rolante** (janela 252 dias) | **p ≈ 7,75×10⁻¹⁰** |
| Fração janelas deslizantes (252) com **p > 0,05** | **≈ 85%** |

**Mensagem para o Conselho:** números **ADF** e **“cointegração”** dependem de **definição do objecto** (resíduos EG vs spread rolante; amostra; TF). Um único *p-value* **não** fecha o dossier de risco.

---

## 7. Confronto com parâmetros do gateway V8.2.3 (documentação interna)

| Parâmetro | Valor típico V8.2.3 | Coerência com *data lake* actual |
|-----------|---------------------|-----------------------------------|
| `window_ols` | 500 | **Exige** \(n \gg 500\); com 478 barras o script usou **159** (tradução honesta) |
| `ewma_span` | 100 | Idem → **39** no *slice* |
| `MIN_Z_ENTRY` | 3,75 | Último Z medido ≈ **1,76** → sem entrada |
| `COST_THRESHOLD` | 19 | Depende de **unidade** de \(|z\cdot\sigma|\); manter anexo dimensional em revisão CFO |
| `TIMEOUT_BARS` | 30 | Regra operacional; não testável só com métricas estáticas |

---

## 8. Matriz de decisão (proposta para acta)

| Pergunta | Evidência mínima | Estado no pacote actual |
|----------|------------------|-------------------------|
| Dataset coincide com manifesto (hash)? | SHA-256 iguais | **Não** |
| Johansen reproduzível no mesmo ficheiro do JSON? | Script + mesmo *n* | **Parcial** — precisa amostra de 50 k referida no JSON |
| ADF/documentação sem ambiguidade? | EG + spread rolante + janelas | **Parcial** — ambos reportados; TF/amostra diferentes |
| Pronto para Fase 4 (demo) com *sign-off* institucional? | Gates acima + PnL | **Condicionado** — corrigir *data lineage* primeiro |

---

## 9. Próximas acções recomendadas (ordenadas)

1. **Substituir** ou **renomear** o manifesto: ou ficheiros de 50 k com **hash** do manifesto, ou manifesto alinhado ao *slice* 478 com **novos** hashes.
2. **Arquivar** o *script* e `data_lake_metrics.json` em cada *release* com **timestamp UTC** e **versão** do código do motor.
3. **Reexecutar** Johansen e ADF com **50 000** barras **idênticas** às usadas no `johansen_m1_results.json` (ou regenerar o JSON a partir do ficheiro único de verdade).
4. **Anexo dimensional:** tabela “1 ponto = X USD/lote” para XAU e XAG e custo **19** agregado.

---

## 10. Referências de ficheiros gerados

| Ficheiro | Conteúdo |
|----------|----------|
| `data_lake\data_lake_metrics.json` | Métricas deste relatório (merge, ADF, Johansen recomputado) |
| `data_lake\run_data_lake_evidence.py` | Código de reproducibilidade |
| `…\evidence_runs\ADF_EVIDENCE_20260324\adf_results.json` | Evidência proxy Yahoo (comparável em espírito, não substitui MT5) |

---

## 11. Limitações do relatório *data lake*

- Não foi executado o **MetaTrader 5** neste ambiente; métricas derivam de **CSV** e de **statsmodels**.
- A recomputação de Johansen usa **defaults** documentados no script; se o JSON original usou **outra** especificação VAR, o número **32,96** pode ser válido — deve ser **parametrizado** no JSON (incluir `det_order`, `k_ar_diff`, versão *statsmodels*).
- Nenhuma destas métricas **garante** lucro líquido nem ausência de *slippage*.

---

**FIM DA SECÇÃO DATA LAKE** — *texto integral incluído no mestre.*

---

## 5. Evidências numéricas consolidadas

### 5.1 *Slice* MT5 `live_feed` — extracto de `data_lake_metrics.json` (2026-03-24)

| Campo | Valor |
|--------|--------|
| Merge inner (`time`) | **478** linhas, `pct_aligned` **1,0** |
| EG níveis: α | **2243,95** |
| EG níveis: β | **31,32** |
| ADF EG residual | stat **-2,716**, **p = 0,0713** |
| OLS rolante efectivo | janela **159**, EWMA **39** (*adaptativo*) |
| ADF série spread rolante | stat **-3,275**, **p = 0,0160** |
| Z última barra (estilo causal) | **1,76** |
| Johansen recomputado (478) | trace **11,13** vs crit. **15,49** → **não** a 95% |

### 5.2 `johansen_m1_results.json` (declarado no *data lake*)

| Campo | Valor declarado |
|--------|-----------------|
| `bars_analyzed` | 50 000 |
| `trace_statistic` | **32,955729** |
| `critical_value_95%` | **15,4943** |
| `cointegrated` | **true** |

### 5.3 Proxy Yahoo — `adf_results.json` + `MANIFEST.json` (run `ADF_EVIDENCE_20260324`)

| Campo | Valor |
|--------|--------|
| Dados | GC=F / SI=F, **1D**, merge **4079** linhas |
| ADF EG residual (full sample) | **p ≈ 0,191** |
| ADF spread OLS rolante (série completa, janela OLS 252 d) | stat **-6,991**, **p ≈ 7,75×10⁻¹⁰** |
| Chunks anuais (~252): taxa falha H0 a 5% | **87,5%** |
| ADF deslizante (252 obs no spread rolante): fração *p* \> 0,05 | **≈ 85,15%** (*n_windows* = 3576) |
| SHA-256 `GC_F_SI_F_daily.csv` | `f103889b33a4c9df13ec4ad56c781a10f2a55512081fe3c963b28834c7a9a7e7` |
| Ambiente reprodução | Python **3.11.9**, pandas **2.1.3**, statsmodels **0.14.5**, numpy **1.24.3** |

---

## 6. Motor de execução MT5 (V8.2.2 / V8.2.3 SUPREME)

### 6.1 Constantes e parâmetros (consolidado das versões partilhadas)

| Símbolo / variável | Valor |
|--------------------|--------|
| ASSET_Y / ASSET_X | XAUUSD / XAGUSD |
| MAGIC_NUMBER | 821000 |
| LOT_Y | 0,01 (exemplo) |
| DAILY_DD_LIMIT | −0,035 (CB sobre equity vs arranque) |
| MAX_Z_STOP | 5,0 |
| MIN_Z_ENTRY | 3,0 (V8.2.2) → **3,75** (V8.2.3 SUPREME) |
| MIN_Z_EXIT | 0,0 |
| TIMEOUT_BARS | **30** (V8.2.3) |
| COST_THRESHOLD | **19,0** |
| window_ols / ewma_span (motor matemático) | **500** / **100** |

### 6.2 Lógica causal (resumo algorítmico)

1. Obter barras M1; idealmente **merge por `time`** (inner); o código partilhado usou `copy_rates_from_pos` em paralelo — **risco** se timestamps divergirem.  
2. Para cada índice \(t \ge\) janela: OLS de \(Y\) sobre const+\(X\) usando **apenas** \([t-w, t-1]\); \(S_t = Y_t - \hat\alpha_t - \hat\beta_t X_t\).  
3. EWMA(span) sobre \(\{S\}\); \(\mu_{t|t-1}\), \(\sigma_{t|t-1}\) a partir de **iloc[-2]** (equivalente causal a não usar μ/σ do mesmo instante que inclui \(S_t\) na definição ingénua).  
4. \(Z_t = (S_t - \mu_{t|t-1})/(\sigma_{t|t-1}+\varepsilon)\).  
5. Entrada: \(\|Z\| \ge\) MIN_Z_ENTRY e \(|Z\cdot\sigma| >\) COST_THRESHOLD (unidade a documentar).  
6. Saída: \(Z\) cruza 0; ou \|Z\| \> MAX_Z_STOP com posição; ou timeout de barras; ou CB de drawdown.  
7. **Hedge:** razão de valor notion em USD (`trade_contract_size * bid`) para dimensionar lote em XAG.  
8. **Execução:** duas ordens IOC; rollback `close_all_by_magic` se segunda perna falhar.

### 6.3 Auditoria de código e documentação (pontos de não conformidade conhecidos)

| ID | Observação |
|----|------------|
| C1 | **Duas variantes** “oficiais” V8.2.3 (uma sem `check_health`/`log_audit`, outra com `BASE_DIR` hardcoded e CSV de auditoria). |
| C2 | Cabeçalho de código mencionou **ATR / trailing**; **não** há implementação ATR nas versões analisadas. |
| C3 | “OLS vectorizado” afirmado; implementação é **loop** + OLS/`order_send` — linguagem **exagerada**. |
| C4 | `close_all_by_magic` sem verificação sistemática de `retcode` por fecho. |
| C5 | CB “diário” baseado em **equity ao arranque do script**, não necessariamente dia civil. |
| C6 | `log_audit` numa variante **não** regista **ENTRY** (só algumas saídas). |
| C7 | Lista **“22 deficiências Weber”** referida em narrativas **não** está anexada como matriz com evidência por item neste pacote. |

*O código-fonte completo deve permanecer no repositório Git com commit hash referenciado no `MANIFEST` de release.*

---

## 7. Confronto: métricas declaradas vs evidência reproduzida

| Declaração (origem) | Evidência reproduzida neste pacote | Nota |
|----------------------|--------------------------------------|------|
| ADF spread *p* ≈ **8,46×10⁻²⁷** (relatórios internos V8.2.1) | *Slice* 478: spread rolante *p* **0,016**; proxy diário: *p* **~10⁻⁹** | **Ordens de grandeza diferentes** — amostra, TF e janelas distintas |
| Johansen **cointegrado** (`johansen_m1_results.json`, 50 k) | Recomputação em **478** barras: **não** a 95% | Exige **mesmo ficheiro** que originou trace **32,96** |
| Bloqueador 1 proxy Yahoo (REV3 Anexo C) | GC/SI trace **12,70** \< **15,49** | Coerente com **não** cointegração na especificação base proxy |
| Z entrada **3,75** (V8.2.3) | Z última barra *slice* **1,76** | Sem entrada neste extracto |

---

## 8. Gates G-A a G-D e matriz de decisão

**Gates** (síntese): **G-A** reproducibilidade (manifest + SHA + commit); **G-B** inferência (EG/Johansen/ADF bem especificados); **G-C** custos/microestrutura; **G-D** risco OOS / PF / DD.

**Estado global neste mestre:** **G-A** falha enquanto hashes do *live_feed* ≠ manifesto; **G-B** parcial (múltiplos testes com conclusões distintas); **G-C** parcial (19 pts sem tabela dimensional fechada); **G-D** não satisfeito para capital.

**Matriz resumida:** ver secção 8 do relatório *data lake* (reproduzida acima).

---

## 9. Limitações globais

- Nenhuma secção deste mestre **garante** lucro, ausência de *slippage*, nem “homologação total” sem acta e evidências alinhadas.  
- Proxy Yahoo **≠** série MT5 de execução.  
- Narrativas “SUPREME / Quantum / Aeroespacial” são **metáforas** — não substituem prova estatística nem *logs* de corretora.  
- Execução MT5 **não** foi validada neste ambiente.

---

## 10. Homologação (tabela)

| Função | Nome | Data | Assinatura |
|--------|------|------|------------|
| CQO | | | |
| CFO | | | |
| CTO | | | |
| CKO | | | |
| CEO | | | |

---

## 11. Índice de ficheiros, comandos de reproducibilidade e hashes

| Artefacto | Caminho |
|-----------|---------|
| **Este mestre** | `Documentacao_Processo/OMEGA_MASTER_UNIFICADO_COMPLETO_V823.md` |
| Protocolo REV3 (cópia) | `Documentacao_Processo/OMEGA_PROTOCOL_V8.2_MASTER_PROPOSAL_REV3_FINAL.md` |
| V8.2.1 (cópia) | `Documentacao_Processo/OMEGA_V821_RELATORIO_UNIFICADO_FINAL_AUDITADO_20260324.md` |
| Confronto *data lake* (cópia) | `Documentacao_Processo/RELATORIO_CONFRONTO_METRICAS_DATA_LAKE_V823.md` |
| Script evidência *data lake* | `data_lake/run_data_lake_evidence.py` |
| Métricas *data lake* | `data_lake/data_lake_metrics.json` |
| Script proxy ADF | `…/evidence_runs/ADF_EVIDENCE_20260324/run_adf_evidence.py` |
| Resultados proxy | `…/evidence_runs/ADF_EVIDENCE_20260324/adf_results.json` |
| Manifest proxy | `…/evidence_runs/ADF_EVIDENCE_20260324/MANIFEST.json` |

**Comandos:**

```bash
python "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\data_lake\run_data_lake_evidence.py"
python "c:\Users\Lenovo\.cursor\nebular-kuiper\Auditoria PARR-F\evidence_runs\ADF_EVIDENCE_20260324\run_adf_evidence.py"
```

---

**FIM DO DOCUMENTO MESTRE UNIFICADO** — `OMEGA-MASTER-UNIFIED-V823-20260324`

*Última consolidação: incorporação integral dos textos REV3, V8.2.1 e relatório de confronto do data lake; métricas JSON embutidas nas secções 5–7; extensões de gateway e auditoria de código na secção 6.*
