#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

#include "CategoryManager.mqh"
#include "MarketProfileCategory.mqh"
#include "VolumeFootprintCategory.mqh"
#include "VolumeFootprintPerformance.mqh"

// Interface para sub-categorias de volume
class IVolumeSubCategory {
public:
    virtual bool Initialize() = 0;
    virtual void Update() = 0;
    virtual bool Validate() = 0;
    virtual VolumeSignal* GetSignal() = 0;
    virtual VolumeMetrics* GetMetrics() = 0;
};

// Estrutura para sinais de volume
struct VolumeSignal {
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

// Estrutura para métricas de volume
struct VolumeMetrics {
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

// Classe principal para gerenciamento de volume
class CVolumeManager {
private:
    CHashMap<string, IVolumeSubCategory*> m_subCategories;
    CTechnologyManager* m_technologyManager;
    CQuantumLogger* m_logger;
    VolumeSignal m_activeSignals[];
    int m_maxActiveSignals;
    CVolumeFootprintPerformance* m_performanceMonitor;
    
public:
    CVolumeManager() {
        m_technologyManager = new CTechnologyManager();
        m_logger = new CQuantumLogger();
        m_maxActiveSignals = 100;
        ArrayResize(m_activeSignals, 0);
        m_performanceMonitor = new CVolumeFootprintPerformance();
    }
    
    ~CVolumeManager() {
        delete m_technologyManager;
        delete m_logger;
        delete m_performanceMonitor;
        CleanupSubCategories();
    }
    
    bool Initialize() {
        if(!m_technologyManager.Initialize()) return false;
        if(!m_logger.Initialize()) return false;
        if(!m_performanceMonitor) return false;
        
        // Registrar sub-categorias
        RegisterSubCategories();
        
        return true;
    }
    
    void Update() {
        // Atualizar todas as sub-categorias
        UpdateAll();
        
        // Processar sinais ativos
        ProcessActiveSignals();
        
        // Limpar sinais antigos
        CleanupOldSignals();
        
        // Atualizar monitor de performance
        if(m_performanceMonitor) {
            m_performanceMonitor.Update();
        }
    }
    
    bool RegisterSubCategory(IVolumeSubCategory* category) {
        if(!category || !category.Initialize()) return false;
        
        string categoryName = GetCategoryName(category);
        if(categoryName == "") return false;
        
        m_subCategories.Add(categoryName, category);
        return true;
    }
    
    CTechnologyManager* GetTechnologyManager() {
        return m_technologyManager;
    }
    
    CQuantumLogger* GetLogger() {
        return m_logger;
    }
    
    PerformanceMetrics* GetPerformanceMetrics() {
        if(!m_performanceMonitor) return NULL;
        return m_performanceMonitor.GetMetrics();
    }
    
private:
    void RegisterSubCategories() {
        // Registrar Market Profile
        CMarketProfileCategory* marketProfile = new CMarketProfileCategory();
        if(marketProfile.Initialize()) {
            RegisterSubCategory(marketProfile);
        } else {
            delete marketProfile;
        }
        
        // Registrar Volume Footprint
        CVolumeFootprintCategory* volumeFootprint = new CVolumeFootprintCategory();
        if(volumeFootprint.Initialize()) {
            RegisterSubCategory(volumeFootprint);
        } else {
            delete volumeFootprint;
        }
    }
    
    void UpdateAll() {
        for(int i = 0; i < m_subCategories.Size(); i++) {
            IVolumeSubCategory* category = m_subCategories.GetValue(i);
            if(category) {
                category.Update();
                ProcessSignals(category);
                
                // Atualizar métricas de performance para cada categoria
                if(m_performanceMonitor) {
                    m_performanceMonitor.Update();
                }
            }
        }
    }
    
    void ProcessSignals(IVolumeSubCategory* category) {
        VolumeSignal* signal = category.GetSignal();
        if(signal && signal.isValid) {
            AddActiveSignal(signal);
            LogSignal(signal);
        }
    }
    
    void AddActiveSignal(VolumeSignal* signal) {
        if(!signal || !signal.isValid) return;
        
        ArrayResize(m_activeSignals, ArraySize(m_activeSignals) + 1);
        m_activeSignals[ArraySize(m_activeSignals) - 1] = *signal;
        
        // Manter número máximo de sinais ativos
        if(ArraySize(m_activeSignals) > m_maxActiveSignals) {
            ArrayCopy(m_activeSignals, m_activeSignals, 0, 1);
            ArrayResize(m_activeSignals, ArraySize(m_activeSignals) - 1);
        }
    }
    
    void ProcessActiveSignals() {
        for(int i = 0; i < ArraySize(m_activeSignals); i++) {
            if(m_activeSignals[i].isValid) {
                // Processar sinal ativo
                ProcessSignal(&m_activeSignals[i]);
            }
        }
    }
    
    void ProcessSignal(VolumeSignal* signal) {
        if(!signal || !signal.isValid) return;
        
        // Implementar lógica de processamento de sinais
        // Por exemplo, notificar outros componentes do sistema
    }
    
    void LogSignal(VolumeSignal* signal) {
        if(!signal || !signal.isValid) return;
        
        string logMessage = StringFormat(
            "Volume Signal: Type=%s, Strength=%.2f, Confidence=%.2f, Time=%s",
            signal.type,
            signal.strength,
            signal.confidence,
            TimeToString(signal.time)
        );
        
        m_logger.Log(logMessage);
    }
    
    void CleanupOldSignals() {
        datetime currentTime = TimeCurrent();
        datetime maxAge = currentTime - 3600; // 1 hora
        
        for(int i = ArraySize(m_activeSignals) - 1; i >= 0; i--) {
            if(m_activeSignals[i].time < maxAge) {
                ArrayCopy(m_activeSignals, m_activeSignals, i, i + 1);
                ArrayResize(m_activeSignals, ArraySize(m_activeSignals) - 1);
            }
        }
    }
    
    void CleanupSubCategories() {
        for(int i = 0; i < m_subCategories.Size(); i++) {
            IVolumeSubCategory* category = m_subCategories.GetValue(i);
            if(category) {
                delete category;
            }
        }
        m_subCategories.Clear();
    }
    
    string GetCategoryName(IVolumeSubCategory* category) {
        if(!category) return "";
        
        // Identificar o tipo de categoria
        if(dynamic_cast<CMarketProfileCategory*>(category)) {
            return "MarketProfile";
        }
        else if(dynamic_cast<CVolumeFootprintCategory*>(category)) {
            return "VolumeFootprint";
        }
        
        return "";
    }
}; 