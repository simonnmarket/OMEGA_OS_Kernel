# ==============================================================================
# OMEGA FUND: LIÇÕES APRENDIDAS E BACKLOG TECNOLÓGICO (V4.0 -> V5.0)
# ==============================================================================
# Este documento serve de garantia de que nenhuma falha cometida na fase teórica
# será esquecida. Atua como barreira de regressão e mapa para futuras iterações.
# ==============================================================================

## 🛡️ SEÇÃO 1: LIÇÕES APRENDIDAS (NUNCA REPETIR)
1. **O Crime da Omissão (Sinais Perdidos):**
   * *Ocorrência:* Uso de `return` silenciosos para descartar sinais inválidos.
   * *Aprendizado:* Em finanças reguladas (MiFID/SEC), toda a ação, especialmente as rejeições, tem de deixar rastro. A "Dead Letter Queue" é a única forma de garantir validade e rastreamento de erros de agentes.

2. **A "Falsa Tipagem" (TypedDict vs Pydantic):**
   * *Ocorrência:* O uso de tipagem do built-in Python sem verificação estrita em runtime abria brechas de sistema a corrupção de mensagens.
   * *Aprendizado:* Num sistema multi-agente, as portas de entrada não podem ser flexíveis. O Schema de payload dita as regras globais e deve ser esmagador na sua validação na própria fronteira.

3. **O Paradoxo do Lock "Seguro":**
   * *Ocorrência:* Assumir que operações são atómicas ou que concorrência não impactaria variáveis "menores".
   * *Aprendizado:* Mutação de estado (`current_equity` ou `drawdown`) requer 100% de `Async.Locks` de modo a evitar o *Double-Spending*. Concorrência perdoa no laboratório, mas mata o capital em Produção.

4. **Matemática Teórica vs Produção:**
   * *Ocorrência:* Ausência da aplicação do último miligrama do Kelly Ratio à unidade de ação real (Lotes do MT5) e ausência de tolerância a anomalias matemáticas como Divisões por Zero em Matrizes.
   * *Aprendizado:* É estúpido definir a probabilidade mais segura do universo se ao final o sinal não enviar um lote real e calculado para a Exchange.

---

## 📌 SEÇÃO 2: BACKLOG TÉCNICO (PENDÊNCIAS REGISTRADAS)
Como combinado, estas são as pendências não-bloqueantes, mas fundamentais para o aperfeiçoamento contínuo:

### [PRIORIDADE MÉDIA]
* **Rate Limiting de Agentes**
  * *Descrição:* Prevenir que um oráculo enlouquecido num loop envie 1000 sinais no mesmo ms e "afogue" o orquestrador (mesmo que estes sejam esmagados pela CB ou Pydantic).
  * *Solução.* Controlo via Redis Key (`expire = 60s`).
* **Exposição Dinâmica de Portfólio (Fund Leverage Real)**
  * *Descrição:* A `current_portfolio_leverage` no Motor de Risco foi mantida de forma referencial/simulada temporária para garantir destravamento.
  * *Solução:* Substituir a var temporária pela chamada ao Broker MT5 e obter Marge/Exposure exatos por ms.

### [PRIORIDADE BAIXA]
* **Cache Distribuída e Time-To-Live Longo de Matrizes Correlacionais**
  * *Descrição:* Computação da matriz a cada tick no V4 pode impactar CPU. 
  * *Solução:* Migração massiva do peso para a noite, com a leitura matricial via Redis Pub/Sub de matrizes pré-computadas.
* **Testes de Stress Contínuo Unit-Mocked (PyTest)**
  * *Descrição:* Validação assíncrona da pipeline via Pytest simulando caos controlado. 
  * *Solução:* Scripts de Locust testando vazamento e gargalos RAM sob alta frequência HFT.
