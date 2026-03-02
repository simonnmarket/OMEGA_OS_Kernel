//+------------------------------------------------------------------+
//| quantum_behavior_controller.mqh - Controle Quântico de Comportamento |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_BEHAVIOR_CONTROLLER_MQH__
#define __QUANTUM_BEHAVIOR_CONTROLLER_MQH__

#include <Genesis/Core/TradeSignalEnum.mqh>

// Estruturas mínimas compatíveis
struct QuantumBehaviorDecision
{
   double             quantum_weights[];
   double             coherence_level;
   datetime           decision_time;
   int                behavior_state;
   ENUM_TRADE_SIGNAL  last_signal;
   double             signal_confidence;
   double             entropy_level;
};

class QuantumBehaviorController
{
private:
   QuantumBehaviorDecision m_qdecision;

public:
   QuantumBehaviorController() { ArrayResize(m_qdecision.quantum_weights, 0); m_qdecision.coherence_level = 0.0; m_qdecision.decision_time = 0; m_qdecision.behavior_state = -1; m_qdecision.last_signal = SIGNAL_NONE; m_qdecision.signal_confidence = 0.0; m_qdecision.entropy_level = 0.0; }

   // API mínima para compatibilidade
   bool IsReady() const { return true; }
   double GetCoherenceLevel() const { return m_qdecision.coherence_level; }
   ENUM_TRADE_SIGNAL GetLastSignal() const { return m_qdecision.last_signal; }
   QuantumBehaviorDecision UpdateQuantumBehavior()
   {
      // Retorna decisão neutra para compatibilidade; lógica real está isolada em outros módulos
      m_qdecision.decision_time = TimeCurrent();
      return m_qdecision;
   }
};

#endif // __QUANTUM_BEHAVIOR_CONTROLLER_MQH__


