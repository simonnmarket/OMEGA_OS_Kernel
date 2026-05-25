# =============================================================================
# MÓDULO: omega_session_calibrator.py (M3)
# VERSÃO: 1.0.0
# HASH: sha256:F95BB8492A473060614804B4C8F60B3B187ECA523DB244E435C9F78A4C3AA74A
# RESPONSÁVEL: PSA-WIND / Eng. Chefe
# DATA: 2026-04-26
# =============================================================================
# MÓDULO M3 — CALIBRADOR DE SESSÃO
# core/omega_session_calibrator.py
#
# Emitente: Arquiteto OMEGA (CRO/CTO)
# Etapa: 3 de 5
# Versão: 1.0.0
# Hash do Módulo: sha256:m3-session-calibrator-v1-0-0-20260426
# Pasta de Destino: C:\Users\Lenovo\Agent IA Omega\core\omega_session_calibrator.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA SESSION CALIBRATOR v1.0.0
Módulo M3 — Calibrador de Parâmetros por Sessão de Mercado
Arquiteto OMEGA (CRO/CTO) — 2026-04-26

Ajusta automaticamente parâmetros de trading baseado na sessão atual:
- Thresholds de detecção de assinaturas (spoofing, iceberg, momentum)
- Lote máximo e confiança mínima
- Ativos prioritários e estratégias ativas
- Spread máximo aceitável
- Stop Loss e Take Profit por volatilidade da sessão

Baseado em descobertas da Dark Web:
- Spoofing é mais detectável em baixa liquidez (Ásia)
- Icebergs são mais visíveis em mercados finos
- Thresholds devem ser calibrados por sessão

Hash: sha256:m3-session-calibrator-v1-0-0-20260426
"""

import os
import json
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

import numpy as np


# =============================================================================
# ENUMS
# =============================================================================

class MarketSession(Enum):
    """Sessões de mercado internacional."""
    ASIA = "ASIA"           # 00:00-08:00 UTC
    LONDON = "LONDON"       # 08:00-13:30 UTC
    NEW_YORK = "NEW_YORK"   # 13:30-17:00 UTC
    OVERLAP = "OVERLAP"     # 17:00-21:00 UTC
    CLOSED = "CLOSED"       # 21:00-00:00 UTC


# =============================================================================
# CONFIGURAÇÃO DE SESSÃO
# =============================================================================

@dataclass
class SessionConfig:
    """
    Configuração completa para uma sessão de mercado.
    
    Cada sessão tem parâmetros calibrados baseados em:
    - Liquidez média da sessão
    - Volatilidade histórica
    - Comportamento de outros participantes (spoofing, icebergs)
    - Spreads típicos
    """
    
    session: MarketSession
    
    # Ativos e estratégias
    priority_assets: List[str] = field(default_factory=list)
    active_strategies: List[str] = field(default_factory=list)
    
    # Limites de execução
    max_lot: float = 0.01
    min_confidence: float = 0.65
    max_positions: int = 3
    max_spread_pips: float = 3.0
    
    # Thresholds de detecção de assinaturas
    # (mais baixo = mais sensível)
    spoof_threshold: float = 0.70       # Threshold para detecção de spoofing
    iceberg_threshold: float = 0.60     # Threshold para detecção de icebergs
    momentum_threshold: float = 0.70    # Threshold para momentum ignition
    quote_stuffing_threshold: float = 0.60  # Threshold para quote stuffing
    
    # Parâmetros de risco
    sl_atr_multiplier: float = 2.0      # Multiplicador ATR para Stop Loss
    tp_atr_multiplier: float = 3.0      # Multiplicador ATR para Take Profit
    max_slippage_pips: float = 0.5      # Slippage máximo aceitável
    max_latency_ms: float = 200.0       # Latência máxima aceitável
    
    # Características da sessão
    avg_spread_pips: float = 1.0        # Spread médio histórico
    avg_volatility_pips: float = 50.0   # Volatilidade média (ATR)
    liquidity_level: str = "MEDIUM"     # LOW, MEDIUM, HIGH
    description: str = ""


# =============================================================================
# CATÁLOGO DE CONFIGURAÇÕES POR SESSÃO
# =============================================================================

class SessionConfigCatalog:
    """
    Catálogo de configurações calibradas por sessão.
    
    Baseado em análise histórica de microestrutura:
    - Ásia: baixa liquidez, spoofing mais visível, spreads maiores
    - Londres: alta liquidez, tendências fortes, volume crescente
    - NY: liquidez máxima, competitividade extrema, HFT dominante
    - Overlap: liquidez decrescente, oportunidades em índices/cripto
    """
    
    def __init__(self):
        self._configs: Dict[MarketSession, SessionConfig] = {}
        self._init_default_configs()
    
    def _init_default_configs(self) -> None:
        """Inicializa configurações padrão calibradas para cada sessão."""
        
        # =====================================================================
        # SESSÃO ASIÁTICA (00:00-08:00 UTC)
        # Características: Baixa liquidez, spreads maiores, poucos participantes
        # Edge: Spoofing e icebergs são mais visíveis
        # =====================================================================
        self._configs[MarketSession.ASIA] = SessionConfig(
            session=MarketSession.ASIA,
            priority_assets=[
                "XAUUSD",      # Ouro — alta liquidez 24h
                "AUDUSD",      # Dólar australiano — sessão asiática
                "NZDUSD",      # Dólar neozelandês — sessão asiática
                "USDJPY",      # Iene japonês — sessão asiática
                "BTCUSD",      # FIX #3 — cripto opera 24/7, alta liquidez na Ásia (Coreia/Japão)
                "ETHUSD"       # FIX #3 — idem
            ],
            active_strategies=[
                "SCALPING",        # Curto prazo em baixa volatilidade
                "MEAN_REVERSION",  # Reversão à média em ranges
                "ARBITRAGE"        # Spreads entre ativos correlacionados
            ],
            max_lot=0.005,             # Micro-lote (baixa liquidez)
            min_confidence=0.75,       # Confiança elevada (menos sinais, mais qualidade)
            max_positions=2,           # Máximo 2 posições simultâneas
            max_spread_pips=3.0,       # Spread máximo aceitável
            spoof_threshold=0.60,      # MAIS SENSÍVEL (spoofing visível em baixa liquidez)
            iceberg_threshold=0.50,    # MAIS SENSÍVEL (icebergs detectáveis)
            momentum_threshold=0.55,   # MAIS SENSÍVEL (momentum raro mas significativo)
            quote_stuffing_threshold=0.50,  # MAIS SENSÍVEL
            sl_atr_multiplier=2.5,     # SL mais amplo (volatilidade imprevisível)
            tp_atr_multiplier=1.5,     # TP mais curto (movimentos menores)
            max_slippage_pips=0.8,     # Mais tolerante a slippage
            max_latency_ms=300.0,      # Mais tolerante a latência
            avg_spread_pips=2.0,       # Spread médio histórico
            avg_volatility_pips=30.0,  # Volatilidade média (ATR)
            liquidity_level="LOW",
            description="Baixa liquidez, spoofing/iceberg mais detectáveis. Foco em metais e pares asiáticos."
        )
        
        # =====================================================================
        # SESSÃO DE LONDRES (08:00-13:30 UTC)
        # Características: Alta liquidez, tendências fortes, institucionais ativos
        # Edge: Breakouts e trend following funcionam bem
        # =====================================================================
        self._configs[MarketSession.LONDON] = SessionConfig(
            session=MarketSession.LONDON,
            priority_assets=[
                "EURUSD",      # Euro — principal par europeu
                "GBPUSD",      # Libra — sessão britânica
                "USDJPY",      # Iene — ativo nos cruzes europeus
                "AUDUSD",      # Aussie — liquido em abertura Londres
                "XAUUSD",      # Ouro — alta liquidez
                "GER40",       # Índice alemão — mercado europeu
                "BTCUSD",      # FIX #3 — cripto incluso
                "ETHUSD"       # FIX #3 — cripto incluso
            ],
            active_strategies=[
                "TREND_FOLLOWING",  # Tendências fortes na abertura
                "BREAKOUT",         # Rompimentos com volume
                "MOMENTUM",         # Aceleração de preço
                "ADAPTIVE"          # Adaptativa para múltiplos cenários
            ],
            max_lot=0.01,              # Lote padrão
            min_confidence=0.65,       # Confiança padrão
            max_positions=3,           # Máximo 3 posições
            max_spread_pips=2.0,       # Spread controlado
            spoof_threshold=0.75,      # PADRÃO (mais ruído = mais difícil detectar)
            iceberg_threshold=0.65,    # PADRÃO
            momentum_threshold=0.70,   # PADRÃO
            quote_stuffing_threshold=0.70,  # PADRÃO
            sl_atr_multiplier=2.0,     # SL padrão
            tp_atr_multiplier=3.0,     # TP padrão
            max_slippage_pips=0.5,     # Slippage controlado
            max_latency_ms=200.0,      # Latência padrão
            avg_spread_pips=1.0,       # Spread médio histórico
            avg_volatility_pips=50.0,  # Volatilidade média (ATR)
            liquidity_level="HIGH",
            description="Alta liquidez, tendências fortes. Foco em forex europeu e índices."
        )
        
        # =====================================================================
        # SESSÃO DE NEW YORK (13:30-17:00 UTC)
        # Características: Liquidez máxima, HFT dominante, volatilidade alta
        # Edge: Market making e momentum capturam movimentos rápidos
        # =====================================================================
        self._configs[MarketSession.NEW_YORK] = SessionConfig(
            session=MarketSession.NEW_YORK,
            priority_assets=[
                "XAUUSD",      # Ouro — máxima liquidez
                "EURUSD",      # Euro — sobreposição com Londres
                "GBPUSD",      # Libra — sobreposição
                "USDJPY",      # Iene — ativo durante NY
                "AUDUSD",      # Aussie — liquido em NY
                "USDCAD",      # Loonie — petróleo / dados CAD
                "US500",       # S&P 500 — mercado americano
                "NAS100",      # NASDAQ — tecnologia
                "BTCUSD",      # FIX #3 — NY é sessão de pico de volume cripto USD
                "ETHUSD"       # FIX #3 — idem
            ],
            active_strategies=[
                "MOMENTUM",         # Movimentos rápidos
                "MARKET_MAKING",    # Spread capture em alta liquidez
                "TREND_FOLLOWING",  # Tendências intraday
                "BREAKOUT",         # Rompimentos com notícias
                "ADAPTIVE"          # Adaptativa
            ],
            max_lot=0.01,              # Lote padrão
            min_confidence=0.65,       # Confiança padrão
            max_positions=3,           # Máximo 3 posições
            max_spread_pips=1.5,       # Spread mais apertado
            spoof_threshold=0.85,      # MAIS RESTRITIVO (muito ruído = falsos positivos)
            iceberg_threshold=0.75,    # MAIS RESTRITIVO
            momentum_threshold=0.80,   # MAIS RESTRITIVO
            quote_stuffing_threshold=0.80,  # MAIS RESTRITIVO
            sl_atr_multiplier=2.0,     # SL padrão
            tp_atr_multiplier=2.5,     # TP ligeiramente reduzido (movimentos rápidos)
            max_slippage_pips=0.3,     # Menos tolerante (alta liquidez)
            max_latency_ms=100.0,      # Latência crítica (HFT)
            avg_spread_pips=0.5,       # Spread muito baixo
            avg_volatility_pips=60.0,  # Volatilidade alta
            liquidity_level="MAXIMUM",
            description="Liquidez máxima, HFT dominante. Foco em todos os ativos principais."
        )
        
        # =====================================================================
        # SESSÃO OVERLAP (17:00-21:00 UTC)
        # Características: Liquidez decrescente, índices e cripto ativos
        # Edge: Arbitragem e adaptativa em mercados de transição
        # =====================================================================
        # OVERLAP — FIX #3: SOL/DOG incluídos
        self._configs[MarketSession.OVERLAP] = SessionConfig(
            session=MarketSession.OVERLAP,
            priority_assets=[
                "US500",       # S&P 500 — after-hours
                "NAS100",      # NASDAQ — after-hours
                "BTCUSD",      # Bitcoin — mercado 24h
                "ETHUSD",      # Ethereum — mercado 24h
                "XAUUSD",      # Ouro — liquidez residual
                "SOLUSD",      # FIX #3 — altcoin com volume relevante em OVERLAP
                "DOGUSD"       # FIX #3 — altcoin de retail, alta atividade após NY
            ],
            active_strategies=[
                "ADAPTIVE",         # Adaptativa para transição
                "ARBITRAGE",        # Spreads entre ativos
                "MEAN_REVERSION",   # Reversão em mercados de baixa liquidez
                "SCALPING",         # FIX #4 — SCALPING para cobrir cripto,
                "MARKET_MAKING"     # Spread capture residual
            ],
            max_lot=0.01,              # Lote padrão
            min_confidence=0.70,       # Confiança elevada
            max_positions=2,           # Máximo 2 posições
            max_spread_pips=2.5,       # Spread mais largo
            spoof_threshold=0.70,      # INTERMEDIÁRIO
            iceberg_threshold=0.60,    # INTERMEDIÁRIO
            momentum_threshold=0.65,   # INTERMEDIÁRIO
            quote_stuffing_threshold=0.65,  # INTERMEDIÁRIO
            sl_atr_multiplier=2.0,     # SL padrão
            tp_atr_multiplier=2.5,     # TP moderado
            max_slippage_pips=0.6,     # Moderadamente tolerante
            max_latency_ms=250.0,      # Moderadamente tolerante
            avg_spread_pips=1.5,       # Spread moderado
            avg_volatility_pips=45.0,  # Volatilidade moderada
            liquidity_level="MEDIUM",
            description="Transição NY→Ásia. Foco em índices US e criptomoedas."
        )
        
        # =====================================================================
        # MERCADO FECHADO (21:00-00:00 UTC)
        # =====================================================================
        self._configs[MarketSession.CLOSED] = SessionConfig(
            session=MarketSession.CLOSED,
            priority_assets=["BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD"],  # FIX #3 — cripto 24h ampliado
            # FIX #8 — habilita MEAN_REVERSION + SCALPING em CLOSED para operar cripto noturna
            # (overnight 21-00 UTC). MARKET_MAKING isolado nunca emite em fim-de-semana.
            active_strategies=["MARKET_MAKING", "ADAPTIVE", "MEAN_REVERSION", "SCALPING"],
            max_lot=0.005,
            min_confidence=0.75,       # FIX #8 — relaxado de 0.85 → 0.75 (ainda alto; FIX #4 dinâmico)
            max_positions=1,
            max_spread_pips=5.0,
            spoof_threshold=0.50,
            iceberg_threshold=0.40,
            momentum_threshold=0.50,
            quote_stuffing_threshold=0.40,
            sl_atr_multiplier=3.0,
            tp_atr_multiplier=1.5,
            max_slippage_pips=1.0,
            max_latency_ms=500.0,
            avg_spread_pips=3.0,
            avg_volatility_pips=20.0,
            liquidity_level="MINIMUM",
            description="Mercado praticamente fechado. Apenas criptomoedas com precaução extrema."
        )

        # CEO 2026-05-25: ecossistema unificado — mesmo portfolio + max_positions em todas as sessões
        try:
            from modules.omega_ecosystem_unified import apply_unified_session_catalog

            apply_unified_session_catalog(self)
        except Exception:
            pass

    def get_config(self, session: MarketSession) -> SessionConfig:
        """Retorna configuração para uma sessão, com override via env var."""
        cfg = self._configs.get(session, self._configs[MarketSession.CLOSED])
        _env_conf = os.getenv("OMEGA_MIN_CONFIDENCE")
        if _env_conf is not None:
            try:
                import dataclasses
                cfg = dataclasses.replace(cfg, min_confidence=float(_env_conf))
            except Exception:
                pass
        try:
            from modules.omega_ecosystem_unified import is_unified_mode, get_unified_max_positions

            if is_unified_mode():
                import dataclasses

                cfg = dataclasses.replace(cfg, max_positions=get_unified_max_positions(cfg.max_positions))
        except Exception:
            pass
        return cfg
    
    def get_all_configs(self) -> Dict[MarketSession, SessionConfig]:
        """Retorna todas as configurações."""
        return self._configs.copy()


# =============================================================================
# CALIBRADOR DE SESSÃO
# =============================================================================

class SessionCalibrator:
    """
    Calibrador dinâmico de parâmetros por sessão de mercado.
    
    Funcionalidades:
    - Detecta automaticamente a sessão atual
    - Retorna parâmetros calibrados para execução
    - Filtra ativos e estratégias por sessão
    - Ajusta thresholds de detecção de assinaturas
    - Fornece limites de risco por sessão
    """
    
    def __init__(self, config_catalog: Optional[SessionConfigCatalog] = None):
        self.catalog = config_catalog or SessionConfigCatalog()
        self._current_session: Optional[MarketSession] = None
        self._session_change_count: int = 0
        self._last_session_check: str = ""
    
    def get_current_session(self) -> MarketSession:
        """
        Detecta automaticamente a sessão atual baseado no horário UTC.
        
        Returns:
            MarketSession correspondente ao horário atual
        """
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        if 0 <= hour < 8:
            session = MarketSession.ASIA
        elif 8 <= hour < 13:
            session = MarketSession.LONDON
        elif 13 <= hour < 17:
            session = MarketSession.NEW_YORK
        elif 17 <= hour < 21:
            session = MarketSession.OVERLAP
        else:
            session = MarketSession.CLOSED
        
        # Detectar mudança de sessão
        if self._current_session != session:
            if self._current_session is not None:
                self._session_change_count += 1
            self._current_session = session
            self._last_session_check = datetime.now(timezone.utc).isoformat()
        
        return session
    
    def get_config(self, session: Optional[MarketSession] = None) -> SessionConfig:
        """Retorna configuração para a sessão atual ou especificada."""
        if session is None:
            session = self.get_current_session()
        return self.catalog.get_config(session)
    
    def get_priority_assets(self, session: Optional[MarketSession] = None) -> List[str]:
        """Retorna ativos prioritários para a sessão."""
        config = self.get_config(session)
        return config.priority_assets
    
    def get_active_strategies(self, session: Optional[MarketSession] = None) -> List[str]:
        """Retorna estratégias ativas para a sessão."""
        config = self.get_config(session)
        return config.active_strategies
    
    def get_execution_limits(self, session: Optional[MarketSession] = None) -> Dict[str, Any]:
        """
        Retorna limites de execução para a sessão.
        
        Returns:
            Dict com max_lot, min_confidence, max_positions, etc.
        """
        config = self.get_config(session)
        return {
            'max_lot': config.max_lot,
            'min_confidence': config.min_confidence,
            'max_positions': config.max_positions,
            'max_spread_pips': config.max_spread_pips,
            'max_slippage_pips': config.max_slippage_pips,
            'max_latency_ms': config.max_latency_ms,
            'sl_atr_multiplier': config.sl_atr_multiplier,
            'tp_atr_multiplier': config.tp_atr_multiplier
        }
    
    def get_detection_thresholds(self, session: Optional[MarketSession] = None) -> Dict[str, float]:
        """
        Retorna thresholds de detecção de assinaturas para a sessão.
        
        Returns:
            Dict com spoof_threshold, iceberg_threshold, etc.
        """
        config = self.get_config(session)
        return {
            'spoof_threshold': config.spoof_threshold,
            'iceberg_threshold': config.iceberg_threshold,
            'momentum_threshold': config.momentum_threshold,
            'quote_stuffing_threshold': config.quote_stuffing_threshold
        }
    
    def filter_assets_by_session(self, assets: List[str], 
                                 session: Optional[MarketSession] = None) -> List[str]:
        """Filtra lista de ativos pelos prioritários da sessão."""
        priority = self.get_priority_assets(session)
        return [a for a in assets if a in priority]
    
    def get_session_metadata(self, session: Optional[MarketSession] = None) -> Dict[str, Any]:
        """Retorna metadados da sessão atual."""
        config = self.get_config(session)
        return {
            'session': config.session.value,
            'liquidity_level': config.liquidity_level,
            'avg_spread_pips': config.avg_spread_pips,
            'avg_volatility_pips': config.avg_volatility_pips,
            'description': config.description,
            'session_change_count': self._session_change_count,
            'last_session_check': self._last_session_check
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa."""
        all_configs = {}
        for session, config in self.catalog.get_all_configs().items():
            all_configs[session.value] = {
                'priority_assets': config.priority_assets,
                'active_strategies': config.active_strategies,
                'max_lot': config.max_lot,
                'min_confidence': config.min_confidence,
                'max_positions': config.max_positions,
                'max_spread_pips': config.max_spread_pips,
                'spoof_threshold': config.spoof_threshold,
                'iceberg_threshold': config.iceberg_threshold,
                'momentum_threshold': config.momentum_threshold,
                'liquidity_level': config.liquidity_level,
                'description': config.description
            }
        
        return {
            'current_session': self.get_current_session().value,
            'session_change_count': self._session_change_count,
            'configs': all_configs
        }


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def get_effective_min_confidence(base_min_confidence: float,
                                 total_trades: int,
                                 warmup_trades: int = 20,
                                 juvenile_trades: int = 100) -> float:
    """FIX #4 — min_confidence dinâmico por maturidade do agente.

    Em cold-start (total_trades=0) o `risk_adj_conf` é matematicamente
    limitado a 0.50 × 0.333 ≈ 0.167. Min_conf base de 0.65–0.85 é
    inalcançável → HOLD eterno. Este helper relaxa o threshold em
    duas fases (warmup ×0.50, juvenil ×0.75) até maturidade.

    Args:
        base_min_confidence: limiar maduro (de SessionConfig.min_confidence)
        total_trades: histórico do agente
        warmup_trades: limite superior da fase warmup (×0.50 de relax)
        juvenile_trades: limite superior da fase juvenil (×0.75 de relax)

    Returns:
        threshold efetivo aplicado nesta tentativa de sinal.
    """
    if total_trades < warmup_trades:
        return round(base_min_confidence * 0.50, 4)
    if total_trades < juvenile_trades:
        return round(base_min_confidence * 0.75, 4)
    return float(base_min_confidence)

def get_session_for_hour(hour: int) -> MarketSession:
    """Retorna a sessão para uma hora específica (0-23)."""
    if 0 <= hour < 8:
        return MarketSession.ASIA
    elif 8 <= hour < 13:
        return MarketSession.LONDON
    elif 13 <= hour < 17:
        return MarketSession.NEW_YORK
    elif 17 <= hour < 21:
        return MarketSession.OVERLAP
    else:
        return MarketSession.CLOSED


def get_session_trading_hours(session: MarketSession) -> Tuple[int, int]:
    """Retorna horário de início e fim de uma sessão (UTC)."""
    hours = {
        MarketSession.ASIA: (0, 8),
        MarketSession.LONDON: (8, 13),
        MarketSession.NEW_YORK: (13, 17),
        MarketSession.OVERLAP: (17, 21),
        MarketSession.CLOSED: (21, 24)
    }
    return hours.get(session, (0, 0))


# =============================================================================
# TESTE DE INTEGRIDADE
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" OMEGA SESSION CALIBRATOR v1.0.0 — TESTE DE INTEGRIDADE")
    print("=" * 70)
    
    calibrator = SessionCalibrator()
    
    # Detectar sessão atual
    session = calibrator.get_current_session()
    print(f"\n[SESSÃO ATUAL] {session.value}")
    
    # Exibir configuração completa
    config = calibrator.get_config(session)
    print(f"\n[CONFIGURAÇÃO] {session.value}:")
    print(f"  Descrição: {config.description}")
    print(f"  Liquidez: {config.liquidity_level}")
    print(f"  Spread médio: {config.avg_spread_pips} pips")
    print(f"  Volatilidade média: {config.avg_volatility_pips} pips")
    
    print(f"\n  [ATIVOS PRIORITÁRIOS] ({len(config.priority_assets)}):")
    for a in config.priority_assets:
        print(f"    - {a}")
    
    print(f"\n  [ESTRATÉGIAS ATIVAS] ({len(config.active_strategies)}):")
    for s in config.active_strategies:
        print(f"    - {s}")
    
    print(f"\n  [LIMITES DE EXECUÇÃO]:")
    limits = calibrator.get_execution_limits(session)
    for k, v in limits.items():
        print(f"    {k}: {v}")
    
    print(f"\n  [THRESHOLDS DE DETECÇÃO]:")
    thresholds = calibrator.get_detection_thresholds(session)
    for k, v in thresholds.items():
        print(f"    {k}: {v}")
    
    # Exibir todas as sessões
    print(f"\n{'='*70}")
    print(f" TODAS AS SESSÕES")
    print(f"{'='*70}")
    
    for sess in MarketSession:
        if sess == MarketSession.CLOSED:
            continue
        cfg = calibrator.get_config(sess)
        print(f"\n  {sess.value} ({cfg.liquidity_level} liquidez):")
        print(f"    Ativos: {', '.join(cfg.priority_assets[:4])}...")
        print(f"    Estratégias: {', '.join(cfg.active_strategies[:3])}...")
        print(f"    Lote máx: {cfg.max_lot} | Confiança mín: {cfg.min_confidence}")
        print(f"    Spoof threshold: {cfg.spoof_threshold} | Iceberg: {cfg.iceberg_threshold}")
    
    # Testar filtro de ativos
    all_assets = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "US500", "GER40"]
    filtered = calibrator.filter_assets_by_session(all_assets)
    print(f"\n[FILTRO DE ATIVOS] {len(all_assets)} → {len(filtered)} para sessão {session.value}")
    print(f"  Ativos filtrados: {filtered}")
    
    # Metadados
    meta = calibrator.get_session_metadata()
    print(f"\n[METADADOS]")
    for k, v in meta.items():
        print(f"  {k}: {v}")
    
    print(f"\n[OK] Módulo M3 — Session Calibrator — Operacional")
    print(f"[HASH] sha256:m3-session-calibrator-v1-0-0-20260426")
    print(f"[PASTA] C:\\Users\\Lenovo\\Agent IA Omega\\core\\omega_session_calibrator.py")
    print("=" * 70)