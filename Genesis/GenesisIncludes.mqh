//+------------------------------------------------------------------+
//| GenesisIncludes.mqh - Aggregator & Compatibility Layer           |
//| Projeto: Genesis                                                 |
//| Propósito: Reunir includes centrais e expor CGenesisUtils        |
//+------------------------------------------------------------------+
#ifndef __GENESISINCLUDES_MQH__
#define __GENESISINCLUDES_MQH__

// Núcleo Genesis
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Core/SystemEnums.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>
#include <Genesis/Config/GenesisConfig.mqh>

// Compatibilidade: utilitário mínimo para EA que espera CGenesisUtils
class CGenesisUtils
{
private:
   logger_institutional m_logger;
   bool                 m_initialized;

public:
   CGenesisUtils(): m_logger("GenesisEA"), m_initialized(false) {}

   bool Initialize()
   {
      m_initialized = true;
      return true;
   }
};

#endif // __GENESISINCLUDES_MQH__


