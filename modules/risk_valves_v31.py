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
        # CEO 2026-05-14 FIX: TP1 antecipado 1.0→0.7 ATR — fecha 50% mais cedo
        # Motivo: XAUUSD atingia TP1 mas revertia antes do próximo ciclo (20s polling)
        self.levels = [
            {"atr": 0.7, "fraction": 0.50, "description": "Pesados", "executed": False},
            {"atr": 1.5, "fraction": 0.30, "description": "Medios", "executed": False},
            {"atr": 2.5, "fraction": 0.15, "description": "Leves", "executed": False},
            {"atr": 4.0, "fraction": 0.05, "description": "Residual", "executed": False}
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
    
    # CEO 2026-05-14 FIX: breakeven autónomo a 0.4× ATR (antes 0.8×)
    # Motivo: XAUUSD reverte 20pts em 5s; polling 20s não chegava a tempo com 0.8×ATR
    # Com 0.4× ATR o breakeven dispara 2× mais cedo → protecção antes da reversão
    BREAKEVEN_ATR_TRIGGER: float = 0.4
    MIN_LOT: float = 0.01  # mínimo MT5

    def check_partials(self, current_price: float, atr_value: float) -> List[Dict]:
        orders = []
        if self.entry_price is None or self.direction == 0:
            return orders

        # Calcular movimento em múltiplos de ATR
        if self.direction == 1:
            move_atr = (current_price - self.entry_price) / (atr_value + 1e-10)
        else:
            move_atr = (self.entry_price - current_price) / (atr_value + 1e-10)

        # ── FIX CEO 2026-05-14: BREAKEVEN AUTÓNOMO ──────────────────────────────
        # Quando move >= BREAKEVEN_ATR_TRIGGER, mover SL para entry mesmo sem partial.
        # Previne reversão de posição lucrativa para perda sem nenhuma captura de lucro.
        # Este flag é rastreado no 1º level para não repetir após executado.
        _breakeven_due = (
            move_atr >= self.BREAKEVEN_ATR_TRIGGER
            and not getattr(self, "_breakeven_sent", False)
        )
        if _breakeven_due:
            orders.append({
                "action": "MOVE_SL_TO_ENTRY",
                "reason": f"Breakeven autonomo {move_atr:.2f}x ATR (trigger={self.BREAKEVEN_ATR_TRIGGER}x)",
                "move_atr": move_atr
            })
            self._breakeven_sent = True

        for level in self.levels:
            if not level["executed"] and move_atr >= level["atr"]:
                close_lots = round(self.remaining_lots * level["fraction"], 2)
                close_lots = min(close_lots, self.remaining_lots)

                # ── FIX CEO 2026-05-14: verificação lote mínimo ─────────────────
                # Se close_lots < MIN_LOT, não enviar ordem parcial (MT5 rejeita).
                # O breakeven autónomo acima ainda protege a posição.
                # ── FIX CEO BTCUSD/micro-lote: não marcar nível como executado se
                # não houve fecho — antes consumia o nível e nunca mais tentava.
                if close_lots < self.MIN_LOT and self.remaining_lots >= self.MIN_LOT:
                    close_lots = min(self.MIN_LOT, self.remaining_lots)
                if close_lots >= self.MIN_LOT:
                    orders.append({
                        "action": "CLOSE_PARTIAL",
                        "lots": close_lots,
                        "reason": f"Nivel {level['atr']}x ATR - {level['description']}",
                        "move_atr": move_atr
                    })
                    self.remaining_lots -= close_lots
                    level["executed"] = True
                # Se ainda < MIN_LOT: não marcar executed — re-tenta no próximo ciclo

        # Move SL para breakeven também após 1ª parcial executada (redundância segura)
        if any(o["action"] == "CLOSE_PARTIAL" for o in orders):
            if not any(o["action"] == "MOVE_SL_TO_ENTRY" for o in orders):
                orders.append({"action": "MOVE_SL_TO_ENTRY", "reason": "Breakeven apos parcial"})

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
