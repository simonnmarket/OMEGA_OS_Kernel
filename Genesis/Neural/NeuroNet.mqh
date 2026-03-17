//+------------------------------------------------------------------+
//| NeuroNet.mqh - Sistema Neural Avançado                           |
//| Projeto: Genesis                                                |
//| Versão: v1.0                                                     |
//+------------------------------------------------------------------+
#ifndef __NEURONET_MQH__
#define __NEURONET_MQH__

enum ENUM_NEURAL_LAYER_TYPE { NEURAL_LAYER_INPUT, NEURAL_LAYER_HIDDEN, NEURAL_LAYER_OUTPUT };
// Renamed to avoid conflict with built-in ENUM_ACTIVATION_FUNCTION
enum NEURO_ACTIVATION_FUNCTION { ACTIVATION_SIGMOID, ACTIVATION_TANH, ACTIVATION_RELU, ACTIVATION_LINEAR };

struct NeuralNode { double weights[]; double bias; double output; double delta; NEURO_ACTIVATION_FUNCTION activation; };
struct NeuralLayer { NeuralNode nodes[]; ENUM_NEURAL_LAYER_TYPE type; int input_size; int output_size; };

class CNeuroNet
{
private:
   NeuralLayer layers[]; int layer_count; double learning_rate; bool trained;
public:
   CNeuroNet(){ layer_count = 0; learning_rate = 0.1; trained = false; }
   ~CNeuroNet(){ ArrayFree(layers); }
   bool AddLayer(int node_count, ENUM_NEURAL_LAYER_TYPE type, NEURO_ACTIVATION_FUNCTION activation = ACTIVATION_SIGMOID)
   { if(node_count <= 0) return false; layer_count++; ArrayResize(layers, layer_count); int layer_index = layer_count - 1; layers[layer_index].type = type; layers[layer_index].output_size = node_count; layers[layer_index].input_size = (layer_index == 0) ? node_count : layers[layer_index - 1].output_size; ArrayResize(layers[layer_index].nodes, node_count); for(int i = 0; i < node_count; i++){ ArrayResize(layers[layer_index].nodes[i].weights, layers[layer_index].input_size); for(int j = 0; j < layers[layer_index].input_size; j++){ layers[layer_index].nodes[i].weights[j] = MathRand() / 32768.0 - 0.5; } layers[layer_index].nodes[i].bias = MathRand() / 32768.0 - 0.5; layers[layer_index].nodes[i].activation = activation; layers[layer_index].nodes[i].output = 0.0; layers[layer_index].nodes[i].delta = 0.0; } return true; }
   double Activate(double input, NEURO_ACTIVATION_FUNCTION activation)
   { switch(activation){ case ACTIVATION_SIGMOID: return 1.0 / (1.0 + MathExp(-input)); case ACTIVATION_TANH: return MathTanh(input); case ACTIVATION_RELU: return MathMax(0.0, input); case ACTIVATION_LINEAR: return input; default: return input; } }
   double ActivateDerivative(double input, NEURO_ACTIVATION_FUNCTION activation)
   { switch(activation){ case ACTIVATION_SIGMOID: return input * (1.0 - input); case ACTIVATION_TANH: return 1.0 - input * input; case ACTIVATION_RELU: return input > 0.0 ? 1.0 : 0.0; case ACTIVATION_LINEAR: return 1.0; default: return 1.0; } }
   bool Forward(double &input[], double &output[])
   { if(layer_count == 0) return false; if(ArraySize(input) != layers[0].input_size) return false; for(int i = 0; i < layers[0].output_size; i++){ layers[0].nodes[i].output = input[i]; } for(int layer = 1; layer < layer_count; layer++){ for(int node = 0; node < layers[layer].output_size; node++){ double sum = layers[layer].nodes[node].bias; for(int prev_node = 0; prev_node < layers[layer].input_size; prev_node++){ sum += layers[layer].nodes[node].weights[prev_node] * layers[layer - 1].nodes[prev_node].output; } layers[layer].nodes[node].output = Activate(sum, layers[layer].nodes[node].activation); } } int last_layer = layer_count - 1; ArrayResize(output, layers[last_layer].output_size); for(int i = 0; i < layers[last_layer].output_size; i++){ output[i] = layers[last_layer].nodes[i].output; } return true; }
   bool Backpropagate(double &input[], double &target[], double &output[])
   { if(!Forward(input, output)) return false; int last_layer = layer_count - 1; for(int i = 0; i < layers[last_layer].output_size; i++){ double error = target[i] - output[i]; layers[last_layer].nodes[i].delta = error * ActivateDerivative(output[i], layers[last_layer].nodes[i].activation); } for(int layer = last_layer - 1; layer > 0; layer--){ for(int i = 0; i < layers[layer].output_size; i++){ double error = 0.0; for(int j = 0; j < layers[layer + 1].output_size; j++){ error += layers[layer + 1].nodes[j].delta * layers[layer + 1].nodes[j].weights[i]; } layers[layer].nodes[i].delta = error * ActivateDerivative(layers[layer].nodes[i].output, layers[layer].nodes[i].activation); } } for(int layer = 1; layer < layer_count; layer++){ for(int i = 0; i < layers[layer].output_size; i++){ for(int j = 0; j < layers[layer].input_size; j++){ layers[layer].nodes[i].weights[j] += learning_rate * layers[layer].nodes[i].delta * layers[layer - 1].nodes[j].output; } layers[layer].nodes[i].bias += learning_rate * layers[layer].nodes[i].delta; } } return true; }
   bool Train(double &inputs[][], double &targets[][], int epochs = 1000)
   { int data_size = ArrayRange(inputs, 0); if(data_size == 0 || data_size != ArrayRange(targets, 0)) return false; for(int epoch = 0; epoch < epochs; epoch++){ double total_error = 0.0; for(int i = 0; i < data_size; i++){ double input[], target[], output[]; ArrayResize(input, ArrayRange(inputs, 1)); for(int j = 0; j < ArrayRange(inputs, 1); j++) input[j] = inputs[i][j]; ArrayResize(target, ArrayRange(targets, 1)); for(int j = 0; j < ArrayRange(targets, 1); j++) target[j] = targets[i][j]; if(Backpropagate(input, target, output)){ for(int j = 0; j < ArraySize(output); j++){ total_error += MathPow(target[j] - output[j], 2); } } } if(epoch % 100 == 0){ Print(StringFormat("[NEURONET] Epoch %d, Error: %.6f", epoch, total_error / data_size)); } } trained = true; return true; }
   bool Predict(double &input[], double &output[]){ return Forward(input, output); }
   void SetLearningRate(double rate){ if(rate > 0.0 && rate <= 1.0) learning_rate = rate; }
   double GetLearningRate(){ return learning_rate; }
   bool IsTrained(){ return trained; }
   int GetLayerCount(){ return layer_count; }
   string GetArchitecture(){ string arch = ""; for(int i = 0; i < layer_count; i++){ if(i > 0) arch += " -> "; arch += IntegerToString(layers[i].output_size); } return arch; }
   bool Save(string filename){ int handle = FileOpen(filename, FILE_WRITE | FILE_TXT); if(handle == INVALID_HANDLE) return false; FileWrite(handle, "NeuroNet Architecture"); FileWrite(handle, "Layer Count: " + IntegerToString(layer_count)); FileWrite(handle, "Learning Rate: " + DoubleToString(learning_rate, 6)); FileWrite(handle, "Trained: " + (trained ? "Yes" : "No")); FileClose(handle); return true; }
   bool Load(string filename){ int handle = FileOpen(filename, FILE_READ | FILE_TXT); if(handle == INVALID_HANDLE) return false; FileClose(handle); return true; }
   bool Validate(){ if(layer_count <= 0) return false; for(int i = 0; i < layer_count; i++){ if(ArraySize(layers[i].nodes) != layers[i].output_size) return false; } return true; }
};

CNeuroNet g_neuronet;
bool CreateNeuralNetwork(int input_size, int hidden_size, int output_size){ g_neuronet = CNeuroNet(); if(!g_neuronet.AddLayer(input_size, NEURAL_LAYER_INPUT, ACTIVATION_LINEAR)) return false; if(!g_neuronet.AddLayer(hidden_size, NEURAL_LAYER_HIDDEN, ACTIVATION_SIGMOID)) return false; if(!g_neuronet.AddLayer(output_size, NEURAL_LAYER_OUTPUT, ACTIVATION_SIGMOID)) return false; return g_neuronet.Validate(); }
bool TrainNeuralNetwork(double &inputs[][], double &targets[][], int epochs = 1000){ return g_neuronet.Train(inputs, targets, epochs); }
bool PredictNeuralNetwork(double &input[], double &output[]){ return g_neuronet.Predict(input, output); }
bool ValidateNeuroNet(){ if(!g_neuronet.Validate()){ Print("[NEURONET] Erro: Validação falhou"); return false; } Print("[NEURONET] Validação passou. Arquitetura: " + g_neuronet.GetArchitecture()); return true; }

#endif // __NEURONET_MQH__


