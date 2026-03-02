//+------------------------------------------------------------------+
//| quantum_data_processor.mqh - Processador Quântico de Dados       |
//| Projeto: Genesis                                                 |
//| Pasta: Include/Quantum/                                          |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_DATA_PROCESSOR_MQH__
#define __QUANTUM_DATA_PROCESSOR_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumEntanglement.mqh>
#include <Genesis/Quantum/QuantumWaveletTransform.mqh>
#include <Genesis/Neural/QuantumNeuralFilter.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>
#ifdef GENESIS_ENABLE_UI
#include <Controls/Label.mqh>
#endif
#include <Genesis/Config/GenesisConfig.mqh>

// Configuração padrão (evitar inputs/variáveis globais em headers)
#ifndef QDP_QUBITS_PROCESSING
  #define QDP_QUBITS_PROCESSING CFG_QUBITS_PROCESSING
#endif
#ifndef QDP_ENTROPY_THRESHOLD
  #define QDP_ENTROPY_THRESHOLD CFG_ENTROPY_THRESHOLD
#endif
#ifndef QDP_ENABLE_QUANTUM_FILTER
  #define QDP_ENABLE_QUANTUM_FILTER CFG_ENABLE_Q_FILTER
#endif
#ifndef QDP_UPDATE_INTERVAL_MS
  #define QDP_UPDATE_INTERVAL_MS CFG_QDP_UPDATE_MS
#endif

struct QuantumProcessedData
{
   double             signal[];
   double             entropy_level;
   datetime           processing_time;
   int                dominant_mode;
   ENUM_TRADE_SIGNAL  generated_signal;
   double             signal_strength;
};

struct QuantumProcessingResult {
   datetime timestamp;
   string symbol;
   double entropy_level;
   int dominant_mode;
   double signal_strength;
   bool success;
   string processing_summary;
   ENUM_TRADE_SIGNAL generated_signal;
   double execution_time_ms;
};

class QuantumDataProcessor
{
private:
   logger_institutional *m_logger;
   QuantumEntanglement  *m_entangler;
   QuantumWaveletTransform *m_qwavelet;
   QuantumNeuralFilter  *m_qfilter;
   string               m_symbol;
   datetime             m_last_processing_time;

   QuantumProcessedData  m_qdata;
   double               m_processing_latency;
   
   QuantumProcessingResult m_processing_history[];
#ifdef GENESIS_ENABLE_UI
   CLabel *m_processor_label;
   CLabel *m_processor_signal;
#endif

   bool is_valid_context()
   {
       if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_error("[QDP] Sem conexão com o servidor de mercado"); return false; }
       if(!m_entangler || !m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_warning("[QDP] Emaranhamento quântico não ativo"); return false; }
       if(!m_qwavelet || !m_qwavelet->IsReady()) { if(m_logger) m_logger->log_warning("[QDP] Transformada wavelet não está pronta"); return false; }
       if(!m_qfilter || !m_qfilter->IsReady()) { if(m_logger) m_logger->log_warning("[QDP] Filtro neural não está pronto"); return false; }
      return true;
   }

   bool QuantumProcessSignal()
   {
       if(!is_valid_context()) { if(m_logger) m_logger->log_error("[QDP] Contexto inválido. Processamento bloqueado."); return false; }
      double start_time = GetMicrosecondCount();
       double price_superposition[]; ArrayResize(price_superposition, QDP_QUBITS_PROCESSING); for(int i=0;i<QDP_QUBITS_PROCESSING;i++){ price_superposition[i]=iClose(m_symbol, PERIOD_M1, i); }
       QuantumWaveletCoeffs coeffs = m_qwavelet->ExecuteQuantumWavelet(); if(coeffs.entropy_level < 0) { if(m_logger) m_logger->log_error("[QDP] Falha na transformada wavelet"); return false; }
      ArrayResize(m_qdata.signal, QDP_QUBITS_PROCESSING);
      for(int i=0; i<QDP_QUBITS_PROCESSING; i++)
      {
         double entangled_value[2];
          if(m_entangler->EntanglePair(
            coeffs.approximation[i%ArraySize(coeffs.approximation)], 
            coeffs.detail[i%ArraySize(coeffs.detail)], 
            entangled_value))
         { m_qdata.signal[i] = (entangled_value[0] + entangled_value[1])/2.0; }
         else
         { m_qdata.signal[i] = (coeffs.approximation[i%ArraySize(coeffs.approximation)] + coeffs.detail[i%ArraySize(coeffs.detail)])/2.0; }
      }
       if(QDP_ENABLE_QUANTUM_FILTER && m_qfilter)
       { if(!m_qfilter->QuantumDenoise(m_qdata.signal)) { if(m_logger) m_logger->log_warning("[QDP] Falha no denoise quântico - Continuando com fallback"); } }
      m_qdata.entropy_level = CalculateQuantumEntropy(m_qdata.signal);
      m_qdata.dominant_mode = IdentifyDominantMode(m_qdata.signal);
      m_qdata.processing_time = TimeCurrent();
      m_qdata.signal_strength = 1.0 - m_qdata.entropy_level;
      m_qdata.generated_signal = GenerateQuantumSignal();
      double end_time = GetMicrosecondCount(); double execution_time = (end_time - start_time) / 1000.0;
      QuantumProcessingResult result; result.timestamp = TimeCurrent(); result.symbol = m_symbol; result.entropy_level = m_qdata.entropy_level;
      result.dominant_mode = m_qdata.dominant_mode; result.signal_strength = m_qdata.signal_strength; result.success = true; result.generated_signal = m_qdata.generated_signal;
      result.execution_time_ms = execution_time; result.processing_summary = StringFormat("E:%.2f|M:%d|S:%.2f", m_qdata.entropy_level, m_qdata.dominant_mode, m_qdata.signal_strength);
       int __i = ArraySize(m_processing_history); ArrayResize(m_processing_history, __i + 1); m_processing_history[__i] = result;
       if(m_logger) m_logger->log_info("[QDP] Sinal processado - Entropia: " + DoubleToString(m_qdata.entropy_level,3) +
                        " | Modo dominante: " + IntegerToString(m_qdata.dominant_mode) +
                        " | Sinal: " + TradeSignalUtils().ToString(m_qdata.generated_signal) +
                        " | Tempo: " + DoubleToString(execution_time, 1) + "ms");
       m_last_processing_time = TimeCurrent(); updateProcessorDisplay(m_qdata.signal_strength, m_qdata.generated_signal); return true;
   }

   double CalculateQuantumEntropy(double &signal[])
   {
      if(ArraySize(signal) == 0) return 0.0;
      double energy = 0.0; for(int i=0; i<ArraySize(signal); i++) { if(!MathIsValidNumber(signal[i])) continue; energy += signal[i] * signal[i]; }
      if(energy <= 0) return 0.0; double entropy = 0.0;
      for(int i=0; i<ArraySize(signal); i++) { if(!MathIsValidNumber(signal[i])) continue; double p = (signal[i] * signal[i]) / energy; if(p > 0) entropy -= p * MathLog(p); }
      return MathMax(0.0, MathMin(1.0, entropy/MathLog(ArraySize(signal))));
   }

   int IdentifyDominantMode(double &signal[])
   {
      double max_power = -1; int dominant_idx = 0;
      for(int i=0; i<ArraySize(signal); i++)
      {
         if(!MathIsValidNumber(signal[i])) continue;
         double power = signal[i] * signal[i];
         if(power > max_power && power > QDP_ENTROPY_THRESHOLD) { max_power = power; dominant_idx = i; }
      }
      return dominant_idx;
   }

   ENUM_TRADE_SIGNAL GenerateQuantumSignal()
   {
      if(m_qdata.signal_strength > 0.8 && m_qdata.dominant_mode < 10) return SIGNAL_QUANTUM_FLASH;
      else if(m_qdata.entropy_level > 0.7) return SIGNAL_QUANTUM_ALERT;
      else if(m_qdata.signal_strength > 0.6) return SIGNAL_BUY;
      else if(m_qdata.signal_strength < 0.4) return SIGNAL_SELL; else return SIGNAL_NONE;
   }

   void updateProcessorDisplay(double signal_strength, ENUM_TRADE_SIGNAL signal)
   {
#ifdef GENESIS_ENABLE_UI
      if(m_processor_label == NULL)
      { m_processor_label = new CLabel("ProcessorLabel", 0, 10, 810); m_processor_label->Text("PROC: 0%"); m_processor_label->Color(clrGray); }
      if(m_processor_signal == NULL)
      { m_processor_signal = new CLabel("ProcessorSignal", 0, 10, 830); m_processor_signal->Text("SIG: NONE"); m_processor_signal->Color(clrGray); }
      m_processor_label->Text(StringFormat("PROC: %.0f%%", signal_strength * 100));
      m_processor_label->Color(signal_strength > 0.7 ? clrMagenta : signal_strength > 0.5 ? clrOrange : clrYellow);
      m_processor_signal->Text("SIG: " + TradeSignalUtils().ToString(signal));
      m_processor_signal->Color(signal == SIGNAL_QUANTUM_FLASH ? clrRed : signal == SIGNAL_BUY ? clrLime : signal == SIGNAL_SELL ? clrRed : clrGray);
#else
      Print(StringFormat("[QDP] PROC=%.0f%% | SIG=%s", signal_strength*100, TradeSignalUtils().ToString(signal)));
#endif
   }

public:
    QuantumDataProcessor(logger_institutional *logger,
                      QuantumEntanglement *qe, 
                      QuantumWaveletTransform *qwt, 
                      QuantumNeuralFilter *qnf,
                      string symbol = _Symbol) :
      m_logger(logger), m_entangler(qe), m_qwavelet(qwt), m_qfilter(qnf), m_symbol(symbol), m_processing_latency(0.0), m_last_processing_time(0)
   {
#ifdef GENESIS_ENABLE_UI
      m_processor_label = NULL;
      m_processor_signal = NULL;
#endif
      if(!m_logger || !m_logger->is_initialized()) { Print("[QDP] Logger não inicializado"); ExpertRemove(); }
      if(!m_entangler || !m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_error("[QDP] Emaranhamento quântico não ativo"); ExpertRemove(); }
      ArrayResize(m_qdata.signal, QDP_QUBITS_PROCESSING); m_qdata.entropy_level = 0.0; m_qdata.dominant_mode = -1; m_qdata.generated_signal = SIGNAL_NONE; m_qdata.signal_strength = 0.0;
      if(m_logger) m_logger->log_info("[QDP] Processador quântico inicializado com " + IntegerToString(QDP_QUBITS_PROCESSING) + " qubits");
   }

   QuantumProcessedData ProcessQuantumData()
   {
      if(QuantumProcessSignal()) return m_qdata;
      QuantumProcessedData error_data; ArrayResize(error_data.signal, QDP_QUBITS_PROCESSING); ArrayInitialize(error_data.signal, 0.0);
      error_data.entropy_level = -1; error_data.dominant_mode = -1; error_data.processing_time = TimeCurrent(); error_data.generated_signal = SIGNAL_NONE; error_data.signal_strength = 0.0;
      if(m_logger) m_logger->log_warning("[QDP] Falha no processamento quântico - Usando dados de fallback"); return error_data;
   }

   int GetQuantumMarketState()
   {
      if(m_qdata.entropy_level < 0.3) return 0; else if(m_qdata.entropy_level < 0.6) return 1; else return 2;
   }

   double GetQuantumProcessingLatency() const { return m_processing_latency; }
    bool IsReady() const { return m_entangler && m_entangler->IsEntanglementActive() && m_qwavelet && m_qwavelet->IsReady() && m_qfilter && m_qfilter->IsReady(); }
   ENUM_TRADE_SIGNAL GetLastSignal() const { return m_qdata.generated_signal; }
   bool ExportProcessingHistory(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); if(handle == INVALID_HANDLE) return false;
      for(int i = 0; i < ArraySize(m_processing_history); i++)
      {
         FileWrite(handle,
            TimeToString(m_processing_history[i].timestamp, TIME_DATE|TIME_SECONDS),
            m_processing_history[i].symbol,
            DoubleToString(m_processing_history[i].entropy_level, 4),
            IntegerToString(m_processing_history[i].dominant_mode),
            DoubleToString(m_processing_history[i].signal_strength, 4),
            m_processing_history[i].success ? "SIM" : "NÃO",
            m_processing_history[i].processing_summary,
            TradeSignalUtils().ToString(m_processing_history[i].generated_signal),
            DoubleToString(m_processing_history[i].execution_time_ms, 1)
         );
      }
      FileClose(handle); if(m_logger) m_logger->log_info("[QDP] Histórico de processamento exportado para: " + file_path); return true;
   }
};

#endif // __QUANTUM_DATA_PROCESSOR_MQH__


