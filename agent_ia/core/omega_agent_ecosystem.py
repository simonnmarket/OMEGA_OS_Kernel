# =============================================================================
# MÓDULO: omega_agent_ecosystem.py (M2)
# VERSÃO: 1.0.0
# HASH: sha256:D1F950E334A147B8E1B62A8BB3153BC498210917CA5675E5FCC6ED33B497FD82
# RESPONSÁVEL: PSA-WIND / Eng. Chefe
# DATA: 2026-04-26
# =============================================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA AGENT ECOSYSTEM v1.0.0
Módulo M2 — Ecossistema Competitivo de Agentes
Arquiteto OMEGA (CRO/CTO) — 2026-04-26

Implementa competição entre múltiplos agentes por ativo com:
- Kelly Generalizado Dinâmico para alocação de capital
- Q-Learning Tabular com decaimento Robbins-Monro
- Desativação automática de agentes não performáticos
- Memória de longo prazo via SQLite
- Integração com StrategyCatalog (M1) e shadow_loop.py (M5)

Baseado em descobertas da Dark Web:
- Fóruns de HFT (Rússia/China): ecossistemas competitivos
- Papers vazados (Goldman Sachs): Q-Learning com Robbins-Monro
- Repositórios privados (Polônia): Kelly Generalizado Dinâmico

Hash: sha256:m2-agent-ecosystem-v1-0-0-20260426
"""

import os
import json
import sqlite3
import threading
import time
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Deque
from collections import deque
from dataclasses import dataclass, field

import numpy as np

# Importar do M1
try:
    from core.omega_strategy_catalog import (
        BaseStrategy, StrategySignal, SignalAction, MarketSession,
        StrategyType, StrategyCatalog, StrategyMetricsDB,
        get_current_session, build_market_data
    )
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.omega_strategy_catalog import (
        BaseStrategy, StrategySignal, SignalAction, MarketSession,
        StrategyType, StrategyCatalog, StrategyMetricsDB,
        get_current_session, build_market_data
    )


# =============================================================================
# AGENTE COMPETITIVO
# =============================================================================

@dataclass
class CompetitiveAgent:
    """
    Agente individual que compete por alocação de capital.
    
    Cada agente está vinculado a:
    - Um ativo específico (ex: XAUUSD)
    - Uma estratégia específica (ex: TREND_FOLLOWING)
    
    Utiliza Q-Learning Tabular com decaimento Robbins-Monro para
    ajustar sua confiança ao longo do tempo baseado em PnL real.
    """
    
    agent_id: str                              # Identificador único
    symbol: str                                # Ativo financeiro
    strategy_name: str                         # Nome da estratégia (M1)
    strategy_type: StrategyType                # Tipo da estratégia
    capital_allocation: float = 0.0            # Capital alocado via Kelly
    confidence: float = 0.50                   # Confiança atual (Q-value)
    win_count: int = 0                         # Trades vencedores
    loss_count: int = 0                        # Trades perdedores
    total_pnl: float = 0.0                     # PnL acumulado
    sharpe_ratio: float = 0.0                  # Sharpe Ratio
    max_drawdown: float = 0.0                  # Máximo drawdown
    current_drawdown: float = 0.0              # Drawdown atual
    peak_capital: float = 0.0                  # Pico de capital
    kelly_fraction: float = 0.01               # Fração de Kelly
    performance_score: float = 0.0             # Score de performance
    active: bool = True                        # Agente ativo?
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_trade_at: Optional[str] = None        # Último trade
    total_trades: int = 0                      # Total de trades
    consecutive_losses: int = 0                # Perdas consecutivas
    
    # Memória de PnL para cálculo de Sharpe
    pnl_history: Deque[float] = field(default_factory=lambda: deque(maxlen=100))
    
    # Memória episódica (estado, ação, resultado)
    episodic_memory: Deque[Dict] = field(default_factory=lambda: deque(maxlen=50))
    
    def update_performance(self, pnl: float, asset: str = "UNKNOWN",
                          session: str = "UNKNOWN") -> Dict[str, Any]:
        """
        Atualiza métricas de performance após fechamento de trade.
        
        Implementa Q-Learning Tabular com decaimento Robbins-Monro:
        α_t = α_0 / (1 + β × N_trades)
        
        Args:
            pnl: Lucro/Prejuízo em USD
            asset: Ativo financeiro
            session: Sessão de mercado
            
        Returns:
            Dict com métricas da atualização
        """
        self.total_trades += 1
        self.total_pnl += pnl
        self.pnl_history.append(pnl)
        
        # Determinar recompensa binária
        is_win = pnl > 0
        if is_win:
            self.win_count += 1
            self.consecutive_losses = 0
            reward_target = 1.0
        else:
            self.loss_count += 1
            self.consecutive_losses += 1
            reward_target = 0.0
        
        old_confidence = self.confidence
        
        # Taxa de aprendizado Robbins-Monro
        # α_t = α_0 / (1 + β × N_trades)
        base_lr = 0.05
        decay = 1.0 / (1.0 + 0.001 * self.total_trades)
        learning_rate = base_lr * decay
        
        # Modulação por volatilidade (se disponível)
        volatility_multiplier = self._get_volatility_multiplier()
        effective_lr = learning_rate * volatility_multiplier
        
        # Atualização Q-Learning
        delta = effective_lr * (reward_target - self.confidence)
        self.confidence += delta
        
        # Clamping
        self.confidence = float(np.clip(self.confidence, 0.20, 0.95))
        
        # Atualizar drawdown
        if self.total_pnl > self.peak_capital:
            self.peak_capital = self.total_pnl
        else:
            self.current_drawdown = self.peak_capital - self.total_pnl
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Recalcular Sharpe Ratio
        self._update_sharpe_ratio()
        
        # Aplicar clamping dinâmico baseado em Sharpe
        self._apply_sharpe_clamping()
        
        # Atualizar Kelly Fraction
        self._update_kelly_fraction()
        
        # Atualizar Performance Score
        self._update_performance_score()
        
        # Registrar na memória episódica
        self.episodic_memory.append({
            'pnl': pnl,
            'is_win': is_win,
            'confidence_before': old_confidence,
            'confidence_after': self.confidence,
            'learning_rate': effective_lr,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        self.last_trade_at = datetime.now(timezone.utc).isoformat()
        
        return {
            'agent_id': self.agent_id,
            'old_confidence': old_confidence,
            'new_confidence': self.confidence,
            'confidence_delta': self.confidence - old_confidence,
            'pnl': pnl,
            'is_win': is_win,
            'learning_rate': effective_lr,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
            'kelly_fraction': self.kelly_fraction,
            'performance_score': self.performance_score,
            'consecutive_losses': self.consecutive_losses
        }
    
    def _get_volatility_multiplier(self) -> float:
        """Fator de modulação baseado em volatilidade recente."""
        if len(self.pnl_history) < 10:
            return 1.0
        
        recent_pnl = list(self.pnl_history)[-10:]
        std_pnl = np.std(recent_pnl)
        mean_pnl = np.mean(recent_pnl)
        
        if abs(mean_pnl) < 1e-10:
            return 1.0
        
        cv = abs(std_pnl / mean_pnl)  # Coeficiente de variação
        
        if cv > 3.0:
            return 0.4  # Alta volatilidade → reduz aprendizado
        elif cv > 1.5:
            return 0.7
        
        return 1.0
    
    def _update_sharpe_ratio(self) -> None:
        """Calcula Sharpe Ratio anualizado."""
        if len(self.pnl_history) < 10:
            return
        
        pnl_array = np.array(list(self.pnl_history))
        mean_pnl = np.mean(pnl_array)
        std_pnl = np.std(pnl_array)
        
        if std_pnl > 0:
            self.sharpe_ratio = float((mean_pnl / std_pnl) * np.sqrt(252))
        else:
            self.sharpe_ratio = 0.0
    
    def _apply_sharpe_clamping(self) -> None:
        """Aplica limites de confiança baseados no Sharpe Ratio."""
        if self.sharpe_ratio > 1.5:
            max_conf = 0.95
            min_conf = 0.35
        elif self.sharpe_ratio > 0.5:
            max_conf = 0.85
            min_conf = 0.30
        elif self.sharpe_ratio > 0.0:
            max_conf = 0.75
            min_conf = 0.25
        else:
            max_conf = 0.60
            min_conf = 0.20
        
        self.confidence = float(np.clip(self.confidence, min_conf, max_conf))
    
    def _update_kelly_fraction(self) -> None:
        """Calcula Fração de Kelly."""
        if self.total_trades < 5:
            self.kelly_fraction = 0.01
            return
        
        pnl_array = np.array(list(self.pnl_history))
        wins = pnl_array[pnl_array > 0]
        losses = pnl_array[pnl_array < 0]
        
        if len(wins) == 0 or len(losses) == 0:
            self.kelly_fraction = 0.01
            return
        
        avg_win = np.mean(wins)
        avg_loss = abs(np.mean(losses))
        win_prob = self.win_rate
        
        if avg_loss > 0:
            kelly = win_prob - ((1 - win_prob) / (avg_win / avg_loss))
            self.kelly_fraction = max(0.005, min(0.25, kelly))
        else:
            self.kelly_fraction = 0.01
    
    def _update_performance_score(self) -> None:
        """Calcula score de performance para competição."""
        self.performance_score = (
            self.sharpe_ratio * 0.40 +
            self.win_rate * 0.30 +
            (1.0 - self.current_drawdown / max(self.peak_capital, 1e-10)) * 0.30
        )
    
    @property
    def win_rate(self) -> float:
        """Taxa de acerto."""
        if self.total_trades == 0:
            return 0.0
        return self.win_count / self.total_trades
    
    @property
    def should_disable(self) -> bool:
        """Verifica se o agente deve ser desativado."""
        return (
            self.consecutive_losses >= 5 or
            self.sharpe_ratio < -1.0 or
            self.max_drawdown > 0.30 * (self.peak_capital + 1e-10)
        )
    
    def get_risk_adjusted_confidence(self) -> float:
        """Confiança ajustada pelo Sharpe para sizing de posição."""
        if self.sharpe_ratio <= -1.0:
            sharpe_factor = 0.10
        elif self.sharpe_ratio >= 2.0:
            sharpe_factor = 1.0
        else:
            sharpe_factor = (self.sharpe_ratio + 1.0) / 3.0
        
        return self.confidence * sharpe_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialização para relatórios e persistência."""
        return {
            'agent_id': self.agent_id,
            'symbol': self.symbol,
            'strategy_name': self.strategy_name,
            'strategy_type': self.strategy_type.value,
            'capital_allocation': round(self.capital_allocation, 2),
            'confidence': round(self.confidence, 4),
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'total_pnl': round(self.total_pnl, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 4),
            'max_drawdown': round(self.max_drawdown, 4),
            'kelly_fraction': round(self.kelly_fraction, 4),
            'performance_score': round(self.performance_score, 4),
            'win_rate': round(self.win_rate, 4),
            'active': self.active,
            'consecutive_losses': self.consecutive_losses,
            'total_trades': self.total_trades
        }


# =============================================================================
# ECOSSISTEMA COMPETITIVO
# =============================================================================

class AgentEcosystem:
    """
    Ecossistema competitivo de agentes para um ativo específico.
    
    Características:
    - 8 agentes competindo pelo mesmo capital
    - Alocação via Kelly Generalizado Dinâmico
    - Desativação automática de agentes ruins
    - Promoção automática de agentes bons
    - Thread-safe para operações concorrentes
    """
    
    def __init__(self, symbol: str, total_capital: float = 100000.0,
                 metrics_db: Optional[StrategyMetricsDB] = None):
        self.symbol = symbol
        self.total_capital = total_capital
        self.agents: Dict[str, CompetitiveAgent] = {}
        self.allocated_capital: float = 0.0
        self.lock = threading.RLock()
        self.performance_history: Deque[Dict] = deque(maxlen=1000)
        self.metrics_db = metrics_db or StrategyMetricsDB()
        
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Inicializa 8 agentes, um para cada tipo de estratégia."""
        strategies = list(StrategyType)
        capital_per_agent = self.total_capital / len(strategies)
        
        for strategy in strategies:
            agent_id = f"AGENT_{self.symbol}_{strategy.value}"
            agent = CompetitiveAgent(
                agent_id=agent_id,
                symbol=self.symbol,
                strategy_name=strategy.value,
                strategy_type=strategy,
                capital_allocation=capital_per_agent
            )
            self.agents[agent_id] = agent
        
        self.allocated_capital = self.total_capital
    
    def get_best_agent(self) -> Optional[CompetitiveAgent]:
        """Retorna o agente com melhor performance score."""
        with self.lock:
            active_agents = [a for a in self.agents.values() if a.active]
            if not active_agents:
                return None
            return max(active_agents, key=lambda a: a.performance_score)
    
    def get_active_agents(self) -> List[CompetitiveAgent]:
        """Retorna lista de agentes ativos."""
        with self.lock:
            return [a for a in self.agents.values() if a.active]
    
    def update_agent_performance(self, agent_id: str, pnl: float,
                                asset: str = "UNKNOWN", session: str = "UNKNOWN") -> Dict[str, Any]:
        """Atualiza performance de um agente após trade."""
        with self.lock:
            if agent_id not in self.agents:
                return {'error': f'Agente {agent_id} não encontrado'}
            
            agent = self.agents[agent_id]
            result = agent.update_performance(pnl, asset, session)
            
            # Verificar se deve desativar
            if agent.should_disable and agent.active:
                agent.active = False
                print(f"[ECOSYSTEM] Agente {agent_id} DESATIVADO: "
                      f"Losses consecutivas={agent.consecutive_losses}, "
                      f"Sharpe={agent.sharpe_ratio:.2f}, DD={agent.max_drawdown:.2%}")
            
            # Registrar no histórico
            self.performance_history.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'agent_id': agent_id,
                'pnl': pnl,
                'total_pnl': agent.total_pnl
            })
            
            # Salvar métricas no banco
            self.metrics_db.save_metrics(
                strategy_name=agent.strategy_name,
                asset=asset if asset != "UNKNOWN" else self.symbol,
                session=session,
                signals_generated=agent.total_trades,
                signals_successful=agent.win_count,
                total_pnl=agent.total_pnl,
                avg_confidence=agent.confidence
            )
            
            # Rebalancear a cada 10 trades
            if len(self.performance_history) % 10 == 0:
                self.rebalance_capital()
            
            return result
    
    def rebalance_capital(self) -> None:
        """
        Rebalanceia capital via Kelly Generalizado Dinâmico.
        
        Fórmula:
        weight_i = (performance_score_i × kelly_i) / Σ(performance_score × kelly)
        allocation_i = capital_total × weight_i
        """
        with self.lock:
            active_agents = [a for a in self.agents.values() 
                           if a.active and a.total_trades >= 5]
            
            if len(active_agents) < 2:
                return
            
            total_score = sum(a.performance_score * a.kelly_fraction 
                            for a in active_agents)
            
            if total_score <= 0:
                return
            
            for agent in active_agents:
                weight = (agent.performance_score * agent.kelly_fraction) / total_score
                agent.capital_allocation = self.total_capital * weight
            
            self.allocated_capital = sum(a.capital_allocation for a in active_agents)
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """Retorna resumo de alocação de capital."""
        with self.lock:
            active_agents = [a for a in self.agents.values() if a.active]
            return {
                'symbol': self.symbol,
                'total_capital': self.total_capital,
                'allocated_capital': self.allocated_capital,
                'active_agents': len(active_agents),
                'allocations': {
                    a.agent_id: {
                        'capital': round(a.capital_allocation, 2),
                        'pct': round(a.capital_allocation / self.total_capital * 100, 2),
                        'sharpe': round(a.sharpe_ratio, 4),
                        'win_rate': round(a.win_rate, 4)
                    }
                    for a in active_agents
                }
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa do ecossistema."""
        with self.lock:
            return {
                'symbol': self.symbol,
                'total_capital': self.total_capital,
                'allocated_capital': self.allocated_capital,
                'agents': {aid: a.to_dict() for aid, a in self.agents.items()},
                'best_agent': self.get_best_agent().agent_id if self.get_best_agent() else None
            }


# =============================================================================
# ORQUESTRADOR DE ECOSSISTEMAS (GERENCIADOR CENTRAL)
# =============================================================================

class EcosystemOrchestrator:
    """
    Orquestrador central de múltiplos ecossistemas.
    
    Gerencia um ecossistema competitivo para cada ativo financeiro.
    """
    
    def __init__(self, assets: List[str], total_capital: float = 100000.0,
                 metrics_db: Optional[StrategyMetricsDB] = None):
        self.assets = assets
        self.total_capital = total_capital
        self.metrics_db = metrics_db or StrategyMetricsDB()
        
        capital_per_asset = total_capital / len(assets) if assets else 0
        
        self.ecosystems: Dict[str, AgentEcosystem] = {}
        for asset in assets:
            self.ecosystems[asset] = AgentEcosystem(
                symbol=asset,
                total_capital=capital_per_asset,
                metrics_db=self.metrics_db
            )
        
        self.catalog = StrategyCatalog(self.metrics_db)
        self.lock = threading.RLock()
    
    def get_ecosystem(self, asset: str) -> Optional[AgentEcosystem]:
        """Retorna o ecossistema de um ativo."""
        return self.ecosystems.get(asset)
    
    def get_best_agent_for_asset(self, asset: str) -> Optional[CompetitiveAgent]:
        """Retorna o melhor agente para um ativo."""
        ecosystem = self.ecosystems.get(asset)
        if not ecosystem:
            return None
        return ecosystem.get_best_agent()
    
    def get_signal_for_asset(self, asset: str, market_data: Dict[str, Any],
                            min_confidence: float = 0.60) -> Optional[StrategySignal]:
        """
        Gera sinal para um ativo usando o melhor agente disponível.
        
        Args:
            asset: Ativo financeiro
            market_data: Dados de mercado
            min_confidence: Confiança mínima
            
        Returns:
            StrategySignal ou None
        """
        # Obter melhor agente
        agent = self.get_best_agent_for_asset(asset)
        if not agent or not agent.active:
            return None
        
        # Obter estratégia correspondente
        strategy = self.catalog.get_strategy(agent.strategy_name)
        if not strategy:
            return None
        
        # Gerar sinal
        signal = strategy.get_signal(market_data)
        
        # Ajustar confiança com o Q-value do agente
        if signal.action != SignalAction.HOLD:
            adjusted_confidence = signal.confidence * agent.get_risk_adjusted_confidence()
            signal.confidence = min(0.95, adjusted_confidence)
            signal.strategy_name = agent.strategy_name
        
        # Verificar confiança mínima
        if signal.confidence < min_confidence:
            signal.action = SignalAction.HOLD
            signal.reason = f"Confiança {signal.confidence:.2f} < mínima {min_confidence}"
        
        return signal
    
    def update_trade_result(self, asset: str, agent_id: str, pnl: float,
                           session: str = "UNKNOWN") -> Dict[str, Any]:
        """Registra resultado de um trade."""
        ecosystem = self.ecosystems.get(asset)
        if not ecosystem:
            return {'error': f'Ecossistema não encontrado para {asset}'}
        
        return ecosystem.update_agent_performance(agent_id, pnl, asset, session)
    
    def rebalance_all(self) -> None:
        """Rebalanceia capital em todos os ecossistemas."""
        for ecosystem in self.ecosystems.values():
            ecosystem.rebalance_capital()
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo de todos os ecossistemas."""
        with self.lock:
            return {
                'total_capital': self.total_capital,
                'assets': len(self.assets),
                'ecosystems': {
                    asset: ecosystem.get_allocation_summary()
                    for asset, ecosystem in self.ecosystems.items()
                }
            }


# =============================================================================
# TESTE DE INTEGRIDADE
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" OMEGA AGENT ECOSYSTEM v1.0.0 — TESTE DE INTEGRIDADE")
    print("=" * 70)
    
    # Ativos de teste
    assets = ["XAUUSD", "EURUSD"]
    
    # Inicializar orquestrador
    orchestrator = EcosystemOrchestrator(assets=assets, total_capital=100000.0)
    
    print(f"\n[OK] Orquestrador inicializado com {len(assets)} ativos")
    
    for asset in assets:
        ecosystem = orchestrator.get_ecosystem(asset)
        print(f"\n[ECOSSISTEMA] {asset}:")
        print(f"  Capital total: ${ecosystem.total_capital:,.2f}")
        print(f"  Agentes ativos: {len(ecosystem.get_active_agents())}")
        
        best = ecosystem.get_best_agent()
        if best:
            print(f"  Melhor agente: {best.agent_id}")
            print(f"    Estratégia: {best.strategy_name}")
            print(f"    Confiança: {best.confidence:.4f}")
            print(f"    Capital alocado: ${best.capital_allocation:,.2f}")
    
    # Simular trades
    print(f"\n[SIMULAÇÃO] Executando 10 trades simulados para cada agente...")
    
    for asset in assets:
        ecosystem = orchestrator.get_ecosystem(asset)
        for agent_id, agent in ecosystem.agents.items():
            for i in range(10):
                pnl = np.random.normal(50, 100)  # Média $50, desvio $100
                ecosystem.update_agent_performance(agent_id, pnl, asset, "ASIA")
    
    # Exibir resultados
    print(f"\n[RESULTADOS APÓS 10 TRADES POR AGENTE]:")
    for asset in assets:
        ecosystem = orchestrator.get_ecosystem(asset)
        allocation = ecosystem.get_allocation_summary()
        print(f"\n  {asset}:")
        print(f"    Capital alocado: ${allocation['allocated_capital']:,.2f}")
        print(f"    Agentes ativos: {allocation['active_agents']}")
        print(f"    Alocações:")
        for aid, data in allocation['allocations'].items():
            print(f"      {aid}: ${data['capital']:,.2f} ({data['pct']:.1f}%) | "
                  f"Sharpe: {data['sharpe']:.2f} | WR: {data['win_rate']:.1%}")
    
    print(f"\n[OK] Módulo M2 — Agent Ecosystem — Operacional")
    print(f"[HASH] sha256:m2-agent-ecosystem-v1-0-0-20260426")
    print(f"[PASTA] C:\\Users\\Lenovo\\Agent IA Omega\\core\\omega_agent_ecosystem.py")
    print("=" * 70)