//+------------------------------------------------------------------+
//| PatternDetector.mqh                                              |
//+------------------------------------------------------------------+
#ifndef __PATTERN_DETECTOR_MQH__
#define __PATTERN_DETECTOR_MQH__

#include "Patterns.mqh"
#include "AgentInterface.mqh"

// Função fictícia de detecção — deve ser substituída por lógica real
bool DetectSamplePattern(PatternInfo &outPattern)
{
    if (TimeCurrent() % 300 == 0) // A cada 5 minutos
    {
        outPattern.time = TimeCurrent();
        outPattern.symbol = _Symbol;
        outPattern.tf = PERIOD_CURRENT;
        outPattern.type = TRIANGLE_ASCENDING;
        outPattern.name = "Triângulo Ascendente";
        outPattern.entryPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        outPattern.stopLoss = outPattern.entryPrice - 50 * _Point;
        outPattern.takeProfit = outPattern.entryPrice + 100 * _Point;
        return true;
    }
    return false;
}

// Função principal do scanner de padrões
void ScanPatterns()
{
    PatternInfo pattern;
    if (DetectSamplePattern(pattern))
    {
        string mensagem = StringFormat("Padrão detectado: %s em %s | Entrada: %.5f SL: %.5f TP: %.5f",
                                       pattern.name, pattern.symbol,
                                       pattern.entryPrice, pattern.stopLoss, pattern.takeProfit);
        iaAGENT_SendMessage("PADRAO", mensagem);
    }
}

#endif // __PATTERN_DETECTOR_MQH__
