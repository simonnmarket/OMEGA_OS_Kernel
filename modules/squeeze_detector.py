import numpy as np
from collections import deque
from typing import Dict, List, Optional

class SqueezeDetector:
    """
    Motor de pós-combustão para Detecção de Squeeze (Adaptado para XAUUSD/FOREX)
    Substitui Short Interest por Volume Imbalance (Delta Estimado) e Aceleração Parabólica.
    Ativa impulso adicional quando a pressão de um lado se exaure de forma crítica.
    """
    
    def __init__(self, window: int = 20):
        self.window = window
        self.price_history = deque(maxlen=window)
        self.volume_history = deque(maxlen=window)
        self.delta_history = deque(maxlen=window)
        
        self.squeeze_score = 0
        self.afterburner_active = False

    def update(self, candle: Dict[str, float]) -> Dict:
        """
        Calcula o score de Squeeze (0 a 100) baseado em Imbalance exausto.
        candle: {'open': float, 'high': float, 'low': float, 'close': float, 'volume': float}
        """
        # Adicionar dados ao histórico
        self.price_history.append(candle['close'])
        if candle['volume'] > 0:
            self.volume_history.append(candle['volume'])
        else:
            self.volume_history.append(1e-6)

        # Estimativa de Delta (Volume de Compra vs Venda aproximado pelo formato do candle)
        body = candle['close'] - candle['open']
        range_high_low = candle['high'] - candle['low']
        
        if range_high_low > 0:
            delta_ratio = body / range_high_low
        else:
            delta_ratio = 0.0
            
        estimated_delta = delta_ratio * candle['volume']
        self.delta_history.append(estimated_delta)

        # Se não tiver histórico suficiente, não há squeeze
        if len(self.price_history) < self.window:
            return {
                "squeeze_score": 0.0,
                "afterburner_active": False,
                "boost_multiplier": 1.0,
                "components": {}
            }

        # 1. Volume Imbalance Exhaustion (40%)
        # Se os deltas recentes foram muito altos em uma direção, o "elastico" está muito esticado.
        sum_delta = np.sum(list(self.delta_history)[-5:]) # Delta dos últimos 5 candles
        avg_volume_recent = np.mean(list(self.volume_history)[-5:])
        imbalance_ratio = abs(sum_delta) / (avg_volume_recent * 5 + 1e-6)
        
        score = 0
        if imbalance_ratio > 0.8:  # 80% do volume recente empurrou em uma só direção
            score += 40
        elif imbalance_ratio > 0.6:
            score += 30
        elif imbalance_ratio > 0.4:
            score += 20

        # 2. Volume Ratio - Clímax de Volume (30%)
        # Um squeeze acontece após ou durante um pico explosivo de volume
        avg_volume_total = np.mean(self.volume_history)
        current_volume = candle['volume']
        volume_ratio = current_volume / (avg_volume_total + 1e-6)
        
        if volume_ratio > 3.0:
            score += 30
        elif volume_ratio > 2.0:
            score += 20
        elif volume_ratio > 1.5:
            score += 10

        # 3. Price Velocity - Aceleração Parabólica (30%)
        # Velocidade medida pelo desvio padrão do preço (Stretch)
        price_std = np.std(self.price_history) or 1e-6
        price_change = abs(self.price_history[-1] - self.price_history[-5]) # Mudança nos ultimos 5
        velocity_z = price_change / price_std

        if velocity_z > 3.0:
            score += 30
        elif velocity_z > 2.0:
            score += 20
        elif velocity_z > 1.0:
            score += 10

        self.squeeze_score = score
        self.afterburner_active = score > 70

        # Calcular Boost Multiplier
        if score >= 90:
            boost = 3.0
        elif score >= 80:
            boost = 2.5
        elif score >= 70:
            boost = 2.0
        elif score >= 60:
            boost = 1.5
        else:
            boost = 1.0

        return {
            "squeeze_score": score,
            "afterburner_active": self.afterburner_active,
            "boost_multiplier": boost,
            "components": {
                "imbalance_ratio": imbalance_ratio,
                "volume_ratio": volume_ratio,
                "velocity_z": velocity_z
            }
        }
