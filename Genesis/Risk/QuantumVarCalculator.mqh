//+------------------------------------------------------------------+
//| quantum_var_calculator.mqh - Quantum-Enhanced VaR Engine         |
//| Projeto: Genesis                                                 |
//| Pasta: Include/Risk/                                             |
//| Versão: v2.1                                                     |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_VAR_CALCULATOR_MQH__
#define __QUANTUM_VAR_CALCULATOR_MQH__

#include <Controls/Label.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Risk/RiskProfile.mqh>
#include <Genesis/Quantum/QuantumEntanglementSimulator.mqh>
#include <Genesis/Quantum/QuantumNoiseFilter.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>

enum ENUM_QUANTUM_VAR_METHOD
{
   VAR_HISTORICAL_CLASSIC,
   VAR_QUANTUM_ENTANGLED,
   VAR_SUPERPOSITION_ADAPTIVE,
   VAR_MONTE_CARLO_QUANTUM,
   VAR_HYBRID_NEURAL_QUBIT
};

struct QuantumVarResult
{
   double var_value;
   double confidence_level;
   datetime calculation_time;
   ENUM_QUANTUM_VAR_METHOD method_used;
   double risk_multiplier;
   double market_entropy;
};

class QuantumVarCalculator
{
private:
   logger_institutional          &m_logger;
   RiskProfile                   &m_risk_profile;
   QuantumEntanglementSimulator  &m_quantum_entangler;
   QuantumNoiseFilter            &m_qnoise_filter;
   string                         m_symbol;
   ENUM_TIMEFRAMES                m_timeframe;
   ENUM_QUANTUM_VAR_METHOD        m_var_method;
   QuantumVarResult               m_var_history[];
   CLabel                        *m_var_label = NULL;

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { m_logger.log_error("[VAR] Sem conexão com o servidor de mercado"); return false; }
      if(!SymbolInfoInteger(m_symbol, SYMBOL_SELECT)) { m_logger.log_error("[VAR] Símbolo inválido: " + m_symbol); return false; }
      if(!m_quantum_entangler.IsQuantumReady()) { m_logger.log_warning("[VAR] Simulador de entrelaçamento não está pronto"); return false; }
      if(!m_qnoise_filter.IsCalibrated()) { m_logger.log_warning("[VAR] Filtro de ruído quântico não calibrado"); return false; }
      return true;
   }

   double ApplyHeisenbergUncertainty(double returns[], int size)
   { double momentum = MathRand() / 32767.0; for(int i = 0; i < size; i++) returns[i] *= (1 + (momentum - 0.5) * 0.1); return momentum; }

   void ApplyQuantumNoiseFilter(double &returns[], int lookback) { m_qnoise_filter.FilterFinancialNoise(returns, lookback, m_timeframe); }

   double CalculateQuantumEntangledVaR(double confidence_level, int lookback)
   {
      double returns1[], returns2[]; ArrayResize(returns1, lookback); ArrayResize(returns2, lookback);
      m_quantum_entangler.GenerateEntangledReturns(m_symbol, returns1, returns2, lookback);
      for(int i = 0; i < lookback; i++) returns1[i] = (returns1[i] + returns2[i]) / MathSqrt(2.0);
      ArraySort(returns1); int index = (int)MathRound((1.0 - confidence_level) * lookback); if(index >= ArraySize(returns1)) index = ArraySize(returns1) - 1; if(index < 0) index = 0; return -returns1[index] * m_risk_profile.get_risk_multiplier();
   }

   double CalculateSuperpositionVaR(double confidence_level, int lookback)
   { double var_bull = CalculateHistoricalVaR(confidence_level, lookback, 1); double var_bear = CalculateHistoricalVaR(confidence_level, lookback, -1); if(var_bull <= 0 || var_bear <= 0) return MathMax(var_bull, var_bear); double var_superposition = (var_bull + var_bear - MathSqrt(var_bull * var_bear)) / 1.4142; return var_superposition * m_risk_profile.get_quantum_risk_factor(); }

   double CalculateHistoricalVaR(double confidence_level, int lookback, int mode = 0)
   {
      MqlRates rates[]; int copied = CopyRates(m_symbol, m_timeframe, 0, lookback, rates); if(copied <= 0) return 0.0; double returns[]; ArrayResize(returns, copied - 1);
      for(int i = 0; i < copied - 1; i++) { double ret = (rates[i].close - rates[i+1].close) / rates[i+1].close; returns[i] = ret; }
      ApplyQuantumNoiseFilter(returns, ArraySize(returns)); ApplyHeisenbergUncertainty(returns, ArraySize(returns)); ArraySort(returns); int index = (int)MathRound((1.0 - confidence_level) * ArraySize(returns)); if(index >= ArraySize(returns)) index = ArraySize(returns) - 1; if(index < 0) index = 0; return -returns[index];
   }

   void updateVarDisplay(double qvar, double confidence_level)
   {
      if(m_var_label == NULL) m_var_label = new CLabel("VarLabel", 0, 10, 190);
      m_var_label->text(StringFormat("VaR: %.2f%% | Conf: %.0f%%", qvar * 100, confidence_level * 100));
      m_var_label->color(qvar > 0.02 ? clrRed : qvar > 0.01 ? clrOrange : qvar > 0.005 ? clrYellow : clrLime);
   }

public:
   QuantumVarCalculator(logger_institutional &logger, RiskProfile &risk_profile, QuantumEntanglementSimulator &qentangler, QuantumNoiseFilter &qfilter, string symbol, ENUM_TIMEFRAMES timeframe = PERIOD_H1, ENUM_QUANTUM_VAR_METHOD method = VAR_QUANTUM_ENTANGLED)
      : m_logger(logger), m_risk_profile(risk_profile), m_quantum_entangler(qentangler), m_qnoise_filter(qfilter), m_symbol(symbol), m_timeframe(timeframe), m_var_method(method)
   {
      if(!m_logger.is_initialized()) { Print("[VAR] Logger não inicializado"); ExpertRemove(); }
      if(!m_quantum_entangler.IsQuantumReady() || !m_qnoise_filter.IsCalibrated()) { m_logger.log_error("[QUANTUM_VAR] Sistema quântico não inicializado!"); ExpertRemove(); }
      m_logger.log_info("[QUANTUM_VAR] Calculador Quântico ativado para " + m_symbol);
   }

   double GetQuantumVaR(double confidence_level = 0.95, int lookback = 252)
   {
      if(!is_valid_context()) { m_logger.log_warning("[VAR] Contexto inválido. Retornando 0.0"); return 0.0; }
      if(confidence_level <= 0.0 || confidence_level >= 1.0) { m_logger.log_error("[VAR] Nível de confiança inválido: " + DoubleToString(confidence_level)); return 0.0; }
      if(lookback <= 0) { m_logger.log_error("[VAR] Lookback inválido: " + IntegerToString(lookback)); return 0.0; }
      double qvar = 0.0; double market_entropy = m_qnoise_filter.GetMarketEntropy();
      switch(m_var_method)
      {
         case VAR_HISTORICAL_CLASSIC: qvar = CalculateHistoricalVaR(confidence_level, lookback); break;
         case VAR_QUANTUM_ENTANGLED: qvar = CalculateQuantumEntangledVaR(confidence_level, lookback); break;
         case VAR_SUPERPOSITION_ADAPTIVE: qvar = CalculateSuperpositionVaR(confidence_level, lookback); break;
         case VAR_MONTE_CARLO_QUANTUM: qvar = m_quantum_entangler.QuantumMonteCarloVaR(m_symbol, confidence_level, lookback); break;
         case VAR_HYBRID_NEURAL_QUBIT: qvar = m_quantum_entangler.HybridNeuralQubitVaR(m_symbol, confidence_level); break;
         default: m_logger.log_error("[VAR] Método de VaR desconhecido"); return CalculateHistoricalVaR(confidence_level, lookback);
      }
      double risk_multiplier = m_risk_profile.get_quantum_risk_factor(); qvar *= risk_multiplier;
      QuantumVarResult result; result.var_value = qvar; result.confidence_level = confidence_level; result.calculation_time = TimeCurrent(); result.method_used = m_var_method; result.risk_multiplier = risk_multiplier; result.market_entropy = market_entropy; ArrayPushBack(m_var_history, result);
      m_logger.log_info("[QUANTUM_VAR] " + EnumToString(m_var_method) + " VaR: " + DoubleToString(qvar, 4) + " | Confidence: " + DoubleToString(confidence_level * 100, 1) + "% | RM: " + DoubleToString(risk_multiplier, 2));
      updateVarDisplay(qvar, confidence_level); return qvar;
   }

   bool is_ready() const { return m_quantum_entangler.IsQuantumReady() && m_qnoise_filter.IsCalibrated(); }

   bool ExportHistory(string file_path)
   { int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); if(handle == INVALID_HANDLE) return false; for(int i = 0; i < ArraySize(m_var_history); i++){ FileWrite(handle, TimeToString(m_var_history[i].calculation_time, TIME_DATE|TIME_SECONDS), EnumToString(m_var_history[i].method_used), DoubleToString(m_var_history[i].var_value, 6), DoubleToString(m_var_history[i].confidence_level, 4), DoubleToString(m_var_history[i].risk_multiplier, 4), DoubleToString(m_var_history[i].market_entropy, 4)); } FileClose(handle); m_logger.log_info("[QUANTUM_VAR] Histórico exportado para: " + file_path); return true; }

   double getLastVaR() { if(ArraySize(m_var_history) == 0) return 0.0; return m_var_history[ArraySize(m_var_history)-1].var_value; }
};

#endif // __QUANTUM_VAR_CALCULATOR_MQH__


