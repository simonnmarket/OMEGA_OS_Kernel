//+------------------------------------------------------------------+
//| QuantumProcessor.mqh - Processador Quântico Central             |
//| Projeto: Genesis                                                |
//| Pasta: Include/Quantum/                                         |
//| Versão: v1.3 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_PROCESSOR_MQH__
#define __QUANTUM_PROCESSOR_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Security/QuantumFirewall.mqh>
#include <Genesis/Core/QuantumBlockchain.mqh>
#include <Genesis/Risk/RiskProfile.mqh>
// #include <Genesis/Quantum/QuantumDecisionPanel.mqh> // REMOVIDO: Include circular
// Forward declarations para evitar ciclos pesados
class QuantumDecisionPanel;
class CLabel;
class CQuantumRegister;
class CQuantumSignalGenerator;
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Quantum/QuantumDataProcessor.mqh>
#include <Genesis/Quantum/QuantumWaveletTransform.mqh>
// Garantir definição de CQuantumSignalGenerator
#include <Genesis/Quantum/QuantumSignalGenerator.mqh>
// Evitar ciclo com BehaviorController: usar forward declaration e não invocar métodos
class QuantumBehaviorController;
#include <Genesis/Analysis/QuantumLiquidityMatrix.mqh>
#include <Genesis/Detection/QuantumPatternScanner.mqh>
#include <Genesis/Intelligence/QuantumAdaptiveLearning.mqh>
#include <Genesis/Quantum/QuantumFinanceFramework.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>

//+------------------------------------------------------------------+
//| Definições (evitar inputs em headers)                           |
//+------------------------------------------------------------------+
#ifndef QPROC_CONFIDENCE_THRESHOLD
#define QPROC_CONFIDENCE_THRESHOLD 0.75
#endif
#ifndef QPROC_SIGNAL_UPDATE_FREQ
#define QPROC_SIGNAL_UPDATE_FREQ 60
#endif
#ifndef QPROC_UPDATE_INTERVAL_MS
#define QPROC_UPDATE_INTERVAL_MS 50
#endif

//+------------------------------------------------------------------+
//| Estrutura para sinal consolidado                                |
//+------------------------------------------------------------------+
struct QuantumSignal
{
	ENUM_TRADE_SIGNAL signal;
	double confidence;
	double amplitude;
	datetime timestamp;
	double signal_strength;
	string source_module;
	bool is_crisis_signal;
	double risk_multiplier;
	double reward_ratio;
};

//+------------------------------------------------------------------+
//| CLASSE PRINCIPAL: QuantumProcessor - Processador Quântico       |
//+------------------------------------------------------------------+
class QuantumProcessor
{
private:
	logger_institutional      *m_logger;
	QuantumFirewall           *m_firewall;
	QuantumBlockchain         *m_blockchain;
	RiskProfile               *m_risk_profile;
	QuantumDecisionPanel      *m_decision_panel;
	QuantumDataProcessor      *m_data_processor;
	QuantumWaveletTransform   *m_wavelet;
	QuantumBehaviorController *m_behavior;
	QuantumLiquidityMatrix    *m_liquidity;
	QuantumPatternScanner     *m_pattern_scanner;
	QuantumAdaptiveLearning   *m_learning;
	CQuantumRegister          *m_quantum_register;
	CQuantumSignalGenerator   *m_signal_generator;
	string                    m_symbol;
	datetime                  m_last_signal_time;

	QuantumSignal             m_current_signal;

	// Painel de decisão
	CLabel *m_signal_label;
	CLabel *m_confidence_value;

	//+--------------------------------------------------------------+
	//| Valida contexto antes da execução                             |
	//+--------------------------------------------------------------+
	bool is_valid_context()
	{
		if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_error("[PROCESSOR] Sem conexão com o servidor de mercado"); return false; }
		if(!m_firewall || !m_firewall->IsActive()) { if(m_logger) m_logger->log_error("[PROCESSOR] Firewall quântico inativo"); return false; }
		if(!m_risk_profile || !m_risk_profile->is_initialized()) { if(m_logger) m_logger->log_warning("[PROCESSOR] Perfil de risco não inicializado"); return false; }
		if(!m_quantum_register || !m_quantum_register->IsReady()) { if(m_logger) m_logger->log_error("[PROCESSOR] Registrador quântico não está pronto"); return false; }
		return true;
	}

	//+--------------------------------------------------------------+
	//| Atualiza sinal consolidado                                   |
	//+--------------------------------------------------------------+
	void UpdateSignal()
	{
		if(!is_valid_context())
		{
			if(m_logger) m_logger->log_error("[PROCESSOR] Contexto inválido. Atualização bloqueada.");
			return;
		}

		double start_time = GetMicrosecondCount();

		// Atualiza estado quântico com dados de mercado
		double market_data[2] = {m_wavelet ? m_wavelet->GetWaveletAmplitude() : 0.0, m_liquidity ? m_liquidity->GetLiquidityEntropy() : 0.0};
		if(m_signal_generator) m_signal_generator->UpdateMarketState(market_data);

		// Gera sinal quântico
		ENUM_TRADE_SIGNAL quantum_signal = m_signal_generator ? m_signal_generator->GenerateSignal() : SIGNAL_NONE;
		double quantum_strength = m_signal_generator ? m_signal_generator->GetSignalStrength() : 0.0;
		double quantum_confidence = m_signal_generator ? m_signal_generator->GetSignalConfidence() : 0.0;

		// Obter sinais dos módulos
		ENUM_TRADE_SIGNAL data_signal = m_data_processor ? m_data_processor->GetCurrentSignal() : SIGNAL_NONE;
		ENUM_TRADE_SIGNAL pattern_signal = m_pattern_scanner ? m_pattern_scanner->GetLastSignal() : SIGNAL_NONE;
		ENUM_TRADE_SIGNAL learning_signal = m_learning ? m_learning->GetLastSignal() : SIGNAL_NONE;
        // Evitar invocar método de QuantumBehaviorController para quebrar ciclo
        ENUM_TRADE_SIGNAL behavior_signal = SIGNAL_NONE;

		// Calcular confiança ponderada
		double confidence = 0.0;
		double total_weight = 0.0;

		if(quantum_signal != SIGNAL_NONE) 
		{ 
			double weight = 1.5; // Peso máximo para sinal quântico
			confidence += quantum_confidence * weight; 
			total_weight += weight;
		}

		if(data_signal != SIGNAL_NONE && m_data_processor) { double weight = 1.0; confidence += m_data_processor->GetSignalConfidence() * weight; total_weight += weight; }

		if(pattern_signal != SIGNAL_NONE) 
		{ 
			double weight = 1.2; // Peso maior para padrões quânticos
			confidence += 0.8 * weight; 
			total_weight += weight;
		}

		if(learning_signal != SIGNAL_NONE) 
		{ 
			double weight = 1.1;
			confidence += (m_learning ? m_learning->GetQuantumMetrics().quantum_sharpe : 0.0) * weight; 
			total_weight += weight;
		}

		if(behavior_signal != SIGNAL_NONE) 
		{ 
			double weight = 1.3;
			confidence += 0.9 * weight; 
			total_weight += weight;
		}

		confidence = total_weight > 0 ? confidence / total_weight : 0.0;

		// Calcular amplitude
		double amplitude = m_wavelet ? m_wavelet->GetWaveletAmplitude() : 0.0;
		amplitude = MathMax(0.0, MathMin(1.0, amplitude));

		// Determinar sinal final
		ENUM_TRADE_SIGNAL final_signal = SIGNAL_NONE;
		if(confidence >= QPROC_CONFIDENCE_THRESHOLD)
		{
			// Prioridade: Quântico > Comportamento > Padrão > Aprendizado > Dados
			if(quantum_signal != SIGNAL_NONE) final_signal = quantum_signal;
			else if(behavior_signal != SIGNAL_NONE) final_signal = behavior_signal;
			else if(pattern_signal != SIGNAL_NONE) final_signal = pattern_signal;
			else if(learning_signal != SIGNAL_NONE) final_signal = learning_signal;
			else if(data_signal != SIGNAL_NONE) final_signal = data_signal;
		}

		// Obter multiplicador de risco
		double risk_multiplier = m_risk_profile ? m_risk_profile->get_risk_multiplier() : 1.0;
		double reward_ratio = 2.0; // Simulação

		// Atualizar sinal atual
		m_current_signal.signal = final_signal;
		m_current_signal.confidence = confidence;
		m_current_signal.amplitude = amplitude;
		m_current_signal.timestamp = TimeCurrent();
		m_current_signal.signal_strength = confidence * amplitude;
		m_current_signal.source_module = "QuantumProcessor";
		m_current_signal.is_crisis_signal = (final_signal == SIGNAL_QUANTUM_CRISIS);
		m_current_signal.risk_multiplier = risk_multiplier;
		m_current_signal.reward_ratio = reward_ratio;

		double end_time = GetMicrosecondCount();
		double execution_time = (end_time - start_time) / 1000.0; // ms

		if(m_logger) m_logger->log_info("[PROCESSOR] Sinal consolidado: " + 
						TradeSignalUtils().ToString(final_signal) + 
						" | Confiança: " + DoubleToString(confidence, 3) +
						" | Amplitude: " + DoubleToString(amplitude, 3) +
						" | Multi: " + DoubleToString(risk_multiplier, 2) +
						" | Tempo: " + DoubleToString(execution_time, 1) + "ms");

		m_last_signal_time = TimeCurrent();
		updateSignalDisplay(final_signal, confidence);
	}

	//+--------------------------------------------------------------+
	//| Atualiza painel de sinal                                     |
	//+--------------------------------------------------------------+
	void updateSignalDisplay(ENUM_TRADE_SIGNAL signal, double confidence)
	{
		if(m_signal_label == NULL)
		{
			m_signal_label = new CLabel("SignalLabel", 0, 10, 1450);
			m_signal_label->Text("SINAL: ????");
			m_signal_label->Color(clrGray);
		}

		if(m_confidence_value == NULL)
		{
			m_confidence_value = new CLabel("ConfidenceValue", 0, 10, 1470);
			m_confidence_value->Text("CONF: 0%");
			m_confidence_value->Color(clrGray);
		}

		m_signal_label->Text("SINAL: " + TradeSignalUtils().ToString(signal));
		m_signal_label->Color(
			signal == SIGNAL_QUANTUM_FLASH ? clrRed :
			signal == SIGNAL_BUY ? clrLime :
			signal == SIGNAL_SELL ? clrRed : clrGray
		);

		m_confidence_value->Text("CONF: " + DoubleToString(confidence*100, 0) + "%");
		m_confidence_value->Color(
			confidence > 0.8 ? clrLime :
			confidence > 0.5 ? clrYellow : clrRed
		);
	}

public:
	//+--------------------------------------------------------------+
	//| CONSTRUTOR                                                   |
	//+--------------------------------------------------------------+
	QuantumProcessor(logger_institutional *logger,
			  QuantumFirewall *qf,
			  QuantumBlockchain *qb,
			  RiskProfile *rp,
			  QuantumDecisionPanel *qdp,
			  QuantumDataProcessor *qdp2,
			  QuantumWaveletTransform *qwt,
			  QuantumBehaviorController *qbc,
			  QuantumLiquidityMatrix *qlm,
			  QuantumPatternScanner *qps,
			  QuantumAdaptiveLearning *qal,
			  CQuantumRegister *qr,
			  CQuantumSignalGenerator *qsg,
			  string symbol = "") :
		m_logger(logger),
		m_firewall(qf),
		m_blockchain(qb),
		m_risk_profile(rp),
		m_decision_panel(qdp),
		m_data_processor(qdp2),
		m_wavelet(qwt),
		m_behavior(qbc),
		m_liquidity(qlm),
		m_pattern_scanner(qps),
		m_learning(qal),
		m_quantum_register(qr),
		m_signal_generator(qsg),
		m_symbol(symbol),
		m_last_signal_time(0)
	{
		if(m_symbol == "") m_symbol = _Symbol;
		m_signal_label = NULL;
		m_confidence_value = NULL;
		if(!m_logger || !m_logger->is_initialized()) { Print("[PROCESSOR] Logger não inicializado"); ExpertRemove(); }
		if(!m_firewall || !m_firewall->IsActive()) { if(m_logger) m_logger->log_error("[PROCESSOR] Firewall quântico não ativo"); ExpertRemove(); }
		if(!m_blockchain || !m_blockchain->IsReady()) { if(m_logger) m_logger->log_error("[PROCESSOR] Blockchain quântico não está pronto"); ExpertRemove(); }

		m_current_signal.signal = SIGNAL_NONE;
		m_current_signal.confidence = 0.0;
		m_current_signal.amplitude = 0.0;
		m_current_signal.timestamp = TimeCurrent();
		m_current_signal.signal_strength = 0.0;
		m_current_signal.source_module = "QuantumProcessor";
		m_current_signal.is_crisis_signal = false;
		m_current_signal.risk_multiplier = 1.0;
		m_current_signal.reward_ratio = 1.0;

		if(m_logger) m_logger->log_info("[PROCESSOR] QuantumProcessor inicializado para " + m_symbol);
	}

	//+--------------------------------------------------------------+
	//| Obtém sinal consolidado                                      |
	//+--------------------------------------------------------------+
	ENUM_TRADE_SIGNAL GetCurrentSignal()
	{
		UpdateSignal();
		return m_current_signal.signal;
	}

	//+--------------------------------------------------------------+
	//| Obtém confiança do sinal                                     |
	//+--------------------------------------------------------------+
	double GetSignalConfidence()
	{
		UpdateSignal();
		return m_current_signal.confidence;
	}

	//+--------------------------------------------------------------+
	//| Retorna se está pronto                                       |
	//+--------------------------------------------------------------+
	bool IsReady() const
	{
		return m_firewall && m_firewall->IsActive() && 
			   m_risk_profile && m_risk_profile->is_initialized() && 
			   m_blockchain && m_blockchain->IsReady() &&
			   m_quantum_register && m_quantum_register->IsReady();
	}

	//+--------------------------------------------------------------+
	//| Obtém último sinal                                           |
	//+--------------------------------------------------------------+
	ENUM_TRADE_SIGNAL GetLastSignal() const
	{
		return m_current_signal.signal;
	}
};

#endif // __QUANTUM_PROCESSOR_MQH__


