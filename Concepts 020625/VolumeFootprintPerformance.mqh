#property copyright "Quantum Sensory Trading System"
#property link      "https://www.quantumsensory.com"
#property version   "1.0"
#property strict

// Estrutura para métricas de performance
struct PerformanceMetrics {
    // Métricas de Retorno
    double totalReturn;        // Retorno total
    double dailyReturn;        // Retorno diário
    double monthlyReturn;      // Retorno mensal
    double annualizedReturn;   // Retorno anualizado
    
    // Métricas de Risco
    double maxDrawdown;        // Drawdown máximo
    double currentDrawdown;    // Drawdown atual
    double volatility;         // Volatilidade
    double sharpeRatio;        // Índice Sharpe
    double sortinoRatio;       // Índice Sortino
    
    // Métricas de Trade
    int totalTrades;           // Total de trades
    double winRate;            // Taxa de acerto
    double profitFactor;       // Fator de lucro
    double avgTradeReturn;     // Retorno médio por trade
    
    void Reset() {
        totalReturn = 0.0;
        dailyReturn = 0.0;
        monthlyReturn = 0.0;
        annualizedReturn = 0.0;
        maxDrawdown = 0.0;
        currentDrawdown = 0.0;
        volatility = 0.0;
        sharpeRatio = 0.0;
        sortinoRatio = 0.0;
        totalTrades = 0;
        winRate = 0.0;
        profitFactor = 0.0;
        avgTradeReturn = 0.0;
    }
};

// Estrutura para configurações de análise
struct PerformanceConfig {
    int historyDepth;         // Profundidade histórica
    double riskFreeRate;      // Taxa livre de risco
    bool useIntraday;         // Usar dados intraday
    int updateInterval;       // Intervalo de atualização
    
    void Reset() {
        historyDepth = 1000;
        riskFreeRate = 0.02;  // 2% ao ano
        useIntraday = true;
        updateInterval = 60;  // 1 minuto
    }
};

// Estrutura para cache de dados
struct PerformanceCache {
    double returns[];         // Array de retornos
    double drawdowns[];       // Array de drawdowns
    datetime timestamps[];    // Timestamps
    int size;                // Tamanho do cache
    
    void Reset() {
        ArrayResize(returns, 0);
        ArrayResize(drawdowns, 0);
        ArrayResize(timestamps, 0);
        size = 0;
    }
};

// Classe principal de monitoramento de performance
class CVolumeFootprintPerformance {
private:
    PerformanceMetrics m_metrics;
    PerformanceConfig m_config;
    PerformanceCache m_cache;
    string m_symbol;
    ENUM_TIMEFRAME m_timeframe;
    
public:
    CVolumeFootprintPerformance(string symbol = NULL, ENUM_TIMEFRAME timeframe = PERIOD_CURRENT) {
        m_symbol = symbol == NULL ? _Symbol : symbol;
        m_timeframe = timeframe;
        m_metrics.Reset();
        m_config.Reset();
        m_cache.Reset();
    }
    
    void Update() {
        // Atualizar métricas de retorno
        UpdateReturns();
        
        // Atualizar métricas de risco
        UpdateRiskMetrics();
        
        // Atualizar métricas de trade
        UpdateTradeMetrics();
        
        // Atualizar cache
        UpdateCache();
    }
    
    PerformanceMetrics* GetMetrics() {
        return &m_metrics;
    }
    
    void SetConfig(PerformanceConfig &config) {
        m_config = config;
    }
    
private:
    void UpdateReturns() {
        // Calcular retornos
        m_metrics.totalReturn = CalculateTotalReturn();
        m_metrics.dailyReturn = CalculateDailyReturn();
        m_metrics.monthlyReturn = CalculateMonthlyReturn();
        m_metrics.annualizedReturn = CalculateAnnualizedReturn();
    }
    
    void UpdateRiskMetrics() {
        // Calcular métricas de risco
        m_metrics.maxDrawdown = CalculateMaxDrawdown();
        m_metrics.currentDrawdown = CalculateCurrentDrawdown();
        m_metrics.volatility = CalculateVolatility();
        m_metrics.sharpeRatio = CalculateSharpeRatio();
        m_metrics.sortinoRatio = CalculateSortinoRatio();
    }
    
    void UpdateTradeMetrics() {
        // Calcular métricas de trade
        m_metrics.totalTrades = CalculateTotalTrades();
        m_metrics.winRate = CalculateWinRate();
        m_metrics.profitFactor = CalculateProfitFactor();
        m_metrics.avgTradeReturn = CalculateAvgTradeReturn();
    }
    
    void UpdateCache() {
        // Atualizar arrays de cache
        ArrayResize(m_cache.returns, m_cache.size + 1);
        ArrayResize(m_cache.drawdowns, m_cache.size + 1);
        ArrayResize(m_cache.timestamps, m_cache.size + 1);
        
        m_cache.returns[m_cache.size] = m_metrics.totalReturn;
        m_cache.drawdowns[m_cache.size] = m_metrics.currentDrawdown;
        m_cache.timestamps[m_cache.size] = TimeCurrent();
        
        m_cache.size++;
        
        // Manter tamanho máximo do cache
        if(m_cache.size > m_config.historyDepth) {
            ArrayCopy(m_cache.returns, m_cache.returns, 0, 1);
            ArrayCopy(m_cache.drawdowns, m_cache.drawdowns, 0, 1);
            ArrayCopy(m_cache.timestamps, m_cache.timestamps, 0, 1);
            m_cache.size--;
        }
    }
    
    double CalculateTotalReturn() {
        double initialBalance = AccountInfoDouble(ACCOUNT_BALANCE);
        double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
        
        if(initialBalance <= 0) return 0.0;
        
        return ((currentEquity - initialBalance) / initialBalance) * 100;
    }
    
    double CalculateDailyReturn() {
        static datetime lastDay = 0;
        static double lastEquity = 0.0;
        
        datetime currentTime = TimeCurrent();
        MqlDateTime dt;
        TimeToStruct(currentTime, dt);
        
        double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
        
        if(lastDay == 0) {
            lastDay = currentTime;
            lastEquity = currentEquity;
            return 0.0;
        }
        
        MqlDateTime lastDt;
        TimeToStruct(lastDay, lastDt);
        
        if(dt.day != lastDt.day) {
            double dailyReturn = ((currentEquity - lastEquity) / lastEquity) * 100;
            lastDay = currentTime;
            lastEquity = currentEquity;
            return dailyReturn;
        }
        
        return 0.0;
    }
    
    double CalculateMonthlyReturn() {
        static datetime lastMonth = 0;
        static double lastEquity = 0.0;
        
        datetime currentTime = TimeCurrent();
        MqlDateTime dt;
        TimeToStruct(currentTime, dt);
        
        double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
        
        if(lastMonth == 0) {
            lastMonth = currentTime;
            lastEquity = currentEquity;
            return 0.0;
        }
        
        MqlDateTime lastDt;
        TimeToStruct(lastMonth, lastDt);
        
        if(dt.mon != lastDt.mon || dt.year != lastDt.year) {
            double monthlyReturn = ((currentEquity - lastEquity) / lastEquity) * 100;
            lastMonth = currentTime;
            lastEquity = currentEquity;
            return monthlyReturn;
        }
        
        return 0.0;
    }
    
    double CalculateAnnualizedReturn() {
        if(m_metrics.monthlyReturn == 0.0) return 0.0;
        
        // Retorno anualizado = (1 + retorno mensal)^12 - 1
        return (MathPow(1 + m_metrics.monthlyReturn/100, 12) - 1) * 100;
    }
    
    double CalculateMaxDrawdown() {
        double peak = 0.0;
        double maxDrawdown = 0.0;
        
        for(int i = 0; i < m_cache.size; i++) {
            if(m_cache.returns[i] > peak) {
                peak = m_cache.returns[i];
            }
            else {
                double drawdown = peak - m_cache.returns[i];
                maxDrawdown = MathMax(maxDrawdown, drawdown);
            }
        }
        
        return maxDrawdown;
    }
    
    double CalculateCurrentDrawdown() {
        double peak = 0.0;
        
        for(int i = 0; i < m_cache.size; i++) {
            peak = MathMax(peak, m_cache.returns[i]);
        }
        
        if(peak <= 0) return 0.0;
        
        return peak - m_metrics.totalReturn;
    }
    
    double CalculateVolatility() {
        if(m_cache.size < 2) return 0.0;
        
        double sum = 0.0;
        double sumSquared = 0.0;
        int count = 0;
        
        for(int i = 1; i < m_cache.size; i++) {
            double returnDiff = m_cache.returns[i] - m_cache.returns[i-1];
            sum += returnDiff;
            sumSquared += returnDiff * returnDiff;
            count++;
        }
        
        if(count < 2) return 0.0;
        
        double variance = (sumSquared - (sum * sum / count)) / (count - 1);
        return MathSqrt(variance);
    }
    
    double CalculateSharpeRatio() {
        if(m_metrics.volatility == 0.0) return 0.0;
        
        double excessReturn = m_metrics.annualizedReturn - m_config.riskFreeRate;
        return excessReturn / m_metrics.volatility;
    }
    
    double CalculateSortinoRatio() {
        if(m_metrics.volatility == 0.0) return 0.0;
        
        double excessReturn = m_metrics.annualizedReturn - m_config.riskFreeRate;
        double downsideDeviation = CalculateDownsideDeviation();
        
        if(downsideDeviation == 0.0) return 0.0;
        
        return excessReturn / downsideDeviation;
    }
    
    double CalculateDownsideDeviation() {
        if(m_cache.size < 2) return 0.0;
        
        double sumSquared = 0.0;
        int count = 0;
        
        for(int i = 1; i < m_cache.size; i++) {
            double returnDiff = m_cache.returns[i] - m_cache.returns[i-1];
            if(returnDiff < 0) {
                sumSquared += returnDiff * returnDiff;
                count++;
            }
        }
        
        if(count < 2) return 0.0;
        
        return MathSqrt(sumSquared / count);
    }
    
    int CalculateTotalTrades() {
        return HistoryDealsTotal();
    }
    
    double CalculateWinRate() {
        int totalTrades = HistoryDealsTotal();
        if(totalTrades == 0) return 0.0;
        
        int winningTrades = 0;
        for(int i = 0; i < totalTrades; i++) {
            if(HistoryDealSelect(i)) {
                if(HistoryDealGetDouble(DEAL_PROFIT) > 0) {
                    winningTrades++;
                }
            }
        }
        
        return (double)winningTrades / totalTrades * 100;
    }
    
    double CalculateProfitFactor() {
        double grossProfit = 0.0;
        double grossLoss = 0.0;
        
        for(int i = 0; i < HistoryDealsTotal(); i++) {
            if(HistoryDealSelect(i)) {
                double profit = HistoryDealGetDouble(DEAL_PROFIT);
                if(profit > 0) {
                    grossProfit += profit;
                }
                else {
                    grossLoss += MathAbs(profit);
                }
            }
        }
        
        if(grossLoss == 0.0) return 0.0;
        
        return grossProfit / grossLoss;
    }
    
    double CalculateAvgTradeReturn() {
        int totalTrades = HistoryDealsTotal();
        if(totalTrades == 0) return 0.0;
        
        double totalProfit = 0.0;
        for(int i = 0; i < totalTrades; i++) {
            if(HistoryDealSelect(i)) {
                totalProfit += HistoryDealGetDouble(DEAL_PROFIT);
            }
        }
        
        return totalProfit / totalTrades;
    }
}; 