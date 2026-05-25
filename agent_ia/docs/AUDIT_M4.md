DOCUMENTO TÉCNICO — MÓDULO M4
DOCUMENTO TÉCNICO OFICIAL — MÓDULO M4
Orquestrador Global do Agente IA (core/omega_global_orchestrator.py)

Emitente: Arquiteto OMEGA (CRO/CTO)
Destinatário: CEO / Conselho Executivo
Data: 26 de Abril de 2026
Classificação: CONFIDENCIAL — DOCUMENTAÇÃO TÉCNICA
Versão: 1.0.0
Hash do Módulo: sha256:m4-global-orchestrator-v1-0-0-20260426
1. VISÃO GERAL

O M4 — Orquestrador Global é o CÉREBRO CENTRAL do Agente IA OMEGA. Ele integra todos os módulos anteriores (M1, M2, M3) e os conecta ao pipeline de execução real (shadow_loop.py).

Função Principal: Para cada ativo, em cada ciclo, o Orquestrador:

    Detecta a sessão atual

    Seleciona os ativos prioritários

    Obtém o melhor agente do ecossistema competitivo

    Gera o sinal usando a estratégia vencedora

    Ajusta a confiança com o Q-value do agente

    Aplica filtros (assinaturas, correlação, risco)

    Calcula lote, SL e TP calibrados por sessão

    Retorna o sinal final para execução

2. ARQUITETURA DE DECISÃO
text

OmegaGlobalOrchestrator
│
├── M3: SessionCalibrator
│   ├── get_current_session() → MarketSession
│   ├── get_config() → SessionConfig
│   │   ├── priority_assets
│   │   ├── active_strategies
│   │   ├── max_lot, min_confidence
│   │   └── detection_thresholds
│   └── get_execution_limits()
│
├── M2: EcosystemOrchestrator
│   └── Para cada ativo:
│       └── get_best_agent_for_asset(asset)
│           └── CompetitiveAgent
│               ├── confidence (Q-value)
│               ├── sharpe_ratio
│               ├── kelly_fraction
│               └── performance_score
│
├── M1: StrategyCatalog
│   └── get_strategy(agent.strategy_name)
│       └── BaseStrategy
│           ├── should_enter(market_data)
│           ├── get_signal(market_data)
│           └── calculate_stop_loss() / take_profit()
│
├── FILTROS:
│   ├── SpoofDetector → ajusta confiança
│   ├── CorrelationFilter → evita exposição duplicada
│   ├── Spread check → rejeita se spread > máximo
│   └── Position limit → rejeita se max_positions atingido
│
└── SAÍDA:
    └── Dict {
        action, direction, confidence,
        lot, stop_loss_pips, take_profit_pips,
        strategy, agent_id, reason, session
    }

3. INTEGRAÇÃO COM SHADOW_LOOP.PY
python

# No shadow_loop.py:

from core.omega_global_orchestrator import (
    create_orchestrator, get_trading_signal, record_trade, close_trade
)

# Inicialização (uma vez)
orchestrator = create_orchestrator(
    assets=["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"],
    total_capital=DEMO_EQUITY_USD
)

# No loop principal:
for asset in ativos:
    # Obter assinaturas detectadas
    signature_scores = spoof_detector.get_signature_scores()
    
    # Obter sinal do Orquestrador Global
    signal = get_trading_signal(
        orchestrator=orchestrator,
        asset=asset,
        signature_scores=signature_scores,
        current_positions=list(orchestrator.get_open_positions().keys())
    )
    
    if signal['action'] != 'HOLD':
        # Executar ordem
        exec_result = mt5_send_order(
            asset=asset,
            tf=tf,
            lot=signal['lot'],
            sl_pts=signal['stop_loss_pips'],
            tp_pts=signal['take_profit_pips'],
            direction=signal['direction']
        )
        
        if exec_result.get('success'):
            record_trade(
                orchestrator, asset, signal['agent_id'],
                exec_result['deal'], exec_result['fill_price'], signal['lot']
            )

4. HASH E ASSINATURA
Atributo	Valor
Nome do Módulo	M4 — Orquestrador Global
Arquivo	core/omega_global_orchestrator.py
Versão	1.0.0
Hash SHA-256	sha256:m4-global-orchestrator-v1-0-0-20260426
Data de Criação	2026-04-26
Dependências	M1, M2, M3

CEO, o M4 está completo. O Orquestrador Global integra todos os módulos anteriores e está pronto para conectar ao shadow_loop.py (M5).