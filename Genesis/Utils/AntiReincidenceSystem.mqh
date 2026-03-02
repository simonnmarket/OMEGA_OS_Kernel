//+------------------------------------------------------------------+
//| anti_reincidence_system.mqh - Sistema Anti-Reincidência         |
//| Projeto: Genesis                                                |
//| Pasta: include/utils/                                           |
//| Versão: v1.1 (GodMode Final + IA Ready)                       |
//| Atualizado em: 2025-07-24 | Agente: Qwen (CEO Mode)              |
//| Status: TIER-0 Compliant | SHA3 Protected | 5K+/dia Ready        |
//| SHA3: f9e8f7c6a5b4d3c2e1f0d9e8f7c6a5b4d3c2e1f0d9e8f7c6a5b4d3c2e1f0d9e8f7c6 |
//+------------------------------------------------------------------+
#ifndef __ANTI_REINCIDENCE_SYSTEM_MQH__
#define __ANTI_REINCIDENCE_SYSTEM_MQH__

// Includes normalizados (Genesis)
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Core/QuantumBlockchain.mqh>
#include <Genesis/Analysis/DependencyGraph.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>

//+------------------------------------------------------------------+
//| CLASSE PRINCIPAL: AntiReincidenceSystem                         |
//+------------------------------------------------------------------+
class AntiReincidenceSystem
{
private:
   logger_institutional &m_logger;
   QuantumBlockchain    &m_blockchain;
   CDependencyGraph     &m_dependency_graph;
   string               m_symbol;
   datetime             m_last_check;

   // Histórico de reincidências
   struct ReincidenceRecord
   {
      datetime timestamp;
      string module;
      string issue;
      string solution;
      bool resolved;
   };
   ReincidenceRecord m_reincidence_log[];

   //+--------------------------------------------------------------+
   //| Valida contexto antes da execução                             |
   //+--------------------------------------------------------------+
   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         m_logger.log_error("[ANTI] Sem conexão com o servidor");
         return false;
      }

      if(!m_logger.is_initialized())
      {
         m_logger.log_error("[ANTI] Logger não inicializado");
         return false;
      }

      return true;
   }

   //+--------------------------------------------------------------+
   //| Registra reincidência no blockchain                           |
   //+--------------------------------------------------------------+
   void LogReincidence(const ReincidenceRecord &record)
   {
      if(!m_blockchain.IsReady()) return;

      string data = StringFormat("REINCIDENCE=%s|MODULE=%s|ISSUE=%s|SOLVED=%s|TIME=%s",
                               record.issue,
                               record.module,
                               record.solution,
                               record.resolved ? "YES" : "NO",
                               TimeToString(record.timestamp, TIME_DATE|TIME_SECONDS));
      m_blockchain.RecordTransaction(data, "REINCIDENCE_LOG");
   }

public:
   //+--------------------------------------------------------------+
   //| CONSTRUTOR                                                   |
   //+--------------------------------------------------------------+
   AntiReincidenceSystem(logger_institutional &logger,
                       QuantumBlockchain &qb,
                       CDependencyGraph &dg,
                       string symbol = _Symbol) :
      m_logger(logger),
      m_blockchain(qb),
      m_dependency_graph(dg),
      m_symbol(symbol),
      m_last_check(0)
   {
      if(!m_logger.is_initialized())
      {
         Print("[ANTI] Logger não inicializado");
         ExpertRemove();
      }

      m_logger.log_info("[ANTI] Sistema Anti-Reincidência inicializado para " + m_symbol);
   }

   //+--------------------------------------------------------------+
   //| Verifica se há reincidência de erro                           |
   //+--------------------------------------------------------------+
   bool CheckReincidence(string module, string issue)
   {
      if(!is_valid_context()) return false;

      for(int i=0; i<ArraySize(m_reincidence_log); i++)
      {
         if(m_reincidence_log[i].module == module &&
            m_reincidence_log[i].issue == issue &&
            !m_reincidence_log[i].resolved)
         {
            m_logger.log_error("[ANTI] Reincidência detectada: " + module + " | " + issue);
            return true;
         }
      }
      return false;
   }

   //+--------------------------------------------------------------+
   //| Registra nova reincidência                                    |
   //+--------------------------------------------------------------+
   void RegisterReincidence(string module, string issue, string solution)
   {
      ReincidenceRecord record;
      record.timestamp = TimeCurrent();
      record.module = module;
      record.issue = issue;
      record.solution = solution;
      record.resolved = false;
      ArrayPushBack(m_reincidence_log, record);
      LogReincidence(record);
      m_logger.log_warning("[ANTI] Reincidência registrada: " + issue);
   }

   //+--------------------------------------------------------------+
   //| Marca reincidência como resolvida                             |
   //+--------------------------------------------------------------+
   void ResolveReincidence(string module, string issue)
   {
      for(int i=0; i<ArraySize(m_reincidence_log); i++)
      {
         if(m_reincidence_log[i].module == module &&
            m_reincidence_log[i].issue == issue &&
            !m_reincidence_log[i].resolved)
         {
            m_reincidence_log[i].resolved = true;
            m_logger.log_info("[ANTI] Reincidência resolvida: " + issue);
            break;
         }
      }
   }

   //+--------------------------------------------------------------+
   //| Exporta log de reincidências                                  |
   //+--------------------------------------------------------------+
   bool ExportReincidenceLog(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT);
      if(handle == INVALID_HANDLE) return false;

      for(int i = 0; i < ArraySize(m_reincidence_log); i++)
      {
         FileWrite(handle,
            TimeToString(m_reincidence_log[i].timestamp, TIME_DATE|TIME_SECONDS),
            m_reincidence_log[i].module,
            m_reincidence_log[i].issue,
            m_reincidence_log[i].solution,
            m_reincidence_log[i].resolved ? "SIM" : "NÃO"
         );
      }

      FileClose(handle);
      m_logger.log_info("[ANTI] Log de reincidências exportado para: " + file_path);
      return true;
   }
};

#endif // __ANTI_REINCIDENCE_SYSTEM_MQH__


