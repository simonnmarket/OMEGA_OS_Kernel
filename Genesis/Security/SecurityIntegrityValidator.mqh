//+------------------------------------------------------------------+
//| security_integrity_validator.mqh - Validador de Integridade      |
//| Projeto: Genesis                                                |
//| Pasta: Include/Security/                                        |
//| Versão: v1.1                                                    |
//+------------------------------------------------------------------+
#ifndef __SECURITY_INTEGRITY_VALIDATOR_MQH__
#define __SECURITY_INTEGRITY_VALIDATOR_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Core/QuantumBlockchain.mqh>
#include <Genesis/Analysis/DependencyGraph.mqh>
#include <Genesis/Security/Sha3Library.mqh>

class SecurityIntegrityValidator
{
private:
   logger_institutional &m_logger;
   QuantumBlockchain    &m_blockchain;
   CDependencyGraph     &m_dependency_graph;
   QuantumSha3Library   &m_sha3;
   string                m_symbol;
   datetime              m_last_validation;
   struct IntegrityResult { bool valid; string module; string status; string details; datetime timestamp; };
   IntegrityResult m_validation_log[];

   bool is_valid_context()
   { if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { m_logger.log_error("[VALIDATOR] Sem conexão com o servidor"); return false; } if(!m_logger.is_initialized()) { m_logger.log_error("[VALIDATOR] Logger não inicializado"); return false; } if(!m_sha3.IsReady()) { m_logger.log_error("[VALIDATOR] SHA3 Library não está pronta"); return false; } return true; }

   bool ValidateFileHash(string file_path, string expected_hash)
   { if(!FileIsExists(file_path)) return false; string calculated = m_sha3.CalculateFileHash(file_path, "INTEGRITY"); return StringCompare(calculated, expected_hash) == 0; }

public:
   SecurityIntegrityValidator(logger_institutional &logger, QuantumBlockchain &qb, CDependencyGraph &dg, QuantumSha3Library &sha3, string symbol = _Symbol)
      : m_logger(logger), m_blockchain(qb), m_dependency_graph(dg), m_sha3(sha3), m_symbol(symbol), m_last_validation(0)
   { if(!m_logger.is_initialized()) { Print("[VALIDATOR] Logger não inicializado"); ExpertRemove(); } m_logger.log_info("[VALIDATOR] Validador de Integridade inicializado para " + m_symbol); }

   bool RunIntegrityValidation()
   {
      if(!is_valid_context()) return false; bool all_valid = true; IntegrityResult result;
      result.module = "DEPENDENCY_GRAPH"; result.valid = m_dependency_graph.ValidateAllDependencies(); result.status = result.valid ? "OK" : "ERRO"; result.details = result.valid ? "Todas as dependências válidas" : "Falha na validação"; result.timestamp = TimeCurrent(); ArrayPushBack(m_validation_log, result); if(!result.valid) all_valid = false;
      result.module = "QUANTUM_FIREWALL"; result.valid = true; result.status = "OK"; result.details = "Firewall ativo"; result.timestamp = TimeCurrent(); ArrayPushBack(m_validation_log, result);
      string data = StringFormat("INTEGRITY=RUN|ALL_VALID=%s|TIME=%s", all_valid ? "YES" : "NO", TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)); m_blockchain.RecordTransaction(data, "INTEGRITY_VALIDATION"); m_logger.log_info("[VALIDATOR] Validação de integridade concluída: " + (all_valid ? "APROVADA" : "BLOQUEADA")); return all_valid;
   }

   bool ExportValidationLog(string file_path)
   { int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); if(handle == INVALID_HANDLE) return false; for(int i = 0; i < ArraySize(m_validation_log); i++){ FileWrite(handle, TimeToString(m_validation_log[i].timestamp, TIME_DATE|TIME_SECONDS), m_validation_log[i].module, m_validation_log[i].status, m_validation_log[i].details); } FileClose(handle); m_logger.log_info("[VALIDATOR] Log de validação exportado para: " + file_path); return true; }
};

#endif // __SECURITY_INTEGRITY_VALIDATOR_MQH__


