//+------------------------------------------------------------------+
//| quantum_adaptive_learning.mqh - Aprendizado Quântico Adaptativo  |
//| Projeto: Genesis                                                |
//| Pasta: Include/Intelligence/                                    |
//| Versão: v2.1 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_ADAPTIVE_LEARNING_MQH__
#define __QUANTUM_ADAPTIVE_LEARNING_MQH__

#ifdef QAL_ENABLE_UI
#include <Controls/Label.mqh>
#endif
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumEntanglement.mqh>
#include <Genesis/Neural/QuantumNeuralNet.mqh>
#include <Genesis/Intelligence/QuantumLearning.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>

#ifndef QAL_QUBITS_LEARNING
#define QAL_QUBITS_LEARNING 512
#endif
#ifndef QAL_QUANTUM_LEARNING_RATE
#define QAL_QUANTUM_LEARNING_RATE 0.05
#endif
#ifndef QAL_ENABLE_ENTANGLED_LEARNING
#define QAL_ENABLE_ENTANGLED_LEARNING true
#endif
#ifndef QAL_UPDATE_INTERVAL_MS
#define QAL_UPDATE_INTERVAL_MS 300
#endif

// Removido: conflito com definição oficial em QuantumLearning.mqh

struct QuantumLearningResult {
   datetime timestamp;
   string symbol;
   double quantum_sharpe;
   double win_probability;
   double entropy_gain;
   double coherence_level;
   bool success;
   string learning_summary;
   ENUM_TRADE_SIGNAL last_signal;
   double execution_time_ms;
};

class QuantumAdaptiveLearning
{
private:
   logger_institutional *m_logger;
   QuantumEntanglement  *m_entangler;
   QuantumNeuralNet     *m_qnet;
   QuantumLearning      *m_qlearning;
   string               m_symbol;
   datetime             m_last_update_time;
   double               m_qweights[];
   QuantumMetrics       m_qmetrics;
   double               m_learning_entropy;
   QuantumLearningResult m_learning_history[];
#ifdef QAL_ENABLE_UI
   CLabel *m_learning_label;
   CLabel *m_learning_sharpe;
#endif

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_error("[QAL] Sem conexão com o servidor de mercado"); return false; }
      if(!m_entangler || !m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_warning("[QAL] Emaranhamento quântico não ativo"); return false; }
      if(!m_qnet || !m_qnet->IsQuantumReady()) { if(m_logger) m_logger->log_warning("[QAL] Rede neural quântica não está pronta"); return false; }
      if(!m_qlearning || !m_qlearning->IsReady()) { if(m_logger) m_logger->log_warning("[QAL] Sistema de aprendizado não está pronto"); return false; }
      return true;
   }

   bool QuantumWeightUpdate()
   {
      if(!is_valid_context()) { m_logger.log_error("[QAL] Contexto inválido. Atualização bloqueada."); return false; }
      double start_time = GetMicrosecondCount();
      double current_weights[]; if(!m_qnet->GetQuantumWeights(current_weights) || ArraySize(current_weights) == 0){ if(m_logger) m_logger->log_error("[QAL] Falha ao obter pesos quânticos da rede neural"); return false; }
      QuantumMetrics memory_metrics = m_qlearning->GetQuantumMetrics();
      ArrayResize(m_qweights, QAL_QUBITS_LEARNING);
       if(QAL_ENABLE_ENTANGLED_LEARNING && ArraySize(current_weights) > 0)
      {
         for(int i=0; i<QAL_QUBITS_LEARNING && i<ArraySize(current_weights); i++)
         {
            if(!MathIsValidNumber(current_weights[i])) continue;
            double entangled_weights[2];
            if(m_entangler->EntanglePair(current_weights[i], memory_metrics.coherence_level, entangled_weights))
               m_qweights[i] = current_weights[i] + QAL_QUANTUM_LEARNING_RATE * (entangled_weights[1] - current_weights[i]) * memory_metrics.coherence_level;
            else
               m_qweights[i] = current_weights[i] * 0.9 + memory_metrics.coherence_level * 0.1;
            m_qweights[i] = MathMax(0.01, MathMin(1.0, m_qweights[i]));
         }
      }
      else
      {
          for(int i=0; i<ArraySize(current_weights) && i<QAL_QUBITS_LEARNING; i++) if(MathIsValidNumber(current_weights[i])) m_qweights[i] = MathMax(0.01, MathMin(1.0, current_weights[i]));
      }
      m_qmetrics.quantum_sharpe = CalculateQuantumSharpe();
      m_qmetrics.win_probability = memory_metrics.win_rate;
      m_qmetrics.entropy_gain = CalculateEntropyGain();
      m_qmetrics.coherence_level = memory_metrics.coherence_level;
      m_qmetrics.timestamp = TimeCurrent();
      m_qmetrics.last_signal = memory_metrics.last_signal;
      m_qmetrics.signal_confidence = memory_metrics.signal_confidence;
      double end_time = GetMicrosecondCount(); double execution_time = (end_time - start_time) / 1000.0;
      QuantumLearningResult result; result.timestamp = TimeCurrent(); result.symbol = m_symbol; result.quantum_sharpe = m_qmetrics.quantum_sharpe; result.win_probability = m_qmetrics.win_probability; result.entropy_gain = m_qmetrics.entropy_gain; result.coherence_level = m_qmetrics.coherence_level; result.success = true; result.last_signal = m_qmetrics.last_signal; result.execution_time_ms = execution_time; result.learning_summary = StringFormat("SHARPE:%.2f|WIN:%.2f|COH:%.2f", m_qmetrics.quantum_sharpe, m_qmetrics.win_probability, m_qmetrics.coherence_level); ArrayPushBack(m_learning_history, result);
      if(m_logger) m_logger->log_info("[QAL] Pesos atualizados - Sharpe: " + DoubleToString(m_qmetrics.quantum_sharpe,3) + " | Coerência: " + DoubleToString(m_qmetrics.coherence_level,3) + " | Sinal: " + TradeSignalUtils().ToString(m_qmetrics.last_signal) + " | Tempo: " + DoubleToString(execution_time, 1) + "ms");
      m_last_update_time = TimeCurrent(); updateLearningDisplay(m_qmetrics.quantum_sharpe, m_qmetrics.last_signal); return true;
   }

   double CalculateQuantumSharpe()
   {
      if(ArraySize(m_learning_history) == 0) return 0.0; double avg_return = 0.0; double std_dev = 0.0; int count = 0; for(int i=0; i<ArraySize(m_learning_history); i++){ if(m_learning_history[i].success){ avg_return += m_learning_history[i].quantum_sharpe; std_dev += m_learning_history[i].quantum_sharpe * m_learning_history[i].quantum_sharpe; count++; }} if(count == 0) return 0.0; avg_return /= count; std_dev = MathSqrt(std_dev/count - avg_return*avg_return); return std_dev > 0 ? avg_return/std_dev : 0.0;
   }

   double CalculateEntropyGain()
   {
       if(ArraySize(m_qweights) == 0) return 0.0; double current_entropy = 0.0; for(int i=0; i<ArraySize(m_qweights); i++){ if(!MathIsValidNumber(m_qweights[i])) continue; double p = m_qweights[i] * m_qweights[i]; if(p > 0) current_entropy -= p * MathLog(p);} double memory_entropy = m_learning_entropy; return current_entropy - memory_entropy;
   }

   void updateLearningDisplay(double sharpe, ENUM_TRADE_SIGNAL signal)
   {
#ifdef QAL_ENABLE_UI
      if(m_learning_label == NULL) { m_learning_label = new CLabel("LearningLabel", 0, 10, 850); m_learning_label->Text("APREND: ????"); m_learning_label->Color(clrGray); }
      if(m_learning_sharpe == NULL) { m_learning_sharpe = new CLabel("LearningSharpe", 0, 10, 870); m_learning_sharpe->Text("SHARPE: 0.0"); m_learning_sharpe->Color(clrGray); }
      m_learning_label->Text("APREND: " + TradeSignalUtils().ToString(signal)); m_learning_label->Color(signal == SIGNAL_QUANTUM_FLASH ? clrRed : signal == SIGNAL_BUY ? clrLime : signal == SIGNAL_SELL ? clrRed : clrGray);
      m_learning_sharpe->Text("SHARPE: " + DoubleToString(sharpe, 2)); m_learning_sharpe->Color(sharpe > 2.0 ? clrLime : sharpe > 1.0 ? clrYellow : clrRed);
#else
      Print(StringFormat("[QAL] APREND=%s | SHARPE=%.2f", TradeSignalUtils().ToString(signal), sharpe));
#endif
   }

public:
   QuantumAdaptiveLearning(logger_institutional *logger, QuantumEntanglement *qe, QuantumNeuralNet *qnn, QuantumLearning *qlrn, string symbol = _Symbol)
      : m_logger(logger), m_entangler(qe), m_qnet(qnn), m_qlearning(qlrn), m_symbol(symbol), m_learning_entropy(0.0), m_last_update_time(0)
   {
#ifdef QAL_ENABLE_UI
      m_learning_label = NULL;
      m_learning_sharpe = NULL;
#endif
      if(!m_logger || !m_logger->is_initialized()) { Print("[QAL] Logger não inicializado"); ExpertRemove(); }
      if(!m_entangler || !m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_error("[QAL] Emaranhamento quântico não ativo"); ExpertRemove(); }
      ArrayResize(m_qweights, QAL_QUBITS_LEARNING); for(int i=0; i<QAL_QUBITS_LEARNING; i++) m_qweights[i] = 1.0/MathSqrt(QAL_QUBITS_LEARNING);
      m_qmetrics.quantum_sharpe = 0.0; m_qmetrics.win_probability = 0.5; m_qmetrics.entropy_gain = 0.0; m_qmetrics.coherence_level = 1.0; m_qmetrics.timestamp = TimeCurrent(); m_qmetrics.last_signal = SIGNAL_NONE; m_qmetrics.signal_confidence = 0.0;
      if(m_logger) m_logger->log_info("[QAL] Aprendizado quântico inicializado com " + IntegerToString(QAL_QUBITS_LEARNING) + " qubits");
   }

   bool UpdateLearning()
   {
      if(!QuantumWeightUpdate()) return false; m_qnet->AdjustWeights(QAL_QUANTUM_LEARNING_RATE); m_qlearning->ApplyQuantumReinforcement(m_qmetrics.last_signal, m_qmetrics.quantum_sharpe); return true;
   }

   bool GetQuantumWeights(double &weights[])
   { if(ArraySize(m_qweights) == 0) return false; ArrayCopy(weights, m_qweights); return true; }

   QuantumMetrics GetQuantumMetrics() const { return m_qmetrics; }
   double GetLearningEntropy() const { return m_learning_entropy; }
   bool IsReady() const { return (m_entangler && m_entangler->IsEntanglementActive()) && (m_qnet && m_qnet->IsQuantumReady()) && (m_qlearning && m_qlearning->IsReady()); }
   ENUM_TRADE_SIGNAL GetLastSignal() const { return m_qmetrics.last_signal; }
};

#endif // __QUANTUM_ADAPTIVE_LEARNING_MQH__


