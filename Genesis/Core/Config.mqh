//+------------------------------------------------------------------+
//| Config.mqh - Parâmetros Institucionais (TIER-0++)               |
//+------------------------------------------------------------------+
#ifndef __GENESIS_CORE_CONFIG_MQH__
#define __GENESIS_CORE_CONFIG_MQH__

input double MAX_DAILY_RISK = 2.0;           // % do equity
input double MAX_TRADE_RISK = 0.5;           // % do equity
input ENUM_ORDER_TYPE_FILLING ORDER_FILLING_TYPE = ORDER_FILLING_FOK;
input int SLIPPAGE_POINTS = 3;               // desvio em pontos
input int EXECUTION_TIMEOUT = 5000;          // ms
input string ASSETS = "EURUSD,XAUUSD,BTCUSD,NAS100";
input string TIMEFRAMES = "M5,M15,H1";

#endif // __GENESIS_CORE_CONFIG_MQH__


