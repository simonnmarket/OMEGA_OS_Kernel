# Manifesto de evidência, lacunas e veto científico — OMEGA V8.2.x

**Instrumento:** norma interna de decisão (auditoria quantitativa)  
**Âmbito:** qualquer escalão que envolva alocação de capital, *go-live*, ou afirmação pública sobre desempenho ou “homologação”  
**Linguagem:** técnica; proibido uso institucional de vendas, metáforas de produto ou certificações implícitas não verificáveis  
**Data:** 2026-03-24  
**Versão:** 1.0  

---

## 0. Princípio reitor

**Nenhuma decisão positiva** (aprovação, escala, *sign-off*, comunicação externa de conformidade) é admissível **sem** cadeia de evidência que satisfaça os critérios deste manifesto.  
**Veto** é o **estado por defeito** quando qualquer critério obrigatório falha ou quando a afirmação excede o suporte empírico.

Este documento **não** avalia intenção ou esforço; avalia **reprodutibilidade**, **alinhamento objeto–teste–conclusão** e **ausência de ambiguidade dimensional**.

---

## 1. Nível de exigência (equivalente a revisão doctoral / MRM institucional)

Exige-se, para qualquer conclusão que suporte decisão:

1. **Registo prévio de hipóteses e objectos estatísticos** (o que é \(Y_t\), \(X_t\), o que é “spread”, que janela, que TF, que alinhamento temporal).  
2. **Identificação clara do estimador** (OLS rolante com exclusão de \(t\) na estimação de \(\beta_t\) ou não; EWMA com ou sem inclusão de \(S_t\) no mesmo instante na média/desvio).  
3. **Separação estrita** entre: (i) propriedades de **séries construídas**; (ii) **cointegração** no sentido de Engle–Granger / Johansen sobre **preços**; (iii) **desempenho económico** (PnL, PF, *drawdown*). São **domínios distintos**; inferência num **não** transfere automaticamente para outro.  
4. **Reprodutibilidade:** ficheiro de dados com **hash criptográfico**, *script* com versão, *seed* quando aplicável, e **output** arquivado (JSON/CSV) gerado pela mesma invocação documentada.  
5. **Sensibilidade:** quando uma conclusão depende de janela ou sub-amostra, reportar **variação** sob especificações adjacentes (ex.: janela OLS ±20%; ADF com `autolag` documentado).  
6. **Controlo de multiplicidade:** múltiplos testes, *chunks* e janelas deslizantes geram **taxa de falso positivo** elevada; conclusões globais exigem **correcção** ou **modelação hierárquica** explicitada.  
7. **Tradução económica:** qualquer limiar em “pontos” exige **definição física** (ativo, *tick size*, direcção *round-trip*, unidade de PnL).

Incumbe ao **proponente** provar; incumbe ao **revisor** vetar quando a prova não existe ou é **não sequitur**.

---

## 2. Taxonomia de estados de evidência

| Estado | Definição operacional |
|--------|------------------------|
| **PROVADO (P)** | Há *script* + dados com hash coincidente com manifesto + output arquivado; conclusão é **imediata** do output sob hipótese declarada. |
| **PARCIALMENTE PROVADO (PP)** | Existe evidência numa sub-amostra ou proxy; **não** há extensão justificada ao alvo de decisão (ex.: MT5 M1 *live*). |
| **NÃO PROVADO (NP)** | Afirmação existe em texto; **não** há artefacto verificável ou há **contradição** entre artefactos (hashes, *n*, especificação). |
| **REFUTADO PARCIALMENTE (RP)** | Evidência **contradiz** a afirmação numa especificação legítima (ex.: EG *p* alto em proxy enquanto se clama “cointegração global” sem qualificar). |
| **INADMISSÍVEL (I)** | Conclusão viola lógica (ex.: “PF ≥ 1,5” deduzido só de \(Z\) e custo agregado sem PnL). |

**Regra de decisão:** apenas **P** autoriza linguagem de “validado para o alvo”. **PP** autoriza “hipótese de trabalho com limites explícitos”. **NP**, **RP**, **I** implicam **veto** se a decisão depender dessa afirmação.

---

## 3. Quadro mestre — afirmações vs evidência (estado actual do dossiê)

*“Estado” reflecte o pacote analisado até 2026-03-24 (manifestos, JSON, *scripts* `run_data_lake_evidence.py`, `run_adf_evidence.py`, relatórios internos V8.2.1/REV3, código gateway colado em revisões).*

| # | Afirmação (como aparece ou implícita) | Estado | Base / lacuna |
|---|----------------------------------------|--------|----------------|
| 1 | *Dataset* MT5 M1 de **50 000** barras com SHA do `data_manifest_v82.json` está no *data lake* actual | **NP** | CSV `live_feed` com **478** linhas; **hashes diferentes** do manifesto. |
| 2 | Johansen: **cointegração** ao 95% em M1 com *trace* ≈ **32,96** | **PP** | JSON `johansen_m1_results.json` declara; **não reproduzido** no *slice* de 478 barras (*trace* ≈ **11,13** \< **15,49**). Falta ficheiro único de 50 k com hash alinhado. |
| 3 | ADF spread OLS rolante com **p ≈ 8,46×10⁻²⁷** (relatos internos) | **PP** | Número **não** replicado no *slice* 478; noutra execução spread rolante deu **p** ordem **10⁻²**–**10⁻⁹** conforme amostra/TF. Exige **mesmo** CSV e **mesmo** código commitado. |
| 4 | ADF em resíduos **Engle–Granger** (níveis) implica mesma conclusão que ADF no spread rolante | **I** | **Objectos estatísticos diferentes**; conclusões podem divergir **sem contradição lógica**; exige reportar **ambos**. |
| 5 | “Estacionariedade global do par” a partir de um único *p-value* | **NP** / **I** | *Non sequitur* se o teste não for sobre o vector adequado e amostra única; regimes podem falhar em sub-janelas (evidência proxy: alta fração de janelas com *p* \> 0,05). |
| 6 | Proxy Yahoo **substitui** decisão final sobre cointegração | **NP** (para *live*) | REV3 assume falha de proxy em especificação base; **basis** e TF diferentes de MT5. |
| 7 | **Z = 3,75** (ou 3,0) garante **PF líquido ≥ 1,5** ou lucro após **19** pts | **I** | Falta função de PnL medida; **19** pts sem conversão dimensional completa para USD por estratégia. |
| 8 | “Homologação total”, “100% auditado”, “22/22 deficiências” | **NP** | Sem matriz de requisitos com **ID**, evidência por linha, e *hash* de commit. |
| 9 | Gateway único V8.2.5 com ATR(14), CB diário civil, `volume_step`, *path* dinâmico | **NP** | Código apresentado como “V8.2.5” correspondia a classe **V8.2.1** sem ATR/CB activos; narrativa ≠ artefacto. |
| 10 | Paridade causal 1:1 Fase 2 ↔ gateway com **tick** `last` e EWMA `iloc[-1]` sobre spreads de *close* | **NP** | Mistura **bar** / **tick** e possível desvio da especificação EWMA **T−1** documentada em V8.2.1. |
| 11 | Hedge `lot_x = LOT_Y * beta` neutraliza risco de carteira | **NP** | Neutralidade **notional** exige **contrato × preço** (ou modelo explícito); *beta* OLS em preços **não** é por si prova de neutralidade de margem. |
| 12 | Execução de *pairs* **atómica** com duas `order_send` | **NP** | Atomicidade **não** existe; exige protocolo de **compensação** e verificação da segunda perna. |
| 13 | *Circuit breaker* −3,5% diário activo | **NP** | Em revisão de código, constantes definidas **sem** uso no *loop*; “diário” exige baseline **data civil** documentada. |
| 14 | Bloqueador 1 REV3 (Johansen proxy GC/SI base spec) | **P** (no âmbito **declarado** REV3) | Anexo C: *trace* **12,70** \< **15,49** — **não** cointegração a 95% nessa especificação. |

---

## 4. Critérios de veto (aplicáveis a qualquer patamar)

**Veto automático (sem exceção por retórica):**

- **V1 — Linhagem de dados:** manifesto SHA ≠ ficheiro presente OU *n* diferente sem novo manifesto assinado digitalmente no repositório.  
- **V2 — Conclusão estatística fora do objecto testado:** ex.: “cointegração” concluída só com ADF no spread rolante, sem EG/Johansen nos preços **na mesma amostra de decisão**.  
- **V3 — Dimensionalidade:** custos em “pontos” sem tabela de conversão para a unidade de PnL da estratégia.  
- **V4 — Código vs documento:** checklist de segurança (CB, *timeout*, *rollback*, *retcode*) afirmada no texto **ausente** no *commit* referenciado.  
- **V5 — Desempenho:** afirmação numérica de PF/Sharpe/*drawdown* **sem** *backtest* reprodutível e **OOS** pré-registado.  
- **V6 — Multiplicidade não tratada:** selecção *post hoc* de janela/limiar sem robustez documentada.

**Veto condicionado (até prova em contrário):**

- **V7 — Amostra curta:** \(n\) inferior ao mínimo pré-definido para potência do teste (declarar *n_min* por tipo de teste).  
- **V8 — Regime:** fração elevada de sub-janelas em que se **não** rejeita raiz unitária no objecto usado para *trading* — exige modelo de **regime** ou filtro documentado, não adjetivos.

---

## 5. Formato obrigatório de apresentação de resultados processados

Para **cada** resultado numérico citado em acta:

1. **H0 e H1** explícitas (ou definição equivalente do teste).  
2. **Estatística**, *p-value* ou intervalo, **nobs**, **versão** do pacote (`statsmodels`, etc.).  
3. **Identificador do ficheiro** de entrada (caminho relativo ao repositório) + **SHA-256**.  
4. **Comando único** ou *notebook* com célula de execução que regenera o output.  
5. **Figura ou tabela** de sensibilidade quando o resultado for limítrofe (*p* ∈ (0,01 ; 0,10)).

Documentos que contenham apenas narrativa, superlativos ou analogias **não** contam como evidência sob este manifesto.

---

## 6. Síntese para a sala — o que está fechado e o que não está

**Fechado (P) no sentido estrito:**

- Existência de **contradição documentada** entre manifesto 50 k e *slice* 478 (hashes e *n*).  
- Sob REV3, **falha** de Johansen proxy GC/SI em especificação base **anexada** ao protocolo.  
- Sob *scripts* auditados, **divergência** entre ADF EG e ADF spread rolante **conforme esperado** por construção diferente do objecto.

**Não fechado (NP / I) para decisão de capital ou *live*:**

- Paridade completa **dados ↔ motor ↔ gateway** com um único *commit* e um único *dataset* hasheado.  
- Prova de **PnL líquido** e **PF** após custos no mesmo pipeline que o *live*.  
- Implementação verificada de **todas** as salvaguardas de risco descritas em relatórios “SUPREME” / “FINAL”.

---

## 7. Disposição final

1. Este manifesto **prevalece** sobre comunicações internas que usem linguagem de produto ou *sign-off* sem anexos que satisfaçam a §5.  
2. Qualquer excepção temporária (ex.: demo) deve ser rotulada **“sem evidência para decisão de capital”** por escrito.  
3. Revisões futuras: incrementar **apenas** o quadro da §3 e anexar novos *hashes*; **proibido** apagar linhas **NP** sem novo estado **P** com artefactos.

---

**FIM DO MANIFESTO**

*Documento de governação técnica. Não constitui aconselhamento jurídico, regulatório nem de investimento.*
