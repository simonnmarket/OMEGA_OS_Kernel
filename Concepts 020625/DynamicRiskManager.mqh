//+------------------------------------------------------------------+
//| DynamicRiskManager.mqh - Controle de risco adaptativo             |
//| Calcula lote, trailing stop, breakeven e proteção de drawdown     |
//+------------------------------------------------------------------+

#include <Trade\Trade.mqh>

class DynamicRiskManager {
private:
   double m_risk_percent;
   int    m_max_orders;
   double m_take_profit;
   double m_stop_loss;
   bool   m_use_trailing;
   double m_trailing_start;
   double m_trailing_step;
   bool   m_use_breakeven;
   double m_breakeven_trigger;

public:
   // Construtor com injeção de configurações
   DynamicRiskManager(double risk_percent = 1.5,
                      int max_orders = 3,
                      double take_profit = 100,
                      double stop_loss = 100,
                      bool use_trailing = true,
                      double trailing_start = 50,
                      double trailing_step = 20,
                      bool use_breakeven = true,
                      double breakeven_trigger = 60)
   {
      m_risk_percent = risk_percent;
      m_max_orders = max_orders;
      m_take_profit = take_profit;
      m_stop_loss = stop_loss;
      m_use_trailing = use_trailing;
      m_trailing_start = trailing_start;
      m_trailing_step = trailing_step;
      m_use_breakeven = use_breakeven;
      m_breakeven_trigger = breakeven_trigger;
   }

   // Verifica se pode abrir nova posição
   bool CanOpenNewPosition(string symbol, int magic) {
      int count = 0;
      for(int i=0; i<PositionsTotal(); i++) {
         if(PositionGetSymbol(i) == symbol && PositionGetInteger(POSITION_MAGIC) == magic)
            count++;
      }
      return count < m_max_orders;
   }

   // Calcula o tamanho do lote com base no risco e tick value
   double CalcLot(string symbol, double sl_pips) {
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double tick_value = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
      double lot = (balance * m_risk_percent / 100.0) / (sl_pips * _Point * tick_value);

      double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
      double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
      double step_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

      lot = MathMax(min_lot, MathMin(max_lot, lot));
      lot = MathFloor(lot / step_lot) * step_lot;

      return NormalizeDouble(lot, 2);
   }

   // Atualiza trailing stop dinamicamente
   void ManageTrailing(string symbol, int magic) {
      for(int i=0; i<PositionsTotal(); i++) {
         if(PositionGetSymbol(i) != symbol || PositionGetInteger(POSITION_MAGIC) != magic)
            continue;

         double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
         double price = SymbolInfoDouble(symbol, SYMBOL_BID);
         double profit = (price - open_price) / _Point;

         if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) {
            double sl = PositionGetDouble(POSITION_SL);
            if(profit > m_trailing_start) {
               double new_sl = price - m_trailing_step * _Point;
               if(new_sl > sl)
                  trade.PositionModify(symbol, new_sl, PositionGetDouble(POSITION_TP));
            }
            if(m_use_breakeven && profit > m_breakeven_trigger && sl < open_price)
               trade.PositionModify(symbol, open_price, PositionGetDouble(POSITION_TP));
         }

         if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL) {
            price = SymbolInfoDouble(symbol, SYMBOL_ASK);
            profit = (open_price - price) / _Point;
            double sl = PositionGetDouble(POSITION_SL);

            if(profit > m_trailing_start) {
               double new_sl = price + m_trailing_step * _Point;
               if(new_sl < sl || sl == 0)
                  trade.PositionModify(symbol, new_sl, PositionGetDouble(POSITION_TP));
            }
            if(m_use_breakeven && profit > m_breakeven_trigger && (sl > open_price || sl == 0))
               trade.PositionModify(symbol, open_price, PositionGetDouble(POSITION_TP));
         }
      }
   }
};