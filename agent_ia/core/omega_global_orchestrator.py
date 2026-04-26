# =============================================================================
# MÓDULO: omega_global_orchestrator.py (M4)
# VERSÃO: 1.0.0
# HASH: sha256:2EB62F817499BA774AEF1F69DE432C2E9D73F8552015889431586E0D5583D13A
# RESPONSÁVEL: PSA-WIND / Eng. Chefe
# DATA: 2026-04-26
# =============================================================================
# MÓDULO M4 — ORQUESTRADOR GLOBAL
# core/omega_global_orchestrator.py
#
# Emitente: Arquiteto OMEGA (CRO/CTO)
# Etapa: 4 de 5
# Versão: 1.0.0
# Hash do Módulo: sha256:m4-global-orchestrator-v1-0-0-20260426
# Pasta de Destino: C:\Users\Lenovo\Agent IA Omega\core\omega_global_orchestrator.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA GLOBAL ORCHESTRATOR v1.0.0
Módulo M4 — Orquestrador Global do Agente IA
Arquiteto OMEGA (CRO/CTO) — 2026-04-26

Orquestra todos os componentes do Agente IA OMEGA:
- M1: Catálogo de Estratégias (StrategyCatalog)
- M2: Ecossistema Competitivo (EcosystemOrchestrator)
- M3: Calibrador de Sessão (SessionCalibrator)
- Detecção de Assinaturas (SpoofIcebergDetector)
- Filtro de Correlação (CorrelationFilter)
- Execução de Ordens (MT5 via shadow_loop)

Integração completa com o pipeline de execução real.

Baseado em:
- Dark Web: ecossistemas multi-agente com competição
- Protocolo CQO: validação pré-execução
- Microestrutura: detecção de assinaturas por sessão

Hash: sha256:m4-global-orchestrator-v1-0-0-20260426
"""

import os
import json
import time
import threading
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque

import numpy as np

# Importar módulos do Agente IA
try:
    from core.omega_strategy_catalog import (
        StrategyCatalog, StrategySignal, SignalAction, MarketSession,
        StrategyMetricsDB, get_current_session, build_market_data,
        StrategyIntegrator
    )
    from core.omega_agent_ecosystem import (
        EcosystemOrchestrator, CompetitiveAgent, AgentEcosystem
    )
    from core.omega_session_calibrator import (
        SessionCalibrator, SessionConfig, SessionConfigCatalog
    )
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.omega_strategy_catalog import (
        StrategyCatalog, StrategySignal, SignalAction, MarketSession,
        StrategyMetricsDB, get_current_session, build_market_data,
        StrategyIntegrator
    )
    from core.omega_agent_ecosystem import (
        EcosystemOrchestrator, CompetitiveAgent, AgentEcosystem
    )
    from core.omega_session_calibrator import (
        SessionCalibrator, SessionConfig, SessionConfigCatalog
    )


# =============================================================================
# ORQUESTRADOR GLOBAL
# =============================================================================

class OmegaGlobalOrchestrator:
    """
    Orquestrador Global do Agente IA OMEGA.
    
    Este é o CÉREBRO CENTRAL que integra todos os módulos:
    
    1. Detecta a sessão atual (M3)
    2. Seleciona ativos prioritários (M3)
    3. Obtém thresholds de detecção calibrados (M3)
    4. Para cada ativo prioritário:
       a. Obtém o melhor agente do ecossistema (M2)
       b. Gera sinal usando a estratégia do agente (M1)
       c. Ajusta confiança com o Q-value do agente (M2)
       d. Aplica filtros de correlação e assinaturas
       e. Se aprovado, envia para execução
    5. Registra resultados e atualiza métricas
    6. Rebalanceia capital periodicamente
    
    Arquitetura de Decisão:
    ┌─────────────────────────────────────────────────────────────┐
    │                    OMEGA GLOBAL ORCHESTRATOR                 │
    ├─────────────────────────────────────────────────────────────┤
    │  M3: SessionCalibrator                                      │
    │      ↓                                                      │
    │  Sessão Atual → Ativos → Estratégias → Thresholds           │
    │      ↓                                                      │
    │  M2: EcosystemOrchestrator                                  │
    │      ↓                                                      │
    │  Melhor Agente por Ativo (8 competindo)                     │
    │      ↓                                                      │
    │  M1: StrategyCatalog                                        │
    │      ↓                                                      │
    │  Sinal (BUY/SELL/HOLD) + Confiança + SL/TP                  │
    │      ↓                                                      │
    │  FILTROS:                                                   │
    │  ├── SpoofDetector (assinaturas de robôs)                   │
    │  ├── CorrelationFilter (exposição duplicada)                │
    │  ├── RiskManager (VaR, DD, Kill Switch)                     │
    │  └── Guardrails (lote, confiança, slippage)                 │
    │      ↓                                                      │
    │  EXECUÇÃO:                                                  │
    │  └── mt5_send_order() → MT5                                │
    │      ↓                                                      │
    │  FEEDBACK:                                                  │
    │  └── update_trade_result() → Aprendizado                    │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self,
                 assets: List[str] = None,
                 total_capital: float = 100000.0,
                 metrics_db_path: str = None):
        """
        Inicializa o Orquestrador Global.
        
        Args:
            assets: Lista de ativos a operar (default: todos os prioritários)
            total_capital: Capital total do fundo
            metrics_db_path: Caminho para banco de métricas SQLite
        """
        # Componentes
        self.metrics_db = StrategyMetricsDB(metrics_db_path)
        self.calibrator = SessionCalibrator()
        self.catalog = StrategyCatalog(self.metrics_db)
        
        # Definir ativos
        if assets is None:
            current_session = self.calibrator.get_current_session()
            self.assets = self.calibrator.get_priority_assets(current_session)
        else:
            self.assets = assets
        
        self.total_capital = total_capital
        
        # Inicializar ecossistema competitivo
        self.ecosystem = EcosystemOrchestrator(
            assets=self.assets,
            total_capital=total_capital,
            metrics_db=self.metrics_db
        )
        
        # Estado
        self.current_session: MarketSession = self.calibrator.get_current_session()
        self.open_positions: Dict[str, Dict] = {}
        self.trade_history: deque = deque(maxlen=1000)
        self.consecutive_failures: int = 0
        self.max_consecutive_failures: int = 3
        self.daily_pnl: float = 0.0
        self.daily_drawdown: float = 0.0
        self.kill_switch_triggered: bool = False

        # Fix 3 — Kill switch via highwater mark (peak_equity)
        # peak_equity = max(equity histórico do dia); current_equity = total_capital + daily_pnl
        self.peak_equity: float = float(total_capital)

        # Fix 8 (CTO) — Idempotência: ticket → bool (já processado em close)
        self._processed_tickets: set = set()
        # Fix 8 (CTO) — Lock dedicado para chamadas MT5 externas (evitar reentrância
        # quando feedback thread e loop principal coexistem). Consumidores devem
        # adquirir mt5_lock ANTES de chamar a API MT5.
        self.mt5_lock = threading.Lock()

        # Thread-safety geral
        self.lock = threading.RLock()
        
        # Sessão de monitoramento
        self._session_monitor_thread = threading.Thread(
            target=self._monitor_session_changes,
            daemon=True
        )
        self._session_monitor_thread.start()
        
        print(f"[OMEGA] Orquestrador Global inicializado")
        print(f"[OMEGA] Sessão atual: {self.current_session.value}")
        print(f"[OMEGA] Ativos: {self.assets}")
        print(f"[OMEGA] Capital total: ${self.total_capital:,.2f}")
    
    def get_signal_for_asset(self, asset: str, 
                            market_data: Optional[Dict[str, Any]] = None,
                            signature_scores: Optional[Dict[str, float]] = None,
                            current_positions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Gera sinal completo para um ativo específico.
        
        Este é o MÉTODO PRINCIPAL que deve ser chamado pelo shadow_loop.py
        para cada ativo em cada ciclo.
        
        Args:
            asset: Símbolo do ativo (ex: 'XAUUSD')
            market_data: Dados de mercado (se None, busca do MT5)
            signature_scores: Pontuações de assinaturas detectadas
            current_positions: Lista de ativos já em posição
            
        Returns:
            Dict com ação, direção, confiança, lote, SL, TP, razão
        """
        with self.lock:
            # 1. Obter dados de mercado se não fornecidos
            if market_data is None:
                market_data = build_market_data(asset)
            
            if not market_data:
                return self._no_signal(asset, "Dados de mercado indisponíveis")
            
            # 2. Obter configuração da sessão
            session_config = self.calibrator.get_config(self.current_session)
            
            # 3. Verificar se ativo é prioritário para esta sessão
            if asset not in session_config.priority_assets:
                return self._no_signal(asset, f"Ativo não prioritário para sessão {self.current_session.value}")
            
            # 4. Verificar limites de posições
            if current_positions and len(current_positions) >= session_config.max_positions:
                return self._no_signal(asset, f"Limite de {session_config.max_positions} posições atingido")
            
            # 5. Verificar se já tem posição neste ativo
            if asset in self.open_positions:
                return self._no_signal(asset, "Já existe posição aberta neste ativo")
            
            # 6. Obter melhor agente do ecossistema
            agent = self.ecosystem.get_best_agent_for_asset(asset)
            if not agent or not agent.active:
                return self._no_signal(asset, "Nenhum agente ativo disponível")
            
            # 7. Obter estratégia correspondente
            strategy = self.catalog.get_strategy(agent.strategy_name)
            if not strategy:
                return self._no_signal(asset, f"Estratégia {agent.strategy_name} não encontrada")
            
            # 8. Gerar sinal da estratégia
            try:
                signal = strategy.get_signal(market_data)
            except Exception as e:
                return self._no_signal(asset, f"Erro ao gerar sinal: {e}")
            
            if signal.action == SignalAction.HOLD:
                return self._no_signal(asset, signal.reason)
            
            # 9. Ajustar confiança com Q-value do agente
            risk_adj_conf = agent.get_risk_adjusted_confidence()
            adjusted_confidence = signal.confidence * risk_adj_conf
            adjusted_confidence = min(0.95, adjusted_confidence)
            
            # 10. Verificar confiança mínima da sessão
            if adjusted_confidence < session_config.min_confidence:
                return self._no_signal(
                    asset, 
                    f"Confiança {adjusted_confidence:.2f} < mínima {session_config.min_confidence}"
                )
            
            # 11. Aplicar filtro de assinaturas (se disponível)
            if signature_scores:
                thresholds = self.calibrator.get_detection_thresholds()
                
                # Spoofing detectado: reduzir confiança
                if signature_scores.get('SPOOFER_LAYER', 0) > thresholds['spoof_threshold']:
                    adjusted_confidence *= 0.7
                
                # Iceberg detectado: ajustar direção
                if signature_scores.get('ICEBERG_HIDDEN', 0) > thresholds['iceberg_threshold']:
                    # Iceberg sugere grande player acumulando
                    if signal.action == SignalAction.SELL:
                        adjusted_confidence *= 0.5  # Não lutar contra big player
            
            # 12. Calcular lote (Fix 2 — Kelly clamp determinístico, sem multiplicador mágico):
            #     lot = clamp(kelly_fraction × max_lot, 0.01, max_lot)
            kelly_lot = agent.kelly_fraction * session_config.max_lot
            lot = max(0.01, min(session_config.max_lot, round(kelly_lot, 2)))

            # 12b. Fix 5 — Concentração por ativo: se já há posições no mesmo ativo
            #      representando >40% das posições abertas, reduzir lote pela metade
            #      (proteção contra over-concentration, ex.: XAUUSD).
            try:
                open_pos_snapshot = self.open_positions
                total_open = len(open_pos_snapshot)
                if total_open > 0:
                    same_asset = sum(1 for k in open_pos_snapshot.keys() if k == asset)
                    concentration = same_asset / total_open
                    if concentration > 0.40:
                        lot = max(0.01, round(lot * 0.5, 2))
            except Exception:
                pass
            
            # 13. Calcular SL/TP
            atr = market_data.get('atr_14', 50)
            sl_pips = atr * session_config.sl_atr_multiplier
            tp_pips = atr * session_config.tp_atr_multiplier
            
            # 14. Verificar spread máximo
            spread = market_data.get('spread', 0)
            if spread > session_config.max_spread_pips:
                return self._no_signal(asset, f"Spread {spread:.1f} > máximo {session_config.max_spread_pips}")
            
            return {
                'action': signal.action.value,
                'direction': signal.action.value,
                'confidence': round(adjusted_confidence, 4),
                'lot': lot,
                'stop_loss_pips': round(sl_pips, 2),
                'take_profit_pips': round(tp_pips, 2),
                'strategy': agent.strategy_name,
                'agent_id': agent.agent_id,
                'reason': signal.reason,
                'session': self.current_session.value,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def record_trade_result(self, asset: str, agent_id: str, pnl: float,
                            ticket: Optional[int] = None) -> Dict[str, Any]:
        """
        Registra resultado de um trade fechado.

        Fix 3: Kill switch agora usa peak_equity (highwater) e não daily_pnl.
        Fix 8: Idempotência por ticket — evita double-counting quando feedback
        thread e loop principal podem chamar este método para o mesmo trade.

        Args:
            asset: Ativo financeiro
            agent_id: ID do agente que executou
            pnl: Lucro/Prejuízo em USD
            ticket: ID do trade no MT5 (recomendado para idempotência)

        Returns:
            Dict com métricas atualizadas
        """
        with self.lock:
            # Fix 8 — idempotência por ticket
            if ticket is not None:
                if ticket in self._processed_tickets:
                    return {
                        'status': 'DUPLICATE_IGNORED',
                        'ticket': ticket,
                        'asset': asset,
                        'agent_id': agent_id,
                    }
                # marca ANTES de mutar estado para evitar double-count em race
                self._processed_tickets.add(ticket)

            # Atualizar PnL diário
            self.daily_pnl += pnl

            # Atualizar drawdown clássico (mantido para compat e logging)
            if self.daily_pnl < self.daily_drawdown:
                self.daily_drawdown = self.daily_pnl

            # Fix 3 — Highwater mark / peak_equity
            current_equity = self.total_capital + self.daily_pnl
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            # DD% sobre o peak (não sobre capital inicial)
            dd_from_peak = self.peak_equity - current_equity
            dd_pct = (dd_from_peak / self.peak_equity) if self.peak_equity > 0 else 0.0

            if dd_pct >= 0.05:
                self.kill_switch_triggered = True
                return {
                    'error': 'KILL_SWITCH_TRIGGERED',
                    'daily_pnl': self.daily_pnl,
                    'peak_equity': self.peak_equity,
                    'current_equity': current_equity,
                    'drawdown_pct': dd_pct,
                }

            # Atualizar ecossistema
            result = self.ecosystem.update_trade_result(
                asset=asset,
                agent_id=agent_id,
                pnl=pnl,
                session=self.current_session.value
            )

            # Registrar no histórico
            self.trade_history.append({
                'asset': asset,
                'agent_id': agent_id,
                'pnl': pnl,
                'ticket': ticket,
                'session': self.current_session.value,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

            # Remover da lista de posições abertas (Fix 8 — dedup posição)
            if asset in self.open_positions:
                del self.open_positions[asset]

            return result
    
    def register_open_position(self, asset: str, ticket: int,
                               entry_price: float, lot: float,
                               agent_id: str) -> bool:
        """Registra uma posição aberta para rastreamento.

        Fix 8 (CTO) — Dedup de posição: se já existe registro para o mesmo ticket
        em qualquer ativo, retorna False sem sobrescrever (evita race entre
        feedback thread e loop principal).
        """
        with self.lock:
            # Dedup por ticket: se já registrado, ignora
            for existing in self.open_positions.values():
                if existing.get('ticket') == ticket:
                    return False
            self.open_positions[asset] = {
                'ticket': ticket,
                'entry_price': entry_price,
                'lot': lot,
                'agent_id': agent_id,
                'entry_time': datetime.now(timezone.utc).isoformat(),
                'session': self.current_session.value
            }
            return True
    
    def get_open_positions(self) -> Dict[str, Dict]:
        """Retorna posições abertas."""
        with self.lock:
            return self.open_positions.copy()
    
    def get_open_position_count(self) -> int:
        """Retorna número de posições abertas."""
        with self.lock:
            return len(self.open_positions)
    
    def _no_signal(self, asset: str, reason: str) -> Dict[str, Any]:
        """Retorna um sinal HOLD padronizado."""
        return {
            'action': 'HOLD',
            'direction': None,
            'confidence': 0.0,
            'lot': 0.0,
            'stop_loss_pips': 0.0,
            'take_profit_pips': 0.0,
            'strategy': None,
            'agent_id': None,
            'reason': reason,
            'session': self.current_session.value,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _monitor_session_changes(self) -> None:
        """Thread que monitora mudanças de sessão."""
        while True:
            try:
                new_session = self.calibrator.get_current_session()
                if new_session != self.current_session:
                    with self.lock:
                        old_session = self.current_session
                        self.current_session = new_session
                        
                        # Atualizar ativos prioritários
                        self.assets = self.calibrator.get_priority_assets(new_session)
                        
                        print(f"\n[OMEGA] 🔄 MUDANÇA DE SESSÃO: {old_session.value} → {new_session.value}")
                        print(f"[OMEGA] Novos ativos prioritários: {self.assets}")
                        
                        # Rebalancear capital
                        self.ecosystem.rebalance_all()
                
                time.sleep(60)  # Verificar a cada minuto
            except Exception as e:
                print(f"[OMEGA] Erro no monitor de sessão: {e}")
                time.sleep(60)
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo do Orquestrador Global."""
        with self.lock:
            session_config = self.calibrator.get_config(self.current_session)
            
            return {
                'current_session': self.current_session.value,
                'session_description': session_config.description,
                'liquidity_level': session_config.liquidity_level,
                'assets': self.assets,
                'total_capital': self.total_capital,
                'daily_pnl': round(self.daily_pnl, 2),
                'daily_drawdown': round(self.daily_drawdown, 2),
                'drawdown_pct': round((self.peak_equity - (self.total_capital + self.daily_pnl)) / self.peak_equity * 100, 2) if self.peak_equity > 0 else 0,
                'peak_equity': round(self.peak_equity, 2),
                'current_equity': round(self.total_capital + self.daily_pnl, 2),
                'kill_switch_triggered': self.kill_switch_triggered,
                'open_positions': len(self.open_positions),
                'max_positions': session_config.max_positions,
                'session_change_count': self.calibrator._session_change_count,
                'ecosystems': self.ecosystem.get_status() if hasattr(self, 'ecosystem') else {},
                'execution_limits': self.calibrator.get_execution_limits(),
                'detection_thresholds': self.calibrator.get_detection_thresholds()
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa."""
        return self.get_status()


# =============================================================================
# FUNÇÕES DE INTEGRAÇÃO COM SHADOW_LOOP.PY
# =============================================================================

def create_orchestrator(assets: List[str] = None, 
                       total_capital: float = 100000.0) -> OmegaGlobalOrchestrator:
    """
    Factory function para criar o Orquestrador Global.
    
    Deve ser chamada no início do shadow_loop.py.
    
    Exemplo:
        orchestrator = create_orchestrator(
            assets=["XAUUSD", "EURUSD", "GBPUSD"],
            total_capital=DEMO_EQUITY_USD
        )
    """
    return OmegaGlobalOrchestrator(
        assets=assets,
        total_capital=total_capital
    )


def get_trading_signal(orchestrator: OmegaGlobalOrchestrator,
                      asset: str,
                      signature_scores: Dict[str, float] = None,
                      current_positions: List[str] = None) -> Dict[str, Any]:
    """
    Obtém sinal de trading do Orquestrador Global.
    
    Função principal a ser chamada no loop do shadow_loop.py.
    
    Args:
        orchestrator: Instância do OmegaGlobalOrchestrator
        asset: Ativo financeiro
        signature_scores: Assinaturas detectadas (spoofing, iceberg, etc.)
        current_positions: Posições já abertas
        
    Returns:
        Dict com ação, direção, confiança, lote, SL, TP
    """
    return orchestrator.get_signal_for_asset(
        asset=asset,
        signature_scores=signature_scores,
        current_positions=current_positions
    )


def record_trade(orchestrator: OmegaGlobalOrchestrator,
                asset: str, agent_id: str, ticket: int,
                entry_price: float, lot: float) -> None:
    """Registra uma posição aberta no orquestrador."""
    orchestrator.register_open_position(asset, ticket, entry_price, lot, agent_id)


def close_trade(orchestrator: OmegaGlobalOrchestrator,
               asset: str, agent_id: str, pnl: float,
               ticket: Optional[int] = None) -> Dict[str, Any]:
    """Registra fechamento de trade no orquestrador (Fix 8 — propaga ticket)."""
    return orchestrator.record_trade_result(asset, agent_id, pnl, ticket=ticket)


# =============================================================================
# TESTE DE INTEGRIDADE
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" OMEGA GLOBAL ORCHESTRATOR v1.0.0 — TESTE DE INTEGRIDADE")
    print("=" * 70)
    
    # Criar orquestrador
    orchestrator = OmegaGlobalOrchestrator(
        assets=["XAUUSD", "EURUSD", "GBPUSD"],
        total_capital=100000.0
    )
    
    # Status inicial
    status = orchestrator.get_status()
    print(f"\n[STATUS INICIAL]")
    print(f"  Sessão: {status['current_session']}")
    print(f"  Liquidez: {status['liquidity_level']}")
    print(f"  Ativos: {status['assets']}")
    print(f"  Limite de posições: {status['max_positions']}")
    
    # Simular sinais para cada ativo
    print(f"\n[SIMULAÇÃO DE SINAIS]")
    for asset in orchestrator.assets:
        market_data = build_market_data(asset)
        if market_data:
            signal = orchestrator.get_signal_for_asset(asset, market_data)
            if signal['action'] != 'HOLD':
                print(f"  ✅ {asset}: {signal['action']} | "
                      f"Confiança: {signal['confidence']:.2f} | "
                      f"Lote: {signal['lot']} | "
                      f"SL: {signal['stop_loss_pips']} pips | "
                      f"TP: {signal['take_profit_pips']} pips | "
                      f"Estratégia: {signal['strategy']}")
            else:
                print(f"  ⏸️  {asset}: HOLD | {signal['reason']}")
    
    # Simular trades
    print(f"\n[SIMULAÇÃO DE TRADES]")
    for i in range(10):
        asset = np.random.choice(orchestrator.assets)
        agent = orchestrator.ecosystem.get_best_agent_for_asset(asset)
        if agent:
            pnl = np.random.normal(50, 100)
            
            # Registrar abertura
            orchestrator.register_open_position(asset, 1000+i, 2650.50, 0.01, agent.agent_id)
            
            # Registrar fechamento
            result = orchestrator.record_trade_result(asset, agent.agent_id, pnl)
            
            if 'error' not in result:
                print(f"  Trade {i+1}: {asset} via {agent.agent_id} | PnL: ${pnl:+.2f}")
    
    # Status final
    status = orchestrator.get_status()
    print(f"\n[STATUS FINAL]")
    print(f"  PnL diário: ${status['daily_pnl']:,.2f}")
    print(f"  Drawdown: {status['drawdown_pct']:.2f}%")
    print(f"  Kill Switch: {status['kill_switch_triggered']}")
    print(f"  Posições abertas: {status['open_positions']}")
    
    print(f"\n[OK] Módulo M4 — Global Orchestrator — Operacional")
    print(f"[HASH] sha256:m4-global-orchestrator-v1-0-0-20260426")
    print(f"[PASTA] C:\\Users\\Lenovo\\Agent IA Omega\\core\\omega_global_orchestrator.py")
    print("=" * 70)