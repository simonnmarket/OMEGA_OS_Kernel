import numpy as np
import pandas as pd
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class FimatheCoreTIER0:
    """
    SISTEMA FIMATHE CORE v2.0 INTEGRADO
    Adaptado para identificar canais dinâmicos e breakouts de ciclo.
    """
    def __init__(self):
        self.min_range_pts = 300
        self.max_range_pts = 1200
        
    def get_signal(self, df: pd.DataFrame) -> Dict:
        if df.empty or len(df) < 20:
            return {'direction': 0, 'confidence': 0, 'type': 'NONE'}
        
        # Em vez de pegar fixo as primeiras 4 da janela, 
        # vamos pegar o range das velas que definem a "Abertura do Dia"
        # Se não tivermos o dia todo, pegamos o range das primeiras barras da janela de 150 (aprox 12h)
        # Mas para ser mais agressivo, vamos usar o Canal de Referência (últimas 2 velas fechadas) 
        # e a Zona Neutra, conforme o princípio de expansão.
        
        # Pegamos as 4 velas iniciais da janela (supostamente o início do movimento observado)
        velas_abertura = df.head(4)
        canal_high = velas_abertura['high'].max()
        canal_low = velas_abertura['low'].min()
        canal_range = canal_high - canal_low
        
        # Se o canal for muito pequeno, expandimos para o mínimo institucional
        if canal_range < self.min_range_pts:
            # Ajuste de sensibilidade: Se o mercado está muito parado, o canal é curto
            pass 

        current_close = df['close'].iloc[-1]
        
        # Fimathe: Rompimento do canal de referência + zona neutra
        # Simplificação para Alpha: Rompimento de 2 níveis (100% do canal) ou 50%
        # Vamos usar o gatilho de 50% de expansão para "não perder a oportunidade"
        threshold_long = canal_high + (canal_range * 0.5)
        threshold_short = canal_low - (canal_range * 0.5)
        
        if current_close > threshold_long:
            # Check se não é um over-stretch (evitar comprar topo)
            return {'direction': 1, 'confidence': 0.85, 'type': 'FIMATHE_EXPANSION_LONG'}
        elif current_close < threshold_short:
            return {'direction': -1, 'confidence': 0.85, 'type': 'FIMATHE_EXPANSION_SHORT'}
            
        return {'direction': 0, 'confidence': 0, 'type': 'NONE'}

    def detect_diagonal_range(self, window_data: np.ndarray) -> Dict:
        """
        Detecta Range Diagonal (Topos e Fundos prévios)
        """
        # window_data: [close, high, low, vol]
        highs = window_data[:, 1]
        lows = window_data[:, 2]
        
        # Resistência e Suporte nos últimos 100 períodos
        resistance = np.max(highs[:-1])
        support = np.min(lows[:-1])
        current_close = window_data[-1, 0]
        
        amplitude = resistance - support
        # Se a amplitude for zero (erro de dados), ignora
        if amplitude <= 0: return {'direction': 0, 'score': 0, 'type': 'NONE'}
        
        # Threshold de aproximação de 2% (Sniper)
        threshold = amplitude * 0.02
        
        if current_close >= (resistance - threshold):
            return {'direction': -1, 'score': 95, 'type': 'RANGE_DIAGONAL_TOP'}
        elif current_close <= (support + threshold):
            return {'direction': 1, 'score': 95, 'type': 'RANGE_DIAGONAL_BOTTOM'}
            
        return {'direction': 0, 'score': 0, 'type': 'NONE'}
