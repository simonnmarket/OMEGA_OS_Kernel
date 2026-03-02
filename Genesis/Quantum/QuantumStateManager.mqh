//+------------------------------------------------------------------+
//| QuantumStateManager.mqh - Gerenciador de Estados Quânticos      |
//| Projeto: Genesis                                                |
//| Pasta: Include/Quantum/                                         |
//| Versão: v2.1 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_STATE_MANAGER_MQH__
#define __QUANTUM_STATE_MANAGER_MQH__

#include <Controls/Label.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumEntanglement.mqh>
#include <Genesis/Quantum/QuantumGateSystem.mqh>
#include <Genesis/Neural/QuantumNeuralNet.mqh>
class QuantumProcessor; // evitar include circular
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>

//+------------------------------------------------------------------+
//| PARÂMETROS (evitar inputs em headers)                           |
//+------------------------------------------------------------------+
#ifndef QSTATE_QUBITS_STATE
#define QSTATE_QUBITS_STATE 512
#endif
#ifndef QSTATE_DECOHERENCE_RATE
#define QSTATE_DECOHERENCE_RATE 0.01
#endif
#ifndef QSTATE_ENABLE_SUPERPOSITION
#define QSTATE_ENABLE_SUPERPOSITION true
#endif
#ifndef QSTATE_UPDATE_INTERVAL_MS
#define QSTATE_UPDATE_INTERVAL_MS 200
#endif

//+------------------------------------------------------------------+
//| ESTRUTURA DO ESTADO QUÂNTICO                                    |
//+------------------------------------------------------------------+
struct QuantumStateVector
{
	double             amplitudes[];    // Amplitudes de probabilidade
	double             coherence;       // Nível de coerência (0-1)
	datetime           update_time;     // Timestamp quântico
	int                state_phase;     // Fase do estado
	ENUM_TRADE_SIGNAL  last_signal;     // Sinal associado
	double             signal_confidence; // Confiança do sinal
};

//+------------------------------------------------------------------+
//| Estrutura de Resultados de Estado                               |
//+------------------------------------------------------------------+
struct QuantumStateResult {
	datetime timestamp;
	string symbol;
	double coherence;
	double entropy;
	bool coherent;
	int state_phase;
	ENUM_TRADE_SIGNAL last_signal;
	double execution_time_ms;
	bool success;
};

//+------------------------------------------------------------------+
//| CLASSE PRINCIPAL: QuantumStateManager                           |
//+------------------------------------------------------------------+
class QuantumStateManager
{
private:
	logger_institutional *m_logger;
	QuantumEntanglement  *m_entangler;
	QuantumGates         *m_gates;
	QuantumNeuralNet     *m_qnet;
	QuantumProcessor     *m_qprocessor;
	string               m_symbol;
	datetime             m_last_update_time;

	QuantumStateVector    m_qstate;
	double               m_state_entropy;
	
	// Histórico de estados
	QuantumStateResult m_state_history[];

	// Painel de decisão
	CLabel *m_state_label = NULL;
	CLabel *m_state_coherence = NULL;

	//+--------------------------------------------------------------+
	//| Valida contexto antes da execução                             |
	//+--------------------------------------------------------------+
	bool is_valid_context()
	{
		if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_error("[QSM] Sem conexão com o servidor de mercado"); return false; }
		if(!m_entangler || !m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_warning("[QSM] Emaranhamento quântico não ativo"); return false; }
		if(!m_qnet || !m_qnet->IsQuantumReady()) { if(m_logger) m_logger->log_warning("[QSM] Rede neural quântica não está pronta"); return false; }
		if(!m_qprocessor || !m_qprocessor->IsReady()) { if(m_logger) m_logger->log_warning("[QSM] Processador quântico não está pronto"); return false; }
		return true;
	}

	//+---------------------------------------------------------------+
	//| MÉTODO: UpdateQuantumState                                    |
	//+---------------------------------------------------------------+
	bool UpdateQuantumState()
	{
		if(!is_valid_context())
		{
			if(m_logger) m_logger->log_error("[QSM] Contexto inválido. Atualização bloqueada.");
			return false;
		}

		double start_time = GetMicrosecondCount();

		// Obter estado emaranhado
		double entangled_state[];
		if(!m_entangler->GetQuantumState(entangled_state, QSTATE_QUBITS_STATE/2))
		{
			if(m_logger) m_logger->log_error("[QSM] Falha ao obter estado emaranhado");
			return false;
		}
		
		// Aplicar portas quânticas
		double gate_state[];
		if(!m_gates->ApplyHadamard(entangled_state, gate_state))
		{
			if(m_logger) m_logger->log_error("[QSM] Falha ao aplicar porta Hadamard");
			return false;
		}
		
		// Configurar estado atual
		ArrayResize(m_qstate.amplitudes, QSTATE_QUBITS_STATE);
		
		// Manter superposição quântica
	   if(QSTATE_ENABLE_SUPERPOSITION)
		{
			for(int i=0; i<QSTATE_QUBITS_STATE; i++)
			{
                if(i < ArraySize(gate_state) && MathIsValidNumber(gate_state[i]))
					m_qstate.amplitudes[i] = gate_state[i];
				else
					m_qstate.amplitudes[i] = 1.0/MathSqrt(QSTATE_QUBITS_STATE);
			}
		}
		else
		{
			for(int i=0; i<ArraySize(m_qstate.amplitudes); i++)
				m_qstate.amplitudes[i] = MathAbs(gate_state[0]);
		}
		
		// Normalização quântica
		NormalizeState();
		
		// Atualizar metadados
		m_qstate.coherence = CalculateCoherence();
		m_qstate.update_time = TimeCurrent();
		m_qstate.state_phase = (m_qstate.state_phase + 1) % 4;
		m_qstate.last_signal = m_qprocessor->GetCurrentSignal();
		m_qstate.signal_confidence = 0.0;
		
		m_state_entropy = GetStateEntropy();

		double end_time = GetMicrosecondCount();
		double execution_time = (end_time - start_time) / 1000.0; // ms

		// Registro histórico
		QuantumStateResult result;
		result.timestamp = TimeCurrent();
		result.symbol = m_symbol;
		result.coherence = m_qstate.coherence;
		result.entropy = m_state_entropy;
		result.coherent = m_qstate.coherence > 0.5;
		result.state_phase = m_qstate.state_phase;
		result.last_signal = m_qstate.last_signal;
		result.execution_time_ms = execution_time;
		result.success = true;
		{ int __n = ArraySize(m_state_history); ArrayResize(m_state_history, __n + 1); m_state_history[__n] = result; }

		if(m_logger) m_logger->log_info("[QSM] Estado atualizado - Coerência: " + 
						DoubleToString(m_qstate.coherence,3) + 
						" | Fase: " + IntegerToString(m_qstate.state_phase) +
						" | Sinal: " + TradeSignalUtils().ToString(m_qstate.last_signal) +
						" | Tempo: " + DoubleToString(execution_time, 1) + "ms");
		
		m_last_update_time = TimeCurrent();
		return true;
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: NormalizeState                                        |
	//+---------------------------------------------------------------+
	void NormalizeState()
	{
		double norm = 0.0;
		for(int i=0; i<ArraySize(m_qstate.amplitudes); i++)
		{
            if(!MathIsValidNumber(m_qstate.amplitudes[i])) continue;
			norm += m_qstate.amplitudes[i] * m_qstate.amplitudes[i];
		}
		
		if(norm <= 0.0) return;
		
		norm = MathSqrt(norm);
		for(int i=0; i<ArraySize(m_qstate.amplitudes); i++)
		{
            if(MathIsValidNumber(m_qstate.amplitudes[i]))
				m_qstate.amplitudes[i] /= norm;
		}
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: CalculateCoherence                                    |
	//+---------------------------------------------------------------+
	double CalculateCoherence()
	{
		if(ArraySize(m_qstate.amplitudes) == 0) return 0.0;
		
		double purity = 0.0;
		for(int i=0; i<ArraySize(m_qstate.amplitudes); i++)
		{
			if(!MathIsValidNumber(m_qstate.amplitudes[i])) continue;
			double p = m_qstate.amplitudes[i] * m_qstate.amplitudes[i];
			purity += p * p;
		}
		
		double coherence = purity * ArraySize(m_qstate.amplitudes);
		return MathMax(0.0, MathMin(1.0, coherence));
	}

	//+--------------------------------------------------------------+
	//| Atualiza painel de estado                                    |
	//+--------------------------------------------------------------+
	void updateStateDisplay(double coherence, ENUM_TRADE_SIGNAL signal)
	{
		if(m_state_label == NULL)
		{
			m_state_label = new CLabel("StateLabel", 0, 10, 750);
			m_state_label->Text("ESTADO: ????");
			m_state_label->Color(clrGray);
		}

		if(m_state_coherence == NULL)
		{
			m_state_coherence = new CLabel("StateCoherence", 0, 10, 770);
			m_state_coherence->Text("COER: 0%");
			m_state_coherence->Color(clrGray);
		}

		string phase_text = 
			m_qstate.state_phase == 0 ? "SUPERPOSICAO" :
			m_qstate.state_phase == 1 ? "ENTRELACAMENTO" :
			m_qstate.state_phase == 2 ? "MEDICAO" : "COLAPSO";

		m_state_label->Text("ESTADO: " + phase_text);
		m_state_label->Color(
			m_qstate.state_phase == 0 ? clrLime :
			m_qstate.state_phase == 1 ? clrMagenta :
			m_qstate.state_phase == 2 ? clrYellow : clrRed
		);

		m_state_coherence->Text("COER: " + DoubleToString(coherence*100, 0) + "%");
		m_state_coherence->Color(
			coherence > 0.8 ? clrLime :
			coherence > 0.5 ? clrYellow : clrRed
		);
	}

public:
	//+---------------------------------------------------------------+
	//| CONSTRUTOR                                                    |
	//+---------------------------------------------------------------+
	QuantumStateManager(logger_institutional *logger,
					  QuantumEntanglement *qe, 
					  QuantumGates *qg, 
					  QuantumNeuralNet *qnn,
					  QuantumProcessor *qp,
					  string symbol = _Symbol) :
		m_logger(logger),
		m_entangler(qe),
		m_gates(qg),
		m_qnet(qnn),
		m_qprocessor(qp),
		m_symbol(symbol),
		m_state_entropy(0.0),
		m_last_update_time(0)
	{
		if(!m_logger || !m_logger->is_initialized()) { Print("[QSM] Logger não inicializado"); ExpertRemove(); }

		// Verificação de ambiente quântico
		if(!m_entangler || !m_entangler->IsEntanglementActive()) { if(m_logger) m_logger->log_error("[QSM] Emaranhamento quântico não ativo"); ExpertRemove(); }
		
		ArrayResize(m_qstate.amplitudes, QSTATE_QUBITS_STATE);
		for(int i=0; i<QSTATE_QUBITS_STATE; i++)
			m_qstate.amplitudes[i] = 1.0/MathSqrt(QSTATE_QUBITS_STATE);
		
		m_qstate.coherence = 1.0;
		m_qstate.state_phase = 0;
		m_qstate.last_signal = SIGNAL_NONE;
		m_qstate.signal_confidence = 0.0;
		
		if(m_logger) m_logger->log_info("[QSM] Gerenciador de estados inicializado com " + 
						IntegerToString(QSTATE_QUBITS_STATE) + " qubits");
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: GetQuantumState                                       |
	//+---------------------------------------------------------------+
	QuantumStateVector GetQuantumState()
	{
		if(UpdateQuantumState())
			return m_qstate;
		
		// Fallback
		QuantumStateVector error_state;
		ArrayResize(error_state.amplitudes, QSTATE_QUBITS_STATE);
		ArrayInitialize(error_state.amplitudes, 0.0);
		error_state.coherence = -1;
		error_state.update_time = TimeCurrent();
		error_state.state_phase = -1;
		error_state.last_signal = SIGNAL_NONE;
		error_state.signal_confidence = 0.0;
		
		if(m_logger) m_logger->log_warning("[QSM] Falha ao atualizar estado quântico - Usando fallback");
		return error_state;
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: GetStateEntropy                                       |
	//+---------------------------------------------------------------+
	double GetStateEntropy()
	{
		if(ArraySize(m_qstate.amplitudes) == 0) return 0.0;
		
		m_state_entropy = 0.0;
		for(int i=0; i<ArraySize(m_qstate.amplitudes); i++)
		{
            if(!MathIsValidNumber(m_qstate.amplitudes[i])) continue;
			
			double p = m_qstate.amplitudes[i] * m_qstate.amplitudes[i];
			if(p > 0)
				m_state_entropy -= p * MathLog(p);
		}
		return m_state_entropy;
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: IsStateCoherent                                       |
	//+---------------------------------------------------------------+
	bool IsStateCoherent() const
	{
		return m_qstate.coherence > 0.5;
	}

	//+--------------------------------------------------------------+
	//| Retorna se o sistema está pronto                             |
	//+--------------------------------------------------------------+
	bool IsReady() const
	{
		return (m_entangler && m_entangler->IsEntanglementActive()) && 
			   (m_qnet && m_qnet->IsQuantumReady()) && 
			   (m_qprocessor && m_qprocessor->IsReady());
	}

	//+--------------------------------------------------------------+
	//| Obtém nível de coerência                                     |
	//+--------------------------------------------------------------+
	double GetCoherenceLevel() const
	{
		return m_qstate.coherence;
	}

	//+--------------------------------------------------------------+
	//| Exporta histórico de estados                                 |
	//+--------------------------------------------------------------+
	bool ExportStateHistory(string file_path)
	{
		int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT);
		if(handle == INVALID_HANDLE) return false;

		for(int i = 0; i < ArraySize(m_state_history); i++)
		{
			FileWrite(handle,
				TimeToString(m_state_history[i].timestamp, TIME_DATE|TIME_SECONDS),
				m_state_history[i].symbol,
				DoubleToString(m_state_history[i].coherence, 4),
				DoubleToString(m_state_history[i].entropy, 4),
				m_state_history[i].coherent ? "SIM" : "NÃO",
				IntegerToString(m_state_history[i].state_phase),
				TradeSignalUtils().ToString(m_state_history[i].last_signal),
				DoubleToString(m_state_history[i].execution_time_ms, 1),
				m_state_history[i].success ? "SIM" : "NÃO"
			);
		}

		FileClose(handle);
		m_logger.log_info("[QSM] Histórico de estados exportado para: " + file_path);
		return true;
	}

	//+---------------------------------------------------------------+
	//| MÉTODO: OptimizeStateSpace                                    |
	//+---------------------------------------------------------------+
	void OptimizeStateSpace()
	{
		if(GetStateEntropy() > 2.0)
			QUBITS_STATE = MathMin(1024, QUBITS_STATE + 128);
	}
};

#endif // __QUANTUM_STATE_MANAGER_MQH__


