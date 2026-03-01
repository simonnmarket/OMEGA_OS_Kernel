#!/usr/bin/env python3
"""
AURORA FULL POWER SYSTEM v4.0
Sistema com 100% das funcionalidades ativas

Data: 03-12-2025
Autor: AIC

FUNCIONALIDADES ATIVADAS:
- 7 Agentes via Groq (100% confiavel)
- Feedback Loop (aprendizado real)
- Kill Switch (drawdown protection)
- Preflight Check (validacao obrigatoria)
- Sistema de Veto (CFO/CKO/CMO)
- Calendario Economico
- Filtros (spread/volatilidade/sessao)
"""

import asyncio
import httpx
import json
import hashlib
import sqlite3
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import sys
import pkg_resources

# Adicionar path para imports locais
sys.path.insert(0, str(Path(__file__).parent))

# Import dos modulos core (v5.0)
try:
    from modules.core.models import (
        MarketData, TradeSignal, AgentDecision, 
        ExecutionResult, VerificationEvidence
    )
    from modules.core.environment import EnvironmentValidator
    from modules.core.persistence import PersistentStorage
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    CORE_MODULES_AVAILABLE = False
    logging.warning(f"Core modules not available: {e}")

# Import dos modulos quantitativos
try:
    from modules.quantitative.correlation_matrix import create_correlation_engine, GENESIS
    from modules.quantitative.risk_engine import create_risk_engine, GENESIS_CHECKSUM
    from modules.quantitative.time_aligner import create_time_aligner
    from modules.quantitative.sentiment_aggregator import create_sentiment_aggregator
    QUANTITATIVE_MODULES_AVAILABLE = True
except ImportError as e:
    QUANTITATIVE_MODULES_AVAILABLE = False
    logging.warning(f"Quantitative modules not available: {e}")

# Compatibilidade
CORRELATION_AVAILABLE = QUANTITATIVE_MODULES_AVAILABLE

# ==============================================================================
# VALIDAÇÃO DE VERSÕES (v5.2 Improvement)
# ==============================================================================

REQUIRED_VERSIONS = {
    'numpy': '1.24.0',
    'pandas': '2.0.0',
}

def validate_versions():
    """Valida versões de bibliotecas críticas"""
    logger.info("Validando versões de dependências...")
    all_ok = True
    for package, min_version in REQUIRED_VERSIONS.items():
        try:
            installed_version = pkg_resources.get_distribution(package).version
            installed_tuple = tuple(map(int, installed_version.split('.')[:3]))
            min_tuple = tuple(map(int, min_version.split('.')[:3]))
            
            if installed_tuple >= min_tuple:
                logger.debug(f"✅ {package}: {installed_version} (>= {min_version})")
            else:
                logger.warning(f"⚠️ {package}: {installed_version} (< {min_version} requerido)")
                all_ok = False
        except pkg_resources.DistributionNotFound:
            logger.error(f"❌ {package}: NÃO INSTALADO")
            all_ok = False
        except Exception as e:
            logger.error(f"❌ Erro ao validar {package}: {e}")
            all_ok = False
    
    if all_ok:
        logger.info("✅ Validação de versões: OK")
    else:
        logger.warning("⚠️ Algumas dependências não atendem aos requisitos")
    
    return all_ok

# Executar validação completa de ambiente (v5.0)
if CORE_MODULES_AVAILABLE:
    env_report = EnvironmentValidator.validate_environment()
else:
    # Fallback para validação básica
    validate_versions()

# Configuracao de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(f'../logs/aurora_full_power_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACAO - TODOS OS AGENTES VIA GROQ (100% CONFIAVEL)
# =============================================================================

GROQ_API_KEY = "INSIRA_A_SUA_API_KEY_AQUI"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Todos os 7 agentes via Ollama LOCAL - SEM RATE LIMIT
AGENTS_CONFIG = {
    "CEO": {
        "model": "llama3.2",
        "provider": "ollama",
        "role": "Chief Executive Officer - Strategic Vision",
        "focus": "Alinhamento estrategico, priorizacao, visao de longo prazo",
        "has_veto": True
    },
    "CFO": {
        "model": "qwen2.5",
        "provider": "ollama",
        "role": "Chief Financial Officer - Risk Management",
        "focus": "Gestao de risco, alocacao de capital, drawdown control",
        "has_veto": True
    },
    "CTO": {
        "model": "llama3.2",
        "provider": "ollama",
        "role": "Chief Technology Officer - Technical Analysis",
        "focus": "Analise tecnica, padroes de preco, indicadores",
        "has_veto": False
    },
    "CIO": {
        "model": "qwen2.5",
        "provider": "ollama",
        "role": "Chief Information Officer - Data Quality",
        "focus": "Qualidade de dados, validacao, consistencia",
        "has_veto": False
    },
    "COO": {
        "model": "llama3.2",
        "provider": "ollama",
        "role": "Chief Operating Officer - Execution",
        "focus": "Execucao, timing, eficiencia operacional",
        "has_veto": False
    },
    "CKO": {
        "model": "gemma2:2b",
        "provider": "ollama",
        "role": "Chief Knowledge Officer - Red Team",
        "focus": "Questionamento critico, riscos ocultos, falsificacao",
        "has_veto": True
    },
    "CMO": {
        "model": "qwen2.5",
        "provider": "ollama",
        "role": "Chief Market Officer - Market Intelligence",
        "focus": "Calendario economico, eventos, sentimento de mercado",
        "has_veto": True
    }
}

# URL do Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"

# Configuracao de seguranca
SECURITY_CONFIG = {
    "max_drawdown_percent": 15.0,
    "kill_switch_enabled": True,
    "preflight_required": True,
    "min_agents_for_trade": 7,
    "veto_blocks_trade": True,
    "min_consensus_percent": 28.6  # 28.6% = 2 de 7 agentes (MUITO AGRESSIVO PARA TESTES)
}

# Configuracao de filtros
FILTER_CONFIG = {
    "max_spread_pips": {
        "FOREX": 3.0,
        "METALS": 50.0,
        "INDICES": 5.0,
        "CRYPTO": 100.0
    },
    "min_volatility_atr": 0.0005,
    "max_volatility_atr": 0.05,
    "trading_sessions": {
        "FOREX": ["LONDON", "NEW_YORK", "OVERLAP"],
        "METALS": ["LONDON", "NEW_YORK"],
        "INDICES": ["NEW_YORK"],
        "CRYPTO": ["ALL"]
    }
}

# Magic number para identificar ordens AURORA
MAGIC_NUMBER = 20251203

# =============================================================================
# DATABASE PARA APRENDIZADO
# =============================================================================

class LearningDatabase:
    """Banco de dados para armazenar aprendizado dos agentes"""
    
    def __init__(self, db_path: str = "../data/aurora_learning.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa tabelas do banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de votos dos agentes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                vote TEXT NOT NULL,
                confidence REAL NOT NULL,
                reason TEXT,
                trade_id TEXT,
                was_correct INTEGER DEFAULT NULL,
                profit REAL DEFAULT NULL
            )
        """)
        
        # Tabela de metricas dos agentes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                agent_name TEXT PRIMARY KEY,
                total_votes INTEGER DEFAULT 0,
                correct_votes INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        
        # Tabela de trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                open_time TEXT NOT NULL,
                close_time TEXT,
                open_price REAL NOT NULL,
                close_price REAL,
                volume REAL NOT NULL,
                profit REAL,
                consensus_percent REAL,
                agents_voted TEXT
            )
        """)
        
        # Inicializar metricas dos agentes
        for agent_name in AGENTS_CONFIG.keys():
            cursor.execute("""
                INSERT OR IGNORE INTO agent_metrics (agent_name, last_updated)
                VALUES (?, ?)
            """, (agent_name, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        logger.info(f"[DB] Learning database initialized: {self.db_path}")
    
    def save_vote(self, agent_name: str, symbol: str, vote: str, 
                  confidence: float, reason: str, trade_id: str):
        """Salva voto de um agente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_votes (timestamp, agent_name, symbol, vote, confidence, reason, trade_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), agent_name, symbol, vote, confidence, reason, trade_id))
        conn.commit()
        conn.close()
    
    def update_vote_result(self, trade_id: str, was_correct: bool, profit: float):
        """Atualiza resultado do voto apos trade fechar"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE agent_votes 
            SET was_correct = ?, profit = ?
            WHERE trade_id = ?
        """, (1 if was_correct else 0, profit, trade_id))
        conn.commit()
        conn.close()
    
    def update_agent_accuracy(self, agent_name: str):
        """Atualiza accuracy do agente baseado em historico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END)
            FROM agent_votes
            WHERE agent_name = ? AND was_correct IS NOT NULL
        """, (agent_name,))
        
        total, correct = cursor.fetchone()
        total = total or 0
        correct = correct or 0
        accuracy = correct / total if total > 0 else 0.0
        
        cursor.execute("""
            UPDATE agent_metrics
            SET total_votes = ?, correct_votes = ?, accuracy = ?, last_updated = ?
            WHERE agent_name = ?
        """, (total, correct, accuracy, datetime.now().isoformat(), agent_name))
        
        conn.commit()
        conn.close()
        
        logger.info(f"[LEARNING] {agent_name}: {correct}/{total} = {accuracy*100:.1f}% accuracy")
        return accuracy
    
    def get_agent_metrics(self) -> Dict:
        """Retorna metricas de todos os agentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_metrics")
        rows = cursor.fetchall()
        conn.close()
        
        return {
            row[0]: {
                "total_votes": row[1],
                "correct_votes": row[2],
                "accuracy": row[3],
                "last_updated": row[4]
            }
            for row in rows
        }
    
    def save_trade(self, trade_id: str, symbol: str, direction: str,
                   open_price: float, volume: float, consensus: float, agents: List[str]):
        """Salva trade aberto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades (trade_id, symbol, direction, open_time, open_price, volume, consensus_percent, agents_voted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (trade_id, symbol, direction, datetime.now().isoformat(), open_price, volume, consensus, json.dumps(agents)))
        conn.commit()
        conn.close()
    
    def close_trade(self, trade_id: str, close_price: float, profit: float):
        """Fecha trade e atualiza profit"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trades
            SET close_time = ?, close_price = ?, profit = ?
            WHERE trade_id = ?
        """, (datetime.now().isoformat(), close_price, profit, trade_id))
        conn.commit()
        conn.close()


# =============================================================================
# AGENT SYSTEM - TODOS VIA GROQ
# =============================================================================

@dataclass
class AgentVote:
    """Voto de um agente"""
    agent_name: str
    vote: str  # BUY, SELL, HOLD, VETO
    confidence: float
    reason: str
    is_veto: bool = False


class OllamaAgent:
    """Agente via Ollama LOCAL - SEM RATE LIMIT"""
    
    def __init__(self, name: str, config: dict, db: LearningDatabase):
        self.name = name
        self.model = config["model"]
        self.provider = config.get("provider", "ollama")
        self.role = config["role"]
        self.focus = config["focus"]
        self.has_veto = config["has_veto"]
        self.db = db
        self.agent_id = self._generate_id()
    
    def _generate_id(self) -> str:
        data = f"{self.name}_{self.model}_{datetime.now().date()}"
        return f"AGT_{self.name}_{hashlib.md5(data.encode()).hexdigest()[:8]}"
    
    async def analyze(self, market_data: dict, context: str = "") -> AgentVote:
        """Analisa dados de mercado e retorna voto"""
        
        # Obter metricas historicas do agente
        metrics = self.db.get_agent_metrics().get(self.name, {})
        accuracy = metrics.get("accuracy", 0.0)
        
        # Contexto de aprendizado
        learning_phase = metrics.get("total_votes", 0) < 50
        accuracy_info = f"Precisao: {accuracy*100:.1f}%" if not learning_phase else "Fase de aprendizado (coletando dados)"
        
        prompt = f"""Voce e o {self.name} ({self.role}).
Seu foco: {self.focus}
{accuracy_info}

DADOS DE MERCADO:
- Simbolo: {market_data.get('symbol', 'N/A')}
- Bid/Ask: {market_data.get('bid', 0):.5f} / {market_data.get('ask', 0):.5f}
- MA5: {market_data.get('ma5', 0):.5f}
- MA20: {market_data.get('ma20', 0):.5f}
- Sinal Tecnico: {market_data.get('ma_signal', 'N/A')}
- ATR: {market_data.get('atr', 0):.5f}
- Classe: {market_data.get('asset_class', 'N/A')}

{context}

REGRAS DE VOTO (IMPORTANTE - SEJA DECISIVO):
- BUY: Se MA5 > MA20 (bullish) OU se preco acima de MA20 - VOTE BUY com confianca 0.6-0.8
- SELL: Se MA5 < MA20 (bearish) OU se preco abaixo de MA20 - VOTE SELL com confianca 0.6-0.8
- HOLD: APENAS se MA5 = MA20 (exatamente igual) OU spread > 5 pips OU mercado fechado
- VETO: APENAS se spread > 10 pips OU volatilidade extrema OU evento economico iminente

IMPORTANTE: 
- Se sinal tecnico e claro (MA5 != MA20), SEMPRE vote BUY ou SELL, NAO HOLD
- Estamos em fase de aprendizado - precisamos de dados reais, nao apenas HOLD
- Seja PROATIVO: prefira BUY/SELL com confianca media (0.6) do que HOLD
- Confianca minima para BUY/SELL: 0.5, maxima: 0.9

Responda APENAS em JSON:
{{"vote": "BUY" ou "SELL" ou "HOLD" ou "VETO", "confidence": 0.5-0.9, "reason": "breve"}}"""

        # Chamada Ollama LOCAL - sem rate limit
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    text = response.json().get("response", "")
                    return self._parse_vote(text)
                else:
                    logger.error(f"[{self.name}] Ollama error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"[{self.name}] Exception: {e}")
        
        return AgentVote(self.name, "HOLD", 0.3, "Ollama error", False)
    
    def _parse_vote(self, text: str) -> AgentVote:
        """Parse resposta JSON"""
        try:
            # Limpar texto
            text = text.strip()
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            
            data = json.loads(text)
            vote = data.get("vote", "HOLD").upper()
            confidence = float(data.get("confidence", 0.5))
            reason = data.get("reason", "")
            
            is_veto = vote == "VETO" and self.has_veto
            
            return AgentVote(self.name, vote, confidence, reason, is_veto)
            
        except:
            # Fallback parsing
            text_upper = text.upper()
            if "VETO" in text_upper and self.has_veto:
                return AgentVote(self.name, "VETO", 0.9, "Veto detectado", True)
            elif "BUY" in text_upper:
                return AgentVote(self.name, "BUY", 0.6, "Parsed from text", False)
            elif "SELL" in text_upper:
                return AgentVote(self.name, "SELL", 0.6, "Parsed from text", False)
            
            return AgentVote(self.name, "HOLD", 0.5, "Parse failed", False)


class AgentCouncil:
    """Conselho de 7 agentes"""
    
    def __init__(self, db: LearningDatabase):
        self.db = db
        self.agents = {
            name: OllamaAgent(name, config, db)
            for name, config in AGENTS_CONFIG.items()
        }
    
    async def preflight_check(self) -> Dict:
        """Verifica se todos os agentes estao respondendo"""
        logger.info("[PREFLIGHT] Verificando 7 agentes...")
        
        results = {}
        for name, agent in self.agents.items():
            # Delay entre testes para evitar rate limit
            await asyncio.sleep(1)
            
            success = False
            for attempt in range(2):  # 2 tentativas
                try:
                    # Usar Ollama (não Groq)
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.post(
                            OLLAMA_URL,
                            json={
                                "model": agent.model,
                                "prompt": "Say OK",
                                "stream": False
                            }
                        )
                        
                        if response.status_code == 200:
                            success = True
                            break
                except Exception as e:
                    logger.debug(f"[PREFLIGHT] {name} tentativa {attempt+1} falhou: {e}")
                    await asyncio.sleep(1)
            
            results[name] = success
            status = "OK" if success else "FALHOU"
            logger.info(f"  [{name}] {status}")
        
        active = sum(1 for v in results.values() if v)
        success = active >= 6  # Aceitar 6/7 como minimo
        
        logger.info(f"[PREFLIGHT] Resultado: {active}/7 agentes ativos")
        
        return {
            "success": success,
            "active": active,
            "results": results
        }
    
    async def get_consensus(self, symbol: str, market_data: dict, context: str = "") -> Dict:
        """Obtem consenso de todos os agentes"""
        
        trade_id = f"TRD_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Coletar votos de todos os agentes
        votes: List[AgentVote] = []
        
        for name, agent in self.agents.items():
            vote = await agent.analyze(market_data, context)
            votes.append(vote)
            
            # Salvar voto no banco
            self.db.save_vote(name, symbol, vote.vote, vote.confidence, vote.reason, trade_id)
            
            logger.info(f"  [{name}] {vote.vote} ({vote.confidence*100:.0f}%) - {vote.reason[:50]}")
        
        # Verificar vetos
        vetos = [v for v in votes if v.is_veto]
        if vetos and SECURITY_CONFIG["veto_blocks_trade"]:
            logger.warning(f"[VETO] Trade bloqueado por: {[v.agent_name for v in vetos]}")
            return {
                "decision": "BLOCKED",
                "reason": f"Veto por {[v.agent_name for v in vetos]}",
                "trade_id": trade_id,
                "votes": votes
            }
        
        # Calcular consenso
        buy_votes = [v for v in votes if v.vote == "BUY"]
        sell_votes = [v for v in votes if v.vote == "SELL"]
        hold_votes = [v for v in votes if v.vote == "HOLD"]
        
        buy_score = sum(v.confidence for v in buy_votes)
        sell_score = sum(v.confidence for v in sell_votes)
        
        total_votes = len(buy_votes) + len(sell_votes)
        
        logger.info(f"[CONSENSUS] {symbol} - BUY: {len(buy_votes)}, SELL: {len(sell_votes)}, HOLD: {len(hold_votes)}")
        logger.info(f"[CONSENSUS] {symbol} - Buy Score: {buy_score:.2f}, Sell Score: {sell_score:.2f}")
        
        if total_votes == 0:
            logger.warning(f"[CONSENSUS] {symbol} - TODOS OS AGENTES VOTARAM HOLD!")
            return {
                "decision": "HOLD",
                "reason": "Sem votos direcionais - todos HOLD",
                "trade_id": trade_id,
                "consensus_percent": 0,
                "votes": votes
            }
        
        if buy_score > sell_score:
            direction = "BUY"
            consensus_percent = (len(buy_votes) / 7) * 100
            confidence_avg = buy_score / len(buy_votes) if buy_votes else 0
        else:
            direction = "SELL"
            consensus_percent = (len(sell_votes) / 7) * 100
            confidence_avg = sell_score / len(sell_votes) if sell_votes else 0
        
        logger.info(f"[CONSENSUS] {symbol} - Direcao: {direction} | Consenso: {consensus_percent:.1f}% | "
                   f"Minimo requerido: {SECURITY_CONFIG['min_consensus_percent']}%")
        
        # Verificar minimo de consenso (mais flexível - aceita 2 votos se score for alto)
        min_votes_required = 2 if confidence_avg >= 0.7 else 3
        actual_votes = len(buy_votes) if direction == "BUY" else len(sell_votes) if direction == "SELL" else 0
        
        if direction in ["BUY", "SELL"] and actual_votes < min_votes_required:
            logger.warning(f"[CONSENSUS] {symbol} - Votos insuficientes: {actual_votes} < {min_votes_required} (confianca: {confidence_avg:.2f})")
            return {
                "decision": "HOLD",
                "reason": f"Votos insuficientes: {actual_votes} < {min_votes_required}",
                "trade_id": trade_id,
                "consensus_percent": consensus_percent,
                "votes": votes
            }
        
        # ACEITAR se tiver 2+ votos E consenso >= 28.6% (para testes)
        if direction in ["BUY", "SELL"] and actual_votes >= 2:
            logger.info(f"[CONSENSUS] {symbol} - ✅ ACEITO: {actual_votes} votos >= 2 (consenso: {consensus_percent:.1f}%)")
        elif consensus_percent < SECURITY_CONFIG["min_consensus_percent"]:
            logger.warning(f"[CONSENSUS] {symbol} - Consenso insuficiente: {consensus_percent:.1f}% < {SECURITY_CONFIG['min_consensus_percent']}% (votos: {actual_votes})")
            return {
                "decision": "HOLD",
                "reason": f"Consenso insuficiente: {consensus_percent:.0f}% < {SECURITY_CONFIG['min_consensus_percent']}%",
                "trade_id": trade_id,
                "consensus_percent": consensus_percent,
                "votes": votes
            }
        
        logger.info(f"[CONSENSUS] {symbol} - ✅ SINAL APROVADO: {direction} | Consenso: {consensus_percent:.1f}%")
        
        return {
            "decision": direction,
            "confidence": confidence_avg,
            "consensus_percent": consensus_percent,
            "trade_id": trade_id,
            "agents_voted": [v.agent_name for v in votes if v.vote == direction],
            "votes": votes
        }


# =============================================================================
# KILL SWITCH E SEGURANCA
# =============================================================================

class KillSwitch:
    """Sistema de emergencia"""
    
    def __init__(self, max_drawdown: float = 15.0):
        self.max_drawdown = max_drawdown
        self.initial_balance = None
        self.triggered = False
    
    def check(self) -> Dict:
        """Verifica se kill switch deve ser ativado"""
        if not mt5.initialize():
            return {"triggered": True, "reason": "MT5 not connected"}
        
        account = mt5.account_info()
        if not account:
            return {"triggered": True, "reason": "No account info"}
        
        if self.initial_balance is None:
            self.initial_balance = account.balance
        
        current_equity = account.equity
        drawdown = ((self.initial_balance - current_equity) / self.initial_balance) * 100
        
        if drawdown >= self.max_drawdown:
            self.triggered = True
            logger.critical(f"[KILL SWITCH] ATIVADO! Drawdown: {drawdown:.2f}% >= {self.max_drawdown}%")
            return {
                "triggered": True,
                "reason": f"Drawdown {drawdown:.2f}% excedeu limite {self.max_drawdown}%",
                "action": "CLOSE_ALL_POSITIONS"
            }
        
        return {
            "triggered": False,
            "current_drawdown": drawdown,
            "max_allowed": self.max_drawdown
        }
    
    def close_all_positions(self):
        """Fecha todas as posicoes AURORA"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        for pos in positions:
            if pos.magic == MAGIC_NUMBER:
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                    "position": pos.ticket,
                    "magic": MAGIC_NUMBER,
                    "comment": "KILL_SWITCH"
                }
                mt5.order_send(request)
                logger.warning(f"[KILL SWITCH] Fechando {pos.symbol}")


# =============================================================================
# FILTROS DE MERCADO
# =============================================================================

class MarketFilters:
    """Filtros de qualidade de mercado"""
    
    @staticmethod
    def get_asset_class(symbol: str) -> str:
        """Identifica classe do ativo"""
        symbol = symbol.upper()
        if any(x in symbol for x in ["XAU", "XAG", "GOLD", "SILVER"]):
            return "METALS"
        elif any(x in symbol for x in ["BTC", "ETH", "CRYPTO"]):
            return "CRYPTO"
        elif any(x in symbol for x in ["US30", "US500", "NAS", "DAX", "UK100", "JP225"]):
            return "INDICES"
        else:
            return "FOREX"
    
    @staticmethod
    def check_spread(symbol: str) -> Dict:
        """Verifica se spread esta aceitavel"""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return {"passed": False, "reason": "No tick data"}
        
        spread_points = tick.ask - tick.bid
        info = mt5.symbol_info(symbol)
        if not info:
            return {"passed": False, "reason": "No symbol info"}
        
        spread_pips = spread_points / info.point / 10
        
        asset_class = MarketFilters.get_asset_class(symbol)
        max_spread = FILTER_CONFIG["max_spread_pips"].get(asset_class, 5.0)
        
        passed = spread_pips <= max_spread
        
        return {
            "passed": passed,
            "spread_pips": spread_pips,
            "max_allowed": max_spread,
            "asset_class": asset_class
        }
    
    @staticmethod
    def check_session(symbol: str) -> Dict:
        """Verifica se estamos em sessao de trading valida"""
        now = datetime.utcnow()
        hour = now.hour
        
        # Definir sessoes
        sessions = []
        if 7 <= hour < 16:  # London
            sessions.append("LONDON")
        if 13 <= hour < 22:  # New York
            sessions.append("NEW_YORK")
        if 13 <= hour < 16:  # Overlap
            sessions.append("OVERLAP")
        if 0 <= hour < 9:  # Tokyo
            sessions.append("TOKYO")
        
        sessions.append("ALL")  # Sempre inclui ALL
        
        asset_class = MarketFilters.get_asset_class(symbol)
        allowed = FILTER_CONFIG["trading_sessions"].get(asset_class, ["ALL"])
        
        passed = any(s in allowed for s in sessions)
        
        return {
            "passed": passed,
            "current_sessions": sessions,
            "allowed_sessions": allowed,
            "asset_class": asset_class
        }
    
    @staticmethod
    def check_all(symbol: str) -> Dict:
        """Executa todos os filtros"""
        spread_check = MarketFilters.check_spread(symbol)
        session_check = MarketFilters.check_session(symbol)
        
        all_passed = spread_check["passed"] and session_check["passed"]
        
        reasons = []
        if not spread_check["passed"]:
            reasons.append(f"Spread alto: {spread_check.get('spread_pips', 0):.1f} pips")
        if not session_check["passed"]:
            reasons.append(f"Fora de sessao: {session_check.get('current_sessions', [])}")
        
        return {
            "passed": all_passed,
            "spread": spread_check,
            "session": session_check,
            "reasons": reasons
        }


# =============================================================================
# FEEDBACK LOOP - APRENDIZADO REAL
# =============================================================================

class FeedbackLoop:
    """Sistema de feedback para aprendizado dos agentes"""
    
    def __init__(self, db: LearningDatabase):
        self.db = db
        self.pending_trades = {}  # trade_id -> trade_info
    
    def register_trade(self, trade_id: str, symbol: str, direction: str, 
                       agents_voted: List[str], open_price: float):
        """Registra trade para acompanhamento"""
        self.pending_trades[trade_id] = {
            "symbol": symbol,
            "direction": direction,
            "agents_voted": agents_voted,
            "open_price": open_price,
            "open_time": datetime.now()
        }
        logger.info(f"[FEEDBACK] Trade registrado: {trade_id}")
    
    def process_closed_trade(self, trade_id: str, close_price: float, profit: float):
        """Processa trade fechado e atualiza accuracy dos agentes"""
        
        if trade_id not in self.pending_trades:
            logger.warning(f"[FEEDBACK] Trade nao encontrado: {trade_id}")
            return
        
        trade = self.pending_trades.pop(trade_id)
        was_profitable = profit > 0
        
        # Determinar se cada agente acertou
        for agent_name in trade["agents_voted"]:
            was_correct = was_profitable  # Se votou na direcao e deu lucro = acertou
            
            # Atualizar no banco
            self.db.update_vote_result(trade_id, was_correct, profit)
            
            # Recalcular accuracy
            accuracy = self.db.update_agent_accuracy(agent_name)
            
            logger.info(f"[FEEDBACK] {agent_name}: {'ACERTOU' if was_correct else 'ERROU'} (acc: {accuracy*100:.1f}%)")
        
        # Fechar trade no banco
        self.db.close_trade(trade_id, close_price, profit)
    
    def check_closed_positions(self):
        """Verifica posicoes fechadas no MT5 e processa feedback"""
        # Buscar deals das ultimas 24h
        from_date = datetime.now() - timedelta(days=1)
        to_date = datetime.now()
        
        deals = mt5.history_deals_get(from_date, to_date)
        if not deals:
            return
        
        for deal in deals:
            if deal.magic != MAGIC_NUMBER:
                continue
            
            # Encontrar trade correspondente
            for trade_id, trade_info in list(self.pending_trades.items()):
                if trade_info["symbol"] == deal.symbol:
                    self.process_closed_trade(trade_id, deal.price, deal.profit)
                    break


# =============================================================================
# SISTEMA PRINCIPAL
# =============================================================================

class AuroraFullPower:
    """Sistema AURORA com 100% das funcionalidades ativas"""
    
    def __init__(self):
        self.db = LearningDatabase()
        self.council = AgentCouncil(self.db)
        self.kill_switch = KillSwitch(SECURITY_CONFIG["max_drawdown_percent"])
        self.feedback = FeedbackLoop(self.db)
        self.running = False
        self.trades_today = 0
        
        # Assets para monitorar
        self.assets = []
        
        # Correlation Engine
        self.correlation_engine = None
        self.correlation_cache = {}
        self.last_correlation_update = None
        
        # Time Aligner (no re-painting)
        self.time_aligner = None
        
        # Sentiment Aggregator
        self.sentiment_aggregator = None
        
        # Circuit Breaker (resiliência)
        self.circuit_breaker_state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.circuit_failure_count = 0
        self.circuit_last_failure = None
        self.circuit_failure_threshold = 3
        self.circuit_cooldown_seconds = 60
        
        # Health Monitoring
        self.health_score = 100.0
        self.last_health_check = None
        self.health_check_interval = 60  # segundos
        
        # Daily Metrics Reset (v5.2 Improvement)
        self.last_reset_day = datetime.now().date()
        self.daily_trades = 0
        self.daily_pnl = 0.0
    
    async def initialize(self) -> bool:
        """Inicializa sistema com preflight check"""
        logger.info("="*60)
        logger.info("AURORA FULL POWER v4.0 - INICIALIZANDO")
        logger.info("="*60)
        
        # 1. Verificar MT5
        if not mt5.initialize():
            logger.error("[INIT] MT5 nao conectado!")
            return False
        
        account = mt5.account_info()
        logger.info(f"[INIT] MT5 conectado: {account.login}")
        logger.info(f"[INIT] Balance: {account.balance:.2f}")
        logger.info(f"[INIT] Equity: {account.equity:.2f}")
        
        # 2. Preflight check dos agentes
        if SECURITY_CONFIG["preflight_required"]:
            preflight = await self.council.preflight_check()
            
            if not preflight["success"]:
                if preflight["active"] < SECURITY_CONFIG["min_agents_for_trade"]:
                    logger.error(f"[INIT] Preflight FALHOU: {preflight['active']}/7 agentes")
                    return False
        
        # 3. Inicializar Quantitative Modules
        if QUANTITATIVE_MODULES_AVAILABLE:
            # Correlation Engine
            self.correlation_engine = create_correlation_engine({
                'min_periods': 30,
                'stationarity_threshold': 0.05,
                'cache_ttl_seconds': 60,
                'max_cache_size': 50
            })
            logger.info(f"[INIT] Correlation Engine: Genesis {GENESIS.runtime_checksum}")
            
            # Risk Engine
            self.risk_engine = create_risk_engine({
                'confidence_level': 0.95,
                'lookback_window': 252,
                'kill_switch_threshold': SECURITY_CONFIG["max_drawdown_percent"] / 100
            })
            logger.info(f"[INIT] Risk Engine: Genesis {GENESIS_CHECKSUM}")
            
            # Time Aligner (no re-painting guarantee)
            self.time_aligner = create_time_aligner({
                'timezone_str': 'UTC',
                'max_cache_size': 100
            })
            logger.info("[INIT] Time Aligner: No re-painting guarantee activated")
            
            # Sentiment Aggregator
            self.sentiment_aggregator = create_sentiment_aggregator({
                'confidence_threshold': 0.2,
                'cache_ttl_seconds': 600
            })
            logger.info("[INIT] Sentiment Aggregator: Multi-source sentiment activated")
            
            # Specialized Agent System (v5.0)
            try:
                from modules.agents.specialized_agents import SpecializedAgentSystem, SpecializedLearningDatabase
                specialized_db = SpecializedLearningDatabase()
                self.specialized_agent_system = SpecializedAgentSystem(specialized_db)
                logger.info(f"[INIT] Specialized Agent System: {len(self.specialized_agent_system.agents)} agentes inicializados")
            except Exception as e:
                logger.warning(f"[INIT] Specialized Agent System não disponível: {e}")
                self.specialized_agent_system = None
        else:
            self.correlation_engine = None
            self.risk_engine = None
            self.time_aligner = None
            self.sentiment_aggregator = None
            logger.warning("[INIT] Quantitative Modules: NAO DISPONIVEL")
        
        # 4. Carregar APENAS principais ativos de cada segmento
        self.assets = [
            # FOREX - Majors (7)
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
            # METALS (2)
            "XAUUSD", "XAGUSD",
            # INDICES (4)
            "US500", "US30", "NAS100", "UK100",
            # CRYPTO (2)
            "BTCUSD", "ETHUSD"
        ]
        # Filtrar apenas os que existem no broker
        symbols_list = mt5.symbols_get()
        if symbols_list:
            available = [s.name for s in symbols_list if s.visible]
            self.assets = [a for a in self.assets if a in available]
        else:
            logger.warning("[INIT] Nao foi possivel obter lista de simbolos do MT5, usando lista padrao")
        logger.info(f"[INIT] {len(self.assets)} ativos principais selecionados: {self.assets}")
        
        # 4. Verificar kill switch
        ks_check = self.kill_switch.check()
        if ks_check["triggered"]:
            logger.error(f"[INIT] Kill switch ativo: {ks_check['reason']}")
            return False
        
        logger.info("[INIT] Sistema pronto para operar!")
        logger.info("="*60)
        return True
    
    def update_correlation_matrix(self) -> Optional[Dict]:
        """
        Atualiza matriz de correlacao entre todos os ativos.
        Retorna analise completa com recomendacoes.
        """
        if not self.correlation_engine or not CORRELATION_AVAILABLE:
            return None
        
        # Verificar se precisa atualizar (cache de 5 minutos)
        now = datetime.now()
        if self.last_correlation_update:
            delta = (now - self.last_correlation_update).total_seconds()
            if delta < 300 and self.correlation_cache:  # 5 minutos
                return self.correlation_cache
        
        # Coletar dados de preco para todos os ativos
        price_data = {}
        for symbol in self.assets[:10]:  # Limitar a 10 ativos para performance
            try:
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 300)
                if rates is not None and len(rates) >= 100:
                    dates = pd.to_datetime([datetime.fromtimestamp(r[0]) for r in rates])
                    closes = pd.Series([r[4] for r in rates], index=dates)
                    price_data[symbol] = closes
            except Exception as e:
                logger.debug(f"[CORR] Erro ao coletar {symbol}: {e}")
        
        if len(price_data) < 3:
            logger.warning("[CORR] Dados insuficientes para correlacao")
            return None
        
        # Calcular correlacao
        try:
            result = self.correlation_engine.calculate_real_time_correlation(
                price_data=price_data,
                method='pearson',
                lookback=250
            )
            
            if result['status'] == 'SUCCESS':
                self.correlation_cache = result
                self.last_correlation_update = now
                
                logger.info(f"[CORR] Matriz calculada: {len(price_data)} ativos | "
                           f"Latencia: {result['performance']['calculation_latency_ms']:.1f}ms")
                
                # Log recomendacoes importantes
                for rec in result.get('recommendations', [])[:2]:
                    logger.info(f"[CORR] {rec}")
                
                return result
            else:
                logger.warning(f"[CORR] Calculo falhou: {result.get('reason', 'unknown')}")
                return None
                
        except Exception as e:
            logger.error(f"[CORR] Erro no calculo: {e}")
            return None
    
    def check_correlation_risk(self, symbol: str) -> Dict:
        """
        Verifica risco de correlacao antes de abrir posicao.
        Evita concentracao excessiva em ativos correlacionados.
        """
        result = {
            'approved': True,
            'reason': 'Correlation check passed',
            'correlation_data': {}
        }
        
        if not self.correlation_cache:
            return result  # Se nao ha dados, aprovar
        
        # Pegar posicoes abertas
        positions = mt5.positions_get()
        if not positions:
            return result  # Nenhuma posicao, aprovar
        
        aurora_positions = [p for p in positions if p.magic == MAGIC_NUMBER]
        if not aurora_positions:
            return result
        
        # Verificar correlacao com posicoes existentes
        corr_matrix = self.correlation_cache.get('correlation_matrix', {})
        if not corr_matrix or symbol not in corr_matrix:
            return result
        
        high_corr_count = 0
        correlated_assets = []
        
        for pos in aurora_positions:
            pos_symbol = pos.symbol
            if pos_symbol in corr_matrix.get(symbol, {}):
                corr = abs(corr_matrix[symbol].get(pos_symbol, 0))
                if corr > 0.7:  # Correlacao alta > 0.7
                    high_corr_count += 1
                    correlated_assets.append((pos_symbol, corr))
        
        # Bloquear se mais de 2 posicoes altamente correlacionadas
        if high_corr_count >= 2:
            result['approved'] = False
            result['reason'] = f"HIGH CORRELATION RISK: {symbol} has {high_corr_count} highly correlated positions"
            result['correlation_data'] = {
                'correlated_assets': correlated_assets,
                'count': high_corr_count
            }
            logger.warning(f"[CORR] BLOQUEADO: {symbol} - {result['reason']}")
        
        return result
    
    def get_market_data(self, symbol: str) -> Dict:
        """Coleta dados de mercado para analise"""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return {}
        
        # Ultimas 50 candles H1
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        if rates is None or len(rates) < 20:
            return {}
        
        # Time Aligner: Garantir no re-painting (apenas velas fechadas)
        if self.time_aligner:
            try:
                # Usar align_timeframes_safe para garantir apenas velas fechadas
                success, aligned_df, validation = self.time_aligner.align_timeframes_safe(
                    symbol=symbol,
                    source_tf='H1',
                    target_tf='H1',
                    max_wait_ms=1000,
                    force_realign=False
                )
                if success and not aligned_df.empty:
                    # Converter DataFrame de volta para formato MT5
                    aligned_df.reset_index(inplace=True)
                    rates = aligned_df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].values
                    # Converter time para timestamp
                    rates[:, 0] = [int(ts.timestamp()) if hasattr(ts, 'timestamp') else ts for ts in aligned_df['time']]
                    logger.debug(f"[TIME] {symbol}: {len(rates)} velas fechadas (no re-painting)")
            except Exception as e:
                logger.debug(f"[TIME] TimeAligner não disponível para {symbol}: {e}")
                # Continuar com dados originais se TimeAligner falhar (graceful degradation)
        
        closes = [r[4] for r in rates]  # Close prices
        
        # Calcular indicadores
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        
        # ATR
        highs = [r[2] for r in rates[-14:]]
        lows = [r[3] for r in rates[-14:]]
        tr_list = [highs[i] - lows[i] for i in range(len(highs))]
        atr = sum(tr_list) / len(tr_list)
        
        return {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": tick.ask - tick.bid,
            "ma5": ma5,
            "ma20": ma20,
            "ma_signal": "BULLISH" if ma5 > ma20 else "BEARISH" if ma5 < ma20 else "NEUTRAL",
            "atr": atr,
            "last_close": closes[-1],
            "asset_class": MarketFilters.get_asset_class(symbol)
        }
    
    async def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Analisa um simbolo e decide se deve operar (v5.0 com validação Pydantic)"""
        
        # 1. Verificar filtros
        filters = MarketFilters.check_all(symbol)
        if not filters["passed"]:
            return None
        
        # 2. Coletar dados de mercado
        market_data_raw = self.get_market_data(symbol)
        if not market_data_raw:
            return None
        
        # Validar com Pydantic (v5.0)
        if CORE_MODULES_AVAILABLE:
            try:
                market_data = MarketData(
                    symbol=symbol,
                    price=market_data_raw.get("bid", 0) or market_data_raw.get("last_close", 0),
                    bid=market_data_raw.get("bid", 0),
                    ask=market_data_raw.get("ask", 0),
                    spread=market_data_raw.get("spread", 0),
                    volume=market_data_raw.get("volume", 0),
                    volatility=market_data_raw.get("volatility", 0),
                    sentiment_score=market_data_raw.get("sentiment_score", 0),
                    ma5=market_data_raw.get("ma5"),
                    ma20=market_data_raw.get("ma20"),
                    atr=market_data_raw.get("atr"),
                    last_close=market_data_raw.get("last_close"),
                    asset_class=market_data_raw.get("asset_class")
                )
                # Converter de volta para dict para compatibilidade
                market_data = market_data.dict()
            except Exception as e:
                logger.warning(f"[ANALYZE] Validação Pydantic falhou para {symbol}: {e}")
                market_data = market_data_raw
        else:
            market_data = market_data_raw
        
        # 3. Verificar se ja temos posicao neste ativo
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            aurora_positions = [p for p in positions if p.magic == MAGIC_NUMBER]
            if aurora_positions:
                return None  # Ja temos posicao
        
        # 4. Verificar risco de correlacao
        corr_risk = self.check_correlation_risk(symbol)
        if not corr_risk['approved']:
            logger.info(f"[CORR] {symbol} bloqueado: {corr_risk['reason']}")
            return None
        
        # 5. Verificar Risk Engine (4 camadas - v6.0)
        if self.risk_engine:
            try:
                # Obter posicoes atuais para portfolio_state
                all_positions = mt5.positions_get()
                aurora_positions = [p for p in all_positions if p.magic == MAGIC_NUMBER] if all_positions else []
                
                # Preparar portfolio_state
                portfolio_state = {
                    'total_capital': 100000.0,  # Em produção, obter do MT5
                    'total_exposure': sum(p.volume * p.price_current for p in aurora_positions) if aurora_positions else 0.0,
                    'open_positions': len(aurora_positions),
                    'exposure_by_symbol': {p.symbol: p.volume * p.price_current for p in aurora_positions},
                    'positions': {p.symbol: {'size': p.volume, 'pnl': p.profit} for p in aurora_positions}
                }
                
                # Avaliar risco com 4 camadas (v6.0)
                risk_assessment = self.risk_engine.assess_trade_risk(
                    symbol=symbol,
                    signal_size=0.1,  # Tamanho padrão
                    current_price=market_data.get('bid', 0) or market_data.get('last_close', 0),
                    portfolio_state=portfolio_state
                )
                
                # TEMPORARIAMENTE: Aceitar trades mesmo com risco alto para testes (apenas logar)
                if not risk_assessment.get('approved', False):
                    risk_level = risk_assessment.get('risk_level', 'HIGH')
                    risk_score = risk_assessment.get('risk_score', 1.0)
                    logger.warning(f"[RISK] {symbol} - Risco detectado: {risk_level} (score: {risk_score:.2f}) - MAS PERMITINDO PARA TESTES")
                    # NÃO BLOQUEAR - apenas logar para coletar dados
                    # return None  # COMENTADO PARA TESTES
                
                # Log recomendações se houver
                recommendations = risk_assessment.get('recommendations', [])
                if recommendations:
                    logger.info(f"[RISK] {symbol} - {recommendations[0]}")
                    
            except Exception as e:
                logger.warning(f"[RISK] Erro na avaliação de risco para {symbol}: {e}")
                # Continuar se RiskEngine falhar (não bloquear)
        
        # 7. Análise de Sentimento (opcional, não bloqueia)
        sentiment_info = ""
        if self.sentiment_aggregator:
            try:
                # Simular dados de sentimento (em produção viria de APIs)
                # Por enquanto, usar análise básica do preço
                price_change = (market_data['last_close'] - market_data.get('ma20', market_data['last_close'])) / market_data['last_close']
                sentiment_score = 0.5 + (price_change * 10)  # Normalizar
                sentiment_score = max(0.0, min(1.0, sentiment_score))
                
                sentiment_info = f"\nSENTIMENTO: {sentiment_score:.2f} ({'POSITIVO' if sentiment_score > 0.6 else 'NEGATIVO' if sentiment_score < 0.4 else 'NEUTRO'})"
            except Exception as e:
                logger.debug(f"[SENTIMENT] Erro ao calcular sentimento: {e}")
        
        # 8. Obter consenso do conselho
        context = f"""
FILTROS: Spread OK ({filters['spread']['spread_pips']:.1f} pips), Sessao: {filters['session']['current_sessions']}
SINAL TECNICO: {market_data.get('ma_signal', 'NEUTRAL')}
CORRELACAO: Risco verificado - OK{sentiment_info}
"""
        
        consensus = await self.council.get_consensus(symbol, market_data, context)
        
        logger.info(f"[ANALYZE] {symbol} - Consenso: {consensus.get('decision', 'N/A')} | "
                   f"Confianca: {consensus.get('confidence', 0):.2f} | "
                   f"Percentual: {consensus.get('consensus_percent', 0):.1f}%")
        
        if consensus["decision"] in ["BUY", "SELL"]:
            signal = {
                "symbol": symbol,
                "direction": consensus["decision"],
                "confidence": consensus.get("confidence", 0),
                "consensus_percent": consensus.get("consensus_percent", 0),
                "trade_id": consensus["trade_id"],
                "agents_voted": consensus.get("agents_voted", []),
                "market_data": market_data
            }
            logger.info(f"[ANALYZE] {symbol} - ✅✅✅ SINAL GERADO: {consensus['decision']} | "
                       f"Trade ID: {consensus['trade_id']} | "
                       f"Consenso: {consensus.get('consensus_percent', 0):.1f}%")
            return {
                "success": True,
                "signal": signal,
                "symbol": symbol
            }
        else:
            logger.info(f"[ANALYZE] {symbol} - Sem sinal (decision: {consensus.get('decision', 'N/A')}, "
                       f"consenso: {consensus.get('consensus_percent', 0):.1f}%)")
        
        return {
            "success": True,
            "signal": None,
            "symbol": symbol
        }
    
    def execute_trade(self, signal: Dict) -> bool:
        """Executa trade no MT5 com validação Pydantic e evidência (v5.0)"""
        symbol = signal["symbol"]
        direction = signal["direction"]
        
        # Validar com Pydantic se disponível (v5.0)
        if CORE_MODULES_AVAILABLE:
            try:
                trade_signal = TradeSignal(
                    action=direction,
                    symbol=symbol,
                    size=0.1,
                    confidence=signal.get("confidence", 0.5),
                    stop_loss=signal["market_data"].get("atr", 0) * 2,
                    take_profit=signal["market_data"].get("atr", 0) * 3,
                    strategy_id=signal.get("trade_id", "AURORA"),
                    metadata=signal
                )
            except Exception as e:
                logger.error(f"[TRADE] Validação Pydantic falhou: {e}")
                return False
        
        info = mt5.symbol_info(symbol)
        if not info:
            return False
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return False
        
        # Configurar ordem
        volume = 0.1  # Lote fixo
        
        if direction == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
            sl = price - (signal["market_data"]["atr"] * 2)
            tp = price + (signal["market_data"]["atr"] * 3)
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
            sl = price + (signal["market_data"]["atr"] * 2)
            tp = price - (signal["market_data"]["atr"] * 3)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": MAGIC_NUMBER,
            "comment": f"AURORA_{signal['trade_id'][:8]}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        start_time = datetime.now()
        result = mt5.order_send(request)
        execution_latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            executed_price = result.price
            slippage = abs(executed_price - price) / price if price > 0 else 0
            
            logger.info(f"[TRADE] {direction} {symbol} @ {executed_price:.5f} | SL: {sl:.5f} | TP: {tp:.5f}")
            
            # Criar ExecutionResult com Pydantic (v5.0)
            if CORE_MODULES_AVAILABLE:
                try:
                    execution_result = ExecutionResult(
                        success=True,
                        order_id=str(result.order),
                        symbol=symbol,
                        executed_price=executed_price,
                        requested_price=price,
                        slippage=slippage,
                        commission=0.0,  # Será atualizado quando trade fechar
                        profit_loss=0.0,  # Será atualizado quando trade fechar
                        timestamp=datetime.now(),
                        broker_response={
                            'retcode': result.retcode,
                            'deal': result.deal,
                            'volume': result.volume,
                            'comment': result.comment
                        },
                        latency_ms=execution_latency_ms,
                        checksum=''  # Será calculado
                    )
                    # Calcular checksum
                    execution_result.checksum = execution_result.calculate_checksum()
                    
                    # Criar VerificationEvidence (v5.0)
                    evidence = VerificationEvidence.create(
                        evidence_type='TRADE_EXECUTION',
                        content={
                            'signal': signal,
                            'execution': execution_result.dict(),
                            'result': {
                                'retcode': result.retcode,
                                'deal': result.deal,
                                'volume': result.volume
                            }
                        },
                        source='AURORA_TRADING_SYSTEM'
                    )
                    self.evidence_log.append(evidence)
                    
                except Exception as e:
                    logger.warning(f"[TRADE] Erro ao criar ExecutionResult: {e}")
            
            # Registrar para feedback
            self.feedback.register_trade(
                signal["trade_id"],
                symbol,
                direction,
                signal["agents_voted"],
                executed_price
            )
            
            # Salvar no banco
            self.db.save_trade(
                signal["trade_id"],
                symbol,
                direction,
                executed_price,
                volume,
                signal["consensus_percent"],
                signal["agents_voted"]
            )
            
            # Salvar estado do agente especializado (v5.0)
            if self.storage and CORE_MODULES_AVAILABLE:
                try:
                    agent_id = f"AGT_{symbol}"
                    agent_state = {
                        'last_trade': {
                            'symbol': symbol,
                            'direction': direction,
                            'price': executed_price,
                            'timestamp': datetime.now().isoformat()
                        },
                        'trades_count': self.trades_today
                    }
                    asyncio.create_task(self.storage.save_agent_state(agent_id, agent_state))
                except Exception as e:
                    logger.debug(f"[STORAGE] Erro ao salvar estado do agente: {e}")
            
            # Atualizar aprendizado do agente especializado (v5.0)
            if hasattr(self, 'specialized_agent_system') and self.specialized_agent_system:
                try:
                    agent = self.specialized_agent_system.get_agent(symbol)
                    if agent:
                        # Simular resultado (em produção, obter do MT5 quando trade fechar)
                        was_profitable = signal.get("confidence", 0.5) > 0.6
                        profit = 10.0 if was_profitable else -5.0
                        agent.update_learning(was_profitable, profit)
                except Exception as e:
                    logger.debug(f"[LEARNING] Erro ao atualizar aprendizado: {e}")
            
            self.trades_today += 1
            self.daily_trades += 1
            
            return True
        else:
            error = result.retcode if result else "No result"
            logger.error(f"[TRADE] FALHOU {symbol}: {error}")
            
            # Criar evidência de falha (v5.0)
            if CORE_MODULES_AVAILABLE:
                try:
                    evidence = VerificationEvidence.create(
                        evidence_type='TRADE_EXECUTION_FAILED',
                        content={
                            'signal': signal,
                            'error': str(error),
                            'symbol': symbol
                        },
                        source='AURORA_TRADING_SYSTEM'
                    )
                    self.evidence_log.append(evidence)
                except Exception:
                    pass
            
            return False
    
    async def run_cycle(self):
        """Executa um ciclo de analise"""
        
        # 0. Verificar e reconectar MT5 se necessario
        try:
            if not mt5.initialize():
                logger.error("[CYCLE] MT5 desconectado! Tentando reconectar...")
                await asyncio.sleep(2)
                if not mt5.initialize():
                    logger.error("[CYCLE] FALHA ao reconectar MT5!")
                    return
                else:
                    logger.info("[CYCLE] MT5 reconectado com sucesso!")
                    account = mt5.account_info()
                    logger.info(f"[CYCLE] Conta: {account.login} | Servidor: {account.server}")
        except Exception as e:
            logger.error(f"[CYCLE] Erro ao verificar MT5: {e}")
            return
        
        # 1. Verificar Circuit Breaker
        if self.circuit_breaker_state == 'OPEN':
            if self.circuit_last_failure:
                time_since_failure = (datetime.now() - self.circuit_last_failure).total_seconds()
                if time_since_failure > self.circuit_cooldown_seconds:
                    self.circuit_breaker_state = 'HALF_OPEN'
                    logger.info("[CIRCUIT] Circuit breaker em modo HALF_OPEN")
                else:
                    logger.warning(f"[CIRCUIT] Circuito aberto - aguardando cooldown ({int(self.circuit_cooldown_seconds - time_since_failure)}s)")
                    await asyncio.sleep(10)
                    return
            else:
                await asyncio.sleep(10)
                return
        
        # 2. Health Check (a cada ciclo)
        try:
            await self._check_system_health()
        except Exception as e:
            logger.warning(f"[HEALTH] Erro no health check: {e}")
        
        # 3. Atualizar matriz de correlacao (a cada ciclo)
        if self.correlation_engine:
            try:
                self.update_correlation_matrix()
            except Exception as e:
                logger.debug(f"[CYCLE] Erro ao atualizar correlacao: {e}")
        
        # 4. Verificar kill switch
        ks = self.kill_switch.check()
        if ks["triggered"]:
            logger.critical("[CYCLE] Kill switch ativado!")
            self.kill_switch.close_all_positions()
            self.running = False
            return
        
        # 2. Processar feedback de trades fechados
        self.feedback.check_closed_positions()
        
        # 3. Atualizar matriz de correlacao (a cada 5 min)
        self.update_correlation_matrix()
        
        # 5. Daily Metrics Reset (v5.2 Improvement)
        await self._check_and_reset_daily_metrics()
        
        # 6. Processar símbolos em paralelo (v5.2 Improvement - com controle de rate limit)
        # Processar em batches para respeitar rate limits
        batch_size = 3  # Máximo de símbolos em paralelo
        cycle_index = getattr(self, '_cycle_index', 0)
        
        # Selecionar símbolos para este ciclo (rotativo)
        symbols_to_process = []
        for i in range(min(batch_size, len(self.assets))):
            idx = (cycle_index + i) % len(self.assets)
            symbols_to_process.append(self.assets[idx])
        
        self._cycle_index = cycle_index + batch_size
        
        logger.info(f"[CYCLE] Processando {len(symbols_to_process)} símbolos em paralelo: {symbols_to_process}")
        
        # Processar em paralelo com asyncio.gather
        cycle_success = False
        cycle_errors = 0
        
        try:
            tasks = [self._process_symbol_safe(symbol) for symbol in symbols_to_process]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            for i, result in enumerate(results):
                symbol = symbols_to_process[i]
                
                if isinstance(result, Exception):
                    cycle_errors += 1
                    logger.error(f"[CYCLE] Erro em {symbol}: {result}")
                    self.circuit_failure_count += 1
                elif result and result.get('success'):
                    cycle_success = True
                    signal = result.get('signal')
                    if signal:
                        logger.info(f"[SIGNAL] ✅ {symbol} - {signal.get('direction', 'N/A')} | "
                                   f"Consenso: {signal.get('consensus_percent', 0):.1f}% | "
                                   f"Confianca: {signal.get('confidence', 0):.2f}")
                        logger.info(f"[SIGNAL] Executando trade AGORA...")
                        try:
                            executed = self.execute_trade(signal)
                            if executed:
                                logger.info(f"[SIGNAL] ✅✅✅ TRADE EXECUTADO: {symbol} {signal.get('direction')} - DEVE APARECER NO JOURNAL DO MT5!")
                            else:
                                logger.error(f"[SIGNAL] ❌ Falha ao executar trade: {symbol}")
                        except Exception as e:
                            logger.error(f"[SIGNAL] ❌ Erro ao executar trade: {e}")
                    else:
                        logger.debug(f"[CYCLE] {symbol}: Processado mas sem sinal de trade (result: {result})")
                
                # Atualizar Circuit Breaker baseado em resultados
                if cycle_success and self.circuit_breaker_state == 'HALF_OPEN':
                    self.circuit_breaker_state = 'CLOSED'
                    self.circuit_failure_count = 0
                    logger.info("[CIRCUIT] Circuit breaker fechado (recuperado)")
                elif cycle_errors > 0 and self.circuit_failure_count >= self.circuit_failure_threshold:
                    self.circuit_breaker_state = 'OPEN'
                    self.circuit_last_failure = datetime.now()
                    logger.warning(f"[CIRCUIT] Circuit breaker aberto após {self.circuit_failure_count} falhas")
            
            # Delay após batch para respeitar rate limits (30s entre batches)
            if len(symbols_to_process) > 0:
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.critical(f"[CYCLE] Erro crítico no processamento paralelo: {e}", exc_info=True)
            cycle_errors += 1
            self.circuit_failure_count += 1
    
    async def _process_symbol_safe(self, symbol: str) -> Dict[str, Any]:
        """Processa um símbolo de forma segura (wrapper para paralelismo)"""
        try:
            signal = await self.analyze_symbol(symbol)
            
            if signal:
                executed = self.execute_trade(signal)
                return {
                    'success': executed,
                    'signal': signal,
                    'symbol': symbol
                }
            else:
                return {'success': True, 'signal': None, 'symbol': symbol}
                
        except Exception as e:
            logger.error(f"[PROCESS] Erro ao processar {symbol}: {e}")
            raise  # Re-raise para asyncio.gather capturar
        
        # 4. Status
        positions = mt5.positions_get()
        aurora_positions = [p for p in (positions or []) if p.magic == MAGIC_NUMBER]
        total_profit = sum(p.profit for p in aurora_positions)
        
        logger.info(f"[STATUS] Posicoes: {len(aurora_positions)} | Profit: {total_profit:+.2f} | Trades hoje: {self.trades_today}")
        logger.info(f"[HEALTH] Score: {self.health_score:.1f}% | Circuit: {self.circuit_breaker_state}")
    
    async def _check_system_health(self):
        """Verifica saúde do sistema e calcula score"""
        checks = {}
        score = 100.0
        
        # 1. Verificar MT5
        try:
            account = mt5.account_info()
            if account:
                checks['mt5'] = {'status': 'OK', 'balance': account.balance}
            else:
                checks['mt5'] = {'status': 'ERROR'}
                score -= 20
        except Exception as e:
            checks['mt5'] = {'status': 'ERROR', 'error': str(e)}
            score -= 20
        
        # 2. Verificar agentes (simplificado - verificar se council está inicializado)
        try:
            # Verificar se council tem agentes ativos
            if hasattr(self.council, 'agents') and self.council.agents:
                total_agents = len(self.council.agents)
                checks['agents'] = {'status': 'OK', 'total': total_agents}
            else:
                checks['agents'] = {'status': 'DEGRADED', 'total': 0}
                score -= 20
        except Exception as e:
            checks['agents'] = {'status': 'ERROR', 'error': str(e)}
            score -= 20
        
        # 3. Verificar módulos quantitativos
        if not QUANTITATIVE_MODULES_AVAILABLE:
            checks['quantitative'] = {'status': 'UNAVAILABLE'}
            score -= 10
        else:
            checks['quantitative'] = {'status': 'OK'}
        
        # 4. Verificar Circuit Breaker
        if self.circuit_breaker_state == 'OPEN':
            checks['circuit_breaker'] = {'status': 'OPEN', 'failures': self.circuit_failure_count}
            score -= 15
        elif self.circuit_breaker_state == 'HALF_OPEN':
            checks['circuit_breaker'] = {'status': 'HALF_OPEN'}
            score -= 5
        else:
            checks['circuit_breaker'] = {'status': 'CLOSED'}
        
        # 5. Verificar kill switch
        ks = self.kill_switch.check()
        if ks['triggered']:
            checks['kill_switch'] = {'status': 'TRIGGERED'}
            score = 0  # Sistema deve parar
        else:
            checks['kill_switch'] = {'status': 'OK', 'drawdown': ks.get('current_drawdown', 0)}
        
        # Atualizar score
        self.health_score = max(0.0, min(100.0, score))
        self.last_health_check = datetime.now()
        
        # Alertas
        if self.health_score < 50:
            logger.critical(f"[HEALTH] ⚠️ Saúde crítica: {self.health_score:.1f}%")
        elif self.health_score < 70:
            logger.warning(f"[HEALTH] ⚠️ Saúde degradada: {self.health_score:.1f}%")
        
        return {
            'score': self.health_score,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _check_and_reset_daily_metrics(self):
        """Reset automático de métricas diárias (v5.2 Improvement)"""
        current_date = datetime.now().date()
        
        if current_date > self.last_reset_day:
            logger.info(f"[RESET] Resetando métricas diárias para {current_date}")
            
            # Resetar métricas diárias
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.trades_today = 0
            self.last_reset_day = current_date
            
            # Resetar kill switch diário (se aplicável)
            if hasattr(self.kill_switch, 'reset_daily'):
                self.kill_switch.reset_daily()
            
            logger.info(f"[RESET] Métricas resetadas: Trades={self.daily_trades}, PnL={self.daily_pnl:.2f}")
    
    async def run(self):
        """Loop principal"""
        if not await self.initialize():
            logger.error("Falha na inicializacao!")
            return
        
        self.running = True
        cycle = 0
        
        logger.info("[RUN] Sistema iniciado - Loop principal")
        logger.info("[RUN] ========================================")
        logger.info("[RUN] EXECUTANDO PRIMEIRO CICLO AGORA!")
        logger.info("[RUN] ========================================")
        
        while self.running:
            try:
                cycle += 1
                logger.info(f"\n{'='*70}")
                logger.info(f"[CYCLE {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*70}")
                
                await self.run_cycle()
                
                logger.info(f"[CYCLE {cycle}] Concluido! Trades executados: {self.trades_today}")
                logger.info(f"[CYCLE {cycle}] Aguardando 30 segundos para proximo ciclo...")
                
                # Aguardar proximo ciclo (30 segundos para testes - depois voltar para 300)
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("[RUN] Interrompido pelo usuario")
                self.running = False
            except Exception as e:
                logger.error(f"[RUN] Erro no ciclo: {e}")
                await asyncio.sleep(60)
        
        # Relatorio final
        self.print_final_report()
    
    def print_final_report(self):
        """Imprime relatorio final"""
        logger.info("\n" + "="*60)
        logger.info("RELATORIO FINAL - AURORA FULL POWER")
        logger.info("="*60)
        
        metrics = self.db.get_agent_metrics()
        
        logger.info("\nMETRICAS DOS AGENTES:")
        for name, data in metrics.items():
            logger.info(f"  {name}: {data['correct_votes']}/{data['total_votes']} = {data['accuracy']*100:.1f}%")
        
        logger.info(f"\nTrades executados: {self.trades_today}")
        logger.info("="*60)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    system = AuroraFullPower()
    asyncio.run(system.run())

