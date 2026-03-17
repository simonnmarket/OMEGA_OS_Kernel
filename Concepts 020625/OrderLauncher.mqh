//+------------------------------------------------------------------+
//| OrderLauncher.mqh - Disparador seguro de ordens                  |
//| Abstrai a lógica de execução de ordens                         |
//+------------------------------------------------------------------+

#include <Trade\Trade.mqh>

class OrderLauncher {
private:
   CTrade m_trade;

public:
   OrderLauncher() {}

   // Envia uma ordem de compra ou venda
   bool LaunchOrder(string symbol, int direction, double lot, double price, double sl, double tp, string comment = "") {
      if(direction == ORDER_TYPE_BUY) {
         return m_trade.Buy(lot, symbol, price, sl, tp, comment);
      } else if(direction == ORDER_TYPE_SELL) {
         return m_trade.Sell(lot, symbol, price, sl, tp, comment);
      }
      return false;
   }

   // Calcula preço ideal com base em ticks
   double GetEntryPrice(string symbol, int direction) {
      return (direction == ORDER_TYPE_BUY)
             ? SymbolInfoDouble(symbol, SYMBOL_ASK)
             : SymbolInfoDouble(symbol, SYMBOL_BID);
   }

   // Calcula SL com base na direção
   double CalculateSL(string symbol, double entry, int direction, double sl_pips) {
      return (direction == ORDER_TYPE_BUY)
             ? entry - sl_pips * _Point
             : entry + sl_pips * _Point;
   }

   // Calcula TP com base na direção
   double CalculateTP(string symbol, double entry, int direction, double tp_pips) {
      return (direction == ORDER_TYPE_BUY)
             ? entry + tp_pips * _Point
             : entry - tp_pips * _Point;
   }

   // Retorna o número atual de posições abertas
   int ActivePositions(string symbol, int magic) {
      int count = 0;
      for(int i=0; i<PositionsTotal(); i++) {
         if(PositionGetString(POSITION_SYMBOL) == symbol &&
            PositionGetInteger(POSITION_MAGIC) == magic)
            count++;
      }
      return count;
   }

   // Fecha todas as posições atuais (opcional para sistema de proteção)
   void CloseAllPositions(string symbol, int magic) {
      for(int i=0; i<PositionsTotal(); i++) {
         if(PositionGetString(POSITION_SYMBOL) == symbol &&
            PositionGetInteger(POSITION_MAGIC) == magic)
         {
            m_trade.PositionClose(symbol);
         }
      }
   }
};