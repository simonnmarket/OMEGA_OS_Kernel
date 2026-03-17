//+------------------------------------------------------------------+
//| SignalProvider.mqh - Provedor de Sinais Profissional (Heurístico)
//+------------------------------------------------------------------+
#ifndef __GENESIS_SIGNAL_PROVIDER_MQH__
#define __GENESIS_SIGNAL_PROVIDER_MQH__

class CSignalProvider
{
private:
   int    m_fast_ma_period;
   int    m_slow_ma_period;
   int    m_rsi_period;
   int    m_atr_period;
   bool   m_use_rsi;
   bool   m_use_atr;
   double m_min_confidence;
   double m_min_atr_points;

   bool read_last_values(const string symbol,
                         double &fast0, double &fast1,
                         double &slow0, double &slow1,
                         double &rsi0,
                         double &atr0)
   {
      int hF = iMA(symbol, PERIOD_CURRENT, m_fast_ma_period, 0, MODE_EMA, PRICE_CLOSE);
      int hS = iMA(symbol, PERIOD_CURRENT, m_slow_ma_period, 0, MODE_EMA, PRICE_CLOSE);
      if(hF==INVALID_HANDLE || hS==INVALID_HANDLE) return false;
      double f[2], s[2];
      if(CopyBuffer(hF,0,0,2,f)!=2 || CopyBuffer(hS,0,0,2,s)!=2) return false;
      fast0=f[0]; fast1=f[1]; slow0=s[0]; slow1=s[1];

      if(m_use_rsi)
      {
         int hR = iRSI(symbol, PERIOD_CURRENT, m_rsi_period, PRICE_CLOSE);
         if(hR==INVALID_HANDLE) return false;
         double r[1]; if(CopyBuffer(hR,0,0,1,r)!=1) return false; rsi0=r[0];
      }
      else rsi0=50.0;

      if(m_use_atr)
      {
         int hA = iATR(symbol, PERIOD_CURRENT, m_atr_period);
         if(hA==INVALID_HANDLE) return false;
         double a[1]; if(CopyBuffer(hA,0,0,1,a)!=1) return false; atr0=a[0];
      }
      else atr0=0.0;

      return true;
   }

public:
   CSignalProvider(int fastMA=20, int slowMA=50, int rsiPeriod=14, int atrPeriod=14,
                   bool useRSI=true, bool useATR=true,
                   double minConfidence=0.6, double minAtrPoints=0.0)
   {
      m_fast_ma_period = fastMA;
      m_slow_ma_period = slowMA;
      m_rsi_period = rsiPeriod;
      m_atr_period = atrPeriod;
      m_use_rsi = useRSI;
      m_use_atr = useATR;
      m_min_confidence = minConfidence;
      m_min_atr_points = minAtrPoints;
   }

   bool Generate(const string symbol, ENUM_TRADE_SIGNAL &signal, double &confidence)
   {
      signal = SIGNAL_NONE; confidence = 0.0;
      double f0,f1,s0,s1,rsi,atr;
      if(!read_last_values(symbol, f0,f1,s0,s1,rsi,atr)) return false;

      // Regras básicas
      bool crossUp   = (f1 <= s1 && f0 > s0);
      bool crossDown = (f1 >= s1 && f0 < s0);
      bool slopeUp   = (f0 > f1 && s0 >= s1);
      bool slopeDown = (f0 < f1 && s0 <= s1);

      if(m_use_atr && m_min_atr_points > 0.0)
      {
         double pt = SymbolInfoDouble(symbol, SYMBOL_POINT);
         if(pt>0.0 && atr/pt < m_min_atr_points) return false; // pouca volatilidade
      }

      double scoreBuy = 0.0, scoreSell = 0.0;
      if(crossUp)   scoreBuy  += 0.5;
      if(slopeUp)   scoreBuy  += 0.2;
      if(crossDown) scoreSell += 0.5;
      if(slopeDown) scoreSell += 0.2;

      if(m_use_rsi)
      {
         if(rsi >= 55.0) scoreBuy  += 0.3; else if(rsi <= 45.0) scoreSell += 0.3;
      }

      if(scoreBuy >= scoreSell && scoreBuy >= m_min_confidence)
      { signal = SIGNAL_BUY;  confidence = scoreBuy;  return true; }
      if(scoreSell > scoreBuy && scoreSell >= m_min_confidence)
      { signal = SIGNAL_SELL; confidence = scoreSell; return true; }

      return true; // sem sinal forte
   }
};

#endif // __GENESIS_SIGNAL_PROVIDER_MQH__


