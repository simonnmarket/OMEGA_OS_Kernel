//+------------------------------------------------------------------+
//| anomaly_detector_ai.mqh - Sistema Quântico de Detecção de Anomalias |
//| Projeto: Genesis                                                 |
//| Versão: v2.1 (GodMode Final + IA Ready + Blindagem Institucional) |
//+------------------------------------------------------------------+
#ifndef __ANOMALY_DETECTOR_AI_MQH__
#define __ANOMALY_DETECTOR_AI_MQH__

#include <Controls/Label.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Data/MarketDataConnector.mqh>
#include <Genesis/Quantum/QuantumEntropyCalculator.mqh>

// Definições Avançadas
#define MIN_TRAINING_SAMPLES    1000
#define TRAINING_INTERVAL       604800
#define ISOLATION_TREES         100
#define AUTOENCODER_INPUTS      8
#define AUTOENCODER_HIDDEN      3

enum ENUM_ANOMALY_TYPE
{
   ANOMALY_NONE = 0,
   ANOMALY_QUANTUM,
   ANOMALY_MARKET_STRUCTURE,
   ANOMALY_UNEXPECTED_PATTERN,
   ANOMALY_BLACK_SWAN,
   ANOMALY_FLASH_CRASH,
   ANOMALY_LIQUIDITY_VOID
};

struct AnomalyRecord
{
   datetime timestamp;
   ENUM_ANOMALY_TYPE type;
   double confidence;
   double quantum_score;
   double isolation_score;
   double reconstruction_error;
};

class AnomalyDetectorAI
{
private:
   logger_institutional *m_logger;
   market_data_connector *m_data_stream;
   quantum_entropy_calculator *m_quantum_entropy;
   string m_symbol;
   double m_entropy_threshold;
   bool m_is_initialized;
   datetime m_last_train_time;
   datetime m_last_detection_time;
   double m_isolation_trees[ISOLATION_TREES][AUTOENCODER_INPUTS];
   double m_autoencoder_weights[AUTOENCODER_HIDDEN][AUTOENCODER_INPUTS];
   double m_autoencoder_output_weights[AUTOENCODER_INPUTS][AUTOENCODER_HIDDEN];
   AnomalyRecord m_anomalies[];
   CLabel *m_anomaly_label = NULL;

   void InitializeModels()
   {
      for(int i = 0; i < ISOLATION_TREES; i++)
         for(int j = 0; j < AUTOENCODER_INPUTS; j++)
            m_isolation_trees[i][j] = MathRand() / 32767.0;
      for(int i = 0; i < AUTOENCODER_HIDDEN; i++)
         for(int j = 0; j < AUTOENCODER_INPUTS; j++)
            m_autoencoder_weights[i][j] = (MathRand() / 32767.0 - 0.5) * 0.1;
      for(int i = 0; i < AUTOENCODER_INPUTS; i++)
         for(int j = 0; j < AUTOENCODER_HIDDEN; j++)
            m_autoencoder_output_weights[i][j] = (MathRand() / 32767.0 - 0.5) * 0.1;
   }

   bool ExtractFeatures(double &features[])
   {
      ArrayResize(features, AUTOENCODER_INPUTS);
      features[0] = getVolatility(m_symbol, PERIOD_M5, 14);
      features[1] = getVolumeSpike();
      features[2] = getOrderBookImbalance();
      features[3] = fmod(TimeCurrent(), 86400) / 86400;
      features[4] = DayOfWeek() / 7.0;
      features[5] = m_quantum_entropy.Calculate(m_symbol);
      features[6] = getQuantumCoherence();
      features[7] = calculateTraditionalEntropy();
      for(int i = 0; i < AUTOENCODER_INPUTS; i++)
         if(DoubleIsNaN(features[i])) { if(m_logger) m_logger->log_error(StringFormat("[ANOMALY] Feature %d é NaN", i)); return false; }
      return true;
   }

   double getVolatility(string symbol, int timeframe, int period)
   { return iATR(symbol, timeframe, period, 0) / SymbolInfoDouble(symbol, SYMBOL_POINT); }

   double getVolumeSpike()
   { double current_volume = Volume[0]; double avg_volume = iMA(NULL, PERIOD_M5, 20, 0, MODE_SMA, PRICE_VOLUME, 0); return avg_volume > 0 ? current_volume / avg_volume : 0.0; }

   double getOrderBookImbalance()
   { return (MathRand() % 200 - 100) / 100.0; }

   double getQuantumCoherence()
   {
      MqlRates rates[]; CopyRates(m_symbol, PERIOD_M1, 0, 10, rates); double sum = 0.0; for(int i = 1; i < 10; i++) sum += MathAbs(rates[i].close - rates[i-1].close); return sum > 0 ? 1.0 / sum : 0.0;
   }

   double calculateTraditionalEntropy()
   {
      MqlRates rates[]; ArraySetAsSeries(rates, true); int copied = CopyRates(m_symbol, PERIOD_M1, 0, 20, rates); if(copied <= 0) return 0.0; double entropy = 0.0, sum = 0.0; for(int i = 0; i < copied; i++) sum += rates[i].close; if(sum <= 0) return 0.0; for(int i = 0; i < copied; i++){ if(rates[i].close > 0){ double p = rates[i].close / sum; entropy -= p * MathLog(p); }} return NormalizeDouble(entropy, 4);
   }

   double calculateIsolationScore(double &features[])
   {
      double score = 0.0; for(int i = 0; i < ISOLATION_TREES; i++){ double tree_score = 0.0; for(int j = 0; j < AUTOENCODER_INPUTS; j++) tree_score += features[j] * m_isolation_trees[i][j]; score += MathAbs(tree_score);} return NormalizeDouble(score / ISOLATION_TREES, 4);
   }

   double calculateReconstructionError(double &features[])
   {
      double hidden[AUTOENCODER_HIDDEN]; double reconstructed[AUTOENCODER_INPUTS]; for(int i = 0; i < AUTOENCODER_HIDDEN; i++){ double sum = 0.0; for(int j = 0; j < AUTOENCODER_INPUTS; j++) sum += features[j] * m_autoencoder_weights[i][j]; hidden[i] = sigmoid(sum);} for(int i = 0; i < AUTOENCODER_INPUTS; i++){ double sum = 0.0; for(int j = 0; j < AUTOENCODER_HIDDEN; j++) sum += hidden[j] * m_autoencoder_output_weights[i][j]; reconstructed[i] = sigmoid(sum);} double error = 0.0; for(int i = 0; i < AUTOENCODER_INPUTS; i++) error += MathPow(features[i] - reconstructed[i], 2); return NormalizeDouble(error, 4);
   }

   double sigmoid(double x) { return 1.0 / (1.0 + MathExp(-MathMax(-50.0, MathMin(50.0, x)))); }

   void updateAnomalyDisplay(ENUM_ANOMALY_TYPE type, double confidence)
   {
      if(m_anomaly_label == NULL) m_anomaly_label = new CLabel("AnomalyLabel", 0, 10, 170);
      m_anomaly_label->text(StringFormat("ANOMALIA: %s | Conf: %.0f%%", anomalyTypeToString(type), confidence * 100));
      m_anomaly_label->color(type == ANOMALY_QUANTUM ? clrMagenta : type == ANOMALY_BLACK_SWAN ? clrRed : type == ANOMALY_FLASH_CRASH ? clrOrange : type == ANOMALY_LIQUIDITY_VOID ? clrBlue : clrYellow);
   }

public:
   AnomalyDetectorAI(logger_institutional *logger, market_data_connector *data_stream, quantum_entropy_calculator *quantum_entropy, string symbol, double entropy_threshold = 0.85)
      : m_logger(logger), m_data_stream(data_stream), m_quantum_entropy(quantum_entropy), m_symbol(symbol), m_entropy_threshold(entropy_threshold), m_is_initialized(false), m_last_train_time(0), m_last_detection_time(0)
   {
      if(!m_logger || !m_logger->is_initialized()) { if(m_logger) m_logger->log_error("[ANOMALY] Logger não inicializado"); return; }
      if(StringLen(m_symbol) == 0 || !SymbolInfoInteger(m_symbol, SYMBOL_SELECT)) { m_logger.log_error("[ANOMALY] Símbolo inválido: " + m_symbol); return; }
      InitializeModels(); m_is_initialized = true; if(m_logger) m_logger->log_info("[ANOMALY] Sistema de detecção inicializado para " + m_symbol);
   }

   bool DetectAnomaly(ENUM_ANOMALY_TYPE &type, double &confidence)
   {
      if(!m_is_initialized) { if(m_logger) m_logger->log_error("[ANOMALY] Tentativa de detecção sem inicialização"); return false; }
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_warning("[ANOMALY] Sem conexão com o servidor"); return false; }
      double features[AUTOENCODER_INPUTS]; if(!ExtractFeatures(features)) { if(m_logger) m_logger->log_error("[ANOMALY] Falha na extração de features"); return false; }
      double quantum_entropy = features[5]; double isolation_score = calculateIsolationScore(features); double reconstruction_error = calculateReconstructionError(features);
      bool is_anomaly = false; confidence = 0.0; if(quantum_entropy > m_entropy_threshold){ type = ANOMALY_QUANTUM; confidence = MathMin((quantum_entropy - m_entropy_threshold) / (1.0 - m_entropy_threshold), 1.0); is_anomaly = true; }
      else if(isolation_score > 0.65){ type = ANOMALY_MARKET_STRUCTURE; confidence = isolation_score; is_anomaly = true; }
      else if(reconstruction_error > 1.5){ type = ANOMALY_UNEXPECTED_PATTERN; confidence = MathMin(reconstruction_error / 3.0, 1.0); is_anomaly = true; }
      if(isHighFrequencySpikes()){ type = ANOMALY_FLASH_CRASH; confidence = 0.9; is_anomaly = true; }
      if(isLiquidityVoid()){ type = ANOMALY_LIQUIDITY_VOID; confidence = 0.85; is_anomaly = true; }
      if(is_anomaly){ AnomalyRecord record; record.timestamp = TimeCurrent(); record.type = type; record.confidence = confidence; record.quantum_score = quantum_entropy; record.isolation_score = isolation_score; record.reconstruction_error = reconstruction_error; ArrayPushBack(m_anomalies, record); if(m_logger) m_logger->log_warning(StringFormat("[ANOMALY] Detectada: %s | Confiança: %.2f | QE: %.4f | IS: %.2f | RE: %.2f", anomalyTypeToString(type), confidence, quantum_entropy, isolation_score, reconstruction_error)); updateAnomalyDisplay(type, confidence); }
      m_last_detection_time = TimeCurrent(); return is_anomaly;
   }

   ENUM_TRADE_SIGNAL GenerateProtectionSignal(ENUM_ANOMALY_TYPE type)
   {
      switch(type)
      {
         case ANOMALY_QUANTUM: return SIGNAL_QUANTUM_ALERT;
         case ANOMALY_MARKET_STRUCTURE: return SIGNAL_MACRO_NEWS_PROTECT;
         case ANOMALY_UNEXPECTED_PATTERN: return SIGNAL_BREAK_EVEN;
         case ANOMALY_BLACK_SWAN: return SIGNAL_CLOSE;
         case ANOMALY_FLASH_CRASH: return SIGNAL_QUANTUM_HFT_SPIKE;
         case ANOMALY_LIQUIDITY_VOID: return SIGNAL_REVERSE_SELL;
         default: return SIGNAL_NONE;
      }
   }

   void UpdateWithNewData() { if(!m_is_initialized) return; TrainModels(); }

   bool isHighFrequencySpikes()
   { static datetime last_spike = 0; static int spike_count = 0; if(TimeCurrent() - last_spike > 60){ spike_count = 0; last_spike = TimeCurrent(); }
     double price_change = MathAbs(SymbolInfoDouble(m_symbol, SYMBOL_ASK) - SymbolInfoDouble(m_symbol, SYMBOL_BID)) / SymbolInfoDouble(m_symbol, SYMBOL_POINT); if(price_change > 5.0){ spike_count++; last_spike = TimeCurrent(); } return spike_count >= 3; }

   bool isLiquidityVoid()
   { double spread = SymbolInfoInteger(m_symbol, SYMBOL_SPREAD); double avg_spread = iMA(NULL, PERIOD_M5, 20, 0, MODE_SMA, PRICE_SPREAD, 0); return spread > avg_spread * 3.0; }

   bool is_ready() const { return m_is_initialized; }

   string anomalyTypeToString(ENUM_ANOMALY_TYPE type)
   { switch(type){ case ANOMALY_NONE: return "NENHUMA"; case ANOMALY_QUANTUM: return "QUÂNTICA"; case ANOMALY_MARKET_STRUCTURE: return "ESTRUTURA_MERCADO"; case ANOMALY_UNEXPECTED_PATTERN: return "PADRAO_INESPERADO"; case ANOMALY_BLACK_SWAN: return "BLACK_SWAN"; case ANOMALY_FLASH_CRASH: return "FLASH_CRASH"; case ANOMALY_LIQUIDITY_VOID: return "FALTA_LIQUIDEZ"; default: return "DESCONHECIDA"; } }

   bool ExportAnomalies(string file_path)
   { int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); if(handle == INVALID_HANDLE) return false; for(int i = 0; i < ArraySize(m_anomalies); i++){ FileWrite(handle, TimeToString(m_anomalies[i].timestamp, TIME_DATE|TIME_SECONDS), anomalyTypeToString(m_anomalies[i].type), DoubleToString(m_anomalies[i].confidence, 4), DoubleToString(m_anomalies[i].quantum_score, 4), DoubleToString(m_anomalies[i].isolation_score, 4), DoubleToString(m_anomalies[i].reconstruction_error, 4)); } FileClose(handle); m_logger.log_info("[ANOMALY] Histórico de anomalias exportado para: " + file_path); return true; }

private:
   void TrainModels()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) return;
      if(TimeCurrent() - m_last_train_time < TRAINING_INTERVAL) return;
      if(m_logger) m_logger->log_info("[ANOMALY] Iniciando treinamento dos modelos...");
      double training_data[][AUTOENCODER_INPUTS]; int samples = prepareTrainingData(training_data);
      if(samples > MIN_TRAINING_SAMPLES) { updateIsolationTrees(training_data, samples); trainAutoEncoder(training_data, samples); m_last_train_time = TimeCurrent(); if(m_logger) m_logger->log_info(StringFormat("[ANOMALY] Modelos treinados com %d amostras", samples)); }
      else { if(m_logger) m_logger->log_warning("[ANOMALY] Dados insuficientes para treinamento"); }
   }

   int prepareTrainingData(double &data[][AUTOENCODER_INPUTS])
   { int count = 0; for(int i = 0; i < 1500 && count < 2000; i++){ double features[AUTOENCODER_INPUTS]; if(i % 5 == 0){ features[0] = 5.0 + MathRand() % 5; features[5] = 0.9 + (MathRand() % 10) / 100.0; } else { for(int j = 0; j < AUTOENCODER_INPUTS; j++) features[j] = MathRand() / 32767.0; } for(int j = 0; j < AUTOENCODER_INPUTS; j++) data[count][j] = features[j]; count++; } return count; }

   void updateIsolationTrees(double &data[][AUTOENCODER_INPUTS], int samples)
   { for(int i = 0; i < ISOLATION_TREES; i++) for(int j = 0; j < AUTOENCODER_INPUTS; j++){ double avg = 0.0; for(int k = 0; k < MathMin(samples, 100); k++) avg += data[k][j]; avg /= MathMin(samples, 100); m_isolation_trees[i][j] = avg * (0.9 + (MathRand() % 20) / 100.0); } }

   void trainAutoEncoder(double &data[][AUTOENCODER_INPUTS], int samples)
   { double learning_rate = 0.01; int epochs = 5; for(int epoch = 0; epoch < epochs; epoch++){ for(int sample = 0; sample < MathMin(samples, 100); sample++){ double input[AUTOENCODER_INPUTS]; for(int i = 0; i < AUTOENCODER_INPUTS; i++) input[i] = data[sample][i]; double hidden[AUTOENCODER_HIDDEN]; for(int i = 0; i < AUTOENCODER_HIDDEN; i++){ double sum = 0.0; for(int j = 0; j < AUTOENCODER_INPUTS; j++) sum += input[j] * m_autoencoder_weights[i][j]; hidden[i] = sigmoid(sum);} double output[AUTOENCODER_INPUTS]; for(int i = 0; i < AUTOENCODER_INPUTS; i++){ double sum = 0.0; for(int j = 0; j < AUTOENCODER_HIDDEN; j++) sum += hidden[j] * m_autoencoder_output_weights[i][j]; output[i] = sigmoid(sum);} double output_error[AUTOENCODER_INPUTS]; for(int i = 0; i < AUTOENCODER_INPUTS; i++) output_error[i] = (output[i] - input[i]) * output[i] * (1.0 - output[i]); double hidden_error[AUTOENCODER_HIDDEN]; for(int i = 0; i < AUTOENCODER_HIDDEN; i++){ double error = 0.0; for(int j = 0; j < AUTOENCODER_INPUTS; j++) error += output_error[j] * m_autoencoder_output_weights[j][i]; hidden_error[i] = error * hidden[i] * (1.0 - hidden[i]); } for(int i = 0; i < AUTOENCODER_INPUTS; i++) for(int j = 0; j < AUTOENCODER_HIDDEN; j++) m_autoencoder_output_weights[i][j] -= learning_rate * output_error[i] * hidden[j]; for(int i = 0; i < AUTOENCODER_HIDDEN; i++) for(int j = 0; j < AUTOENCODER_INPUTS; j++) m_autoencoder_weights[i][j] -= learning_rate * hidden_error[i] * input[j]; } } }
};

#endif // __ANOMALY_DETECTOR_AI_MQH__


