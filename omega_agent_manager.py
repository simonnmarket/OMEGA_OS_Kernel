import os
import sqlite3
import numpy as np
import threading
import time
from datetime import datetime
import MetaTrader5 as mt5

class TradingAgent:
    """
    Agente individual especializado num Símbolo e numa Estratégia.
    O Verdadeiro Organismo Meta-Cognitivo.
    """
    def __init__(self, agent_id: str, symbol: str, strategy_name: str, 
                 confidence: float, win_count: int, loss_count: int, total_pnl: float):
        self.agent_id = agent_id
        self.symbol = symbol
        self.strategy = strategy_name
        self.confidence = float(confidence)
        self.win_count = int(win_count)
        self.loss_count = int(loss_count)
        self.total_pnl = float(total_pnl)
        self.total_trades = self.win_count + self.loss_count

    def process_closed_trade(self, pnl: float):
        """ Feedback Loop: O sistema aprende e afina o rigor dele mesmo """
        if pnl > 0:
            self.win_count += 1
            # Recompensa
            self.confidence *= 1.05
        else:
            self.loss_count += 1
            # Penalidade
            self.confidence *= 0.95
        
        # Limites Saudáveis Institucionais (30% a 95%)
        self.confidence = max(0.30, min(0.95, self.confidence))
        self.total_pnl += pnl
        self.total_trades += 1

class OmegaAgentManager:
    """
    Gerenciador Central de Agentes Artificiais OMEGA (O Meta-Learning).
    """
    def __init__(self, db_path=r"C:\Users\Lenovo\BAU_DO_TESOURO\05_DATABASE\omega_agents.db"):
        self.db_path = db_path
        self._init_db()
        self.agents = {} # Em Memória Viva
        self.processed_tickets = set()
        self._load_agents()
        
        # Iniciar Feedback Thread Paralela
        self.feedback_thread = threading.Thread(target=self._monitor_mt5_history, daemon=True)
        self.feedback_thread.start()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                confidence REAL DEFAULT 0.50,
                win_count INTEGER DEFAULT 0,
                loss_count INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0.0,
                last_updated TEXT
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                ticket INTEGER PRIMARY KEY,
                agent_id TEXT,
                pnl REAL,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def _load_agents(self):
        """Carrega do DB para Memória"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT * FROM agents')
        rows = cur.fetchall()
        for r in rows:
            # 0: id, 1: sym, 2: strat, 3: conf, 4: win, 5: loss, 6: pnl, 7: last
            ag = TradingAgent(r[0], r[1], r[2], r[3], r[4], r[5], r[6])
            self.agents[ag.agent_id] = ag
            
        cur.execute('SELECT ticket FROM trade_history')
        for t in cur.fetchall():
            self.processed_tickets.add(t[0])
        conn.close()
        print(f"      [🧠] OMEGA Meta-Learning: {len(self.agents)} Agentes recuperados da Memória Episódica.")

    def get_or_create_agent(self, symbol: str, strategy_name: str) -> TradingAgent:
        agent_id = f"AGENT_{symbol}_{strategy_name}"
        if agent_id in self.agents:
            return self.agents[agent_id]
            
        # Não existe, vamos criar e injetar a Probabilidade Incial Conservadora
        agent = TradingAgent(agent_id, symbol, strategy_name, 0.50, 0, 0, 0.0)
        self.agents[agent_id] = agent
        
        # Persistir
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO agents (agent_id, symbol, strategy, confidence, win_count, loss_count, total_pnl, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (agent_id, symbol, strategy_name, agent.confidence, agent.win_count, agent.loss_count, agent.total_pnl, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return agent

    def save_agent_state(self, agent: TradingAgent):
        """Guarda Feedback"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            UPDATE agents SET 
                confidence=?, win_count=?, loss_count=?, total_pnl=?, last_updated=?
            WHERE agent_id=?
        ''', (agent.confidence, agent.win_count, agent.loss_count, agent.total_pnl, datetime.now().isoformat(), agent.agent_id))
        conn.commit()
        conn.close()

    def register_new_ticket(self, ticket: int, agent_id: str):
        """Regista no DB que Ticket X pertence a Agente Y (para quando fechar)"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
             cur.execute('INSERT INTO trade_history (ticket, agent_id, pnl, timestamp) VALUES (?, ?, ?, ?)', 
                         (ticket, agent_id, 0.0, datetime.now().isoformat()))
             conn.commit()
        except:
             pass
        conn.close()

    def _monitor_mt5_history(self):
        """
        Feedback Loop: Varre o Metatrader constantemente em Background
        Se apanhar um trade fechado, recompensa ou pune o Agente correspondente.
        """
        while True:
            time.sleep(30) # Varia a cada 30 segundos
            if not mt5.terminal_info():
                continue
                
            # Buscar deals desde ontem
            date_from = datetime.now() - timedelta(days=2)
            deals = mt5.history_deals_get(date_from, datetime.now())
            if deals is None: continue
            
            for deal in deals:
                if deal.entry == mt5.DEAL_ENTRY_OUT: # Fecho de posição
                    ticket = deal.position_id # MT5 liga deals de saída à posição original
                    if ticket not in self.processed_tickets:
                        pnl = deal.profit + deal.commission + deal.swap
                        self._process_closed_trade(ticket, pnl)
                        
    def _process_closed_trade(self, ticket: int, pnl: float):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # Verificar qual Agente foi responsável por esta ordem
        cur.execute('SELECT agent_id FROM trade_history WHERE ticket=?', (ticket,))
        row = cur.fetchone()
        
        if row:
            agent_id = row[0]
            if agent_id in self.agents:
                ag = self.agents[agent_id]
                old_conf = ag.confidence
                ag.process_closed_trade(pnl)
                self.save_agent_state(ag)
                
                # Regista o pnl
                cur.execute('UPDATE trade_history SET pnl=? WHERE ticket=?', (pnl, ticket))
                conn.commit()
                
                print(f"\n      [FEEDBACK LOOP] Trade {ticket} Fechado: {pnl:.2f}USD")
                print(f"      [🧠] Evolução Agente ({ag.agent_id}): Confiança {old_conf*100:.1f}% -> {ag.confidence*100:.1f}%.")
                
        self.processed_tickets.add(ticket)
        conn.close()
