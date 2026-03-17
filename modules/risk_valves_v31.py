import json
import hashlib
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timezone
import numpy as np

class HardVolatilityTrailingStopGeometric:
    """
    VÁLVULA I: Hard Volatility Trailing Stop (Geométrico)
    Implementação Tier-0 para OMEGA OS V3.2
    """
    def __init__(self, atr_multiplier: float = 3.0, min_multiplier: float = 1.0):
        self.atr_multiplier = atr_multiplier
        self.min_multiplier = min_multiplier
        self.entry_price: Optional[float] = None
        self._peak_price: Optional[float] = None
        self._trailing_sl: Optional[float] = None
        
    def update(self, current_price: float, atr_value: float, direction: int) -> Tuple[Optional[float], bool]:
        if direction == 0:
            return None, False
            
        if self.entry_price is None:
            self.entry_price = current_price
            self._peak_price = current_price
            
        # Calcular lucro atual em múltiplos de ATR
        if direction == 1:
            profit_ratio = (current_price - self.entry_price) / (atr_value + 1e-10)
        else:
            profit_ratio = (self.entry_price - current_price) / (atr_value + 1e-10)
            
        # Multiplier geométrico: quanto maior o lucro, mais próximo o stop
        if profit_ratio > 0:
            geometric_multiplier = max(
                self.min_multiplier,
                self.atr_multiplier * np.exp(-0.3 * profit_ratio)
            )
        else:
            geometric_multiplier = self.atr_multiplier
            
        stop_distance = atr_value * geometric_multiplier
        
        # Atualiza o pico
        if direction == 1 and current_price > self._peak_price:
            self._peak_price = current_price
        elif direction == -1 and current_price < self._peak_price:
            self._peak_price = current_price
            
        # Compara trailing e dispara exit se necessário
        if direction == 1:
            new_sl = self._peak_price - stop_distance
            if self._trailing_sl is None or new_sl > self._trailing_sl:
                self._trailing_sl = new_sl
            trigger_exit = current_price <= self._trailing_sl
        else:
            new_sl = self._peak_price + stop_distance
            if self._trailing_sl is None or new_sl < self._trailing_sl:
                self._trailing_sl = new_sl
            trigger_exit = current_price >= self._trailing_sl
            
        return self._trailing_sl, trigger_exit

class ProgressivePartialCloseComplete:
    """
    VÁLVULA II: Parciais Progressivas Completas
    Implementação Tier-0 para OMEGA OS V3.2
    """
    def __init__(self):
        self.levels = [
            {"atr": 1.0, "fraction": 0.50, "description": "Pesados", "executed": False},
            {"atr": 2.0, "fraction": 0.30, "description": "Medios", "executed": False},
            {"atr": 3.0, "fraction": 0.15, "description": "Leves", "executed": False},
            {"atr": 5.0, "fraction": 0.05, "description": "Residual", "executed": False}
        ]
        self.entry_price: Optional[float] = None
        self.initial_lots: Optional[float] = None
        self.direction: Optional[int] = None
        self.remaining_lots: Optional[float] = None
        
    def initialize_position(self, entry_price: float, lots: float, direction: int):
        self.entry_price = entry_price
        self.initial_lots = lots
        self.direction = direction
        self.remaining_lots = lots
        for level in self.levels:
            level["executed"] = False
    
    def check_partials(self, current_price: float, atr_value: float) -> List[Dict]:
        orders = []
        if self.entry_price is None or self.direction == 0:
            return orders
            
        # Calcular movimento em múltiplos de ATR
        if self.direction == 1:
            move_atr = (current_price - self.entry_price) / (atr_value + 1e-10)
        else:
            move_atr = (self.entry_price - current_price) / (atr_value + 1e-10)
            
        for level in self.levels:
            if not level["executed"] and move_atr >= level["atr"]:
                # Calcular lotes a fechar usando a fração dos lotes restantes (como sugeriu o analista superior)
                close_lots = self.remaining_lots * level["fraction"]
                close_lots = min(close_lots, self.remaining_lots)
                
                if close_lots > 0:
                    orders.append({
                        "action": "CLOSE_PARTIAL",
                        "lots": close_lots,
                        "reason": f"Nivel {level['atr']}x ATR - {level['description']}",
                        "move_atr": move_atr
                    })
                    self.remaining_lots -= close_lots
                level["executed"] = True
                
        # Move stop to breakeven após a 1a parcial
        if len(orders) > 0 and any(level["executed"] for level in self.levels[:1]):
            orders.append({"action": "MOVE_SL_TO_ENTRY", "reason": "Breakeven apos 1a parcial"})
            
        return orders

class EmergencyTailRiskHalt:
    """
    VÁLVULA III: Emergency Tail-Risk Stop-Loss (Hard Halt)
    Implementação Tier-0 para OMEGA OS V3.2
    """
    def __init__(self, max_drawdown_per_event: float = 0.03, cooldown_hours: int = 24):
        self.max_dd_per_event = max_drawdown_per_event
        self.cooldown_hours = cooldown_hours
        self._halt_active = False
        self._halt_timestamp = None
        self.peak_equity = None
        self.starting_equity = None
        
    def set_starting_equity(self, equity: float):
        self.starting_equity = equity
        self.peak_equity = equity
        self._halt_active = False
    
    def check_tail_risk(self, current_equity: float) -> Tuple[bool, Dict]:
        if self._halt_active: return True, {"status": "HALT_ACTIVE"}
        if self.peak_equity is None: return False, {"status": "NOT_INITIALIZED"}
        
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            
        event_drawdown = (self.peak_equity - current_equity) / self.peak_equity
        if event_drawdown >= self.max_dd_per_event:
            self._halt_active = True
            self._halt_timestamp = datetime.now(timezone.utc)
            return True, {
                "status": "HALT_TRIGGERED",
                "peak_equity": self.peak_equity,
                "current_equity": current_equity,
                "drawdown": event_drawdown * 100,
                "threshold": self.max_dd_per_event * 100
            }
            
        return False, {"status": "OK", "drawdown": event_drawdown * 100}
