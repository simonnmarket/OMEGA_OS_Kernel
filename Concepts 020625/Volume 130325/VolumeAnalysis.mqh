#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

// Adicionar includes dos agentes
#include <Quantum/StatisticalAnalysisAgent.mqh>
#include <Quantum/QuantumProjectionAgent.mqh>
#include <Quantum/PiCyclicAnalysis.mqh>

// Estruturas para análise institucional
struct InstitutionalVolume {
    double levels[];            // Níveis de volume
    double delta[];             // Delta por nível
    double absorption[];        // Absorção por nível
    bool isInstitutional[];     // Flag institucional
    datetime timestamps[];      // Timestamps
    
    void Reset() {
        ArrayFree(levels);
        ArrayFree(delta);
        ArrayFree(absorption);
        ArrayFree(isInstitutional);
        ArrayFree(timestamps);
    }
};

struct PricePatterns {
    bool isBreakout;           // Rompimento
    bool isReversal;           // Reversão
    bool isAccumulation;       // Acumulação
    bool isDistribution;       // Distribuição
    double confidence;         // Confiança
    ENUM_PATTERN_TYPE type;    // Tipo do padrão
    
    void Reset() {
        isBreakout = false;
        isReversal = false;
        isAccumulation = false;
        isDistribution = false;
        confidence = 0.0;
        type = PATTERN_UNKNOWN;
    }
};

struct Correlations {
    double priceVolume;        // Correlação preço/volume
    double volumeDelta;        // Correlação volume/delta
    double priceAction;        // Correlação preço/ação
    double significance;       // Significância
    bool isValid;             // Validação
    
    void Reset() {
        priceVolume = 0.0;
        volumeDelta = 0.0;
        priceAction = 0.0;
        significance = 0.0;
        isValid = false;
    }
};

// Estrutura para dados de volume
struct VolumeData {
    double volume;           // Volume atual
    double deltaVolume;      // Delta volume (volume compra - volume venda)
    double avgVolume;        // Volume médio
    double volumeRatio;      // Razão volume atual/médio
    double volumeStrength;   // Força do volume
    double volumeTrend;      // Tendência do volume
    double volumePressure;   // Pressão do volume
    double volumeImbalance;  // Desequilíbrio de volume
    
    // Dados institucionais
    InstitutionalVolume institutional;
    PricePatterns patterns;
    Correlations correlations;
    
    void Reset() {
        volume = 0.0;
        deltaVolume = 0.0;
        avgVolume = 0.0;
        volumeRatio = 0.0;
        volumeStrength = 0.0;
        volumeTrend = 0.0;
        volumePressure = 0.0;
        volumeImbalance = 0.0;
        
        institutional.Reset();
        patterns.Reset();
        correlations.Reset();
    }
};

// Estrutura para métricas de volume
struct VolumeMetrics {
    double meanVolume;        // Volume médio
    double stdDevVolume;      // Desvio padrão do volume
    double skewness;          // Assimetria
    double kurtosis;          // Curtose
    double trendStrength;     // Força da tendência
    double momentum;          // Momentum
    bool isValid;             // Validação
    
    void Reset() {
        meanVolume = 0.0;
        stdDevVolume = 0.0;
        skewness = 0.0;
        kurtosis = 0.0;
        trendStrength = 0.0;
        momentum = 0.0;
        isValid = false;
    }
};

// Classe principal de análise de volume
class CVolumeAnalysis {
private:
    // Handles dos indicadores
    int volumeHandle;        // Handle do indicador de volume
    int maVolumeHandle;      // Handle da média móvel de volume
    int priceHandle;         // Handle do preço
    
    // Buffers
    double volumeBuffer[];   // Buffer de volume
    double maVolumeBuffer[]; // Buffer da média móvel de volume
    double priceBuffer[];    // Buffer de preços
    
    // Configurações
    int volumePeriod;        // Período para análise de volume
    int maVolumePeriod;      // Período da média móvel de volume
    int analysisDepth;       // Profundidade da análise
    
    // Estado
    bool initialized;        // Flag de inicialização
    VolumeData currentData;  // Dados atuais de volume
    VolumeMetrics metrics;   // Métricas estatísticas
    
    // Agentes
    CStatisticalAnalysisAgent* m_statisticalAgent;
    CQuantumProjectionAgent* m_quantumAgent;
    CPiCyclicAnalysis* m_piAnalysis;
    
    // Métodos privados
    void InitializeBuffers() {
        ArrayResize(volumeBuffer, volumePeriod);
        ArrayResize(maVolumeBuffer, volumePeriod);
        ArrayResize(priceBuffer, volumePeriod);
        ArrayInitialize(volumeBuffer, 0.0);
        ArrayInitialize(maVolumeBuffer, 0.0);
        ArrayInitialize(priceBuffer, 0.0);
    }
    
    void UpdateBuffers() {
        for(int i = 0; i < volumePeriod; i++) {
            volumeBuffer[i] = iVolume(_Symbol, PERIOD_CURRENT, i);
            maVolumeBuffer[i] = iMA(_Symbol, PERIOD_CURRENT, maVolumePeriod, 0, MODE_SMA, VOLUME_TICK, i);
            priceBuffer[i] = iClose(_Symbol, PERIOD_CURRENT, i);
        }
    }
    
    double CalculateMeanVolume() {
        double sum = 0.0;
        for(int i = 0; i < volumePeriod; i++) {
            sum += volumeBuffer[i];
        }
        return sum / volumePeriod;
    }
    
    double CalculateStandardDeviation() {
        double mean = CalculateMeanVolume();
        double sumSquaredDiff = 0.0;
        
        for(int i = 0; i < volumePeriod; i++) {
            double diff = volumeBuffer[i] - mean;
            sumSquaredDiff += diff * diff;
        }
        
        return MathSqrt(sumSquaredDiff / volumePeriod);
    }
    
    double CalculateSkewness() {
        double mean = CalculateMeanVolume();
        double stdDev = CalculateStandardDeviation();
        double sumCubedDiff = 0.0;
        
        for(int i = 0; i < volumePeriod; i++) {
            double diff = (volumeBuffer[i] - mean) / stdDev;
            sumCubedDiff += diff * diff * diff;
        }
        
        return sumCubedDiff / volumePeriod;
    }
    
    double CalculateKurtosis() {
        double mean = CalculateMeanVolume();
        double stdDev = CalculateStandardDeviation();
        double sumFourthDiff = 0.0;
        
        for(int i = 0; i < volumePeriod; i++) {
            double diff = (volumeBuffer[i] - mean) / stdDev;
            sumFourthDiff += diff * diff * diff * diff;
        }
        
        return sumFourthDiff / volumePeriod;
    }
    
    double CalculateTrendStrength() {
        double sumVolume = 0.0;
        double sumPrice = 0.0;
        double sumPriceVolume = 0.0;
        double sumPriceSquared = 0.0;
        
        for(int i = 0; i < volumePeriod; i++) {
            sumVolume += volumeBuffer[i];
            sumPrice += priceBuffer[i];
            sumPriceVolume += priceBuffer[i] * volumeBuffer[i];
            sumPriceSquared += priceBuffer[i] * priceBuffer[i];
        }
        
        double slope = (volumePeriod * sumPriceVolume - sumPrice * sumVolume) / 
                      (volumePeriod * sumPriceSquared - sumPrice * sumPrice);
        
        return MathAbs(slope);
    }
    
    double CalculateMomentum() {
        double sumVolume = 0.0;
        double sumPriceChange = 0.0;
        
        for(int i = 1; i < volumePeriod; i++) {
            double priceChange = priceBuffer[i-1] - priceBuffer[i];
            sumVolume += volumeBuffer[i];
            sumPriceChange += priceChange * volumeBuffer[i];
        }
        
        return sumPriceChange / sumVolume;
    }
    
public:
    // Construtor
    CVolumeAnalysis() {
        volumePeriod = 20;
        maVolumePeriod = 20;
        analysisDepth = 100;
        initialized = false;
        currentData.Reset();
        metrics.Reset();
        InitializeBuffers();
        
        // Inicializar agentes
        m_statisticalAgent = new CStatisticalAnalysisAgent();
        m_quantumAgent = new CQuantumProjectionAgent();
        m_piAnalysis = new CPiCyclicAnalysis();
    }
    
    // Destrutor
    ~CVolumeAnalysis() {
        if(volumeHandle != INVALID_HANDLE) IndicatorRelease(volumeHandle);
        if(maVolumeHandle != INVALID_HANDLE) IndicatorRelease(maVolumeHandle);
        if(priceHandle != INVALID_HANDLE) IndicatorRelease(priceHandle);
        
        // Liberar agentes
        delete m_statisticalAgent;
        delete m_quantumAgent;
        delete m_piAnalysis;
    }
    
    // Inicialização
    bool Init(string symbol, ENUM_TIMEFRAME timeframe) {
        // Inicializa handles dos indicadores
        volumeHandle = iVolumes(symbol, timeframe, VOLUME_TICK);
        maVolumeHandle = iMA(symbol, timeframe, maVolumePeriod, 0, MODE_SMA, VOLUME_TICK);
        priceHandle = iClose(symbol, timeframe);
        
        if(volumeHandle == INVALID_HANDLE || maVolumeHandle == INVALID_HANDLE || priceHandle == INVALID_HANDLE) {
            Print("Erro ao inicializar indicadores");
            return false;
        }
        
        // Configura buffers
        ArraySetAsSeries(volumeBuffer, true);
        ArraySetAsSeries(maVolumeBuffer, true);
        ArraySetAsSeries(priceBuffer, true);
        
        initialized = true;
        
        // Inicializar agentes
        if(!m_statisticalAgent.Initialize() || 
           !m_quantumAgent.Initialize() || 
           !m_piAnalysis.Initialize()) {
            Print("Erro ao inicializar agentes");
            return false;
        }
        
        return true;
    }
    
    // Processamento de dados
    bool ProcessData() {
        if(!initialized) return false;
        
        // Atualiza buffers
        UpdateBuffers();
        
        // Calcula métricas
        metrics.meanVolume = CalculateMeanVolume();
        metrics.stdDevVolume = CalculateStandardDeviation();
        metrics.skewness = CalculateSkewness();
        metrics.kurtosis = CalculateKurtosis();
        metrics.trendStrength = CalculateTrendStrength();
        metrics.momentum = CalculateMomentum();
        metrics.isValid = true;
        
        // Análise institucional
        AnalyzeInstitutionalVolume();
        
        // Detectar padrões
        DetectPricePatterns();
        
        // Calcular correlações
        CalculateCorrelations();
        
        // Processar com agentes
        if(m_statisticalAgent != NULL) {
            m_statisticalAgent.ProcessData(metrics);
        }
        
        if(m_quantumAgent != NULL) {
            m_quantumAgent.AnalyzeEntanglement(
                metrics.volumeImbalance,
                metrics.trendStrength,
                metrics.momentum
            );
        }
        
        if(m_piAnalysis != NULL) {
            m_piAnalysis.AnalyzeCycles(
                metrics.price,
                metrics.volume,
                metrics.trend
            );
        }
        
        return true;
    }
    
    // Retorna dados atuais
    VolumeData GetCurrentData() const {
        return currentData;
    }
    
    // Retorna métricas
    VolumeMetrics GetMetrics() const {
        return metrics;
    }
    
    // Métodos auxiliares
    static double CalculateVolumeWeightedPrice(const double& prices[], const double& volumes[], int size) {
        double sumPriceVolume = 0.0;
        double sumVolume = 0.0;
        
        for(int i = 0; i < size; i++) {
            sumPriceVolume += prices[i] * volumes[i];
            sumVolume += volumes[i];
        }
        
        return (sumVolume > 0) ? sumPriceVolume / sumVolume : 0.0;
    }
    
    static double CalculateVolumeProfile(const double& prices[], const double& volumes[], int size, double priceLevel) {
        double profileVolume = 0.0;
        double totalVolume = 0.0;
        
        for(int i = 0; i < size; i++) {
            if(MathAbs(prices[i] - priceLevel) < 0.0001) {
                profileVolume += volumes[i];
            }
            totalVolume += volumes[i];
        }
        
        return (totalVolume > 0) ? profileVolume / totalVolume : 0.0;
    }
    
    static bool IsVolumeBreakout(const double& volumes[], int size, double threshold) {
        double currentVolume = volumes[0];
        double avgVolume = 0.0;
        
        for(int i = 1; i < size; i++) {
            avgVolume += volumes[i];
        }
        avgVolume /= (size - 1);
        
        return currentVolume > (avgVolume * threshold);
    }
    
private:
    // Análise institucional
    void AnalyzeInstitutionalVolume() {
        if(!ValidateVolumeData()) return;
        
        // Processar análise de volume
        ProcessVolumeAnalysis();
        
        // Detectar padrões
        DetectPricePatterns();
        
        // Calcular correlações
        CalculateCorrelations();
    }
    
    bool ValidateVolumeData() {
        return ArraySize(volumeBuffer) >= analysisDepth &&
               ArraySize(priceBuffer) >= analysisDepth;
    }
    
    void ProcessVolumeAnalysis() {
        // Reset dados antigos
        currentData.institutional.Reset();
        
        // Analisar níveis
        for(int i = 0; i < analysisDepth; i++) {
            if(IsInstitutionalVolume(i)) {
                ProcessVolumeLevel(i);
            }
        }
    }
    
    bool IsInstitutionalVolume(const int shift) {
        // Verificar tamanho
        if(!IsLargeVolume(shift)) return false;
        
        // Verificar contexto
        if(!HasInstitutionalContext(shift)) return false;
        
        // Verificar padrão
        if(!HasVolumePattern(shift)) return false;
        
        return true;
    }
    
    bool IsLargeVolume(const int shift) {
        return volumeBuffer[shift] > maVolumeBuffer[shift] * 1.5;
    }
    
    bool HasInstitutionalContext(const int shift) {
        // Verificar tendência
        bool hasTrend = MathAbs(priceBuffer[shift] - priceBuffer[shift + 1]) > 0;
        
        // Verificar volume sustentado
        bool hasSustainedVolume = true;
        for(int i = 1; i < 3; i++) {
            if(volumeBuffer[shift + i] < maVolumeBuffer[shift + i]) {
                hasSustainedVolume = false;
                break;
            }
        }
        
        return hasTrend && hasSustainedVolume;
    }
    
    bool HasVolumePattern(const int shift) {
        // Verificar padrões de volume
        bool hasVolumePattern = false;
        
        // Padrão de acumulação
        if(priceBuffer[shift] < priceBuffer[shift + 1] && volumeBuffer[shift] > maVolumeBuffer[shift]) {
            hasVolumePattern = true;
        }
        
        // Padrão de distribuição
        if(priceBuffer[shift] > priceBuffer[shift + 1] && volumeBuffer[shift] > maVolumeBuffer[shift]) {
            hasVolumePattern = true;
        }
        
        return hasVolumePattern;
    }
    
    void ProcessVolumeLevel(const int shift) {
        // Calcular métricas
        double level = priceBuffer[shift];
        double delta = CalculateVolumeDelta(shift);
        double absorption = CalculateAbsorption(shift);
        
        // Adicionar nível
        int index = ArraySize(currentData.institutional.levels);
        ArrayResize(currentData.institutional.levels, index + 1);
        ArrayResize(currentData.institutional.delta, index + 1);
        ArrayResize(currentData.institutional.absorption, index + 1);
        ArrayResize(currentData.institutional.isInstitutional, index + 1);
        ArrayResize(currentData.institutional.timestamps, index + 1);
        
        // Configurar nível
        currentData.institutional.levels[index] = level;
        currentData.institutional.delta[index] = delta;
        currentData.institutional.absorption[index] = absorption;
        currentData.institutional.isInstitutional[index] = true;
        currentData.institutional.timestamps[index] = TimeCurrent();
    }
    
    double CalculateVolumeDelta(const int shift) {
        if(shift >= analysisDepth - 1) return 0.0;
        
        double delta = volumeBuffer[shift];
        if(priceBuffer[shift] > priceBuffer[shift + 1]) {
            delta = -delta;
        }
        
        return delta;
    }
    
    double CalculateAbsorption(const int shift) {
        if(shift >= analysisDepth - 1) return 0.0;
        
        double absorption = 0.0;
        if(volumeBuffer[shift] > maVolumeBuffer[shift]) {
            absorption = (volumeBuffer[shift] - maVolumeBuffer[shift]) / maVolumeBuffer[shift];
        }
        
        return absorption;
    }
    
    void DetectPricePatterns() {
        // Reset padrões
        currentData.patterns.Reset();
        
        // Detectar padrões
        currentData.patterns.isBreakout = DetectBreakout();
        currentData.patterns.isReversal = DetectReversal();
        currentData.patterns.isAccumulation = DetectAccumulation();
        currentData.patterns.isDistribution = DetectDistribution();
        
        // Calcular confiança
        currentData.patterns.confidence = CalculatePatternConfidence();
        
        // Determinar tipo
        currentData.patterns.type = DeterminePatternType();
    }
    
    bool DetectBreakout() {
        if(ArraySize(currentData.institutional.levels) < 2) return false;
        
        double lastLevel = currentData.institutional.levels[0];
        double currentPrice = priceBuffer[0];
        
        return MathAbs(currentPrice - lastLevel) > atrBuffer[0] * 1.5;
    }
    
    bool DetectReversal() {
        if(ArraySize(currentData.institutional.levels) < 3) return false;
        
        double lastLevel = currentData.institutional.levels[0];
        double prevLevel = currentData.institutional.levels[1];
        double currentPrice = priceBuffer[0];
        
        return (currentPrice > lastLevel && lastLevel < prevLevel) ||
               (currentPrice < lastLevel && lastLevel > prevLevel);
    }
    
    bool DetectAccumulation() {
        return currentData.volumeImbalance > 0.7 && currentData.volumePressure > 0;
    }
    
    bool DetectDistribution() {
        return currentData.volumeImbalance < -0.7 && currentData.volumePressure < 0;
    }
    
    double CalculatePatternConfidence() {
        double confidence = 0.0;
        
        // Fatores de confiança
        if(currentData.patterns.isBreakout) confidence += 0.3;
        if(currentData.patterns.isReversal) confidence += 0.2;
        if(currentData.patterns.isAccumulation) confidence += 0.25;
        if(currentData.patterns.isDistribution) confidence += 0.25;
        
        return MathMin(confidence, 1.0);
    }
    
    ENUM_PATTERN_TYPE DeterminePatternType() {
        if(currentData.patterns.isBreakout) return PATTERN_STOP_HUNT;
        if(currentData.patterns.isReversal) return PATTERN_PRICE_MANIP;
        if(currentData.patterns.isAccumulation) return PATTERN_ORDER_BLOCK;
        if(currentData.patterns.isDistribution) return PATTERN_LIQUIDITY_SWEEP;
        
        return PATTERN_UNKNOWN;
    }
    
    void CalculateCorrelations() {
        // Calcular correlações
        currentData.correlations.priceVolume = CalculatePriceVolumeCorr();
        currentData.correlations.volumeDelta = CalculateVolumeDeltaCorr();
        currentData.correlations.priceAction = CalculatePriceActionCorr();
        
        // Calcular significância
        currentData.correlations.significance = CalculateSignificance();
        
        // Validar correlações
        currentData.correlations.isValid = ValidateCorrelations();
    }
    
    double CalculatePriceVolumeCorr() {
        if(ArraySize(priceBuffer) < 2 || ArraySize(volumeBuffer) < 2) return 0.0;
        
        double sumXY = 0.0, sumX = 0.0, sumY = 0.0, sumX2 = 0.0, sumY2 = 0.0;
        int n = MathMin(ArraySize(priceBuffer), ArraySize(volumeBuffer));
        
        for(int i = 0; i < n; i++) {
            sumXY += priceBuffer[i] * volumeBuffer[i];
            sumX += priceBuffer[i];
            sumY += volumeBuffer[i];
            sumX2 += priceBuffer[i] * priceBuffer[i];
            sumY2 += volumeBuffer[i] * volumeBuffer[i];
        }
        
        double numerator = n * sumXY - sumX * sumY;
        double denominator = MathSqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
        
        return denominator != 0 ? numerator / denominator : 0.0;
    }
    
    double CalculateVolumeDeltaCorr() {
        if(ArraySize(volumeBuffer) < 2) return 0.0;
        
        double sumXY = 0.0, sumX = 0.0, sumY = 0.0, sumX2 = 0.0, sumY2 = 0.0;
        int n = ArraySize(volumeBuffer);
        
        for(int i = 0; i < n; i++) {
            double delta = CalculateVolumeDelta(i);
            sumXY += volumeBuffer[i] * delta;
            sumX += volumeBuffer[i];
            sumY += delta;
            sumX2 += volumeBuffer[i] * volumeBuffer[i];
            sumY2 += delta * delta;
        }
        
        double numerator = n * sumXY - sumX * sumY;
        double denominator = MathSqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
        
        return denominator != 0 ? numerator / denominator : 0.0;
    }
    
    double CalculatePriceActionCorr() {
        if(ArraySize(priceBuffer) < 2) return 0.0;
        
        double sumXY = 0.0, sumX = 0.0, sumY = 0.0, sumX2 = 0.0, sumY2 = 0.0;
        int n = ArraySize(priceBuffer) - 1;
        
        for(int i = 0; i < n; i++) {
            double priceChange = priceBuffer[i] - priceBuffer[i + 1];
            double volumeChange = volumeBuffer[i] - volumeBuffer[i + 1];
            
            sumXY += priceChange * volumeChange;
            sumX += priceChange;
            sumY += volumeChange;
            sumX2 += priceChange * priceChange;
            sumY2 += volumeChange * volumeChange;
        }
        
        double numerator = n * sumXY - sumX * sumY;
        double denominator = MathSqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
        
        return denominator != 0 ? numerator / denominator : 0.0;
    }
    
    double CalculateSignificance() {
        double significance = 0.0;
        
        // Fatores de significância
        significance += MathAbs(currentData.correlations.priceVolume) * 0.4;
        significance += MathAbs(currentData.correlations.volumeDelta) * 0.3;
        significance += MathAbs(currentData.correlations.priceAction) * 0.3;
        
        return significance;
    }
    
    bool ValidateCorrelations() {
        return currentData.correlations.significance > 0.5 &&
               MathAbs(currentData.correlations.priceVolume) > 0.3 &&
               MathAbs(currentData.correlations.volumeDelta) > 0.3;
    }
    
    // Métricas básicas de volume (mantidas do código original)
    double CalculateVolumeStrength() {
        if(currentData.avgVolume == 0) return 0.0;
        
        double strength = (currentData.volume - currentData.avgVolume) / currentData.avgVolume;
        return MathMin(MathMax(strength, -1.0), 1.0);
    }
    
    double CalculateVolumeTrend() {
        if(volumePeriod < 2) return 0.0;
        
        double sum = 0.0;
        for(int i = 0; i < volumePeriod - 1; i++) {
            sum += volumeBuffer[i] - volumeBuffer[i + 1];
        }
        
        return sum / (volumePeriod - 1);
    }
    
    double CalculateVolumePressure() {
        if(volumePeriod < 2) return 0.0;
        
        double pressure = 0.0;
        for(int i = 0; i < volumePeriod; i++) {
            pressure += volumeBuffer[i] * (volumePeriod - i);
        }
        
        return pressure / (volumePeriod * (volumePeriod + 1) / 2);
    }
    
    double CalculateVolumeImbalance() {
        if(volumePeriod < 2) return 0.0;
        
        double buyVolume = 0.0;
        double sellVolume = 0.0;
        
        for(int i = 0; i < volumePeriod; i++) {
            if(volumeBuffer[i] > maVolumeBuffer[i]) {
                buyVolume += volumeBuffer[i];
            } else {
                sellVolume += volumeBuffer[i];
            }
        }
        
        double totalVolume = buyVolume + sellVolume;
        if(totalVolume == 0) return 0.0;
        
        return (buyVolume - sellVolume) / totalVolume;
    }
}; 