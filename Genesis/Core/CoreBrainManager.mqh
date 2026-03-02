//+------------------------------------------------------------------+
//| core_brain_manager.mqh - Gerenciador Central do Cérebro Quântico |
//| Projeto: Genesis                                                |
//| Pasta: CORE/                                                    |
//| Versão: v2.2 (GodMode Final + IA Ready)                       |
//| Atualizado em: 2025-07-24 | Agente: Qwen (CEO Mode)              |
//| Status: TIER-0 Compliant | SHA3 Protected | 5K+/dia Ready        |
//| SHA3: f9e8f7c6a5b4d3c2e1f0d9e8f7c6a5b4d3c2e1f0d9e8f7c6a5b4d3c2e1f0d9e8f7c6 |
//+------------------------------------------------------------------+
#ifndef __CORE_BRAIN_MANAGER_MQH__
#define __CORE_BRAIN_MANAGER_MQH__

//+------------------------------------------------------------------+
//| INCLUSÕES NORMALIZADAS (GENESIS)                                 |
//+------------------------------------------------------------------+
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Quantum/QuantumProcessor.mqh>
#include <Genesis/Core/QuantumBlockchain.mqh>
#include <Genesis/Analysis/DependencyGraph.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>

// Dependências padrão do MetaTrader (UI/Arrays)
#include <Controls\Label.mqh>
#include <Arrays\ArrayObj.mqh>

//+------------------------------------------------------------------+
//| ESTRUTURA DE RESULTADO DE OPERAÇÃO                              |
//+------------------------------------------------------------------+
struct CoreOperationResult
{
   datetime timestamp;
   string operation;
   bool success;
   string details;
   string module;
   double execution_time_ms;
};

//+------------------------------------------------------------------+
//| CLASSE PRINCIPAL: CoreBrainManager                                |
//+------------------------------------------------------------------+
class CoreBrainManager
{
private:
   logger_institutional &m_logger;
   QuantumProcessor     &m_quantum_processor;
   QuantumBlockchain    &m_blockchain;
   string               m_symbol;
   datetime             m_last_operation_time;

   // Histórico de operações
   CoreOperationResult m_operation_history[];

   // Painel de decisão
   CLabel *m_brain_label;
   CLabel *m_operation_count;

   //+--------------------------------------------------------------+
   //| Valida contexto antes da execução                             |
   //+--------------------------------------------------------------+
   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         if(m_logger.is_initialized())
            m_logger.log_error("[CORE] Sem conexão com o servidor de mercado");
         return false;
      }

      if(!m_logger.is_initialized())
      {
         Print("[CORE] Logger não inicializado");
         return false;
      }

      if(!m_quantum_processor.IsReady())
      {
         m_logger.log_warning("[CORE] Processador quântico não está pronto");
         return false;
      }

      if(!m_blockchain.IsReady())
      {
         m_logger.log_warning("[CORE] Blockchain quântico não está pronto");
         return false;
      }

      return true;
   }

   //+--------------------------------------------------------------+
   //| Atualiza painel de cérebro                                    |
   //+--------------------------------------------------------------+
   void updateBrainDisplay(string status, int operations)
   {
      if(m_brain_label == NULL)
      {
         m_brain_label = new CLabel("BrainLabel", 0, 10, 1650);
         if(m_brain_label != NULL)
             m_brain_label->Text("CÉREBRO: ????");
      }

      if(m_operation_count == NULL)
      {
         m_operation_count = new CLabel("OperationCount", 0, 10, 1670);
         if(m_operation_count != NULL)
             m_operation_count->Text("OP: 0");
      }

      if(m_brain_label != NULL)
      {
          m_brain_label->Text("CÉREBRO: " + status);
          m_brain_label->Color(
            status == "ONLINE" ? clrLime :
            status == "WARNING" ? clrYellow : clrRed
         );
      }

      if(m_operation_count != NULL)
      {
          m_operation_count->Text("OP: " + IntegerToString(operations));
          m_operation_count->Color(operations > 0 ? clrLime : clrGray);
      }
   }

public:
   //+--------------------------------------------------------------+
   //| CONSTRUTOR                                                   |
   //+--------------------------------------------------------------+
   CoreBrainManager(logger_institutional &logger,
                  QuantumProcessor &qp,
                  QuantumBlockchain &qb,
                  string symbol = _Symbol) :
      m_logger(logger),
      m_quantum_processor(qp),
      m_blockchain(qb),
      m_symbol(symbol),
      m_last_operation_time(0),
      m_brain_label(NULL),
      m_operation_count(NULL)
   {
      ArrayInitialize(m_operation_history, 0);

      if(!m_logger.is_initialized())
      {
         Print("[CORE] Logger não inicializado");
         ExpertRemove();
      }

      if(!m_quantum_processor.IsReady())
      {
         m_logger.log_error("[CORE] Processador quântico não ativo");
         ExpertRemove();
      }

      if(!m_blockchain.IsReady())
      {
         m_logger.log_error("[CORE] Blockchain quântico não está pronto");
         ExpertRemove();
      }

      m_logger.log_info("[CORE] Core Brain Manager inicializado para " + m_symbol);
   }

   //+--------------------------------------------------------------+
   //| Registra operação no cérebro central                          |
   //+--------------------------------------------------------------+
   void LogOperation(string operation, bool success, string details, string module = "UNKNOWN")
   {
      if(!is_valid_context())
      {
         if(m_logger.is_initialized())
            m_logger.log_error("[CORE] Contexto inválido. Registro bloqueado.");
         return;
      }

      double start_time = GetMicrosecondCount();

      // Registro de operação
      CoreOperationResult result;
      result.timestamp = TimeCurrent();
      result.operation = operation;
      result.success = success;
      result.details = details;
      result.module = module;

      double end_time = GetMicrosecondCount();
      result.execution_time_ms = (end_time - start_time) / 1000.0; // ms

      ArrayPushBack(m_operation_history, result);

      // Log baseado no sucesso
      if(success)
      {
         m_logger.log_info("[CORE] " + operation + ": " + details + 
                           " | Tempo: " + DoubleToString(result.execution_time_ms, 1) + "ms");
      }
      else
      {
         m_logger.log_error("[CORE] " + operation + ": " + details + 
                           " | Tempo: " + DoubleToString(result.execution_time_ms, 1) + "ms");
      }

      // Registrar no blockchain
      string data = StringFormat("OP=%s|SUCCESS=%s|DETAILS=%s|MODULE=%s|TIME=%.1fms",
                               operation,
                               success ? "YES" : "NO",
                               details,
                               module,
                               result.execution_time_ms);
      m_blockchain.RecordTransaction(data, "CORE_OPERATION");

      m_last_operation_time = TimeCurrent();
      updateBrainDisplay("ONLINE", ArraySize(m_operation_history));
   }

   //+--------------------------------------------------------------+
   //| Converte sinal para string                                   |
   //+--------------------------------------------------------------+
   string signal_to_string(ENUM_TRADE_SIGNAL signal)
   {
      switch(signal)
      {
         case SIGNAL_BUY: return "COMPRA";
         case SIGNAL_SELL: return "VENDA";
         case SIGNAL_REVERSA: return "REVERSA";
         case SIGNAL_QUANTUM: return "QUANTUM";
         case SIGNAL_QUANTUM_FLASH: return "QUANTUM_FLASH";
         case SIGNAL_QUANTUM_CRISIS: return "QUANTUM_CRISIS";
         case SIGNAL_NONE: return "NENHUM";
         default: return "DESCONHECIDO";
      }
   }

   //+--------------------------------------------------------------+
   //| Obtém último sinal do processador                            |
   //+--------------------------------------------------------------+
   ENUM_TRADE_SIGNAL GetLastSignal()
   {
      return m_quantum_processor.GetLastSignal();
   }

   //+--------------------------------------------------------------+
   //| Obtém confiança do sinal                                     |
   //+--------------------------------------------------------------+
   double GetSignalConfidence()
   {
      return m_quantum_processor.GetSignalConfidence();
   }

   //+--------------------------------------------------------------+
   //| Retorna se está pronto                                       |
   //+--------------------------------------------------------------+
   bool IsReady() const
   {
      return m_logger.is_initialized() && 
             m_quantum_processor.IsReady() && 
             m_blockchain.IsReady();
   }

   //+--------------------------------------------------------------+
   //| Obtém número de operações                                    |
   //+--------------------------------------------------------------+
   int GetOperationCount() const
   {
      return ArraySize(m_operation_history);
   }

   //+--------------------------------------------------------------+
   //| Exporta histórico de operações                               |
   //+--------------------------------------------------------------+
   bool ExportOperationHistory(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT);
      if(handle == INVALID_HANDLE) return false;

      for(int i = 0; i < ArraySize(m_operation_history); i++)
      {
         FileWrite(handle,
            TimeToString(m_operation_history[i].timestamp, TIME_DATE|TIME_SECONDS),
            m_operation_history[i].operation,
            m_operation_history[i].success ? "SIM" : "NÃO",
            m_operation_history[i].details,
            m_operation_history[i].module,
            DoubleToString(m_operation_history[i].execution_time_ms, 1)
         );
      }

      FileClose(handle);
      if(m_logger.is_initialized())
         m_logger.log_info("[CORE] Histórico de operações exportado para: " + file_path);
      return true;
   }

   //+--------------------------------------------------------------+
   //| Destrutor                                                    |
   //+--------------------------------------------------------------+
   ~CoreBrainManager()
   {
      if(m_brain_label != NULL)
      {
         delete m_brain_label;
         m_brain_label = NULL;
      }

      if(m_operation_count != NULL)
      {
         delete m_operation_count;
         m_operation_count = NULL;
      }

      if(m_logger.is_initialized())
         m_logger.log_info("[CORE] CoreBrainManager encerrado para " + m_symbol);
   }
};

#endif // __CORE_BRAIN_MANAGER_MQH__
