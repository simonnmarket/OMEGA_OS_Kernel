#!/usr/bin/env python3
"""
Stub Strategy — placeholder para validação de boot.
Substitua por estratégias reais quando disponíveis.
"""


class StubStrategy:
    """Estratégia mínima para boot validation. Retorna sempre HOLD."""

    name = "stub_strategy"

    def analyze(self, symbol: str, ohlcv=None, **kwargs):
        return {
            "action": "HOLD",
            "confidence": 0.0,
            "reason": "Stub — nenhuma lógica real implementada",
        }
