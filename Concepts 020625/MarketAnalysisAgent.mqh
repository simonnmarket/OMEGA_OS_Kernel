//+------------------------------------------------------------------+
//| MarketAnalysisAgent.mqh - Agente de Análise de Mercado          |
//| Projeto: EA Numeia - Agents                                     |
//| Função: Analisa condições gerais do mercado e tendências        |
//+------------------------------------------------------------------+
#ifndef __MARKET_ANALYSIS_AGENT_MQH__
#define __MARKET_ANALYSIS_AGENT_MQH__

#include "../Utils/Log.mqh"

class MarketAnalysisAgent {
private:
   string agentName;
   string currentSymbol;
   ENUM_TIMEFRAMES currentTimeframe;

public:
   MarketAnalysisAgent() {
      agentName = "MarketAnalysisAgent";
      currentSymbol = Symbol();
      currentTimeframe = PERIOD_CURRENT;
   }

   void Initialize() {
      Log("MarketAnalysisAgent inicializado", "MarketAnalysisAgent");
   }

   void AnalyzeMarket(string symbol) {
      Log("Analisando mercado para " + symbol, "MarketAnalysisAgent");
   }

   //--- Detecta aumento de volatilidade com base no ATR
   double GetVolatilityLevel(int period = 14) {
      int atrHandle = iATR(currentSymbol, currentTimeframe, period);
      if (atrHandle == INVALID_HANDLE) return 0.0;
      
      double atrValues[1];
      if (CopyBuffer(atrHandle, 0, 0, 1, atrValues) > 0) {
         return atrValues[0];
      }
      return 0.0;
   }

   //--- Detecta pressão de compra/venda com base no RSI
   double GetMomentum(int period = 14) {
      int rsiHandle = iRSI(currentSymbol, currentTimeframe, period, PRICE_CLOSE);
      if (rsiHandle == INVALID_HANDLE) return 50.0;
      
      double rsiValues[1];
      if (CopyBuffer(rsiHandle, 0, 0, 1, rsiValues) > 0) {
         return rsiValues[0];
      }
      return 50.0;
   }

   //--- Verifica volume institucional (placeholder para futura lógica de dark pool)
   double GetInstitutionalVolume() {
      long volume = iVolume(currentSymbol, currentTimeframe, 0);
      return (double)volume;
   }

   //--- Detecta candle de força direcional (exemplo básico)
   bool IsStrongDirectionalCandle(double threshold = 1.5) {
      double body = MathAbs(iClose(currentSymbol, currentTimeframe, 0) - iOpen(currentSymbol, currentTimeframe, 0));
      double range = iHigh(currentSymbol, currentTimeframe, 0) - iLow(currentSymbol, currentTimeframe, 0);
      if (range == 0) return false;

      double body_ratio = body / range;
      return body_ratio >= threshold;
   }

   //--- Verifica se há confluência entre ATR e RSI para movimentação relevante
   bool DetectDirectionalBias() {
      double rsi = GetMomentum();
      double atr = GetVolatilityLevel();

      if (atr > 0.0005 && (rsi > 60 || rsi < 40)) {
         Log("Bias identificado: ATR=" + DoubleToString(atr, 5) + " RSI=" + DoubleToString(rsi, 2));
         return true;
      }
      return false;
   }
};

#endif // __MARKET_ANALYSIS_AGENT_MQH__ 