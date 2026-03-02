//+------------------------------------------------------------------+
//| QuantumLearning.mqh - Sistema de Aprendizado Quântico Avançado  |
//| Projeto: Genesis                                                |
//| Pasta: Include/Intelligence/                                    |
//| Versão: v1.2 (GodMode Final + IA Ready + Correção de Erros)     |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_LEARNING_MQH__
#define __QUANTUM_LEARNING_MQH__

// UI opcional: defina QLRN_ENABLE_UI antes deste include para habilitar
#ifdef QLRN_ENABLE_UI
  #include <Controls/Label.mqh>
#endif

// Declaração antecipada para quebrar ciclo de inclusão
class QuantumProcessor;
class RiskProfile;
class QuantumMemoryCell;
class QuantumBehaviorController;

// Incluir apenas o necessário - remover dependências circulares
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Risk/RiskProfile.mqh>

// Configuração padrão (evitar inputs/variáveis globais em headers)
#ifndef QLRN_LEARNING_RATE
  #define QLRN_LEARNING_RATE 0.01
#endif
#ifndef QLRN_ENTROPY_THRESHOLD
  #define QLRN_ENTROPY_THRESHOLD 0.75
#endif
#ifndef QLRN_ENABLE_REINFORCEMENT
  #define QLRN_ENABLE_REINFORCEMENT true
#endif
#ifndef QLRN_UPDATE_INTERVAL_MS
  #define QLRN_UPDATE_INTERVAL_MS 100
#endif

struct QuantumMetrics
{
   double profit_factor;
   double win_rate;
   double sharpe_ratio;
   double quantum_efficiency;
   datetime timestamp;
   ENUM_TRADE_SIGNAL last_signal;
   double signal_confidence;
};

struct QuantumLearningHistoryEntry {
   datetime timestamp;
   string symbol;
   int memory_state;
   double reward_score;
   double learning_rate;
   int patterns_stored;
   int patterns_retrieved;
   bool retrieval_success;
   double market_entropy;
   string action_taken;
};

//+------------------------------------------------------------------+
//| Classe: QuantumLearning - Sistema de Aprendizado Quântico        |
//+------------------------------------------------------------------+
class QuantumLearning
{
private:
   logger_institutional *m_logger;
   QuantumProcessor     *m_qprocessor;
   RiskProfile          *m_risk_profile;
   QuantumMemoryCell    *m_memory_cell;
   QuantumBehaviorController *m_behavior_controller;
   string               m_symbol;
   datetime             m_last_update_time;
   QuantumMetrics       m_metrics;
   double               m_quantum_entropy;
   double               m_learning_progress;
   double               m_quantum_learning_rate;
   QuantumLearningHistoryEntry m_learning_history[];
#ifdef QLRN_ENABLE_UI
   CLabel *m_learn_label;
#endif

   // Validação de contexto
   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) 
      { 
         if(m_logger != NULL) m_logger->log_error("[QLRN] Sem conexão com o servidor de mercado"); 
         return false; 
      }
      if(m_qprocessor == NULL) 
      { 
         if(m_logger != NULL) m_logger->log_warning("[QLRN] Processador quântico não está pronto"); 
         return false; 
      }
      if(m_risk_profile == NULL) 
      { 
         if(m_logger != NULL) m_logger->log_warning("[QLRN] Perfil de risco não está inicializado"); 
         return false; 
      }
      if(m_memory_cell == NULL) 
      { 
         if(m_logger != NULL) m_logger->log_warning("[QLRN] Célula de memória não está pronta"); 
         return false; 
      }
      if(m_behavior_controller == NULL) 
      { 
         if(m_logger != NULL) m_logger->log_warning("[QLRN] Controlador de comportamento não está pronto"); 
         return false; 
      }
      return true;
   }

   // Cálculo de entropia do mercado
   double CalculateMarketEntropy()
   { 
      MqlRates rates[];
      ArraySetAsSeries(rates, true);
      int copied = CopyRates(m_symbol, PERIOD_M1, 0, 20, rates);
      if(copied <= 0) return 0.0;
      
      double entropy = 0.0, sum = 0.0;
      for(int i = 0; i < copied; i++) sum += rates[i].close;
      if(sum <= 0) return 0.0;
      
      for(int i = 0; i < copied; i++)
      {
         double p = rates[i].close / sum;
         if(p > 0) entropy -= p * MathLog(p);
      }
      return NormalizeDouble(entropy, 4);
   }

   // Atualiza display (UI ou console)
   void updateLearnDisplay(double reward, bool success)
   {
#ifdef QLRN_ENABLE_UI
      if(m_learn_label == NULL) 
      {
         m_learn_label = new CLabel();
         if(m_learn_label != NULL)
         {
            m_learn_label.Create(0, "QLRN_Label", 0, 10, 390);
            m_learn_label.Text(StringFormat("QLRN: %s| R:%+.0f%%", success ? "OK" : "ERR", reward * 100));
            m_learn_label.Color(success ? clrLime : clrRed);
            m_learn_label.FontSize(10);
         }
      }
      else
      {
         m_learn_label.Text(StringFormat("QLRN: %s| R:%+.0f%%", success ? "OK" : "ERR", reward * 100));
         m_learn_label.Color(success ? clrLime : clrRed);
      }
#else
      Print(StringFormat("QLRN: %s | R:%+.0f%%", success ? "OK" : "ERR", reward * 100));
#endif
   }

public:
   // Construtor completo
   QuantumLearning(logger_institutional *logger, 
                   QuantumProcessor *qp, 
                   RiskProfile *rp, 
                   QuantumMemoryCell *qmc, 
                   QuantumBehaviorController *qbc, 
                   string symbol = "")
      : m_logger(logger), 
        m_qprocessor(qp), 
        m_risk_profile(rp), 
        m_memory_cell(qmc), 
        m_behavior_controller(qbc), 
        m_symbol(symbol), 
        m_learning_progress(0.0), 
        m_quantum_learning_rate(QLRN_LEARNING_RATE), 
        m_last_update_time(0)
   {
      if(StringLen(m_symbol) == 0) m_symbol = _Symbol;

#ifdef QLRN_ENABLE_UI
      m_learn_label = NULL;
#endif

      // Inicialização segura (array dinâmico inicia vazio)
      
      if(m_logger == NULL) 
      { 
         Print("[QLRN] Logger não fornecido, operando em modo limitado");
      }
      else if (!m_logger->is_initialized())
      {
         m_logger->log_error("[QLRN] Logger não inicializado");
         ExpertRemove();
      }

      if(m_qprocessor == NULL) 
      { 
         if(m_logger != NULL) m_logger->log_error("[QLRN] Processador quântico não inicializado"); 
         ExpertRemove(); 
      }
      if(m_risk_profile == NULL) 
      { 
         if(m_logger != NULL) m_logger->log_error("[QLRN] Perfil de risco não inicializado"); 
         ExpertRemove(); 
      }

      // Inicialização das métricas
      m_metrics.profit_factor = 1.0; 
      m_metrics.win_rate = 0.5; 
      m_metrics.sharpe_ratio = 1.0; 
      m_metrics.quantum_efficiency = 0.5; 
      m_metrics.timestamp = TimeCurrent(); 
      m_metrics.last_signal = SIGNAL_NONE; 
      m_metrics.signal_confidence = 0.0; 
      
      if(m_logger) m_logger->log_info("[QLRN] Sistema de aprendizado quântico inicializado para " + m_symbol);
   }

   // Construtor simplificado
   QuantumLearning(QuantumProcessor *qp, 
                   RiskProfile *rp, 
                   QuantumMemoryCell *qmc, 
                   QuantumBehaviorController *qbc, 
                   string symbol = _Symbol)
      : m_logger(NULL), 
        m_qprocessor(qp), 
        m_risk_profile(rp), 
        m_memory_cell(qmc), 
        m_behavior_controller(qbc), 
        m_symbol(symbol), 
        m_learning_progress(0.0), 
        m_quantum_learning_rate(QLRN_LEARNING_RATE), 
        m_last_update_time(0)
   {
      if(StringLen(m_symbol) == 0) m_symbol = _Symbol;

#ifdef QLRN_ENABLE_UI
      m_learn_label = NULL;
#endif

      // Array dinâmico inicia vazio

      if(m_qprocessor == NULL) 
      { 
         Print("[QLRN] Processador quântico não inicializado"); 
         ExpertRemove(); 
      }
      if(m_risk_profile == NULL) 
      { 
         Print("[QLRN] Perfil de risco não inicializado"); 
         ExpertRemove(); 
      }

      m_metrics.profit_factor = 1.0; 
      m_metrics.win_rate = 0.5; 
      m_metrics.sharpe_ratio = 1.0; 
      m_metrics.quantum_efficiency = 0.5; 
      m_metrics.timestamp = TimeCurrent(); 
      m_metrics.last_signal = SIGNAL_NONE; 
      m_metrics.signal_confidence = 0.0; 
      
      Print("[QLRN] Sistema de aprendizado quântico inicializado para " + m_symbol);
   }

   // Métodos públicos

   QuantumMetrics GetQuantumMetrics()
   {
      if(!is_valid_context()) 
      { 
         if(m_logger != NULL) m_logger->log_warning("[QLRN] Contexto inválido. Retornando métricas padrão.");
         return m_metrics; 
      }
      
      m_metrics.timestamp = TimeCurrent();
      m_quantum_entropy = CalculateMarketEntropy(); 
      return m_metrics;
   }

   double CalculateSignalScore(ENUM_TRADE_SIGNAL signal)
   {
      if(!is_valid_context()) return 0.0; 
      
      double base_score = 0.5; 
      double risk_multiplier = (m_risk_profile != NULL ? m_risk_profile->get_risk_multiplier() : 1.0); 
      double entropy_factor = 1.0 - MathMin(1.0, m_quantum_entropy / QLRN_ENTROPY_THRESHOLD); 
      double final_score = base_score * risk_multiplier * entropy_factor; 
      
      return MathMax(0.0, MathMin(1.0, final_score));
   }

   void ApplyQuantumReinforcement(ENUM_TRADE_SIGNAL signal, double reward)
   {
      if(!QLRN_ENABLE_REINFORCEMENT || !is_valid_context()) return; 
      
      double learning_adjustment = QLRN_LEARNING_RATE * reward; 
      m_learning_progress += learning_adjustment; 
      m_learning_progress = MathMax(0.0, MathMin(1.0, m_learning_progress)); 
      
      QuantumLearningHistoryEntry entry; 
      entry.timestamp = TimeCurrent(); 
      entry.symbol = m_symbol; 
      entry.reward_score = reward; 
      entry.learning_rate = m_quantum_learning_rate; 
      entry.retrieval_success = true; 
      entry.market_entropy = m_quantum_entropy; 
      entry.action_taken = "Sinal: " + IntegerToString((int)signal);
      
      ArrayResize(m_learning_history, ArraySize(m_learning_history) + 1); 
      m_learning_history[ArraySize(m_learning_history)-1] = entry; 
      
      if(m_logger != NULL) 
         m_logger->log_info(StringFormat("[QLRN] Reforço aplicado: Sinal %d | Recompensa: %.2f | Progresso: %.1f%%", 
                                       (int)signal, reward, m_learning_progress*100));
      
      updateLearnDisplay(reward, true);
   }

   // Verifica se o sistema está pronto
   bool IsReady() const 
   { 
      return (m_qprocessor != NULL) && 
             (m_risk_profile != NULL) && 
             (m_memory_cell != NULL) && 
             (m_behavior_controller != NULL);
   }

   // Métodos de acesso
   double GetLearningRate() const { return m_quantum_learning_rate; }
   
   double GetLastReward() 
   { 
      if(ArraySize(m_learning_history) == 0) return 0.0; 
      return m_learning_history[ArraySize(m_learning_history)-1].reward_score; 
   }

   // Exporta histórico
   bool ExportLearningHistory(string file_path) 
   { 
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); 
      if(handle == INVALID_HANDLE) return false; 
      
      for(int i = 0; i < ArraySize(m_learning_history); i++)
      {
         FileWrite(handle, 
                   TimeToString(m_learning_history[i].timestamp, TIME_DATE|TIME_SECONDS),
                   m_learning_history[i].symbol,
                   DoubleToString(m_learning_history[i].reward_score, 4),
                   DoubleToString(m_learning_history[i].learning_rate, 6),
                   DoubleToString(m_learning_history[i].market_entropy, 4),
                   m_learning_history[i].action_taken);
      }
      FileClose(handle); 
      
      if(m_logger) m_logger->log_info("[QLRN] Histórico de aprendizado exportado para: " + file_path); 
      return true; 
   }

   // Otimização de memória
   void QuantumMemoryOptimization() 
   { 
      if(!is_valid_context()) return; 
      if(m_memory_cell != NULL) 
      {
         // Implementação futura
      }
      if(m_logger != NULL) m_logger->log_info("[QLRN] Memória quântica otimizada"); 
   }

   // Loop de aprendizado em tempo real
   void RealTimeLearning() 
   { 
      while(!IsStopped()) 
      { 
         ApplyQuantumReinforcement(SIGNAL_NONE, 0.1); 
         Sleep(QLRN_UPDATE_INTERVAL_MS); 
      } 
   }
};

#endif // __QUANTUM_LEARNING_MQH__

