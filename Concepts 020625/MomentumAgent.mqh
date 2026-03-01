//+------------------------------------------------------------------+
//| MomentumAgent.mqh - Agente de Impulso                            |
//| Detecta momentos de forte momentum e sinaliza entrada            |
//+------------------------------------------------------------------+

#include "AgentBase.mqh"

class MomentumAgent : public AgentBase {
private:
   int m_period;

public:
   MomentumAgent() : AgentBase("MomentumHunter"), m_period(14) {}

   // Analisa o ativo e retorna sinal: +1 (compra), -1 (venda), 0 (neutro)
   int Analyze(string symbol) override {
      QuantumState state;
      state.Update(symbol);

      double mom = state.Momentum();
      double vol = state.Volatility();

      // Sinal forte: momentum alto e volatilidade subindo
      if(mom > 0 && mom > vol) {
         m_confidence = MathMin(1.0, mom / (vol + 1e-8));
         return 1;
      } else if(mom < 0 && mom < -vol) {
         m_confidence = MathMin(1.0, -mom / (vol + 1e-8));
         return -1;
      }

      m_confidence = 0.0;
      return 0;
   }
};