//+------------------------------------------------------------------+
//| QuantumWaveletTransform.mqh - Transformada Wavelet Quântica     |
//| Projeto: Genesis                                                |
//| Pasta: Include/Quantum/                                         |
//| Versão: v2.2 (TIER-0 Quantum Institutional Grade)               |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_WAVELET_TRANSFORM_MQH__
#define __QUANTUM_WAVELET_TRANSFORM_MQH__

#ifdef GENESIS_ENABLE_UI
#include <Controls/Label.mqh>
#endif
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumEntanglement.mqh>
#include <Genesis/Neural/QuantumNeuralFilter.mqh>
#include <Genesis/Data/MarketDataQuantum.mqh>
#include <Genesis/Config/GenesisConfig.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
// #include <Genesis/Quantum/QuantumProcessor.mqh>         // REMOVIDO: Include circular
#include <Genesis/Utils/ArrayHybrid.mqh>

//+------------------------------------------------------------------+
//| PARÂMETROS QUÂNTICOS                                            |
//+------------------------------------------------------------------+
// Configurações padrão (evitar inputs em headers)
#ifndef QWT_QUBITS_WAVELET
  #define QWT_QUBITS_WAVELET CFG_QUBITS_WAVELET
#endif
#ifndef QWT_ENTROPY_THRESHOLD
  #define QWT_ENTROPY_THRESHOLD CFG_ENTROPY_THRESHOLD
#endif
#ifndef QWT_ENABLE_QUANTUM_DENOISE
  #define QWT_ENABLE_QUANTUM_DENOISE CFG_ENABLE_Q_DENOISE
#endif
// Evitar choque com UPDATE_INTERVAL_MS de outros headers
#ifndef QWT_UPDATE_INTERVAL_MS
  #define QWT_UPDATE_INTERVAL_MS CFG_QWT_UPDATE_MS
#endif

//+------------------------------------------------------------------+
//| ESTRUTURA DE COEFICIENTES QUÂNTICOS                             |
//+------------------------------------------------------------------+
struct QuantumWaveletCoeffs
{
	double approximation[];    // Coeficientes de aproximação
	double detail[];           // Coeficientes de detalhe
	double entropy_level;      // Nível de entropia quântica
	datetime timestamp;
	int     dominant_freq;     // Frequência dominante identificada
	double signal_strength;
	ENUM_TRADE_SIGNAL quantum_signal; // Sinal quântico gerado
};

//+------------------------------------------------------------------+
//| Estrutura de Resultados de Análise                              |
//+------------------------------------------------------------------+
struct QuantumWaveletResult {
	datetime timestamp;
	string symbol;
	double entropy_level;
	int dominant_frequency;
	double signal_strength;
	int market_state;
	double execution_time_ms;
	bool success;
	string analysis_summary;
	ENUM_TRADE_SIGNAL generated_signal;
};

//+------------------------------------------------------------------+
//| CLASSE PRINCIPAL: QuantumWaveletTransform                       |
//+------------------------------------------------------------------+
class QuantumWaveletTransform
{
private:
	logger_institutional *m_logger;
    QuantumEntanglement  *m_entangler;
    QuantumNeuralFilter  *m_qfilter;
    CGenesisQuantumMarketData *m_qdata;
	string               m_symbol;
	datetime             m_last_analysis_time;

	QuantumWaveletCoeffs  m_qcoeffs;
	double               m_quantum_noise_floor;
	
	// Histórico de análises
	QuantumWaveletResult m_analysis_history[];

	// Painel de decisão
#ifdef GENESIS_ENABLE_UI
	CLabel *m_wavelet_label;
	CLabel *m_wavelet_signal;
#endif

	//+--------------------------------------------------------------+
	//| Valida contexto antes da execução                             |
	//+--------------------------------------------------------------+
	bool is_valid_context()
	{
		if(!TerminalInfoInteger(TERMINAL_CONNECTED))
		{
			if(m_logger) m_logger->log_error("[QWT] Sem conexão com o servidor de mercado");
			return false;
		}

        if(!m_entangler || !m_entangler->IsEntanglementActive())
		{
			if(m_logger) m_logger->log_warning("[QWT] Emaranhamento quântico não ativo");
			return false;
		}

        if(!m_qfilter || !m_qfilter->IsReady())
		{
			if(m_logger) m_logger->log_warning("[QWT] Filtro neural não está pronto");
			return false;
		}

		// m_qdata readiness simplificada
		if(!m_qdata)
		{
			if(m_logger) m_logger->log_warning("[QWT] Dados quânticos não conectados");
			return false;
		}

		return true;
	}

	//+---------------------------------------------------------------+
	//| MÉTODO: ApplyQuantumWavelet                                   |
	//+---------------------------------------------------------------+
	bool ApplyQuantumWavelet()
	{
		if(!is_valid_context())
		{
			if(m_logger) m_logger->log_error("[QWT] Contexto inválido. Análise bloqueada.");
			return false;
		}

		double start_time = GetMicrosecondCount();

		// Obter dados do mercado em superposição quântica
		double price_superposition[];
        // Fallback simples de série de preço
        ArrayResize(price_superposition, QWT_QUBITS_WAVELET);
        for(int i=0;i<QWT_QUBITS_WAVELET;i++){ price_superposition[i]=iClose(m_symbol, PERIOD_M1, i); }
		
		// Configurar arrays de coeficientes
        ArrayResize(m_qcoeffs.approximation, QWT_QUBITS_WAVELET/2);
        ArrayResize(m_qcoeffs.detail, QWT_QUBITS_WAVELET/2);
		
		// Transformada Wavelet Quântica (Haar-like)
		for(int i=0; i<QWT_QUBITS_WAVELET && i+1<ArraySize(price_superposition); i+=2)
		{
			// Emaranhamento quântico entre pares de preços
			double entangled_pair[2];
            if(m_entangler->EntanglePair(price_superposition[i], price_superposition[i+1], entangled_pair))
			{
				// Cálculo dos coeficientes com efeito quântico
				m_qcoeffs.approximation[i/2] = (entangled_pair[0] + entangled_pair[1])/MathSqrt(2.0);
				m_qcoeffs.detail[i/2] = (entangled_pair[0] - entangled_pair[1])/MathSqrt(2.0);
			}
			else
			{
				// Fallback clássico
				m_qcoeffs.approximation[i/2] = (price_superposition[i] + price_superposition[i+1])/2.0;
				m_qcoeffs.detail[i/2] = (price_superposition[i] - price_superposition[i+1])/2.0;
			}
		}
		
		// Aplicar filtro neural quântico
		if(QWT_ENABLE_QUANTUM_DENOISE && m_qfilter)
		{
			m_qfilter->QuantumDenoise(m_qcoeffs.approximation);
			m_qfilter->QuantumDenoise(m_qcoeffs.detail);
		}
		
		// Cálculo de entropia quântica
		m_qcoeffs.entropy_level = CalculateQuantumEntropy();
		m_qcoeffs.signal_strength = 1.0 - m_qcoeffs.entropy_level;
		m_qcoeffs.timestamp = TimeCurrent();
		
		// Identificar frequência dominante
		m_qcoeffs.dominant_freq = IdentifyDominantFrequency();
		
		// Gerar sinal quântico
		m_qcoeffs.quantum_signal = GenerateQuantumSignal();
		
		double end_time = GetMicrosecondCount();
		double execution_time = (end_time - start_time) / 1000.0; // ms
		
		// Registro histórico
		QuantumWaveletResult result;
		result.timestamp = TimeCurrent();
		result.symbol = m_symbol;
		result.entropy_level = m_qcoeffs.entropy_level;
		result.dominant_frequency = m_qcoeffs.dominant_freq;
		result.signal_strength = m_qcoeffs.signal_strength;
		result.market_state = GetMarketQuantumState();
		result.execution_time_ms = execution_time;
		result.success = true;
		result.analysis_summary = StringFormat("E:%.2f|F:%d|S:%.2f", 
			m_qcoeffs.entropy_level, 
			m_qcoeffs.dominant_freq, 
			m_qcoeffs.signal_strength);
		result.generated_signal = m_qcoeffs.quantum_signal;
		{ int __i = ArraySize(m_analysis_history); ArrayResize(m_analysis_history, __i + 1); m_analysis_history[__i] = result; }

		if(m_logger) m_logger->log_info("[QWT] Transformada concluída - Entropia: " + 
						DoubleToString(m_qcoeffs.entropy_level,3) +
						" | Frequência dominante: " + IntegerToString(m_qcoeffs.dominant_freq) +
						" | Sinal: " + TradeSignalUtils().ToString(m_qcoeffs.quantum_signal) +
						" | Tempo: " + DoubleToString(execution_time, 1) + "ms");
		
		m_last_analysis_time = TimeCurrent();
		
		// Atualiza painel
		updateWaveletDisplay(m_qcoeffs.signal_strength, m_qcoeffs.quantum_signal);
		
		return true;
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: CalculateQuantumEntropy                               |
	//+---------------------------------------------------------------+
	double CalculateQuantumEntropy()
	{
		if(ArraySize(m_qcoeffs.detail) == 0) return 0.0;

		double total_energy = 0.0;
		for(int i=0; i<ArraySize(m_qcoeffs.detail); i++)
		{
            if(MathIsValidNumber(m_qcoeffs.detail[i]))
				total_energy += m_qcoeffs.detail[i] * m_qcoeffs.detail[i];
		}
		
		if(total_energy <= 0.0) return 0.0;
		
		double entropy = 0.0;
		for(int i=0; i<ArraySize(m_qcoeffs.detail); i++)
		{
            double p = (m_qcoeffs.detail[i] * m_qcoeffs.detail[i]) / total_energy;
            if(p > 0 && MathIsValidNumber(p))
				entropy -= p * MathLog(p);
		}
		
		double normalized_entropy = entropy / MathLog(ArraySize(m_qcoeffs.detail));
		return MathMax(0.0, MathMin(1.0, normalized_entropy));
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: IdentifyDominantFrequency                             |
	//+---------------------------------------------------------------+
	int IdentifyDominantFrequency()
	{
		double max_power = -1;
		int dominant_idx = 0;
		
		for(int i=0; i<ArraySize(m_qcoeffs.detail); i++)
		{
            if(!MathIsValidNumber(m_qcoeffs.detail[i])) continue;
			
			double power = m_qcoeffs.detail[i] * m_qcoeffs.detail[i];
            if(power > max_power && power > QWT_ENTROPY_THRESHOLD)
			{
				max_power = power;
				dominant_idx = i;
			}
		}
		
		return dominant_idx;
	}

	//+---------------------------------------------------------------+
	//| Gera sinal quântico baseado na análise                        |
	//+---------------------------------------------------------------+
	ENUM_TRADE_SIGNAL GenerateQuantumSignal()
	{
		if(m_qcoeffs.signal_strength > 0.8 && m_qcoeffs.dominant_freq < 10)
			return SIGNAL_QUANTUM_FLASH;
		else if(m_qcoeffs.entropy_level > 0.7)
			return SIGNAL_QUANTUM_ALERT;
		else if(m_qcoeffs.signal_strength > 0.6)
			return SIGNAL_BUY;
		else if(m_qcoeffs.signal_strength < 0.4)
			return SIGNAL_SELL;
		else
			return SIGNAL_NONE;
	}

	//+--------------------------------------------------------------+
	//| Atualiza painel de wavelet                                   |
	//+--------------------------------------------------------------+
	void updateWaveletDisplay(double signal_strength, ENUM_TRADE_SIGNAL signal)
	{
#ifdef GENESIS_ENABLE_UI
		if(m_wavelet_label == NULL)
		{
			m_wavelet_label = new CLabel("WaveletLabel", 0, 10, 550);
            m_wavelet_label->Text("WLT: 0%");
            m_wavelet_label->Color(clrGray);
		}

		if(m_wavelet_signal == NULL)
		{
			m_wavelet_signal = new CLabel("WaveletSignal", 0, 10, 570);
            m_wavelet_signal->Text("SIG: NONE");
            m_wavelet_signal->Color(clrGray);
		}

        m_wavelet_label->Text(StringFormat("WLT: %.0f%%", signal_strength * 100));
        m_wavelet_label->Color(
			signal_strength > 0.7 ? clrMagenta :
			signal_strength > 0.5 ? clrOrange : clrYellow
		);

        m_wavelet_signal->Text("SIG: " + TradeSignalUtils().ToString(signal));
        m_wavelet_signal->Color(
			signal == SIGNAL_QUANTUM_FLASH ? clrRed :
			signal == SIGNAL_BUY ? clrLime :
			signal == SIGNAL_SELL ? clrRed : clrGray
		);
#else
		Print(StringFormat("[QWT] WLT=%.0f%% | SIG=%s", signal_strength*100, TradeSignalUtils().ToString(signal)));
#endif
	}

public:
	//+---------------------------------------------------------------+
	//| CONSTRUTOR                                                    |
	//+---------------------------------------------------------------+
    QuantumWaveletTransform(logger_institutional *logger,
                          QuantumEntanglement &qe, 
                          QuantumNeuralFilter &qnf, 
                          CGenesisQuantumMarketData &qmd,
                          string symbol = _Symbol) :
        m_logger(logger),
        m_entangler(&qe),
        m_qfilter(&qnf),
        m_qdata(&qmd),
		m_symbol(symbol),
		m_last_analysis_time(0)
	{
#ifdef GENESIS_ENABLE_UI
        m_wavelet_label = NULL;
        m_wavelet_signal = NULL;
#endif
        if(!m_logger || !m_logger->is_initialized())
		{
			Print("[QWT] Logger não inicializado");
			ExpertRemove();
		}

		// Verificação de integridade quântica
        if(!m_entangler || !m_entangler->IsEntanglementActive())
		{
			if(m_logger) m_logger->log_error("[QWT] Emaranhamento quântico não ativo");
			ExpertRemove();
		}
		
        ArrayResize(m_qcoeffs.approximation, QWT_QUBITS_WAVELET/2);
        ArrayResize(m_qcoeffs.detail, QWT_QUBITS_WAVELET/2);
		m_qcoeffs.entropy_level = 0.0;
		m_qcoeffs.dominant_freq = -1;
		m_qcoeffs.signal_strength = 0.0;
		m_qcoeffs.quantum_signal = SIGNAL_NONE;
		
		if(m_logger) m_logger->log_info("[QWT] Transformada Wavelet Quântica inicializada com " + 
                        IntegerToString(QWT_QUBITS_WAVELET) + " qubits");
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: ExecuteQuantumWavelet                                 |
	//+---------------------------------------------------------------+
	QuantumWaveletCoeffs ExecuteQuantumWavelet()
	{
		if(ApplyQuantumWavelet())
			return m_qcoeffs;
		
        QuantumWaveletCoeffs error_coeffs;
        ArrayResize(error_coeffs.approximation, QWT_QUBITS_WAVELET/2);
        ArrayResize(error_coeffs.detail, QWT_QUBITS_WAVELET/2);
		ArrayInitialize(error_coeffs.approximation, 0.0);
		ArrayInitialize(error_coeffs.detail, 0.0);
		error_coeffs.entropy_level = -1;
		error_coeffs.dominant_freq = -1;
		error_coeffs.timestamp = TimeCurrent();
		error_coeffs.signal_strength = 0.0;
		error_coeffs.quantum_signal = SIGNAL_NONE;
		
        if(m_logger) m_logger->log_warning("[QWT] Falha na transformada wavelet - Usando coeficientes de fallback");
		return error_coeffs;
	}
	
	//+---------------------------------------------------------------+
	//| MÉTODO: GetMarketQuantumState                                 |
	//+---------------------------------------------------------------+
	int GetMarketQuantumState()
	{
		if(m_qcoeffs.entropy_level < 0.3)
			return 0; // Mercado tranquilo
		else if(m_qcoeffs.entropy_level < 0.6)
			return 1; // Mercado em transição
		else
			return 2; // Mercado caótico
	}

	//+--------------------------------------------------------------+
	//| Retorna se o sistema está pronto                             |
	//+--------------------------------------------------------------+
    bool IsReady() const
    {
        return m_entangler && m_entangler->IsEntanglementActive() && 
               m_qfilter && m_qfilter->IsReady() && 
               m_qdata != NULL; // simplificado
    }

	//+--------------------------------------------------------------+
	//| Obtém nível de sinal quântico                                |
	//+--------------------------------------------------------------+
	double GetSignalStrength()
	{
		if(ArraySize(m_analysis_history) == 0) return 0.0;
		return m_analysis_history[ArraySize(m_analysis_history)-1].signal_strength;
	}

	//+--------------------------------------------------------------+
	//| Obtém último sinal quântico gerado                           |
	//+--------------------------------------------------------------+
	ENUM_TRADE_SIGNAL GetLastSignal()
	{
		if(ArraySize(m_analysis_history) == 0) return SIGNAL_NONE;
		return m_analysis_history[ArraySize(m_analysis_history)-1].generated_signal;
	}

	//+--------------------------------------------------------------+
	//| Exporta histórico de análise                                 |
	//+--------------------------------------------------------------+
	bool ExportAnalysisHistory(string file_path)
	{
		int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT);
		if(handle == INVALID_HANDLE) return false;

		for(int i = 0; i < ArraySize(m_analysis_history); i++)
		{
			FileWrite(handle,
				TimeToString(m_analysis_history[i].timestamp, TIME_DATE|TIME_SECONDS),
				m_analysis_history[i].symbol,
				DoubleToString(m_analysis_history[i].entropy_level, 4),
				IntegerToString(m_analysis_history[i].dominant_frequency),
				DoubleToString(m_analysis_history[i].signal_strength, 4),
				IntegerToString(m_analysis_history[i].market_state),
				DoubleToString(m_analysis_history[i].execution_time_ms, 1),
				m_analysis_history[i].success ? "SIM" : "NÃO",
				m_analysis_history[i].analysis_summary,
				TradeSignalUtils().ToString(m_analysis_history[i].generated_signal)
			);
		}

        FileClose(handle);
        if(m_logger) m_logger->log_info("[QWT] Histórico de análise exportado para: " + file_path);
		return true;
	}
};

#endif // __QUANTUM_WAVELET_TRANSFORM_MQH__


