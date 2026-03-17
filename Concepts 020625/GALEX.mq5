//+------------------------------------------------------------------+
//| GALEX.mq5 - Galactic Algorithmic Execution System                 |
//| © Visionário Algorítmico                                         |
//+------------------------------------------------------------------+

#include <Trade\Trade.mqh>
#include "Core/QuantumState.mqh"
#include "Core/MarketField.mqh"
#include "Core/DecisionMatrix.mqh"

#include "Agents/AgentBase.mqh"
#include "Agents/MomentumAgent.mqh"
#include "Agents/MeanReversionAgent.mqh"

#include "Risk/DynamicRiskManager.mqh"
#include "Interface/HUDManager.mqh"
#include "Trade/OrderLauncher.mqh"

CTrade trade;

input string Symbols = "EURUSD,GBPUSD,USDJPY";
input double BaseRiskPercent = 1.5;
input int MaxOrdersPerSymbol = 3;
input int MagicNumber = 20250601;
input double TakeProfit = 100;
input double StopLoss = 100;
input bool UseTrailingStop = true;
input double TrailingStart = 50;
input double TrailingStep = 20;
input bool UseBreakeven = true;
input double BreakevenTrigger = 60;

string symbols[];
int total_symbols;

DynamicRiskManager* risk_manager;
HUDManager* hud;
MarketField* market_field;

AgentBase* agents[];

//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   EventSetTimer(10);

   // Inicializa símbolos
   int count = StringSplit(Symbols, ',', symbols);
   total_symbols = count;

   // Inicializa módulos centrais
   risk_manager = new DynamicRiskManager(BaseRiskPercent, MaxOrdersPerSymbol, TakeProfit, StopLoss,
                                         UseTrailingStop, TrailingStart, TrailingStep,
                                         UseBreakeven, BreakevenTrigger);

   hud = new HUDManager();
   market_field = new MarketField();

   // Inicializa agentes autônomos
   ArrayResize(agents, 2);
   agents[0] = new MomentumAgent();
   agents[1] = new MeanReversionAgent();

   // Atualiza campo vetorial inicial
   market_field.AnalyzeAll(symbols, total_symbols);
   hud.Init();

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| OnDeinit                                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   delete hud;
   delete risk_manager;
   delete market_field;

   for(int i=0; i<ArraySize(agents); i++)
      delete agents[i];
}

//+------------------------------------------------------------------+
//| OnTick                                                           |
//+------------------------------------------------------------------+
void OnTick()
{
   for(int i=0; i<total_symbols; i++)
   {
      string symbol = symbols[i];
      StringTrimLeft(symbol); StringTrimRight(symbol);
      if(!SymbolSelect(symbol, true)) continue;

      // Atualiza campo vetorial do mercado
      market_field.Update(symbol, i);

      // Cada agente analisa o mercado
      int signals[];
      ArrayInitialize(signals, 0);
      ArrayResize(signals, ArraySize(agents));

      for(int j=0; j<ArraySize(agents); j++) {
         signals[j] = agents[j].Analyze(symbol);
         Print("Agente ", agents[j].Name(), " | Sinal para ", symbol, ": ", SignalToString(signals[j]));
      }

      // Decisão coletiva via votação ponderada
      DecisionMatrix matrix;
      int final_signal = matrix.CollectiveDecision(signals);

      // Gerencia risco e executa ordem
      if(final_signal != 0 && risk_manager.CanOpenNewPosition(symbol, MagicNumber))
      {
         double lot = risk_manager.CalcLot(symbol, StopLoss);
         LaunchOrder(symbol, final_signal, lot);
      }

      // Atualiza interface gráfica
      string status = market_field.GetStatus(i);
      hud.Update(symbol, final_signal, status);

      // Atualiza trailing stop dinâmico
      risk_manager.ManageTrailing(symbol, MagicNumber);
   }
}

//+------------------------------------------------------------------+
//| Lança ordem com base no sinal                                   |
//+------------------------------------------------------------------+
void LaunchOrder(string symbol, int direction, double lot)
{
   OrderLauncher launcher;

   double price = launcher.GetEntryPrice(symbol, direction);
   double sl = risk_manager.CalculateSL(symbol, price, direction, StopLoss);
   double tp = risk_manager.CalculateTP(symbol, price, direction, TakeProfit);

   trade.SetExpertMagicNumber(MagicNumber);
   launcher.LaunchOrder(symbol, direction, lot, price, sl, tp, "GALEX v1.0");
}

//+------------------------------------------------------------------+
//| Converte sinal para texto                                       |
//+------------------------------------------------------------------+
string SignalToString(int signal) {
   switch(signal) {
      case 1: return "🟢 Compra Forte";
      case -1: return "🔴 Venda Forte";
      default: return "🟠 Neutro";
   }
}