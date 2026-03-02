//+------------------------------------------------------------------+
//| quantum_gate_system.mqh - Sistema Completo de Portas Quânticas   |
//| Projeto: Genesis                                                 |
//| Pasta: Include/Quantum/                                          |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_GATE_SYSTEM_MQH__
#define __QUANTUM_GATE_SYSTEM_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumStateManager.mqh>
#include <Controls/Label.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>

enum ENUM_QUANTUM_GATE_TYPE {
   QGATE_HADAMARD,
   QGATE_PAULI_X,
   QGATE_PAULI_Y,
   QGATE_PAULI_Z,
   QGATE_CNOT,
   QGATE_TOFFOLI,
   QGATE_SWAP,
   QGATE_CUSTOM
};

struct QuantumGateResult {
   datetime timestamp; string symbol; int qubit_count; double gate_fidelity; int gates_executed; double prob_0; double prob_1; bool measurement_success; double market_entropy; string gate_sequence_log;
};

class QuantumGateSystem
{
private:
   logger_institutional &m_logger; QuantumStateManager &m_state_manager; string m_symbol; int m_qubit_count; double m_gate_fidelity; datetime m_last_circuit_time;
   QuantumGateResult m_circuit_history[]; CLabel *m_gate_label = NULL;

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { m_logger.log_error("[QGATE] Sem conexão com o servidor de mercado"); return false; }
      if(!SymbolInfoInteger(m_symbol, SYMBOL_SELECT)) { m_logger.log_error("[QGATE] Símbolo inválido: " + m_symbol); return false; }
      if(!m_state_manager.IsQuantumReady()) { m_logger.log_warning("[QGATE] Gerenciador de estado não está pronto"); return false; }
      return true;
   }

   void ApplySingleGate(ENUM_QUANTUM_GATE_TYPE gate, double &amplitudes[], int target_qubit)
   {
      if(target_qubit*2+1 >= ArraySize(amplitudes)) return;
      switch(gate) {
         case QGATE_HADAMARD:
            amplitudes[target_qubit*2] = (amplitudes[target_qubit*2] + amplitudes[target_qubit*2+1])/MathSqrt(2.0);
            amplitudes[target_qubit*2+1] = (amplitudes[target_qubit*2] - amplitudes[target_qubit*2+1])/MathSqrt(2.0);
            break;
         case QGATE_PAULI_X:
            double temp = amplitudes[target_qubit*2]; amplitudes[target_qubit*2] = amplitudes[target_qubit*2+1]; amplitudes[target_qubit*2+1] = temp; break;
         case QGATE_PAULI_Z:
            amplitudes[target_qubit*2+1] *= -1; break;
         default:
            m_logger.log_warning("[QGATE] Porta não implementada: " + IntegerToString(gate)); break;
      }
   }

   void ApplyTwoQubitGate(ENUM_QUANTUM_GATE_TYPE gate, double &amplitudes[], int control, int target)
   {
      if(control*2+1 >= ArraySize(amplitudes) || target*2+1 >= ArraySize(amplitudes)) return;
      if(gate == QGATE_CNOT) {
         double control_1 = amplitudes[control*2+1]; double new_target_0 = amplitudes[target*2] + control_1 * (amplitudes[target*2+1] - amplitudes[target*2]);
         double new_target_1 = amplitudes[target*2+1] + control_1 * (amplitudes[target*2] - amplitudes[target*2+1]); amplitudes[target*2] = new_target_0; amplitudes[target*2+1] = new_target_1;
      } else if(gate == QGATE_SWAP) {
         double temp0 = amplitudes[control*2]; double temp1 = amplitudes[control*2+1]; amplitudes[control*2] = amplitudes[target*2]; amplitudes[control*2+1] = amplitudes[target*2+1]; amplitudes[target*2] = temp0; amplitudes[target*2+1] = temp1;
      }
   }

   double CalculateMarketEntropy()
   {
      MqlRates rates[]; CopyRates(m_symbol, PERIOD_M1, 0, 20, rates);
      double entropy = 0.0, sum = 0.0; for(int i = 0; i < ArraySize(rates); i++) sum += rates[i].close;
      if(sum <= 0) return 0.0; for(int i = 0; i < ArraySize(rates); i++) { double p = rates[i].close / sum; if(p > 0) entropy -= p * MathLog(p); }
      return NormalizeDouble(entropy, 4);
   }

   void updateGateDisplay(double prob_1)
   {
      if(m_gate_label == NULL) m_gate_label = new CLabel("GateLabel", 0, 10, 430);
      m_gate_label->text(StringFormat("QGATE: %.0f%%", prob_1 * 100));
      m_gate_label->color(!is_valid_context() ? clrRed : prob_1 > 0.7 ? clrMagenta : prob_1 > 0.5 ? clrOrange : clrYellow);
   }

public:
   QuantumGateSystem(logger_institutional &logger, QuantumStateManager &state_manager, string symbol, int qubits = 4, double fidelity = 0.99) :
      m_logger(logger), m_state_manager(state_manager), m_symbol(symbol), m_qubit_count(MathMax(1, MathMin(8, qubits))), m_gate_fidelity(MathMax(0.8, MathMin(1.0, fidelity))), m_last_circuit_time(0)
   {
      if(!m_logger.is_initialized()) { Print("[QGATE] Logger não inicializado"); ExpertRemove(); }
      if(!m_state_manager.IsQuantumReady()) { m_logger.log_error("[QGATE] Gerenciador de estado quântico não inicializado"); ExpertRemove(); }
      m_logger.log_info(StringFormat("[QGATE] Sistema inicializado para %s | %d qubits | Fidelidade: %.2f%%", m_symbol, m_qubit_count, m_gate_fidelity*100));
   }

   void RunQuantumCircuit(ENUM_QUANTUM_GATE_TYPE gates[], int gate_count)
   {
      if(!is_valid_context()) { m_logger.log_warning("[QGATE] Contexto inválido. Circuito bloqueado."); return; }
      if(gate_count <= 0 || ArraySize(gates) < gate_count) { m_logger.log_error("[QGATE] Contagem de portas inválida"); return; }
      double amplitudes[]; ArrayResize(amplitudes, m_qubit_count * 2); ArrayInitialize(amplitudes, 0.0); for(int i = 0; i < m_qubit_count; i++) amplitudes[i*2] = 1.0/MathSqrt(m_qubit_count);
      for(int i=0; i<gate_count; i++) { switch(gates[i]) { case QGATE_HADAMARD: case QGATE_PAULI_X: case QGATE_PAULI_Z: ApplySingleGate(gates[i], amplitudes, i % m_qubit_count); break; case QGATE_CNOT: case QGATE_SWAP: if(m_qubit_count > 1) ApplyTwoQubitGate(gates[i], amplitudes, 0, 1); break; } }
      double norm = 0.0; for(int i = 0; i < ArraySize(amplitudes); i++) norm += amplitudes[i] * amplitudes[i]; if(norm > 0) { for(int i = 0; i < ArraySize(amplitudes); i++) amplitudes[i] /= MathSqrt(norm); }
      for(int i=0; i<ArraySize(amplitudes); i++) { amplitudes[i] *= (1 + (MathRand()/32767.0 - 0.5) * (1 - m_gate_fidelity)); }
      m_state_manager.SetQuantumState(m_symbol, amplitudes);
      QuantumGateResult result; result.timestamp = TimeCurrent(); result.symbol = m_symbol; result.qubit_count = m_qubit_count; result.gate_fidelity = m_gate_fidelity; result.gates_executed = gate_count;
      result.prob_0 = amplitudes[0] * amplitudes[0]; result.prob_1 = amplitudes[1] * amplitudes[1]; result.measurement_success = true; result.market_entropy = CalculateMarketEntropy(); string seq = "";
      for(int i = 0; i < gate_count && i < 10; i++) seq += EnumToString(gates[i]) + ","; if(seq != "") seq = StringSubstr(seq, 0, StringLen(seq)-1); result.gate_sequence_log = seq; ArrayPushBack(m_circuit_history, result);
      m_logger.log_info("[QGATE] Circuito executado com " + IntegerToString(gate_count) + " portas"); updateGateDisplay(result.prob_1); m_last_circuit_time = TimeCurrent();
   }

   bool CreateEntanglement(int qubit1, int qubit2)
   {
      if(!is_valid_context()) { m_logger.log_warning("[QGATE] Contexto inválido. Retornando falso."); return false; }
      if(qubit1 >= m_qubit_count || qubit2 >= m_qubit_count || qubit1 < 0 || qubit2 < 0) { m_logger.log_error("[QGATE] Índice de qubit inválido"); return false; }
      double amplitudes[]; ArrayResize(amplitudes, m_qubit_count*2); ArrayInitialize(amplitudes, 0.0); amplitudes[qubit1*2] = 1.0/MathSqrt(2.0); amplitudes[qubit2*2+1] = 1.0/MathSqrt(2.0);
      m_state_manager.SetQuantumState(m_symbol, amplitudes);
      m_logger.log_info(StringFormat("[QGATE] Qubits %d e %d entrelaçados", qubit1, qubit2)); return true;
   }

   double MeasureQuantumState(int qubit)
   {
      if(!is_valid_context()) { m_logger.log_warning("[QGATE] Contexto inválido. Retornando 0.0."); return 0.0; }
      if(qubit >= m_qubit_count || qubit < 0) { m_logger.log_error("[QGATE] Índice de qubit inválido para medição"); return 0.0; }
      double amplitudes[]; if(!m_state_manager.GetQuantumState(m_symbol, amplitudes)) { m_logger.log_error("[QGATE] Falha ao obter estado quântico"); return 0.0; }
      if(ArraySize(amplitudes) <= qubit*2+1) return 0.0; double prob_0 = amplitudes[qubit*2] * amplitudes[qubit*2]; double prob_1 = amplitudes[qubit*2+1] * amplitudes[qubit*2+1]; double total = prob_0 + prob_1; if(total > 0) { prob_0 /= total; prob_1 /= total; }
      m_logger.log_info(StringFormat("[QGATE] Medição do qubit %d | P(|0⟩)=%.2f%% | P(|1⟩)=%.2f%%", qubit, prob_0*100, prob_1*100)); return prob_1;
   }

   bool IsReady() const { return m_state_manager.IsQuantumReady(); }
   int GetQubitCount() const { return m_qubit_count; }
   bool ExportCircuitHistory(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT); if(handle == INVALID_HANDLE) return false;
      for(int i = 0; i < ArraySize(m_circuit_history); i++)
      {
         FileWrite(handle,
            TimeToString(m_circuit_history[i].timestamp, TIME_DATE|TIME_SECONDS),
            m_circuit_history[i].symbol,
            IntegerToString(m_circuit_history[i].qubit_count),
            DoubleToString(m_circuit_history[i].gate_fidelity, 4),
            IntegerToString(m_circuit_history[i].gates_executed),
            DoubleToString(m_circuit_history[i].prob_0, 4),
            DoubleToString(m_circuit_history[i].prob_1, 4),
            m_circuit_history[i].measurement_success ? "SIM" : "NÃO",
            DoubleToString(m_circuit_history[i].market_entropy, 4),
            m_circuit_history[i].gate_sequence_log
         );
      }
      FileClose(handle); m_logger.log_info("[QGATE] Histórico de circuitos exportado para: " + file_path); return true;
   }

   double GetLastMeasurementProbability() { if(ArraySize(m_circuit_history) == 0) return 0.0; return m_circuit_history[ArraySize(m_circuit_history)-1].prob_1; }
};

#endif // __QUANTUM_GATE_SYSTEM_MQH__


