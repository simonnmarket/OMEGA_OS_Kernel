import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import argparse

class WalkForwardValidator:
    """Validação Walk-Forward OMEGA (v6.4) com purge period"""
    def __init__(self, n_folds=5, train_pct=0.7, purge_days=7):
        self.n_folds = n_folds
        self.train_pct = train_pct
        self.purge_days = purge_days

    def create_walk_forward_folds(self, data: pd.DataFrame):
        total_points = len(data)
        fold_size = total_points // self.n_folds
        folds = []
        for i in range(self.n_folds):
            fold_start = i * fold_size
            fold_end = (i + 1) * fold_size if i < self.n_folds - 1 else total_points
            fold_data = data.iloc[fold_start:fold_end].copy()
            train_size = int(len(fold_data) * self.train_pct)
            train = fold_data.iloc[:train_size].copy()
            purge_points = self.purge_days * 1440 
            test_start = train_size + purge_points
            if test_start >= len(fold_data):
                test_start = train_size + (purge_points // 2)
            test = fold_data.iloc[test_start:].copy()
            if len(test) < 100: continue
            folds.append((train, test))
        return folds
    
    def calculate_fold_performance(self, test_data: pd.DataFrame, symbol: str):
        if len(test_data) < 10: return {'error': 'INSUFFICIENT_DATA'}
        returns = test_data['close'].pct_change().dropna()
        if len(returns) == 0 or returns.std() == 0: return {'error': 'ZERO_VOLATILITY'}
        total_return = (test_data['close'].iloc[-1] / test_data['close'].iloc[0] - 1) * 100
        sharpe = returns.mean() / returns.std() * np.sqrt(1440)
        cumulative = test_data['close'] / test_data['close'].cummax()
        max_dd = (1 - cumulative.min()) * 100
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        return {
            'sharpe_ratio': float(sharpe), 'total_return': float(total_return),
            'max_drawdown': float(max_dd), 'win_rate': float(win_rate),
            'num_trades': len(returns), 'error': None
        }

    def validate_symbol(self, symbol: str, data_file: str):
        print(f"\n[VALIDATING] {symbol}")
        try:
            data = pd.read_csv(data_file)
            data['datetime'] = pd.to_datetime(data['time'], unit='s') if 'time' in data.columns else pd.to_datetime(data['datetime'])
        except Exception as e:
            print(f"Erro ao carregar {data_file}: {e}")
            return {'symbol': symbol, 'error': str(e)}

        folds = self.create_walk_forward_folds(data)
        fold_results = []
        for i, (train, test) in enumerate(folds, 1):
            perf = self.calculate_fold_performance(test, symbol)
            fold_results.append({'fold': i, 'performance': perf})
            
        valid_results = [f['performance'] for f in fold_results if f['performance'].get('error') is None]
        sharpes = [f['sharpe_ratio'] for f in valid_results]
        avg_sharpe = np.mean(sharpes) if sharpes else 0.0
        consistency = 1 - min(np.std(sharpes)/abs(np.mean(sharpes)), 1.0) if sharpes and abs(np.mean(sharpes)) > 0.01 else 0.0
        
        print(f"  Avg Sharpe: {avg_sharpe:.2f} | Consistency: {consistency:.2f}")
        return {
            'symbol': symbol, 'fold_results': fold_results,
            'avg_sharpe': float(avg_sharpe), 'consistency_score': float(consistency),
            'num_folds': len(fold_results), 'valid_folds': len(valid_results)
        }

if __name__ == '__main__':
    print('OMEGA Walk-Forward Validation Engine v6.4 (StandBy)')
