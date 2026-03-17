#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

// Estrutura para nível de suporte/resistência
struct PVSRLevel {
    double price;             // Preço do nível
    double volume;            // Volume no nível
    double strength;          // Força do nível
    bool isSupport;           // Flag de suporte
    datetime lastTouch;       // Último toque
    int touchCount;           // Contador de toques
    
    void Reset() {
        price = 0.0;
        volume = 0.0;
        strength = 0.0;
        isSupport = false;
        lastTouch = 0;
        touchCount = 0;
    }
};

// Estrutura para dados PVSRA
struct PVSRAData {
    PVSRLevel supports[];     // Níveis de suporte
    PVSRLevel resistances[];  // Níveis de resistência
    double currentPrice;      // Preço atual
    double currentVolume;     // Volume atual
    bool isValid;             // Validação
    datetime lastUpdate;      // Última atualização
    
    void Reset() {
        ArrayFree(supports);
        ArrayFree(resistances);
        currentPrice = 0.0;
        currentVolume = 0.0;
        isValid = false;
        lastUpdate = 0;
    }
};

// Classe para análise PVSRA
class CPVSRAnalyzer {
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
    double priceThreshold;   // Limiar de preço
    
    // Estado
    bool initialized;        // Flag de inicialização
    PVSRAData currentData;   // Dados atuais
    
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
    
    void IdentifyLevels() {
        // Reset dados
        currentData.Reset();
        currentData.currentPrice = priceBuffer[0];
        currentData.currentVolume = volumeBuffer[0];
        
        // Identificar suportes
        for(int i = 2; i < lookbackPeriod - 2; i++) {
            if(IsSupport(i)) {
                ProcessSupport(i);
            }
        }
        
        // Identificar resistências
        for(int i = 2; i < lookbackPeriod - 2; i++) {
            if(IsResistance(i)) {
                ProcessResistance(i);
            }
        }
        
        // Atualizar timestamps
        currentData.lastUpdate = TimeCurrent();
        currentData.isValid = true;
    }
    
    bool IsSupport(const int shift) {
        // Verificar padrão de suporte
        bool isSupport = priceBuffer[shift] < priceBuffer[shift - 1] && 
                        priceBuffer[shift] < priceBuffer[shift - 2] &&
                        priceBuffer[shift] < priceBuffer[shift + 1] && 
                        priceBuffer[shift] < priceBuffer[shift + 2];
                        
        // Verificar volume significativo
        bool hasVolume = volumeBuffer[shift] > volumeThreshold;
        
        return isSupport && hasVolume;
    }
    
    bool IsResistance(const int shift) {
        // Verificar padrão de resistência
        bool isResistance = priceBuffer[shift] > priceBuffer[shift - 1] && 
                           priceBuffer[shift] > priceBuffer[shift - 2] &&
                           priceBuffer[shift] > priceBuffer[shift + 1] && 
                           priceBuffer[shift] > priceBuffer[shift + 2];
                           
        // Verificar volume significativo
        bool hasVolume = volumeBuffer[shift] > volumeThreshold;
        
        return isResistance && hasVolume;
    }
    
    void ProcessSupport(const int shift) {
        PVSRLevel level;
        level.Reset();
        
        level.price = priceBuffer[shift];
        level.volume = volumeBuffer[shift];
        level.strength = CalculateLevelStrength(shift);
        level.isSupport = true;
        level.lastTouch = iTime(_Symbol, PERIOD_CURRENT, shift);
        level.touchCount = CountTouches(shift, true);
        
        int size = ArraySize(currentData.supports);
        ArrayResize(currentData.supports, size + 1);
        currentData.supports[size] = level;
    }
    
    void ProcessResistance(const int shift) {
        PVSRLevel level;
        level.Reset();
        
        level.price = priceBuffer[shift];
        level.volume = volumeBuffer[shift];
        level.strength = CalculateLevelStrength(shift);
        level.isSupport = false;
        level.lastTouch = iTime(_Symbol, PERIOD_CURRENT, shift);
        level.touchCount = CountTouches(shift, false);
        
        int size = ArraySize(currentData.resistances);
        ArrayResize(currentData.resistances, size + 1);
        currentData.resistances[size] = level;
    }
    
    double CalculateLevelStrength(const int shift) {
        double strength = 0.0;
        
        // Fator de volume
        double volumeFactor = volumeBuffer[shift] / CalculateAverageVolume();
        
        // Fator de toques
        double touchFactor = CountTouches(shift, priceBuffer[shift] < priceBuffer[shift + 1]) / 5.0;
        
        // Fator de recência
        double recencyFactor = 1.0 - (shift / (double)lookbackPeriod);
        
        // Calcular força total
        strength = (volumeFactor * 0.4) + (touchFactor * 0.4) + (recencyFactor * 0.2);
        
        return MathMin(strength, 1.0);
    }
    
    double CalculateAverageVolume() {
        double sum = 0.0;
        for(int i = 0; i < lookbackPeriod; i++) {
            sum += volumeBuffer[i];
        }
        return sum / lookbackPeriod;
    }
    
    int CountTouches(const int shift, bool isSupport) {
        int count = 0;
        double level = priceBuffer[shift];
        
        for(int i = 0; i < lookbackPeriod; i++) {
            if(isSupport) {
                if(MathAbs(priceBuffer[i] - level) < priceThreshold) {
                    count++;
                }
            } else {
                if(MathAbs(priceBuffer[i] - level) < priceThreshold) {
                    count++;
                }
            }
        }
        
        return count;
    }
    
public:
    // Construtor
    CPVSRAnalyzer() {
        lookbackPeriod = 20;
        volumeThreshold = 1.5;
        priceThreshold = 0.0001;
        initialized = false;
        currentData.Reset();
        InitializeBuffers();
    }
    
    // Destrutor
    ~CPVSRAnalyzer() {
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
        
        // Identifica níveis
        IdentifyLevels();
        
        return true;
    }
    
    // Retorna dados atuais
    PVSRAData GetData() const {
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
    
    void SetPriceThreshold(double threshold) {
        priceThreshold = threshold;
    }
    
    // Métodos auxiliares
    static bool IsStrongLevel(const PVSRLevel& level, double threshold) {
        return level.strength > threshold;
    }
    
    static bool IsRecentLevel(const PVSRLevel& level, int maxBars) {
        return (TimeCurrent() - level.lastTouch) < maxBars * PeriodSeconds(PERIOD_CURRENT);
    }
}; 