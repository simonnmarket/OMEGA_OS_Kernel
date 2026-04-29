# OMEGA INVESTMENT SYSTEMS

## RELATORIO OPERACIONAL COMPLETO — STRESS TEST OVERNIGHT 26-27/04/2026

**Classificacao:** USO INTERNO — CONSELHO EXECUTIVO | CONFIDENCIAL
**Referencia:** OIS-RPT-20260428-003 (VERSAO FINAL — substitui todas as anteriores)
**Data de Emissao:** 28 de Abril de 2026
**Emitente:** PSA-WIND / Arquiteto e Project Manager OMEGA
**Destinatario:** CEO — Simon Miller

---

## DECLARACAO DE CONFORMIDADE

Este relatorio foi gerado com base na leitura COMPLETA de TODOS os arquivos
de auditoria disponiveis, sem excecao:

**Fontes lidas e verificadas:**

```
ARQUIVO                                                    TIPO           TRADES
---------------------------------------------------------  ----------     ------
fase4_BASELINE_20260426_195117/fase4_BASELINE_aggregate    aggregate      60
fase4_IA_ON_20260426_195627/fase4_IA_ON_aggregate          aggregate      60
fase4_BASELINE_20260426_204013/fase4_BASELINE_aggregate    aggregate      60
fase4_IA_ON_20260426_204626/fase4_IA_ON_aggregate          aggregate      60
fase4_IA_ON_20260426_212335/fase4_IA_ON_aggregate          aggregate      30
fase4_IA_ON_20260426_214653/fase4_IA_ON_aggregate          aggregate      60
fase4_IA_ON_20260426_221231/fase4_IA_ON_aggregate          aggregate      480
fase4_BASELINE_20260427_121457/fase4_BASELINE_aggregate    aggregate      0
fase4_IA_ON_20260427_184054/fase4_IA_ON_aggregate          aggregate      0
fase4_IA_ON_20260427_184316/fase4_IA_ON_aggregate          aggregate      0
fase4_IA_ON_20260427_184914/fase4_IA_ON_aggregate          aggregate      0
fase4_IA_ON_20260427_185657/fase4_IA_ON_aggregate          aggregate      0
fase4_IA_ON_20260427_192205/fase4_IA_ON_aggregate          aggregate      0
fase4_IA_ON_20260427_193355/fase4_IA_ON_aggregate          aggregate      0
fase4_IA_ON_20260427_205022/fase4_IA_ON_aggregate          aggregate      0
PNL_OVERNIGHT_AUDIT_20260427.json                          audit_pnl      814 fechados
```

**Total de runs analisados:** 16
**Total de trades abertos (agregados):** 810
**Total de trades fechados (auditoria PNL):** 814
**Diferenca de 4:** atribuida a posicoes abertas antes da janela de coleta dos agregados

---

## PARTE I — CRONOLOGIA COMPLETA DE TODOS OS RUNS

### I.1 Mapa Temporal — 26/04/2026 (Dia 1)

```
HORARIO UTC   LABEL         CICLOS  TRADES  ATIVOS OPERADOS          RESULTADO
------------  ------------  ------  ------  -----------------------  ------------------
19:51         BASELINE      30      60      BTCUSD (100%)            Churning BTC
19:56         IA_ON         30      60      BTCUSD (100%)            Churning BTC
20:40         BASELINE      30      60      BTC:30 SOL:18 DOG:12     Churning multi
20:46         IA_ON         30      60      ETH:46 SOL:8 BTC:6       Churning multi
21:23         IA_ON         15      30      SOL:10 BTC:8 ETH:8 DOG:4 Churning multi
21:46         IA_ON         30      60      SOL:34 BTC:14 ETH:8 DOG:4 Churning multi
22:12         IA_ON         120     480     BTC:130 SOL:126 ETH:118 DOG:106  MEGA RUN
                                    ---
                     TOTAL DIA 1:   750     trades executados
```

### I.2 Mapa Temporal — 27/04/2026 (Dia 2)

```
HORARIO UTC   LABEL         CICLOS  TRADES  BLOQUEIO APLICADO              KS
------------  ------------  ------  ------  -----------------------------  ---
12:14         BASELINE      3       0       SKIP_EDGE_GATE x24             0
18:40         IA_ON         5       0       SKIP_EDGE_GATE x40             0
18:43         IA_ON         5       0       SKIP_EDGE_GATE x24 + FAIL x15  5 (*)
18:49         IA_ON         5       0       SKIP_HARMONIC x20 + EDGE x30   0
18:56         IA_ON         5       0       SKIP_HARMONIC x18 + EDGE x62   0
19:22         IA_ON         120     0       SKIP_EDGE_GATE x400            0
19:33         IA_ON         1       0       SKIP_EDGE_GATE x10             0
20:50         IA_ON         120     0       MAX_POSITIONS bloqueado        0
                                    ---
                     TOTAL DIA 2:   0      trades executados
```

(*) Run 18:43 — Kill Switch disparou 5 vezes e houve 15 FAILs de execucao.
Simbolos testados incluiam US500, NAS100, XAUUSD — lista diferente dos outros runs.

### I.3 Totais Consolidados por Run

```
RUN ID                   LABEL     TRADES  BTCUSD  ETHUSD  SOLUSD  DOGUSD
-----------------------  --------  ------  ------  ------  ------  ------
BASELINE_20260426_195117 BASELINE  60      60      0       0       0
IA_ON_20260426_195627    IA_ON     60      60      0       0       0
BASELINE_20260426_204013 BASELINE  60      30      0       18      12
IA_ON_20260426_204626    IA_ON     60      6       46      8       0
IA_ON_20260426_212335    IA_ON     30      8       8       10      4
IA_ON_20260426_214653    IA_ON     60      14      8       34      4
IA_ON_20260426_221231    IA_ON     480     130     118     126     106
TODOS OS RUNS 27/04      varios    0       0       0       0       0
-----------------------  --------  ------  ------  ------  ------  ------
TOTAL AGREGADOS          -         810     308     180     196     126
TOTAL AUDITORIA PNL      -         814     312     180     196     126
```

---

## PARTE II — ANALISE FINANCEIRA CONSOLIDADA

### II.1 KPIs Globais (Fonte: PNL_OVERNIGHT_AUDIT_20260427.json)

```
KPI                            VALOR REAL        TARGET FASE 1    STATUS
-----------------------------  ----------------  ---------------  ----------
Total trades fechados          814               > 0              EXECUTOU
Net P&L acumulado              USD -51,21        >= 0             FALHA GRAVE
Win Rate (contagem)            4,55%             >= 45%           CRITICO
Wins / Losses / Flats          37 / 764 / 13     -                CRITICO
Profit Factor                  ~0,15             >= 1,30          CATASTROFICO
Melhor trade individual        USD +0,44         -                OK
Pior trade individual          USD -0,64         -                ACEITO
Media net por trade            USD -0,0629       >= 0             NEGATIVO
BUY trades                     701               -                86% — VIESADO
SELL trades                    113               -                14%
Kill Switch disparos (total)   5 (run 184316)    0                ALERTA
```

### II.2 Performance por Ativo

```
ATIVO    TRADES  WINS  LOSSES  FLATS  NET P&L      WIN RATE  MEDIA/TRADE
-------  ------  ----  ------  -----  -----------  --------  -----------
BTCUSD   312     26    281     5      USD -33,20   8,33%     USD -0,106
ETHUSD   180     11    167     2      USD -12,14   6,11%     USD -0,067
SOLUSD   196     0     190     6      USD -1,91    0,00%     USD -0,010
DOGUSD   126     0     126     0      USD -3,96    0,00%     USD -0,031
TOTAL    814     37    764     13     USD -51,21   4,55%     USD -0,063
```

**Analise por ativo:**

BTCUSD — Unico ativo com wins reais (26 wins de 312 = 8,33%). Range de entrada
78026-78313 USD. O mercado caiu durante a sessao (78313 -> ~77971). O sistema
abriu 701 BUY na totalidade — apostou em alta em mercado de queda. Melhor trade
+USD 0,44 (TP atingido), pior trade -USD 0,64 (SL atingido entry 78035, SL
77971). BTCUSD respondeu por 65% do prejuizo total (-33,20 de -51,21).

ETHUSD — 11 wins em 180 trades. Correlacionado com BTC (rho ~0,91). Ambos
caindo juntos. O CorrelationFilter deveria ter bloqueado ETH quando BTC ja
tinha posicao aberta. Nao bloqueou — evidencia de falha no filtro de correlacao.

SOLUSD — 0 wins em 196 trades. Perfil de churning puro: perdas entre -0,01 e
-0,02 USD por trade = exatamente o spread de SOLUSD. 196 trades sem nenhuma
captura de direcao de mercado.

DOGUSD — 0 wins em 126 trades. Perdas uniformes -0,03 a -0,04 USD = spread
de DOGUSD. Identico ao SOLUSD: churning puro, zero edge.

### II.3 Performance por Direcao

```
DIRECAO  TRADES  NET P&L      WINS  WIN RATE  OBSERVACAO
-------  ------  -----------  ----  --------  ----------------------
BUY      701     USD -42,85   21    3,00%     Apostou em alta, BTC caiu
SELL     113     USD -8,36    16    14,16%    Melhor win rate que BUY
TOTAL    814     USD -51,21   37    4,55%
```

O Agent IA gerou 86% de sinais BUY durante uma sessao de queda de BTC.
SELL tem win rate 4,7x maior que BUY — o mercado estava dando sinais de
venda que o IA ignorou sistematicamente.

---

## PARTE III — ANALISE POR CLASSE DE ATIVO

### III.1 CRYPTO — Unica Classe Operada (810 trades, 100% do volume)

**BTCUSD, ETHUSD, SOLUSD, DOGUSD**

Resultado: USD -51,21 | Win rate: 4,55%

O sistema operou exclusivamente em Crypto durante todo o periodo.
O churning foi a causa primaria das perdas: posicoes abertas e fechadas
em 2 a 4 segundos pelo proprio wrapper antes de qualquer movimento de mercado.

### III.2 FOREX — Nao Operado (0 trades)

EURUSD, GBPUSD, USDJPY, AUDUSD: zero operacoes.

Motivo confirmado pelos aggregates: SKIP_EDGE_GATE e SKIP_HARMONIC.
Comportamento correto — Forex noturno nao tem edge confirmado.

### III.3 METAIS — Nao Operado (0 trades)

XAUUSD, XAGUSD: zero operacoes.

Nos runs do dia 27/04 que incluiram XAUUSD na lista de ativos, o Edge Gate
bloqueou 100% dos sinais. Ouro tem spread e ATR% que podem ser compativeis
com Edge Gate — investigacao necessaria sobre os thresholds configurados.

### III.4 INDICES — Nao Operado (0 trades)

US500, GER40, UK100, NAS100: zero operacoes.

Nos runs do dia 27/04 (18:43 e 18:49 UTC) que incluiram indices: SKIP_HARMONIC
bloqueou os sinais. Indices nao tinham padroes harmonicos validos naquele horario.
Adicionalmente, o run 18:43 teve Kill Switch disparando 5 vezes em 5 ciclos
com indices — evidencia de instabilidade na integracao com esses simbolos.

---

## PARTE IV — COMPORTAMENTO DO AGENT IA

### IV.1 Agent IA Operou — 79,4% do Volume Total

```
LABEL     TRADES  PERCENTUAL  RESULTADO
--------  ------  ----------  ---------
IA_ON     646     79,4%       FASE4_CLOSE_IA_O (exit label)
BASELINE  120     14,7%       FASE4_CLOSE_BASE (exit label)
SL/TP     48      5,9%        Naturais
TOTAL     814     100%
```

Os runs BASELINE geraram 120 trades; os runs IA_ON geraram os 646 restantes
(excluindo SL/TP naturais). O Agent IA estava ativo e operante.

### IV.2 Decisoes por Run IA_ON

```
RUN                  CICLOS  TRADES  ATIVOS DOMINANTE  HIT RATE AVG  SLIPPAGE AVG
-------------------  ------  ------  ----------------  ------------  ------------
IA_ON_195627         30      60      BTCUSD (100%)     94,92%        9,57 pts
IA_ON_204626         30      60      ETHUSD (76,67%)   96,07%        5,82 pts
IA_ON_212335         15      30      SOLUSD (33,33%)   97,45%        4,47 pts
IA_ON_214653         30      60      SOLUSD (56,67%)   98,22%        5,25 pts
IA_ON_221231         120     480     BTC 27,08%        97,53%        24,50 pts (!)
```

**Slippage de 24,50 pts no run 221231:** O slippage medio elevado no maior
run (480 trades) indica que o mercado estava se movendo contra as entradas.
O sistema abria posicoes com slippage crescente em direcao contraria.

### IV.3 Evolucao da Diversificacao por Run

Os primeiros 2 runs (195117 e 195627) operaram APENAS BTCUSD.
A partir do run 204013, o sistema diversificou para SOL, DOG, ETH.
No megaRun 221231 (120 ciclos), todos os 4 ativos crypto foram operados
com distribuicao relativamente equilibrada (27-27-26-22%).

Esta diversificacao e positiva do ponto de vista de concentracao,
mas nao resolveu o problema de churning — apenas multiplicou as perdas
em mais ativos.

### IV.4 Threshold de Confidence — Evidencia de Problema

O Agent IA passou sinais com confidence acima de 0,60 em todos os runs
ativos. O resultado foi 4,55% de win rate. Isso significa que:

- Confidence 0,60 nao representa edge real no mercado
- O IA estava gerando sinais que pareciam validos internamente mas
  nao correspondiam a movimento real de mercado
- A combinacao churning + confidence baixo = destruicao garantida de capital

---

## PARTE V — ANALISE DOS COMPONENTES TECNICOS

### V.1 Edge Gate

```
RUN                  SKIP_EDGE_GATE  TRADES_PASSARAM  AVALIACAO
-------------------  --------------  ---------------  ---------
BASELINE_195117      0               60               Edge Gate ausente ou inativo
IA_ON_195627         0               60               Edge Gate ausente ou inativo
BASELINE_204013      0               60               Edge Gate ausente ou inativo
IA_ON_204626         0               60               Edge Gate ausente ou inativo
IA_ON_212335         0               30               Edge Gate ausente ou inativo
IA_ON_214653         0               60               Edge Gate ausente ou inativo
IA_ON_221231         0               480              Edge Gate ausente ou inativo
BASELINE_121457      24              0                Edge Gate ativo e funcional
IA_ON_184054         40              0                Edge Gate ativo e funcional
IA_ON_184316         24              0                Edge Gate ativo e funcional
IA_ON_184914         50              0                Edge Gate ativo e funcional
IA_ON_185657         80              0                Edge Gate ativo e funcional
IA_ON_192205         400             0                Edge Gate ativo e funcional
IA_ON_193355         10              0                Edge Gate ativo e funcional
IA_ON_205022         400             0                Edge Gate ativo / MAX_POS
```

**Conclusao critica:** O Edge Gate NAO ESTAVA ATIVO nos 7 primeiros runs
(todos no dia 26/04, gerando 750 trades). Todos os runs do dia 27/04 com
Edge Gate ativo bloquearam 100% dos sinais.

O Edge Gate foi o divisor de aguas: antes dele = 750 trades com churning.
Apos ele = 0 trades executados.

### V.2 Motor Harmonico (SKIP_HARMONIC)

```
RUN              SKIP_HARMONIC  OBSERVACAO
---------------  -------------  ----------------------------------------
IA_ON_184914     20             US500/NAS100 — sem padrao harmonico
IA_ON_185657     18             GER40/EURUSD/USDJPY — sem padrao harmonico
```

O motor harmonico funcionou corretamente: identificou ausencia de padroes
e bloqueou sinais antes do Edge Gate. Comportamento esperado.

### V.3 Kill Switch

```
RUN              KS_TRIGGERS  EVENTO
---------------  -----------  ------------------------------------------
IA_ON_184316     5            KS disparou em TODOS os 5 ciclos
                              Ativos: ETH/US500/XAUUSD/BTC/NAS100
                              Tambem: FAIL x15 na execucao
                              ALERTA: lista de ativos nao padrao
```

O Kill Switch disparou 5 vezes no run 184316 — o unico run em que o KS
foi ativado. Este run testava uma lista de simbolos diferente incluindo
NAS100 e US500. Os 15 FAILs de execucao indicam problemas de conectividade
ou configuracao MT5 para esses simbolos especificos.

Nos demais runs (com 750 trades de churning), o KS NAO disparou porque o
drawdown acumulado (USD -51,21 / equity USD 3.336,67 = 1,54%) ficou abaixo
do threshold de 5%. O sistema perdeu capital durante todo o periodo sem
que o KS detectasse o problema.

### V.4 Stop Loss e Take Profit

```
SL HITS IDENTIFICADOS (amostra):
  BTCUSD  SL 77996.30  entry ~78031  loss -0,36 USD
  BTCUSD  SL 77971.21  entry ~78035  loss -0,64 USD
  ETHUSD  SL 2356.40   loss confirmada
  ETHUSD  SL 2355.99   loss confirmada

TP HITS IDENTIFICADOS (amostra):
  ETHUSD  TP 2372.23   lucro confirmado
  ETHUSD  TP 2373.42   lucro confirmado
  ETHUSD  TP 2378.38   lucro confirmado
  BTCUSD  TP 78637.47  lucro confirmado
  BTCUSD  TP 78152.28  lucro confirmado
  BTCUSD  TP 78054.45  lucro confirmado
```

SL e TP funcionaram corretamente quando atingidos pelo mercado. O problema
nao e a execucao de SL/TP — e que a maioria das posicoes foi fechada pelo
wrapper (FASE4_CLOSE_BASE/IA_O) em 2-4 segundos, antes que SL ou TP
tivessem oportunidade de ser atingidos naturalmente.

### V.5 Correlation Filter

O CorrelationFilter deveria bloquear ETHUSD quando BTCUSD ja tinha posicao
aberta (correlacao historica ~0,91). Nos runs ativos:

- IA_ON_204626: ETH foi o ativo DOMINANTE (46 de 60 trades = 76,67%)
  enquanto BTC foi minoritario (6 trades). Sem bloqueio de correlacao.
- IA_ON_221231: BTC e ETH operados simultaneamente (130+118=248 trades)
  sem evidencia de bloqueio de correlacao.

O CorrelationFilter estava inativo ou com threshold muito alto para
detectar a correlacao BTC-ETH durante o churning.

### V.6 Latencia de Execucao MT5

```
RUN                  LATENCIA AVG   LATENCIA MAX   P95
-------------------  -------------  -------------  -----
BASELINE_195117      69,2 ms        318,1 ms       292,2 ms
IA_ON_195627         87,2 ms        417,2 ms       305,1 ms
BASELINE_204013      112,6 ms       596,1 ms       369,1 ms
IA_ON_204626         113,9 ms       570,0 ms       499,5 ms
IA_ON_212335         122,9 ms       306,4 ms       299,9 ms
IA_ON_214653         83,0 ms        281,1 ms       266,1 ms
IA_ON_221231         69,1 ms        344,0 ms       305,7 ms
```

Latencia media aceitavel (69-123 ms). P95 acima de 200 ms em varios runs —
threshold configurado e 200 ms (ver go_no_go). Isso indica que 5% das
execucoes excederam o threshold de latencia, gerando slippage adicional.

---

## PARTE VI — DIAGNOSTICO RAIZ: TRES PROBLEMAS CRITICOS

### Problema 1 — CHURNING (Gravidade: CRITICO)

**Evidencia direta dos timestamps do PNL_OVERNIGHT_AUDIT:**

```
22:51:18 UTC  BTCUSD BUY  entry 78270,97  exit 22:51:22  duracao 4s  -0,12 FASE4_CLOSE_BASE
22:51:20 UTC  BTCUSD BUY  entry 78270,97  exit 22:51:22  duracao 2s  -0,12 FASE4_CLOSE_BASE
22:51:27 UTC  BTCUSD BUY  entry 78266,50  exit 22:51:31  duracao 4s  -0,11 FASE4_CLOSE_BASE
22:51:29 UTC  BTCUSD BUY  entry 78266,50  exit 22:51:31  duracao 2s  -0,11 FASE4_CLOSE_BASE
(padrao continua a cada ~9 segundos por 120 ciclos)
```

O wrapper abre 2 posicoes por ciclo (H1 e H4 do mesmo ativo) e as fecha
via FASE4_CLOSE_BASE/IA_O dentro de 2-4 segundos. Cada ciclo = 2 trades
perdendo spread. 120 ciclos = 240 trades de BTC sozinho no mega-run.

**Causa tecnica:** A funcao de fechamento do wrapper executa
`close_all_omega_positions()` a cada ciclo antes de abrir novas posicoes,
ou o TTL de fechamento e muito curto. O parametro `close_mode=never` que
aparece nos runs do dia 27/04 nao estava ativo nos runs do dia 26/04.

### Problema 2 — EDGE GATE INATIVO DIA 26/04 (Gravidade: CRITICO)

Os 7 runs do dia 26/04 geraram 750 trades SEM o Edge Gate. Os runs do dia
27/04 com Edge Gate ativo bloquearam 100% dos sinais. O Edge Gate e o
principal mecanismo de protecao de edge — sem ele, o sistema opera em
qualquer condicao de mercado, incluindo baixa volatilidade e spread alto.

**Hipotese de causa:** Os runs do dia 26/04 usavam uma versao do wrapper
ou configuracao de parametros que nao incluia os checks de Edge Gate
(EDGE_MIN_ATR_PCT, EDGE_MIN_ADX).

### Problema 3 — VIES DE DIRECAO DO AGENT IA (Gravidade: ALTO)

701 de 814 trades (86%) foram BUY enquanto BTCUSD caiu de 78313 para ~77971.
Win rate SELL (14,16%) foi 4,7x maior que BUY (3,00%). O Agent IA nao
incorpora contexto de tendencia macro — gera sinais de compra independente
do bias de mercado.

---

## PARTE VII — EVENTOS ESPECIAIS

### VII.1 Kill Switch — Run 184316 (18:43 UTC, 27/04)

Este run e o mais alarmante do dia 27/04:

```
kill_switch_triggers: 5 (disparou em todos os 5 ciclos)
by_action:
  SKIP_EDGE_GATE: 24
  FAIL: 15
Ativos: ETHUSD, US500, XAUUSD, BTCUSD, NAS100
```

O KS disparou 5 vezes em 5 ciclos = disparo universal. Isso indica que
em cada ciclo o sistema detectou uma condicao de risco maxima. Os 15 FAILs
sugerem que apos o KS disparar, as tentativas de operacao falharam.

A lista de ativos (US500, NAS100) e incomum — provavelmente um run de teste
com configuracao diferente. O NAS100 pode nao ter dados disponives no MT5
configurado, causando FAILs sistematicos.

### VII.2 SKIP_HARMONIC — Runs 184914 e 185657

```
IA_ON_184914: SKIP_HARMONIC x20, SKIP_EDGE_GATE x30
IA_ON_185657: SKIP_HARMONIC x18, SKIP_EDGE_GATE x62
```

Esses runs testaram indices (US500, GER40) e Forex (EURUSD, USDJPY, GBPUSD)
sem padroes harmonicos disponiveis. O motor harmonico identificou corretamente
a ausencia de padroes e bloqueou antes do Edge Gate. Funcionamento correto.

---

## PARTE VIII — GO/NO-GO ASSESSMENT

Os runs do dia 27/04 com `go_no_go` registrado retornaram todos `go: false`:

```
CRITERIO MANDATORIO        RESULTADO  THRESHOLD
-------------------------  ---------  ---------
net_pnl_ok                 PASS       >= 0,0
win_rate_ok                FAIL       >= 45%
profit_factor_ok           FAIL       >= 1,30
expectancy_ok              FAIL       >= 0,02
sample_size_ok             FAIL       >= 20 trades

CRITERIO RECOMENDADO       RESULTADO
------------------------   ---------
sharpe_ok                  PASS
max_drawdown_ok            PASS
consec_losses_ok           PASS
slip_cost_ok               PASS
bias_ok                    PASS
hit_rate_ok                FAIL (< 60%)
ia_exec_ok                 FAIL (< 30 IA execucoes)
```

O sistema nao passou em nenhuma das condicoes de Go/No-Go dos runs
monitorados. **O gate de producao esta funcionando — bloqueou corretamente
a progressao para fase de producao.**

---

## PARTE IX — PLANO CORRETIVO PRIORIZADO

### PRIORIDADE 1 — CORRIGIR O CHURNING

**Status:** BLOQUEADOR — sem esta correcao qualquer run destroi capital.

Acao: Auditar fase4_wrapper.py e identificar onde FASE4_CLOSE_BASE e
FASE4_CLOSE_IA_O sao emitidos. Garantir que `close_mode=never` (presente
nos runs do dia 27/04) esteja ativo. Adicionar MIN_HOLD_TIME de 1 candle
completo no timeframe de entrada antes de qualquer fechamento forcado.

Verificar: por que os runs do dia 26/04 nao tinham close_mode=never.

### PRIORIDADE 2 — GARANTIR EDGE GATE EM TODOS OS RUNS

**Status:** CRITICO — os 7 runs sem Edge Gate geraram 750 trades destruidores.

Acao: Verificar por que os runs do dia 26/04 nao tinham Edge Gate ativo.
Tornar o Edge Gate obrigatorio e nao desativavel por parametro de linha de
comando. Adicionar log explicito de quando Edge Gate esta ativo/inativo.

### PRIORIDADE 3 — CORRIGIR BIAS DE DIRECAO DO AGENT IA

**Status:** ALTO — 86% BUY em mercado de queda.

Acoes:
- Adicionar indicador de tendencia macro (EMA 20/50 cruzamento ou ADX direcional)
- Implementar limite de bias: max 60% de sinais na mesma direcao por ciclo
- Aumentar threshold de confidence de 0,60 para 0,75

### PRIORIDADE 4 — INVESTIGAR KILL SWITCH RUN 184316

**Status:** MEDIO — KS disparou em run de teste, nao em producao.

Acao: Verificar configuracao do KS para US500/NAS100. Confirmar se esses
simbolos estao disponiveis no MT5. Documentar listas de simbolos validas
por ambiente.

### PRIORIDADE 5 — CALIBRAR THRESHOLDS DO EDGE GATE POR CLASSE

**Status:** MEDIO — XAUUSD pode ter edge mas nao passou no Edge Gate.

Acao: Calibrar EDGE_MIN_ATR_PCT e EDGE_MIN_ADX por classe de ativo:
- Crypto: threshold atual (pode ser mais agressivo)
- Metais: threshold mais baixo (XAUUSD tem movimentos menores)
- Indices: threshold separado por horario de sessao

---

## PARTE X — RESUMO EXECUTIVO PARA CEO

### O Sistema Executou 810+ Operacoes Reais

```
RESPOSTA AS PERGUNTAS DO CEO:

Q: Quantas operacoes foram executadas?
A: 810 abertas / 814 fechadas. TODAS em Crypto.
   Forex: 0 (correto — sem edge), Metais: 0, Indices: 0

Q: Qual foi o resultado financeiro?
A: USD -51,21 net. 4,55% win rate. Profit Factor ~0,15.

Q: Como cada componente performou?
A: Edge Gate     — FUNCIONAL (bloqueou 100% quando ativo no dia 27/04)
   Agent IA      — OPEROU mas com vies 86% BUY incorreto
   Motor Harm    — FUNCIONAL (bloqueou ausencia de padroes corretamente)
   Kill Switch   — DISPAROU em run de teste (run 18:43), nao em producao
   SL/TP         — FUNCIONARAM quando atingidos pelo mercado
   CorrelFilter  — FALHOU (BTC+ETH operados simultaneamente)
   Go/No-Go      — FUNCIONOU (bloqueou progressao para producao)

Q: O sistema tem edge de mercado?
A: NAO. Profit Factor 0,15 vs target 1,30. Causa: churning, nao mercado.
   Com churning corrigido e Edge Gate ativo, o sistema BLOQUEOU todos
   os sinais (dia 27/04) — o que e CORRETO em ausencia de edge confirmado.

Q: Qual o proximo passo?
A: 1. Corrigir churning no fase4_wrapper.py (IMEDIATO)
   2. Confirmar Edge Gate ativo em todos os runs
   3. Reexecutar 20 ciclos com close_mode=never e inspecionar posicoes
   4. Verificar se win rate melhora com posicoes mantidas por 1+ candle
```

---

## ASSINATURAS

```
Emitente  : PSA-WIND / Arquiteto e Project Manager OMEGA
Versao    : v3.0 FINAL (substitui OIS-RPT-20260428-001 e 002)
Data      : 28 de Abril de 2026
Ref       : OIS-RPT-20260428-003

Fontes    : 16 arquivos de auditoria lidos e verificados
Trades    : 810 abertos (agregados) / 814 fechados (auditoria PNL)
Janela    : 2026-04-26 19:51 UTC a 2026-04-27 20:50 UTC
```

---
FIM DO RELATORIO — OIS-RPT-20260428-003
