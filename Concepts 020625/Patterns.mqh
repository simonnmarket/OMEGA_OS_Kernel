//+------------------------------------------------------------------+
//| Patterns.mqh - Definição de padrões gráficos                     |
//+------------------------------------------------------------------+
#ifndef __PATTERNS_MQH__
#define __PATTERNS_MQH__

// Enumeração dos tipos de padrões
enum PatternType
{
    NONE = 0,
    TRIANGLE_ASCENDING,
    TRIANGLE_DESCENDING,
    HEAD_AND_SHOULDERS,
    DOUBLE_TOP,
    DOUBLE_BOTTOM,
    FLAG_BULLISH,
    FLAG_BEARISH,
    PENNANT,
    CUP_WITH_HANDLE,
    WEDGE_RISING,
    WEDGE_FALLING
};

// Estrutura de um padrão detectado
struct PatternInfo
{
    datetime time;           // Momento da detecção
    string   symbol;         // Símbolo
    ENUM_TIMEFRAMES tf;      // Timeframe
    PatternType type;        // Tipo de padrão
    string   name;           // Nome do padrão
    double   entryPrice;     // Preço de entrada sugerido
    double   stopLoss;       // SL sugerido
    double   takeProfit;     // TP sugerido
};

#endif // __PATTERNS_MQH__
