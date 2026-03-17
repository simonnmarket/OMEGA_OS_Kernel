//+------------------------------------------------------------------+
//| AgentBase.mqh - Classe base para agentes autônomos               |
//| Define a interface comum para todos os tipos de agentes          |
//+------------------------------------------------------------------+

#include "QuantumState.mqh"
#include "MarketField.mqh"

class AgentBase {
protected:
   string m_name;         // Nome do agente
   double m_confidence;   // Nível de confiança na decisão (0.0 a 1.0)

public:
   // Construtor abstrato
   AgentBase(string name) : m_name(name), m_confidence(0.0) {}

   // Método virtual puro (simulado em MQL5)
   virtual int Analyze(string symbol) {
      return 0; // Neutro por padrão
   }

   // Retorna o nome do agente
   string Name() const { return m_name; }

   // Retorna a confiança da análise atual
   double Confidence() const { return m_confidence; }

   // Método auxiliar: retorna se o preço está acima da média móvel
   bool IsPriceAboveMA(string symbol, int period = 20) {
      double ma = iMA(symbol, PERIOD_M1, period, 0, MODE_SMA, PRICE_CLOSE, 0);
      return iClose(symbol, PERIOD_M1, 0) > ma;
   }

   // Método auxiliar: retorna se o volume está acima da média
   bool IsVolumeSurge(string symbol, int period = 20) {
      double vol = iVolume(symbol, PERIOD_M1, 0);
      double avg_vol = iMA(NULL, 0, period, 0, MODE_SMA, PRICE_VOLUME, 0);
      return vol > avg_vol * 1.5;
   }
};