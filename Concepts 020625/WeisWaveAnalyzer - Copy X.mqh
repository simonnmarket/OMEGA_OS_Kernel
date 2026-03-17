//+------------------------------------------------------------------+
//|                              WeisWaveAnalyzer.mqh                |
//|       Análise de Ondas de Volume no Estilo Weis Wave             |
//+------------------------------------------------------------------+
#property strict

#include <Utils/PriceUtils.mqh>
#include <Utils/Log.mqh>

class WeisWaveAnalyzer {
private:
   string symbol;
   ENUM_TIMEFRAMES timeframe;
   double last_price;
   double wave_volume;
   bool is_up_wave;
   int wave_count;

public:
   struct Wave {
      int index;
      double volume;
      bool is_up;
      datetime start_time;
      datetime end_time;
   };

   CArrayObj waves;

   WeisWaveAnalyzer(string _symbol, ENUM_TIMEFRAMES _tf = PERIOD_M5) {
      symbol = _symbol;
      timeframe = _tf;
      last_price = 0;
      wave_volume = 0;
      is_up_wave = true;
      wave_count = 0;
      waves.Clear();
   }

   void Reset() {
      wave_volume = 0;
      last_price = 0;
      is_up_wave = true;
      wave_count = 0;
      waves.Clear();
   }

   void Update() {
      int bars = iBars(symbol, timeframe);
      if (bars < 2)
         return;

      double price_now = iClose(symbol, timeframe, 1);
      double price_prev = iClose(symbol, timeframe, 2);
      double tick_volume = iVolume(symbol, timeframe, 1);
      datetime bar_time = iTime(symbol, timeframe, 1);

      if (last_price == 0) {
         last_price = price_now;
         return;
      }

      bool up = price_now >= last_price;

      if (up == is_up_wave) {
         wave_volume += tick_volume;
      } else {
         // Finaliza onda anterior
         Wave* new_wave = new Wave;
         new_wave.index = wave_count++;
         new_wave.volume = wave_volume;
         new_wave.is_up = is_up_wave;
         new_wave.start_time = bar_time - PeriodSeconds(timeframe);
         new_wave.end_time = bar_time;
         waves.Add(new_wave);

         // Reinicia nova onda
         is_up_wave = up;
         wave_volume = tick_volume;
      }

      last_price = price_now;
   }

   Wave* GetLastWave() {
      if (waves.Total() == 0)
         return NULL;
      return (Wave*)waves.At(waves.Total() - 1);
   }

   void DebugPrint() {
      Wave* last = GetLastWave();
      if (last != NULL)
         Log::Info("WeisWave: " + (last.is_up ? "↑" : "↓") +
                   " Vol=" + DoubleToString(last.volume, 0));
   }

   double GetLastWaveVolume() {
      Wave* last = GetLastWave();
      if (last != NULL)
         return last.volume;
      return 0;
   }

   bool IsExhaustion() {
      Wave* last = GetLastWave();
      if (last != NULL && last.volume < 1000)
         return true;
      return false;
   }
}; 