# OMEGA QUANTITATIVE FUND: ARQUITETURA DE CLASSE INSTITUCIONAL (TIER-0)
**Documento Mestre de Engenharia Quantitativa e Gestão de Risco**

---

## 🏛️ PREFÁCIO: O PADRÃO GOLDMAN SACHS (TIER-0)
Em infraestruturas quantitativas de elite, não existe espaço para "adaptações reativas", "amostras pequenas" ou "arquiteturas de conveniência". Cada componente deste sistema foi desenhado sob o pressuposto de que o mercado é não-estacionário, os dados têm ruído e a preservação do capital é a diretriz primária. Todo o otimismo foi substituído por rigor estatístico e engenharia de alta disponibilidade.

---

## 1. SEGREGATION OF DUTIES (SEPARAÇÃO DE RESPONSABILIDADES)
A falha mais comum em sistemas de trading retail é permitir que o gerador de sinal execute o risco. No OMEGA, aplicamos a separação institucional rigorosa:

### 1.1 A Camada Quant (Agentes Alpha / Signal Generators)
*   **Função:** Detetar ineficiências (Edges) e emitir Sinais.
*   **Ação:** O Agente (ex: `NasaIntegratedStrategy`) avalia o mercado, o ADX, o Regime. Ele **NÃO** calcula lotes. Ele **NÃO** abre posições.
*   **Output:** Emite um pacote de intenção estruturado: `[Timestamp, Ativo, Direção, Preço_Sugestão, SL_Técnico, Nível_Confiança, Vetor_Contexto]`.

### 1.2 A Camada de Risco (OMEGA Virtual Fund / Execution Engine)
*   **Função:** Gestor de Portfólio Centralizado.
*   **Ação:** Recebe o Sinal da Camada Quant. Avalia o *Capital em Risco* atual, a *Correlação Global* (Heatmap), o *Sharpe Ponderado* do Agente emissor e os limites de *Drawdown* do fundo.
*   **Output:** Se aprovado, usa a Fração de Kelly ajustada por volatilidade para calcular o tamanho real do lote e executa a ordem.

---

## 2. DATA LAKE & TELEMETRIA DE ALTA FREQUÊNCIA (HFT)
Dados atrasados ou corrompidos geram "Look-Ahead Bias" e destroem fundos quantitativos. OMT5 não é um banco de dados de séries temporais; ele é apenas um *broker gateway*.

### 2.1 O Extrator de Ticks Contínuo (TickRecorderAgent)
*   **Missão:** Gravar assincronamente o stream de Ticks (Bid, Ask, Volume) de todos os ativos autorizados, 24/5. 
*   **Motivo:** O cálculo preciso do **MAE** (Maximum Adverse Excursion) e **MFE** (Maximum Favorable Excursion) é impossível retrospectivamente no MT5 para grandes volumes. Precisamos do *nosso* histórico ininterrupto.

### 2.2 Imutabilidade e Persistência (PostgreSQL + TimescaleDB)
*   SQLite é banido da telemetria crítica devido ao "Write-Locking" concorrente.
*   Usaremos **TimescaleDB** (ou estrutura PostgreSQL robusta) para ingestão paralela de sinais, execuções e telemetria.
*   **Tabela `Trade_Ledger_Tier0`:** Contém 85+ campos, incluindo `execution_latency_ns`, slippage real medido e `context_json` (gravado no ms do sinal).
*   **Integridade:** Hash Hashlib Checksum em Cadeia (Blockchain-like) em cada split de ordem para auditoria imaculada.

---

## 3. VALIDAÇÃO ESTATÍSTICA E CALIBRAÇÃO DE MÁQUINA
Fica proibido o "Machine Learning" raso (ajustes após 3 perdas). Toda a adaptação da máquina requer prova estatística.

### 3.1 Significância Estatística Obrigatória
*   Nenhuma calibração ou aumento de exposição será feito sem um **T-Test ou Bootstrapping**.
*   O *Sharpe Ratio*, *Sortino Ratio* e *Calmar Ratio* de um agente só são considerados válidos se o *p-value* for < 0.05 e a amostra (N) for superior a 100 eventos fechados intra-regime.

### 3.2 Protocolo de Calibração Out-Of-Sample (Walk-Forward)
O motor de calibração que ajustará os fatores de SL dinâmicos (baseados no percentil 95 do MAE, não na média) processará os dados assim:
1.  Treina parâmetros num Set In-Sample (Jan-Mar).
2.  Valida num Set Out-Of-Sample (Abr-Mai).
3.  Só aplica em Produção se a degradação do Sharpe entre IS e OOS for inferior a 30%.
*Isto aniquila o Overfitting Dinâmico.*

### 3.3 Penalização por Múltiplos Testes
Se testarmos 50 parâmetros diferentes para achar a otimização de uma moeda, aplicamos automaticamente a **Correção de Bonferroni** aos P-Values para evitar P-Hacking.

---

## 4. CIRCUIT BREAKERS E PROTEÇÃO DO PORTFÓLIO
A máquina deve saber "desligar-se" de forma autônoma e inteligente. O fundo possui limites codificados inegociáveis ("Hard Caps"):

*   **Max Daily Drawdown (Ex: -3.5% AUM):** Trava imediata de todas as novas posições. Transição para modo *Close-Only*.
*   **Max Correlation Spike:** Se a matriz de correlação em janela de 3 horas mostrar USD pairs convergindo acima de 0.85, o sistema aplica um veto instantâneo (Treasury Lock) a novas entradas baseadas em USD, evitando exposição direcional sistêmica.
*   **Agent Quarantine:** Se o desempenho de um agente (Pnl ou Win-Rate) desviar mais de 3 Desvios Padrão da sua média histórica estocástica verificada, ele é isolado em ambiente "Paper Trading", até reversão à média comprovada fora do dinheiro real.

---

## 5. ROTEIRO DE DEPLOYMENT ESTRITO
1.  **Fundações de Telemetria:** Instaurar o `TickRecorderAgent` e PostgreSQL Ledger. (Coletando os átomos antes de fazer ciência).
2.  **Transição de Lógica:** Isolar os Códigos das Estratégias para emitir via *Bus de Eventos* apenas SINAIS, sem chamar `OrderSend`.
3.  **Lançamento do Virtual Fund:** Construir o módulo Gestor de Risco que processa a Fila de Sinais e emite lotes usando Fractional Kelly.
4.  **Maturação Estatística:** Aguardar a recolha nativa de N > 300 trades para engatilhar os modelos de regressão MAE/MFE validada OOS.
