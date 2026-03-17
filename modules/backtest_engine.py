import numpy as np
from typing import List, Dict

class BacktestMetricsEngine:
    """
    Motor de Extracao de Metricas Fiduciarias Institucionais
    Conforme exigências do CQO (Chief Quant Officer)
    """

    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity_curve = [initial_balance]
        self.trades = []
        self.peak_equity = initial_balance
        self.max_drawdown = 0.0

    def add_trade(self, profit: float, is_win: bool):
        """Registra um trade fechado"""
        self.balance += profit
        self.equity_curve.append(self.balance)
        self.trades.append(profit)

        if self.balance > self.peak_equity:
            self.peak_equity = self.balance
            
        dd = (self.peak_equity - self.balance) / self.peak_equity if self.peak_equity > 0 else 0
        if dd > self.max_drawdown:
            self.max_drawdown = dd

    def compute_metrics(self) -> Dict:
        """Calcula todas as métricas exigidas pelo conselho"""
        total_trades = len(self.trades)
        if total_trades == 0:
            return {"error": "Nenhum trade registrado"}

        wins = [t for t in self.trades if t > 0]
        losses = [t for t in self.trades if t <= 0]
        
        win_rate = (len(wins) / total_trades) * 100
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        net_profit = gross_profit - gross_loss
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        expectancy = net_profit / total_trades

        # Sharpe Ratio (Simplificado: Retorno diario vs risco)
        # Assumindo cada trade como um passo 'diário' ou 'por evento'
        returns = np.array(self.trades) / self.initial_balance
        avg_return = np.mean(returns)
        std_return = np.std(returns) if len(returns) > 1 else 1e-6
        # Ajuste anualizado hipotetico, mas para HFT usamos o evento base
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252 * 24) if std_return > 0 else 0

        calmar_ratio = (net_profit / self.initial_balance) / self.max_drawdown if self.max_drawdown > 0 else float('inf')
        recovery_factor = net_profit / (self.max_drawdown * self.peak_equity) if self.max_drawdown > 0 else float('inf')

        return {
            "Total Trades": total_trades,
            "Win Rate (%)": win_rate,
            "Net Profit ($)": net_profit,
            "Max Drawdown (%)": self.max_drawdown * 100,
            "Profit Factor": profit_factor,
            "Expectancy ($/trade)": expectancy,
            "Sharpe Ratio": sharpe_ratio,
            "Calmar Ratio": calmar_ratio,
            "Recovery Factor": recovery_factor,
            "Final Balance ($)": self.balance
        }

def walk_forward_split(data: list, k: int = 5):
    """
    Divide os dados em K-Folds para Walk-Forward
    70% In-Sample, 30% Out-of-Sample para cada fold
    """
    fold_size = len(data) // k
    folds = []
    
    for i in range(k):
        start_idx = i * fold_size
        end_idx = start_idx + fold_size if i < k - 1 else len(data)
        fold_data = data[start_idx:end_idx]
        
        is_size = int(len(fold_data) * 0.7)
        is_data = fold_data[:is_size]
        oos_data = fold_data[is_size:]
        
        folds.append({"IS": is_data, "OOS": oos_data})
        
    return folds
