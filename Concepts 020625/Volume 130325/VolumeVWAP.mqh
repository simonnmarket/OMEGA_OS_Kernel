#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

// Estrutura para dados VWAP
struct VWAPData {
    double vwap;              // Preço médio ponderado por volume
    double upperBand;         // Banda superior
    double lowerBand;         // Banda inferior
    double standardDev;       // Desvio padrão
    double volume;            // Volume total
    double trend;             // Tendência (-1 a 1)
    bool isValid;             // Validação
    datetime lastUpdate;      // Última atualização
    
    void Reset() {
        vwap = 0.0;
        upperBand = 0.0;
        lowerBand = 0.0;
        standardDev = 0.0;
        volume = 0.0;
        trend = 0.0;
        isValid = false;
        lastUpdate = 0;
    }
};

// Classe para análise VWAP
class CVWAPAnalyzer {
private:
    // Handles dos indicadores
    int volumeHandle;        // Handle do indicador de volume
    int priceHandle;         // Handle do preço
    
    // Buffers
    double volumeBuffer[];   // Buffer de volume
    double priceBuffer[];    // Buffer de preços
    double vwapBuffer[];     // Buffer de VWAP
    
    // Configurações
    int lookbackPeriod;      // Período de análise
    double stdDevMultiplier; // Multiplicador do desvio padrão
    
    // Estado
    bool initialized;        // Flag de inicialização
    VWAPData currentData;   // Dados atuais
    
    // Métodos privados
    void InitializeBuffers() {
        ArrayResize(volumeBuffer, lookbackPeriod);
        ArrayResize(priceBuffer, lookbackPeriod);
        ArrayResize(vwapBuffer, lookbackPeriod);
        ArrayInitialize(volumeBuffer, 0.0);
        ArrayInitialize(priceBuffer, 0.0);
        ArrayInitialize(vwapBuffer, 0.0);
    }
    
    void UpdateBuffers() {
        for(int i = 0; i < lookbackPeriod; i++) {
            volumeBuffer[i] = iVolume(_Symbol, PERIOD_CURRENT, i);
            priceBuffer[i] = iClose(_Symbol, PERIOD_CURRENT, i);
        }
    }
    
    void CalculateVWAP() {
        // Reset dados
        currentData.Reset();
        
        // Calcular VWAP
        double sumPV = 0.0;
        double sumV = 0.0;
        
        for(int i = 0; i < lookbackPeriod; i++) {
            sumPV += priceBuffer[i] * volumeBuffer[i];
            sumV += volumeBuffer[i];
        }
        
        if(sumV > 0) {
            currentData.vwap = sumPV / sumV;
            currentData.volume = sumV;
            
            // Calcular desvio padrão
            CalculateStandardDeviation();
            
            // Calcular bandas
            currentData.upperBand = currentData.vwap + (currentData.standardDev * stdDevMultiplier);
            currentData.lowerBand = currentData.vwap - (currentData.standardDev * stdDevMultiplier);
            
            // Calcular tendência
            CalculateTrend();
            
            // Atualizar timestamps
            currentData.lastUpdate = TimeCurrent();
            currentData.isValid = true;
        }
    }
    
    void CalculateStandardDeviation() {
        double sumSquaredDiff = 0.0;
        
        for(int i = 0; i < lookbackPeriod; i++) {
            double diff = priceBuffer[i] - currentData.vwap;
            sumSquaredDiff += diff * diff;
        }
        
        currentData.standardDev = MathSqrt(sumSquaredDiff / lookbackPeriod);
    }
    
    void CalculateTrend() {
        // Calcular tendência baseada na posição do preço atual em relação ao VWAP
        double currentPrice = priceBuffer[0];
        double priceRange = currentData.upperBand - currentData.lowerBand;
        
        if(priceRange > 0) {
            currentData.trend = (currentPrice - currentData.vwap) / (priceRange / 2);
            currentData.trend = MathMax(MathMin(currentData.trend, 1.0), -1.0);
        }
    }
    
public:
    // Construtor
    CVWAPAnalyzer() {
        lookbackPeriod = 20;
        stdDevMultiplier = 2.0;
        initialized = false;
        currentData.Reset();
        InitializeBuffers();
    }
    
    // Destrutor
    ~CVWAPAnalyzer() {
        if(volumeHandle != INVALID_HANDLE) IndicatorRelease(volumeHandle);
        if(priceHandle != INVALID_HANDLE) IndicatorRelease(priceHandle);
    }
    
    // Inicialização
    bool Init(string symbol, ENUM_TIMEFRAME timeframe) {
        // Inicializa handles dos indicadores
        volumeHandle = iVolumes(symbol, timeframe, VOLUME_TICK);
        priceHandle = iClose(symbol, timeframe);
        
        if(volumeHandle == INVALID_HANDLE || priceHandle == INVALID_HANDLE) {
            Print("Erro ao inicializar indicadores");
            return false;
        }
        
        // Configura buffers
        ArraySetAsSeries(volumeBuffer, true);
        ArraySetAsSeries(priceBuffer, true);
        ArraySetAsSeries(vwapBuffer, true);
        
        initialized = true;
        return true;
    }
    
    // Processamento de dados
    bool ProcessData() {
        if(!initialized) return false;
        
        // Atualiza buffers
        UpdateBuffers();
        
        // Calcula VWAP
        CalculateVWAP();
        
        return true;
    }
    
    // Retorna dados atuais
    VWAPData GetData() const {
        return currentData;
    }
    
    // Métodos para configuração
    void SetLookbackPeriod(int period) {
        lookbackPeriod = period;
        InitializeBuffers();
    }
    
    void SetStdDevMultiplier(double multiplier) {
        stdDevMultiplier = multiplier;
    }
    
    // Métodos auxiliares
    static bool IsPriceAboveVWAP(const VWAPData& data) {
        return data.isValid && data.vwap > 0 && data.currentPrice > data.vwap;
    }
    
    static bool IsPriceBelowVWAP(const VWAPData& data) {
        return data.isValid && data.vwap > 0 && data.currentPrice < data.vwap;
    }
    
    static bool IsPriceInUpperBand(const VWAPData& data) {
        return data.isValid && data.upperBand > 0 && data.currentPrice > data.upperBand;
    }
    
    static bool IsPriceInLowerBand(const VWAPData& data) {
        return data.isValid && data.lowerBand > 0 && data.currentPrice < data.lowerBand;
    }
}; 