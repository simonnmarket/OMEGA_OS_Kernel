#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

#include "CategoryManager.mqh"

// Estruturas comuns para todas as sub-categorias
struct VolumeSignal {
    string categoryName;
    string signalName;
    double strength;
    double confidence;
    datetime timestamp;
    string description;
    bool isValid;
    
    void Reset() {
        categoryName = "";
        signalName = "";
        strength = 0.0;
        confidence = 0.0;
        timestamp = 0;
        description = "";
        isValid = false;
    }
};

struct VolumeMetrics {
    double value;
    double average;
    double delta;
    double force;
    datetime lastUpdate;
    
    void Reset() {
        value = 0.0;
        average = 0.0;
        delta = 0.0;
        force = 0.0;
        lastUpdate = 0;
    }
};

// Interface expandida para sub-categorias
interface IVolumeSubCategory {
public:
    // Métodos principais
    virtual bool Initialize() = 0;
    virtual void Update() = 0;
    virtual bool ValidateSignals() = 0;
    virtual string GetSubCategoryName() = 0;
    
    // Métodos adicionais
    virtual VolumeSignal* GetSignals() = 0;
    virtual VolumeMetrics* GetMetrics() = 0;
    virtual bool IsValidState() = 0;
    virtual void Reset() = 0;
};

// Estrutura para dados de volume básico
struct VolumeBasicData {
    // Métricas básicas
    double currentVolume;     // Volume atual
    double averageVolume;     // Volume médio
    double relativeVolume;    // Volume relativo
    double deltaVolume;       // Delta volume
    datetime lastUpdate;      // Última atualização
    
    // VSA Metrics
    struct VSA {
        bool isClimax;        // Clímax
        bool isChurn;         // Churn
        bool isTest;          // Teste
        bool isUpThrust;      // Upthrust
        bool isSpringTest;    // Teste de spring
        bool isNoSupply;      // Sem oferta
        bool isDemandComing;  // Demanda chegando
        double effort;        // Esforço
        double result;        // Resultado
    } vsa;
    
    // Delta Analysis
    struct Delta {
        double buyVolume;     // Volume compra
        double sellVolume;    // Volume venda
        double delta;         // Delta
        double cumDelta;      // Delta cumulativo
        bool isDeltaPositive; // Delta positivo
        double strength;      // Força
        bool isDiverging;     // Divergência
    } delta;
    
    // Statistical Analysis
    struct Stats {
        double correlation;   // Correlação
        double standardDev;   // Desvio padrão
        double zscore;        // Z-score
        double momentum;      // Momentum
        double efficiency;    // Eficiência
        double quality;       // Qualidade
    } stats;
    
    // Pattern Recognition
    struct Patterns {
        bool isAccumulation;  // Acumulação
        bool isDistribution;  // Distribuição
        bool isBreakout;      // Rompimento
        bool isExhaustion;    // Exaustão
        double strength;      // Força
        datetime lastUpdate;  // Última atualização
    } patterns;
    
    // Liquidez
    struct Liquidity {
        double marketDepth;   // Profundidade do mercado
        double bidAskSpread;  // Spread bid/ask
        double turnoverRate;  // Taxa de giro
        bool isLiquid;        // É líquido
        double flowRate;      // Taxa de fluxo
    } liquidity;
    
    // Order Flow
    struct OrderFlow {
        double buyPressure;   // Pressão compra
        double sellPressure;  // Pressão venda
        double absorption;    // Absorção
        bool isImbalance;     // Desequilíbrio
        double netFlow;       // Fluxo líquido
    } orderFlow;
    
    // Machine Learning
    struct ML {
        double prediction;     // Previsão
        double confidence;    // Confiança
        double accuracy;      // Precisão
        datetime lastUpdate;  // Última atualização
        bool isValid;         // Válido
    } ml;
    
    void Reset() {
        currentVolume = 0.0;
        averageVolume = 0.0;
        relativeVolume = 0.0;
        deltaVolume = 0.0;
        lastUpdate = 0;
        
        // Reset VSA
        vsa.isClimax = false;
        vsa.isChurn = false;
        vsa.isTest = false;
        vsa.isUpThrust = false;
        vsa.isSpringTest = false;
        vsa.isNoSupply = false;
        vsa.isDemandComing = false;
        vsa.effort = 0.0;
        vsa.result = 0.0;
        
        // Reset Delta
        delta.buyVolume = 0.0;
        delta.sellVolume = 0.0;
        delta.delta = 0.0;
        delta.cumDelta = 0.0;
        delta.isDeltaPositive = false;
        delta.strength = 0.0;
        delta.isDiverging = false;
        
        // Reset Stats
        stats.correlation = 0.0;
        stats.standardDev = 0.0;
        stats.zscore = 0.0;
        stats.momentum = 0.0;
        stats.efficiency = 0.0;
        stats.quality = 0.0;
        
        // Reset Patterns
        patterns.isAccumulation = false;
        patterns.isDistribution = false;
        patterns.isBreakout = false;
        patterns.isExhaustion = false;
        patterns.strength = 0.0;
        patterns.lastUpdate = 0;
        
        // Reset Liquidity
        liquidity.marketDepth = 0.0;
        liquidity.bidAskSpread = 0.0;
        liquidity.turnoverRate = 0.0;
        liquidity.isLiquid = false;
        liquidity.flowRate = 0.0;
        
        // Reset OrderFlow
        orderFlow.buyPressure = 0.0;
        orderFlow.sellPressure = 0.0;
        orderFlow.absorption = 0.0;
        orderFlow.isImbalance = false;
        orderFlow.netFlow = 0.0;
        
        // Reset ML
        ml.prediction = 0.0;
        ml.confidence = 0.0;
        ml.accuracy = 0.0;
        ml.lastUpdate = 0;
        ml.isValid = false;
    }
};

// Categoria de análise de volume básico
class CVolumeBasicCategory : public CBaseCategoryAnalyzer, public IVolumeSubCategory {
private:
    string          m_symbol;
    ENUM_TIMEFRAME  m_timeframe;
    int             m_volumeHandle;
    int             m_maVolumeHandle;
    double          m_volumeBuffer[];
    double          m_maVolumeBuffer[];
    VolumeBasicData m_currentData;
    
    // Configurações
    struct Config {
        int lookbackPeriod;           // Período de análise
        double minVolumeRatio;        // Razão mínima de volume
        double minConfidence;         // Confiança mínima
        double maxSpread;             // Spread máximo
        int minSequence;              // Sequência mínima
        bool enableAlerts;            // Alertas ativos
        bool enableML;                // Machine Learning ativo
        bool enableAdvancedAnalysis;  // Análise avançada ativa
    } m_config;
    
    // Gerenciadores
    CDataCollector*    m_dataCollector;
    CPatternAnalyzer*  m_patternAnalyzer;
    CStatsAnalyzer*    m_statsAnalyzer;
    CQualityAnalyzer*  m_qualityAnalyzer;
    CAlertManager*     m_alertManager;
    CDataManager*      m_dataManager;
    CErrorHandler*     m_errorHandler;
    TeamMember*        m_responsibleTeam;
    
    // Métricas de execução
    struct ExecutionMetrics {
        double latency;
        double execution_accuracy;
        double cost_efficiency;
    };
    
    // Cache de sinais e métricas
    CArrayObj m_signalCache;
    VolumeMetrics m_metrics;
    
public:
    CVolumeBasicCategory(string symbol, ENUM_TIMEFRAME timeframe) 
        : CBaseCategoryAnalyzer("VolumeBasic") {
        m_symbol = symbol;
        m_timeframe = timeframe;
        m_volumeHandle = INVALID_HANDLE;
        m_maVolumeHandle = INVALID_HANDLE;
        m_currentData.Reset();
        
        // Configurações padrão
        m_config.lookbackPeriod = 20;
        m_config.minVolumeRatio = 1.5;
        m_config.minConfidence = 0.7;
        m_config.maxSpread = 0.0002;
        m_config.minSequence = 3;
        m_config.enableAlerts = true;
        m_config.enableML = false;
        m_config.enableAdvancedAnalysis = true;
        
        ArraySetAsSeries(m_volumeBuffer, true);
        ArraySetAsSeries(m_maVolumeBuffer, true);
    }
    
    ~CVolumeBasicCategory() {
        Cleanup();
        if(m_volumeHandle != INVALID_HANDLE) IndicatorRelease(m_volumeHandle);
        if(m_maVolumeHandle != INVALID_HANDLE) IndicatorRelease(m_maVolumeHandle);
    }
    
    virtual bool Initialize() override {
        if(!CBaseCategoryAnalyzer::Initialize()) return false;
        
        // Inicializa gerenciadores
        m_dataCollector = new CDataCollector();
        m_patternAnalyzer = new CPatternAnalyzer();
        m_statsAnalyzer = new CStatsAnalyzer();
        m_qualityAnalyzer = new CQualityAnalyzer();
        m_alertManager = new CAlertManager();
        m_dataManager = new CDataManager();
        m_errorHandler = new CErrorHandler();
        
        // Atribui equipe responsável
        AssignResponsibleTeam();
        
        // Inicializa handles dos indicadores
        m_volumeHandle = iVolumes(m_symbol, m_timeframe, VOLUME_TICK);
        m_maVolumeHandle = iMA(m_symbol, m_timeframe, m_config.lookbackPeriod, 0, MODE_SMA, VOLUME_TICK);
        
        if(m_volumeHandle == INVALID_HANDLE || m_maVolumeHandle == INVALID_HANDLE) {
            LogError("Falha ao inicializar indicadores de volume");
            return false;
        }
        
        return true;
    }
    
    virtual bool Update() override {
        if(!CBaseCategoryAnalyzer::Update()) return false;
        
        try {
            // 1. Coletar e validar dados
            if(!CollectAndValidateData()) {
                LogError("Falha na coleta/validação de dados");
                return false;
            }
            
            // 2. Análises principais e avançadas
            PerformCompleteAnalysis();
            
            // 3. Gerar e validar sinais
            GenerateAndValidateSignals();
            
            // 4. Otimização e manutenção
            OptimizeAndMaintain();
            
            return true;
            
        } catch(const int error) {
            LogError("Erro durante atualização: " + IntegerToString(error));
            return false;
        }
    }
    
    virtual bool Validate() override {
        if(!CBaseCategoryAnalyzer::Validate()) return false;
        
        return m_volumeHandle != INVALID_HANDLE && 
               m_maVolumeHandle != INVALID_HANDLE;
    }
    
    // Retorna dados atuais
    VolumeBasicData GetCurrentData() const {
        return m_currentData;
    }
    
    // Implementação da interface IVolumeSubCategory
    virtual string GetSubCategoryName() override {
        return "VolumeBasic";
    }
    
    virtual VolumeSignal* GetSignals() override {
        return m_signalCache;
    }
    
    virtual VolumeMetrics* GetMetrics() override {
        return &m_metrics;
    }
    
    virtual bool IsValidState() override {
        return Validate();
    }
    
    virtual void Reset() override {
        m_currentData.Reset();
        m_signalCache.Clear();
        m_metrics.Reset();
    }
    
    virtual bool ValidateSignals() override {
        if(m_signalCache.Count() == 0) return false;
        
        bool isValid = true;
        for(int i = 0; i < m_signalCache.Count(); i++) {
            VolumeSignal* signal = m_signalCache.At(i);
            if(signal == NULL || !signal.isValid) {
                isValid = false;
                break;
            }
        }
        
        return isValid;
    }
    
private:
    bool CollectAndValidateData() {
        // Atualiza buffers
        if(!UpdateBuffers()) return false;
        
        // Volume atual
        m_currentData.currentVolume = m_volumeBuffer[0];
        
        // Volume médio
        m_currentData.averageVolume = m_maVolumeBuffer[0];
        
        // Volume relativo
        if(m_currentData.averageVolume > 0) {
            m_currentData.relativeVolume = m_currentData.currentVolume / m_currentData.averageVolume;
        }
        
        // Delta volume
        m_currentData.deltaVolume = CalculateDeltaVolume();
        
        // Atualiza timestamp
        m_currentData.lastUpdate = TimeCurrent();
        
        return ValidateDataQuality();
    }
    
    void PerformCompleteAnalysis() {
        // Análises base
        AnalyzeVSA();
        AnalyzeDelta();
        AnalyzeStatistics();
        AnalyzePatterns();
        
        // Análises avançadas
        if(m_config.enableAdvancedAnalysis) {
            AnalyzeLiquidity();
            AnalyzeOrderFlow();
        }
        
        // Análise ML
        if(m_config.enableML) {
            AnalyzeML();
        }
    }
    
    void GenerateAndValidateSignals() {
        // Sinais tradicionais
        if(IsValidVSASignal()) GenerateVSASignal();
        if(IsValidDeltaSignal()) GenerateDeltaSignal();
        if(IsValidPatternSignal()) GeneratePatternSignal();
        
        // Sinais avançados
        if(m_config.enableAdvancedAnalysis) {
            if(IsValidLiquiditySignal()) GenerateLiquiditySignal();
            if(IsValidOrderFlowSignal()) GenerateOrderFlowSignal();
        }
        
        // Sinais ML
        if(m_config.enableML && IsValidMLSignal()) {
            GenerateMLSignal();
        }
        
        // Processar alertas
        ProcessAlerts();
    }
    
    void OptimizeAndMaintain() {
        // Otimização de memória
        if(m_dataManager.GetMemoryUsage() > m_dataManager.memoryThreshold) {
            m_dataManager.OptimizeMemory();
        }
        
        // Atualização de métricas de performance
        UpdatePerformanceMetrics();
        
        // Manutenção de cache
        CleanupOldSignals();
        DefragmentArrays();
    }
    
    bool UpdateBuffers() {
        if(CopyBuffer(m_volumeHandle, 0, 0, m_config.lookbackPeriod, m_volumeBuffer) <= 0) {
            LogError("Falha ao copiar buffer de volume");
            return false;
        }
        
        if(CopyBuffer(m_maVolumeHandle, 0, 0, m_config.lookbackPeriod, m_maVolumeBuffer) <= 0) {
            LogError("Falha ao copiar buffer de média móvel de volume");
            return false;
        }
        
        return true;
    }
    
    double CalculateDeltaVolume() {
        if(ArraySize(m_volumeBuffer) < 2) return 0.0;
        
        double delta = 0.0;
        for(int i = 0; i < m_config.lookbackPeriod; i++) {
            if(m_volumeBuffer[i] > m_maVolumeBuffer[i]) {
                delta += m_volumeBuffer[i];
            } else {
                delta -= m_volumeBuffer[i];
            }
        }
        
        return delta;
    }
    
    bool ValidateDataQuality() {
        // Verifica spread
        double spread = SymbolInfoInteger(m_symbol, SYMBOL_SPREAD) * SymbolInfoDouble(m_symbol, SYMBOL_POINT);
        if(spread > m_config.maxSpread) {
            LogError("Spread muito alto: " + DoubleToString(spread));
            return false;
        }
        
        // Verifica sequência mínima
        if(!ValidateMinSequence()) {
            LogError("Sequência mínima não atingida");
            return false;
        }
        
        return true;
    }
    
    bool ValidateMinSequence() {
        int sequence = 0;
        for(int i = 0; i < m_config.minSequence; i++) {
            if(m_volumeBuffer[i] > m_maVolumeBuffer[i]) {
                sequence++;
            }
        }
        return sequence >= m_config.minSequence;
    }
    
    void AnalyzeVSA() {
        m_currentData.vsa.isClimax = DetectClimaxVolume();
        m_currentData.vsa.isChurn = DetectChurnVolume();
        m_currentData.vsa.isTest = DetectTestVolume();
        m_currentData.vsa.isUpThrust = DetectUpThrust();
        m_currentData.vsa.isSpringTest = DetectSpringTest();
        m_currentData.vsa.effort = CalculateEffort();
        m_currentData.vsa.result = CalculateResult();
        
        // Integração com TechnologyAdvances
        m_techManager.UpdateVSAMetrics(m_currentData.vsa);
    }
    
    void AnalyzeDelta() {
        m_currentData.delta.buyVolume = CalculateBuyVolume();
        m_currentData.delta.sellVolume = CalculateSellVolume();
        m_currentData.delta.delta = m_currentData.delta.buyVolume - m_currentData.delta.sellVolume;
        m_currentData.delta.cumDelta = UpdateCumulativeDelta();
        m_currentData.delta.isDeltaPositive = (m_currentData.delta.delta > 0);
        m_currentData.delta.strength = CalculateDeltaStrength();
        m_currentData.delta.isDiverging = CheckDeltaDivergence();
    }
    
    void AnalyzeStatistics() {
        // Implementação da análise estatística
        CalculateCorrelation();
        CalculateStandardDeviation();
        CalculateZScore();
        CalculateMomentum();
        CalculateEfficiency();
        CalculateQuality();
    }
    
    void AnalyzePatterns() {
        // Implementação da análise de padrões
        DetectAccumulation();
        DetectDistribution();
        DetectBreakout();
        DetectExhaustion();
    }
    
    void AnalyzeLiquidity() {
        // Implementação da análise de liquidez
        CalculateMarketDepth();
        CalculateBidAskSpread();
        CalculateTurnoverRate();
        AnalyzeFlowRate();
    }
    
    void AnalyzeOrderFlow() {
        // Implementação da análise de order flow
        CalculateBuySellPressure();
        CalculateAbsorption();
        AnalyzeImbalance();
        CalculateNetFlow();
    }
    
    void AnalyzeML() {
        m_currentData.ml.prediction = PredictVolumePattern();
        m_currentData.ml.confidence = CalculateMLConfidence();
        m_currentData.ml.accuracy = UpdateMLAccuracy();
        m_currentData.ml.lastUpdate = TimeCurrent();
        m_currentData.ml.isValid = ValidateMLPrediction();
        
        // Integração com TechnologyAdvances
        m_techManager.UpdateMLMetrics(m_currentData.ml);
    }
    
    void GenerateVSASignal() {
        if(m_currentData.vsa.isClimax) {
            AddSignal("VolumeClimax", "Clímax de volume detectado", 0.8);
        }
        if(m_currentData.vsa.isChurn) {
            AddSignal("VolumeChurn", "Churn de volume detectado", 0.7);
        }
        if(m_currentData.vsa.isTest) {
            AddSignal("VolumeTest", "Teste de volume detectado", 0.6);
        }
    }
    
    void GenerateDeltaSignal() {
        if(m_currentData.delta.isDeltaPositive && m_currentData.delta.strength > 0.7) {
            AddSignal("StrongBuyDelta", "Delta de compra forte", 0.8);
        }
        if(!m_currentData.delta.isDeltaPositive && m_currentData.delta.strength > 0.7) {
            AddSignal("StrongSellDelta", "Delta de venda forte", 0.8);
        }
    }
    
    void GeneratePatternSignal() {
        if(m_currentData.patterns.isAccumulation) {
            AddSignal("Accumulation", "Padrão de acumulação detectado", 0.7);
        }
        if(m_currentData.patterns.isDistribution) {
            AddSignal("Distribution", "Padrão de distribuição detectado", 0.7);
        }
        if(m_currentData.patterns.isBreakout) {
            AddSignal("Breakout", "Rompimento detectado", 0.8);
        }
    }
    
    void GenerateLiquiditySignal() {
        if(m_currentData.liquidity.isLiquid && m_currentData.liquidity.flowRate > 0.7) {
            AddSignal("HighLiquidity", "Alta liquidez detectada", 0.7);
        }
    }
    
    void GenerateOrderFlowSignal() {
        // Implementação da geração de sinal de order flow
        // ... lógica de geração ...
    }
    
    void GenerateMLSignal() {
        InsightSignal signal;
        signal.Reset();
        signal.categoryName = m_categoryName;
        signal.signalName = "ML_Volume";
        signal.strength = m_currentData.ml.confidence;
        signal.confidence = m_currentData.ml.accuracy;
        signal.timestamp = TimeCurrent();
        signal.description = GenerateMLDescription();
        signal.isValid = m_currentData.ml.isValid;
        
        AddSignal(signal);
        
        // Notificar equipe responsável
        if(signal.strength > 0.8) {
            NotifyTeam(signal);
        }
    }
    
    void AddSignal(string name, string description, double strength) {
        VolumeSignal* signal = new VolumeSignal();
        signal.Reset();
        signal.categoryName = GetSubCategoryName();
        signal.signalName = name;
        signal.strength = strength;
        signal.confidence = CalculateSignalConfidence();
        signal.timestamp = TimeCurrent();
        signal.description = description;
        signal.isValid = true;
        
        m_signalCache.Add(signal);
        
        // Atualiza métricas
        UpdateMetrics();
    }
    
    double CalculateSignalConfidence() {
        double confidence = 0.0;
        
        // Fatores de confiança
        confidence += m_currentData.vsa.effort * 0.2;
        confidence += m_currentData.delta.strength * 0.2;
        confidence += m_currentData.patterns.strength * 0.2;
        confidence += m_currentData.liquidity.flowRate * 0.2;
        confidence += m_currentData.orderFlow.netFlow * 0.2;
        
        return MathMin(confidence, 1.0);
    }
    
    void UpdateMetrics() {
        m_metrics.value = m_currentData.currentVolume;
        m_metrics.average = m_currentData.averageVolume;
        m_metrics.delta = m_currentData.deltaVolume;
        m_metrics.force = CalculateSignalConfidence();
        m_metrics.lastUpdate = TimeCurrent();
    }
    
    void CleanupResources() {
        // Limpa buffers não utilizados
        if(ArraySize(m_volumeBuffer) > m_config.lookbackPeriod) {
            ArrayResize(m_volumeBuffer, m_config.lookbackPeriod);
        }
        if(ArraySize(m_maVolumeBuffer) > m_config.lookbackPeriod) {
            ArrayResize(m_maVolumeBuffer, m_config.lookbackPeriod);
        }
    }
    
    // Funções auxiliares para análise VSA
    bool DetectClimaxVolume() {
        return m_currentData.relativeVolume > 2.0;
    }
    
    bool DetectChurnVolume() {
        return m_currentData.relativeVolume > 1.5 && 
               MathAbs(m_currentData.deltaVolume) < 0.1;
    }
    
    bool DetectTestVolume() {
        return m_currentData.relativeVolume < 0.5 && 
               m_currentData.deltaVolume > 0;
    }
    
    bool DetectUpThrust() {
        return m_currentData.relativeVolume > 1.2 && 
               m_currentData.deltaVolume < 0;
    }
    
    bool DetectSpringTest() {
        return m_currentData.relativeVolume > 1.5 && 
               m_currentData.deltaVolume > 0.5;
    }
    
    double CalculateEffort() {
        return m_currentData.relativeVolume;
    }
    
    double CalculateResult() {
        double priceChange = SymbolInfoDouble(m_symbol, SYMBOL_ASK) - 
                            SymbolInfoDouble(m_symbol, SYMBOL_BID);
        return priceChange;
    }
    
    // Funções auxiliares para análise Delta
    double CalculateBuyVolume() {
        double buyVolume = 0.0;
        for(int i = 0; i < m_config.lookbackPeriod; i++) {
            if(m_volumeBuffer[i] > m_maVolumeBuffer[i]) {
                buyVolume += m_volumeBuffer[i];
            }
        }
        return buyVolume;
    }
    
    double CalculateSellVolume() {
        double sellVolume = 0.0;
        for(int i = 0; i < m_config.lookbackPeriod; i++) {
            if(m_volumeBuffer[i] < m_maVolumeBuffer[i]) {
                sellVolume += m_volumeBuffer[i];
            }
        }
        return sellVolume;
    }
    
    double UpdateCumulativeDelta() {
        return m_currentData.delta.cumDelta + m_currentData.delta.delta;
    }
    
    double CalculateDeltaStrength() {
        double totalVolume = m_currentData.delta.buyVolume + m_currentData.delta.sellVolume;
        if(totalVolume == 0) return 0.0;
        return MathAbs(m_currentData.delta.delta) / totalVolume;
    }
    
    bool CheckDeltaDivergence() {
        // Implementação da verificação de divergência
        return false;
    }
    
    // Funções auxiliares para análise ML
    double PredictVolumePattern() {
        // Implementação da previsão de padrão de volume
        return 0.0;
    }
    
    double CalculateMLConfidence() {
        // Implementação do cálculo de confiança ML
        return 0.0;
    }
    
    double UpdateMLAccuracy() {
        // Implementação da atualização de precisão ML
        return 0.0;
    }
    
    bool ValidateMLPrediction() {
        // Implementação da validação de previsão ML
        return false;
    }
    
    string GenerateMLDescription() {
        return StringFormat(
            "ML Volume Prediction: %.2f, Confidence: %.2f, Accuracy: %.2f",
            m_currentData.ml.prediction,
            m_currentData.ml.confidence,
            m_currentData.ml.accuracy
        );
    }
    
    // Funções auxiliares para validação de sinais
    bool IsValidVSASignal() {
        return m_currentData.vsa.isClimax || 
               m_currentData.vsa.isChurn || 
               m_currentData.vsa.isTest;
    }
    
    bool IsValidDeltaSignal() {
        return MathAbs(m_currentData.delta.strength) > 0.7;
    }
    
    bool IsValidPatternSignal() {
        return m_currentData.patterns.isAccumulation || 
               m_currentData.patterns.isDistribution || 
               m_currentData.patterns.isBreakout;
    }
    
    bool IsValidLiquiditySignal() {
        return m_currentData.liquidity.isLiquid && 
               m_currentData.liquidity.flowRate > 0.7;
    }
    
    bool IsValidOrderFlowSignal() {
        return m_currentData.orderFlow.isImbalance && 
               MathAbs(m_currentData.orderFlow.netFlow) > 0.5;
    }
    
    bool IsValidMLSignal() {
        return m_currentData.ml.isValid && 
               m_currentData.ml.confidence > 0.7;
    }
    
    // Funções auxiliares para métricas de performance
    double GetExecutionLatency() {
        // Implementação do cálculo de latência
        return 0.0;
    }
    
    double CalculateCostEfficiency() {
        // Implementação do cálculo de eficiência de custo
        return 0.0;
    }
    
    void CleanupOldSignals() {
        // Implementação da limpeza de sinais antigos
    }
    
    void DefragmentArrays() {
        // Implementação da desfragmentação de arrays
    }
    
    void ProcessAlerts() {
        // Implementação do processamento de alertas
    }
    
    void NotifyTeam(const InsightSignal& signal) {
        if(m_responsibleTeam == NULL) return;
        
        string message = StringFormat(
            "Volume Signal Alert\nType: %s\nStrength: %.2f\nConfidence: %.2f",
            signal.signalName,
            signal.strength,
            signal.confidence
        );
        
        // Integração com TeamStructure
        for(int i = 0; i < ArraySize(m_responsibleTeam); i++) {
            if(m_responsibleTeam[i].department == QUANTITATIVE_RESEARCH ||
               m_responsibleTeam[i].department == ALGO_TRADING) {
                SendNotification(m_responsibleTeam[i], message);
            }
        }
    }
    
    void AssignResponsibleTeam() {
        // Integração com TeamStructure
        m_responsibleTeam = new TeamMember[2];
        m_responsibleTeam[0].department = QUANTITATIVE_RESEARCH;
        m_responsibleTeam[0].expertise = "Volume Analysis";
        m_responsibleTeam[1].department = ALGO_TRADING;
        m_responsibleTeam[1].expertise = "Execution";
    }
    
    void Cleanup() {
        delete m_dataCollector;
        delete m_patternAnalyzer;
        delete m_statsAnalyzer;
        delete m_qualityAnalyzer;
        delete m_alertManager;
        delete m_dataManager;
        delete m_errorHandler;
        delete[] m_responsibleTeam;
    }
}; 