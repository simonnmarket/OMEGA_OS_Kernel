"""Camada Gold — agregados CEO (stubs; ligar a API/views materializadas)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class CEOViews:
    @staticmethod
    def get_pnl_daily(strategy_id: Optional[str] = None) -> Dict[str, Any]:
        del strategy_id
        return {}

    @staticmethod
    def get_last_trades(limit: int = 10) -> List[Dict[str, Any]]:
        del limit
        return []

    @staticmethod
    def get_risk_exposure() -> Dict[str, Any]:
        return {}
