//+------------------------------------------------------------------+
//| STO_Fused.mqh (rev)                                              |
//| Fusão: STOBarDetector + ForceHistogram + Gate de Execução        |
//| Revisado: incremental, classe com estado isolado, sizing correto |
//+------------------------------------------------------------------+
#ifndef __STO_FUSED_MQH__
#define __STO_FUSED_MQH__

#include <Trade\Trade.mqh>

// Opcional: ajuste conforme seu projeto
#include <Utils/Log.mqh> // AuditLog (se não tiver, comente)

//--------------------------
// Configurações / inputs
//--------------------------
input int    StoVolumePeriod      = 20;
input double StoAlertZScore       = 2.0;
input bool   StoUseDeltaFilter    = true;
input int    StoDeltaThreshold    = 1000;
input bool   StoEnableLog         = true;

input int    StoTicksPerSwing     = 15;
input int    StoMinSwingCandles   = 3;
input int    StoMAPeriod          = 20;
input double StoVolumeFactor      = 1.3;
input int    StoSwingBufferSize   = 50;
input double StoPercentileCut     = 90.0;
input bool   StoUseMAFilter       = true;
input bool   StoUsePercentile     = true;
input bool   StoUseCandleFilter   = true;
input bool   StoDebugSwing        = false;

// Defesa / execução
input bool   StoEnableAutoTrade   = false;
input bool   StoEnableAlerts      = true;
input double StoRiskPerTrade      = 0.01;   // 1% do balance
input double StoSlAtrMult         = 1.5;
input double StoTpAtrMult         = 2.0;
input int    StoAtrPeriod         = 14;
input int    StoMaxOpenTrades     = 3;
input double StoMaxSpreadPoints   = 50;     // ajuste por símbolo
input int    StoSlippagePoints    = 20;
input ulong  StoMagic             = 20251203;
input bool   StoEnableWarmup      = true;
input int    StoWarmupBars        = 300;

//--------------------------
// Tipos
//--------------------------
enum PlayerStrength {
   StoNone = 0,
   StoLight,
   StoModerate,
   StoStrong,
   StoInstitutional
};

struct StoDefenseStatus {
   int    signal;      // -1 sell, 0 none, 1 buy
   double strength;    // 0..1 score
   string reason;
};

struct Swing {
   int     startIdx;
   int     endIdx;
   double  volume;
   double  startPrice;
   double  endPrice;
   bool    isUp;
};

//--------------------------
// Classe com estado isolado
//--------------------------
class CSTOFused
{
private:
   CArrayObj m_swingHistory;
   int    m_swingDir;
   double m_swingVol;
   double m_swingStartPrice;
   int    m_swingStartIdx;
   int    m_swingCandleCount;

   CTrade m_trade;
   bool   m_warmedUp;

public:
   CSTOFused()
   {
      ResetSwing();
   }

   void ResetSwing()
   {
      m_swingHistory.Clear();
      m_swingDir = 0;
      m_swingVol = 0;
      m_swingStartPrice = 0;
      m_swingStartIdx = 0;
      m_swingCandleCount = 0;
      m_warmedUp = false;
      ArrayResize(m_histUpLocal, 0);
      ArrayResize(m_histDownLocal, 0);
   }

   // Warmup: carrega histórico para preencher swings antes de operar
   void WarmupHistory(const int barsToLoad,
                      double &histUp[],
                      double &histDown[])
   {
      MqlRates rates[];
      int copied = CopyRates(_Symbol, _Period, 0, barsToLoad, rates);
      if(copied <= 1) return;

      ArraySetAsSeries(rates, false); // ordem cronológica

      double close[], open[];
      long volume[], tvol[];
      ArrayResize(close, copied);
      ArrayResize(open,  copied);
      ArrayResize(volume,copied);
      ArrayResize(tvol,  copied);
      for(int i=0;i<copied;i++){
         close[i]  = rates[i].close;
         open[i]   = rates[i].open;
         volume[i] = (long)rates[i].tick_volume;
         tvol[i]   = (long)rates[i].tick_volume;
      }
      // prepara buffers de hist
      ArrayResize(histUp,   copied);
      ArrayResize(histDown, copied);
      ArrayInitialize(histUp,   0.0);
      ArrayInitialize(histDown, 0.0);

      // processa de forma incremental (da 1 até último fechado)
      for(int i=1;i<copied;i++){
         ProcessSwingIncremental(i, close, tvol, histUp, histDown);
      }
      m_warmedUp = true;
   }

private:
   // Buffers internos para validação/benchmark (opcionais)
   double m_histUpLocal[];
   double m_histDownLocal[];

   // Util: spread gate
   bool SpreadOk() const
   {
      double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK)-SymbolInfoDouble(_Symbol, SYMBOL_BID))/(point>0?point:1);
      return (spread <= StoMaxSpreadPoints);
   }

   // Util: lote via risco monetário e stop em ATR
   double CalcLotSize(double atrPoints, double riskPct) const
   {
      double balance   = AccountInfoDouble(ACCOUNT_BALANCE);
      double point     = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double stopPriceDist = atrPoints * StoSlAtrMult * point; // distância em preço
      if(stopPriceDist <= 0 || tickSize <= 0 || tickValue <= 0) return 0.0;

      double moneyRiskPerLot = (stopPriceDist / tickSize) * tickValue; // $ por lote no SL
      double riskAmt = balance * riskPct;
      if(moneyRiskPerLot <= 0) return 0.0;

      double lot = riskAmt / moneyRiskPerLot;
      double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      double stepLot= SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
      int    volDigits = (int)SymbolInfoInteger(_Symbol, SYMBOL_VOLUME_DIGITS);
      lot = MathMax(minLot, MathFloor(lot / stepLot) * stepLot);
      return NormalizeDouble(lot, volDigits);
   }

   // Gate: sem posições do mesmo tipo/símbolo/magic
   bool CheckNoOpen(int type) const
   {
      for(int i=0;i<PositionsTotal();i++) {
         ulong ticket = PositionGetTicket(i);
         if(!PositionSelectByTicket(ticket)) continue;
         if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
         if(StoMagic && PositionGetInteger(POSITION_MAGIC)!=StoMagic) continue;
         if(PositionGetInteger(POSITION_TYPE)==type) return false;
      }
      return true;
   }

   // Detector de big player (retorna força + z + delta)
   PlayerStrength DetectBigPlayer(const int index,
                                  const long &volume[],
                                  const long &tick_volume[],
                                  const double &open[],
                                  const double &close[],
                                  double &z_out,
                                  double &delta_out)
   {
      z_out = 0; delta_out = 0;
      if(index < StoVolumePeriod) return StoNone;

      double sumVol=0, sumSq=0;
      for(int j=1;j<=StoVolumePeriod;j++) {
         double v=volume[index-j];
         sumVol+=v; sumSq+=v*v;
      }
      double avgVol = sumVol / StoVolumePeriod;
      double stdVol = MathSqrt(MathMax(sumSq / StoVolumePeriod - avgVol*avgVol, 1e-6));
      z_out = (volume[index]-avgVol)/stdVol;

      if(StoUseDeltaFilter) {
         if(close[index] > open[index]) delta_out = tick_volume[index];
         else if(close[index] < open[index]) delta_out = -tick_volume[index];
      }

      PlayerStrength s = StoNone;
      if(z_out < 0.5) s=StoNone;
      else if(z_out < 1.0) s=StoLight;
      else if(z_out < 1.5) s=StoModerate;
      else if(z_out < StoAlertZScore) s=StoStrong;
      else if(!StoUseDeltaFilter || MathAbs(delta_out)>=StoDeltaThreshold) s=StoInstitutional;
      else s=StoStrong;

      return s;
   }

   // Processa apenas UM candle fechado (index) incrementalmente
   void ProcessSwingIncremental(const int index,
                                const double &close[],
                                const long &tick_volume[],
                                double &histUp[],
                                double &histDown[])
   {
      // requer index >= 1 (candle fechado)
      if(index < 1) return;

      double delta = close[index]-m_swingStartPrice;
      if(m_swingDir==0){
         m_swingStartIdx   = index-1;
         m_swingStartPrice = close[index-1];
         m_swingDir        = (delta>=0?1:-1);
         m_swingVol        = tick_volume[index];
         m_swingCandleCount= 1;
         return;
      }

      m_swingVol        += tick_volume[index];
      m_swingCandleCount++;
      bool reverse=(m_swingDir==1 && delta<=-StoTicksPerSwing*_Point) ||
                   (m_swingDir==-1 && delta>= StoTicksPerSwing*_Point);
      if(!reverse) return;

      bool passCandle=!StoUseCandleFilter || (m_swingCandleCount>=StoMinSwingCandles);
      if(passCandle){
         double maVol  = CalcMASwingVolume();
         double percVol= CalcPercentileSwingVolume();
         bool passMA   = !StoUseMAFilter || (m_swingVol>=maVol*StoVolumeFactor);
         bool passPERC = !StoUsePercentile || (m_swingVol>=percVol);
         if(StoDebugSwing){
            Print("SwingVol=",m_swingVol," MA=",maVol," Perc=",percVol,
                  " [",(passMA?"OK-MA":"NO-MA"),", ",(passPERC?"OK-PERC":"NO-PERC"),"]");
         }
         if(passMA && passPERC){
            // garante tamanho dos buffers
            if(ArraySize(histUp)   <= index) ArrayResize(histUp,   index+1);
            if(ArraySize(histDown) <= index) ArrayResize(histDown, index+1);
            if(m_swingDir==1) histUp[index]=m_swingVol; else histDown[index]=m_swingVol;
         }
         StoreSwing(m_swingStartIdx,index,m_swingVol,m_swingStartPrice,close[index],m_swingDir==1);
      }
      // inverte swing
      m_swingDir        = -m_swingDir;
      m_swingStartIdx   = index;
      m_swingStartPrice = close[index];
      m_swingVol        = tick_volume[index];
      m_swingCandleCount= 1;
   }

   void StoreSwing(int start,int end,double vol,double p1,double p2,bool isUp)
   {
      Swing *s = new Swing;
      s.startIdx=start; s.endIdx=end; s.volume=vol; s.startPrice=p1; s.endPrice=p2; s.isUp=isUp;
      m_swingHistory.Add(s);
      if(m_swingHistory.Total()>StoSwingBufferSize) m_swingHistory.Delete(0);
   }

   double CalcMASwingVolume()
   {
      int total=MathMin(m_swingHistory.Total(), StoMAPeriod);
      if(total==0) return 0.0;
      double sum=0;
      for(int i=m_swingHistory.Total()-total;i<m_swingHistory.Total();i++){
         Swing *s=(Swing*)m_swingHistory.At(i);
         sum+=s.volume;
      }
      return sum/total;
   }

   double CalcPercentileSwingVolume()
   {
      int total=m_swingHistory.Total();
      if(total==0) return 0.0;
      double vols[];
      ArrayResize(vols,total);
      for(int i=0;i<total;i++){
         Swing *s=(Swing*)m_swingHistory.At(i);
         vols[i]=s.volume;
      }
      ArraySort(vols,WHOLE_ARRAY,0,MODE_DESCEND);
      int idx=MathFloor((StoPercentileCut/100.0)*total);
      idx=MathMin(idx,total-1);
      return vols[idx];
   }

   // Score / sinal (usa candle fechado, ex: index=1)
   StoDefenseStatus MakeSignal(const int index,
                               const long &volume[],
                               const long &tick_volume[],
                               const double &open[],
                               const double &close[],
                               const double &histUp[],
                               const double &histDown[])
   {
      StoDefenseStatus ds; ds.signal=0; ds.strength=0; ds.reason="NEUTRAL";
      double z=0, delta=0;
      PlayerStrength ps = DetectBigPlayer(index, volume, tick_volume, open, close, z, delta);
      if(index < StoVolumePeriod) return ds;

      // normalizações
      double z_norm = MathMax(0.0, MathMin(1.0, z/ StoAlertZScore));
      double delta_norm = StoDeltaThreshold>0 ? MathMin(1.0, MathAbs(delta)/(double)StoDeltaThreshold) : 0.0;

      // força do swing (último swing)
      double swing_strength=0.0;
      if(m_swingHistory.Total()>0){
         Swing *s=(Swing*)m_swingHistory.At(m_swingHistory.Total()-1);
         double percVol = CalcPercentileSwingVolume();
         if(percVol>0) swing_strength = MathMin(1.0, s.volume/percVol);
      }

      double raw = 0.5*z_norm + 0.3*delta_norm + 0.2*swing_strength;
      double score = 1.0/(1.0 + MathExp(-3.0*(raw-0.5))); // logística

      if(score >= 0.6) { ds.signal = 1; ds.strength=score; ds.reason="BUY_ZONE"; }
      else if(score <= 0.4) { ds.signal = -1; ds.strength=1.0-score; ds.reason="SELL_ZONE"; }
      else { ds.signal=0; ds.reason="NEUTRAL"; ds.strength=score; }

      if(StoEnableLog && ps>=StoModerate){
         AuditLog("STOScore", _Symbol,
                  StringFormat("i=%d | score=%.2f | z=%.2f | delta=%.0f | swing=%.2f | strength=%d | reason=%s",
                               index, score, z, delta, swing_strength, ps, ds.reason));
      }
      return ds;
   }

   // Execução (usar em barra fechada, ex: OnTick detectando nova barra)
   void EvaluateAndExecute(const int barIndex,
                           const double &close[],
                           const long &volume[],
                           const long &tick_volume[],
                           double &histUp[],
                           double &histDown[])
   {
      if(barIndex < 1) return; // precisa de barra fechada
      // warmup primeiro para evitar estado inconsistente
      if(!m_warmedUp && StoEnableWarmup) {
         WarmupHistory(StoWarmupBars, histUp, histDown);
      }
      ProcessSwingIncremental(barIndex, close, tick_volume, histUp, histDown);

      if(!StoEnableAutoTrade) return;
      if(!SpreadOk()) return;
      if(PositionsTotal() >= StoMaxOpenTrades) return;

      StoDefenseStatus ds = MakeSignal(barIndex, volume, tick_volume, close, close, histUp, histDown);
      if(ds.signal==0) return;

      double atr = iATR(_Symbol, PERIOD_CURRENT, StoAtrPeriod, barIndex);
      double price = close[barIndex];
      double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      double lot = CalcLotSize(atr/point, StoRiskPerTrade);
      if(lot <= 0) return;

      m_trade.SetExpertMagicNumber(StoMagic);
      m_trade.SetDeviationInPoints(StoSlippagePoints);

      double sl = price - (ds.signal==1 ? StoSlAtrMult*atr : -StoSlAtrMult*atr);
      double tp = price + (ds.signal==1 ? StoTpAtrMult*atr : -StoTpAtrMult*atr);

      if(ds.signal==1 && CheckNoOpen(POSITION_TYPE_BUY)) {
         m_trade.Buy(lot, _Symbol, price, sl, tp, "STO_BUY");
      } else if(ds.signal==-1 && CheckNoOpen(POSITION_TYPE_SELL)) {
         m_trade.Sell(lot, _Symbol, price, sl, tp, "STO_SELL");
      }
   }
};

#endif // __STO_FUSED_MQH__
