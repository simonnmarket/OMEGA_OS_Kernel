#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

#include "CategoryManager.mqh"

// Estruturas Avançadas de Market Profile
struct ProfileStructure {
    double valueAreaHigh;
    double valueAreaLow;
    double poc;                    
    double[] volumeNodes;
    double[] priceNodes;
    string[] tpoLetters;
    datetime initialBalance;
    bool isBalanced;
    double deviation;
    datetime timeStart;
    datetime timeEnd;
    
    void Reset() {
        valueAreaHigh = 0.0;
        valueAreaLow = 0.0;
        poc = 0.0;
        ArrayResize(volumeNodes, 0);
        ArrayResize(priceNodes, 0);
        ArrayResize(tpoLetters, 0);
        initialBalance = 0;
        isBalanced = false;
        deviation = 0.0;
        timeStart = 0;
        timeEnd = 0;
    }
};

struct TPOData {
    int letterCount;
    double[] prices;
    int[] frequency;
    string currentLetter;
    datetime periodStart;
    double initialBalance;
    
    void Reset() {
        letterCount = 0;
        ArrayResize(prices, 0);
        ArrayResize(frequency, 0);
        currentLetter = "";
        periodStart = 0;
        initialBalance = 0.0;
    }
};

struct PatternMetrics {
    bool isSinglePrint;
    bool isPoorHigh;
    bool isPoorLow;
    bool isBalanced;
    bool isBreakoutProfile;
    bool isInitialBalanceBreak;
    bool isExtendedPOC;
    double confidence;
    
    void Reset() {
        isSinglePrint = false;
        isPoorHigh = false;
        isPoorLow = false;
        isBalanced = false;
        isBreakoutProfile = false;
        isInitialBalanceBreak = false;
        isExtendedPOC = false;
        confidence = 0.0;
    }
};

// Classe para cálculo de Value Area
class CValueAreaCalculator {
private:
    double m_valueAreaPercent;
    double m_pocThreshold;
    double[] m_volumeNodes;
    double[] m_priceNodes;
    
public:
    CValueAreaCalculator() {
        m_valueAreaPercent = 0.7;
        m_pocThreshold = 0.5;
        ArrayResize(m_volumeNodes, 0);
        ArrayResize(m_priceNodes, 0);
    }
    
    ValueAreaMetrics* CalculateValueArea() {
        ValueAreaMetrics* metrics = new ValueAreaMetrics();
        
        if(ArraySize(m_volumeNodes) == 0 || ArraySize(m_priceNodes) == 0) {
            return metrics;
        }
        
        double totalVolume = 0;
        double volumeThreshold = 0;
        
        // Calcular 70% do volume total
        for(int i = 0; i < ArraySize(m_volumeNodes); i++) {
            totalVolume += m_volumeNodes[i];
        }
        
        volumeThreshold = totalVolume * m_valueAreaPercent;
        
        // Identificar Value Area
        IdentifyValueAreaBoundaries(volumeThreshold);
        
        // Calcular POC
        metrics.poc = CalculatePOC();
        metrics.high = m_valueAreaHigh;
        metrics.low = m_valueAreaLow;
        
        return metrics;
    }
    
private:
    void IdentifyValueAreaBoundaries(double threshold) {
        double currentVolume = 0;
        bool foundHigh = false;
        bool foundLow = false;
        
        for(int i = 0; i < ArraySize(m_volumeNodes); i++) {
            currentVolume += m_volumeNodes[i];
            
            if(!foundHigh && currentVolume >= threshold) {
                m_valueAreaHigh = m_priceNodes[i];
                foundHigh = true;
            }
            
            if(foundHigh && !foundLow && currentVolume >= threshold * 2) {
                m_valueAreaLow = m_priceNodes[i];
                foundLow = true;
            }
        }
    }
    
    double CalculatePOC() {
        int maxVolumeIndex = 0;
        double maxVolume = m_volumeNodes[0];
        
        for(int i = 1; i < ArraySize(m_volumeNodes); i++) {
            if(m_volumeNodes[i] > maxVolume) {
                maxVolume = m_volumeNodes[i];
                maxVolumeIndex = i;
            }
        }
        
        return m_priceNodes[maxVolumeIndex];
    }
};

// Classe para análise de padrões de perfil
class CProfilePatternAnalyzer {
private:
    double[] m_priceNodes;
    double[] m_volumeNodes;
    datetime m_initialBalance;
    double m_poc;
    
public:
    PatternMetrics* AnalyzePattern() {
        PatternMetrics* metrics = new PatternMetrics();
        
        if(!ValidateData()) {
            return metrics;
        }
        
        metrics.isSinglePrint = CheckForSinglePrints();
        metrics.isBalanced = CheckProfileBalance();
        metrics.isInitialBalanceBreak = CheckInitialBalanceBreak();
        metrics.isPoorHigh = CheckPoorHigh();
        metrics.isPoorLow = CheckPoorLow();
        metrics.isExtendedPOC = CheckExtendedPOC();
        
        // Calcular confiança
        metrics.confidence = CalculatePatternConfidence(metrics);
        
        return metrics;
    }
    
private:
    bool ValidateData() {
        return ArraySize(m_priceNodes) > 0 && 
               ArraySize(m_volumeNodes) > 0 && 
               m_initialBalance > 0 && 
               m_poc > 0;
    }
    
    bool CheckForSinglePrints() {
        if(ArraySize(m_volumeNodes) < 3) return false;
        
        int singlePrintCount = 0;
        for(int i = 1; i < ArraySize(m_volumeNodes) - 1; i++) {
            if(m_volumeNodes[i] > m_volumeNodes[i-1] * 2 && 
               m_volumeNodes[i] > m_volumeNodes[i+1] * 2) {
                singlePrintCount++;
            }
        }
        
        return singlePrintCount >= 2;
    }
    
    bool CheckProfileBalance() {
        double upperVolume = 0;
        double lowerVolume = 0;
        
        for(int i = 0; i < ArraySize(m_volumeNodes); i++) {
            if(m_priceNodes[i] > m_poc) {
                upperVolume += m_volumeNodes[i];
            } else {
                lowerVolume += m_volumeNodes[i];
            }
        }
        
        double ratio = MathMax(upperVolume, lowerVolume) / MathMin(upperVolume, lowerVolume);
        return ratio < 1.5;
    }
    
    bool CheckInitialBalanceBreak() {
        double initialHigh = m_priceNodes[0];
        double initialLow = m_priceNodes[0];
        
        for(int i = 1; i < 30; i++) { // Primeiros 30 períodos
            if(m_priceNodes[i] > initialHigh) initialHigh = m_priceNodes[i];
            if(m_priceNodes[i] < initialLow) initialLow = m_priceNodes[i];
        }
        
        double currentPrice = m_priceNodes[ArraySize(m_priceNodes) - 1];
        return currentPrice > initialHigh || currentPrice < initialLow;
    }
    
    bool CheckPoorHigh() {
        if(ArraySize(m_priceNodes) < 3) return false;
        
        int lastIndex = ArraySize(m_priceNodes) - 1;
        return m_priceNodes[lastIndex] > m_priceNodes[lastIndex-1] && 
               m_volumeNodes[lastIndex] < m_volumeNodes[lastIndex-1] * 0.7;
    }
    
    bool CheckPoorLow() {
        if(ArraySize(m_priceNodes) < 3) return false;
        
        int lastIndex = ArraySize(m_priceNodes) - 1;
        return m_priceNodes[lastIndex] < m_priceNodes[lastIndex-1] && 
               m_volumeNodes[lastIndex] < m_volumeNodes[lastIndex-1] * 0.7;
    }
    
    bool CheckExtendedPOC() {
        int pocCount = 0;
        double pocRange = m_poc * 0.0001; // 1 pip
        
        for(int i = 0; i < ArraySize(m_priceNodes); i++) {
            if(MathAbs(m_priceNodes[i] - m_poc) <= pocRange) {
                pocCount++;
            }
        }
        
        return pocCount >= 5; // POC estendido se tiver pelo menos 5 toques
    }
    
    double CalculatePatternConfidence(PatternMetrics* metrics) {
        double confidence = 0.0;
        int patternCount = 0;
        
        if(metrics.isSinglePrint) { confidence += 0.2; patternCount++; }
        if(metrics.isBalanced) { confidence += 0.2; patternCount++; }
        if(metrics.isInitialBalanceBreak) { confidence += 0.2; patternCount++; }
        if(metrics.isPoorHigh) { confidence += 0.2; patternCount++; }
        if(metrics.isPoorLow) { confidence += 0.2; patternCount++; }
        if(metrics.isExtendedPOC) { confidence += 0.2; patternCount++; }
        
        return patternCount > 0 ? confidence / patternCount : 0.0;
    }
};

// Classe para análise TPO
class CTPOAnalyzer {
private:
    datetime[] m_timeNodes;
    double[] m_pricePoints;
    string[] m_letters;
    int[] m_frequency;
    datetime m_periodStart;
    
public:
    void UpdateTPO() {
        if(!ValidateData()) return;
        
        MapTPOStructure();
        UpdateTPOLetters();
        CalculateTPOFrequency();
    }
    
private:
    bool ValidateData() {
        return ArraySize(m_timeNodes) > 0 && 
               ArraySize(m_pricePoints) > 0 && 
               m_periodStart > 0;
    }
    
    void MapTPOStructure() {
        ArrayResize(m_letters, 0);
        ArrayResize(m_pricePoints, 0);
        ArrayResize(m_frequency, 0);
        
        for(int i = 0; i < ArraySize(m_timeNodes); i++) {
            string letter = GetTPOLetter(i);
            double price = m_pricePoints[i];
            
            int index = ArraySearch(m_letters, letter);
            if(index >= 0) {
                m_frequency[index]++;
            } else {
                ArrayResize(m_letters, ArraySize(m_letters) + 1);
                ArrayResize(m_pricePoints, ArraySize(m_pricePoints) + 1);
                ArrayResize(m_frequency, ArraySize(m_frequency) + 1);
                
                m_letters[ArraySize(m_letters) - 1] = letter;
                m_pricePoints[ArraySize(m_pricePoints) - 1] = price;
                m_frequency[ArraySize(m_frequency) - 1] = 1;
            }
        }
    }
    
    string GetTPOLetter(int index) {
        datetime time = m_timeNodes[index];
        int minutes = (int)((time - m_periodStart) / 60);
        int letterIndex = minutes / 30; // 30 minutos por letra
        
        if(letterIndex >= 26) return "Z";
        return StringSubstr("ABCDEFGHIJKLMNOPQRSTUVWXYZ", letterIndex, 1);
    }
    
    void UpdateTPOLetters() {
        // Atualizar letras TPO baseado no tempo atual
        datetime currentTime = TimeCurrent();
        int currentIndex = (int)((currentTime - m_periodStart) / 60) / 30;
        
        if(currentIndex >= ArraySize(m_letters)) {
            ArrayResize(m_letters, currentIndex + 1);
            ArrayResize(m_pricePoints, currentIndex + 1);
            ArrayResize(m_frequency, currentIndex + 1);
        }
    }
    
    void CalculateTPOFrequency() {
        // Normalizar frequências
        int maxFreq = 0;
        for(int i = 0; i < ArraySize(m_frequency); i++) {
            if(m_frequency[i] > maxFreq) maxFreq = m_frequency[i];
        }
        
        if(maxFreq > 0) {
            for(int i = 0; i < ArraySize(m_frequency); i++) {
                m_frequency[i] = (int)((double)m_frequency[i] / maxFreq * 10);
            }
        }
    }
    
    int ArraySearch(string &array[], string value) {
        for(int i = 0; i < ArraySize(array); i++) {
            if(array[i] == value) return i;
        }
        return -1;
    }
};

// Classe para gerenciamento de memória do perfil
class CProfileMemoryManager {
private:
    double m_memoryThreshold;
    double m_currentMemoryUsage;
    
public:
    CProfileMemoryManager() {
        m_memoryThreshold = 45.0;
        m_currentMemoryUsage = 0.0;
    }
    
    bool ValidateMemoryUsage() {
        m_currentMemoryUsage = GetMemoryUsage();
        return m_currentMemoryUsage < m_memoryThreshold;
    }
    
    void OptimizeMemory() {
        CompressArrays();
        CleanupUnusedData();
    }
    
private:
    double GetMemoryUsage() {
        // Implementação do cálculo de uso de memória
        return 0.0;
    }
    
    void CompressArrays() {
        // Implementação da compressão de arrays
        // Reduzir tamanho de arrays mantendo dados essenciais
    }
    
    void CleanupUnusedData() {
        // Implementação da limpeza de dados não utilizados
        // Remover dados antigos e não essenciais
    }
};

// Implementação Atualizada da Categoria
class CMarketProfileCategory : public CBaseCategoryAnalyzer {
private:
    // Componentes principais
    ProfileStructure m_profile;
    TPOData m_tpo;
    PatternMetrics m_patterns;
    CValueAreaCalculator* m_valueCalculator;
    CProfilePatternAnalyzer* m_patternAnalyzer;
    CTPOAnalyzer* m_tpoAnalyzer;
    CProfileMemoryManager* m_memoryManager;
    
    // Constantes de performance
    const int UPDATE_INTERVAL = 1800; // 30 minutos
    const double MEMORY_THRESHOLD = 45.0; // MB
    const double MIN_PATTERN_CONFIDENCE = 0.89;
    
public:
    CMarketProfileCategory() : CBaseCategoryAnalyzer("MarketProfile") {
        m_valueCalculator = new CValueAreaCalculator();
        m_patternAnalyzer = new CProfilePatternAnalyzer();
        m_tpoAnalyzer = new CTPOAnalyzer();
        m_memoryManager = new CProfileMemoryManager();
        
        m_profile.Reset();
        m_tpo.Reset();
        m_patterns.Reset();
    }
    
    ~CMarketProfileCategory() {
        delete m_valueCalculator;
        delete m_patternAnalyzer;
        delete m_tpoAnalyzer;
        delete m_memoryManager;
    }
    
    virtual bool Initialize() override {
        if(!CBaseCategoryAnalyzer::Initialize()) return false;
        
        if(!ValidateTimeframe()) return false;
        if(!InitializeBuffers()) return false;
        if(!ConfigureProfile()) return false;
        
        return true;
    }
    
    virtual bool Update() override {
        if(!ValidateState()) return false;
        if(!m_memoryManager.ValidateMemoryUsage()) {
            m_memoryManager.OptimizeMemory();
        }
        
        UpdateProfile();
        GenerateProfileSignals();
        
        return true;
    }
    
    virtual bool Validate() override {
        return ValidateProfile() && ValidatePatterns();
    }

private:
    void UpdateProfile() {
        // Atualizar Value Area
        ValueAreaMetrics* metrics = m_valueCalculator.CalculateValueArea();
        m_profile.valueAreaHigh = metrics.high;
        m_profile.valueAreaLow = metrics.low;
        m_profile.poc = metrics.poc;
        
        // Atualizar TPO
        m_tpoAnalyzer.UpdateTPO();
        
        // Analisar Padrões
        PatternMetrics* patterns = m_patternAnalyzer.AnalyzePattern();
        m_patterns = *patterns;
        
        // Otimizar Profile
        OptimizeProfile();
    }
    
    void GenerateProfileSignals() {
        InsightSignal signal;
        
        // Value Area Signal
        if(IsValueAreaSignal()) {
            signal.categoryName = "MarketProfile";
            signal.signalName = "ValueArea";
            signal.strength = CalculateVASignalStrength();
            signal.confidence = m_patterns.confidence;
            signal.timestamp = TimeCurrent();
            signal.description = "Value Area Trading Opportunity";
            signal.isValid = true;
            
            AddSignal(signal);
        }
        
        // TPO Pattern Signal
        if(IsTPOPatternSignal()) {
            signal.categoryName = "MarketProfile";
            signal.signalName = "TPOPattern";
            signal.strength = CalculateTPOSignalStrength();
            signal.confidence = m_patterns.confidence;
            signal.timestamp = TimeCurrent();
            signal.description = GenerateTPOPatternDescription();
            signal.isValid = true;
            
            AddSignal(signal);
        }
        
        // Profile Pattern Signal
        if(IsProfilePatternSignal()) {
            signal.categoryName = "MarketProfile";
            signal.signalName = "ProfilePattern";
            signal.strength = CalculatePatternStrength();
            signal.confidence = m_patterns.confidence;
            signal.timestamp = TimeCurrent();
            signal.description = GeneratePatternDescription();
            signal.isValid = true;
            
            AddSignal(signal);
        }
    }
    
    bool IsValueAreaSignal() {
        return m_patterns.isBalanced && 
               fabs(m_profile.deviation) < 0.2;
    }
    
    bool IsTPOPatternSignal() {
        return m_patterns.isSinglePrint || 
               m_patterns.isPoorHigh || 
               m_patterns.isPoorLow;
    }
    
    bool IsProfilePatternSignal() {
        return m_patterns.isBreakoutProfile && 
               m_patterns.confidence >= MIN_PATTERN_CONFIDENCE;
    }
    
    double CalculateVASignalStrength() {
        return (m_patterns.confidence * 0.4 +
                (1.0 - fabs(m_profile.deviation)) * 0.3 +
                (m_patterns.isBalanced ? 0.3 : 0.0));
    }
    
    double CalculateTPOSignalStrength() {
        double strength = 0;
        
        if(m_patterns.isSinglePrint) strength += 0.4;
        if(m_patterns.isPoorHigh) strength += 0.3;
        if(m_patterns.isPoorLow) strength += 0.3;
        
        return strength * m_patterns.confidence;
    }
    
    string GenerateTPOPatternDescription() {
        string desc = "TPO Pattern: ";
        
        if(m_patterns.isSinglePrint) desc += "Single Print ";
        if(m_patterns.isPoorHigh) desc += "Poor High ";
        if(m_patterns.isPoorLow) desc += "Poor Low ";
        
        return desc;
    }
    
    void OptimizeProfile() {
        // Otimização de memória periódica
        if(IsCriticalMemoryUsage()) {
            m_memoryManager.OptimizeMemory();
        }
        
        // Otimização de performance
        CompressProfileData();
        OptimizeArrays();
    }
    
    bool ValidateProfile() {
        if(!ValidateValueArea()) return false;
        if(!ValidateTPOStructure()) return false;
        if(!ValidatePatterns()) return false;
        
        return true;
    }
    
    void AddSignal(const InsightSignal &signal) {
        int size = ArraySize(m_signals);
        ArrayResize(m_signals, size + 1);
        m_signals[size] = signal;
        m_state.signalCount++;
    }
    
    // Métodos auxiliares
    bool ValidateTimeframe() {
        ENUM_TIMEFRAME currentTimeframe = Period();
        
        // Validar timeframe para Market Profile
        switch(currentTimeframe) {
            case PERIOD_M1:
            case PERIOD_M5:
            case PERIOD_M15:
            case PERIOD_M30:
            case PERIOD_H1:
            case PERIOD_H4:
            case PERIOD_D1:
                return true;
            default:
                return false;
        }
    }
    
    bool InitializeBuffers() {
        // Inicializar arrays de dados
        ArrayResize(m_profile.volumeNodes, 0);
        ArrayResize(m_profile.priceNodes, 0);
        ArrayResize(m_profile.tpoLetters, 0);
        
        // Inicializar arrays de TPO
        ArrayResize(m_tpo.prices, 0);
        ArrayResize(m_tpo.frequency, 0);
        
        return true;
    }
    
    bool ConfigureProfile() {
        // Configurar parâmetros do perfil
        m_profile.timeStart = TimeCurrent();
        m_profile.timeEnd = m_profile.timeStart + UPDATE_INTERVAL;
        
        // Configurar TPO
        m_tpo.periodStart = m_profile.timeStart;
        m_tpo.letterCount = 0;
        
        return true;
    }
    
    bool ValidateState() {
        if(!m_valueCalculator || !m_patternAnalyzer || !m_tpoAnalyzer || !m_memoryManager) {
            return false;
        }
        
        if(!m_profile.isValid || !m_tpo.isValid) {
            return false;
        }
        
        return true;
    }
    
    bool ValidateValueArea() {
        if(m_profile.valueAreaHigh <= 0 || m_profile.valueAreaLow <= 0) {
            return false;
        }
        
        if(m_profile.valueAreaHigh <= m_profile.valueAreaLow) {
            return false;
        }
        
        if(m_profile.poc <= 0 || m_profile.poc < m_profile.valueAreaLow || m_profile.poc > m_profile.valueAreaHigh) {
            return false;
        }
        
        return true;
    }
    
    bool ValidateTPOStructure() {
        if(m_tpo.letterCount <= 0) {
            return false;
        }
        
        if(ArraySize(m_tpo.prices) != ArraySize(m_tpo.frequency)) {
            return false;
        }
        
        if(m_tpo.periodStart <= 0) {
            return false;
        }
        
        return true;
    }
    
    bool ValidatePatterns() {
        if(!m_patterns.isValid) {
            return false;
        }
        
        // Validar consistência dos padrões
        if(m_patterns.isBalanced && (m_patterns.isPoorHigh || m_patterns.isPoorLow)) {
            return false;
        }
        
        if(m_patterns.isBreakoutProfile && m_patterns.isBalanced) {
            return false;
        }
        
        return true;
    }
    
    bool IsCriticalMemoryUsage() {
        return m_memoryManager.GetCurrentMemoryUsage() > MEMORY_THRESHOLD;
    }
    
    void CompressProfileData() {
        // Comprimir dados do perfil mantendo pontos importantes
        int newSize = ArraySize(m_profile.volumeNodes) / 2;
        
        if(newSize > 0) {
            // Manter pontos de Value Area e POC
            double vaHigh = m_profile.valueAreaHigh;
            double vaLow = m_profile.valueAreaLow;
            double poc = m_profile.poc;
            
            // Redimensionar arrays
            ArrayResize(m_profile.volumeNodes, newSize);
            ArrayResize(m_profile.priceNodes, newSize);
            
            // Recalcular Value Area e POC
            m_profile.valueAreaHigh = vaHigh;
            m_profile.valueAreaLow = vaLow;
            m_profile.poc = poc;
        }
    }
    
    void OptimizeArrays() {
        // Otimizar arrays de TPO
        if(ArraySize(m_tpo.prices) > 100) {
            int newSize = 100;
            ArrayResize(m_tpo.prices, newSize);
            ArrayResize(m_tpo.frequency, newSize);
        }
        
        // Otimizar arrays de padrões
        if(ArraySize(m_patterns) > 50) {
            ArrayResize(m_patterns, 50);
        }
    }
    
    double CalculatePatternStrength() {
        double strength = 0.0;
        
        // Calcular força baseada em diferentes padrões
        if(m_patterns.isSinglePrint) strength += 0.3;
        if(m_patterns.isPoorHigh) strength += 0.2;
        if(m_patterns.isPoorLow) strength += 0.2;
        if(m_patterns.isBalanced) strength += 0.2;
        if(m_patterns.isBreakoutProfile) strength += 0.3;
        if(m_patterns.isInitialBalanceBreak) strength += 0.2;
        if(m_patterns.isExtendedPOC) strength += 0.2;
        
        // Ajustar força baseado na confiança
        return strength * m_patterns.confidence;
    }
    
    string GeneratePatternDescription() {
        string desc = "Profile Pattern: ";
        
        if(m_patterns.isSinglePrint) desc += "Single Print ";
        if(m_patterns.isPoorHigh) desc += "Poor High ";
        if(m_patterns.isPoorLow) desc += "Poor Low ";
        if(m_patterns.isBalanced) desc += "Balanced ";
        if(m_patterns.isBreakoutProfile) desc += "Breakout ";
        if(m_patterns.isInitialBalanceBreak) desc += "IB Break ";
        if(m_patterns.isExtendedPOC) desc += "Extended POC ";
        
        desc += StringFormat("(Strength: %.2f, Confidence: %.2f)", 
                           CalculatePatternStrength(), 
                           m_patterns.confidence);
        
        return desc;
    }
}; 