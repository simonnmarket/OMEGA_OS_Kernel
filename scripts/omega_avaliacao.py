"""
OMEGA QUANTUM LAB — Avaliação Institucional do Sistema
Preenche o template de avaliação com os valores reais do sistema.
Execução: python scripts/omega_avaliacao.py
"""
import json
from datetime import datetime

# =============================================
# TEMPLATE PARA AVALIAÇÃO DE SISTEMA DE TRADING
# =============================================

def gerar_template_avaliacao():
    template = {
        "metadados": {
            "nome_sistema": "NOME_DO_SEU_SISTEMA",
            "data_avaliacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "versao_agent_ia": "VERSÃO_DO_AGENT_IA",
            "tipo_sistema": "AUTOMATIZADO/SEMI_AUTOMATIZADO/MANUAL"
        },
        "dados_infra": {
            "fonte_dados_historicos": {
                "tipo": "TICK_DATA/OHLC/OUTRO",
                "fonte": "TickData/CME/Bloomberg/Reuters/Outra",
                "resolucao_temporal": "MILISSEGUNDOS/SEGUNDOS/MINUTOS",
                "anos_cobertos": 5
            },
            "order_flow": {
                "usa_order_flow": True,
                "ferramenta": "Bookmap/SierraChart/Jigsaw/Nenhuma"
            },
            "latencia_execucao": {
                "valor_ms": 10,
                "ambiente": "COLOCATION/Cloud/Local"
            },
            "dados_alternativos": {
                "usa_dados_alternativos": False,
                "tipos": ["SATELITE", "FLUXO_NAVIOS", "SENTIMENTO_REDES_SOCIAIS"]
            },
            "armazenamento_dados": {
                "tipo": "BANCO_DADOS/CSV/EXCEL/OUTRO",
                "ferramenta": "TimescaleDB/Kafka/PostgreSQL"
            }
        },
        "estrategia": {
            "tipo_estrategia": "TREND_FOLLOWING/MEAN_REVERSION/ARBITRAGE/HFT/OUTRO",
            "backtest": {
                "usa_tick_data": True,
                "periodo_backtest_anos": 5,
                "out_of_sample_test": True,
                "sharpe_ratio": 2.5,
                "max_drawdown": 15.0,
                "win_rate": 0.60,
                "risk_reward_ratio": 2.0,
                "correlacao_mercado": "BAIXA/ALTA/NEUTRA"
            },
            "machine_learning": {
                "usa_ml": False,
                "bibliotecas": ["TensorFlow", "PyTorch", "Scikit-learn"],
                "validacao_cruzada": True
            }
        },
        "execucao_risco": {
            "position_sizing": {
                "metodo": "KELLY_CRITERION/VOLATILITY_TARGETING/FIXO",
                "max_risco_por_operacao": 0.02
            },
            "stop_loss": {
                "usa_stop_loss": True,
                "tipo": "FIXO/DINAMICO/ATR",
                "valor_atr": 1.5
            },
            "slippage": {
                "media_por_operacao": 0.005,
                "contabiliza_no_backtest": True
            },
            "news_events": {
                "pausa_operacoes": True,
                "ferramenta_monitoramento": "Bloomberg/Reuters/TradingView"
            },
            "kill_switch": {
                "ativo": True,
                "limite_drawdown": 20.0
            }
        },
        "tecnologia": {
            "linguagem_principal": "Python/C++/MQL4/Outra",
            "ambiente_execucao": "CLOUD/LOCAL/HIBRIDO",
            "corretora_api": {
                "nome": "InteractiveBrokers/MetaTrader/Outra",
                "latencia_api_ms": 5
            },
            "monitoramento": {
                "ferramenta": "Grafana/Kibana/Outra",
                "alertas_automaticos": True
            },
            "fail_safes": {
                "reconexao_automatica": True,
                "backup_dados": True
            }
        },
        "psicologia": {
            "trading_journal": {
                "ativo": True,
                "metricas_registradas": ["P&L", "SLIPPAGE", "EMOCOES"]
            },
            "revisao_sistema": {
                "frequencia": "DIARIO/SEMANAL/MENSAL",
                "ajustes_automaticos": True
            },
            "black_swan_plan": {
                "ativo": True,
                "estrategia_hedge": "OPCOES/FUTUROS/OUTRO"
            }
        }
    }
    return template


def avaliar_sistema(respostas):
    pontuacao = {
        "dados_infra": 0, "estrategia": 0,
        "execucao_risco": 0, "tecnologia": 0, "psicologia": 0, "total": 0
    }
    diagnostico = {"gaps_criticos": [], "sugestoes": []}

    if respostas["dados_infra"]["fonte_dados_historicos"]["tipo"] != "TICK_DATA":
        pontuacao["dados_infra"] += 1
        diagnostico["gaps_criticos"].append("Dados históricos não são tick data (precisão insuficiente).")
        diagnostico["sugestoes"].append("Usar TickData ou CME para dados de alta frequência.")

    if not respostas["dados_infra"]["order_flow"]["usa_order_flow"]:
        pontuacao["dados_infra"] += 1
        diagnostico["gaps_criticos"].append("Não usa order flow (fluxo de ordens).")
        diagnostico["sugestoes"].append("Integrar Bookmap ou Sierra Chart para visualizar fluxo de ordens.")

    if respostas["dados_infra"]["latencia_execucao"]["valor_ms"] > 10:
        pontuacao["dados_infra"] += 1
        diagnostico["gaps_criticos"].append(f"Latência de execução alta ({respostas['dados_infra']['latencia_execucao']['valor_ms']}ms).")
        diagnostico["sugestoes"].append("Usar colocation ou APIs de baixa latência.")

    if respostas["estrategia"]["backtest"]["sharpe_ratio"] < 2.0:
        pontuacao["estrategia"] += 1
        diagnostico["gaps_criticos"].append(f"Sharpe Ratio baixo ({respostas['estrategia']['backtest']['sharpe_ratio']}) — insuficiente para validação.")
        diagnostico["sugestoes"].append("Acumular 50+ trades para calcular Sharpe real. Alvo: > 1.0 fase inicial, > 2.0 institucional.")

    if respostas["estrategia"]["backtest"]["max_drawdown"] > 20:
        pontuacao["estrategia"] += 1
        diagnostico["gaps_criticos"].append(f"Max Drawdown alto ({respostas['estrategia']['backtest']['max_drawdown']}%).")
        diagnostico["sugestoes"].append("Manter DD diário < 1%, total < 5% em paper. Escalar só após validação.")

    if not respostas["estrategia"]["backtest"]["out_of_sample_test"]:
        pontuacao["estrategia"] += 1
        diagnostico["gaps_criticos"].append("Sem out-of-sample test (risco de overfitting).")
        diagnostico["sugestoes"].append("Separar 30% dos dados históricos para validação fora da amostra.")

    if respostas["execucao_risco"]["position_sizing"]["metodo"] == "FIXO":
        pontuacao["execucao_risco"] += 1
        diagnostico["gaps_criticos"].append("Position sizing fixo (não adaptativo ao risco).")
        diagnostico["sugestoes"].append("Usar Kelly Criterion ou Volatility Targeting.")

    if not respostas["execucao_risco"]["stop_loss"]["usa_stop_loss"]:
        pontuacao["execucao_risco"] += 1
        diagnostico["gaps_criticos"].append("Não usa stop-loss.")
        diagnostico["sugestoes"].append("Implementar stop-loss dinâmico (1.2-1.5× ATR por regime).")

    if respostas["execucao_risco"]["slippage"]["media_por_operacao"] > 0.01:
        pontuacao["execucao_risco"] += 1
        diagnostico["gaps_criticos"].append(f"Slippage médio alto ({respostas['execucao_risco']['slippage']['media_por_operacao']*100:.1f}%).")
        diagnostico["sugestoes"].append("Usar limit orders e corretoras com execução rápida.")

    if respostas["tecnologia"]["linguagem_principal"] in ["MQL4", "MQL5", "Excel VBA"]:
        pontuacao["tecnologia"] += 1
        diagnostico["gaps_criticos"].append(f"Linguagem limitada ({respostas['tecnologia']['linguagem_principal']}).")
        diagnostico["sugestoes"].append("Migrar para Python ou C++ para maior flexibilidade.")

    if respostas["tecnologia"]["ambiente_execucao"] == "LOCAL":
        pontuacao["tecnologia"] += 1
        diagnostico["gaps_criticos"].append("Execução local (risco de falhas de hardware/energia).")
        diagnostico["sugestoes"].append("Migrar para VPS ou cloud com redundância e UPS.")

    if not respostas["psicologia"]["trading_journal"]["ativo"]:
        pontuacao["psicologia"] += 1
        diagnostico["gaps_criticos"].append("Não mantém trading journal.")
        diagnostico["sugestoes"].append("Implementar registro automático de operações (P&L, slippage).")

    if not respostas["psicologia"]["black_swan_plan"]["ativo"]:
        pontuacao["psicologia"] += 1
        diagnostico["gaps_criticos"].append("Não tem plano para black swan events.")
        diagnostico["sugestoes"].append("Adicionar hedge ou redução automática de alavancagem em eventos extremos.")

    pontuacao["total"] = sum(pontuacao[k] for k in pontuacao if k != "total")

    if pontuacao["total"] <= 5:
        diagnostico["classificacao"] = "INSTITUCIONAL"
    elif pontuacao["total"] <= 12:
        diagnostico["classificacao"] = "SEMI-PROFISSIONAL"
    else:
        diagnostico["classificacao"] = "AMADOR"

    return {"pontuacao": pontuacao, "diagnostico": diagnostico}


# =============================================
# RESPOSTAS REAIS DO SISTEMA OMEGA
# =============================================

respostas_omega = {
    "metadados": {
        "nome_sistema": "OMEGA OS Kernel v4.0 — FASE 4",
        "data_avaliacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "versao_agent_ia": "Cascade + HarmonicEngine v3 + LotCalcV2",
        "tipo_sistema": "AUTOMATIZADO"
    },

    "dados_infra": {
        "fonte_dados_historicos": {
            # MT5 fornece OHLCV por candle — não tick raw. Harmonic engine usa CSV exportados por export_ohlcv_mt5.py.
            "tipo": "OHLC",
            "fonte": "MetaTrader5 (Demo — MetaQuotes build 5833)",
            "resolucao_temporal": "MINUTOS",  # M1/M3/M5/M15/H1/H4
            "anos_cobertos": 1  # MT5 demo: ~1 ano de histórico disponível
        },
        "order_flow": {
            # SpoofIcebergDetector analisa volume tick a tick, mas sem book de profundidade real
            "usa_order_flow": False,
            "ferramenta": "SpoofIcebergDetector (volume superficial — sem L2 book)"
        },
        "latencia_execucao": {
            # lat_max observado nos logs: 46ms (ciclo completo Python→MT5→fill)
            "valor_ms": 46,
            "ambiente": "LOCAL"
        },
        "dados_alternativos": {
            "usa_dados_alternativos": False,
            "tipos": []
        },
        "armazenamento_dados": {
            # audit/paper/*.log + logs/agent_ia_phase3/*/paper_summary_*.json + data/ohlcv/*.csv
            "tipo": "CSV",
            "ferramenta": "CSV + JSON (sem banco relacional ou time-series DB)"
        }
    },

    "estrategia": {
        # Estratégia primária: Harmonic Pattern Engine (ABCD/Gartley/Bat/Cypher) + JPY Cluster momentum
        "tipo_estrategia": "OUTRO",  # Harmonic patterns + cluster momentum + MTF alignment
        "backtest": {
            # Apenas paper trading ao vivo (demo MT5). Sem backtest histórico formal.
            "usa_tick_data": False,
            "periodo_backtest_anos": 0,   # Sem backtest — apenas forward paper
            "out_of_sample_test": False,  # Paper ao vivo = OOS de facto, mas sem separação formal
            "sharpe_ratio": 0.0,          # Ainda calculando — apenas 2 trades (ciclo 1)
            "max_drawdown": 0.0,          # Ainda calculando — DD diário máx configurado: 2%
            "win_rate": 1.0,              # 2/2 = 100% — amostra insuficiente (N=2)
            "risk_reward_ratio": 3.0,     # R:R mínimo enforçado: 1:3.0 (mt5_send_order floor)
            "correlacao_mercado": "ALTA"  # JPY cluster = alta correlação entre USDJPY/EURJPY/GBPJPY
        },
        "machine_learning": {
            # HarmonicEngine v3 usa reconhecimento de padrões geométricos (não ML clássico)
            # MFAEngine e OmegaIntegrationGate usam scoring baseado em regras + estatísticas
            "usa_ml": False,
            "bibliotecas": ["numpy", "scipy"],  # Sem deep learning
            "validacao_cruzada": False
        }
    },

    "execucao_risco": {
        "position_sizing": {
            # LotCalcV2: volatility targeting por ATR% + confidence score + performance feedback
            "metodo": "VOLATILITY_TARGETING",
            "max_risco_por_operacao": 0.001  # 0.1% do equity por trade
        },
        "stop_loss": {
            # SL = ATR(M1/M3) × sl_atr_mult por regime. Hard cap _MAX_SL_PTS por classe.
            "usa_stop_loss": True,
            "tipo": "ATR",
            "valor_atr": 1.2  # jpy_major=1.2, jpy_cross=1.3-1.5, commodity=1.5, crypto=2.0
        },
        "slippage": {
            # RETCODE_WARN = requote monitorado. Slippage não contabilizado em backtest (não há backtest).
            "media_por_operacao": 0.002,  # ~0.2% estimado em demo MT5
            "contabiliza_no_backtest": False  # N/A — sem backtest formal
        },
        "news_events": {
            # Sem integração de calendário econômico. Opera 24/5 incluindo NFP/FOMC.
            "pausa_operacoes": False,
            "ferramenta_monitoramento": "Nenhuma"
        },
        "kill_switch": {
            # DD_DAILY_MAX=2%, MAX_CONSEC_FAIL=3, LatencyCircuitBreaker ativo
            "ativo": True,
            "limite_drawdown": 2.0
        }
    },

    "tecnologia": {
        "linguagem_principal": "Python",
        "ambiente_execucao": "LOCAL",  # Máquina local + MT5 demo
        "corretora_api": {
            "nome": "MetaTrader5 Python API",
            "latencia_api_ms": 46  # Medido: lat_max ciclo completo
        },
        "monitoramento": {
            # audit/paper logs + paper_summary JSON + check_positions.py manual
            "ferramenta": "Logs JSON customizados (sem Grafana/Kibana)",
            "alertas_automaticos": False  # Sem alertas push/email/SMS
        },
        "fail_safes": {
            # PID lockfile OMEGA_FASE4.lock previne instâncias múltiplas
            # MT5 reconecta automaticamente na inicialização de cada ciclo
            "reconexao_automatica": True,
            "backup_dados": False  # Sem backup automático dos logs
        }
    },

    "psicologia": {
        "trading_journal": {
            # audit/paper/paper_loop_*.log + logs/*/paper_summary_*.json (automático, cada ciclo)
            "ativo": True,
            "metricas_registradas": ["P&L", "SLIPPAGE", "R:R", "SL_CUSTO_USD", "LATENCIA", "CONFIANCA"]
        },
        "revisao_sistema": {
            # Ciclos automáticos a cada 60s. Parâmetros ajustados manualmente entre sessões.
            "frequencia": "CONTINUA",
            "ajustes_automaticos": False  # Parâmetros ajustados manualmente (não auto-tuning)
        },
        "black_swan_plan": {
            # Kill switch por DD% + MAX_CONSEC_FAIL. Sem hedge com opções.
            "ativo": True,
            "estrategia_hedge": "KILL_SWITCH_DD"
        }
    }
}


if __name__ == "__main__":
    print("=" * 65)
    print("  OMEGA OS KERNEL v4.0 — AVALIAÇÃO INSTITUCIONAL")
    print("=" * 65)

    resultado = avaliar_sistema(respostas_omega)
    p = resultado["pontuacao"]
    d = resultado["diagnostico"]

    print(f"\n{'CATEGORIA':<22} {'GAPS':>5}")
    print("-" * 30)
    cats = ["dados_infra", "estrategia", "execucao_risco", "tecnologia", "psicologia"]
    labels = ["Dados & Infra", "Estratégia", "Execução/Risco", "Tecnologia", "Psicologia"]
    for cat, lbl in zip(cats, labels):
        bar = "■" * p[cat] + "□" * (3 - p[cat])
        print(f"  {lbl:<20} {bar}  ({p[cat]} gap(s))")

    print(f"\n  TOTAL DE GAPS: {p['total']}/13")
    print(f"  CLASSIFICAÇÃO: {d['classificacao']}")

    print(f"\n{'─'*65}")
    print("  GAPS CRÍTICOS:")
    for i, g in enumerate(d["gaps_criticos"], 1):
        print(f"  {i:>2}. {g}")

    print(f"\n{'─'*65}")
    print("  PLANO DE AÇÃO (PRIORIDADE):")
    priority = [
        ("CRÍTICO",  "Backtest formal com walk-forward (2+ anos OOS). PENDENTE pós-20 trades."),
        ("CRÍTICO",  "Calendário econômico: pausar operações em NFP/FOMC/BOJ. Risco de gap extremo."),
        ("ALTO",     "Migrar para VPS/cloud com UPS. Risco de queda de energia/internet."),
        ("ALTO",     "Order flow L2 real (SpoofIcebergDetector atual é superficial sem book)."),
        ("MÉDIO",    "Backup automático de logs e audit para storage remoto."),
        ("MÉDIO",    "Grafana/Kibana para monitoramento em tempo real + alertas Telegram/email."),
        ("BAIXO",    "Auto-tuning de parâmetros (walk-forward automático após 50+ trades)."),
    ]
    for nivel, acao in priority:
        print(f"  [{nivel:<8}] {acao}")

    print(f"\n{'─'*65}")
    print("  PONTOS FORTES DO SISTEMA:")
    strengths = [
        "Kill switch ativo: DD_DAILY_MAX=2% + MAX_CONSEC_FAIL=3 + LatencyCircuitBreaker",
        "Position sizing dinâmico: LotCalcV2 com ATR% + confidence + pip_value USD correto",
        "R:R mínimo 1:3.0 enforçado (recompensa cobre fee + risco com margem)",
        "SL por ATR real com hard cap por classe de ativo (_MAX_SL_PTS)",
        "JPY Cluster Engine: USDJPY lidera, 5 crosses seguem com CorrelationFilter",
        "PID lockfile: previne instâncias duplicadas",
        "Audit log completo por ciclo (JSON + log texto com SHA3-256)",
    ]
    for s in strengths:
        print(f"  ✓ {s}")

    print(f"\n{'=' * 65}")
    print(f"  STATUS: Paper trading ativo | Trades: 2 | Alvo GO/NO-GO: 20 trades")
    print(f"  Classificação: {d['classificacao']} — Meta: INSTITUCIONAL após backtest formal")
    print("=" * 65)
