//+------------------------------------------------------------------+
//| QuantumEntropyCalculator.mqh - Cálculo de Entropia Quântica      |
//| Projeto: Genesis                                                 |
//+------------------------------------------------------------------+
#ifndef __GENESIS_QUANTUM_ENTROPY_CALCULATOR_MQH__
#define __GENESIS_QUANTUM_ENTROPY_CALCULATOR_MQH__

class quantum_entropy_calculator
{
public:
   double Calculate(string symbol)
   {
      MqlRates rates[];
      int copied = CopyRates(symbol, PERIOD_M1, 0, 20, rates);
      if(copied <= 0)
         return 0.0;

      double sum = 0.0;
      for(int i = 0; i < copied; i++)
         sum += rates[i].close;
      if(sum <= 0.0)
         return 0.0;

      double entropy = 0.0;
      for(int i = 0; i < copied; i++)
      {
         double p = rates[i].close / sum;
         if(p > 0.0)
            entropy -= p * MathLog(p);
      }
      return NormalizeDouble(entropy, 4);
   }
};

#endif // __GENESIS_QUANTUM_ENTROPY_CALCULATOR_MQH__


