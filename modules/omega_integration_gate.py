"""
omega_integration_gate.py — Stub mínimo para compatibilidade com módulos nebular.
Fornece OmegaBaseAgent e RiskParameters sem dependência de omega_config.json.
Integration phase-1: suporta kalman_pullback_engine e outros módulos OMEGA_OS_Kernel.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RiskParameters:
    """Parâmetros de risco para agentes OMEGA (stub institucional)."""
    max_drawdown_limit:    float = 0.05
    latency_tolerance_ms:  float = 50.0
    required_confidence:   float = 0.65
    max_risk_per_trade:    float = 0.002
    max_drawdown_daily:    float = 0.01
    kelly_fraction:        float = 0.0
    max_leverage:          float = 10.0
    min_sharpe_required:   float = 0.5
    proposed_tp_distance:  float = 50.0

    def validate(self, strategy_type: str = "SCALPING") -> bool:
        return (0 < self.max_risk_per_trade <= 0.05 and
                0 < self.max_drawdown_daily <= 0.10 and
                self.min_sharpe_required >= 0.3)


class OmegaBaseAgent(ABC):
    """Classe base para agentes OMEGA (stub para compatibilidade nebular)."""

    def __init__(self):
        self.contract_hash: str = self._hash_core_logic()
        self.version:       str = "stub-1.0"
        self._halt:         bool = False

    @abstractmethod
    def _hash_core_logic(self) -> str:
        """Retorna hash identificador da lógica central do agente."""

    @abstractmethod
    def get_risk_parameters(self) -> RiskParameters:
        """Retorna os parâmetros de risco do agente."""

    @abstractmethod
    def execute(self, *args, **kwargs) -> dict:
        """Executa a lógica principal do agente."""

    def force_halt(self) -> bool:
        """Verifica se o agente deve parar emergencialmente."""
        return self._halt
