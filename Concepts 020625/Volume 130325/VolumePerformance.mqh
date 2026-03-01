#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

// Adicionar include do sistema few-shot
#include <Quantum/FewShotTrainingSystem.mqh>

// Estrutura para métricas de performance
struct PerformanceMetrics {
    double accuracy;          // Precisão dos sinais
    double latency;           // Latência de processamento
    double cpuUsage;          // Uso de CPU
    double memoryUsage;       // Uso de memória
    int totalSignals;         // Total de sinais gerados
    int validSignals;         // Sinais válidos
    datetime lastUpdate;      // Última atualização
    bool isValid;             // Validação
    
    void Reset() {
        accuracy = 0.0;
        latency = 0.0;
        cpuUsage = 0.0;
        memoryUsage = 0.0;
        totalSignals = 0;
        validSignals = 0;
        lastUpdate = 0;
        isValid = false;
    }
};

// Estrutura para logs de performance
struct PerformanceLog {
    datetime timestamp;       // Timestamp
    string message;          // Mensagem
    int level;              // Nível do log (0=Info, 1=Warning, 2=Error)
    
    void Reset() {
        timestamp = 0;
        message = "";
        level = 0;
    }
};

// Classe para monitoramento de performance
class CVolumePerformance {
private:
    PerformanceMetrics m_metrics;     // Métricas de performance
    PerformanceLog m_logs[];          // Logs de performance
    int m_maxLogs;                    // Máximo de logs armazenados
    datetime m_startTime;             // Tempo de início
    double m_totalLatency;            // Latência total
    int m_latencyCount;               // Contador de latência
    
    // Sistema de treinamento few-shot
    CFewShotTrainingSystem* m_fewShotSystem;
    
    // Métodos privados
    void UpdateMetrics() {
        // Atualizar métricas de performance
        m_metrics.accuracy = CalculateAccuracy();
        m_metrics.latency = CalculateAverageLatency();
        m_metrics.cpuUsage = GetCPUUsage();
        m_metrics.memoryUsage = GetMemoryUsage();
        m_metrics.lastUpdate = TimeCurrent();
        m_metrics.isValid = true;
        
        // Atualizar treinamento few-shot
        if(m_fewShotSystem != NULL) {
            m_fewShotSystem.Train(
                m_metrics,
                m_logs
            );
        }
    }
    
    double CalculateAccuracy() {
        if(m_metrics.totalSignals == 0) return 0.0;
        return (double)m_metrics.validSignals / m_metrics.totalSignals;
    }
    
    double CalculateAverageLatency() {
        if(m_latencyCount == 0) return 0.0;
        return m_totalLatency / m_latencyCount;
    }
    
    double GetCPUUsage() {
        // Implementar medição de CPU
        return 0.0;
    }
    
    double GetMemoryUsage() {
        // Implementar medição de memória
        return 0.0;
    }
    
    void AddLog(const string& message, int level) {
        PerformanceLog log;
        log.timestamp = TimeCurrent();
        log.message = message;
        log.level = level;
        
        ArrayResize(m_logs, ArraySize(m_logs) + 1);
        m_logs[ArraySize(m_logs) - 1] = log;
        
        // Manter apenas os últimos logs
        if(ArraySize(m_logs) > m_maxLogs) {
            ArrayCopy(m_logs, m_logs, 0, 1, ArraySize(m_logs) - 1);
            ArrayResize(m_logs, ArraySize(m_logs) - 1);
        }
    }
    
public:
    CVolumePerformance() {
        m_maxLogs = 1000;
        m_metrics.Reset();
        m_startTime = TimeCurrent();
        m_totalLatency = 0.0;
        m_latencyCount = 0;
        
        // Inicializar sistema few-shot
        m_fewShotSystem = new CFewShotTrainingSystem();
    }
    
    ~CVolumePerformance() {
        // Liberar sistema few-shot
        delete m_fewShotSystem;
    }
    
    bool Initialize() {
        // Inicializar sistema few-shot
        if(!m_fewShotSystem.Initialize()) {
            Print("Erro ao inicializar sistema few-shot");
            return false;
        }
        
        return true;
    }
    
    void Update() {
        UpdateMetrics();
    }
    
    void RecordLatency(double latency) {
        m_totalLatency += latency;
        m_latencyCount++;
    }
    
    void RecordSignal(bool isValid) {
        m_metrics.totalSignals++;
        if(isValid) m_metrics.validSignals++;
    }
    
    PerformanceMetrics GetMetrics() const {
        return m_metrics;
    }
    
    PerformanceLog GetLogs() const {
        return m_logs;
    }
    
    // Métodos para logging
    void LogInfo(const string& message) {
        AddLog(message, 0);
    }
    
    void LogWarning(const string& message) {
        AddLog(message, 1);
    }
    
    void LogError(const string& message) {
        AddLog(message, 2);
    }
    
    // Métodos para configuração
    void SetMaxLogs(int maxLogs) {
        m_maxLogs = maxLogs;
    }
    
    // Métodos para análise
    double GetUptime() const {
        return TimeCurrent() - m_startTime;
    }
    
    double GetSignalRate() const {
        double uptime = GetUptime();
        if(uptime == 0) return 0.0;
        return m_metrics.totalSignals / uptime;
    }
    
    bool IsPerformanceAcceptable() const {
        return m_metrics.accuracy >= 0.7 && 
               m_metrics.latency < 0.1 && 
               m_metrics.cpuUsage < 80.0;
    }
}; 