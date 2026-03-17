//+------------------------------------------------------------------+
//| quantum_pattern_scanner.mqh - Scanner Quântico de Padrões        |
//| Projeto: Genesis                                                |
//| Pasta: Include/Detection/                                       |
//| Versão: v2.1 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_PATTERN_SCANNER_MQH__
#define __QUANTUM_PATTERN_SCANNER_MQH__

#ifdef GENESIS_ENABLE_UI
#include <Controls/Label.mqh>
#endif
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumEntanglement.mqh>
#include <Genesis/Analysis/QuantumHFTDetector.mqh>
#include <Genesis/Neural/QuantumNeuralNet.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>

class QuantumPatternScanner
{
private:
   logger_institutional *m_logger;
   QuantumEntanglement  *m_entangler;
   HFTDetector          *m_hftdetector;
   QuantumNeuralNet     *m_qnet;
   string               m_symbol;
   datetime             m_last_scan_time;

   struct QuantumPatternResult
   {
      bool             spoofing_detected;
      bool             iceberg_detected;
      bool             hft_activity;
      double           probability;
      datetime         detection_time;
      ENUM_TRADE_SIGNAL  generated_signal;
      double           signal_confidence;
   } m_last_result;

   double               m_scanning_entropy;
   struct QuantumPatternHistory {
      datetime timestamp;
      string symbol;
      bool spoofing_detected;
      bool iceberg_detected;
      bool hft_activity;
      double probability;
      ENUM_TRADE_SIGNAL generated_signal;
      double execution_time_ms;
      bool success;
   };
   QuantumPatternHistory m_pattern_history[];

#ifdef GENESIS_ENABLE_UI
   CLabel *m_pattern_label;
   CLabel *m_pattern_prob;
#endif

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         if(m_logger) m_logger->log_error("[QPS] Sem conexão com o servidor de mercado");
         return false;
      }
      if(!m_entangler || !m_entangler->IsEntanglementActive())
      {
         if(m_logger) m_logger->log_warning("[QPS] Emaranhamento quântico não ativo");
         return false;
      }
      if(!m_hftdetector || !m_hftdetector->IsReady())
      {
         if(m_logger) m_logger->log_warning("[QPS] Detector HFT não está pronto");
         return false;
      }
      if(!m_qnet || !m_qnet->IsQuantumReady())
      {
         if(m_logger) m_logger->log_warning("[QPS] Rede neural quântica não está pronta");
         return false;
      }
      return true;
   }

   bool QuantumScanPatterns()
   {
      if(!is_valid_context())
      {
         if(m_logger) m_logger->log_error("[QPS] Contexto inválido. Varredura bloqueada.");
         return false;
      }
      double start_time = GetMicrosecondCount();
      double price_volume[];
      if(!m_entangler->GetEntangledData(price_volume, 512))
      {
         if(m_logger) m_logger->log_error("[QPS] Falha ao obter dados emaranhados");
         return false;
      }
      bool spoofing = DetectQuantumSpoofing(price_volume);
      bool iceberg = DetectQuantumIceberg(price_volume);
      bool hft_activity = false;
      HFTResult hft_result;
      if(m_hftdetector->Analyze(hft_result))
         hft_activity = hft_result.hft_activity;
      double probability = CalculateQuantumProbability(spoofing, iceberg, hft_activity);
      m_last_result.spoofing_detected = spoofing;
      m_last_result.iceberg_detected = iceberg;
      m_last_result.hft_activity = hft_activity;
      m_last_result.probability = probability;
      m_last_result.detection_time = TimeCurrent();
      m_last_result.generated_signal = GenerateSignal(spoofing, iceberg, hft_activity, probability);
      m_last_result.signal_confidence = probability;
      double end_time = GetMicrosecondCount();
      double execution_time = (end_time - start_time) / 1000.0;
      QuantumPatternHistory record;
      record.timestamp = TimeCurrent();
      record.symbol = m_symbol;
      record.spoofing_detected = spoofing;
      record.iceberg_detected = iceberg;
      record.hft_activity = hft_activity;
      record.probability = probability;
      record.generated_signal = m_last_result.generated_signal;
      record.execution_time_ms = execution_time;
      record.success = true;
      ArrayPushBack(m_pattern_history, record);
      if(m_logger) m_logger->log_info("[QPS] Varredura concluída - Probabilidade: " + DoubleToString(probability,3) +
                        " | Sinal: " + TradeSignalUtils().ToString(m_last_result.generated_signal) +
                        " | Tempo: " + DoubleToString(execution_time, 1) + "ms");
      m_last_scan_time = TimeCurrent();
      updatePatternDisplay(probability, m_last_result.generated_signal);
      return true;
   }

   bool DetectQuantumSpoofing(double &data[])
   {
      if(ArraySize(data) == 0) return false;
      double spoofing_metric = 0.0;
      for(int i=0; i<ArraySize(data); i++)
      {
         if(DoubleIsNaN(data[i])) continue;
         double weight = 0.01;
        spoofing_metric += data[i] * weight;
      }
      return spoofing_metric > 0.15;
   }

   bool DetectQuantumIceberg(double &data[])
   {
      if(ArraySize(data) < 2) return false;
      double iceberg_metric = 0.0;
      for(int i=0; i<ArraySize(data)-1; i++)
      {
         if(DoubleIsNaN(data[i]) || DoubleIsNaN(data[i+1])) continue;
         double weight = 0.01;
         iceberg_metric += MathAbs(data[i+1] - data[i]) * weight;
      }
      return iceberg_metric > 0.15/2.0;
   }

   double CalculateQuantumProbability(bool spoofing, bool iceberg, bool hft)
   {
      int positive_signals = 0;
      if(spoofing) positive_signals++;
      if(iceberg) positive_signals++;
      if(hft) positive_signals++;
      double base_prob = (double)positive_signals / 3.0;
      double coherence_factor = m_entangler->GetCoherenceLevel();
      return MathMax(0.0, MathMin(1.0, base_prob * coherence_factor));
   }

   ENUM_TRADE_SIGNAL GenerateSignal(bool spoofing, bool iceberg, bool hft, double probability)
   {
      if(probability > 0.9)
      {
         if(spoofing && iceberg)
            return SIGNAL_QUANTUM_FLASH;
         else if(spoofing)
            return SIGNAL_QUANTUM_ALERT;
         else if(iceberg)
            return SIGNAL_QUANTUM_DARKPOOL;
      }
      else if(probability > 0.7)
      {
         if(hft)
            return SIGNAL_QUANTUM_HFT_SPIKE;
      }
      return SIGNAL_NONE;
   }

   void updatePatternDisplay(double probability, ENUM_TRADE_SIGNAL signal)
   {
#ifdef GENESIS_ENABLE_UI
      if(m_pattern_label == NULL)
      {
         m_pattern_label = new CLabel("PatternLabel", 0, 10, 1100);
         m_pattern_label->Text("PADRÃO: ????");
         m_pattern_label->Color(clrGray);
      }
      if(m_pattern_prob == NULL)
      {
         m_pattern_prob = new CLabel("PatternProb", 0, 10, 1120);
         m_pattern_prob->Text("PROB: 0%");
         m_pattern_prob->Color(clrGray);
      }
      m_pattern_label->Text("PADRÃO: " + TradeSignalUtils().ToString(signal));
      m_pattern_label->Color(
         signal == SIGNAL_QUANTUM_FLASH ? clrRed :
         signal == SIGNAL_QUANTUM_ALERT ? clrOrange :
         signal == SIGNAL_QUANTUM_DARKPOOL ? clrMagenta : clrGray
      );
      m_pattern_prob->Text("PROB: " + DoubleToString(probability*100, 0) + "%");
      m_pattern_prob->Color(
         probability > 0.8 ? clrLime :
         probability > 0.5 ? clrYellow : clrRed
      );
#else
      Print(StringFormat("[QPS] PADRÃO=%s | PROB=%.0f%%", TradeSignalUtils().ToString(signal), probability*100));
#endif
   }

public:
   QuantumPatternScanner(logger_institutional *logger,
                        QuantumEntanglement *qe, 
                        HFTDetector *hd, 
                        QuantumNeuralNet *qnn,
                        string symbol = _Symbol) :
      m_logger(logger), m_entangler(qe), m_hftdetector(hd), m_qnet(qnn), m_symbol(symbol),
      m_scanning_entropy(0.0), m_last_scan_time(0)
   {
#ifdef GENESIS_ENABLE_UI
      m_pattern_label = NULL;
      m_pattern_prob = NULL;
#endif
      if(!m_logger || !m_logger->is_initialized())
      {
         Print("[QPS] Logger não inicializado");
         ExpertRemove();
      }
      if(!m_entangler || !m_entangler->IsEntanglementActive())
      {
         if(m_logger) m_logger->log_error("[QPS] Emaranhamento quântico não ativo");
         ExpertRemove();
      }
      m_last_result.spoofing_detected = false;
      m_last_result.iceberg_detected = false;
      m_last_result.hft_activity = false;
      m_last_result.probability = 0.0;
      m_last_result.generated_signal = SIGNAL_NONE;
      m_last_result.signal_confidence = 0.0;
      if(m_logger) m_logger->log_info("[QPS] Scanner quântico inicializado com 512 qubits");
   }

   double GetScanningEntropy() const { return m_scanning_entropy; }
   bool IsReady() const { return m_entangler && m_entangler->IsEntanglementActive() && m_hftdetector && m_hftdetector->IsReady() && m_qnet && m_qnet->IsQuantumReady(); }
   ENUM_TRADE_SIGNAL GetLastSignal() const { return m_last_result.generated_signal; }
};

#endif // __QUANTUM_PATTERN_SCANNER_MQH__


