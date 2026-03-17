//+------------------------------------------------------------------+
//| Calcular tamanho do lote                                         |
//+------------------------------------------------------------------+
double CalculateLots()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = balance * RiskPercent / 100.0;
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   Print("DEBUG: Cálculo de Lotes - Balance: ", balance);
   Print("DEBUG: Cálculo de Lotes - Risk Amount: ", risk_amount);
   Print("DEBUG: Cálculo de Lotes - Tick Value: ", tick_value);
   Print("DEBUG: Cálculo de Lotes - Tick Size: ", tick_size);
   Print("DEBUG: Cálculo de Lotes - Point: ", point);
   Print("DEBUG: Cálculo de Lotes - Min Lot: ", min_lot);
   Print("DEBUG: Cálculo de Lotes - Lot Step: ", lot_step);
   
   double stop_loss_points;
   if(UseATRStopLoss)
   {
      int atr_handle = iATR(_Symbol, PERIOD_CURRENT, 14);
      if(atr_handle != INVALID_HANDLE)
      {
         double atr[];
         ArraySetAsSeries(atr, true);
         if(CopyBuffer(atr_handle, 0, 0, 1, atr) > 0)
         {
            stop_loss_points = atr[0] * ATRStopLossMultiplier / point;
            Print("DEBUG: Cálculo de Lotes - ATR Stop Loss Points: ", stop_loss_points);
         }
         else
         {
            Print("DEBUG: Falha ao copiar buffer ATR para cálculo de lote: ", GetLastError());
            stop_loss_points = StopLossPoints;
         }
         IndicatorRelease(atr_handle);
      }
      else
      {
         Print("DEBUG: Falha ao criar handle ATR para cálculo de lote: ", GetLastError());
         stop_loss_points = StopLossPoints;
      }
   }
   else
   {
      stop_loss_points = StopLossPoints;
   }
   
   // Evitar divisão por zero
   if(stop_loss_points <= 0 || tick_value <= 0 || tick_size <= 0)
   {
      Print("DEBUG: Erro no cálculo de lotes: valores inválidos");
      return InitialLots;
   }
   
   // Calcular lote baseado no risco
   double lots = NormalizeDouble(risk_amount / (stop_loss_points * tick_value * point / tick_size), 2);
   Print("DEBUG: Cálculo de Lotes - Lote Calculado (antes dos limites): ", lots);
   
   // Verificar se o lote está dentro dos limites
   lots = MathMax(lots, min_lot);
   lots = MathMin(lots, MaxLots);
   
   // Arredondar para o lot_step
   lots = MathFloor(lots / lot_step) * lot_step;
   
   // Garantir que o lote não seja zero
   if(lots < min_lot) lots = min_lot;
   
   Print("DEBUG: Cálculo de Lotes - Lote Final: ", lots);
   
   return lots;
}
