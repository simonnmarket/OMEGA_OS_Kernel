import copy
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass(frozen=True)
class CostSnapshot:
    """
    Snapshot de custos para um símbolo específico (Imutável para thread-safety).
    Valores baseados em nível NASA/JPL para precisão fiduciária.
    """
    symbol: str
    spread_points: float          # Pontos de spread (ex: 20 pts para 2.0 pips)
    slippage_points: float        # Slippage médio esperado em condições normais
    commission_per_lot: float      # Comissão fixa de ida e volta por lote (USD)
    swap_long_per_day: float       # Swap para compra por dia por lote (USD)
    swap_short_per_day: float      # Swap para venda por dia por lote (USD)
    pip_value: float               # Valor monetário de 1 ponto/pip por lote (USD)
    lot_size: float                # Tamanho do lote padrão (ex: 100000)
    volatility_factor: float = 1.0 # Multiplicador de slippage baseado no regime de volatilidade

class CostOracle:
    """
    Núcleo Independente de Estimativa de Custos Operacionais OMEGA V5.5.0.
    Fornece métricas de fricção e lucro mínimo sem dependências externas.
    """
    def __init__(self):
        self._snapshots: Dict[str, CostSnapshot] = {}

    def set_snapshot(self, snapshot: CostSnapshot):
        """Atualiza ou insere um novo snapshot de custo."""
        self._snapshots[snapshot.symbol.upper()] = snapshot

    def get_snapshot(self, symbol: str) -> Optional[CostSnapshot]:
        """Recupera o snapshot atual para o símbolo."""
        return self._snapshots.get(symbol.upper())

    def effective_cost(self, symbol: str, direction: str, lots: float, hold_days: float = 0, stress_factor: float = 1.0) -> dict:
        """
        Calcula o custo efetivo total simulado.
        stress_factor: Multiplicador para simular condições adversas (2.0 = dobro do spread/slippage).
        """
        snap = self.get_snapshot(symbol)
        if not snap:
            raise ValueError(f"Oracle Error: No snapshot found for symbol {symbol}")

        dir_norm = direction.lower()
        if dir_norm not in ["buy", "sell", "long", "short"]:
            raise ValueError(f"Invalid direction: {direction}")

        # 1. Spread Cost
        spread_cost = (snap.spread_points * snap.pip_value * lots) * stress_factor

        # 2. Slippage Cost (escalado pela volatilidade)
        slippage_cost = (snap.slippage_points * snap.volatility_factor * snap.pip_value * lots) * stress_factor

        # 3. Commission (Ida e Volta)
        commission = snap.commission_per_lot * lots

        # 4. Swap Cost
        is_long = dir_norm in ["buy", "long"]
        swap_rate = snap.swap_long_per_day if is_long else snap.swap_short_per_day
        swap_cost = abs(swap_rate * lots * hold_days) # Assume custo sempre reduz PnL na estimativa conservadora

        total_cost = spread_cost + slippage_cost + commission + swap_cost

        return {
            "symbol": symbol.upper(),
            "total_cost": round(total_cost, 4),
            "breakdown": {
                "spread": round(spread_cost, 4),
                "slippage": round(slippage_cost, 4),
                "commission": round(commission, 4),
                "swap": round(swap_cost, 4)
            }
        }

    def friction_ratio(self, gross_pnl: float, total_cost: float) -> float:
        """
        Calcula o Friction Ratio (FR).
        FR = Custos / |PnL Bruto|
        """
        if abs(gross_pnl) < 0.0001:
            return 1.0 # Custo infinito se não há ganho
        return round(total_cost / abs(gross_pnl), 4)

    def min_profit_required(self, symbol: str, direction: str, lots: float, hold_days: float = 0, buffer_ratio: float = 0.2) -> float:
        """
        Calcula o lucro bruto mínimo necessário para cobrir custos e manter o FR alvo.
        buffer_ratio: Margem extra exigida (e.g., 0.2 = exige 20% a mais que o custo).
        """
        costs = self.effective_cost(symbol, direction, lots, hold_days)
        total = costs["total_cost"]
        return round(total * (1 + buffer_ratio), 4)

    def clone_with_stress(self, symbol: str, spread_up_pct: float = 0, slippage_up_pct: float = 0) -> Optional[CostSnapshot]:
        """
        Cria um clone do snapshot com estresse aplicado para simulação de cenários de ruptura.
        """
        snap = self.get_snapshot(symbol)
        if not snap: return None
        
        return CostSnapshot(
            symbol=snap.symbol,
            spread_points=snap.spread_points * (1 + spread_up_pct),
            slippage_points=snap.slippage_points * (1 + slippage_up_pct),
            commission_per_lot=snap.commission_per_lot,
            swap_long_per_day=snap.swap_long_per_day,
            swap_short_per_day=snap.swap_short_per_day,
            pip_value=snap.pip_value,
            lot_size=snap.lot_size,
            volatility_factor=snap.volatility_factor
        )

# Exemplo de Teste de Integridade (NASA Validation)
if __name__ == "__main__":
    oracle = CostOracle()
    # Mock XAUUSD (Broker Real Spreads)
    xau_snap = CostSnapshot(
        symbol="XAUUSD",
        spread_points=25,       # 2.5 pips
        slippage_points=5,     # 0.5 pips slippage
        commission_per_lot=7,  # $7 standard across industry
        swap_long_per_day=-15, 
        swap_short_per_day=5,
        pip_value=1.0,         # $1 per point for 0.01 lot approx, adjusted for 1 lot here
        lot_size=100
    )
    oracle.set_snapshot(xau_snap)
    
    # Simulação de custo para trade de 1 lote, mantido por 2 dias
    res = oracle.effective_cost("XAUUSD", "buy", lots=1.0, hold_days=2)
    print(f"Custo Efetivo Estimado: ${res['total_cost']}")
    
    # Lucro mínimo para FR < 0.2 (Buffer 4.0x custo)
    min_p = oracle.min_profit_required("XAUUSD", "buy", lots=1.0, hold_days=2, buffer_ratio=4.0)
    print(f"Lucro Bruto Mínimo para Viabilidade NASA: ${min_p}")
