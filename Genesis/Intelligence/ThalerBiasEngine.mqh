//+------------------------------------------------------------------+
//| thaler_quantum_bias_engine.mqh - Motor de Viés Quântico         |
//| Projeto: Genesis                                                |
//| Versão: v2.1 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __THALER_QUANTUM_BIAS_ENGINE_MQH__
#define __THALER_QUANTUM_BIAS_ENGINE_MQH__

#include <Controls/Label.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Risk/RiskProfile.mqh>
// Forward declarations para evitar include circular
class MarketRegimeDetector;
#include <Genesis/Core/TradeSignalEnum.mqh>

// Compatibilidade
#define trade_signal ENUM_TRADE_SIGNAL
#define signal_to_string(sig) (TradeSignalUtils().ToString(sig))

// Configuração interna (evita inputs em headers)
bool   m_simulate_default   = true;
double m_kelly_min_default  = 0.3;
double m_kelly_max_default  = 2.5;
double m_herding_threshold_default = 0.82;

class ThalerQuantumBiasEngine
{
private:
   struct QuantumMetrics { double quantum_entropy; double neuro_sentiment; double darkpool_imbalance; double kelly_adaptive; } m_quantum_metrics;
   logger_institutional *m_logger;
   MarketRegimeDetector *m_regime_detector;
   RiskProfile *m_risk_profile;
   CLabel *m_quantum_label = NULL;
   string m_decision_history[];

   void update_quantum_metrics()
   {
      m_quantum_metrics.quantum_entropy = calculate_market_entropy();
      m_quantum_metrics.neuro_sentiment = 0.5; // placeholder
      m_quantum_metrics.darkpool_imbalance = 0.0; // placeholder
   }

   double calculate_market_entropy()
   { double vol = iATR(_Symbol, PERIOD_D1, 14, 0); double avg_vol = iMA(_Symbol, PERIOD_D1, 30, 0, MODE_SMA, PRICE_CLOSE, 0); double entropy = (avg_vol != 0.0 ? vol / avg_vol : 0.0); if(m_logger) m_logger->log_debug(StringFormat("[Q-BIAS] Entropia quântica calculada: %.2f", entropy)); return entropy; }

   void log_quantum_decision(trade_signal signal)
   {
      string entry = TimeToString(TimeCurrent(), TIME_DATE) + " | " + signal_to_string(signal);
      int __i = ArraySize(m_decision_history); ArrayResize(m_decision_history, __i + 1); m_decision_history[__i] = entry;
      if(m_logger) m_logger->log_debug("[Q-BIAS] Decisão registrada: " + entry);
   }

   void update_chart_quantum_signal(trade_signal signal)
   {
       if(m_quantum_label == NULL) m_quantum_label = new CLabel("QuantumLabel", 0, 10, 70);
       m_quantum_label->text(signal_to_string(signal));
       m_quantum_label->color(signal == SIGNAL_BUY ? clrLime : signal == SIGNAL_SELL ? clrRed : clrGray);
   }

public:
   ThalerQuantumBiasEngine(logger_institutional &logger, MarketRegimeDetector &regime, RiskProfile &risk)
   {
      m_logger = &logger;
      m_regime_detector = &regime;
      m_risk_profile = &risk;
      m_quantum_metrics.kelly_adaptive = 1.0;
   }

   void initialize()
   { if(m_logger) m_logger->log_info("[Q-BIAS] Iniciando motor de viés quântico..."); }

   bool detect_quantum_herding()
   {
       if(m_simulate_default) { if(m_logger) m_logger->log_debug("[Q-BIAS] Modo simulado. Viés quântico ativado."); return true; }
       if(!is_market_ready()) { if(m_logger) m_logger->log_warning("[Q-BIAS] Mercado não está pronto. Bloqueando detecção."); return false; }
       update_quantum_metrics(); double input_vector[] = { m_quantum_metrics.quantum_entropy, m_quantum_metrics.neuro_sentiment, m_quantum_metrics.darkpool_imbalance, 0.0 }; double output0 = 0.6; double output1 = 0.4; bool result = (output0 > m_herding_threshold_default && output1 < 0.45); log_quantum_decision(result ? SIGNAL_BUY : SIGNAL_NONE); return result;
   }

   trade_signal get_quantum_signal()
   {
       trade_signal signal = SIGNAL_NONE; log_quantum_decision(signal); update_chart_quantum_signal(signal); return signal;
   }

   double get_adaptive_kelly()
   {
       m_quantum_metrics.kelly_adaptive = MathMax(m_kelly_min_default, MathMin(m_kelly_max_default, 1.0)); if(m_logger) m_logger->log_info("[Q-BIAS] Fator Kelly adaptativo: " + DoubleToString(m_quantum_metrics.kelly_adaptive, 2)); return m_quantum_metrics.kelly_adaptive;
   }

   bool is_market_ready()
   { int spread = (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD); int hour = TimeHour(TimeCurrent()); return (m_regime_detector != NULL ? spread <= (int)m_regime_detector->get_max_spread() : true) && (hour >= 3 && hour <= 22); }
};

#endif // __THALER_QUANTUM_BIAS_ENGINE_MQH__


