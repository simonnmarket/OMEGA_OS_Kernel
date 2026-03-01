//+------------------------------------------------------------------+
//|                  VolumeDecisionEngine.mqh                        |
//|       Define o tamanho da posição com base em análise de volume |
//+------------------------------------------------------------------+
#property strict

#include <Config/GlobalConfig.mqh>
#include <Utils/PriceUtils.mqh>
#include <Analysis/WeisWaveAnalyzer.mqh>
#include <Analysis/VolumeProfile.mqh>

class VolumeDecisionEngine {
private:
   string symbol;
   ENUM_TIMEFRAMES timeframe;
   double base_risk_per_trade;
   double max_lot;

public:
   VolumeDecisionEngine(string _symbol, ENUM_TIMEFRAMES _timeframe = PERIOD_M1, double _risk = 0.01, double _maxLot = 100.0) {
      symbol = _symbol;
      timeframe = _timeframe;
      base_risk_per_trade = _risk;
      max_lot = _maxLot;
   }

   double CalculateOptimalLot(double account_balance, double sl_points) {
      if (sl_points <= 0.0)
         return 0.0;

      double risk_amount = account_balance * base_risk_per_trade;
      double tick_value = MarketInfo(symbol, MODE_TICKVALUE);
      double tick_size = MarketInfo(symbol, MODE_TICKSIZE);

      double lot = NormalizeDouble((risk_amount / (sl_points * tick_value / tick_size)), 2);

      // Ajuste baseado em volume institucional
      lot *= VolumeFactor();

      // Cap no máximo definido
      return MathMin(lot, max_lot);
   }

private:
   double VolumeFactor() {
      WeisWaveAnalyzer wave(symbol, timeframe);
      wave.Update();
      double wave_strength = wave.GetStrength(); // 0.0 a 1.0

      VolumeProfile vp(symbol, timeframe);
      double price = iClose(symbol, timeframe, 0);
      double vwap = vp.GetVWAP();

      double alignment_bonus = (price > vwap) ? 1.2 : 0.9;

      return MathMax(0.5, MathMin(2.0, wave_strength * alignment_bonus));
   }
}; 