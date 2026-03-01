//+------------------------------------------------------------------+
//| STOBarULTIMATE.mqh - Análise STO Avançada                        |
//| Projeto: EA Numeia - Analysis                                    |
//| Função: Análise STO institucional com múltiplos timeframes       |
//+------------------------------------------------------------------+
#ifndef __ANALYSIS_STOBAR_ULTIMATE_MQH__
#define __ANALYSIS_STOBAR_ULTIMATE_MQH__

#include <Utils/Log.mqh>

#define COLOR_BLUE    0
#define COLOR_WHITE   1
#define COLOR_YELLOW  2
#define COLOR_ORANGE  3
#define COLOR_RED     4

input int    VolumePeriod    = 20;
input double AlertLevel      = 2.0;
input bool   UseDeltaFilter  = true;
input bool   PlayAlertSound  = true;

//--- Buffers internos
double ExtColorBuffer[];
double ExtVolumeBuffer[];

//+------------------------------------------------------------------+
//| Inicialização                                                    |
//+------------------------------------------------------------------+
int InitSTOBarULTIMATE()
{
   SetIndexBuffer(0, ExtColorBuffer, INDICATOR_COLOR_INDEX);
   SetIndexBuffer(1, ExtVolumeBuffer);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Execução principal de detecção                                   |
//+------------------------------------------------------------------+
void ProcessSTOBarULTIMATE(const int rates_total,
                           const int prev_calculated,
                           const double &open[],
                           const double &close[],
                           const long &tick_volume[],
                           const long &volume[],
                           const datetime &time[])
{
   int start = prev_calculated == 0 ? VolumePeriod : prev_calculated - 1;

   for (int i = start; i < rates_total; i++)
   {
      if (i < VolumePeriod)
      {
         ExtColorBuffer[i] = COLOR_BLUE;
         continue;
      }

      // Média e desvio padrão
      double sum = 0, sumSq = 0;
      for (int j = 1; j <= VolumePeriod; j++)
      {
         double v = volume[i - j];
         sum += v;
         sumSq += v * v;
      }

      double avg = sum / VolumePeriod;
      double std = MathSqrt(sumSq / VolumePeriod - avg * avg);
      double zscore = (volume[i] - avg) / std;

      // Delta
      double delta = UseDeltaFilter ? (close[i] > open[i] ? tick_volume[i] : -tick_volume[i]) : 0;

      int colorIndex = COLOR_BLUE;

      if (zscore < 0.5)
         colorIndex = COLOR_BLUE;
      else if (zscore < 1.0)
         colorIndex = COLOR_WHITE;
      else if (zscore < 1.5)
         colorIndex = COLOR_YELLOW;
      else if (zscore < AlertLevel)
         colorIndex = COLOR_ORANGE;
      else {
         colorIndex = COLOR_RED;

         if (PlayAlertSound && MathAbs(delta) > 1000)
         {
            PlaySound("bigplayer_alert.wav");
            SendNotification("🔴 Big Player detectado em " + Symbol());
         }
      }

      ExtColorBuffer[i] = colorIndex;
      ExtVolumeBuffer[i] = zscore;

      // Log Institucional
      string logMsg = StringFormat("STOBar i=%d | Z=%.2f | Δ=%.0f | Color=%d | Time=%s",
                                   i, zscore, delta, colorIndex, TimeToString(time[i]));
      AuditLog("STOBarULTIMATE", Symbol(), logMsg);
   }
}

#endif // __ANALYSIS_STOBAR_ULTIMATE_MQH__ 