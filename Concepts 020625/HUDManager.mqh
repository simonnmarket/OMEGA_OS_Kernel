//+------------------------------------------------------------------+
//| HUDManager.mqh - Interface tipo cockpit                          |
//| Mostra sinais, vetores, status e decisão coletiva                |
//+------------------------------------------------------------------+

#include "VectorDisplay.mqh"

class HUDManager {
private:
   VectorDisplay* m_displays[];
   int m_count;

public:
   HUDManager() {
      m_count = 3; // Para até 3 ativos simultâneos
      ArrayResize(m_displays, m_count);

      for(int i=0; i<m_count; i++) {
         m_displays[i] = new VectorDisplay("vector_"+IntegerToString(i), 50, 70 + i*20);
      }
   }

   ~HUDManager() {
      for(int i=0; i<m_count; i++)
         delete m_displays[i];
   }

   // Inicializa a interface
   void Init() {
      VectorDisplay title("title", 50, 30);
      title.Create(0);
      title.Text("🌌 GALEX v1.0 - Galactic Algorithmic Execution System");
      title.SetColor(clrLime);

      VectorDisplay header("header", 50, 50);
      header.Create(0);
      header.Text("Símbolo     Sinal       Status                  Peso");
      header.SetColor(clrYellow);
   }

   // Atualiza interface com base no símbolo e sinal
   void Update(string symbol, int signal, string status) {
      int index = SymbolToIndex(symbol);
      if(index >= 0 && index < m_count) {
         color clr = (signal == 1) ? clrGreen : (signal == -1) ? clrRed : clrGray;
         m_displays[index].Update(symbol + "     " + SignalToString(signal) + "     " + status + "     " + DoubleToString(CalcSignalWeight(signal), 2));
         m_displays[index].SetColor(clr);
         m_displays[index].Create(0);
      }
   }

   // Converte sinal para texto visual
   string SignalToString(int signal) {
      return (signal == 1) ? "🔺 Compra" : (signal == -1) ? "🔻 Venda" : "⬤ Neutro";
   }

   // Calcula peso visual do sinal
   double CalcSignalWeight(int signal) {
      return (signal != 0) ? MathAbs(signal * 0.8) : 0.0;
   }

   // Mapeia o símbolo para índice (ex: EURUSD → 0)
   int SymbolToIndex(string symbol) {
      if(symbol == "EURUSD") return 0;
      if(symbol == "GBPUSD") return 1;
      if(symbol == "USDJPY") return 2;
      return -1;
   }
};