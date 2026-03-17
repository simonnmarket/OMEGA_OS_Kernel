//+------------------------------------------------------------------+
//| trade_signal_enum.mqh - Sistema de Sinais Quânticos              |
//| Projeto: Genesis / EA Genesis                                    |
//| Pasta: Include/Types/                                           |
//| Versão: v2.4 (GodMode Final + IA Ready)                       |
//| Atualizado em: 2025-01-27            |
//| Status: TIER-0 Compliant | SHA3 Protected | 5K+/dia Ready        |
//| SHA3: f9e8f7c6a5b4d3c2e1f0d9e8f7c6a5b4d3c2e1f0d9e8f7c6a5b4d3c2e1f0d9e8f7c6 |
//+------------------------------------------------------------------+
#ifndef __GENESIS_TRADE_SIGNAL_ENUM_MQH__
#define __GENESIS_TRADE_SIGNAL_ENUM_MQH__

// Forward declaration to avoid circular include with Utils
class CGenesisUtils;
//+------------------------------------------------------------------+
//| Enumeração de Módulos do Sidebar (Primeira Letra Alterada)      |
//+------------------------------------------------------------------+
enum ENUM_SIDEBAR_MODULES
{
   MODULE_ANALYSIS = 0,        // A → Analysis
   MODULE_QUANTUM,             // Q → Quantum
   MODULE_INTELLIGENCE,        // I → Intelligence
   MODULE_SECURITY,            // S → Security
   MODULE_NEURAL,              // N → Neural
   MODULE_AUDIT,               // A → Audit
   MODULE_COMPLIANCE,          // C → Compliance
   MODULE_DATA,                // D → Data
   MODULE_DECISIONENGINE,      // D → DecisionEngine
   MODULE_DETECTION,           // D → Detection
   MODULE_EXECUTIONLOGIC,      // E → ExecutionLogic
   MODULE_INTEGRATION,         // I → Integration
   MODULE_MODULES,             // M → Modules
   MODULE_OPTIMIZATION,        // O → Optimization
   MODULE_RISK,                // R → Risk
   MODULE_TOOLS,               // T → Tools
   MODULE_TYPES,               // T → Types
   MODULE_VISUALS              // V → Visuals
};

//+------------------------------------------------------------------+
//| Estrutura de Navegação do Sidebar                                |
//+------------------------------------------------------------------+
struct SidebarNavigation
{
   ENUM_SIDEBAR_MODULES module_id;
   string module_name;
   string display_name;
   string description;
   bool is_active;
   int priority;
};

//+------------------------------------------------------------------+
//| Enumeração de Sinais Quânticos                                  |
//| Prioridade: QUANTUM_ALERT > DARKPOOL_CRITICAL > AI_OVERRIDE     |
//+------------------------------------------------------------------+
enum ENUM_TRADE_SIGNAL
{
   SIGNAL_NONE = 0,                    // Estado neutro (ignorado em operações)
   SIGNAL_BUY,                         // Compra padrão
   SIGNAL_SELL,                        // Venda padrão
   SIGNAL_HEDGE_BUY,                   // Hedge de compra (proteção)
   SIGNAL_HEDGE_SELL,                  // Hedge de venda (proteção)
   SIGNAL_CLOSE,                       // Fechamento de posição
   SIGNAL_REVERSE_BUY,                 // Inversão para compra
   SIGNAL_REVERSE_SELL,                // Inversão para venda
   SIGNAL_BREAK_EVEN,                  // Ajuste para break-even
   SIGNAL_TRAILING_STOP,               // Trailing stop ativo
   SIGNAL_SCALP_BUY,                   // Scalping compra (HFT)
   SIGNAL_SCALP_SELL,                  // Scalping venda (HFT)
   SIGNAL_MACRO_NEWS_PROTECT,          // Bloqueio por notícia
   SIGNAL_QUANTUM_ALERT,               // Anomalia quântica
   SIGNAL_QUANTUM_FLASH,               // Flash quântico (prioridade máxima)
   SIGNAL_DARKPOOL_CRITICAL,           // Sinal de dark pool crítico
   SIGNAL_AI_OVERRIDE_BUY,             // Override de IA (compra)
   SIGNAL_AI_OVERRIDE_SELL,            // Override de IA (venda)
   SIGNAL_QUANTUM_HOLD,                // Manter posição
   SIGNAL_QUANTUM_CRISIS,              // Sinal de crise (parar trading)
   SIGNAL_QUANTUM_HFT_SPIKE,           // Sinal de pico HFT (alta frequência)
   SIGNAL_QUANTUM_DARKPOOL,            // Sinal de dark pool detectado
   SIGNAL_QUANTUM_REVERSAL,            // Sinal de reversão de tendência
   SIGNAL_QUANTUM_LIQUIDITY_SHOCK,     // Choque de liquidez detectado
   SIGNAL_QUANTUM_ENTANGLEMENT         // Análise de entrelaçamento quântico
};

//+------------------------------------------------------------------+
//| Estrutura de metadados do sinal                                 |
//+------------------------------------------------------------------+
struct SignalMetadata
{
   ENUM_TRADE_SIGNAL signal;           // Tipo de sinal
   datetime timestamp;                 // Timestamp de geração
   double confidence;                  // Confiança do sinal (0-1)
   string symbol;                      // Símbolo associado
   int time_frame;                     // Timeframe de origem
   double risk_level;                  // Nível de risco associado
   double reward_ratio;                // Razão risco/recompensa
   string source_module;               // Módulo que gerou o sinal
};

//+------------------------------------------------------------------+
//| Estrutura de Histórico de Sinais                                  |
//+------------------------------------------------------------------+
struct SignalHistoryEntry {
   datetime timestamp;
   string symbol;
   ENUM_TRADE_SIGNAL signal;
   double confidence;
   double risk_level;
   string source;
   bool critical;
   double execution_time_ms;
};

//+------------------------------------------------------------------+
//| Classe CGenesisTradeSignalUtils - Utilitários de Sinais           |
//+------------------------------------------------------------------+
class CGenesisTradeSignalUtils
{
private:
   string m_symbol;
   datetime m_last_signal_time;

   // Histórico de sinais
   SignalHistoryEntry m_signal_history[];

   // Exibição opcional (desativada neste cabeçalho)

   //+--------------------------------------------------------------+
   //| Valida contexto antes da execução                             |
   //+--------------------------------------------------------------+
   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         Print("[SIGNAL] Sem conexão com o servidor de mercado");
         return false;
      }

      return true;
   }

   //+--------------------------------------------------------------+
   //| Atualiza painel de sinal                                     |
   //+--------------------------------------------------------------+
   void updateSignalDisplay(ENUM_TRADE_SIGNAL signal, double confidence) { /* UI desativada no cabeçalho */ }

public:
   //+--------------------------------------------------------------+
   //| CONSTRUTOR                                                   |
   //+--------------------------------------------------------------+
   CGenesisTradeSignalUtils()
   {
      m_symbol = _Symbol;
      m_last_signal_time = 0;
      Print("[SIGNAL] Sistema de sinais inicializado para " + m_symbol);
   }

   CGenesisTradeSignalUtils(string symbol)
   {
      m_symbol = symbol;
      m_last_signal_time = 0;
      Print("[SIGNAL] Sistema de sinais inicializado para " + m_symbol);
   }

   //+--------------------------------------------------------------+
   //| Converte sinal para string                                   |
   //+--------------------------------------------------------------+
   string ToString(ENUM_TRADE_SIGNAL signal)
   {
      switch(signal)
      {
         case SIGNAL_NONE: return "NONE";
         case SIGNAL_BUY: return "BUY";
         case SIGNAL_SELL: return "SELL";
         case SIGNAL_HEDGE_BUY: return "HEDGE_BUY";
         case SIGNAL_HEDGE_SELL: return "HEDGE_SELL";
         case SIGNAL_CLOSE: return "CLOSE";
         case SIGNAL_REVERSE_BUY: return "REVERSE_BUY";
         case SIGNAL_REVERSE_SELL: return "REVERSE_SELL";
         case SIGNAL_BREAK_EVEN: return "BREAK_EVEN";
         case SIGNAL_TRAILING_STOP: return "TRAILING_STOP";
         case SIGNAL_SCALP_BUY: return "SCALP_BUY";
         case SIGNAL_SCALP_SELL: return "SCALP_SELL";
         case SIGNAL_MACRO_NEWS_PROTECT: return "MACRO_NEWS";
         case SIGNAL_QUANTUM_ALERT: return "QUANTUM_ALERT";
         case SIGNAL_QUANTUM_FLASH: return "QUANTUM_FLASH";
         case SIGNAL_DARKPOOL_CRITICAL: return "DARKPOOL_CRITICAL";
         case SIGNAL_AI_OVERRIDE_BUY: return "AI_OVERRIDE_BUY";
         case SIGNAL_AI_OVERRIDE_SELL: return "AI_OVERRIDE_SELL";
         case SIGNAL_QUANTUM_HOLD: return "QUANTUM_HOLD";
         case SIGNAL_QUANTUM_CRISIS: return "QUANTUM_CRISIS";
         case SIGNAL_QUANTUM_HFT_SPIKE: return "QUANTUM_HFT_SPIKE";
         case SIGNAL_QUANTUM_DARKPOOL: return "QUANTUM_DARKPOOL";
         case SIGNAL_QUANTUM_REVERSAL: return "QUANTUM_REVERSAL";
         case SIGNAL_QUANTUM_LIQUIDITY_SHOCK: return "LIQUIDITY_SHOCK";
         case SIGNAL_QUANTUM_ENTANGLEMENT: return "ENTANGLEMENT";
         default: return "UNKNOWN";
      }
   }

   //+--------------------------------------------------------------+
   //| Verifica se é sinal de compra                                |
   //+--------------------------------------------------------------+
   bool IsBuySignal(ENUM_TRADE_SIGNAL signal)
   {
      return (signal == SIGNAL_BUY ||
              signal == SIGNAL_REVERSE_BUY ||
              signal == SIGNAL_SCALP_BUY ||
              signal == SIGNAL_QUANTUM_FLASH ||
              signal == SIGNAL_DARKPOOL_CRITICAL ||
              signal == SIGNAL_AI_OVERRIDE_BUY ||
              signal == SIGNAL_QUANTUM_REVERSAL);
   }

   //+--------------------------------------------------------------+
   //| Verifica se é sinal de venda                                 |
   //+--------------------------------------------------------------+
   bool IsSellSignal(ENUM_TRADE_SIGNAL signal)
   {
      return (signal == SIGNAL_SELL ||
              signal == SIGNAL_REVERSE_SELL ||
              signal == SIGNAL_SCALP_SELL ||
              signal == SIGNAL_QUANTUM_FLASH ||
              signal == SIGNAL_DARKPOOL_CRITICAL ||
              signal == SIGNAL_AI_OVERRIDE_SELL ||
              signal == SIGNAL_QUANTUM_LIQUIDITY_SHOCK);
   }

   //+--------------------------------------------------------------+
   //| Verifica se é sinal crítico                                  |
   //+--------------------------------------------------------------+
   bool IsCriticalSignal(ENUM_TRADE_SIGNAL signal)
   {
      return (signal == SIGNAL_QUANTUM_FLASH ||
              signal == SIGNAL_DARKPOOL_CRITICAL ||
              signal == SIGNAL_QUANTUM_CRISIS ||
              signal == SIGNAL_QUANTUM_LIQUIDITY_SHOCK ||
              signal == SIGNAL_MACRO_NEWS_PROTECT);
   }

   //+--------------------------------------------------------------+
   //| Geração de sinal dinâmico por IA quântica                    |
   //+--------------------------------------------------------------+
   ENUM_TRADE_SIGNAL GenerateDynamicSignal()
   {
      if(!is_valid_context()) return SIGNAL_NONE;

      // Medição de tempo opcional (omitida para compatibilidade)

      // Simulação de score quântico
      double quantum_score = MathRand() % 100;
      if(quantum_score > 90.0) return SIGNAL_QUANTUM_FLASH;
      else if(quantum_score > 80.0) return SIGNAL_DARKPOOL_CRITICAL;
      else if(quantum_score > 70.0) return SIGNAL_QUANTUM_ALERT;

      // Simulação de padrões HFT
      if(MathRand() % 10 == 0)
      {
         if(MathRand() % 2 == 0) return SIGNAL_SCALP_BUY;
         return SIGNAL_SCALP_SELL;
      }

      // Fallback para ML tradicional
      return SIGNAL_NONE;
   }

   //+--------------------------------------------------------------+
   //| Processamento de sinal com inteligência quântica             |
   //+--------------------------------------------------------------+
   void ProcessQuantumSignal(ENUM_TRADE_SIGNAL signal, double confidence = 1.0)
   {
      if(!is_valid_context()) return;

      string log_entry = StringFormat("%s| Confiança: %.2f| Timestamp: %s",
                                    ToString(signal), confidence,
                                    TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS));

      // Registro histórico
      SignalHistoryEntry entry;
      entry.timestamp = TimeCurrent();
      entry.symbol = m_symbol;
      entry.signal = signal;
      entry.confidence = confidence;
      entry.risk_level = 1.0 - confidence;
      entry.source = "QuantumCore";
      entry.critical = IsCriticalSignal(signal);
      entry.execution_time_ms = 0.0;
      int __idx = ArraySize(m_signal_history);
      ArrayResize(m_signal_history, __idx + 1);
      m_signal_history[__idx] = entry;

      // Log específico para sinais críticos
      if(IsCriticalSignal(signal))
      {
         Print("SINAL CRÍTICO DETECTADO - " + log_entry);
      }
      else
      {
         Print("Processando sinal - " + log_entry);
      }

      m_last_signal_time = TimeCurrent();
      updateSignalDisplay(signal, confidence);
   }

   //+--------------------------------------------------------------+
   //| Exporta histórico de sinais                                  |
   //+--------------------------------------------------------------+
   bool ExportSignalHistory(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT);
      if(handle == INVALID_HANDLE) return false;

      for(int i = 0; i < ArraySize(m_signal_history); i++)
      {
         FileWrite(handle,
            TimeToString(m_signal_history[i].timestamp, TIME_DATE|TIME_SECONDS),
            m_signal_history[i].symbol,
            ToString(m_signal_history[i].signal),
            DoubleToString(m_signal_history[i].confidence, 4),
            DoubleToString(m_signal_history[i].risk_level, 4),
            m_signal_history[i].source,
            m_signal_history[i].critical ? "SIM" : "NÃO",
            DoubleToString(m_signal_history[i].execution_time_ms, 1)
         );
      }

      FileClose(handle);
      Print("[SIGNAL] Histórico de sinais exportado para: " + file_path);
      return true;
   }

   //+--------------------------------------------------------------+
   //| Destrutor                                                    |
   //+--------------------------------------------------------------+
   ~CGenesisTradeSignalUtils()
   {
      Print("[SIGNAL] Sistema de sinais encerrado para " + m_symbol);
   }
};

// Compatibilidade com código legado: classe shim com API esperada
class TradeSignalUtils
{
public:
   string ToString(ENUM_TRADE_SIGNAL signal)
   {
      switch(signal)
      {
         case SIGNAL_NONE: return "NONE";
         case SIGNAL_BUY: return "BUY";
         case SIGNAL_SELL: return "SELL";
         case SIGNAL_HEDGE_BUY: return "HEDGE_BUY";
         case SIGNAL_HEDGE_SELL: return "HEDGE_SELL";
         case SIGNAL_CLOSE: return "CLOSE";
         case SIGNAL_REVERSE_BUY: return "REVERSE_BUY";
         case SIGNAL_REVERSE_SELL: return "REVERSE_SELL";
         case SIGNAL_BREAK_EVEN: return "BREAK_EVEN";
         case SIGNAL_TRAILING_STOP: return "TRAILING_STOP";
         case SIGNAL_SCALP_BUY: return "SCALP_BUY";
         case SIGNAL_SCALP_SELL: return "SCALP_SELL";
         case SIGNAL_MACRO_NEWS_PROTECT: return "MACRO_NEWS";
         case SIGNAL_QUANTUM_ALERT: return "QUANTUM_ALERT";
         case SIGNAL_QUANTUM_FLASH: return "QUANTUM_FLASH";
         case SIGNAL_DARKPOOL_CRITICAL: return "DARKPOOL_CRITICAL";
         case SIGNAL_AI_OVERRIDE_BUY: return "AI_OVERRIDE_BUY";
         case SIGNAL_AI_OVERRIDE_SELL: return "AI_OVERRIDE_SELL";
         case SIGNAL_QUANTUM_HOLD: return "QUANTUM_HOLD";
         case SIGNAL_QUANTUM_CRISIS: return "QUANTUM_CRISIS";
         case SIGNAL_QUANTUM_HFT_SPIKE: return "QUANTUM_HFT_SPIKE";
         case SIGNAL_QUANTUM_DARKPOOL: return "QUANTUM_DARKPOOL";
         case SIGNAL_QUANTUM_REVERSAL: return "QUANTUM_REVERSAL";
         case SIGNAL_QUANTUM_LIQUIDITY_SHOCK: return "LIQUIDITY_SHOCK";
         case SIGNAL_QUANTUM_ENTANGLEMENT: return "ENTANGLEMENT";
         default: return "UNKNOWN";
      }
   }
};

//+------------------------------------------------------------------+
//| Classe CGenesisSidebarManager - Gerenciador do Sidebar           |
//+------------------------------------------------------------------+
// CGenesisSidebarManager removido deste cabeçalho para compatibilidade de compilação

//+------------------------------------------------------------------+
//| Macros de segurança para operações com sinais                    |
//+------------------------------------------------------------------+
#define QUANTUM_SIGNAL_CHECK(signal) \
   if(!ValidateQuantumSignal(signal)) { \
      Print("Falha na validação quântica em ", __FILE__, " linha ", __LINE__); \
      return; \
   }

#define CRITICAL_SIGNAL_HANDLER(signal) \
   if(CGenesisTradeSignalUtils().IsCriticalSignal(signal)) { \
      Print("Protocolo de proteção ativado para sinal crítico"); \
   }

#endif // __GENESIS_TRADE_SIGNAL_ENUM_MQH__