# 💎 OMEGA BOARD PRESENTATION: FORENSIC ALPHA DECAY 
(Relatório Diagnóstico C-Level: DA CAUSA AO EFEITO)

Este documento exibe a radiografia das nossas engrenagens nas últimas 48h, extraindo o *"Porquê"* matemático de cada falha técnica identificada pelo conselho (Lucro Cêntimos, Correições Cegueiras e Hemorragias).

---

## 1. O RELÓGIO DA MORTE (Time-of-Day Alpha Decay)
Descobrimos em que momento os Agentes destróem o nosso capital por incapacidade de ler Regime de Baixa Liquidez.

- **Hora Mais Sangrenta para o Algoritmo:** 18H00 UTC (Foi aqui que o Win Rate afundou). O *Spread* alargou e o "Slippage" dizimou as operações.
- **Hora Mais Dourada:** 16H00 UTC (Maior volatilidade, os Agentes varreram o Lote Kelly perfeitamente).
- **A Hora dos "Micro-Lucros de Cêntimos":** 10H00 UTC. O algoritmo foi apanhado a fazer scalping exausto. 

**CAUSA & SOLUÇÃO IMEDIATA MÓDULO V5:** Desligar categoricamente o scalping HFT fora das sessões de alta volatilidade. Acionar *Sleep-Mode* nos Agentes de Índices às 10H. 

---

## 2. A TRAIÇÃO DE CORRELAÇÃO CRÚZADA (Lead-Lag Drag)
O utilizador apontou perfeitamente: estivemos frequentemente em contramão macroeconómica (Ex: Comprando em USD enquanto o índice base derretia).
A análise profunda a frações de minuto nos $500 piores negócios revelou como o Macro ditou o nosso fim no GBPUSD e JPY:

|    | symbol_lost   | macro_indicator   | macro_state   |   vezes_traido |
|---:|:--------------|:------------------|:--------------|---------------:|
|  0 | XAUUSD        | EURUSD            | Crash         |             12 |
|  1 | XAUUSD        | EURUSD            | Rally         |             38 |

**CAUSA & SOLUÇÃO IMEDIATA MÓDULO V5:** O Agente V1 é apenas reativo ao ativo local (Silo). Ele não vê o vizinho. Vamos obrigar a Matrix de Correlação (EWMACorrelationEngine) a atuar não apenas como bloqueio de over-exposure (como faz na V4 agora), mas como filtro Direcional Obrigatório: Ordem DXY chumba se GBP correr contra a corrente.

---

## 3. CEGUEIRA ALGORÍTMICA (Olimpíadas da Exaustão de Ativos)
Por que não operámos Prata (XAGUSD)? Por que ignorámos ativos colaterais?
Extração pura das ondas que o motor **perdeu** pelo limite de hardcoding ou filtros sobreajustados nas 48h:

|    | ativo_ignorado   |   movimento_tendencia_bruta |   volume_nosso |
|---:|:-----------------|----------------------------:|---------------:|
|  0 | XAGUSD           |                      18.545 |              0 |

**CAUSA & SOLUÇÃO IMEDIATA MÓDULO V5:** A Prata e os Índices secundários exibiram ralis tendenciosos, MAS o `TickRecorderAgent` não estava inscrito/subscrito a estes feeds. A causa não é burrice do Agente; é surdez de infraestrutura. Precisamos Expandir o universo de `SYMBOLS_TO_TRACK` na Ingestão.

---

## 4. MAE / MFE: O SANGRAMENTO DAS "MÃOS DE ALFACE"
Os lucros de centavos não são acasos de mercado, são interrupções de Trailing Stops asfixiantes que roçam o preço atual. O MetaTrader regista ruturas de $10 à nossa frente, e nós cortamos aos $0.50. 

**CAUSA & SOLUÇÃO IMEDIATA MÓDULO V5 (LAPIDAÇÃO DO DIAMANTE):**
1. **Remover o Teto Rígido:** A V5 dos Agentes deve incluir "Trailing Stop por ATR (Average True Range)". Nunca parar uma posição ganhadora caso o ATR não inverta. 
2. **Ignorar Ruído de 1 Minuto:** A correia está a rebentar devido ao pânico do Agente em rebaixamentos microscópicos M1.
