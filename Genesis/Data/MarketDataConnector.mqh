//+------------------------------------------------------------------+
//| MarketDataConnector.mqh - Conector de Dados de Mercado           |
//| Projeto: Genesis                                                 |
//+------------------------------------------------------------------+
#ifndef __GENESIS_MARKET_DATA_CONNECTOR_MQH__
#define __GENESIS_MARKET_DATA_CONNECTOR_MQH__

class market_data_connector
{
public:
   market_data_connector() {}

   bool is_initialized() const { return true; }
   bool is_ready() const { return true; }

   bool Subscribe(string symbol) { return (StringLen(symbol) > 0); }
};

#endif // __GENESIS_MARKET_DATA_CONNECTOR_MQH__


