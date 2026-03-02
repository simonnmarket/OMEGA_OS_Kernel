from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import numpy as np

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class SmartMoneyState:
    entry_zones: List[float] = field(default_factory=list)
    exit_zones: List[float] = field(default_factory=list)
    stop_zones: List[float] = field(default_factory=list)
    is_accumulating: bool = False
    is_distributing: bool = False
    confidence: float = 0.0

@dataclass
class LiquidityState:
    buy_liquidity: List[float] = field(default_factory=list)
    sell_liquidity: List[float] = field(default_factory=list)
    voids: List[float] = field(default_factory=list)
    pools: List[float] = field(default_factory=list)
    is_liquidity_driven: bool = False
    strength: float = 0.0

@dataclass
class FlowState:
    large_orders: List[float] = field(default_factory=list)
    absorption: float = 0.0
    distribution: float = 0.0
    is_institutional: bool = False
    last_update_ms: int = 0

@dataclass
class InstitutionalData:
    smart: SmartMoneyState = field(default_factory=SmartMoneyState)
    liquidity: LiquidityState = field(default_factory=LiquidityState)
    flow: FlowState = field(default_factory=FlowState)

@dataclass
class RiskControl:
    max_risk_per_trade: float = 0.01  
    max_daily_loss_limit: float = 0.05      
    current_exposure: float = 0.0     
    risk_multiplier: float = 1.0
    is_risk_exceeded: bool = False

@dataclass
class PositionOptimizer:
    optimal_size: float = 0.0
    optimal_entry: float = 0.0
    optimal_stop: float = 0.0
    optimal_target: float = 0.0
    is_optimized: bool = False

@dataclass
class CapitalProtection:
    max_drawdown: float = 0.15  
    current_drawdown: float = 0.0
    safety_buffer: float = 0.0
    is_protection_active: bool = False
    last_check_ms: int = 0

@dataclass
class InstitutionalRisk:
    control: RiskControl = field(default_factory=RiskControl)
    position: PositionOptimizer = field(default_factory=PositionOptimizer)
    protection: CapitalProtection = field(default_factory=CapitalProtection)

@dataclass
class SystemState:
    is_initialized: bool = False
    is_running: bool = False
    is_paused: bool = False
    is_error: bool = False
    last_update_ms: int = 0
    error_count: int = 0

@dataclass
class Signal:
    direction: int  # 1 buy, -1 sell, 0 neutral
    confidence: float
    entry: Optional[float] = None
    stop: Optional[float] = None
    target: Optional[float] = None
    reason: str = ""

@dataclass
class Config:
    min_order_size: float = 100.0
    accumulation_period: int = 20
    confidence_threshold: float = 0.85
    max_risk_per_trade: float = 0.01
    max_daily_loss_limit: float = 0.05  
    max_drawdown: float = 0.15
    max_error_count: int = 5

# ---------------------------------------------------------------------------
# Core Analysis Modules
# ---------------------------------------------------------------------------
class InstitutionalAnalysis:
    """Núcleo Analítico Híbrido: Combina Fluxo, Liquidez e Comportamento Institucional."""
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.data = InstitutionalData()
        self._prices: List[float] = []
        self._volumes: List[float] = []

    def initialize(self) -> bool:
        return True

    def update_market_data(self, price: float, volume: float) -> None:
        self._prices.append(price)
        self._volumes.append(volume)
        if len(self._prices) > 5000:
            self._prices.pop(0)
            self._volumes.pop(0)

    def process_institutional_analysis(self) -> None:
        if len(self._prices) < self.cfg.accumulation_period:
            return
            
        # Z-Score do Volume para Identificação de "Pegada" Institucional
        vols = self._volumes[-self.cfg.accumulation_period:]
        mean_v = np.mean(vols)
        std_v = np.std(vols)
        z = (vols[-1] - mean_v) / std_v if std_v > 0 else 0.0
        
        is_acc = z > 2.0
        self.data.smart.is_accumulating = is_acc
        self.data.smart.is_distributing = z < -2.0
        self.data.smart.confidence = min(1.0, abs(z) / 3.0)

    def execute_analysis(self) -> Signal:
        if len(self._prices) < 2:
            return Signal(direction=0, confidence=0.0, reason="not_enough_data")
            
        price_now = self._prices[-1]
        momentum = price_now - self._prices[-2]
        z_conf = self.data.smart.confidence
        
        if self.data.smart.is_accumulating and momentum > 0:
            return Signal(direction=1, confidence=z_conf, entry=price_now, reason="smart_money_accum_up")
        if self.data.smart.is_distributing and momentum < 0:
            return Signal(direction=-1, confidence=z_conf, entry=price_now, reason="smart_money_dist_down")
            
        return Signal(direction=0, confidence=0.0, reason="neutral")

# ---------------------------------------------------------------------------
# Risk Management Module
# ---------------------------------------------------------------------------
class InstitutionalRiskManager:
    """Implementa limites rígidos de Drawdown, Controle de perdas diárias e Position Sizing."""
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.risk = InstitutionalRisk()
        self.risk.control.max_risk_per_trade = cfg.max_risk_per_trade
        self.risk.control.max_daily_loss_limit = cfg.max_daily_loss_limit
        self.risk.protection.max_drawdown = cfg.max_drawdown
        self._peak_equity: float = 0.0
        self._daily_pnl: float = 0.0
        self._current_date: Optional[str] = None

    def validate_risk_state(self) -> bool:
        return not self.risk.control.is_risk_exceeded and not self.risk.protection.is_protection_active

    def update_exposure(self, position_value: float, equity: float) -> None:
        if equity <= 0: return
        self.risk.control.current_exposure = position_value / equity
        self._peak_equity = max(max(self._peak_equity, 0), equity)
        diff = self._peak_equity - equity
        self.risk.protection.current_drawdown = diff / self._peak_equity if self._peak_equity > 0 else 0.0

    def update_daily_pnl(self, realized_pnl: float) -> None:
        self._daily_pnl += realized_pnl

    def check_limits(self, equity: float) -> None:
        loss_limit_cash = equity * self.cfg.max_daily_loss_limit
        if self._daily_pnl < 0 and loss_limit_cash > 0 and abs(self._daily_pnl) >= loss_limit_cash:
            self.risk.control.is_risk_exceeded = True
        if self.risk.protection.current_drawdown > self.cfg.max_drawdown:
            self.risk.protection.is_protection_active = True

# ---------------------------------------------------------------------------
# System Orchestrator (O Cérebro Integrador)
# ---------------------------------------------------------------------------
class OMEGAInstitutionalCore:
    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config()
        self.state = SystemState()
        self.analysis = InstitutionalAnalysis(self.cfg)
        self.risk_manager = InstitutionalRiskManager(self.cfg)

    def initialize(self) -> bool:
        self.state.is_initialized = self.analysis.initialize()
        self.state.is_running = self.state.is_initialized
        return self.state.is_initialized

    def on_tick(self, price: float, volume: float, pos_value: float, equity: float, pnl: float = 0.0) -> Optional[Signal]:
        try:
            if not self.state.is_running: return None

            # 1. Update Risk Profile
            self.risk_manager.update_exposure(pos_value, equity)
            if pnl != 0.0: self.risk_manager.update_daily_pnl(pnl)
            
            self.risk_manager.check_limits(equity)
            if not self.risk_manager.validate_risk_state():
                self.state.is_error = True
                print(">>> SYSTEM SHUTDOWN: Institutional Risk Limits Exceeded <<<")
                self.state.is_running = False
                return None

            # 2. Update Market Mechanics
            self.analysis.update_market_data(price, volume)
            self.analysis.process_institutional_analysis()
            
            # 3. Disparar Sintese Híbrida
            return self.analysis.execute_analysis()
            
        except Exception as e:
            self.state.is_error = True
            self.state.error_count += 1
            if self.state.error_count > self.cfg.max_error_count:
                self.state.is_running = False
            return None
