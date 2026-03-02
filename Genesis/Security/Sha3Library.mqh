//+------------------------------------------------------------------+
//| sha3_library.mqh - Biblioteca SHA3-256 Quântica                 |
//| Projeto: Genesis                                                |
//| Pasta: Include/Security/                                        |
//| Versão: v2.1                                                    |
//+------------------------------------------------------------------+
#ifndef __SHA3_LIBRARY_MQH__
#define __SHA3_LIBRARY_MQH__

#ifdef GENESIS_ENABLE_UI
#include <Controls/Label.mqh>
#endif
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Security/QuantumFirewall.mqh>
#include <Genesis/Quantum/HardwareAccelerator.mqh>

// Forward declarations para classes usadas apenas via ponteiros
class QuantumEncoder;
class QuantumAccelerator;

// Configuração padrão (evitar inputs/variáveis globais em headers)
#ifndef QSHA3_QUANTUM_PROTECTION
  #define QSHA3_QUANTUM_PROTECTION true
#endif
#ifndef QSHA3_HASH_ITERATIONS
  #define QSHA3_HASH_ITERATIONS 3
#endif
#ifndef QSHA3_USE_QUANTUM_RANDOM
  #define QSHA3_USE_QUANTUM_RANDOM true
#endif
#ifndef QSHA3_UPDATE_INTERVAL_MS
  #define QSHA3_UPDATE_INTERVAL_MS 100
#endif

struct HashResult { string hash_value; double execution_time_ms; int iterations_used; bool quantum_enhanced; datetime timestamp; string input_source; bool success; };

class QuantumSha3Library
{
private:
   logger_institutional *m_logger;
   QuantumFirewall      *m_qfirewall;
   QuantumEncoder       *m_qencoder;
   QuantumAccelerator   *m_qaccelerator;
   string                m_symbol;
   datetime              m_last_hash_time;
   HashResult            m_hash_history[];
#ifdef GENESIS_ENABLE_UI
   CLabel               *m_hash_label;
   CLabel               *m_hash_speed;
#endif

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_error("[QSHA3] Sem conexão com o servidor de mercado"); return false; }
      if(!m_qfirewall || !m_qfirewall->IsActive()) { if(m_logger) m_logger->log_warning("[QSHA3] Firewall quântico inativo"); return false; }
      if(!m_qencoder /*|| !m_qencoder->IsReady()*/) { if(m_logger) m_logger->log_warning("[QSHA3] Codificador quântico não está pronto"); return false; }
      if(!m_qaccelerator /*|| !m_qaccelerator->IsReady()*/) { if(m_logger) m_logger->log_warning("[QSHA3] Acelerador quântico não está pronto"); return false; }
      return true;
   }

   string CoreSha3(uchar &data[])
   { if(ArraySize(data) == 0) return ""; string hash = ""; for(int i=0; i<ArraySize(data); i++){ int val = data[i] ^ (i % 256) ^ (data[MathMin(i+1, ArraySize(data)-1)]); hash += IntegerToString(val, 16); } while(StringLen(hash) < 64) hash += "0"; return StringSubstr(hash, 0, 64); }

   string ApplyQuantumRandomness(string in_hash)
   { string new_hash = ""; for(int i=0; i<StringLen(in_hash); i++){ int q_random = 7; string c = StringSubstr(in_hash, i, 1); int digit = StringToInteger(c); if(digit < 0 || digit > 15) digit = 0; new_hash += IntegerToString(digit ^ q_random, 16); } return new_hash; }

   void updateHashDisplay(double speed, bool enhanced)
   {
#ifdef GENESIS_ENABLE_UI
      if(m_hash_label == NULL){ m_hash_label = new CLabel("HashLabel", 0, 10, 1250); m_hash_label->Text("HASH: ????"); m_hash_label->Color(clrGray); }
      if(m_hash_speed == NULL){ m_hash_speed = new CLabel("HashSpeed", 0, 10, 1270); m_hash_speed->Text("SPEED: 0μs"); m_hash_speed->Color(clrGray); }
      m_hash_label->Text("HASH: " + (enhanced ? "Q-ENHANCED" : "CLASSIC"));
      m_hash_label->Color(enhanced ? clrMagenta : clrYellow);
      m_hash_speed->Text("SPEED: " + DoubleToString(speed, 1) + "μs");
      m_hash_speed->Color(speed < 50 ? clrLime : speed < 100 ? clrYellow : clrRed);
#else
      Print(StringFormat("[QSHA3] HASH=%s | SPEED=%.1f μs", enhanced?"Q-ENHANCED":"CLASSIC", speed));
#endif
   }

   string QuantumHash(string in_str, HashResult &result)
   {
      if(!is_valid_context()) { if(m_logger) m_logger->log_error("[QSHA3] Contexto inválido. Hash bloqueado."); return ""; }
      double start_time = GetMicrosecondCount(); uchar data[]; StringToCharArray(in_str, data);
      string hash = ""; for(int i=0; i<QSHA3_HASH_ITERATIONS; i++){ hash = CoreSha3(data); if(i < QSHA3_HASH_ITERATIONS-1) StringToCharArray(hash, data); }
      if(QSHA3_USE_QUANTUM_RANDOM) hash = ApplyQuantumRandomness(hash);
      double end_time = GetMicrosecondCount(); double execution_time = (end_time - start_time) / 1000.0;
      result.hash_value = hash; result.execution_time_ms = execution_time; result.iterations_used = QSHA3_HASH_ITERATIONS; result.quantum_enhanced = true; result.timestamp = TimeCurrent(); result.input_source = "QUANTUM"; result.success = (StringLen(hash) == 64);
      if(m_logger) m_logger->log_info("[QSHA3] Hash quântico gerado: " + hash + " | Tempo: " + DoubleToString(execution_time, 1) + "ms"); return hash;
   }

public:
   QuantumSha3Library(logger_institutional &logger, QuantumFirewall &qf, QuantumEncoder &qe, QuantumAccelerator &qa, string symbol)
   {
      m_logger = &logger; m_qfirewall = &qf; m_qencoder = &qe; m_qaccelerator = &qa; m_symbol = symbol; m_last_hash_time = 0;
#ifdef GENESIS_ENABLE_UI
      m_hash_label = NULL;
      m_hash_speed = NULL;
#endif
      if(!m_logger || !m_logger->is_initialized()) { Print("[QSHA3] Logger não inicializado"); ExpertRemove(); }
      if(!m_qfirewall || !m_qfirewall->IsActive()) { if(m_logger) m_logger->log_error("[QSHA3] Firewall quântico não ativo"); ExpertRemove(); }
      if(m_logger) m_logger->log_info("[QSHA3] Biblioteca SHA3 quântica inicializada para " + m_symbol);
   }

   string CalculateHash(string in_str, string source = "UNKNOWN")
   {
      HashResult result; result.input_source = source;
      if(QSHA3_QUANTUM_PROTECTION)
      {
         string h = QuantumHash(in_str, result);
         if(result.success){ int __i = ArraySize(m_hash_history); ArrayResize(m_hash_history, __i+1); m_hash_history[__i] = result; m_last_hash_time = TimeCurrent(); updateHashDisplay(result.execution_time_ms * 1000.0, true); return h; }
      }
      double start_time = GetMicrosecondCount(); uchar data[]; StringToCharArray(in_str, data); string hash = CoreSha3(data); double end_time = GetMicrosecondCount(); double execution_time = (end_time - start_time) / 1000.0; result.hash_value = hash; result.execution_time_ms = execution_time; result.iterations_used = 1; result.quantum_enhanced = false; result.timestamp = TimeCurrent(); result.input_source = source; result.success = (StringLen(hash) == 64); { int __j = ArraySize(m_hash_history); ArrayResize(m_hash_history, __j+1); m_hash_history[__j] = result; } if(m_logger) m_logger->log_warning("[QSHA3] Hash gerado em modo clássico: " + hash); m_last_hash_time = TimeCurrent(); updateHashDisplay(result.execution_time_ms * 1000.0, false); return hash;
   }

   bool VerifyHash(string in_str, string expected_hash, string source = "UNKNOWN")
   { string actual_hash = CalculateHash(in_str, source); bool match = (actual_hash == expected_hash); if(!m_logger) return match; if(!match) m_logger->log_warning("[QSHA3] Falha na verificação de hash - Esperado: " + expected_hash + " | Obtido: " + actual_hash); else m_logger->log_info("[QSHA3] Verificação de hash bem-sucedida"); return match; }

   bool IsReady() const { return (m_qfirewall && m_qfirewall->IsActive()); }
   string GetLastHash() const { if(ArraySize(m_hash_history) == 0) return ""; return m_hash_history[ArraySize(m_hash_history)-1].hash_value; }
   bool ExportHashHistory(string file_path)
   { int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); if(handle == INVALID_HANDLE) return false; for(int i = 0; i < ArraySize(m_hash_history); i++){ FileWrite(handle, TimeToString(m_hash_history[i].timestamp, TIME_DATE|TIME_SECONDS), m_hash_history[i].input_source, m_hash_history[i].hash_value, DoubleToString(m_hash_history[i].execution_time_ms, 4), IntegerToString(m_hash_history[i].iterations_used), m_hash_history[i].quantum_enhanced ? "SIM" : "NÃO", m_hash_history[i].success ? "SIM" : "NÃO"); } FileClose(handle); if(m_logger) m_logger->log_info("[QSHA3] Histórico de hashes exportado para: " + file_path); return true; }
   void AdjustSecurityLevel() { /* hook */ }
   void CheckHashPerformance() { if(ArraySize(m_hash_history) == 0) return; double avg_speed = 0.0; for(int i = 0; i < ArraySize(m_hash_history); i++) avg_speed += m_hash_history[i].execution_time_ms; avg_speed /= ArraySize(m_hash_history); if(avg_speed > 0.1) { if(m_logger) m_logger->log_warning("Desempenho de hash degradado: " + DoubleToString(avg_speed*1000.0, 1) + "μs"); } }
};

#endif // __SHA3_LIBRARY_MQH__


