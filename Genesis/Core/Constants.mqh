//+------------------------------------------------------------------+
//| Constants.mqh - Constantes Institucionais Centrais (Completo)   |
//| Projeto: Genesis                                                |
//| Pasta: Core/                                                    |
//| Versão: v2.0 (Institutional)                                    |
//| Atualizado em: 2025-08-01                                       |
//| Status: TIER-0++ Compliant | 10K+/dia Ready                     |
//+------------------------------------------------------------------+
#ifndef __GENESIS_CONSTANTS_MQH__
#define __GENESIS_CONSTANTS_MQH__

//+------------------------------------------------------------------+
//| LIMITES DE NEGOCIAÇÃO                                            |
//+------------------------------------------------------------------+
#ifndef MAX_LOT_SIZE
   #define MAX_LOT_SIZE          10.0      // Lote máximo permitido (institucional)
#endif
#ifndef MIN_LOT_SIZE
   #define MIN_LOT_SIZE          0.01      // Lote mínimo (micro-lote)
#endif
#ifndef LOT_STEP
   #define LOT_STEP              0.01      // Incremento de lote
#endif

//+------------------------------------------------------------------+
//| GESTÃO DE RISCO                                                  |
//+------------------------------------------------------------------+
#ifndef MAX_RISK_PERCENT
   #define MAX_RISK_PERCENT      2.0       // Risco máximo por operação (% do equity)
#endif
#ifndef MAX_DAILY_LOSS
   #define MAX_DAILY_LOSS        8.0       // Perda máxima diária (% do equity)
#endif
#ifndef MIN_ACCOUNT_BALANCE
   #define MIN_ACCOUNT_BALANCE   100.0     // Saldo mínimo para operar (USD)
#endif
#ifndef RISK_REWARD_RATIO
   #define RISK_REWARD_RATIO     2.0       // Razão mínima risco-retorno
#endif

//+------------------------------------------------------------------+
//| TEMPO E CICLOS                                                   |
//+------------------------------------------------------------------+
#ifndef TICKS_PER_SECOND
   #define TICKS_PER_SECOND      4         // Taxa média de ticks por segundo
#endif
#ifndef SECONDS_PER_MINUTE
   #define SECONDS_PER_MINUTE    60
#endif
#ifndef MINUTES_PER_HOUR
   #define MINUTES_PER_HOUR      60
#endif
#ifndef HOURS_PER_DAY
   #define HOURS_PER_DAY         24
#endif

//+------------------------------------------------------------------+
//| ESCALONAMENTO DIRECIONAL                                         |
//+------------------------------------------------------------------+
#ifndef MAX_SCALE_LEVELS
   #define MAX_SCALE_LEVELS      10        // Número máximo de níveis de escalonamento
#endif
#ifndef SCALE_FACTOR
   #define SCALE_FACTOR          1.6       // Fator de crescimento do lote (exponencial controlado)
#endif
#ifndef STEP_POINTS
   #define STEP_POINTS           10        // Distância entre níveis (em pontos)
#endif
#ifndef MAX_TOTAL_LOT_SIZE
   #define MAX_TOTAL_LOT_SIZE    10.0      // Limite total de exposição (soma de todos os lotes)
#endif

//+------------------------------------------------------------------+
//| TOLERÂNCIAS DE SPREAD E DEVIATION                                |
//+------------------------------------------------------------------+
#ifndef MAX_SPREAD_PIPS
   #define MAX_SPREAD_PIPS       25.0      // Spread máximo permitido (em pips)
#endif
#ifndef DEFAULT_DEVIATION
   #define DEFAULT_DEVIATION     10        // Desvio padrão para ordens (em pontos)
#endif
#ifndef SLIPPAGE_TOLERANCE
   #define SLIPPAGE_TOLERANCE    3         // Tolerância de slippage (em pontos)
#endif

//+------------------------------------------------------------------+
//| LIMITES DE VOLATILIDADE                                          |
//+------------------------------------------------------------------+
#ifndef HIGH_VOLATILITY_THRESHOLD
   #define HIGH_VOLATILITY_THRESHOLD  1.5  // Limiar de volatilidade alta (ATR em pips)
#endif
#ifndef LOW_VOLATILITY_THRESHOLD
   #define LOW_VOLATILITY_THRESHOLD   0.3  // Limiar de volatilidade baixa (ATR em pips)
#endif
#ifndef VOLATILITY_UPDATE_INTERVAL
   #define VOLATILITY_UPDATE_INTERVAL 300  // Atualização a cada 5 minutos
#endif

//+------------------------------------------------------------------+
//| NÍVEIS DE CONFIDÊNCIA (evitar conflito com enums)                |
//+------------------------------------------------------------------+
#ifndef CONFIDENCE_LOW
   #define CONFIDENCE_LOW        1
#endif
#ifndef CONFIDENCE_MEDIUM
   #define CONFIDENCE_MEDIUM     2
#endif
#ifndef CONFIDENCE_HIGH
   #define CONFIDENCE_HIGH       3
#endif
#ifndef CONFIDENCE_CRITICAL
   #define CONFIDENCE_CRITICAL   4
#endif

//+------------------------------------------------------------------+
//| CÓDIGOS DE RETORNO                                               |
//+------------------------------------------------------------------+
#ifndef SUCCESS
   #define SUCCESS               0
#endif
#ifndef ERROR
   #define ERROR                 -1
#endif
#ifndef WARNING
   #define WARNING               1
#endif
#ifndef INIT_FAILED
   #define INIT_FAILED           -2
#endif
#ifndef TRADE_REJECTED
   #define TRADE_REJECTED        -3
#endif

//+------------------------------------------------------------------+
//| NÍVEIS DE LOG                                                    |
//+------------------------------------------------------------------+
#ifndef LOG_LEVEL_DEBUG
   #define LOG_LEVEL_DEBUG       0
#endif
#ifndef LOG_LEVEL_INFO
   #define LOG_LEVEL_INFO        1
#endif
#ifndef LOG_LEVEL_WARNING
   #define LOG_LEVEL_WARNING     2
#endif
#ifndef LOG_LEVEL_ERROR
   #define LOG_LEVEL_ERROR       3
#endif
#ifndef LOG_LEVEL_CRITICAL
   #define LOG_LEVEL_CRITICAL    4
#endif

//+------------------------------------------------------------------+
//| ESTADOS DO SISTEMA                                               |
//+------------------------------------------------------------------+
#ifndef SYSTEM_STATUS_OFFLINE
   #define SYSTEM_STATUS_OFFLINE     0
#endif
#ifndef SYSTEM_STATUS_INITIALIZING
   #define SYSTEM_STATUS_INITIALIZING 1
#endif
#ifndef SYSTEM_STATUS_OPERATIONAL
   #define SYSTEM_STATUS_OPERATIONAL 2
#endif
#ifndef SYSTEM_STATUS_WARNING
   #define SYSTEM_STATUS_WARNING     3
#endif
#ifndef SYSTEM_STATUS_CRITICAL
   #define SYSTEM_STATUS_CRITICAL    4
#endif

//+------------------------------------------------------------------+
//| TIPOS DE EVENTOS QUÂNTICOS (evitar conflito com enums)           |
//+------------------------------------------------------------------+
#ifndef QUANTUM_EVENT_NONE
   #define QUANTUM_EVENT_NONE        0
#endif
#ifndef QUANTUM_EVENT_ENTANGLEMENT
   #define QUANTUM_EVENT_ENTANGLEMENT 1
#endif
#ifndef QUANTUM_EVENT_COLLAPSE
   #define QUANTUM_EVENT_COLLAPSE     2
#endif
#ifndef QUANTUM_EVENT_TUNNELING
   #define QUANTUM_EVENT_TUNNELING    3
#endif
#ifndef QUANTUM_EVENT_SUPERPOSITION
   #define QUANTUM_EVENT_SUPERPOSITION 4
#endif

//+------------------------------------------------------------------+
//| MENSAGENS DE SISTEMA                                             |
//+------------------------------------------------------------------+
#ifndef MSG_SYSTEM_READY
   #define MSG_SYSTEM_READY          "Sistema Genesis pronto para operação"
#endif
#ifndef MSG_RISK_LIMIT_REACHED
   #define MSG_RISK_LIMIT_REACHED    "Limite de risco atingido - Operações suspensas"
#endif
#ifndef MSG_HIGH_VOLATILITY
   #define MSG_HIGH_VOLATILITY       "Alta volatilidade detectada - Modo de segurança ativado"
#endif
#ifndef MSG_LOW_LIQUIDITY
   #define MSG_LOW_LIQUIDITY         "Baixa liquidez detectada - Execução de ordens suspensa"
#endif
#ifndef MSG_SCALING_ACTIVATED
   #define MSG_SCALING_ACTIVATED     "ESCALONAMENTO DINÂMICO ATIVADO | Modo: SURFING TENDÊNCIA"
#endif
#ifndef MSG_SCALING_PARTIAL_CLOSE
   #define MSG_SCALING_PARTIAL_CLOSE "Fechar parcial: %.2f lotes | Realizado"
#endif
#ifndef MSG_SCALING_ALL_CLOSED
   #define MSG_SCALING_ALL_CLOSED    "Todas as posições da escala fechadas"
#endif

//+------------------------------------------------------------------+
//| ESTRATÉGIAS DE ESCALONAMENTO                                     |
//+------------------------------------------------------------------+
#ifndef SCALING_STRATEGY_EXPONENTIAL
   #define SCALING_STRATEGY_EXPONENTIAL  1  // Crescimento exponencial (1.6^n)
#endif
#ifndef SCALING_STRATEGY_LINEAR
   #define SCALING_STRATEGY_LINEAR       2  // Crescimento linear
#endif
#ifndef SCALING_STRATEGY_LOGARITHMIC
   #define SCALING_STRATEGY_LOGARITHMIC  3  // Crescimento logarítmico
#endif

//+------------------------------------------------------------------+
//| TIPOS DE FECHAMENTO PARCIAL                                      |
//+------------------------------------------------------------------+
#ifndef PARTIAL_CLOSE_25_PERCENT
   #define PARTIAL_CLOSE_25_PERCENT    0.25
#endif
#ifndef PARTIAL_CLOSE_50_PERCENT
   #define PARTIAL_CLOSE_50_PERCENT    0.50
#endif
#ifndef PARTIAL_CLOSE_75_PERCENT
   #define PARTIAL_CLOSE_75_PERCENT    0.75
#endif
#ifndef PARTIAL_CLOSE_100_PERCENT
   #define PARTIAL_CLOSE_100_PERCENT   1.00
#endif

//+------------------------------------------------------------------+
//| INTERVALOS DE ATUALIZAÇÃO                                        |
//+------------------------------------------------------------------+
#ifndef UPDATE_INTERVAL_1MIN
   #define UPDATE_INTERVAL_1MIN        60
#endif
#ifndef UPDATE_INTERVAL_5MIN
   #define UPDATE_INTERVAL_5MIN        300
#endif
#ifndef UPDATE_INTERVAL_15MIN
   #define UPDATE_INTERVAL_15MIN       900
#endif
#ifndef UPDATE_INTERVAL_1HOUR
   #define UPDATE_INTERVAL_1HOUR       3600
#endif

//+------------------------------------------------------------------+
//| NÍVEIS DE MERCADO                                                |
//+------------------------------------------------------------------+
#ifndef MARKET_REGIME_NEUTRAL
   #define MARKET_REGIME_NEUTRAL       0
#endif
#ifndef MARKET_REGIME_RANGING
   #define MARKET_REGIME_RANGING       1
#endif
#ifndef MARKET_REGIME_STRONG_TREND
   #define MARKET_REGIME_STRONG_TREND  2
#endif
#ifndef MARKET_REGIME_REVERSAL
   #define MARKET_REGIME_REVERSAL      3
#endif

//+------------------------------------------------------------------+
//| TIPOS DE SINAL QUÂNTICO                                          |
//+------------------------------------------------------------------+
#ifndef SIGNAL_QUANTUM_NEUTRAL
   #define SIGNAL_QUANTUM_NEUTRAL      0
#endif
#ifndef SIGNAL_QUANTUM_FLASH_BUY
   #define SIGNAL_QUANTUM_FLASH_BUY    1
#endif
#ifndef SIGNAL_QUANTUM_FLASH_SELL
   #define SIGNAL_QUANTUM_FLASH_SELL   -1
#endif
#ifndef SIGNAL_QUANTUM_HOLD
   #define SIGNAL_QUANTUM_HOLD         2
#endif
#ifndef SIGNAL_QUANTUM_CRISIS
   #define SIGNAL_QUANTUM_CRISIS       3
#endif
#ifndef SIGNAL_QUANTUM_HFT_SPIKE
   #define SIGNAL_QUANTUM_HFT_SPIKE    4
#endif

//+------------------------------------------------------------------+
//| MÉTODOS DE CÁLCULO DE VaR                                        |
//+------------------------------------------------------------------+
#ifndef VAR_METHOD_HISTORICAL
   #define VAR_METHOD_HISTORICAL       1
#endif
#ifndef VAR_METHOD_PARAMETRIC
   #define VAR_METHOD_PARAMETRIC       2
#endif
#ifndef VAR_METHOD_MONTE_CARLO
   #define VAR_METHOD_MONTE_CARLO      3
#endif
#ifndef VAR_METHOD_GARCH
   #define VAR_METHOD_GARCH            4
#endif

//+------------------------------------------------------------------+
//| PERFIS DE RISCO                                                  |
//+------------------------------------------------------------------+
#ifndef RISK_PROFILE_CONSERVATIVE
   #define RISK_PROFILE_CONSERVATIVE   1
#endif
#ifndef RISK_PROFILE_MODERATE
   #define RISK_PROFILE_MODERATE       2
#endif
#ifndef RISK_PROFILE_AGGRESSIVE
   #define RISK_PROFILE_AGGRESSIVE     3
#endif
#ifndef RISK_PROFILE_CRISIS
   #define RISK_PROFILE_CRISIS         4
#endif
#ifndef RISK_PROFILE_HFT
   #define RISK_PROFILE_HFT            5
#endif

//+------------------------------------------------------------------+
//| MODOS DE FORÇA                                                   |
//+------------------------------------------------------------------+
#ifndef FORCE_MODE_STANDARD_ID
   #define FORCE_MODE_STANDARD_ID         0
#endif
#ifndef FORCE_MODE_ENHANCED_ID
   #define FORCE_MODE_ENHANCED_ID         1
#endif
#ifndef FORCE_MODE_GODMODE_ID
   #define FORCE_MODE_GODMODE_ID          2
#endif
#ifndef FORCE_MODE_TRANSCENDENT_ID
   #define FORCE_MODE_TRANSCENDENT_ID     3
#endif

//+------------------------------------------------------------------+
//| TIPOS DE OPERAÇÃO                                                |
//+------------------------------------------------------------------+
#ifndef OPERATION_PROCESS_SIGNAL
   #define OPERATION_PROCESS_SIGNAL    "PROCESS_SIGNAL"
#endif
#ifndef OPERATION_UPDATE_RISK
   #define OPERATION_UPDATE_RISK       "UPDATE_RISK_PROFILE"
#endif
#ifndef OPERATION_VALIDATE_BLOCKCHAIN
   #define OPERATION_VALIDATE_BLOCKCHAIN "VALIDATE_BLOCKCHAIN"
#endif
#ifndef OPERATION_CLOSE_ALL
   #define OPERATION_CLOSE_ALL         "CLOSE_ALL_ORDERS"
#endif
#ifndef OPERATION_OPEN_LEVEL
   #define OPERATION_OPEN_LEVEL        "OPEN_SCALING_LEVEL"
#endif

//+------------------------------------------------------------------+
//| MÓDULOS DO SISTEMA                                               |
//+------------------------------------------------------------------+
#ifndef MODULE_LOGGER
   #define MODULE_LOGGER               "LOGGER"
#endif
#ifndef MODULE_RISK
   #define MODULE_RISK                 "RISK"
#endif
#ifndef MODULE_EXECUTOR
   #define MODULE_EXECUTOR             "EXECUTOR"
#endif
#ifndef MODULE_CORE
   #define MODULE_CORE                 "CORE"
#endif
#ifndef MODULE_QUANTUM
   #define MODULE_QUANTUM              "QUANTUM"
#endif
#ifndef MODULE_AI
   #define MODULE_AI                   "AI"
#endif
#ifndef MODULE_BLOCKCHAIN
   #define MODULE_BLOCKCHAIN           "BLOCKCHAIN"
#endif

#endif // __GENESIS_CONSTANTS_MQH__


