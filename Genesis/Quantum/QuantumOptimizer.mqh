//+------------------------------------------------------------------+
//| QuantumOptimizer.mqh - Otimizador Quântico Avançado             |
//| Projeto: Genesis                                                |
//| Pasta: Include/Quantum/                                         |
//| Versão: v15.1 (GodMode Final + IA Ready)                        |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_OPTIMIZER_MQH__
#define __QUANTUM_OPTIMIZER_MQH__

#include <Controls/Label.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumAnnealingSimulator.mqh>
#include <Genesis/Quantum/QuantumGeneticAlgorithm.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>

//+------------------------------------------------------------------+
//| Métodos de Otimização Quântica                                   |
//+------------------------------------------------------------------+
enum ENUM_QUANTUM_OPTIMIZATION {
	QOPTIMIZE_ANNEALING,      // Recozimento quântico
	QOPTIMIZE_GENETIC,        // Algoritmo genético quântico
	QOPTIMIZE_GROVER,         // Busca de Grover
	QOPTIMIZE_HYBRID          // Método híbrido quântico-clássico
};

//+------------------------------------------------------------------+
//| Estrutura de Resultados de Otimização                            |
//+------------------------------------------------------------------+
struct QuantumOptimizationResult {
	datetime timestamp;
	string symbol;
	ENUM_QUANTUM_OPTIMIZATION method_used;
	double initial_energy;
	double final_energy;
	double improvement_rate;
	int iterations_performed;
	bool optimization_successful;
	double market_entropy;
	double execution_time_ms;
};

//+------------------------------------------------------------------+
//| Classe QuantumOptimizer - Otimização Quântica Avançada           |
//+------------------------------------------------------------------+
class QuantumOptimizer
{
private:
	logger_institutional          &m_logger;
	QuantumAnnealingSimulator    &m_annealer;
	QuantumGeneticAlgorithm      &m_qga;
	string                       m_symbol;
	ENUM_QUANTUM_OPTIMIZATION    m_optimization_method;
	double                       m_optimization_precision;
	datetime                     m_last_optimization_time;

	// Histórico de otimizações
	QuantumOptimizationResult m_optimization_history[];

	// Painel de decisão
	CLabel *m_optimize_label = NULL;

	//+--------------------------------------------------------------+
	//| Valida contexto antes da execução                             |
	//+--------------------------------------------------------------+
	bool is_valid_context()
	{
		if(!TerminalInfoInteger(TERMINAL_CONNECTED))
		{
			m_logger.log_error("[QOPTIM] Sem conexão com o servidor de mercado");
			return false;
		}

		if(!SymbolInfoInteger(m_symbol, SYMBOL_SELECT))
		{
			m_logger.log_error("[QOPTIM] Símbolo inválido: " + m_symbol);
			return false;
		}

		if(!m_annealer.IsReady())
		{
			m_logger.log_warning("[QOPTIM] Simulador de recozimento não está pronto");
			return false;
		}

		if(!m_qga.IsInitialized())
		{
			m_logger.log_warning("[QOPTIM] Algoritmo genético não inicializado");
			return false;
		}

		return true;
	}

	//+------------------------------------------------------------------+
	//| Executa Recozimento Quântico                                    |
	//+------------------------------------------------------------------+
	bool QuantumAnnealingOptimization(double ¶meters[], double &result[])
	{
		if(!is_valid_context()) return false;

		double initial_energy = CalculateEnergyState(parameters);
		if(DoubleIsNaN(initial_energy)) {
			m_logger.log_error("[QOPTIM] Energia inicial inválida");
			return false;
		}
		
		m_annealer.SetInitialState(parameters, initial_energy);
		
		if(!m_annealer.RunAnnealingProcess()) {
			m_logger.log_error("[QOPTIM] Falha no processo de recozimento");
			return false;
		}
		
		m_annealer.GetOptimizedParameters(result);
		double final_energy = CalculateEnergyState(result);
		
		m_logger.log_info(StringFormat(
			"[QOPTIM] Recozimento completo | Energia: %.2f -> %.2f",
			initial_energy,
			final_energy
		));
		
		return true;
	}

	//+------------------------------------------------------------------+
	//| Executa Algoritmo Genético Quântico                             |
	//+------------------------------------------------------------------+
	bool QuantumGeneticOptimization(double ¶meters[], double &result[])
	{
		if(!is_valid_context()) return false;

		m_qga.InitializePopulation(parameters);
		
		for(int generation=0; generation<10; generation++) {
			if(!m_qga.RunGeneration()) {
				m_logger.log_error("[QOPTIM] Falha na geração "+IntegerToString(generation));
				return false;
			}
		}
		
		m_qga.GetBestSolution(result);
		double fitness = m_qga.GetBestFitness();
		
		m_logger.log_info(StringFormat(
			"[QOPTIM] Evolução quântica completa | Fitness: %.4f",
			fitness
		));
		
		return true;
	}

	//+------------------------------------------------------------------+
	//| Calcula Estado de Energia (Função de Custo)                     |
	//+------------------------------------------------------------------+
	double CalculateEnergyState(double ¶meters)
	{
		if(ArraySize(parameters) == 0) return 0.0;

		double volatility = iATR(m_symbol, PERIOD_H1, 14)/Point;
		if(volatility <= 0.0) volatility = 1.0;
		
		double energy = 0.0;
		for(int i=0; i<ArraySize(parameters); i++) {
			if(DoubleIsNaN(parameters[i])) continue;
			energy += MathAbs(parameters[i]) * (i+1) * volatility;
		}
		return MathMax(0.0, energy);
	}

	//+--------------------------------------------------------------+
	//| Calcula entropia quântica do mercado                         |
	//+--------------------------------------------------------------+
	double CalculateMarketEntropy()
	{
		MqlRates rates[];
		CopyRates(m_symbol, PERIOD_M1, 0, 20, rates);
		double entropy = 0.0, sum = 0.0;
		for(int i = 0; i < ArraySize(rates); i++) sum += rates[i].close;
		if(sum <= 0) return 0.0;
		for(int i = 0; i < ArraySize(rates); i++)
		{
			double p = rates[i].close / sum;
			if(p > 0) entropy -= p * MathLog(p);
		}
		return NormalizeDouble(entropy, 4);
	}

	//+--------------------------------------------------------------+
	//| Atualiza painel de otimização                                |
	//+--------------------------------------------------------------+
	void updateOptimizeDisplay(double improvement)
	{
		if(m_optimize_label == NULL)
			m_optimize_label = new CLabel("OptimizeLabel", 0, 10, 450);

		m_optimize_label->text(StringFormat("OPT: %.0f%%",
			improvement * 100));

		m_optimize_label->color(
			!is_valid_context() ? clrRed :
			improvement > 0.3 ? clrMagenta :
			improvement > 0.1 ? clrOrange : clrYellow
		);
	}

public:
	//+------------------------------------------------------------------+
	//| Construtor Quântico                                              |
	//+------------------------------------------------------------------+
	QuantumOptimizer(
		logger_institutional &logger,
		QuantumAnnealingSimulator &annealer,
		QuantumGeneticAlgorithm &qga,
		string symbol,
		ENUM_QUANTUM_OPTIMIZATION method = QOPTIMIZE_HYBRID,
		double precision = 0.001
	) : m_logger(logger),
	   m_annealer(annealer),
	   m_qga(qga),
	   m_symbol(symbol),
	   m_optimization_method(method),
	   m_optimization_precision(MathMax(0.0001, MathMin(0.1, precision))),
	   m_last_optimization_time(0)
	{
		if(!m_logger.is_initialized())
		{
			Print("[QOPTIM] Logger não inicializado");
			ExpertRemove();
		}

		if(!m_annealer.IsReady() || !m_qga.IsInitialized()) {
			m_logger.log_error("[QOPTIM] Subsistema quântico não inicializado");
			ExpertRemove();
		}
		
		m_logger.log_info(StringFormat(
			"[QOPTIM] Otimizador inicializado para %s | Método: %s | Precisão: %.4f",
			m_symbol,
			EnumToString(m_optimization_method),
			m_optimization_precision
		));
	}

	//+------------------------------------------------------------------+
	//| Otimização Quântica de Parâmetros                                |
	//+------------------------------------------------------------------+
	bool OptimizeParameters(double ¶meters[], double &optimized_params[])
	{
		if(!is_valid_context())
		{
			m_logger.log_warning("[QOPTIM] Contexto inválido. Retornando parâmetros originais.");
			ArrayCopy(optimized_params, parameters);
			return false;
		}

		if(ArraySize(parameters) == 0)
		{
			m_logger.log_error("[QOPTIM] Vetor de parâmetros vazio");
			ArrayResize(optimized_params, 0);
			return false;
		}

		ArrayResize(optimized_params, ArraySize(parameters));
		ArrayCopy(optimized_params, parameters);
		
		double start_time = GetMicrosecondCount();
		double initial_energy = CalculateEnergyState(parameters);
		bool success = false;
		int iterations = 0;
		
		switch(m_optimization_method) {
			case QOPTIMIZE_ANNEALING:
				success = QuantumAnnealingOptimization(parameters, optimized_params);
				iterations = 1;
				break;
				
			case QOPTIMIZE_GENETIC:
				success = QuantumGeneticOptimization(parameters, optimized_params);
				iterations = 10;
				break;
				
			case QOPTIMIZE_HYBRID:
				// Primeiro recozimento, depois refinamento genético
				if(QuantumAnnealingOptimization(parameters, optimized_params)) {
					success = QuantumGeneticOptimization(optimized_params, optimized_params);
					iterations = 11;
				}
				break;
				
			default:
				m_logger.log_warning("[QOPTIM] Método desconhecido. Usando ANNEALING como fallback.");
				success = QuantumAnnealingOptimization(parameters, optimized_params);
				iterations = 1;
				break;
		}
		
		double final_energy = CalculateEnergyState(optimized_params);
		double improvement_rate = initial_energy > 0 ? (initial_energy - final_energy) / initial_energy : 0.0;
		double end_time = GetMicrosecondCount();
		double execution_time = (end_time - start_time) / 1000.0; // ms

		// Registro histórico
		QuantumOptimizationResult result;
		result.timestamp = TimeCurrent();
		result.symbol = m_symbol;
		result.method_used = m_optimization_method;
		result.initial_energy = initial_energy;
		result.final_energy = final_energy;
		result.improvement_rate = improvement_rate;
		result.iterations_performed = iterations;
		result.optimization_successful = success;
		result.market_entropy = CalculateMarketEntropy();
		result.execution_time_ms = execution_time;
		ArrayPushBack(m_optimization_history, result);

		if(success) {
			m_logger.log_info(StringFormat(
				"[QOPTIM] Parâmetros otimizados com sucesso | Melhoria: %.1f%% | Tempo: %.1fms",
				improvement_rate * 100,
				execution_time
			));
			
			// Atualiza display
			updateOptimizeDisplay(improvement_rate);
			
			m_last_optimization_time = TimeCurrent();
			return true;
		}
		
		m_logger.log_warning("[QOPTIM] Usando parâmetros originais como fallback");
		ArrayCopy(optimized_params, parameters);
		return false;
	}

	//+------------------------------------------------------------------+
	//| Otimização em Tempo Real                                         |
	//+------------------------------------------------------------------+
	void RealTimeOptimization(double ¶meters[], int interval_minutes=60)
	{
		while(!IsStopped()) {
			double optimized_params[];
			if(OptimizeParameters(parameters, optimized_params)) {
				ArrayCopy(parameters, optimized_params);
			}
			Sleep(interval_minutes*60000);
		}
	}

	//+--------------------------------------------------------------+
	//| Retorna se o sistema está pronto                             |
	//+--------------------------------------------------------------+
	bool IsReady() const
	{
		return m_annealer.IsReady() && m_qga.IsInitialized();
	}

	//+--------------------------------------------------------------+
	//| Obtém método atual de otimização                             |
	//+--------------------------------------------------------------+
	ENUM_QUANTUM_OPTIMIZATION GetCurrentMethod() const
	{
		return m_optimization_method;
	}

	//+--------------------------------------------------------------+
	//| Exporta histórico de otimização                              |
	//+--------------------------------------------------------------+
	bool ExportOptimizationHistory(string file_path)
	{
		int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT);
		if(handle == INVALID_HANDLE) return false;

		for(int i = 0; i < ArraySize(m_optimization_history); i++)
		{
			FileWrite(handle,
				TimeToString(m_optimization_history[i].timestamp, TIME_DATE|TIME_SECONDS),
				m_optimization_history[i].symbol,
				EnumToString(m_optimization_history[i].method_used),
				DoubleToString(m_optimization_history[i].initial_energy, 4),
				DoubleToString(m_optimization_history[i].final_energy, 4),
				DoubleToString(m_optimization_history[i].improvement_rate, 4),
				IntegerToString(m_optimization_history[i].iterations_performed),
				m_optimization_history[i].optimization_successful ? "SIM" : "NÃO",
				DoubleToString(m_optimization_history[i].market_entropy, 4),
				DoubleToString(m_optimization_history[i].execution_time_ms, 1)
			);
		}

		FileClose(handle);
		m_logger.log_info("[QOPTIM] Histórico de otimização exportado para: " + file_path);
		return true;
	}

	//+--------------------------------------------------------------+
	//| Obtém última taxa de melhoria                                |
	//+--------------------------------------------------------------+
	double GetLastImprovementRate()
	{
		if(ArraySize(m_optimization_history) == 0) return 0.0;
		return m_optimization_history[ArraySize(m_optimization_history)-1].improvement_rate;
	}
};

#endif // __QUANTUM_OPTIMIZER_MQH__


