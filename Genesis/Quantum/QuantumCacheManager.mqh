//+------------------------------------------------------------------+
//| quantum_cache_manager.mqh - Gerenciador de Cache Quântico       |
//| Projeto: Genesis                                                 |
//| Pasta: Include/Quantum/                                          |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_CACHE_MANAGER_MQH__
#define __QUANTUM_CACHE_MANAGER_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
// Dependências concretas (necessárias para tipos em parâmetros)
#include <Genesis/Quantum/QuantumEntanglement.mqh>
#include <Genesis/Neural/QuantumNeuralNet.mqh>
#include <Genesis/Intelligence/QuantumLearning.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>
#include <Genesis/Config/GenesisConfig.mqh>
#include <Controls/Label.mqh>

// Configurações (sem inputs em headers)
#ifndef QCM_QUBITS_CACHE
  #define QCM_QUBITS_CACHE     1024
#endif
#ifndef QCM_COHERENCE_TIME
  #define QCM_COHERENCE_TIME   3600.0
#endif
#ifndef QCM_ENABLE_ENTANGLED_CACHE
  #define QCM_ENABLE_ENTANGLED_CACHE true
#endif
#ifndef QCM_UPDATE_INTERVAL_MS
  #define QCM_UPDATE_INTERVAL_MS 300
#endif

struct QuantumCacheEntry
{
   double             quantum_state[];
   datetime           storage_time;
   double             coherence_level;
   double             entanglement_strength;
};

struct QuantumCacheResult {
   datetime timestamp;
   string symbol;
   int cache_ptr;
   double coherence_level;
   double cache_density;
   bool success;
   double entropy_level;
   int total_entries;
   string operation_type;
};

class QuantumCacheManager
{
private:
   logger_institutional *m_logger;
   QuantumEntanglement  *m_entangler;
   CNeuroNet            *m_qnet;
   QuantumLearning      *m_qlearning;
   string               m_symbol;
   datetime             m_last_update_time;

   QuantumCacheEntry    m_qcache[];
   int                  m_cache_ptr;
   double               m_quantum_entropy;
   
   QuantumCacheResult m_cache_history[];
   CLabel *m_cache_label = NULL;

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_error("[QCM] Sem conexão com o servidor de mercado"); return false; }
      if(!m_entangler || !m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_warning("[QCM] Emaranhamento quântico não ativo"); return false; }
      if(!m_qnet || !m_qnet->IsReady()) { if(m_logger) m_logger->log_warning("[QCM] Rede neural quântica não está pronta"); return false; }
      if(!m_qlearning || !m_qlearning->IsReady()) { if(m_logger) m_logger->log_warning("[QCM] Sistema de aprendizado não está pronto"); return false; }
      return true;
   }

   bool StoreQuantumState()
   {
      if(!is_valid_context()) { if(m_logger) m_logger->log_error("[QCM] Contexto inválido. Armazenamento bloqueado."); return false; }
      if(!m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_error("[QCM] Emaranhamento inativo - armazenamento bloqueado"); return false; }
      double current_state[]; if(!m_qnet->GetOutputs(current_state) || ArraySize(current_state) == 0)
      { if(m_logger) m_logger->log_error("[QCM] Falha ao obter estado quântico da rede neural"); return false; }
      if(m_cache_ptr >= ArraySize(m_qcache)) m_cache_ptr = 0;
      ArrayResize(m_qcache[m_cache_ptr].quantum_state, ArraySize(current_state));
       if(QCM_ENABLE_ENTANGLED_CACHE && m_cache_ptr > 0)
      {
          double strength = m_entangler->CreateEntanglement(
             m_qcache[m_cache_ptr-1].quantum_state,
             current_state);
         m_qcache[m_cache_ptr].entanglement_strength = strength;
      }
      else { m_qcache[m_cache_ptr].entanglement_strength = 0.0; }
       double norm_factor = 1.0/MathSqrt(ArraySize(current_state));
       for(int i=0; i<ArraySize(current_state); i++) { if(!MathIsValidNumber(current_state[i])) continue; m_qcache[m_cache_ptr].quantum_state[i] = norm_factor * current_state[i]; }
      m_qcache[m_cache_ptr].storage_time = TimeCurrent();
      m_qcache[m_cache_ptr].coherence_level = 1.0;
       if(m_logger) m_logger->log_info("[QCM] Estado quântico armazenado - Qubits: " + IntegerToString(ArraySize(current_state)) + " | Entropia: " + DoubleToString(m_quantum_entropy,3));
      m_cache_ptr++; return true;
   }

   void UpdateCoherenceLevels()
   {
       for(int i=0; i<ArraySize(m_qcache); i++)
      {
          if(m_qcache[i].storage_time > 0)
          { double time_decay = (TimeCurrent() - m_qcache[i].storage_time)/QCM_COHERENCE_TIME; m_qcache[i].coherence_level = MathExp(-time_decay); m_qcache[i].coherence_level = MathMax(0.0, m_qcache[i].coherence_level); }
      }
   }

   double CalculateMarketEntropy()
   {
      MqlRates rates[]; CopyRates(m_symbol, PERIOD_M1, 0, 20, rates);
      double entropy = 0.0, sum = 0.0; for(int i = 0; i < ArraySize(rates); i++) sum += rates[i].close;
      if(sum <= 0) return 0.0; for(int i = 0; i < ArraySize(rates); i++) { double p = rates[i].close / sum; if(p > 0) entropy -= p * MathLog(p); }
      return NormalizeDouble(entropy, 4);
   }

   void updateCacheDisplay(double density)
   {
      if(m_cache_label == NULL) m_cache_label = new CLabel("CacheLabel", 0, 10, 610);
      m_cache_label->Text(StringFormat("CACHE: %.0f%%", density * 100));
      m_cache_label->Color(!is_valid_context() ? clrRed : density > 0.75 ? clrOrange : density > 0.5 ? clrYellow : clrLime);
   }

public:
   QuantumCacheManager(logger_institutional *logger,
                     QuantumEntanglement *qe,
                     CNeuroNet *qnn,
                     QuantumLearning *qlrn,
                     string symbol = _Symbol)
   {
      m_logger = logger;
      m_entangler = qe;
      m_qnet = qnn;
      m_qlearning = qlrn;
      m_symbol = symbol;
      m_cache_ptr = 0;
      m_quantum_entropy = 0.0;
      m_last_update_time = 0;
      if(!m_logger || !m_logger->is_initialized()) { Print("[QCM] Logger não inicializado"); ExpertRemove(); }
      if(!m_qnet || !m_qnet->IsReady()) { m_logger->log_error("[QCM] Rede neural quântica não inicializada"); ExpertRemove(); }
      ArrayResize(m_qcache, QCM_QUBITS_CACHE);
      for(int i=0; i<QCM_QUBITS_CACHE; i++)
      { ArrayResize(m_qcache[i].quantum_state, QCM_QUBITS_CACHE); m_qcache[i].storage_time = 0; m_qcache[i].coherence_level = 0.0; m_qcache[i].entanglement_strength = 0.0; }
      m_logger->log_info("[QCM] Cache quântico inicializado com " + IntegerToString(QCM_QUBITS_CACHE) + " qubits");
   }

   bool StoreState()
   {
      if(!is_valid_context()) return false;
      UpdateCoherenceLevels(); bool success = StoreQuantumState();
      QuantumCacheResult result; result.timestamp = TimeCurrent(); result.symbol = m_symbol; result.cache_ptr = m_cache_ptr - 1;
      result.coherence_level = success ? m_qcache[m_cache_ptr-1].coherence_level : 0.0; result.cache_density = GetQuantumCacheDensity(); result.success = success;
      result.entropy_level = CalculateMarketEntropy(); result.total_entries = m_cache_ptr; result.operation_type = "STORE"; { int __i = ArraySize(m_cache_history); ArrayResize(m_cache_history, __i+1); m_cache_history[__i] = result; }
      if(success) { updateCacheDisplay(result.cache_density); }
      m_last_update_time = TimeCurrent(); return success;
   }

   bool RetrieveState(int index, QuantumCacheEntry &state)
   {
      if(!is_valid_context()) return false;
      if(index < 0 || index >= m_cache_ptr) { if(m_logger) m_logger->log_error("[QCM] Índice de cache inválido: " + IntegerToString(index)); return false; }
      UpdateCoherenceLevels(); if(m_qcache[index].coherence_level < 0.1)
      { if(m_logger) m_logger->log_warning("[QCM] Decoerência quântica detectada no índice " + IntegerToString(index) + " | Coerência: " + DoubleToString(m_qcache[index].coherence_level, 3)); return false; }
      state = m_qcache[index];
      QuantumCacheResult result; result.timestamp = TimeCurrent(); result.symbol = m_symbol; result.cache_ptr = index; result.coherence_level = state.coherence_level;
      result.cache_density = GetQuantumCacheDensity(); result.success = true; result.entropy_level = CalculateMarketEntropy(); result.total_entries = m_cache_ptr; result.operation_type = "RETRIEVE";
      { int __j = ArraySize(m_cache_history); ArrayResize(m_cache_history, __j+1); m_cache_history[__j] = result; } m_last_update_time = TimeCurrent(); return true;
   }

   double GetQuantumCacheDensity()
   {
      int used_entries = 0; for(int i=0; i<ArraySize(m_qcache); i++) { if(m_qcache[i].storage_time > 0) used_entries++; }
      return (double)used_entries / ArraySize(m_qcache);
   }

   bool IsQuantumReady() const { return (m_entangler && m_entangler->IsEntanglementActive()) && (m_qnet && m_qnet->IsReady()) && (m_qlearning && m_qlearning->IsReady()); }
   double GetAverageCoherence()
   {
      double total = 0.0; int count = 0; for(int i = 0; i < ArraySize(m_qcache); i++) { if(m_qcache[i].storage_time > 0) { total += m_qcache[i].coherence_level; count++; } }
      return count > 0 ? total / count : 0.0;
   }

   bool ExportCacheHistory(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); if(handle == INVALID_HANDLE) return false;
      for(int i = 0; i < ArraySize(m_cache_history); i++)
      {
         FileWrite(handle,
            TimeToString(m_cache_history[i].timestamp, TIME_DATE|TIME_SECONDS),
            m_cache_history[i].symbol,
            IntegerToString(m_cache_history[i].cache_ptr),
            DoubleToString(m_cache_history[i].coherence_level, 4),
            DoubleToString(m_cache_history[i].cache_density, 4),
            m_cache_history[i].success ? "SIM" : "NÃO",
            DoubleToString(m_cache_history[i].entropy_level, 4),
            IntegerToString(m_cache_history[i].total_entries),
            m_cache_history[i].operation_type
         );
      }
      FileClose(handle); if(m_logger) m_logger->log_info("[QCM] Histórico de cache exportado para: " + file_path); return true;
   }

   // Utilitário para uso externo
   int GetLastIndex() const { return m_cache_ptr; }
};

#endif // __QUANTUM_CACHE_MANAGER_MQH__


