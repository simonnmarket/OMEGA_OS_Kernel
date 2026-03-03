# OMEGA QUANTITATIVE FUND: ARQUITETURA TIER-0 (V3 FINAL)
**Documento Mestre de Engenharia de Software, Infraestrutura HFT e Risco Quantitativo**

*Versão 3.0: Refinada sob escrutínio extremo de falhas de I/O em banco de dados, falsas precisões de latência, excesso computacional de correlações e correção de sobrecarga de rede. Foco na execução técnica pragmática de padrões de Hedge Funds.*

---

## 🏛️ 1. SEGREGAÇÃO DE DEVERES E COMUNICAÇÃO (EVENT BUS)
O clássico monólito onde "o bot abre o trade" está oficialmente obsoleto.

### 1.1 Comunicação via `Redis Streams` (Event Bus Institucional)
*   **A Abstração:** Agentes Alpha geram "Sinais de Intenção". O Fundo (Risk Manager) escuta, avalia risco global, emite ordens, e o Execution Engine interage com as corretoras (MT5/IB).
*   **O Middleware:** A comunicação bidirecional será feita usando **Redis Streams**. Isso garante latência sub-milisegundo (<1ms), persistência nativa na ram, e capacidades robustas de *Publish/Subscribe* e *Consumer Groups*.
*   **Latência Realista:** O MT5 retail opera em milissegundos (ms), tipicamente 50-500ms. Falar em latência de "nanosegundos" (ns) em Retail-to-Broker é *falsa precisão*. Toda a telemetria será baseada em **Milissegundos (ms)** ancorada via **NTP Sync** local, corrigindo o *clock drift*.

---

## 💾 2. DATA LAKE: O TICK RECORDER E A BASE DE DADOS HFT
Armazenar dados puros e imutáveis sem parar os processos da camada alfa. Não começaremos com "92 colunas bloatwares".

### 2.1 O Componente `TickRecorderAgent`
*   **Evitar I/O Bottleneck:** Inserir Ticks direto numa base relacional a cada sub-segundo irá travar o sistema na primeira notícia do NFP (folha de pagamento agrícola dos EUA).
*   **Buffer in-Memory:** O TickRecorder vai empilhar o fluxo em Listas/Streams do Redis.
*   **Flush Assíncrono:** Um "Batch Writer Worker" irá acordar a cada instante (ex: 5000ms ou 5000 ticks) e fará um `BULK INSERT (COPY)` no banco principal.
*   **Crash Recovery:** Se o Worker cair, os Ticks continuam salvos no Redis Stream esperando reinicialização.
*   **Retenção:** Ticks brutos mantidos por 7 dias para análise de MAE/MFE; depois, *downsampling* para velas/séries de 1 segundo compactáveis.

### 2.2 PostgreSQL com MVP Schema (Fase 1)
Abandonamos a complexidade teatral de "Blockchain Hashes" (pesado e inútil) em prol do `row_hash` nativo e do `pg_audit` do **PostgreSQL** para imutabilidade real e ágil (sem sobrecarga transacional).
*   **MVP Trade Ledger (20 Campos Essenciais):** Começamos o banco de dados restrito as informações que podemos testar de imediato: `trade_id`, `broker_timestamp_ms`, `latency_ms`, `asset`, `direction`, `entry_price_requested`, `fill_price` (slippage originado), `mfe_max_price`, `mae_max_price`, `regime_signal`, `pnl`. Após validarmos com N > 300, migraremos ao schema expandido de 85 variaveis.

---

## 📉 3. GESTÃO DE CAPITAL E MATEMÁTICA DE RISCO (OMEGA FUND)
Implementação explícita de limiares matemáticos para gerir a exposição e falhas estatísticas.

### 3.1 Fração de Kelly (Fractional Kelly Estrito)
O modelo *Full Kelly* leva a drawdowns massivos (-80%). Instituições do porte de Renaissance/Citadel operam frações.
*   **Parâmetro Base:** Fração Kelly fixa no máximo de **0.25 (Quarter-Kelly)**. Default duro no sistema.
*   **Maximum Total Exposição:** A agregação total do fundo nunca ultrapassará 25% do AUM.

### 3.2 Validação Estatística Institucional (P-Value & Bonferroni)
*   **P-Value mais Rígido:** Substituímos o tolerante `p < 0.05` pelo rigor quantitativo aceitável de **`p < 0.01`**. Qualquer filtro ou regra não passa para produção sem bater 99% de comprovação de que não é ruído.
*   **Tamanho de Amostra:** Calibrações de SL dinâmicos (Mae-percentil) requerem *N > 100 observações passadas dentro do mesmo regime de mercado*. Nenhuma otimização acontece antes desse número. 

### 3.3 A Evolução do Agent Quarantine
Um agente que tenha apenas 20 trades não tem distribuição estatística para ser medido por Desvios Padrão (3σ). A avaliação deve espelhar o tempo de vida do robô:
*   **Incubação (N < 50 trades):** Risco fixo mínimo de alocação (não usa Kelly). Monitoramento passivo.
*   **Crescimento (N = 50 a 100):** Se o Z-score do retorno violar **2σ**, o agente entra em quarentena (Paper Trading).
*   **Maturidade (N > 100):** Exposição Kelly total (até 0.25). Quarentena se o Z-score violar **3σ**.

---

## ⚔️ 4. CIRCUIT BREAKERS E CÁLCULO DE CORRELAÇÃO
Proteção hard-coded, computacionalmente eficiente e dissociada das emoções.

### 4.1 Correlação Dinâmica Otimizada (EWMA)
Calcular a Matriz de Correlação a cada Tick para dezenas de instrumentos frita as CPUs.
*   **Método:** `EWMA Correlation (λ=0.94)` aplicada sobre *log-returns* dos ativos num período deslizante de 1 hora.
*   **Periodicidade de Cálculo:** O Worker atualiza os mapas de calor da correlação a cada **5 minutos**, e não na ocorrência de cada Tick.
*   **Threshold:** Se um *Cluster* (Ex: derivados de Yen ou Ouro/Cobre) bater **0.85** de correlação concentrada, aplica-se um "Treasury Lock" automático prevenindo qualquer nova exposição para esse bloco.

### 4.2 Limites Operacionais Globais
*   **Drawdown Máximo de Fundo:** Interrupção (Halt) instantânea global ao bater a marca dura de **-3.5% Diário**.
*   **Ambiente de Produção Múltiplo:** Alterações e novas calibrações de parâmetros (Walk-Forwards passados) jamais vão direito para os MT5s reais. Parametros novos são mandatos a rodarem no `Staging Environment` (MT5 de Demo), e apenas são migrados após sobrevivencia em forward testing.

---

## 🚦 ROTEIRO TÉCNICO DE IMPLEMENTAÇÃO (RESUMO EXECUTIVO)
Esta arquitetura não é uma visão do futuro, é o guia da nossa programação de hoje e baseia-se fortemente nas tecnologias escolhidas: **Python + Redis + MT5 + PostgreSQL**.

1. **Sprint 1 (O Pipeline Sangrento):** Levantar a Fila Redis (Streams). Codificar o `TickRecorderAgent` isolado. Garantir NTP Time-Sync e Buffer Flush no PostgreSQL, sem falhas de rede.
2. **Sprint 2 (Modo Signal-Only):** Refatorar os bots `Apollo11 / Nasa / etc.` O `OrderSend` morre nesses painéis; todos exportam o seu JSon de intenção para o Redis via PubSub.
3. **Sprint 3 (Risk Manager MVP):** O Fundo virtual lê a fila. Faz check da matriz Otimizada em lotes de 5m. Aplica Fração Kelly de 0.25. E por fim repassa à ponte Executora Mestre MT5.
4. **Sprint 4 (Papel Ininterrupto):** Rodar dias no vazio com Data base ativa, preenchendo as métricas das 20 Colunas do PostgreSQL, para obtermos OOS e calibrarmos sem curva fitada.
