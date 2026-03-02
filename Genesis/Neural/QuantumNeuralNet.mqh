//+------------------------------------------------------------------+
//| QuantumNeuralNet.mqh - Rede Neural Completa                     |
//| Projeto: Genesis                                                |
//| Pasta: Include/Neural/                                          |
//| Versão: v6.1                                                    |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_NEURAL_NET_MQH__
#define __QUANTUM_NEURAL_NET_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
class logger_institutional;
#include <Genesis/Utils/ArrayHybrid.mqh>

// Forward declarations para evitar dependências pesadas neste header
class QuantumBlockchain;
class QuantumLearning;
class CDependencyGraph;

enum GEN_ACTIVATION_FUNCTION { ACTIVATION_SIGMOID, ACTIVATION_TANH, ACTIVATION_RELU, ACTIVATION_LINEAR };

struct NeuralLayer
{
   double inputs[];
   double outputs[];
   double weights[]; // matriz linearizada: index = i*output_count + j
   double biases[];
   double errors[];
   GEN_ACTIVATION_FUNCTION activation;
};

struct TrainingResult
{
   bool success;
   int epoch;
   double loss;
   double accuracy;
   datetime start_time;
   datetime end_time;
   string details;
};

class CNeuroNet
{
private:
   logger_institutional *m_logger;
   QuantumBlockchain    *m_blockchain;
   QuantumLearning      *m_learning;
   CDependencyGraph     *m_dependency_graph;
   string                m_symbol;
   NeuralLayer           m_layers[];
   int                   m_input_size;
   int                   m_output_size;
   int                   m_hidden_layers;
   double                m_learning_rate;
   double                m_momentum;
   int                   m_max_epochs;
   double                m_target_loss;
   TrainingResult        m_training_history[];

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { if(m_logger) m_logger->log_error("[NEURAL] Sem conexão com o servidor"); return false; }
      if(m_logger && !m_logger->is_initialized()) { m_logger->log_error("[NEURAL] Logger não inicializado"); return false; }
      return true;
   }

   double activate(double x, GEN_ACTIVATION_FUNCTION func)
   { switch(func){ case ACTIVATION_SIGMOID: return 1.0 / (1.0 + MathExp(-x)); case ACTIVATION_TANH: return MathTanh(x); case ACTIVATION_RELU: return MathMax(0.0, x); case ACTIVATION_LINEAR: return x; default: return x; } }

   double activation_derivative(double output, GEN_ACTIVATION_FUNCTION func)
   { switch(func){ case ACTIVATION_SIGMOID: return output * (1.0 - output); case ACTIVATION_TANH: return 1.0 - MathPow(output, 2); case ACTIVATION_RELU: return output > 0 ? 1.0 : 0.0; case ACTIVATION_LINEAR: return 1.0; default: return 1.0; } }

   void initialize_weights(NeuralLayer &layer, int next_outputs)
   {
      int inputs = ArraySize(layer.outputs); // tamanho de saída da camada atual = entradas para pesos
      int outputs = next_outputs;
      ArrayResize(layer.weights, inputs * outputs);
      for(int i = 0; i < inputs; i++)
      {
         for(int j = 0; j < outputs; j++)
         {
            int idx = i * outputs + j;
            layer.weights[idx] = MathRand() / 32767.0 * 2.0 - 1.0;
         }
      }
   }

   bool feed_forward(double &inputs[])
   {
      if(ArraySize(inputs) != m_input_size) return false;
      ArrayCopy(m_layers[0].outputs, inputs);
      for(int l = 0; l < m_hidden_layers + 1; l++)
      {
         NeuralLayer &layer = m_layers[l];
         NeuralLayer &next_layer = m_layers[l + 1];
         int next_count = ArraySize(next_layer.outputs);
         int curr_count = ArraySize(layer.outputs);
         for(int j = 0; j < next_count; j++)
         {
            double sum = next_layer.biases[j];
            for(int i = 0; i < curr_count; i++)
            {
               int idx = i * next_count + j;
               sum += layer.outputs[i] * layer.weights[idx];
            }
            next_layer.inputs[j] = sum;
            next_layer.outputs[j] = activate(sum, next_layer.activation);
         }
      }
      return true;
   }

   bool backpropagate(double &targets[])
   {
      int output_size = ArraySize(m_layers[m_hidden_layers + 1].outputs);
      if(ArraySize(targets) != output_size) return false;
      NeuralLayer &output_layer = m_layers[m_hidden_layers + 1];
      for(int i = 0; i < output_size; i++)
      {
         double error = targets[i] - output_layer.outputs[i];
         output_layer.errors[i] = error * activation_derivative(output_layer.outputs[i], output_layer.activation);
      }
      for(int l = m_hidden_layers; l >= 0; l--)
      {
         NeuralLayer &layer = m_layers[l];
         NeuralLayer &next_layer = m_layers[l + 1];
         int next_count = ArraySize(next_layer.outputs);
         int curr_count = ArraySize(layer.outputs);
         for(int i = 0; i < curr_count; i++)
         {
            double error = 0.0;
            for(int j = 0; j < next_count; j++)
            {
               int idx = i * next_count + j;
               error += next_layer.errors[j] * layer.weights[idx];
            }
            layer.errors[i] = error * activation_derivative(layer.outputs[i], layer.activation);
         }
      }
      for(int l = 0; l <= m_hidden_layers; l++)
      {
         NeuralLayer &layer = m_layers[l];
         NeuralLayer &next_layer = m_layers[l + 1];
         int next_count = ArraySize(next_layer.outputs);
         int curr_count = ArraySize(layer.outputs);
         for(int i = 0; i < curr_count; i++)
         {
            for(int j = 0; j < next_count; j++)
            {
               int idx = i * next_count + j;
               double delta = m_learning_rate * next_layer.errors[j] * layer.outputs[i];
               layer.weights[idx] += delta;
            }
         }
         for(int j = 0; j < next_count; j++)
         {
            next_layer.biases[j] += m_learning_rate * next_layer.errors[j];
         }
      }
      return true;
   }

   double calculate_loss(double &outputs[], double &targets[])
   { double loss = 0.0; int size = ArraySize(outputs); for(int i = 0; i < size; i++){ double error = targets[i] - outputs[i]; loss += error * error; } return loss / size; }

public:
   // Construtor compacto (sem dependências externas obrigatórias)
   CNeuroNet(int input_size,
             int hidden_layers,
             int neurons_per_layer,
             int output_size,
             double learning_rate = 0.1,
             double momentum = 0.9,
             int max_epochs = 1000,
             double target_loss = 0.001,
             logger_institutional *logger = NULL,
             string symbol = "")
      : m_logger(logger), m_blockchain(NULL), m_learning(NULL), m_dependency_graph(NULL), m_symbol(symbol),
        m_input_size(input_size), m_output_size(output_size), m_hidden_layers(hidden_layers), m_learning_rate(learning_rate),
        m_momentum(momentum), m_max_epochs(max_epochs), m_target_loss(target_loss)
   {
      if(m_logger) m_logger->log_info("[NEURAL] Inicializando NeuroNet");
      m_learning_rate = MathMax(0.001, MathMin(1.0, learning_rate));
      m_momentum = MathMax(0.0, MathMin(1.0, momentum));

      ArrayResize(m_layers, hidden_layers + 2);
      // Camada de entrada
      ArrayResize(m_layers[0].outputs, input_size);
      m_layers[0].activation = ACTIVATION_LINEAR;
      // Camadas ocultas
      for(int l = 1; l <= hidden_layers; l++)
      {
         ArrayResize(m_layers[l].outputs, neurons_per_layer);
         ArrayResize(m_layers[l].biases, neurons_per_layer);
         ArrayResize(m_layers[l].errors, neurons_per_layer);
         m_layers[l].activation = ACTIVATION_RELU;
      }
      // Camada de saída
      ArrayResize(m_layers[hidden_layers + 1].outputs, output_size);
      ArrayResize(m_layers[hidden_layers + 1].biases, output_size);
      ArrayResize(m_layers[hidden_layers + 1].errors, output_size);
      m_layers[hidden_layers + 1].activation = ACTIVATION_SIGMOID;

      // Inicializar pesos entre camadas l -> l+1
      for(int l = 0; l < hidden_layers + 1; l++)
      {
         initialize_weights(m_layers[l], ArraySize(m_layers[l + 1].outputs));
      }

      if(m_logger) m_logger->log_info("[NEURAL] Rede Neural v6.1 inicializada com sucesso");
   }

   // Construtor auxiliar sem logger (usa _Symbol internamente)
   CNeuroNet(int input_size,
             int hidden_layers,
             int neurons_per_layer,
             int output_size)
      : m_logger(NULL), m_blockchain(NULL), m_learning(NULL), m_dependency_graph(NULL), m_symbol(_Symbol),
        m_input_size(input_size), m_output_size(output_size), m_hidden_layers(hidden_layers), m_learning_rate(0.1),
        m_momentum(0.9), m_max_epochs(1000), m_target_loss(0.001)
   {
      ArrayResize(m_layers, hidden_layers + 2);
      ArrayResize(m_layers[0].outputs, input_size);
      m_layers[0].activation = ACTIVATION_LINEAR;
      for(int l = 1; l <= hidden_layers; l++)
      { ArrayResize(m_layers[l].outputs, neurons_per_layer); ArrayResize(m_layers[l].biases, neurons_per_layer); ArrayResize(m_layers[l].errors, neurons_per_layer); m_layers[l].activation = ACTIVATION_RELU; }
      ArrayResize(m_layers[hidden_layers + 1].outputs, output_size); ArrayResize(m_layers[hidden_layers + 1].biases, output_size); ArrayResize(m_layers[hidden_layers + 1].errors, output_size); m_layers[hidden_layers + 1].activation = ACTIVATION_SIGMOID;
      for(int l = 0; l < hidden_layers + 1; l++) { initialize_weights(m_layers[l], ArraySize(m_layers[l + 1].outputs)); }
   }

   bool Process(double &inputs[], double &outputs[])
   {
      if(!is_valid_context()) return false;
      if(!feed_forward(inputs)) return false;
      ArrayCopy(outputs, m_layers[m_hidden_layers + 1].outputs);
      return true;
   }

   bool Train(double &inputs[][], double &targets[][], int num_samples)
   {
      if(!is_valid_context()) return false; double start_time = TimeCurrent();
      for(int epoch = 0; epoch < m_max_epochs; epoch++)
      {
         double total_loss = 0.0;
         for(int s = 0; s < num_samples; s++)
         {
            if(!feed_forward(inputs[s])) continue;
            if(!backpropagate(targets[s])) continue;
            double loss = calculate_loss(m_layers[m_hidden_layers + 1].outputs, targets[s]);
            total_loss += loss;
         }
         double avg_loss = total_loss / num_samples;
         if(avg_loss < m_target_loss)
         {
            TrainingResult result; result.success = true; result.epoch = epoch; result.loss = avg_loss; result.accuracy = 1.0 - avg_loss; result.start_time = (datetime)start_time; result.end_time = TimeCurrent(); result.details = StringFormat("Treinamento concluído em %d épocas", epoch + 1); int __r = ArraySize(m_training_history); ArrayResize(m_training_history, __r+1); m_training_history[__r] = result; if(m_logger) m_logger->log_info("[NEURAL] Treinamento concluído com sucesso | Perda: " + DoubleToString(avg_loss, 6)); return true;
         }
      }
      TrainingResult result; result.success = false; result.epoch = m_max_epochs; result.loss = -1; result.accuracy = 0; result.start_time = (datetime)start_time; result.end_time = TimeCurrent(); result.details = "Treinamento falhou: número máximo de épocas atingido"; int __f = ArraySize(m_training_history); ArrayResize(m_training_history, __f+1); m_training_history[__f] = result; if(m_logger) m_logger->log_error("[NEURAL] Treinamento falhou: número máximo de épocas atingido"); return false;
   }

   bool GetOutputs(double &outputs[]) { ArrayCopy(outputs, m_layers[m_hidden_layers + 1].outputs); return true; }
   bool IsReady() const { return (m_logger == NULL || m_logger->is_initialized()) && ArraySize(m_layers) > 0; }
};

// Compatibilidade: Wrapper para APIs antigas esperadas por outros módulos
class QuantumNeuralNet
{
private:
   CNeuroNet m_core;
public:
   QuantumNeuralNet(int input_size=8, int hidden_layers=2, int neurons_per_layer=8, int output_size=4)
      : m_core(input_size, hidden_layers, neurons_per_layer, output_size) {}

   bool IsQuantumReady() const { return m_core.IsReady(); }

   // Mapeia para saídas atuais da rede
   bool GetQuantumState(double &state_out[])
   {
      ArrayResize(state_out, 0);
      double tmp[];
      if(!m_core.GetOutputs(tmp)) return false;
      ArrayResize(state_out, ArraySize(tmp));
      ArrayCopy(state_out, tmp);
      return true;
   }

   bool GetQuantumWeights(double &weights_out[])
   {
      // Sem pesos expostos; retorna saídas como aproximação compatível
      return GetQuantumState(weights_out);
   }

   // Compatibilidade: reusa Process
   bool Process(double &inputs[], double &outputs[])
   {
      return m_core.Process(inputs, outputs);
   }

   bool GetOutputs(double &outputs[]) { return m_core.GetOutputs(outputs); }
};

#endif // __QUANTUM_NEURAL_NET_MQH__


