import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging

class MarketRegimeDetector:
    """
    SISTEMA OMEGA TIER-0: TRADUÇÃO DIRETA DO 'NUMEIA MARKET REGIME DETECTOR'
    Objetivo: Identificar o estado do mercado (Tendência, Range, Caos)
    Ação: Cortar lote a meio quando 'CHAOTIC' ou bloquear operações (SafeMode).
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("RegimeDetector")
        self.adx_period = 14
        self.volatility_period = 20
        self.chaos_threshold_z = 2.0  # Volatilidade > 2 Desvios Padrões = CAOS
        
    def _calculate_atr(self, df, period):
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
        
    def _calculate_adx(self, df, period):
        # Simplificação de ADX para Regime (Directional Movement)
        up_move = df['high'] - df['high'].shift(1)
        down_move = df['low'].shift(1) - df['low']
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        
        tr = self._calculate_atr(df, 1)
        
        plus_di = 100 * (pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / tr.ewm(alpha=1/period, adjust=False).mean())
        minus_di = 100 * (pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / tr.ewm(alpha=1/period, adjust=False).mean())
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        return adx.values[-1]

    def detect_regime(self, symbol) -> dict:
        """
        Retorna o dicionário com o regime atual e o Fator de Risco
        """
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
        if rates is None or len(rates) < self.volatility_period * 2:
            return {"state": "UNKNOWN", "risk_factor": 1.0, "reason": "No Data"}
            
        df = pd.DataFrame(rates)
        
        # 1. Medir Volatilidade Atual vs Histórica (Z-Score)
        atr_series = self._calculate_atr(df, self.volatility_period)
        current_atr = atr_series.iloc[-1]
        historical_atr_mean = atr_series.mean()
        historical_atr_std = atr_series.std()
        
        if historical_atr_std == 0:
            vol_z_score = 0
        else:
            vol_z_score = (current_atr - historical_atr_mean) / historical_atr_std
            
        # 2. Medir Força da Tendência (ADX)
        current_adx = self._calculate_adx(df, self.adx_period)
        
        # 3. Classificação de Regime (Decision Engine)
        state = "RANGING"
        risk_factor = 1.0
        reason = "Normal Consolidation"
        
        if vol_z_score > self.chaos_threshold_z:
            state = "CHAOTIC"
            risk_factor = 0.5  # Cortar lote a meio! Proteção tipo Safemode/Numeia
            reason = f"Extreme Volatility (Z: {vol_z_score:.2f})"
        elif current_adx > 25:
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            if df['close'].iloc[-1] > sma_20:
                state = "TRENDING_UP"
            else:
                state = "TRENDING_DOWN"
            risk_factor = 1.0
            reason = f"Strong Trend (ADX: {current_adx:.1f})"
        else:
            state = "RANGING"
            risk_factor = 1.0
            reason = f"Weak Trend (ADX: {current_adx:.1f})"
            
        return {
            "state": state,
            "risk_factor": risk_factor,
            "volatility_z": round(vol_z_score, 2),
            "adx": round(current_adx, 2),
            "reason": reason
        }
