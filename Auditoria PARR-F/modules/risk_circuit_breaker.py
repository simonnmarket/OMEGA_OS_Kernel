#!/usr/bin/env python3
"""
risk_circuit_breaker.py v1.0
Módulo P-01 — Especificação do Conselho OMEGA-CONSELHO-DEMO-20260322
"""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("OMEGA_CIRCUIT_BREAKER")

class CircuitBreakerConfig:
    def __init__(
        self,
        daily_loss_threshold_pct: float = -3.5,
        warning_threshold_pct: float = -1.0,
        alert_threshold_pct: float = -2.0,
        trip_callback: Optional[Callable] = None
    ):
        self.daily_loss_threshold_pct = daily_loss_threshold_pct
        self.warning_threshold_pct = warning_threshold_pct
        self.alert_threshold_pct = alert_threshold_pct
        self.trip_callback = trip_callback

    def get_hash(self) -> str:
        import hashlib
        data = f"{self.daily_loss_threshold_pct}|{self.warning_threshold_pct}|{self.alert_threshold_pct}"
        return hashlib.sha3_256(data.encode()).hexdigest()[:8]

class CircuitBreakerTracker:
    def __init__(self):
        self.anchor_equity = 0.0
        self.current_equity = 0.0
        self.daily_peak = 0.0
        self.date = None
        self.state = "CLOSED" # CLOSED (Trading allowed) ou OPEN (Halted)
        self.trigger_time = None
        self.alerts_sent = []

    def to_dict(self) -> Dict:
        return {
            "anchor_equity": self.anchor_equity,
            "current_equity": self.current_equity,
            "daily_return_pct": round(((self.current_equity / self.anchor_equity) - 1.0) * 100, 4) if self.anchor_equity > 0 else 0,
            "gross_loss_intraday_pct": round(((self.anchor_equity - self.current_equity) / self.anchor_equity) * 100, 4) if self.anchor_equity > 0 else 0,
            "state": self.state,
            "date": self.date,
            "trigger_time": self.trigger_time,
            "alerts_sent": self.alerts_sent
        }

class RiskCircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.tracker = CircuitBreakerTracker()

    def initialize_day(self, anchor_equity: float):
        self.tracker.anchor_equity = anchor_equity
        self.tracker.current_equity = anchor_equity
        self.tracker.daily_peak = anchor_equity
        self.tracker.date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.tracker.state = "CLOSED"
        self.tracker.trigger_time = None
        self.tracker.alerts_sent = []
        logger.info(f"Circuit Breaker Initialized: Date={self.tracker.date} | Anchor=${anchor_equity:,.2f}")

    def update_equity(self, current_equity: float, pnl_change: float = 0.0):
        if self.tracker.state == "OPEN":
            return False, "CIRCUIT_BREAKER_OPEN_TRADING_HALTED", self.tracker.to_dict()

        self.tracker.current_equity = current_equity
        if current_equity > self.tracker.daily_peak:
            self.tracker.daily_peak = current_equity

        status = self.tracker.to_dict()
        loss_pct = -status['daily_return_pct'] # Converter retorno negativo em perda positiva

        # Checar Gatilho Crítico (-3.5%)
        if loss_pct >= abs(self.config.daily_loss_threshold_pct):
            self.tracker.state = "OPEN"
            self.tracker.trigger_time = datetime.now(timezone.utc).isoformat()
            self._trigger_alert("OPEN", loss_pct)
            return False, "CRITICAL_LOSS_LIMIT_REACHED_HALTING", self.tracker.to_dict()

        # Checar Alertas (Warning/Alert)
        if loss_pct >= abs(self.config.alert_threshold_pct) and "ALERT" not in self.tracker.alerts_sent:
            self.tracker.alerts_sent.append("ALERT")
            self._trigger_alert("ALERT", loss_pct)
        elif loss_pct >= abs(self.config.warning_threshold_pct) and "WARNING" not in self.tracker.alerts_sent:
            self.tracker.alerts_sent.append("WARNING")
            self._trigger_alert("WARNING", loss_pct)

        return True, "TRADING_ALLOWED", self.tracker.to_dict()

    def _trigger_alert(self, level: str, loss_pct: float):
        logger.warning(f"CIRCUIT BREAKER ALERT [{level}]: Current Loss {loss_pct:.2f}%")
        if self.config.trip_callback:
            try:
                self.config.trip_callback(level, loss_pct)
            except:
                pass

    def get_status_report(self) -> Dict:
        return self.tracker.to_dict()

    def export_status(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.get_status_report(), f, indent=2)

def smoke_test_circuit_breaker():
    config = CircuitBreakerConfig(daily_loss_threshold_pct=-3.5)
    cb = RiskCircuitBreaker(config)
    
    anchor = 100000.0
    cb.initialize_day(anchor)
    
    # Simular perda de 3.6%
    allowed, msg, status = cb.update_equity(anchor * (1 - 0.036))
    
    if not allowed and status['state'] == "OPEN":
        print(f"✅ Smoke Test PASSED: Circuit Breaker OPEN at {status['gross_loss_intraday_pct']}%")
        cb.export_status("smoke_test_circuit_breaker_status.json")
        return True
    return False

if __name__ == "__main__":
    smoke_test_circuit_breaker()
