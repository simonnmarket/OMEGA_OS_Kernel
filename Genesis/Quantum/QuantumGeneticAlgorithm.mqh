//+------------------------------------------------------------------+
//| quantum_genetic_algorithm.mqh - Algoritmo Genético Quântico      |
//| Projeto: Genesis                                                 |
//| Pasta: Include/Quantum/                                          |
//| Versão: v1.1 (GodMode Final + IA Ready)                          |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_GENETIC_ALGORITHM_MQH__
#define __QUANTUM_GENETIC_ALGORITHM_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Security/QuantumFirewall.mqh>
#include <Genesis/Intelligence/QuantumAdaptiveLearning.mqh>
#include <Genesis/Quantum/QuantumOptimizer.mqh>
#include <Genesis/Utils/ArrayHybrid.mqh>
#include <Controls/Label.mqh>

//+------------------------------------------------------------------+
//| Definições de Input                                              |
//+------------------------------------------------------------------+
input int POPULATION_SIZE = 50;       // Tamanho da população
input int GENERATIONS = 20;           // Número de gerações
input double MUTATION_RATE = 0.1;     // Taxa de mutação

//+------------------------------------------------------------------+
//| Estrutura para indivíduo genético                                |
//+------------------------------------------------------------------+
struct GeneticIndividual
{
   double weights[];
   double fitness;
   datetime timestamp;
};

//+------------------------------------------------------------------+
//| Estrutura de Resultados de Evolução                              |
//+------------------------------------------------------------------+
struct QuantumGeneticResult {
   datetime timestamp;
   string symbol;
   int generation;
   double best_fitness;
   double average_fitness;
   double fitness_improvement;
   double mutation_rate;
   bool success;
   double market_entropy;
   string best_weights_str;
};

//+------------------------------------------------------------------+
//| Classe QuantumGeneticAlgorithm - Algoritmo genético quântico     |
//+------------------------------------------------------------------+
class QuantumGeneticAlgorithm
{
private:
   logger_institutional &m_logger;
   QuantumFirewall     &m_firewall;
   AdaptiveLearning    &m_adaptive_learning;
   QuantumOptimizer    &m_optimizer;
   string               m_symbol;
   GeneticIndividual    m_population[];
   datetime             m_last_update;
   int                  m_generation_count;

   // Histórico de evoluções
   QuantumGeneticResult m_evolution_history[];

   // Painel de decisão
   CLabel *m_genetic_label = NULL;

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         m_logger.log_error("[GENETIC] Sem conexão com o servidor de mercado");
         return false;
      }

      if(!m_firewall.is_firewall_active())
      {
         m_logger.log_error("[GENETIC] QuantumFirewall inativo, evolução bloqueada");
         return false;
      }

      if(!m_adaptive_learning.IsReady())
      {
         m_logger.log_warning("[GENETIC] Módulo de aprendizado não está pronto");
         return false;
      }

      if(!m_optimizer.IsReady())
      {
         m_logger.log_warning("[GENETIC] Otimizador não está pronto");
         return false;
      }

      return true;
   }

   double CalculateFitness(double &weights[])
   {
      if(!is_valid_context()) return 0.0;

      PerformanceMetrics metrics = m_adaptive_learning.GetPerformanceMetrics();
      if(metrics.profit_factor <= 0.0 || metrics.drawdown < 0.0)
         return 0.0;

      double fitness = metrics.profit_factor - metrics.drawdown;
      fitness = MathMax(0.0, fitness);
      m_logger.log_info("[GENETIC] Fitness calculado: " + DoubleToString(fitness, 4));
      return fitness;
   }

   void InitializePopulation()
   {
      if(ArraySize(m_population) != POPULATION_SIZE)
         ArrayResize(m_population, POPULATION_SIZE);

      for(int i = 0; i < POPULATION_SIZE; i++)
      {
         ArrayResize(m_population[i].weights, 3);
         for(int j = 0; j < 3; j++)
         {
            m_population[i].weights[j] = MathRand() / 32767.0; // Superposição simulada
            m_population[i].weights[j] = NormalizeDouble(MathMax(0.1, MathMin(m_population[i].weights[j], 1.0)), 2);
         }
         m_population[i].fitness = CalculateFitness(m_population[i].weights);
         m_population[i].timestamp = TimeCurrent();
      }
      m_logger.log_info("[GENETIC] População inicializada: Tamanho=" + IntegerToString(POPULATION_SIZE));
   }

   bool EvolvePopulation()
   {
      if(!is_valid_context())
      {
         m_logger.log_error("[GENETIC] Contexto inválido. Evolução bloqueada.");
         return false;
      }

      if(!m_firewall.is_firewall_active())
      {
         m_logger.log_error("[GENETIC] QuantumFirewall inativo, evolução bloqueada");
         return false;
      }

      InitializePopulation();
      m_generation_count = 0;

      for(int gen = 0; gen < GENERATIONS && !IsStopped(); gen++)
      {
         GeneticIndividual new_population[];
         ArrayResize(new_population, POPULATION_SIZE);
         
         int best_index = 0;
         double best_fitness = m_population[0].fitness;
         for(int i = 1; i < POPULATION_SIZE; i++)
         {
            if(m_population[i].fitness > best_fitness)
            {
               best_fitness = m_population[i].fitness;
               best_index = i;
            }
         }
         ArrayCopy(new_population[0].weights, m_population[best_index].weights);
         new_population[0].fitness = best_fitness;
         new_population[0].timestamp = TimeCurrent();
         
         for(int i = 1; i < POPULATION_SIZE; i++)
         {
            ArrayResize(new_population[i].weights, 3);
            int parent1 = MathRand() % POPULATION_SIZE;
            int parent2 = MathRand() % POPULATION_SIZE;
            
            for(int j = 0; j < 3; j++)
            {
               new_population[i].weights[j] = (m_population[parent1].weights[j] + m_population[parent2].weights[j]) / 2.0;
               if(MathRand() / 32767.0 < MUTATION_RATE)
               {
                  new_population[i].weights[j] += MathRand() / 32767.0 * 0.1 - 0.05;
               }
               new_population[i].weights[j] = NormalizeDouble(MathMax(0.1, MathMin(new_population[i].weights[j], 1.0)), 2);
            }
            new_population[i].fitness = CalculateFitness(new_population[i].weights);
            new_population[i].timestamp = TimeCurrent();
         }
         ArrayCopy(m_population, new_population);
         
         m_generation_count++;
         
         double avg_fitness = 0.0;
         for(int i = 0; i < POPULATION_SIZE; i++) avg_fitness += m_population[i].fitness;
         avg_fitness /= POPULATION_SIZE;
         
         double prev_best = gen == 0 ? 0.0 : m_evolution_history[ArraySize(m_evolution_history)-1].best_fitness;
         double improvement = prev_best > 0 ? (best_fitness - prev_best) / prev_best : 0.0;
         
         QuantumGeneticResult result;
         result.timestamp = TimeCurrent();
         result.symbol = m_symbol;
         result.generation = gen + 1;
         result.best_fitness = best_fitness;
         result.average_fitness = avg_fitness;
         result.fitness_improvement = improvement;
         result.mutation_rate = MUTATION_RATE;
         result.success = true;
         result.market_entropy = CalculateMarketEntropy();
         result.best_weights_str = StringFormat("%.2f/%.2f/%.2f", 
            m_population[0].weights[0], 
            m_population[0].weights[1], 
            m_population[0].weights[2]);
         ArrayPushBack(m_evolution_history, result);
      }

      m_logger.log_info("[GENETIC] Evolução concluída: Melhor fitness=" + DoubleToString(m_population[0].fitness, 4));
      return true;
   }

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

   void updateGeneticDisplay(double fitness)
   {
      if(m_genetic_label == NULL)
         m_genetic_label = new CLabel("GeneticLabel", 0, 10, 490);

      m_genetic_label->text(StringFormat("GEN: %.2f", fitness));

      m_genetic_label->color(
         !is_valid_context() ? clrRed :
         fitness > 1.5 ? clrMagenta :
         fitness > 1.0 ? clrOrange : clrYellow
      );
   }

public:
   QuantumGeneticAlgorithm(logger_institutional &logger, 
                          QuantumFirewall &firewall, 
                          AdaptiveLearning &adaptive_learning, 
                          QuantumOptimizer &optimizer, 
                          string symbol)
      : m_logger(logger), 
        m_firewall(firewall), 
        m_adaptive_learning(adaptive_learning), 
        m_optimizer(optimizer), 
        m_symbol(symbol),
        m_last_update(0),
        m_generation_count(0)
   {
      if(!m_logger.is_initialized())
      {
         Print("Erro: Logger não inicializado");
         ExpertRemove();
      }

      SAFE_EXEC(m_logger.is_initialized() && &m_firewall != NULL && &m_adaptive_learning != NULL && &m_optimizer != NULL);
      
      if(&m_firewall == NULL)
      {
         m_logger.log_error("[GENETIC] QuantumFirewall não inicializado");
         ExpertRemove();
      }
      if(&m_adaptive_learning == NULL)
      {
         m_logger.log_error("[GENETIC] AdaptiveLearning não inicializado");
         ExpertRemove();
      }
      if(&m_optimizer == NULL)
      {
         m_logger.log_error("[GENETIC] QuantumOptimizer não inicializado");
         ExpertRemove();
      }
      if(StringLen(m_symbol) == 0 || !SymbolInfoInteger(m_symbol, SYMBOL_SELECT))
      {
         m_logger.log_error("[GENETIC] Símbolo inválido: " + m_symbol);
         ExpertRemove();
      }
      if(StringFind(TerminalInfoString(TERMINAL_DATA_PATH), "\\Tester") >= 0)
      {
         m_logger.log_error("[GENETIC] Execução em modo Tester não permitida");
         ExpertRemove();
      }
      
      ArrayResize(m_population, POPULATION_SIZE);
      m_logger.log_info("[GENETIC] QuantumGeneticAlgorithm inicializado para " + m_symbol);
   }

   bool Evolve()
   {
      if(!is_valid_context())
      {
         m_logger.log_warning("[GENETIC] Contexto inválido. Evolução bloqueada.");
         return false;
      }

      if(TimeCurrent() < m_last_update + GENERATIONS * 60) return true;
      
      bool success = EvolvePopulation();
      m_last_update = TimeCurrent();
      
      if(success && ArraySize(m_population) > 0) {
         updateGeneticDisplay(m_population[0].fitness);
      }
      
      return success;
   }

   GeneticIndividual GetBestIndividual()
   {
      if(ArraySize(m_population) == 0) {
         Evolve();
      }
      
      int best_index = 0;
      double best_fitness = m_population[0].fitness;
      for(int i = 1; i < ArraySize(m_population); i++)
      {
         if(m_population[i].fitness > best_fitness)
         {
            best_fitness = m_population[i].fitness;
            best_index = i;
         }
      }
      return m_population[best_index];
   }

   double GetBestFitness()
   {
      GeneticIndividual best = GetBestIndividual();
      return best.fitness;
   }

   bool IsInitialized() const
   {
      return m_logger.is_initialized() && 
             m_firewall.is_firewall_active() && 
             m_adaptive_learning.IsReady();
   }

   bool ExportEvolutionHistory(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE|FILE_TXT);
      if(handle == INVALID_HANDLE) return false;

      for(int i = 0; i < ArraySize(m_evolution_history); i++)
      {
         FileWrite(handle,
            TimeToString(m_evolution_history[i].timestamp, TIME_DATE|TIME_SECONDS),
            m_evolution_history[i].symbol,
            IntegerToString(m_evolution_history[i].generation),
            DoubleToString(m_evolution_history[i].best_fitness, 4),
            DoubleToString(m_evolution_history[i].average_fitness, 4),
            DoubleToString(m_evolution_history[i].fitness_improvement, 4),
            DoubleToString(m_evolution_history[i].mutation_rate, 4),
            m_evolution_history[i].success ? "SIM" : "NÃO",
            DoubleToString(m_evolution_history[i].market_entropy, 4),
            m_evolution_history[i].best_weights_str
         );
      }

      FileClose(handle);
      m_logger.log_info("[GENETIC] Histórico de evolução exportado para: " + file_path);
      return true;
   }

   ~QuantumGeneticAlgorithm()
   {
      m_logger.log_info("[GENETIC] QuantumGeneticAlgorithm encerrado para " + m_symbol);
   }
};

#endif // __QUANTUM_GENETIC_ALGORITHM_MQH__


