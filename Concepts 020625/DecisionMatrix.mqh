//+------------------------------------------------------------------+
//| DecisionMatrix.mqh - Sistema de Decisão Coletiva                  |
//| Combina sinais dos agentes para tomar decisão final              |
//+------------------------------------------------------------------+

#include "AgentBase.mqh"

class DecisionMatrix {
private:
   double m_buy_weight;    // Peso total para compra
   double m_sell_weight;   // Peso total para venda

public:
   DecisionMatrix() : m_buy_weight(0.0), m_sell_weight(0.0) {}

   // Coleta os sinais e calcula a decisão coletiva
   int CollectiveDecision(int signals[]) {
      int count = ArraySize(signals);
      m_buy_weight = 0.0;
      m_sell_weight = 0.0;

      for(int i=0; i<count; i++) {
         if(signals[i] == 1)
            m_buy_weight += 1.0;  // Peso básico por voto
         else if(signals[i] == -1)
            m_sell_weight += 1.0;
      }

      // Normaliza pesos pelo número de agentes
      double total_weight = m_buy_weight + m_sell_weight;
      if(total_weight == 0) return 0;

      m_buy_weight /= total_weight;
      m_sell_weight /= total_weight;

      // Decide com base na maioria ponderada
      if(m_buy_weight > 0.6)
         return 1; // Compra forte
      else if(m_sell_weight > 0.6)
         return -1; // Venda forte
      else if(m_buy_weight > m_sell_weight + 0.2)
         return 1; // Leve viés de alta
      else if(m_sell_weight > m_buy_weight + 0.2)
         return -1; // Leve viés de baixa
      else
         return 0; // Neutro ou empate
   }

   // Retorna o peso atual para compra
   double BuyWeight() const { return m_buy_weight; }

   // Retorna o peso atual para venda
   double SellWeight() const { return m_sell_weight; }

   // Retorna a decisão como texto
   string DecisionToString(int decision) {
      switch(decision) {
         case 1: return "🟢 Compra Forte";
         case -1: return "🔴 Venda Forte";
         case 0: return "🟠 Neutro";
         default: return "❓ Desconhecido";
      }
   }
};