"""
Métricas de engajamento e convenções n=0 — alinhado a DEFINICOES v1.1 (Métrica 9).

Uso: pós-instalação, cruzar com logs de sinais/ordens/execuções; testes unitários aqui
não substituem evidência empírica em produção.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EngagementSnapshot:
    """Instante ou janela: flags de pipeline sinal → ordem → fill."""

    signal_fired: bool
    order_sent: bool
    order_filled: bool


def engagement_rate(signals_valid: int, orders_filled: int) -> float | None:
    """
    Taxa de engajamento: fração de sinais válidos que resultaram em execução.

    Returns:
        None se signals_valid == 0 (convénio oficial: N/A, não 0%).
    """
    if signals_valid < 0 or orders_filled < 0:
        raise ValueError("Contagens devem ser >= 0.")
    if orders_filled > signals_valid:
        raise ValueError("orders_filled não pode exceder signals_valid.")
    if signals_valid == 0:
        return None
    return float(orders_filled) / float(signals_valid)


def performance_placeholders_when_n_trades_zero() -> dict[str, Any]:
    """
    Convenção explícita quando n_total_trades = 0 (auditoria CQO).

    Drawdown máximo 0% significa apenas que não houve equity de trades;
    não substitui métricas de engajamento nem custo de oportunidade.
    """
    return {
        "winrate": None,
        "sharpe": None,
        "sortino": None,
        "calmar": None,
        "max_drawdown_pct": 0.0,
        "max_drawdown_note": "Sem trades executados: DD sobre equity de trades é 0% por vacuidade.",
        "status": "N_A_ZERO_TRADES",
    }


def opportunity_cost_points(
    signal_fired: bool,
    order_filled: bool,
    price_move_if_entered_pts: float,
    price_move_actual_pts: float,
    position_size: float,
) -> float | None:
    """
    Custo de oportunidade em pontos (notional), só quando houve sinal sem fill.

    opportunity_cost_pts = |move_if_entered - move_actual| * position_size

    Se signal_fired é False ou order_filled é True, retorna None (métrica não aplicável).
    """
    if not signal_fired:
        return None
    if order_filled:
        return None
    if position_size < 0:
        raise ValueError("position_size deve ser >= 0.")
    return abs(price_move_if_entered_pts - price_move_actual_pts) * position_size
