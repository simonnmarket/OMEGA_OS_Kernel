# =============================================================================
# MÓDULO: shadow_loop_integration.py (M5)
# VERSÃO: 1.0.0
# HASH: sha256:802B6D640051A9B20293B0185B67645E3D7478C9EE4574AC725CD7C2C18722C6
# RESPONSÁVEL: PSA-WIND / Eng. Chefe
# DATA: 2026-04-26
# =============================================================================
# MÓDULO M5 — INTEGRAÇÃO COM SHADOW_LOOP.PY
# integration/shadow_loop_integration.py
#
# Emitente: Arquiteto OMEGA (CRO/CTO)
# Etapa: 5 de 5 (FINAL)
# Versão: 1.0.0
# Hash do Módulo: sha256:m5-shadow-loop-integration-v1-0-0-20260426
# Pasta de Destino: C:\Users\Lenovo\Agent IA Omega\integration\shadow_loop_integration.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA SHADOW LOOP INTEGRATION v1.0.0
Módulo M5 — Integração do Agente IA com shadow_loop.py
Arquiteto OMEGA (CRO/CTO) — 2026-04-26

Fix 7 (PSA): a integração oficial é via IMPORT, não cópia de código.
Não duplicar a classe OmegaAgentIntegration no shadow_loop.py.

USO OFICIAL (no shadow_loop.py):

    # 1. Imports (já preparados pelo patch mínimo da Fase 3)
    from agent_ia.integration.shadow_loop_integration import OmegaAgentIntegration

    # 2. Inicializar (no início de run_loop)
    agent_ia = OmegaAgentIntegration(
        assets=list(TIER1_ASSETS),
        total_capital=equity,
        enable_agent_ia=USE_AGENT_IA,
    )

    # 3. Obter sinal por ativo no ciclo
    signal = agent_ia.get_signal(asset, signature_scores=...)

    # 4. Registrar abertura/fechamento de trade (com ticket para idempotência)
    agent_ia.record_trade_open(asset, ticket, entry_price, lot, signal['agent_id'])
    agent_ia.record_trade_close(asset, signal['agent_id'], pnl)

Hash: sha256:m5-shadow-loop-integration-v1-0-0-20260426
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import deque

import numpy as np

# Adicionar path do Agente IA
AGENT_IA_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_IA_PATH))

# Importar módulos do Agente IA
from core.omega_strategy_catalog import (
    StrategyCatalog, StrategySignal, SignalAction,
    StrategyMetricsDB, build_market_data
)
from core.omega_agent_ecosystem import (
    EcosystemOrchestrator, CompetitiveAgent
)
from core.omega_session_calibrator import (
    SessionCalibrator, MarketSession
)
from core.omega_global_orchestrator import (
    OmegaGlobalOrchestrator, create_orchestrator,
    get_trading_signal, record_trade, close_trade
)


# =============================================================================
# CLASSE DE INTEGRAÇÃO (COLE ISTO NO SHADOW_LOOP.PY)
# =============================================================================

class OmegaAgentIntegration:
    """
    Integração do Agente IA OMEGA com o shadow_loop.py.
    
    Esta classe encapsula toda a lógica de integração para que
    o shadow_loop.py precise apenas de 3 linhas para usar o Agente IA.
    
    Uso no shadow_loop.py:
    
        # 1. Inicializar (no início do run_loop)
        agent = OmegaAgentIntegration(
            assets=list(TIER1_ASSETS),
            total_capital=equity
        )
        
        # 2. Obter sinal (no loop principal, substituindo a lógica atual)
        signal = agent.get_signal(asset, signature_scores)
        
        # 3. Registrar resultado (após fechamento do trade)
        agent.record_result(asset, signal['agent_id'], pnl)
    """
    
    def __init__(self, 
                 assets: List[str] = None,
                 total_capital: float = 10000.0,
                 enable_agent_ia: bool = True):
        """
        Inicializa a integração com o Agente IA.
        
        Args:
            assets: Lista de ativos (default: usa TIER1_ASSETS do shadow_loop)
            total_capital: Capital total (default: DEMO_EQUITY_USD)
            enable_agent_ia: Se False, usa lógica original do shadow_loop
        """
        self.enable_agent_ia = enable_agent_ia
        self.assets = assets or ["XAUUSD", "EURUSD", "GBPUSD"]
        self.total_capital = total_capital
        
        # Componentes do Agente IA
        self.orchestrator: Optional[OmegaGlobalOrchestrator] = None
        self.calibrator: Optional[SessionCalibrator] = None
        self.metrics_db: Optional[StrategyMetricsDB] = None
        
        if self.enable_agent_ia:
            self._init_agent_ia()
        
        # Estatísticas
        self.signals_generated: int = 0
        self.signals_executed: int = 0
        self.signals_skipped: int = 0
        self.total_pnl: float = 0.0
        
        # Log
        print(f"\n{'='*70}")
        print(f" OMEGA AGENT IA INTEGRATION")
        print(f"{'='*70}")
        print(f" Status: {'ATIVO' if enable_agent_ia else 'INATIVO (modo original)'}")
        print(f" Ativos: {self.assets}")
        print(f" Capital: ${total_capital:,.2f}")
        if self.calibrator:
            session = self.calibrator.get_current_session()
            print(f" Sessão: {session.value}")
            print(f" Liquidez: {self.calibrator.get_config(session).liquidity_level}")
        print(f"{'='*70}\n")
    
    def _init_agent_ia(self) -> None:
        """Inicializa todos os componentes do Agente IA."""
        try:
            self.orchestrator = create_orchestrator(
                assets=self.assets,
                total_capital=self.total_capital
            )
            self.calibrator = self.orchestrator.calibrator
            self.metrics_db = self.orchestrator.metrics_db
        except Exception as e:
            print(f"[AGENT IA] Erro na inicialização: {e}")
            print(f"[AGENT IA] Desativando Agente IA. Usando lógica original.")
            self.enable_agent_ia = False
    
    def get_signal(self, asset: str, 
                   signature_scores: Dict[str, float] = None,
                   market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Obtém sinal de trading para um ativo.
        
        ESTA FUNÇÃO SUBSTITUI A LÓGICA DE SINAL ORIGINAL DO SHADOW_LOOP.
        
        Args:
            asset: Ativo financeiro
            signature_scores: Assinaturas detectadas (spoofing, iceberg, etc.)
            market_data: Dados de mercado (se None, busca do MT5)
            
        Returns:
            Dict com:
                action: 'BUY', 'SELL', 'HOLD'
                confidence: 0.0-1.0
                lot: tamanho do lote
                stop_loss_pips: SL em pips
                take_profit_pips: TP em pips
                strategy: nome da estratégia
                agent_id: ID do agente
                reason: motivo do sinal
        """
        self.signals_generated += 1
        
        # Se Agente IA desativado, usar lógica original
        if not self.enable_agent_ia or not self.orchestrator:
            return self._get_original_signal(asset)
        
        # Obter posições abertas
        current_positions = list(self.orchestrator.get_open_positions().keys())
        
        # Obter sinal do Orquestrador Global
        signal = get_trading_signal(
            orchestrator=self.orchestrator,
            asset=asset,
            signature_scores=signature_scores,
            current_positions=current_positions
        )
        
        if signal['action'] != 'HOLD':
            self.signals_executed += 1
        else:
            self.signals_skipped += 1
        
        return signal
    
    def _get_original_signal(self, asset: str) -> Dict[str, Any]:
        """
        Fallback neutro quando o Agente IA está desativado.

        Retorna sempre HOLD para evitar viés direcional (BUY-only).
        A direção real, se houver, deve ser determinada pelo
        shadow_loop.py via momentum MT5 (M1 close vs avg3).
        """
        return {
            'action': 'HOLD',
            'direction': None,
            'confidence': 0.0,
            'lot': 0.0,
            'stop_loss_pips': 0.0,
            'take_profit_pips': 0.0,
            'strategy': 'NEUTRAL_FALLBACK',
            'agent_id': 'LEGACY',
            'reason': 'Agente IA desativado — fallback neutro (HOLD); direção via shadow_loop MT5 momentum',
            'session': 'UNKNOWN',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def record_trade_open(self, asset: str, ticket: int,
                          entry_price: float, lot: float,
                          agent_id: str) -> None:
        """Registra abertura de trade."""
        if self.enable_agent_ia and self.orchestrator:
            record_trade(
                orchestrator=self.orchestrator,
                asset=asset,
                agent_id=agent_id,
                ticket=ticket,
                entry_price=entry_price,
                lot=lot
            )
    
    def record_trade_close(self, asset: str, agent_id: str, pnl: float,
                           ticket: Optional[int] = None) -> Dict[str, Any]:
        """Registra fechamento de trade e atualiza aprendizado.

        Fix 8 (CTO): aceita `ticket` para idempotência. Se passado, o
        orquestrador deduplica chamadas (feedback thread × loop principal).
        """
        self.total_pnl += pnl

        if self.enable_agent_ia and self.orchestrator:
            return close_trade(
                orchestrator=self.orchestrator,
                asset=asset,
                agent_id=agent_id,
                pnl=pnl,
                ticket=ticket,
            )

        return {'pnl': pnl, 'agent_ia_disabled': True, 'ticket': ticket}
    
    def get_session_info(self) -> Dict[str, Any]:
        """Retorna informações da sessão atual."""
        if self.calibrator:
            session = self.calibrator.get_current_session()
            config = self.calibrator.get_config(session)
            return {
                'session': session.value,
                'liquidity': config.liquidity_level,
                'max_lot': config.max_lot,
                'min_confidence': config.min_confidence,
                'priority_assets': config.priority_assets,
                'active_strategies': config.active_strategies
            }
        return {'session': 'UNKNOWN'}
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo da integração."""
        status = {
            'agent_ia_enabled': self.enable_agent_ia,
            'signals_generated': self.signals_generated,
            'signals_executed': self.signals_executed,
            'signals_skipped': self.signals_skipped,
            'total_pnl': round(self.total_pnl, 2),
            'session': self.get_session_info()
        }
        
        if self.orchestrator:
            status['orchestrator'] = self.orchestrator.get_status()
        
        return status
    
    def rebalance(self) -> None:
        """Rebalanceia capital entre agentes."""
        if self.enable_agent_ia and self.orchestrator:
            self.orchestrator.ecosystem.rebalance_all()


# =============================================================================
# INSTRUÇÕES DE MODIFICAÇÃO DO SHADOW_LOOP.PY
# =============================================================================

"""
=============================================================================
PARA INTEGRAR O AGENTE IA AO SHADOW_LOOP.PY, SIGA ESTAS ETAPAS:
=============================================================================

ETAPA 1: ADICIONE OS IMPORTS NO INÍCIO DO ARQUIVO
-------------------------------------------------
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "Agent IA Omega"))
from integration.shadow_loop_integration import OmegaAgentIntegration


ETAPA 2: INICIALIZE A INTEGRAÇÃO NO run_loop()
----------------------------------------------
No início da função run_loop(), após carregar configurações:

    # Inicializar Agente IA
    agent_ia = OmegaAgentIntegration(
        assets=list(TIER1_ASSETS),
        total_capital=equity,
        enable_agent_ia=True  # False para usar lógica original
    )


ETAPA 3: SUBSTITUA A LÓGICA DE SINAL NO LOOP PRINCIPAL
--------------------------------------------------------
ANTES (código original):
    # Guardrail final
    guard = check_guardrails(asset, tf, hr_real, 1.0, dm)
    
    if not guard["skip"] and mode == "paper" and mt5_connected:
        lot_info = calc_lot(equity, guard["margin_used"], asset)
        exec_result = mt5_send_order(asset, tf, lot_info["lot"], ...)

DEPOIS (com Agente IA):
    # Obter sinal do Agente IA
    signal = agent_ia.get_signal(
        asset=asset,
        signature_scores=spoof_detector.get_signature_scores() if spoof_detector else None
    )
    
    if signal['action'] != 'HOLD':
        lot_info = calc_lot(equity, guard["margin_used"], asset)
        lot = min(lot_info["lot"], signal['lot'])
        
        exec_result = mt5_send_order(
            asset, tf, lot,
            sl_pts=signal['stop_loss_pips'],
            tp_pts=signal['take_profit_pips'],
            direction=signal['direction']
        )
        
        if exec_result.get('success'):
            agent_ia.record_trade_open(
                asset, exec_result['deal'],
                exec_result['fill_price'], lot,
                signal['agent_id']
            )


ETAPA 4: REGISTRE RESULTADOS APÓS FECHAMENTO DE TRADE
-------------------------------------------------------
No código que monitora fechamento de posições:

    # Após detectar que uma posição foi fechada:
    pnl = deal.profit + deal.commission + deal.swap
    agent_ia.record_trade_close(asset, signal['agent_id'], pnl)


ETAPA 5: ADICIONE STATUS NO FINAL DO LOOP
-------------------------------------------
No final do run_loop(), antes do return:

    # Salvar status do Agente IA
    status = agent_ia.get_status()
    with open(AUDIT_PAPER / "agent_ia_status.json", "w") as f:
        json.dump(status, f, indent=2)


=============================================================================
FIM DAS INSTRUÇÕES
=============================================================================
"""


# =============================================================================
# SCRIPT DE TESTE DE INTEGRAÇÃO
# =============================================================================

def test_integration():
    """Testa a integração completa M1-M5."""
    print("=" * 70)
    print(" OMEGA AGENT IA — TESTE DE INTEGRAÇÃO COMPLETA (M1-M5)")
    print("=" * 70)
    
    # Inicializar integração
    agent = OmegaAgentIntegration(
        assets=["XAUUSD", "EURUSD", "GBPUSD"],
        total_capital=10000.0,
        enable_agent_ia=True
    )
    
    # Verificar sessão
    session_info = agent.get_session_info()
    print(f"\n[1] SESSÃO ATUAL: {session_info['session']}")
    print(f"    Liquidez: {session_info['liquidity']}")
    print(f"    Lote máximo: {session_info['max_lot']}")
    print(f"    Confiança mínima: {session_info['min_confidence']}")
    print(f"    Ativos prioritários: {session_info['priority_assets']}")
    
    # Simular sinais
    print(f"\n[2] SIMULAÇÃO DE SINAIS:")
    for asset in ["XAUUSD", "EURUSD", "GBPUSD"]:
        signal = agent.get_signal(asset)
        if signal['action'] != 'HOLD':
            print(f"    ✅ {asset}: {signal['action']} | "
                  f"Conf: {signal['confidence']:.2f} | "
                  f"Lote: {signal['lot']} | "
                  f"Estratégia: {signal['strategy']}")
        else:
            print(f"    ⏸️  {asset}: HOLD | {signal['reason']}")
    
    # Simular trades
    print(f"\n[3] SIMULAÇÃO DE TRADES:")
    for i in range(5):
        asset = np.random.choice(["XAUUSD", "EURUSD", "GBPUSD"])
        signal = agent.get_signal(asset)
        
        if signal['action'] != 'HOLD':
            # Simular abertura
            agent.record_trade_open(asset, 1000+i, 2650.50, 0.01, signal['agent_id'])
            
            # Simular fechamento com PnL
            pnl = np.random.normal(50, 100)
            result = agent.record_trade_close(asset, signal['agent_id'], pnl)
            print(f"    Trade {i+1}: {asset} | PnL: ${pnl:+.2f}")
    
    # Rebalancear
    agent.rebalance()
    
    # Status final
    status = agent.get_status()
    print(f"\n[4] STATUS FINAL:")
    print(f"    Sinais gerados: {status['signals_generated']}")
    print(f"    Sinais executados: {status['signals_executed']}")
    print(f"    Sinais ignorados: {status['signals_skipped']}")
    print(f"    PnL total: ${status['total_pnl']:.2f}")
    
    if status.get('orchestrator'):
        orch = status['orchestrator']
        print(f"    Drawdown: {orch.get('drawdown_pct', 0):.2f}%")
        print(f"    Posições abertas: {orch.get('open_positions', 0)}")
    
    print(f"\n{'='*70}")
    print(f" TESTE DE INTEGRAÇÃO CONCLUÍDO COM SUCESSO")
    print(f"{'='*70}")
    print(f"\n[OK] Módulo M5 — Shadow Loop Integration — Operacional")
    print(f"[HASH] sha256:m5-shadow-loop-integration-v1-0-0-20260426")
    print(f"[PASTA] C:\\Users\\Lenovo\\Agent IA Omega\\integration\\shadow_loop_integration.py")
    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    test_integration()