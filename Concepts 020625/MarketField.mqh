//+------------------------------------------------------------------+
//| MarketField.mqh - Campo Vetorial do Mercado                      |
//| Interpreta o movimento de preços como um campo vetorial dinâmico |
//+------------------------------------------------------------------+

#include "QuantumState.mqh"

class MarketVector {
private:
   double m_magnitude;       // Intensidade da variação (normalizada)
   double m_direction;       // Direção: +1 = subida, -1 = queda
   string m_status;          // Estado visual ("↑↑", "↑", "→", "↓", "↓↓")

public:
   MarketVector() : m_magnitude(0), m_direction(0), m_status("→ Neutro") {}

   // Atualiza o vetor com base no estado quântico do mercado
   void Update(const QuantumState& state) {
      double delta = 0;
      if (state.Price() > 0 && state.Momentum() != 0) {
         delta = state.Momentum() / (state.Volatility() + 1e-8); // Evita divisão por zero
      }

      m_magnitude = NormalizeDouble(MathAbs(delta), 2);
      m_direction = (delta > 0) ? 1 : (delta < 0) ? -1 : 0;

      // Define status visual
      if (m_direction > 0) {
         if (m_magnitude > 1.5) m_status = "↑↑ Forte Impulso";
         else if (m_magnitude > 0.8) m_status = "↑ Impulso";
         else m_status = "→ Leve Alta";
      } else if (m_direction < 0) {
         if (m_magnitude > 1.5) m_status = "↓↓ Queda Acentuada";
         else if (m_magnitude > 0.8) m_status = "↓ Queda";
         else m_status = "→ Leve Queda";
      } else {
         m_status = "→ Estável";
      }
   }

   // Retorna a magnitude do vetor
   double Magnitude() const { return m_magnitude; }

   // Retorna a direção do vetor
   double Direction() const { return m_direction; }

   // Retorna o status visual
   string Status() const { return m_status; }
};

class MarketField {
private:
   MarketVector m_vectors[3]; // Para até 3 ativos simultâneos
   QuantumState m_states[3];

public:
   MarketField() {}

   // Analisa todos os símbolos e atualiza o campo vetorial
   void AnalyzeAll(string symbols[], int count) {
      for(int i=0; i<count && i<3; i++) {
         m_states[i].Update(symbols[i]);
         m_vectors[i].Update(m_states[i]);
      }
   }

   // Atualiza um único ativo em tempo real
   void Update(string symbol, int index) {
      if(index >= 0 && index < 3) {
         m_states[index].Update(symbol);
         m_vectors[index].Update(m_states[index]);
      }
   }

   // Retorna o vetor do ativo na posição dada
   MarketVector GetVector(int index) {
      if(index >= 0 && index < 3)
         return m_vectors[index];
      else {
         MarketVector empty;
         return empty;
      }
   }

   // Retorna o status completo do campo vetorial
   string GetStatus(int index) {
      if(index >= 0 && index < 3)
         return m_vectors[index].Status();
      return "→ Desconhecido";
   }

   // Calcula força combinada do campo (para decisão coletiva)
   double TotalForce() {
      double total = 0;
      for(int i=0; i<3; i++)
         total += m_vectors[i].Magnitude() * m_vectors[i].Direction();
      return total;
   }
};