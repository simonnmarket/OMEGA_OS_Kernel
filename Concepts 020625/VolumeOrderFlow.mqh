#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

// Estrutura para dados de delta volume
struct DeltaVolumeData {
    double buyVolume;         // Volume de compra
    double sellVolume;        // Volume de venda
    double delta;             // Delta (compra - venda)
    double cumulativeDelta;   // Delta cumulativo
    double pressure;          // Pressão do volume
    bool isValid;             // Validação
    datetime timestamp;       // Timestamp
    
    void Reset() {
        buyVolume = 0.0;
        sellVolume = 0.0;
        delta = 0.0;
        cumulativeDelta = 0.0;
        pressure = 0.0;
        isValid = false;
        timestamp = 0;
    }
};

// Estrutura para dados de absorção
struct AbsorptionData {
    double priceLevel;        // Nível de preço
    double absorbedVolume;    // Volume absorvido
    bool isBuyAbsorption;     // Flag de absorção de compra
    double strength;          // Força da absorção
    datetime timestamp;       // Timestamp
    
    void Reset() {
        priceLevel = 0.0;
        absorbedVolume = 0.0;
        isBuyAbsorption = false;
        strength = 0.0;
        timestamp = 0;
    }
};

// Estrutura para dados de fluxo de ordens
struct OrderFlowData {
    DeltaVolumeData deltaVolume;  // Dados de delta volume
    AbsorptionData absorptions[]; // Array de absorções
    double volumeImbalance;       // Desequilíbrio de volume
    bool isValid;                 // Validação
    datetime lastUpdate;          // Última atualização
    
    void Reset() {
        deltaVolume.Reset();
        ArrayFree(absorptions);
        volumeImbalance = 0.0;
        isValid = false;
        lastUpdate = 0;
    }
};

// Classe para análise de fluxo de ordens
class COrderFlowAnalyzer {
private:
    // Handles dos indicadores
    int volumeHandle;        // Handle do indicador de volume
    int priceHandle;         // Handle do preço
    
    // Buffers
    double volumeBuffer[];   // Buffer de volume
    double priceBuffer[];    // Buffer de preços
    
    // Configurações
    int lookbackPeriod;      // Período de análise
    double volumeThreshold;  // Limiar de volume
    double deltaThreshold;   // Limiar de delta
    
    // Estado
    bool initialized;        // Flag de inicialização
    OrderFlowData currentData; // Dados atuais
    
    // Métodos privados
    void InitializeBuffers() {
        ArrayResize(volumeBuffer, lookbackPeriod);
        ArrayResize(priceBuffer, lookbackPeriod);
        ArrayInitialize(volumeBuffer, 0.0);
        ArrayInitialize(priceBuffer, 0.0);
    }
    
    void UpdateBuffers() {
        for(int i = 0; i < lookbackPeriod; i++) {
            volumeBuffer[i] = iVolume(_Symbol, PERIOD_CURRENT, i);
            priceBuffer[i] = iClose(_Symbol, PERIOD_CURRENT, i);
        }
    }
    
    void CalculateDeltaVolume() {
        currentData.deltaVolume.Reset();
        
        for(int i = 0; i < lookbackPeriod; i++) {
            if(priceBuffer[i] > priceBuffer[i + 1]) {
                currentData.deltaVolume.buyVolume += volumeBuffer[i];
            } else {
                currentData.deltaVolume.sellVolume += volumeBuffer[i];
            }
        }
        
        currentData.deltaVolume.delta = currentData.deltaVolume.buyVolume - currentData.deltaVolume.sellVolume;
        currentData.deltaVolume.cumulativeDelta += currentData.deltaVolume.delta;
        currentData.deltaVolume.pressure = CalculatePressure();
        currentData.deltaVolume.isValid = true;
        currentData.deltaVolume.timestamp = TimeCurrent();
    }
    
    double CalculatePressure() {
        double pressure = 0.0;
        double totalVolume = currentData.deltaVolume.buyVolume + currentData.deltaVolume.sellVolume;
        
        if(totalVolume > 0) {
            pressure = currentData.deltaVolume.delta / totalVolume;
        }
        
        return pressure;
    }
    
    void DetectAbsorptions() {
        ArrayFree(currentData.absorptions);
        
        for(int i = 1; i < lookbackPeriod - 1; i++) {
            if(IsAbsorption(i)) {
                ProcessAbsorption(i);
            }
        }
    }
    
    bool IsAbsorption(const int shift) {
        // Verificar volume significativo
        if(volumeBuffer[shift] < volumeThreshold) return false;
        
        // Verificar padrão de absorção
        bool isBuyAbsorption = priceBuffer[shift] < priceBuffer[shift + 1] && 
                              volumeBuffer[shift] > volumeBuffer[shift + 1];
                              
        bool isSellAbsorption = priceBuffer[shift] > priceBuffer[shift + 1] && 
                               volumeBuffer[shift] > volumeBuffer[shift + 1];
                               
        return isBuyAbsorption || isSellAbsorption;
    }
    
    void ProcessAbsorption(const int shift) {
        AbsorptionData absorption;
        absorption.Reset();
        
        absorption.priceLevel = priceBuffer[shift];
        absorption.absorbedVolume = volumeBuffer[shift];
        absorption.isBuyAbsorption = priceBuffer[shift] < priceBuffer[shift + 1];
        absorption.strength = CalculateAbsorptionStrength(shift);
        absorption.timestamp = TimeCurrent();
        
        int size = ArraySize(currentData.absorptions);
        ArrayResize(currentData.absorptions, size + 1);
        currentData.absorptions[size] = absorption;
    }
    
    double CalculateAbsorptionStrength(const int shift) {
        double strength = 0.0;
        double avgVolume = 0.0;
        
        // Calcular volume médio
        for(int i = 1; i < 5; i++) {
            avgVolume += volumeBuffer[shift + i];
        }
        avgVolume /= 4;
        
        // Calcular força
        if(avgVolume > 0) {
            strength = volumeBuffer[shift] / avgVolume;
        }
        
        return strength;
    }
    
    void CalculateVolumeImbalance() {
        double totalVolume = currentData.deltaVolume.buyVolume + currentData.deltaVolume.sellVolume;
        
        if(totalVolume > 0) {
            currentData.volumeImbalance = (currentData.deltaVolume.buyVolume - currentData.deltaVolume.sellVolume) / totalVolume;
        }
    }
    
public:
    // Construtor
    COrderFlowAnalyzer() {
        lookbackPeriod = 20;
        volumeThreshold = 1.5;
        deltaThreshold = 0.7;
        initialized = false;
        currentData.Reset();
        InitializeBuffers();
    }
    
    // Destrutor
    ~COrderFlowAnalyzer() {
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
        
        initialized = true;
        return true;
    }
    
    // Processamento de dados
    bool ProcessData() {
        if(!initialized) return false;
        
        // Atualiza buffers
        UpdateBuffers();
        
        // Calcula delta volume
        CalculateDeltaVolume();
        
        // Detecta absorções
        DetectAbsorptions();
        
        // Calcula desequilíbrio
        CalculateVolumeImbalance();
        
        // Atualiza timestamp
        currentData.lastUpdate = TimeCurrent();
        currentData.isValid = true;
        
        return true;
    }
    
    // Retorna dados atuais
    OrderFlowData GetData() const {
        return currentData;
    }
    
    // Métodos para configuração
    void SetLookbackPeriod(int period) {
        lookbackPeriod = period;
        InitializeBuffers();
    }
    
    void SetVolumeThreshold(double threshold) {
        volumeThreshold = threshold;
    }
    
    void SetDeltaThreshold(double threshold) {
        deltaThreshold = threshold;
    }
    
    // Métodos auxiliares
    static bool IsSignificantDelta(const DeltaVolumeData& delta, double threshold) {
        return MathAbs(delta.delta) > threshold;
    }
    
    static bool IsStrongAbsorption(const AbsorptionData& absorption, double threshold) {
        return absorption.strength > threshold;
    }
}; 