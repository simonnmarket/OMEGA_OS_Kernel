//+------------------------------------------------------------------+
//| neural_signal_processor.mqh - Processador Neural Institucional   |
//| Projeto: Genesis                                                |
//| Versão: v2.1 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __NEURAL_SIGNAL_PROCESSOR_MQH__
#define __NEURAL_SIGNAL_PROCESSOR_MQH__

#include <Controls/Label.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Data/MarketDataConnector.mqh>
#include <Genesis/Intelligence/AnomalyDetectorAI.mqh>
#include <Genesis/Risk/RiskProfile.mqh>

#define INPUT_LAYER_SIZE      12
#define HIDDEN_LAYER_SIZE     24
#define OUTPUT_LAYER_SIZE     5
#define RETRAIN_INTERVAL      86400
#define MIN_TRAINING_SAMPLES  1000

// Compatibilidade
#define signal_to_string(sig) TradeSignalUtils::ToString(sig)

class NeuralSignalProcessor
{
private:
   logger_institutional &m_logger;
   market_data_connector &m_data_stream;
   RiskProfile &m_risk;
   AnomalyDetectorAI &m_ai;
   string m_symbol;
   bool m_is_initialized;
   datetime m_last_retrain;
   double m_weights[HIDDEN_LAYER_SIZE][INPUT_LAYER_SIZE];
   double m_biases[HIDDEN_LAYER_SIZE];
   double m_output_weights[OUTPUT_LAYER_SIZE][HIDDEN_LAYER_SIZE];
   double m_output_bias[OUTPUT_LAYER_SIZE];
   struct SignalHistory { datetime timestamp; ENUM_TRADE_SIGNAL signal; double confidence; double profit; };
   SignalHistory m_signal_history[];
   CLabel *m_neural_label = NULL;

   void InitializeWeights()
   {
      for(int i = 0; i < HIDDEN_LAYER_SIZE; i++) { m_biases[i] = MathRand() / 32767.0 - 0.5; for(int j = 0; j < INPUT_LAYER_SIZE; j++) m_weights[i][j] = MathRand() / 32767.0 - 0.5; }
      for(int i = 0; i < OUTPUT_LAYER_SIZE; i++) { m_output_bias[i] = MathRand() / 32767.0 - 0.5; for(int j = 0; j < HIDDEN_LAYER_SIZE; j++) m_output_weights[i][j] = MathRand() / 32767.0 - 0.5; }
   }

   double ReLU(double x) { return MathMax(0.0, x); }
   double ReLUDerivative(double x) { return x > 0 ? 1.0 : 0.0; }

   void NormalizeFeature(double &value, double mean, double stddev) { if(stddev != 0 && !DoubleIsNaN(mean) && !DoubleIsNaN(stddev)) value = (value - mean) / stddev; else value = 0.0; }

   bool ExtractFeatures(double &features[])
   {
      ArrayResize(features, INPUT_LAYER_SIZE);
      features[0] = iRSI(m_symbol, PERIOD_H1, 14, PRICE_CLOSE, 0);
      features[1] = iATR(m_symbol, PERIOD_H1, 14, 0) / SymbolInfoDouble(m_symbol, SYMBOL_POINT);
      features[2] = iADX(m_symbol, PERIOD_H1, 14, PRICE_CLOSE, MODE_PLUSDI, 0);
      features[3] = iMACD(m_symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
      features[4] = Volume[0];
      features[5] = getOrderBookImbalance();
      features[6] = getVolatilityIndex();
      features[7] = fmod(TimeCurrent(), 86400) / 86400;
      features[8] = DayOfWeek() / 7.0;
      features[9] = calculateQuantumEntropy();
      features[10] = 0.5; // placeholder
      features[11] = 1.0; // placeholder
      for(int i = 0; i < INPUT_LAYER_SIZE; i++) if(DoubleIsNaN(features[i])) { m_logger.log_error(StringFormat("[NEURAL] Feature %d é NaN", i)); return false; }
      double means[] = {50, 20, 30, 0, 1000, 0, 0.5, 0.5, 0.5, 0.5, 0.5, 1.0};
      double stddevs[] = {15, 10, 15, 1.5, 500, 1.0, 0.2, 0.3, 0.2, 0.2, 0.2, 0.5};
      for(int i = 0; i < INPUT_LAYER_SIZE; i++) NormalizeFeature(features[i], means[i], stddevs[i]);
      return true;
   }

   double calculateQuantumEntropy()
   { MqlRates rates[]; CopyRates(m_symbol, PERIOD_M1, 0, 20, rates); double entropy = 0.0, sum = 0.0; for(int i = 0; i < ArraySize(rates); i++) sum += rates[i].close; if(sum <= 0) return 0.0; for(int i = 0; i < ArraySize(rates); i++){ double p = rates[i].close / sum; if(p > 0) entropy -= p * MathLog(p);} return NormalizeDouble(entropy, 4); }

   double getOrderBookImbalance() { return (MathRand() % 200 - 100) / 100.0; }
   double getVolatilityIndex() { double atr = iATR(m_symbol, PERIOD_H1, 14, 0); double avg_price = (SymbolInfoDouble(m_symbol, SYMBOL_ASK) + SymbolInfoDouble(m_symbol, SYMBOL_BID)) / 2; return atr / avg_price; }

   void FeedForward(double &inputs[], double &outputs[])
   {
      double hidden[HIDDEN_LAYER_SIZE]; for(int i = 0; i < HIDDEN_LAYER_SIZE; i++){ double sum = m_biases[i]; for(int j = 0; j < INPUT_LAYER_SIZE; j++) sum += inputs[j] * m_weights[i][j]; hidden[i] = ReLU(sum);} for(int i = 0; i < OUTPUT_LAYER_SIZE; i++){ double sum = m_output_bias[i]; for(int j = 0; j < HIDDEN_LAYER_SIZE; j++) sum += hidden[j] * m_output_weights[i][j]; outputs[i] = sigmoid(sum);} softmax(outputs, OUTPUT_LAYER_SIZE);
   }

   double sigmoid(double x) { return 1.0 / (1.0 + MathExp(-MathMax(-50.0, MathMin(50.0, x)))); }
   void softmax(double &values[], int size) { double max_val = values[0]; for(int i = 1; i < size; i++) if(values[i] > max_val) max_val = values[i]; double sum = 0.0; for(int i = 0; i < size; i++){ values[i] = MathExp(values[i] - max_val); sum += values[i]; } if(sum > 0) for(int i = 0; i < size; i++) values[i] /= sum; }

   ENUM_TRADE_SIGNAL PostprocessOutput(double &output[])
   {
      double buy_strength = output[0] + output[1]; double sell_strength = output[3] + output[4]; double hold_strength = output[2]; double threshold_high = 0.7; double threshold_low = 0.55;
      if(buy_strength > threshold_high && buy_strength > sell_strength) return (output[0] > output[1]) ? SIGNAL_QUANTUM_ALERT : SIGNAL_BUY;
      else if(sell_strength > threshold_high && sell_strength > buy_strength) return (output[4] > output[3]) ? SIGNAL_DARKPOOL_CRITICAL : SIGNAL_SELL;
      else if(buy_strength > threshold_low) return SIGNAL_REVERSE_BUY;
      else if(sell_strength > threshold_low) return SIGNAL_REVERSE_SELL;
      else if(hold_strength > 0.6) return SIGNAL_NONE; return SIGNAL_BREAK_EVEN;
   }

   void updateNeuralDisplay(ENUM_TRADE_SIGNAL signal, double &output[])
   {
      if(m_neural_label == NULL) m_neural_label = new CLabel("NeuralLabel", 0, 10, 150);
      m_neural_label->text(StringFormat("IA: %s | Conf: %.2f%%", signal_to_string(signal), MathMax(output[0], MathMax(output[1], MathMax(output[2], MathMax(output[3], output[4])))) * 100));
      m_neural_label->color(signal == SIGNAL_QUANTUM_ALERT ? clrMagenta : signal == SIGNAL_DARKPOOL_CRITICAL ? clrRed : signal == SIGNAL_BUY ? clrLime : signal == SIGNAL_SELL ? clrRed : clrWhite);
   }

public:
   NeuralSignalProcessor(logger_institutional &logger, market_data_connector &data_stream, RiskProfile &risk, AnomalyDetectorAI &ai, string symbol)
      : m_logger(logger), m_data_stream(data_stream), m_risk(risk), m_ai(ai)
   {
      m_symbol = symbol; m_is_initialized = false; m_last_retrain = 0; if(!m_logger.is_initialized()) { m_logger.log_error("[NEURAL] Logger não inicializado"); return; } if(StringLen(m_symbol) == 0 || !SymbolInfoInteger(m_symbol, SYMBOL_SELECT)) { m_logger.log_error("[NEURAL] Símbolo inválido: " + m_symbol); return; } InitializeWeights(); m_is_initialized = true; m_logger.log_info("[NEURAL] Processador neural inicializado para " + m_symbol);
   }

   ENUM_TRADE_SIGNAL ProcessSignal()
   {
      if(!m_is_initialized) { m_logger.log_error("[NEURAL] Tentativa de processar sinal sem inicialização"); return SIGNAL_NONE; }
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { m_logger.log_warning("[NEURAL] Sem conexão com o servidor"); return SIGNAL_NONE; }
      double inputs[INPUT_LAYER_SIZE]; if(!ExtractFeatures(inputs)) { m_logger.log_error("[NEURAL] Falha na extração de features"); return SIGNAL_NONE; }
      double outputs[OUTPUT_LAYER_SIZE]; FeedForward(inputs, outputs);
      ENUM_TRADE_SIGNAL signal = PostprocessOutput(outputs);
      SignalHistory hist; hist.timestamp = TimeCurrent(); hist.signal = signal; hist.confidence = MathMax(outputs[0], MathMax(outputs[1], MathMax(outputs[2], MathMax(outputs[3], outputs[4])))); ArrayPushBack(m_signal_history, hist);
      m_logger.log_info(StringFormat("[NEURAL] Sinal gerado: %s", signal_to_string(signal)));
      updateNeuralDisplay(signal, outputs);
      return signal;
   }
};

#endif // __NEURAL_SIGNAL_PROCESSOR_MQH__


