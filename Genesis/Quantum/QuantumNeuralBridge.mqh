//+------------------------------------------------------------------+
//| QuantumNeuralBridge.mqh - Ponte Quântico-Neural                 |
//| Projeto: Genesis                                                |
//| Pasta: Include/Quantum/                                         |
//| Versão: v1.1 (TIER-0+)                                          |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_NEURAL_BRIDGE_MQH__
#define __QUANTUM_NEURAL_BRIDGE_MQH__

#include <Genesis/Quantum/QuantumNeuralCore.mqh>
#include <Genesis/Analysis/NeuralDependencyGraph.mqh>

//+------------------------------------------------------------------+
//| Ponte Quântico-Neural                                           |
//+------------------------------------------------------------------+
class CQuantumNeuralBridge
{
private:
	CQuantumNeuralProcessor *m_qn_processor;
	CNeuralDependencyGraph  *m_dependency_graph;
	logger_institutional    &m_logger;
	string                   m_symbol;

	//+--------------------------------------------------------------+
	//| Processa estado híbrido                                       |
	//+--------------------------------------------------------------+
	bool ProcessHybridState()
	{
		if(!m_dependency_graph->ValidateDependencies("quantum_neural_core"))
		{
			m_logger.log_error("[BRIDGE] Falha na validação de dependências");
			return false;
		}

		return m_qn_processor->ProcessState();
	}

public:
	//+--------------------------------------------------------------+
	//| CONSTRUTOR                                                   |
	//+--------------------------------------------------------------+
	CQuantumNeuralBridge(CQuantumRegister &qr,
					   QuantumFirewall &qf,
					   logger_institutional &logger,
					   QuantumLearning &ql,
					   string symbol = _Symbol) :
		m_logger(logger),
		m_symbol(symbol)
	{
		m_qn_processor = new CQuantumNeuralProcessor(qr, qf, logger, ql, symbol);
		m_dependency_graph = new CNeuralDependencyGraph(logger, qf, ql, "MQL5/");

		if(m_qn_processor == NULL || m_dependency_graph == NULL)
		{
			m_logger.log_error("[BRIDGE] Falha ao criar componentes híbridos");
			ExpertRemove();
		}

		m_logger.log_info("[BRIDGE] Ponte Quântico-Neural inicializada");
	}

	//+--------------------------------------------------------------+
	//| Gera sinal de trading                                         |
	//+--------------------------------------------------------------+
	ENUM_TRADE_SIGNAL GenerateSignal()
	{
		if(!ProcessHybridState())
		{
			m_logger.log_error("[BRIDGE] Falha no processamento híbrido");
			return SIGNAL_NONE;
		}

		ENUM_TRADE_SIGNAL signal = m_qn_processor->GetDecisionSignal();
		double confidence = CalculateSignalConfidence();

		if(signal != SIGNAL_NONE && confidence < 0.65)
		{
			m_logger.log_warning("[BRIDGE] Sinal com baixa confiança bloqueado");
			return SIGNAL_NONE;
		}

		m_logger.log_info("[BRIDGE] Sinal gerado: " + TradeSignalUtils().ToString(signal) + 
						" | Confiança: " + DoubleToString(confidence, 3));
		return signal;
	}

	//+--------------------------------------------------------------+
	//| Calcula confiança do sinal                                    |
	//+--------------------------------------------------------------+
	double CalculateSignalConfidence()
	{
		// Implementação real usaria rede neural
		return 0.8 + MathRand() / 32767.0 * 0.2;
	}

	//+--------------------------------------------------------------+
	//| Destrutor                                                    |
	//+--------------------------------------------------------------+
	~CQuantumNeuralBridge()
	{
		if(m_qn_processor != NULL)
		{
			delete m_qn_processor;
			m_qn_processor = NULL;
		}

		if(m_dependency_graph != NULL)
		{
			delete m_dependency_graph;
			m_dependency_graph = NULL;
		}

		m_logger.log_info("[BRIDGE] Ponte Quântico-Neural encerrada");
	}
};

#endif // __QUANTUM_NEURAL_BRIDGE_MQH__


