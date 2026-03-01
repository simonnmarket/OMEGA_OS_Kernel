//+------------------------------------------------------------------+
//|                                               VolumeProfile.mqh  |
//|          Perfil de Volume Institucional - EA Numeia / Sky Lab   |
//+------------------------------------------------------------------+
#property strict

#include <Utils/Log.mqh>

class VolumeProfile {
private:
   int    profile_range;    // Número de candles para calcular o perfil
   double price_step;       // Granularidade do agrupamento de preço

public:
   struct VolumeBin {
      double price;
      double volume;
   };

   CArrayObj bins;

   // Construtor
   VolumeProfile(int range = 100, double step = 0.0005) {
      profile_range = range;
      price_step = step;
      bins.Clear();
   }

   void Reset() {
      bins.Clear();
   }

   void Calculate(string symbol, ENUM_TIMEFRAMES tf) {
      Reset();
      double min_price = iLow(symbol, tf, 0);
      double max_price = iHigh(symbol, tf, 0);

      // Definir faixa de preço
      for (int i = 0; i < profile_range; i++) {
         double low = iLow(symbol, tf, i);
         double high = iHigh(symbol, tf, i);
         if (low < min_price) min_price = low;
         if (high > max_price) max_price = high;
      }

      int bin_count = int((max_price - min_price) / price_step) + 1;
      double bin_volumes[];

      ArrayResize(bin_volumes, bin_count);
      ArrayInitialize(bin_volumes, 0.0);

      // Distribuir volume em bins
      for (int i = 0; i < profile_range; i++) {
         double vol = iVolume(symbol, tf, i);
         double typical_price = (iHigh(symbol, tf, i) + iLow(symbol, tf, i) + iClose(symbol, tf, i)) / 3.0;
         int bin_index = int((typical_price - min_price) / price_step);
         if (bin_index >= 0 && bin_index < bin_count)
            bin_volumes[bin_index] += vol;
      }

      // Criar estrutura
      for (int j = 0; j < bin_count; j++) {
         VolumeBin *vb = new VolumeBin;
         vb.price = min_price + j * price_step;
         vb.volume = bin_volumes[j];
         bins.Add(vb);
      }

      Log::Info("VolumeProfile: bins=" + (string)bin_count + " | faixa: " + DoubleToString(min_price,5) + " - " + DoubleToString(max_price,5));
   }

   double GetPOC() {
      double max_volume = 0.0;
      double poc_price = 0.0;
      for (int i = 0; i < bins.Total(); i++) {
         VolumeBin *vb = (VolumeBin*)bins.At(i);
         if (vb.volume > max_volume) {
            max_volume = vb.volume;
            poc_price = vb.price;
         }
      }
      return poc_price;
   }

   void PrintBins() {
      for (int i = 0; i < bins.Total(); i++) {
         VolumeBin *vb = (VolumeBin*)bins.At(i);
         Log::Info("Bin: " + DoubleToString(vb.price, 5) + " | Volume: " + DoubleToString(vb.volume, 2));
      }
   }
}; 