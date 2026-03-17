#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

#include "CategoryManager.mqh"
#include "VolumeFootprintPerformance.mqh"

// Estruturas para Volume Footprint
struct FootprintData {
    // Dados de Mercado
    struct Market {
        double open;
        double high;
        double low;
        double close;
        double volume;
        double volumeMA;
        double volumeDelta;
        double trend;
        double momentum;
        double volatility;
        double valueAreaHigh;
        double valueAreaLow;
        double poc;
        ENUM_MARKET_CONDITION condition;
        bool isValid;
        datetime lastUpdate;
        
        void Reset() {
            open = 0.0;
            high = 0.0;
            low = 0.0;
            close = 0.0;
            volume = 0.0;
            volumeMA = 0.0;
            volumeDelta = 0.0;
            trend = 0.0;
            momentum = 0.0;
            volatility = 0.0;
            valueAreaHigh = 0.0;
            valueAreaLow = 0.0;
            poc = 0.0;
            condition = MARKET_CONDITION_NEUTRAL;
            isValid = false;
            lastUpdate = 0;
        }
    } market;
    
    // Setup de Trade
    struct Setup {
        ENUM_TRADE_SIGNAL signal;
        double entry;
        double stopLoss;
        double takeProfit;
        double volume;
        double risk;
        double reward;
        double confidence;
        string reason;
        bool isValid;
        
        void Reset() {
            signal = TRADE_SIGNAL_NONE;
            entry = 0.0;
            stopLoss = 0.0;
            takeProfit = 0.0;
            volume = 0.0;
            risk = 0.0;
            reward = 0.0;
            confidence = 0.0;
            reason = "";
            isValid = false;
        }
    } setup;
    
    void Reset() {
        market.Reset();
        setup.Reset();
    }
};

struct FootprintMetrics {
    double valueAreaHigh;
    double valueAreaLow;
    double pointOfControl;
    double initialBalance;
    double balanceStatus;
    double deltaStrength;
    double volumeProfile;
    bool isValid;
    
    void Reset() {
        valueAreaHigh = 0.0;
        valueAreaLow = 0.0;
        pointOfControl = 0.0;
        initialBalance = 0.0;
        balanceStatus = 0.0;
        deltaStrength = 0.0;
        volumeProfile = 0.0;
        isValid = false;
    }
};

struct FootprintSignal {
    string type;
    double strength;
    double confidence;
    datetime time;
    string description;
    bool isValid;
    
    void Reset() {
        type = "";
        strength = 0.0;
        confidence = 0.0;
        time = 0;
        description = "";
        isValid = false;
    }
};

// Classe para cálculo de Delta
class CDeltaCalculator {
private:
    double[] m_priceNodes;
    double[] m_volumeNodes;
    double[] m_buyVolume;
    double[] m_sellVolume;
    double m_deltaThreshold;
    
public:
    CDeltaCalculator() {
        m_deltaThreshold = 0.7;
        ArrayResize(m_priceNodes, 0);
        ArrayResize(m_volumeNodes, 0);
        ArrayResize(m_buyVolume, 0);
        ArrayResize(m_sellVolume, 0);
    }
    
    double CalculateDelta(int index) {
        if(index < 0 || index >= ArraySize(m_volumeNodes)) return 0.0;
        
        return m_buyVolume[index] - m_sellVolume[index];
    }
    
    double CalculateCumulativeDelta(int index) {
        if(index < 0 || index >= ArraySize(m_volumeNodes)) return 0.0;
        
        double cumulativeDelta = 0.0;
        for(int i = 0; i <= index; i++) {
            cumulativeDelta += CalculateDelta(i);
        }
        
        return cumulativeDelta;
    }
    
    double CalculateDeltaStrength() {
        if(ArraySize(m_volumeNodes) == 0) return 0.0;
        
        double totalVolume = 0.0;
        double totalDelta = 0.0;
        
        for(int i = 0; i < ArraySize(m_volumeNodes); i++) {
            totalVolume += m_volumeNodes[i];
            totalDelta += MathAbs(CalculateDelta(i));
        }
        
        return totalVolume > 0 ? totalDelta / totalVolume : 0.0;
    }
    
    bool IsSignificantDelta(int index) {
        if(index < 0 || index >= ArraySize(m_volumeNodes)) return false;
        
        double delta = CalculateDelta(index);
        double volume = m_volumeNodes[index];
        
        return MathAbs(delta) > volume * m_deltaThreshold;
    }
};

// Classe para análise de Volume Profile
class CVolumeProfileAnalyzer {
private:
    double[] m_priceNodes;
    double[] m_volumeNodes;
    double[] m_buyVolume;
    double[] m_sellVolume;
    double m_valueAreaPercent;
    
public:
    CVolumeProfileAnalyzer() {
        m_valueAreaPercent = 0.7;
        ArrayResize(m_priceNodes, 0);
        ArrayResize(m_volumeNodes, 0);
        ArrayResize(m_buyVolume, 0);
        ArrayResize(m_sellVolume, 0);
    }
    
    FootprintMetrics* AnalyzeVolumeProfile() {
        FootprintMetrics* metrics = new FootprintMetrics();
        
        if(!ValidateData()) {
            return metrics;
        }
        
        CalculateValueArea(metrics);
        CalculatePointOfControl(metrics);
        CalculateInitialBalance(metrics);
        CalculateBalanceStatus(metrics);
        CalculateVolumeProfile(metrics);
        
        metrics.isValid = true;
        return metrics;
    }
    
private:
    bool ValidateData() {
        return ArraySize(m_priceNodes) > 0 && 
               ArraySize(m_volumeNodes) > 0 && 
               ArraySize(m_buyVolume) > 0 && 
               ArraySize(m_sellVolume) > 0;
    }
    
    void CalculateValueArea(FootprintMetrics* metrics) {
        double totalVolume = 0.0;
        double volumeThreshold = 0.0;
        
        for(int i = 0; i < ArraySize(m_volumeNodes); i++) {
            totalVolume += m_volumeNodes[i];
        }
        
        volumeThreshold = totalVolume * m_valueAreaPercent;
        
        double currentVolume = 0.0;
        bool foundHigh = false;
        bool foundLow = false;
        
        for(int i = 0; i < ArraySize(m_volumeNodes); i++) {
            currentVolume += m_volumeNodes[i];
            
            if(!foundHigh && currentVolume >= volumeThreshold) {
                metrics.valueAreaHigh = m_priceNodes[i];
                foundHigh = true;
            }
            
            if(foundHigh && !foundLow && currentVolume >= volumeThreshold * 2) {
                metrics.valueAreaLow = m_priceNodes[i];
                foundLow = true;
            }
        }
    }
    
    void CalculatePointOfControl(FootprintMetrics* metrics) {
        int maxVolumeIndex = 0;
        double maxVolume = m_volumeNodes[0];
        
        for(int i = 1; i < ArraySize(m_volumeNodes); i++) {
            if(m_volumeNodes[i] > maxVolume) {
                maxVolume = m_volumeNodes[i];
                maxVolumeIndex = i;
            }
        }
        
        metrics.pointOfControl = m_priceNodes[maxVolumeIndex];
    }
    
    void CalculateInitialBalance(FootprintMetrics* metrics) {
        if(ArraySize(m_priceNodes) < 30) return;
        
        double high = m_priceNodes[0];
        double low = m_priceNodes[0];
        
        for(int i = 1; i < 30; i++) {
            if(m_priceNodes[i] > high) high = m_priceNodes[i];
            if(m_priceNodes[i] < low) low = m_priceNodes[i];
        }
        
        metrics.initialBalance = high - low;
    }
    
    void CalculateBalanceStatus(FootprintMetrics* metrics) {
        if(ArraySize(m_priceNodes) < 2) return;
        
        double currentPrice = m_priceNodes[ArraySize(m_priceNodes) - 1];
        double previousPrice = m_priceNodes[ArraySize(m_priceNodes) - 2];
        
        metrics.balanceStatus = (currentPrice - previousPrice) / previousPrice;
    }
    
    void CalculateVolumeProfile(FootprintMetrics* metrics) {
        double totalVolume = 0.0;
        double totalBuyVolume = 0.0;
        double totalSellVolume = 0.0;
        
        for(int i = 0; i < ArraySize(m_volumeNodes); i++) {
            totalVolume += m_volumeNodes[i];
            totalBuyVolume += m_buyVolume[i];
            totalSellVolume += m_sellVolume[i];
        }
        
        metrics.volumeProfile = totalVolume > 0 ? 
            (totalBuyVolume - totalSellVolume) / totalVolume : 0.0;
    }
};

// Classe principal Volume Footprint
class CVolumeFootprintCategory : public CBaseCategoryAnalyzer {
private:
    FootprintData m_data;
    FootprintMetrics m_metrics;
    FootprintSignal m_signal;
    CDeltaCalculator* m_deltaCalculator;
    CVolumeProfileAnalyzer* m_profileAnalyzer;
    CDataCollector* m_dataCollector;
    CPatternAnalyzer* m_patternAnalyzer;
    CStatisticsManager* m_statisticsManager;
    CQualityAnalyzer* m_qualityAnalyzer;
    CAlertManager* m_alertManager;
    CDataManager* m_dataManager;
    CTeam* m_responsibleTeam;
    CVolumeFootprintPerformance* m_performanceMonitor;
    
    // Cache de sinais
    FootprintSignal m_signalCache[];
    int m_maxCacheSize;
    
    // Métricas de execução
    double m_executionLatency;
    double m_executionAccuracy;
    double m_costEfficiency;
    
    // Configurações
    struct Config {
        // Parâmetros de Trading
        int timeframeMin;
        double riskPercent;
        int maxDailyTrades;
        bool useBreakEven;
        int breakEvenPoints;
        
        // Parâmetros de Volume
        double volumeThreshold;
        int volumePeriod;
        int stopLoss;
        int takeProfit;
        
        // Análises Avançadas
        bool useVolumeProfile;
        bool useOrderFlow;
        bool useMarketProfile;
        bool useInstitutional;
        
        void Reset() {
            timeframeMin = 5;
            riskPercent = 1.0;
            maxDailyTrades = 3;
            useBreakEven = true;
            breakEvenPoints = 300;
            volumeThreshold = 1.5;
            volumePeriod = 20;
            stopLoss = 400;
            takeProfit = 800;
            useVolumeProfile = true;
            useOrderFlow = true;
            useMarketProfile = true;
            useInstitutional = true;
        }
    } m_config;
    
    // Handles e Buffers
    struct Handles {
        int ma;
        int rsi;
        int atr;
        
        void Reset() {
            ma = INVALID_HANDLE;
            rsi = INVALID_HANDLE;
            atr = INVALID_HANDLE;
        }
    } m_handles;
    
    struct Buffers {
        double ma[];
        double rsi[];
        double atr[];
        
        void Reset() {
            ArrayResize(ma, 0);
            ArrayResize(rsi, 0);
            ArrayResize(atr, 0);
        }
    } m_buffers;
    
    // Métricas de Performance
    struct Performance {
        int dailyTrades;
        int consecutiveLosses;
        double currentDrawdown;
        string logFile;
        
        void Reset() {
            dailyTrades = 0;
            consecutiveLosses = 0;
            currentDrawdown = 0.0;
            logFile = "";
        }
    } m_performance;
    
    // Estruturas de Diagnóstico
    struct DiagnosticMetrics {
        double cpuUsage;
        double memoryUsage;
        int errorCount;
        datetime lastCheck;
        bool isSystemHealthy;
        
        void Reset() {
            cpuUsage = 0.0;
            memoryUsage = 0.0;
            errorCount = 0;
            lastCheck = 0;
            isSystemHealthy = true;
        }
    };
    
    struct LogConfig {
        string logFile;
        bool enableDetailedLogs;
        bool enablePerformanceLogs;
        bool enableErrorLogs;
        int logRetentionDays;
        
        void Reset() {
            logFile = "";
            enableDetailedLogs = true;
            enablePerformanceLogs = true;
            enableErrorLogs = true;
            logRetentionDays = 30;
        }
    };
    
    DiagnosticMetrics m_diagnostics;
    LogConfig m_logConfig;
    
    // Estrutura para gerenciamento de indicadores
    struct IndicatorManager {
        // Handles dos indicadores
        struct Handles {
            int ma;
            int rsi;
            int atr;
            int volume;
            
            void Reset() {
                ma = INVALID_HANDLE;
                rsi = INVALID_HANDLE;
                atr = INVALID_HANDLE;
                volume = INVALID_HANDLE;
            }
        } handles;
        
        // Buffers dos indicadores
        struct Buffers {
            double ma[];
            double rsi[];
            double atr[];
            double volume[];
            
            void Reset() {
                ArrayResize(ma, 0);
                ArrayResize(rsi, 0);
                ArrayResize(atr, 0);
                ArrayResize(volume, 0);
            }
        } buffers;
        
        // Configurações
        struct Config {
            int maPeriod;
            int rsiPeriod;
            int atrPeriod;
            int volumePeriod;
            ENUM_MA_METHOD maMethod;
            ENUM_APPLIED_PRICE priceType;
            
            void Reset() {
                maPeriod = 20;
                rsiPeriod = 14;
                atrPeriod = 14;
                volumePeriod = 20;
                maMethod = MODE_EMA;
                priceType = PRICE_CLOSE;
            }
        } config;
    } m_indicators;
    
    // Estrutura para dados de mercado em tempo real
    struct RealTimeData {
        // Dados de preço
        struct Price {
            double open;
            double high;
            double low;
            double close;
            double last;
            double bid;
            double ask;
            
            void Reset() {
                open = 0.0;
                high = 0.0;
                low = 0.0;
                close = 0.0;
                last = 0.0;
                bid = 0.0;
                ask = 0.0;
            }
        } price;
        
        // Dados de volume
        struct Volume {
            double current;
            double ma;
            double delta;
            double buyVolume;
            double sellVolume;
            double imbalance;
            
            void Reset() {
                current = 0.0;
                ma = 0.0;
                delta = 0.0;
                buyVolume = 0.0;
                sellVolume = 0.0;
                imbalance = 0.0;
            }
        } volume;
        
        // Análise técnica
        struct Technical {
            double trend;
            double momentum;
            double volatility;
            double strength;
            
            void Reset() {
                trend = 0.0;
                momentum = 0.0;
                volatility = 0.0;
                strength = 0.0;
            }
        } tech;
        
        // Market Profile
        struct Profile {
            double valueAreaHigh;
            double valueAreaLow;
            double poc;
            bool isBalanced;
            
            void Reset() {
                valueAreaHigh = 0.0;
                valueAreaLow = 0.0;
                poc = 0.0;
                isBalanced = false;
            }
        } profile;
        
        datetime lastUpdate;
        bool isValid;
        
        void Reset() {
            price.Reset();
            volume.Reset();
            tech.Reset();
            profile.Reset();
            lastUpdate = 0;
            isValid = false;
        }
    } m_rtData;
    
    // Estrutura para gerenciamento de risco
    struct RiskManager {
        // Configurações de Risco
        struct Config {
            double maxRiskPercent;      // Risco máximo por operação
            double maxExposurePercent;  // Exposição máxima total
            double maxDrawdownPercent;  // Drawdown máximo permitido
            double minStopDistance;     // Distância mínima do stop
            int maxDailyTrades;         // Máximo de trades diários
            bool useAdaptivePosition;   // Usar tamanho adaptativo
            
            void Reset() {
                maxRiskPercent = 1.0;
                maxExposurePercent = 5.0;
                maxDrawdownPercent = 10.0;
                minStopDistance = 50;
                maxDailyTrades = 3;
                useAdaptivePosition = true;
            }
        } config;
        
        // Métricas de Risco
        struct Metrics {
            double currentExposure;     // Exposição atual
            double currentDrawdown;     // Drawdown atual
            double dailyPnL;           // Lucro/Prejuízo diário
            int dailyTrades;           // Trades realizados hoje
            bool isRiskExceeded;       // Risco excedido
            datetime lastUpdate;        // Última atualização
            
            void Reset() {
                currentExposure = 0.0;
                currentDrawdown = 0.0;
                dailyPnL = 0.0;
                dailyTrades = 0;
                isRiskExceeded = false;
                lastUpdate = 0;
            }
        } metrics;
        
        // Controle de Posição
        struct Position {
            double size;               // Tamanho da posição
            double entryPrice;         // Preço de entrada
            double stopLoss;           // Stop Loss
            double takeProfit;         // Take Profit
            double riskRewardRatio;    // Ratio Risco/Retorno
            bool isValid;              // Posição válida
            
            void Reset() {
                size = 0.0;
                entryPrice = 0.0;
                stopLoss = 0.0;
                takeProfit = 0.0;
                riskRewardRatio = 0.0;
                isValid = false;
            }
        } position;
        
        void Reset() {
            config.Reset();
            metrics.Reset();
            position.Reset();
        }
    } m_risk;
    
    // Estrutura para execução de trades
    struct TradeExecutor {
        // Configurações de Execução
        struct Config {
            int maxRetries;            // Tentativas máximas
            int retryDelay;            // Delay entre tentativas (ms)
            double slippage;           // Slippage máximo permitido
            bool useAsyncExecution;    // Execução assíncrona
            bool useSmartRouting;      // Roteamento inteligente
            
            void Reset() {
                maxRetries = 3;
                retryDelay = 1000;
                slippage = 0.5;
                useAsyncExecution = true;
                useSmartRouting = true;
            }
        } config;
        
        // Métricas de Execução
        struct Metrics {
            int successfulTrades;      // Trades bem sucedidos
            int failedTrades;          // Falhas de execução
            double avgExecutionTime;   // Tempo médio de execução
            double slippageTotal;      // Slippage total
            datetime lastExecution;     // Última execução
            
            void Reset() {
                successfulTrades = 0;
                failedTrades = 0;
                avgExecutionTime = 0.0;
                slippageTotal = 0.0;
                lastExecution = 0;
            }
        } metrics;
        
        // Estado da Execução
        struct State {
            bool isExecuting;          // Em execução
            int retryCount;            // Contagem de tentativas
            string lastError;          // Último erro
            bool isValid;              // Estado válido
            
            void Reset() {
                isExecuting = false;
                retryCount = 0;
                lastError = "";
                isValid = true;
            }
        } state;
        
        void Reset() {
            config.Reset();
            metrics.Reset();
            state.Reset();
        }
    } m_executor;
    
    // Estrutura para histórico de trades
    struct TradeHistory {
        string direction;
        double entryPrice;
        double volume;
        double stopLoss;
        double takeProfit;
        datetime time;
    } m_tradeHistory[];
    
    // Estrutura para gerenciamento de posições
    struct PositionManager {
        // Configurações de Gerenciamento
        struct Config {
            bool useBreakEven;         // Usar break even
            int breakEvenPoints;       // Pontos para break even
            bool useTrailingStop;      // Usar trailing stop
            int trailingPoints;        // Pontos para trailing
            bool usePartialClose;      // Usar fechamento parcial
            double partialCloseLevel;  // Nível para fechamento parcial
            
            void Reset() {
                useBreakEven = true;
                breakEvenPoints = 300;
                useTrailingStop = true;
                trailingPoints = 200;
                usePartialClose = true;
                partialCloseLevel = 0.5;
            }
        } config;
        
        // Estado da Posição
        struct State {
            bool isBreakEvenActive;    // Break even ativado
            bool isTrailingActive;     // Trailing ativo
            bool isPartialClosed;      // Parcial executado
            double maxFloatingProfit;  // Máximo lucro flutuante
            double currentDrawdown;    // Drawdown atual
            
            void Reset() {
                isBreakEvenActive = false;
                isTrailingActive = false;
                isPartialClosed = false;
                maxFloatingProfit = 0.0;
                currentDrawdown = 0.0;
            }
        } state;
        
        // Métricas de Performance
        struct Metrics {
            int totalPositions;        // Total de posições
            int breakEvenHits;         // Break evens atingidos
            int trailingStopHits;      // Trailing stops atingidos
            double avgHoldingTime;     // Tempo médio de posição
            
            void Reset() {
                totalPositions = 0;
                breakEvenHits = 0;
                trailingStopHits = 0;
                avgHoldingTime = 0.0;
            }
        } metrics;
        
        void Reset() {
            config.Reset();
            state.Reset();
            metrics.Reset();
        }
    } m_posManager;
    
    // Sistema de Conexão Externa
    struct ExternalConnector {
        // Configurações de Conexão
        struct Config {
            string apiUrl;            // URL da API
            string apiKey;            // Chave de API
            int timeout;             // Timeout de conexão
            bool useSSL;             // Usar conexão segura
            bool enableRetry;        // Habilitar retry
            int maxRetries;          // Máximo de tentativas
            
            void Reset() {
                apiUrl = "";
                apiKey = "";
                timeout = 5000;
                useSSL = true;
                enableRetry = true;
                maxRetries = 3;
            }
        } config;
        
        // Métricas de Conexão
        struct Metrics {
            int successfulRequests;   // Requisições bem sucedidas
            int failedRequests;       // Falhas de conexão
            double avgResponseTime;   // Tempo médio de resposta
            datetime lastConnection;  // Última conexão
            
            void Reset() {
                successfulRequests = 0;
                failedRequests = 0;
                avgResponseTime = 0.0;
                lastConnection = 0;
            }
        } metrics;
        
        // Cache de Dados
        struct DataCache {
            CArrayObj* pendingData;   // Dados pendentes
            int maxCacheSize;         // Tamanho máximo do cache
            bool isProcessing;        // Flag de processamento
            
            void Reset() {
                pendingData = new CArrayObj();
                maxCacheSize = 1000;
                isProcessing = false;
            }
        } cache;
    } m_connector;
    
    // Estado do Sistema
    struct SystemState {
        bool isInitialized;
        bool isMarketValid;
        bool isAnalysisReady;
        double confidence;
        datetime lastUpdate;
        
        void Reset() {
            isInitialized = false;
            isMarketValid = false;
            isAnalysisReady = false;
            confidence = 0.0;
            lastUpdate = 0;
        }
    } m_state;
    
public:
    CVolumeFootprintCategory() {
        m_deltaCalculator = new CDeltaCalculator();
        m_profileAnalyzer = new CVolumeProfileAnalyzer();
        m_dataCollector = new CDataCollector();
        m_patternAnalyzer = new CPatternAnalyzer();
        m_statisticsManager = new CStatisticsManager();
        m_qualityAnalyzer = new CQualityAnalyzer();
        m_alertManager = new CAlertManager();
        m_dataManager = new CDataManager();
        m_responsibleTeam = new CTeam();
        m_performanceMonitor = new CVolumeFootprintPerformance();
        
        m_maxCacheSize = 100;
        ArrayResize(m_signalCache, 0);
        
        m_executionLatency = 0.0;
        m_executionAccuracy = 0.0;
        m_costEfficiency = 0.0;
        
        m_config.Reset();
        m_handles.Reset();
        m_buffers.Reset();
        m_performance.Reset();
        
        m_diagnostics.Reset();
        m_logConfig.Reset();
        
        // Inicializar sistema de logs
        InitializeLogSystem();
        
        // Inicializar sistema de conexão externa
        m_connector.config.Reset();
        m_connector.metrics.Reset();
        m_connector.cache.Reset();
        
        m_state.Reset();
    }
    
    ~CVolumeFootprintCategory() {
        delete m_deltaCalculator;
        delete m_profileAnalyzer;
        delete m_dataCollector;
        delete m_patternAnalyzer;
        delete m_statisticsManager;
        delete m_qualityAnalyzer;
        delete m_alertManager;
        delete m_dataManager;
        delete m_responsibleTeam;
        delete m_performanceMonitor;
    }
    
    virtual bool Initialize() override {
        if(!super.Initialize()) return false;
        
        // Inicializar componentes
        if(!InitializeComponents()) return false;
        
        // Inicializar indicadores
        if(!InitializeIndicators()) return false;
        
        // Inicializar sistema de logs
        InitializeLogSystem();
        
        // Inicializar monitor de performance
        if(!m_performanceMonitor) return false;
        
        // Inicializar sistema de conexão externa
        if(!InitializeExternalConnector()) return false;
        
        return true;
    }
    
    void Update() override {
        if(!IsEnabled()) return;
        
        try {
            // Atualizar diagnóstico
            UpdateDiagnostics();
            
            // Validar recursos do sistema
            if(!ValidateSystemResources()) {
                LogMessage("Sistema com recursos críticos", LOG_ERROR);
                return;
            }
            
            // 1. Atualizar dados de mercado
            if(!UpdateMarketData()) return;
            
            // 2. Análise de volume
            if(!AnalyzeVolume()) return;
            
            // 3. Gerar sinais
            GenerateAndValidateSignals();
            
            // 4. Gerenciar trades
            GerenciarTrades();
            
            // 5. Atualizar cache
            UpdateSignalCache();
            
            // 6. Processar alertas
            ProcessAlerts();
            
            // 7. Atualizar métricas de execução
            UpdateExecutionMetrics();
            
            // 8. Atualizar monitor de performance
            if(m_performanceMonitor) {
                m_performanceMonitor.Update();
            }
            
        } catch(const int error) {
            HandleSystemError(error);
        }
    }
    
    void GenerateAndValidateSignals() {
        // Gerar sinais
        if(!GenerateTradeSignals()) return;
        
        // Validar sinais
        if(!ValidateSignals()) return;
        
        // Processar sinais válidos
        ProcessValidSignals();
    }
    
    void ProcessValidSignals() {
        if(!m_signal.isValid) return;
        
        // Atualizar setup
        m_data.setup.signal = m_signal.type == "BUY" ? SIGNAL_BUY : SIGNAL_SELL;
        m_data.setup.confidence = m_signal.confidence;
        m_data.setup.isValid = true;
        
        // Calcular níveis
        CalculateTradeLevels();
        
        // Notificar equipe
        NotifyTeam(StringFormat(
            "Sinal gerado: %s\nForça: %.2f\nConfiança: %.2f",
            m_signal.type,
            m_signal.strength,
            m_signal.confidence
        ));
    }
    
    void GerenciarTrades() {
        // Verificar trades existentes
        if(m_data.setup.isValid) {
            // Atualizar stop loss e take profit
            AtualizarNiveisTrade();
            
            // Verificar break even
            if(m_config.useBreakEven) {
                VerificarBreakEven();
            }
            
            // Verificar fechamento
            VerificarFechamentoTrade();
        }
    }
    
    void AtualizarNiveisTrade() {
        if(!m_data.setup.isValid) return;
        
        double atr = m_data.market.volatility;
        double novoStopLoss = m_data.setup.entry - (atr * 2);
        double novoTakeProfit = m_data.setup.entry + (atr * 4);
        
        // Atualizar apenas se melhorar o setup
        if(novoStopLoss > m_data.setup.stopLoss) {
            m_data.setup.stopLoss = novoStopLoss;
        }
        if(novoTakeProfit > m_data.setup.takeProfit) {
            m_data.setup.takeProfit = novoTakeProfit;
        }
    }
    
    void VerificarBreakEven() {
        if(!ValidarCondicoesBreakEven()) return;
        
        double precoEntrada = PositionGetDouble(POSITION_PRICE_OPEN);
        double precoAtual = ObterPrecoAtual();
        double stopLoss = PositionGetDouble(POSITION_SL);
        
        if(VerificarTriggerBreakEven(precoEntrada, precoAtual)) {
            if(AplicarBreakEven(precoEntrada)) {
                ProcessarSucessoBreakEven();
            }
        }
    }
    
    bool ValidarCondicoesBreakEven() {
        if(!m_posManager.config.useBreakEven) return false;
        if(!PositionSelect(_Symbol)) return false;
        if(m_posManager.state.isBreakEvenActive) return false;
        
        return true;
    }
    
    bool VerificarTriggerBreakEven(const double precoEntrada, const double precoAtual) {
        ENUM_POSITION_TYPE tipoPosicao = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        double distanciaBE = m_posManager.config.breakEvenPoints * _Point;
        
        if(tipoPosicao == POSITION_TYPE_BUY) {
            return (precoAtual - precoEntrada > distanciaBE);
        }
        else if(tipoPosicao == POSITION_TYPE_SELL) {
            return (precoEntrada - precoAtual > distanciaBE);
        }
        
        return false;
    }
    
    bool AplicarBreakEven(const double precoEntrada) {
        return m_trade.PositionModify(
            _Symbol,
            precoEntrada,
            PositionGetDouble(POSITION_TP)
        );
    }
    
    void ProcessarSucessoBreakEven() {
        m_posManager.state.isBreakEvenActive = true;
        m_posManager.metrics.breakEvenHits++;
        
        string mensagem = StringFormat(
            "Break Even ativado\nSímbolo: %s\nPreço: %.5f",
            _Symbol,
            PositionGetDouble(POSITION_PRICE_OPEN)
        );
        
        LogMessage(mensagem, LOG_INFO);
        NotificarEquipe(mensagem);
        
        // Atualizar TechnologyAdvances
        AtualizarMetricasPosicao();
    }
    
    void AtualizarStops() {
        if(!ValidarCondicoesAtualizacaoStop()) return;
        
        double precoAtual = ObterPrecoAtual();
        ENUM_POSITION_TYPE tipoPosicao = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        
        // Atualizar trailing stop
        if(m_posManager.config.useTrailingStop) {
            AtualizarTrailingStop(precoAtual, tipoPosicao);
        }
        
        // Verificar fechamento parcial
        if(m_posManager.config.usePartialClose) {
            VerificarFechamentoParcial(precoAtual, tipoPosicao);
        }
        
        // Atualizar métricas
        AtualizarMetricasPosicao();
    }
    
    void AtualizarTrailingStop(const double precoAtual, const ENUM_POSITION_TYPE tipoPosicao) {
        double precoEntrada = PositionGetDouble(POSITION_PRICE_OPEN);
        double distanciaTrailing = m_posManager.config.trailingPoints * _Point;
        double stopAtual = PositionGetDouble(POSITION_SL);
        
        double novoStopLoss = stopAtual;
        bool deveAtualizar = false;
        
        if(tipoPosicao == POSITION_TYPE_BUY) {
            double stopPotencial = precoAtual - distanciaTrailing;
            if(stopPotencial > stopAtual) {
                novoStopLoss = stopPotencial;
                deveAtualizar = true;
            }
        }
        else if(tipoPosicao == POSITION_TYPE_SELL) {
            double stopPotencial = precoAtual + distanciaTrailing;
            if(stopPotencial < stopAtual || stopAtual == 0) {
                novoStopLoss = stopPotencial;
                deveAtualizar = true;
            }
        }
        
        if(deveAtualizar) {
            if(m_trade.PositionModify(_Symbol, novoStopLoss, PositionGetDouble(POSITION_TP))) {
                m_posManager.metrics.trailingStopHits++;
                LogMessage("Trailing Stop atualizado: " + DoubleToString(novoStopLoss, _Digits), LOG_INFO);
            }
        }
    }
    
    void VerificarFechamentoParcial(const double precoAtual, const ENUM_POSITION_TYPE tipoPosicao) {
        if(m_posManager.state.isPartialClosed) return;
        
        double precoEntrada = PositionGetDouble(POSITION_PRICE_OPEN);
        double takeProfit = PositionGetDouble(POSITION_TP);
        double nivelParcial = m_posManager.config.partialCloseLevel;
        
        bool deveFechar = false;
        if(tipoPosicao == POSITION_TYPE_BUY) {
            deveFechar = (precoAtual - precoEntrada) >= (takeProfit - precoEntrada) * nivelParcial;
        }
        else if(tipoPosicao == POSITION_TYPE_SELL) {
            deveFechar = (precoEntrada - precoAtual) >= (precoEntrada - takeProfit) * nivelParcial;
        }
        
        if(deveFechar) {
            double volume = PositionGetDouble(POSITION_VOLUME);
            double volumeParcial = volume * 0.5; // Fechar 50% da posição
            
            if(m_trade.PositionClosePartial(_Symbol, volumeParcial)) {
                m_posManager.state.isPartialClosed = true;
                LogMessage("Fechamento parcial executado", LOG_INFO);
            }
        }
    }
    
    void AtualizarMetricasPosicao() {
        // Calcular métricas
        m_posManager.state.maxFloatingProfit = MathMax(
            m_posManager.state.maxFloatingProfit,
            CalcularLucroFlutuante()
        );
        
        m_posManager.state.currentDrawdown = CalcularDrawdownPosicao();
        
        // Atualizar TechnologyAdvances
        PositionMetrics metricas;
        metricas.floatingProfit = CalcularLucroFlutuante();
        metricas.drawdown = m_posManager.state.currentDrawdown;
        metricas.holdingTime = CalcularTempoPosicao();
        
        m_techManager.UpdatePositionMetrics(metricas);
    }
    
    double ObterPrecoAtual() {
        return SymbolInfoDouble(_Symbol, 
            PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? SYMBOL_BID : SYMBOL_ASK
        );
    }
    
    double CalcularLucroFlutuante() {
        if(!PositionSelect(_Symbol)) return 0.0;
        
        return PositionGetDouble(POSITION_PROFIT);
    }
    
    double CalcularDrawdownPosicao() {
        if(!PositionSelect(_Symbol)) return 0.0;
        
        double lucro = PositionGetDouble(POSITION_PROFIT);
        double lucroMaximo = m_posManager.state.maxFloatingProfit;
        
        if(lucroMaximo <= 0) return 0.0;
        
        return (lucroMaximo - lucro) / lucroMaximo * 100;
    }
    
    double CalcularTempoPosicao() {
        if(!PositionSelect(_Symbol)) return 0.0;
        
        datetime tempoEntrada = (datetime)PositionGetInteger(POSITION_TIME);
        return (double)(TimeCurrent() - tempoEntrada);
    }
    
    bool ValidarCondicoesAtualizacaoStop() {
        if(!PositionSelect(_Symbol)) return false;
        if(!m_posManager.config.useTrailingStop && !m_posManager.config.usePartialClose) return false;
        
        return true;
    }
    
    void VerificarFechamentoTrade() {
        if(!m_data.setup.isValid) return;
        
        double precoAtual = m_data.market.close;
        
        // Verificar stop loss
        if(precoAtual <= m_data.setup.stopLoss) {
            FecharTrade(false);
        }
        // Verificar take profit
        else if(precoAtual >= m_data.setup.takeProfit) {
            FecharTrade(true);
        }
    }
    
    void FecharTrade(bool isLucro) {
        // Atualizar métricas de performance
        if(isLucro) {
            m_performance.consecutiveLosses = 0;
            m_performance.currentDrawdown = 0.0;
        } else {
            m_performance.consecutiveLosses++;
            m_performance.currentDrawdown += m_data.setup.risk;
        }
        
        m_performance.dailyTrades++;
        
        // Resetar setup
        m_data.setup.Reset();
    }
    
    bool Validate() override {
        if(!super.Validate()) return false;
        
        // Validar dados
        if(!ValidateData()) return false;
        
        // Validar métricas
        if(!ValidateMetrics()) return false;
        
        // Validar sinais
        if(!ValidateSignals()) return false;
        
        return true;
    }
    
private:
    bool InitializeComponents() {
        // Inicializar componentes principais
        if(!m_deltaCalculator || !m_profileAnalyzer || !m_dataCollector || 
           !m_patternAnalyzer || !m_statisticsManager || !m_qualityAnalyzer || 
           !m_alertManager || !m_dataManager || !m_responsibleTeam) {
            return false;
        }
        
        return true;
    }
    
    bool InitializeIndicators() {
        // Configurar parâmetros padrão
        SetupIndicatorDefaults();
        
        // Inicializar indicadores
        if(!InitializeMA() || 
           !InitializeRSI() || 
           !InitializeATR()) {
            LogMessage("Falha na inicialização dos indicadores", LOG_ERROR);
            return false;
        }
        
        // Configurar buffers
        ConfigureBuffers();
        
        // Validar inicialização
        return ValidateIndicators();
    }
    
    void SetupIndicatorDefaults() {
        m_indicators.config.Reset();
    }
    
    bool InitializeMA() {
        m_indicators.handles.ma = iMA(_Symbol, 
                                    PERIOD_CURRENT, 
                                    m_indicators.config.maPeriod,
                                    0,
                                    m_indicators.config.maMethod,
                                    m_indicators.config.priceType);
                                    
        if(m_indicators.handles.ma == INVALID_HANDLE) {
            LogMessage("Erro: Falha ao inicializar Média Móvel", LOG_ERROR);
            return false;
        }
        return true;
    }
    
    bool InitializeRSI() {
        m_indicators.handles.rsi = iRSI(_Symbol,
                                      PERIOD_CURRENT,
                                      m_indicators.config.rsiPeriod,
                                      m_indicators.config.priceType);
                                      
        if(m_indicators.handles.rsi == INVALID_HANDLE) {
            LogMessage("Erro: Falha ao inicializar RSI", LOG_ERROR);
            return false;
        }
        return true;
    }
    
    bool InitializeATR() {
        m_indicators.handles.atr = iATR(_Symbol,
                                      PERIOD_CURRENT,
                                      m_indicators.config.atrPeriod);
                                      
        if(m_indicators.handles.atr == INVALID_HANDLE) {
            LogMessage("Erro: Falha ao inicializar ATR", LOG_ERROR);
            return false;
        }
        return true;
    }
    
    void ConfigureBuffers() {
        // Configurar arrays como séries
        ArraySetAsSeries(m_indicators.buffers.ma, true);
        ArraySetAsSeries(m_indicators.buffers.rsi, true);
        ArraySetAsSeries(m_indicators.buffers.atr, true);
        ArraySetAsSeries(m_indicators.buffers.volume, true);
        
        // Copiar dados iniciais
        CopyBuffer(m_indicators.handles.ma, 0, 0, 100, m_indicators.buffers.ma);
        CopyBuffer(m_indicators.handles.rsi, 0, 0, 100, m_indicators.buffers.rsi);
        CopyBuffer(m_indicators.handles.atr, 0, 0, 100, m_indicators.buffers.atr);
    }
    
    double CalculateVolumeMA() {
        double sum = 0;
        
        // Validar período
        if(m_indicators.config.volumePeriod <= 0) {
            LogMessage("Erro: Período de volume inválido", LOG_ERROR);
            return 0;
        }
        
        // Calcular média
        for(int i = 0; i < m_indicators.config.volumePeriod; i++) {
            sum += m_indicators.buffers.volume[i];
        }
        
        return sum / m_indicators.config.volumePeriod;
    }
    
    bool ValidateIndicators() {
        // Verificar handles
        if(m_indicators.handles.ma == INVALID_HANDLE ||
           m_indicators.handles.rsi == INVALID_HANDLE ||
           m_indicators.handles.atr == INVALID_HANDLE) {
            return false;
        }
        
        // Verificar buffers
        if(ArraySize(m_indicators.buffers.ma) == 0 ||
           ArraySize(m_indicators.buffers.rsi) == 0 ||
           ArraySize(m_indicators.buffers.atr) == 0) {
            return false;
        }
        
        return true;
    }
    
    void UpdateIndicators() {
        // Atualizar buffers
        CopyBuffer(m_indicators.handles.ma, 0, 0, 100, m_indicators.buffers.ma);
        CopyBuffer(m_indicators.handles.rsi, 0, 0, 100, m_indicators.buffers.rsi);
        CopyBuffer(m_indicators.handles.atr, 0, 0, 100, m_indicators.buffers.atr);
        
        // Integração com TechnologyAdvances
        UpdateTechIndicators();
    }
    
    void UpdateTechIndicators() {
        if(m_techManager) {
            // Atualizar indicadores no TechnologyAdvances
            m_techManager.UpdateIndicators(
                m_indicators.buffers.ma,
                m_indicators.buffers.rsi,
                m_indicators.buffers.atr,
                m_indicators.buffers.volume
            );
        }
    }
    
    bool CollectData() {
        return m_dataCollector.CollectData();
    }
    
    bool UpdateMarketData() {
        // Validar condições de mercado
        if(!ValidateMarketConditions()) {
            LogMessage("Mercado fechado ou condições inválidas", LOG_WARNING);
            return false;
        }
        
        try {
            // 1. Atualizar preços
            UpdatePriceData();
            
            // 2. Atualizar indicadores
            UpdateIndicatorData();
            
            // 3. Atualizar volume
            UpdateVolumeData();
            
            // 4. Atualizar análises avançadas
            UpdateAdvancedAnalysis();
            
            // 5. Validar e finalizar
            FinalizeUpdate();
            
        } catch(const int error) {
            HandleUpdateError(error);
        }
        
        return true;
    }
    
    bool ValidateMarketConditions() {
        // Verificar horário de mercado
        if(!IsMarketOpen()) return false;
        
        // Verificar conectividade
        if(!TerminalInfoInteger(TERMINAL_CONNECTED)) {
            LogMessage("Terminal desconectado", LOG_ERROR);
            return false;
        }
        
        // Verificar dados disponíveis
        if(!BarsInRange()) return false;
        
        return true;
    }
    
    void UpdatePriceData() {
        m_rtData.price.open = iOpen(_Symbol, PERIOD_CURRENT, 0);
        m_rtData.price.high = iHigh(_Symbol, PERIOD_CURRENT, 0);
        m_rtData.price.low = iLow(_Symbol, PERIOD_CURRENT, 0);
        m_rtData.price.close = iClose(_Symbol, PERIOD_CURRENT, 0);
        m_rtData.price.last = SymbolInfoDouble(_Symbol, SYMBOL_LAST);
        m_rtData.price.bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        m_rtData.price.ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    }
    
    void UpdateIndicatorData() {
        // Atualizar buffers dos indicadores
        CopyBuffer(m_indicators.handles.ma, 0, 0, 3, m_indicators.buffers.ma);
        CopyBuffer(m_indicators.handles.rsi, 0, 0, 3, m_indicators.buffers.rsi);
        CopyBuffer(m_indicators.handles.atr, 0, 0, 3, m_indicators.buffers.atr);
        
        // Calcular métricas técnicas
        m_rtData.tech.trend = CalcularTendencia();
        m_rtData.tech.momentum = CalcularMomentum();
        m_rtData.tech.volatility = m_indicators.buffers.atr[0];
        m_rtData.tech.strength = CalcularForcaMercado();
    }
    
    void UpdateVolumeData() {
        // Volume básico
        m_rtData.volume.current = iVolume(_Symbol, PERIOD_CURRENT, 0);
        m_rtData.volume.ma = CalculateVolumeMA();
        
        // Volume avançado
        if(m_config.useOrderFlow) {
            m_rtData.volume.buyVolume = CalcularVolumeCompra();
            m_rtData.volume.sellVolume = CalcularVolumeVenda();
            m_rtData.volume.delta = m_rtData.volume.buyVolume - m_rtData.volume.sellVolume;
            m_rtData.volume.imbalance = CalcularDesbalanceamentoVolume();
        }
    }
    
    void UpdateAdvancedAnalysis() {
        // Market Profile
        if(m_config.useMarketProfile) {
            UpdateMarketProfile();
        }
        
        // Order Flow
        if(m_config.useOrderFlow) {
            UpdateOrderFlow();
        }
        
        // Integração com TechnologyAdvances
        if(m_techManager) {
            m_techManager.UpdateMarketData(m_rtData);
        }
    }
    
    void FinalizeUpdate() {
        m_rtData.lastUpdate = TimeCurrent();
        m_rtData.isValid = true;
        
        // Notificar atualizações significativas
        if(DetectarMudancasSignificativas()) {
            NotificarEquipe("Mudanças significativas detectadas no mercado");
        }
    }
    
    bool IsMarketOpen() {
        datetime time = TimeCurrent();
        MqlDateTime dt;
        TimeToStruct(time, dt);
        
        // Verificar dia da semana
        if(dt.day_of_week == 0 || dt.day_of_week == 6) return false;
        
        // Verificar horário (9:00 - 18:00)
        if(dt.hour < 9 || dt.hour >= 18) return false;
        
        return true;
    }
    
    void HandleUpdateError(const int error) {
        string errorMsg = StringFormat("Erro na atualização: %d", error);
        LogMessage(errorMsg, LOG_ERROR);
        m_rtData.isValid = false;
        
        // Notificar equipe técnica
        NotificarEquipeTecnica(errorMsg);
    }
    
    // Métodos auxiliares para cálculos
    double CalcularTendencia() {
        if(ArraySize(m_indicators.buffers.ma) < 3) return 0.0;
        
        double ma1 = m_indicators.buffers.ma[0];
        double ma2 = m_indicators.buffers.ma[1];
        double ma3 = m_indicators.buffers.ma[2];
        
        // Tendência positiva
        if(ma1 > ma2 && ma2 > ma3) return 1.0;
        // Tendência negativa
        if(ma1 < ma2 && ma2 < ma3) return -1.0;
        
        return 0.0;
    }
    
    double CalcularMomentum() {
        if(ArraySize(m_indicators.buffers.rsi) == 0) return 0.0;
        return m_indicators.buffers.rsi[0];
    }
    
    double CalcularForcaMercado() {
        double forcaVolume = m_rtData.volume.current / m_rtData.volume.ma;
        double forcaMomentum = MathAbs(m_rtData.tech.momentum - 50) / 50;
        double forcaTendencia = MathAbs(m_rtData.tech.trend);
        
        return (forcaVolume + forcaMomentum + forcaTendencia) / 3;
    }
    
    double CalcularVolumeCompra() {
        double volumeCompra = 0.0;
        int totalTicks = 100;
        
        for(int i = 0; i < totalTicks; i++) {
            if(iClose(_Symbol, PERIOD_CURRENT, i) > iOpen(_Symbol, PERIOD_CURRENT, i)) {
                volumeCompra += iVolume(_Symbol, PERIOD_CURRENT, i);
            }
        }
        
        return volumeCompra;
    }
    
    double CalcularVolumeVenda() {
        double volumeVenda = 0.0;
        int totalTicks = 100;
        
        for(int i = 0; i < totalTicks; i++) {
            if(iClose(_Symbol, PERIOD_CURRENT, i) < iOpen(_Symbol, PERIOD_CURRENT, i)) {
                volumeVenda += iVolume(_Symbol, PERIOD_CURRENT, i);
            }
        }
        
        return volumeVenda;
    }
    
    double CalcularDesbalanceamentoVolume() {
        double volumeTotal = m_rtData.volume.buyVolume + m_rtData.volume.sellVolume;
        if(volumeTotal == 0) return 0.0;
        
        return (m_rtData.volume.buyVolume - m_rtData.volume.sellVolume) / volumeTotal;
    }
    
    bool DetectarMudancasSignificativas() {
        static double ultimoPreco = 0.0;
        static double ultimoVolume = 0.0;
        
        if(ultimoPreco == 0.0 || ultimoVolume == 0.0) {
            ultimoPreco = m_rtData.price.close;
            ultimoVolume = m_rtData.volume.current;
            return false;
        }
        
        double variacaoPreco = MathAbs(m_rtData.price.close - ultimoPreco) / ultimoPreco;
        double variacaoVolume = MathAbs(m_rtData.volume.current - ultimoVolume) / ultimoVolume;
        
        ultimoPreco = m_rtData.price.close;
        ultimoVolume = m_rtData.volume.current;
        
        return variacaoPreco > 0.01 || variacaoVolume > 0.5;
    }
    
    bool BarsInRange() {
        int totalBarras = Bars(_Symbol, PERIOD_CURRENT);
        return totalBarras >= 100;
    }
    
    void UpdateMarketProfile() {
        // Implementar atualização do Market Profile
    }
    
    void UpdateOrderFlow() {
        // Implementar atualização do Order Flow
    }
    
    void HandleSystemError(const int error) {
        string errorDesc = GetLastError();
        Print("Erro no Volume Footprint Chart: ", error, " - ", errorDesc);
        
        // Registrar erro
        if(m_performance.logFile != "") {
            FileWrite(m_performance.logFile, 
                      StringFormat("%s - Erro: %d - %s", 
                                  TimeToString(TimeCurrent()), 
                                  error, 
                                  errorDesc));
        }
    }
    
    bool ValidateData() {
        return m_dataCollector.ValidateData();
    }
    
    bool ValidateMetrics() {
        return m_metrics.isValid;
    }
    
    bool ValidateSignals() {
        return m_signal.isValid;
    }
    
    void UpdateSignalCache() {
        if(m_signal.isValid) {
            ArrayResize(m_signalCache, ArraySize(m_signalCache) + 1);
            m_signalCache[ArraySize(m_signalCache) - 1] = m_signal;
            
            // Manter tamanho máximo do cache
            if(ArraySize(m_signalCache) > m_maxCacheSize) {
                ArrayCopy(m_signalCache, m_signalCache, 0, 1);
                ArrayResize(m_signalCache, ArraySize(m_signalCache) - 1);
            }
        }
    }
    
    void ProcessAlerts() {
        if(m_signal.isValid && m_signal.strength > 0.7) {
            m_alertManager.ProcessAlert(m_signal, m_responsibleTeam);
        }
    }
    
    void UpdateExecutionMetrics() {
        m_executionLatency = ObterLatenciaExecucao();
        m_executionAccuracy = CalcularPrecisaoExecucao();
        m_costEfficiency = CalcularEficienciaCusto();
    }
    
    double ObterLatenciaExecucao() {
        static datetime ultimoTempoAtualizacao = 0;
        datetime tempoAtual = TimeCurrent();
        
        if(ultimoTempoAtualizacao == 0) {
            ultimoTempoAtualizacao = tempoAtual;
            return 0.0;
        }
        
        double latencia = (double)(tempoAtual - ultimoTempoAtualizacao);
        ultimoTempoAtualizacao = tempoAtual;
        
        return latencia;
    }
    
    double CalcularPrecisaoExecucao() {
        if(ArraySize(m_signalCache) < 2) return 0.0;
        
        int sinaisCorretos = 0;
        int totalSinais = 0;
        
        for(int i = 1; i < ArraySize(m_signalCache); i++) {
            if(m_signalCache[i].type == m_signalCache[i-1].type) {
                // Verificar se o sinal anterior foi correto
                if(ValidarResultadoSinal(&m_signalCache[i-1])) {
                    sinaisCorretos++;
                }
            }
            totalSinais++;
        }
        
        return totalSinais > 0 ? (double)sinaisCorretos / totalSinais : 0.0;
    }
    
    double CalcularEficienciaCusto() {
        if(ArraySize(m_signalCache) == 0) return 0.0;
        
        double custoTotal = 0.0;
        double ganhoTotal = 0.0;
        
        for(int i = 0; i < ArraySize(m_signalCache); i++) {
            if(m_signalCache[i].isValid) {
                // Calcular custo do sinal (baseado em volume e latência)
                double custoSinal = CalcularCustoSinal(&m_signalCache[i]);
                custoTotal += custoSinal;
                
                // Calcular ganho do sinal (baseado em acurácia e força)
                double ganhoSinal = CalcularGanhoSinal(&m_signalCache[i]);
                ganhoTotal += ganhoSinal;
            }
        }
        
        return custoTotal > 0 ? ganhoTotal / custoTotal : 0.0;
    }
    
    bool ValidarResultadoSinal(FootprintSignal* signal) {
        if(!signal || !signal.isValid) return false;
        
        // Implementar validação do resultado do sinal
        // Por exemplo, verificar se o preço moveu na direção esperada
        return true;
    }
    
    double CalcularCustoSinal(FootprintSignal* signal) {
        if(!signal || !signal.isValid) return 0.0;
        
        // Custo baseado em volume e latência
        double custoVolume = m_data.market.volume * 0.0001; // 0.01% do volume
        double custoLatencia = ObterLatenciaExecucao() * 0.001; // 0.1% da latência
        
        return custoVolume + custoLatencia;
    }
    
    double CalcularGanhoSinal(FootprintSignal* signal) {
        if(!signal || !signal.isValid) return 0.0;
        
        // Ganho baseado em acurácia e força do sinal
        double ganhoPrecisao = signal.confidence * 100;
        double ganhoForca = signal.strength * 50;
        
        return ganhoPrecisao + ganhoForca;
    }
}; 