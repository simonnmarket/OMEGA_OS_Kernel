//+------------------------------------------------------------------+
//| VectorDisplay.mqh - Exibição de vetores no gráfico               |
//| Mostra magnitude e direção do movimento de preços                |
//+------------------------------------------------------------------+

#include <Objects/Label.mqh>

class VectorDisplay {
private:
   CLabel m_label;
   string m_name;
   int    m_x;
   int    m_y;

public:
   VectorDisplay(string name, int x, int y) : m_name(name), m_x(x), m_y(y) {}

   // Desenha o vetor na tela
   bool Create(long chart_id, int window = 0) {
      m_label.Create(chart_id, m_name, window, m_x, m_y);
      m_label.Font("Arial");
      m_label.FontSize(12);
      m_label.Color(clrWhite);
      m_label.Background(false);
      return true;
   }

   // Atualiza o vetor com base no status do mercado
   void Update(const string status) {
      m_label.Text(status);
   }

   // Muda a cor do vetor para refletir força do sinal
   void SetColor(color clr) {
      m_label.Color(clr);
   }

   // Move o vetor para nova posição
   void Move(int x, int y) {
      m_x = x;
      m_y = y;
      m_label.XDistance(m_x);
      m_label.YDistance(m_y);
   }

   // Remove da tela
   void Destroy() {
      m_label.Delete();
   }
};