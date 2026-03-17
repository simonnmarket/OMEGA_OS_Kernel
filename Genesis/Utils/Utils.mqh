//+------------------------------------------------------------------+
//| Utils.mqh - Biblioteca de Utilidades Globais                     |
//| Projeto: Genesis                                                |
//| Pasta: Include/Utils/                                          |
//| Versão: v1.0 (Institutional)                                   |
//| Atualizado em: 2025-07-31                                       |
//| Status: TIER-0 Compliant | 10K+/dia Ready                       |
//+------------------------------------------------------------------+
#ifndef __UTILS_MQH__
#define __UTILS_MQH__

#include <Genesis/Core/TradeSignalEnum.mqh>

//+------------------------------------------------------------------+
//| ENUMS GLOBAIS                                                   |
//+------------------------------------------------------------------+

// Direção do mercado
enum ENUM_DIRECTION
{
   DIRECTION_NEUTRAL = 0,
   DIRECTION_BULLISH,
   DIRECTION_BEARISH
};

// Níveis de confiança do sinal
enum ENUM_CONFIDENCE_LEVEL
{
   CONFIDENCE_LOW = 1,
   CONFIDENCE_MEDIUM = 2,
   CONFIDENCE_HIGH = 3,
   CONFIDENCE_CRITICAL = 4
};

// Tipos de eventos quânticos
enum ENUM_QUANTUM_EVENT
{
   QUANTUM_EVENT_NONE = 0,
   QUANTUM_EVENT_ENTANGLEMENT,
   QUANTUM_EVENT_COLLAPSE,
   QUANTUM_EVENT_TUNNELING,
   QUANTUM_EVENT_SUPERPOSITION
};

//+------------------------------------------------------------------+
//| FUNÇÕES DE CONVERSÃO                                             |
//+------------------------------------------------------------------+

// Converte ENUM_TRADE_SIGNAL para string
string SignalToString(ENUM_TRADE_SIGNAL signal)
{
   switch(signal)
   {
      case SIGNAL_BUY:               return "BUY";
      case SIGNAL_SELL:              return "SELL";
      case SIGNAL_CLOSE:             return "CLOSE";
      case SIGNAL_QUANTUM_HOLD:      return "HOLD";
      default:                       return "NONE";
   }
}

// Converte ENUM_DIRECTION para string
string DirectionToString(ENUM_DIRECTION direction)
{
   switch(direction)
   {
      case DIRECTION_BULLISH:  return "BULLISH";
      case DIRECTION_BEARISH:  return "BEARISH";
      default:                 return "NEUTRAL";
   }
}

//+------------------------------------------------------------------+
//| FUNÇÕES DE VALIDAÇÃO                                             |
//+------------------------------------------------------------------+

// Valida se o símbolo é negociável
bool IsSymbolValid(string symbol)
{
   if(StringLen(symbol) == 0) return false;
   return SymbolInfoInteger(symbol, SYMBOL_SELECT);
}

// Valida se há conexão com o terminal
bool IsTerminalConnected()
{
   return TerminalInfoInteger(TERMINAL_CONNECTED);
}

// Valida se o volume é permitido
bool IsValidLotSize(double lot)
{
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   if(lot < min_lot || lot > max_lot) return false;
   return (MathAbs(lot - MathRound(lot / step_lot) * step_lot) < 0.00001);
}

//+------------------------------------------------------------------+
//| FUNÇÕES DE TEMPO E TICKS                                         |
//+------------------------------------------------------------------+

// Obtém timestamp atual em milissegundos (aproximação)
long GetTimestampMS()
{
   return (long)TimeCurrent() * 1000;
}

// Verifica se é novo candle
bool IsNewCandle(ENUM_TIMEFRAMES timeframe)
{
   static datetime last_time[16] = {0};
   int tf_index = (int)timeframe;
   
   datetime current = iTime(_Symbol, timeframe, 0);
   if(current != last_time[tf_index])
   {
      last_time[tf_index] = current;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| MATEMÁTICA AVANÇADA                                              |
//+------------------------------------------------------------------+

// Calcula média móvel simples
double SimpleMovingAverage(double &array[], int period)
{
   if(ArraySize(array) < period) return 0.0;
   double sum = 0.0;
   for(int i = 0; i < period; i++)
      sum += array[i];
   return sum / period;
}

// Normaliza valor entre min e max
double Normalize(double value, double min, double max)
{
   if(max - min == 0) return 0.0;
   return (value - min) / (max - min);
}

//+------------------------------------------------------------------+
//| GESTÃO DE ERROS                                                  |
//+------------------------------------------------------------------+

// Imprime erro com contexto
void PrintError(string message, string source = "Utils")
{
   Print("[ERROR|", source, "] ", message, " | Time: ", TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS));
}

// Imprime informação com contexto
void PrintInfo(string message, string source = "Utils")
{
   Print("[INFO|", source, "] ", message, " | Time: ", TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS));
}

//+------------------------------------------------------------------+
//| MACROS ÚTEIS                                                     |
//+------------------------------------------------------------------+

// Macro para verificar e retornar erro
#define CHECK(x, msg) if(!(x)) { PrintError(msg); return false; }

// Macro para execução segura com log
#define SAFE_EXEC(x, logger) if(!(x)) { if(logger) logger.log_error("Erro em " + #x); return false; }

//+------------------------------------------------------------------+
//| ESTRUTURAS DE DADOS                                              |
//+------------------------------------------------------------------+

// Estrutura de sinal de trading
struct TradeSignal
{
   ENUM_TRADE_SIGNAL signal;
   double            price;
   double            sl;
   double            tp;
   double            lot;
   datetime          timestamp;
   double            confidence;
   string            reason;
};

// Estrutura de resultado de análise
struct AnalysisResult
{
   ENUM_DIRECTION          direction;
   double                  strength;
   double                  volatility;
   datetime                timestamp;
   ENUM_CONFIDENCE_LEVEL   confidence;
};

#endif // __UTILS_MQH__


