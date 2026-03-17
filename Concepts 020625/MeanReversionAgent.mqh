//+------------------------------------------------------------------+
//| MeanReversionAgent.mqh - Agente de Reversão à Média               |
//| Detecta desvios extremos e sinaliza reversão                     |
//+------------------------------------------------------------------+

#include "AgentBase.mqh"

class MeanReversionAgent : public AgentBase {
private:
   int m_period;

public:
   MeanReversionAgent() : AgentBase("MeanReversionBot"), m_period(20) {}

   // Analisa o ativo e retorna sinal: +1 (compra), -1 (venda), 0 (neutro)
   int Analyze(string symbol) override {
      double price = iClose(symbol, PERIOD_M1, 0);
      double ma = iMA(symbol, PERIOD_M1, m_period, 0, MODE_SMA, PRICE_CLOSE, 0);
      double dev = (price - ma) / iATR(symbol, PERIOD_M1, m_period, 0);

      // Desvio padrão acima da média indica oportunidade de reversão
      if(dev < -1.5) { // Preço muito abaixo da média → Compra
         m_confidence = NormalizeDouble(MathMin(1.0, -dev / 2.0), 2);
         return 1;
      } else if(dev > 1.5) { // Preço muito acima da média → Venda
         m_confidence = NormalizeDouble(MathMin(1.0, dev / 2.0), 2);
         return -1;
      }

      m_confidence = 0.0;
      return 0;
   }
};