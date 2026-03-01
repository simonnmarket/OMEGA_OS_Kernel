#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROMETHEUS MASTER CONTROL v5.1: MÓDULO DE CONTROLE E EXECUÇÃO

Arquitetura Científica: Karl Popper (Filtros de Refutação) + John von Neumann (Sistemas Modulares)
Objetivo: Corrigir o viés destrutivo e o excesso de trades em regime de ruído.

Dependências: MetaTrader5 (mt5), pandas (pd), numpy (np)
"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import time
import datetime
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# --- CONFIGURAÇÕES GLOBAIS ---
_BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = str(_BASE_DIR / "config.json")
LOG_FILE = "prometheus_master_log_v5.1.jsonl"
HEARTBEAT_FILE = "prometheus_heartbeat.tmp"
LEARNING_FILE = "prometheus_v6_learning.json"
MAX_MEMORY = 100  # Número de resultados de trades a manter para o cálculo do Q-Value

# Configuração do Logger
logger = logging.getLogger("PrometheusMaster_v5.1")
logger.setLevel(logging.INFO)
logger.handlers.clear()
handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
formatter = logging.Formatter('{"timestamp":"%(asctime)s","level":"%(levelname)s","message":%(message)s}')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Adicionar handler para console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# ==============================================================================
# --- MÓDULO 1: DIAGNÓSTICO E CONFIGURAÇÃO DE RISCO ADAPTATIVO (Von Neumann) ---
# ==============================================================================

RISK_CONFIG_ASSET_CLASSES = {
    # CONFIGURAÇÃO DE MOEDAS PRINCIPAIS (ALTA LIQUIDEZ, PULLBACK CONSERVADOR)
    "FX_MAJORS": {
        "symbols": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
        "atr_sl_multiplier": 2.0,
        "atr_tp_multiplier": 3.0,
        "risk_per_trade_percent": 0.01,
        "max_daily_trades": 5,
        "min_adx_threshold": 20,
        # ESTÁGIO 1: Horário Otimizado (UTC) - Foco Londres/Nova York
        "optimal_trading_hours_utc": [[7, 0], [21, 0]], 
        "forbidden_trading_days": ["Saturday", "Sunday", "Friday_Pre_Close"], 
        # ESTÁGIO 2: RSI CONSERVADOR (Pullbacks mais discretos/mais perto do 50)
        "rsi_pullback_range": [40, 60], 
    },
    # CONFIGURAÇÃO DE METAIS (MÉDIA VOLATILIDADE, PULLBACK MAIS PROFUNDO)
    "METALS": {
        "symbols": ["XAUUSD", "XAGUSD"],
        "atr_sl_multiplier": 2.5,
        "atr_tp_multiplier": 4.0,
        "risk_per_trade_percent": 0.008,
        "max_daily_trades": 3,
        "min_adx_threshold": 25,
        # ESTÁGIO 1: Horário Otimizado (UTC) - Foco Sessão Americana
        "optimal_trading_hours_utc": [[12, 0], [22, 0]], 
        "forbidden_trading_days": ["Saturday", "Sunday", "Friday_Pre_Close"], 
        # ESTÁGIO 2: RSI RELAXADO (Permite Pullbacks mais profundos)
        "rsi_pullback_range": [30, 70], 
    },
    # CONFIGURAÇÃO DE CRYPTOMOEDAS (ALTA VOLATILIDADE, REQUER ADX FORTE)
    "CRYPTO": {
        "symbols": ["BTCUSD", "ETHUSD"],
        "atr_sl_multiplier": 3.0,
        "atr_tp_multiplier": 5.0,
        "risk_per_trade_percent": 0.005,
        "max_daily_trades": 2,
        # Aumento do ADX para 30 para mitigar o ruído 24/7
        "min_adx_threshold": 30, 
        # ESTÁGIO 1: 24/7 Operacional (Apenas dias/horários proibidos aplicam)
        "optimal_trading_hours_utc": [[0, 0], [24, 0]], 
        "forbidden_trading_days": [], 
        # ESTÁGIO 2: RSI RELAXADO (Permite Pullbacks mais profundos)
        "rsi_pullback_range": [30, 70], 
    },
    "CFD_STOCKS": {
        "symbols": [],  # Será preenchido dinamicamente
        "atr_sl_multiplier": 2.5,
        "atr_tp_multiplier": 4.0,
        "risk_per_trade_percent": 0.007,
        "max_daily_trades": 4,
        "min_adx_threshold": 22,
        # ESTÁGIO 1: Horário de mercado de ações (UTC)
        "optimal_trading_hours_utc": [[13, 30], [20, 0]],  # 13:30-20:00 UTC (horário de mercado US)
        "forbidden_trading_days": ["Saturday", "Sunday"], 
        # ESTÁGIO 2: RSI MODERADO para stocks
        "rsi_pullback_range": [35, 65], 
    }
}

def get_asset_config(symbol: str):
    """Obtém configuração específica de risco e filtro para cada ativo. Retorna (config, asset_class)."""
    for asset_class, config in RISK_CONFIG_ASSET_CLASSES.items():
        if symbol in config["symbols"]:
            # Retorna a configuração do grupo e o nome da classe
            return config, asset_class
    
    # Fallback seguro
    logger.warning(json.dumps({"event": "symbol_not_found", "symbol": symbol, "message": f"Símbolo {symbol} não encontrado, usando configuração FX_MAJORS como padrão seguro."}))
    return RISK_CONFIG_ASSET_CLASSES["FX_MAJORS"], "FX_MAJORS"

def is_optimal_time_to_trade(symbol: str) -> bool:
    """
    FILTRO DE INDIVIDUALIDADE 1.0 (ESTÁGIO 1):
    Verifica se o horário e dia atual estão dentro das janelas de negociação 
    definidas (baseado em liquidez).
    """
    config, asset_class = get_asset_config(symbol)
    
    # Obter hora atual em UTC
    now_utc = datetime.datetime.utcnow()
    day_of_week = now_utc.strftime('%A')
    
    # Mapeamento do dia da semana (apenas para exibição no log)
    day_map = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }

    # 1. Checagem de Dias Proibidos
    if day_of_week in config.get("forbidden_trading_days", []):
        logger.debug(json.dumps({
            "event": "forbidden_day",
            "symbol": symbol,
            "day": day_of_week,
            "message": f"Dia '{day_map.get(day_of_week, day_of_week)}' é um dia de negociação proibido."
        }))
        return False
        
    # Checagem de Sexta-feira Pre-fechamento (Se aplicável)
    if day_of_week == 'Friday' and 'Friday_Pre_Close' in config.get("forbidden_trading_days", []):
        # Bloqueio de trades após 20:00 UTC na sexta-feira
        if now_utc.hour >= 20: 
            logger.debug(json.dumps({
                "event": "friday_pre_close",
                "symbol": symbol,
                "hour": now_utc.hour,
                "message": "Sexta-feira Pós 20:00 UTC (Pre-fechamento)."
            }))
            return False

    # 2. Checagem de Janela de Horário
    start_hour, start_minute = config["optimal_trading_hours_utc"][0]
    end_hour, end_minute = config["optimal_trading_hours_utc"][1]
    
    current_time_minutes = now_utc.hour * 60 + now_utc.minute
    start_time_minutes = start_hour * 60 + start_minute
    end_time_minutes = end_hour * 60 + end_minute

    is_open_window = False
    
    # Lógica para janelas que cruzam a meia-noite (e.g., 22:00 - 05:00)
    if start_time_minutes <= end_time_minutes:
        if start_time_minutes <= current_time_minutes < end_time_minutes:
            is_open_window = True
    else:
        if current_time_minutes >= start_time_minutes or current_time_minutes < end_time_minutes:
            is_open_window = True

    # Crypto opera 24/7 (a menos que explicitamente restrito acima)
    if not is_open_window and asset_class != "CRYPTO":
        logger.debug(json.dumps({
            "event": "outside_trading_hours",
            "symbol": symbol,
            "current_time": f"{now_utc.hour:02d}:{now_utc.minute:02d}",
            "window": f"{start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d}",
            "message": "Horário fora da janela de negociação."
        }))
        return False
    
    return True

# ==============================================================================
# --- MÓDULO 2: FILTRO DE REGIME E INDICADORES (Popper/Wilder's DMI) ---
# ==============================================================================

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Calcula o ADX (Average Directional Index) - Força de Tendência."""
    # 1. True Range (TR)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    
    # 2. Directional Movement (DM)
    up = high - high.shift(1)
    down = low.shift(1) - low
    
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    
    # 3. Smoothed Directional Index (DI)
    plus_di = 100 * (pd.Series(plus_dm).ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm).ewm(span=period, adjust=False).mean() / atr)
    
    # 4. Directional Index (DX) e Average Directional Index (ADX)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(span=period, adjust=False).mean()
    
    return adx.iloc[-1] if not adx.empty else 0.0

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Calcula o ATR para Stop Loss dinâmico."""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    return atr.iloc[-1] if not atr.empty else 0.0

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """Calcula o RSI (Relative Strength Index)."""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Cálculo da média móvel exponencial de ganho e perda
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    # Evita divisão por zero
    rs = avg_gain / avg_loss if avg_loss.iloc[-1] != 0 else np.inf
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1] if not rsi.empty else 50.0

def is_trending_regime(symbol: str, timeframe: str = 'H4') -> bool:
    """Filtro Popperiano: Refuta trades em mercados sem tendência (ADX)."""
    config, _ = get_asset_config(symbol)
    threshold = config["min_adx_threshold"]
    
    try:
        # Mapeamento do Timeframe para MT5
        tf_mapping = {'M5': mt5.TIMEFRAME_M5, 'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4}
        mt5_tf = tf_mapping.get(timeframe, mt5.TIMEFRAME_H4)
        
        # Obter dados (pelo menos 100 barras para cálculo robusto)
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 100)
        if rates is None or len(rates) < 50:
            logger.warning(json.dumps({"event": "insufficient_data", "symbol": symbol, "timeframe": timeframe, "message": f"Dados insuficientes para {symbol} {timeframe}"}))
            return False
            
        df = pd.DataFrame(rates)
        
        # Calcular ADX
        adx_value = calculate_adx(pd.Series(df['high']), pd.Series(df['low']), pd.Series(df['close']))
        
        # Aplicar filtro
        regime_trending = adx_value >= threshold
        
        logger.info(json.dumps({
            "event": "regime_check",
            "symbol": symbol,
            "timeframe": timeframe,
            "adx": round(adx_value, 1),
            "threshold": threshold,
            "regime": "TENDÊNCIA" if regime_trending else "RUIDO"
        }))
        
        return regime_trending
        
    except Exception as e:
        logger.error(json.dumps({"event": "adx_calculation_error", "symbol": symbol, "error": str(e)}))
        return False

# ==============================================================================
# --- MÓDULO 3: POSIÇÃO E GESTÃO DE RISCO (Saída Probabilística) ---
# ==============================================================================

def calculate_position_size(symbol: str, account_balance: float, sl_price: float, entry_price: float) -> float:
    """Calcula tamanho de posição baseado em risco percentual e SL dinâmico (com MT5)."""
    config, _ = get_asset_config(symbol)
    
    # 1. Calcular risco em dinheiro
    risk_capital = account_balance * config["risk_per_trade_percent"]
    
    # 2. Calcular pontos de SL
    sl_points = abs(entry_price - sl_price)
    
    # 3. Obter informações do símbolo (pip size, volume limits)
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(json.dumps({"event": "symbol_info_failed", "symbol": symbol}))
        return 0.01  # Fallback
        
    # Calcular valor do pip (depende da corretora e contrato)
    # Assumindo cálculo padrão: Valor Ponto * Unidades/Lote / Pip
    point_value = symbol_info.trade_contract_size * symbol_info.point
    
    # Calcular volume (lotes)
    if sl_points > 0 and point_value > 0:
        # (Risco em Dinheiro) / (Distância SL em Pontos * Valor do Ponto)
        # O sl_points / symbol_info.point normaliza para o tamanho do 'ponto' do MT5.
        volume = risk_capital / (sl_points / symbol_info.point * point_value)
        
        # 4. Ajustar para lotes mínimos/máximos e step
        volume = max(symbol_info.volume_min, min(symbol_info.volume_max, volume))
        # Arredondar para o volume_step da corretora
        volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
        
        logger.info(json.dumps({
            "event": "position_size_calculated",
            "symbol": symbol,
            "volume": round(volume, 2),
            "risk_capital": round(risk_capital, 2),
            "sl_points": round(sl_points, 5)
        }))
        return volume
    
    return symbol_info.volume_min if symbol_info else 0.01

class PositionManager:
    """Gerencia Saída Parcial (Break-Even) e Trailing Stop."""
    def __init__(self):
        # Dicionário para rastrear o estado de cada posição ativa (persistência da memória)
        self.active_positions = {}
    
    def manage_open_positions(self):
        """Monitora e gerencia todas as posições abertas no MT5."""
        positions = mt5.positions_get()
        if positions is None:
            return
            
        # Limpar posições que foram fechadas e reportar ao AFR
        current_tickets = {pos.ticket for pos in positions}
        for ticket in list(self.active_positions.keys()):
            if ticket not in current_tickets:
                # Posição foi fechada - reportar resultado ao AFR
                if self.reinforcement_agent and ticket in self.entry_adx and ticket in self.entry_asset_class:
                    # Calcular P&L da posição fechada (buscar no histórico de deals)
                    profit_loss = self._calculate_closed_position_pnl(ticket)
                    if profit_loss is not None:
                        asset_class = self.entry_asset_class[ticket]
                        adx_at_entry = self.entry_adx[ticket]
                        self.reinforcement_agent.report_trade_result(asset_class, adx_at_entry, profit_loss)
                
                # Limpar dados
                del self.active_positions[ticket]
                if ticket in self.entry_adx:
                    del self.entry_adx[ticket]
                if ticket in self.entry_asset_class:
                    del self.entry_asset_class[ticket]

        for position in positions:
            self._manage_single_position(position)
    
    def _manage_single_position(self, position):
        symbol = position.symbol
        ticket = position.ticket
        
        # Inicializar dados da posição se for nova
        if ticket not in self.active_positions:
            self.active_positions[ticket] = {
                'initial_volume': position.volume,
                'entry_price': position.price_open,
                'partial_closed': False,
                'be_triggered': False,
                'current_sl': position.sl,
                'highest_low': position.price_open # Ponto extremo para Trailing
            }
        
        pos_data = self.active_positions[ticket]
        
        # Obter o preço atual
        tick = mt5.symbol_info_tick(symbol)
        if tick is None: return
        current_price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        # 1. VERIFICAR BREAK-EVEN (Saída Parcial em 1:1 RR)
        if not pos_data['partial_closed']:
            self._check_break_even(ticket, position, current_price, pos_data)
        
        # 2. VERIFICAR TRAILING STOP (Após Break-Even)
        if pos_data['partial_closed']:
            self._check_trailing_stop(ticket, position, current_price, pos_data)

    def _check_break_even(self, ticket, position, current_price, pos_data):
        """Fecha 50% da posição quando o lucro atinge a distância do SL (1:1 RR)."""
        # Distância do SL em pontos (risco original)
        sl_points_distance = abs(position.price_open - position.sl)
        
        if position.type == mt5.ORDER_TYPE_BUY:
            be_price = position.price_open + sl_points_distance # 1:1 RR
            condition = current_price >= be_price
        else:
            be_price = position.price_open - sl_points_distance # 1:1 RR
            condition = current_price <= be_price
        
        if condition and not pos_data['be_triggered']:
            close_volume = position.volume / 2
            
            # 1. Fechar 50% da posição
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position.symbol,
                "volume": close_volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "price": current_price,
                "deviation": 10,
                "magic": 789012,
                "comment": "BREAK_EVEN_50%"
            }
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(json.dumps({
                    "event": "break_even_partial_close",
                    "symbol": position.symbol,
                    "volume_closed": close_volume,
                    "ticket": ticket
                }))
                pos_data['partial_closed'] = True
                
                # 2. Mover SL para o entry price (Protege o resto da posição)
                self._move_sl_to_be(ticket, position, pos_data)

    def _move_sl_to_be(self, ticket, position, pos_data):
        """Move Stop Loss para o preço de entrada (Break-Even)."""
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position.symbol,
            "sl": position.price_open, # SL no preço de entrada original
            "tp": position.tp          # Manter TP original para o resto
        }
        
        result = mt5.order_send(modify_request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(json.dumps({
                "event": "sl_moved_to_break_even",
                "symbol": position.symbol,
                "sl_price": position.price_open,
                "ticket": ticket
            }))
            pos_data['be_triggered'] = True
            pos_data['current_sl'] = position.price_open
        else:
            logger.error(json.dumps({
                "event": "sl_move_failed",
                "symbol": position.symbol,
                "error": result.comment,
                "ticket": ticket
            }))

    def _check_trailing_stop(self, ticket, position, current_price, pos_data):
        """Aplica Trailing Stop de 1.0x ATR a partir do último extremo."""
        
        # 1. Calcular ATR atual no M5
        rates_m5 = mt5.copy_rates_from_pos(position.symbol, mt5.TIMEFRAME_M5, 0, 30)
        if rates_m5 is None: return
        df_m5 = pd.DataFrame(rates_m5)
        atr_value = calculate_atr(df_m5['high'], df_m5['low'], df_m5['close'])
        
        # Usar 1.0x ATR como distância de trailing
        trail_distance = atr_value * 1.0 
        
        is_buy = position.type == mt5.ORDER_TYPE_BUY
        
        # 2. Atualizar Ponto Extremo (Highest High/Lowest Low)
        if is_buy:
            if current_price > pos_data['highest_low']:
                pos_data['highest_low'] = current_price
            
            # Novo SL é o Ponto Extremo - Distância do Trail
            new_sl_price = pos_data['highest_low'] - trail_distance
            
            # Não permitir que o SL retroceda abaixo do SL atual (BE price)
            if new_sl_price > pos_data['current_sl']:
                self._modify_sl_trailing(ticket, position, new_sl_price, pos_data)
                
        else: # SELL
            if current_price < pos_data['highest_low']:
                pos_data['highest_low'] = current_price
                
            # Novo SL é o Ponto Extremo + Distância do Trail
            new_sl_price = pos_data['highest_low'] + trail_distance
            
            # Não permitir que o SL retroceda abaixo do SL atual (BE price)
            if new_sl_price < pos_data['current_sl']:
                self._modify_sl_trailing(ticket, position, new_sl_price, pos_data)

    def _modify_sl_trailing(self, ticket, position, new_sl_price, pos_data):
        """Executa a modificação do SL pelo Trailing Stop."""
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position.symbol,
            "sl": new_sl_price,
            "tp": position.tp,
        }
        
        result = mt5.order_send(modify_request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            pos_data['current_sl'] = new_sl_price
            logger.info(json.dumps({
                "event": "trailing_stop_updated",
                "symbol": position.symbol,
                "new_sl": round(new_sl_price, 5),
                "ticket": ticket
            }))
    
    def _calculate_closed_position_pnl(self, ticket: int) -> Optional[float]:
        """Calcula o P&L de uma posição fechada buscando no histórico de deals"""
        try:
            # Buscar deals do ticket (posição fechada)
            deals = mt5.history_deals_get(ticket=ticket)
            if deals is None or len(deals) == 0:
                return None
            
            # Somar o profit de todos os deals dessa posição
            total_profit = sum(deal.profit for deal in deals)
            return total_profit
        except Exception as e:
            logger.error(json.dumps({"event": "pnl_calculation_error", "ticket": ticket, "error": str(e)}))
            return None
    
    def register_new_position(self, ticket: int, symbol: str, adx_value: float, asset_class: str):
        """Registra uma nova posição para rastreamento do AFR"""
        self.entry_adx[ticket] = adx_value
        self.entry_asset_class[ticket] = asset_class

# ==============================================================================
# --- MÓDULO 4: ESTRATÉGIA DE SINAIS CORRIGIDA (Análise Balanceada) ---
# ==============================================================================

def generate_balanced_signals(symbol: str):
    """
    Gera sinais BUY/SELL baseado em análise real de tendência (MTF MA Cross + Filtro ADX).
    A correção do viés direcional é implementada através da checagem balanceada.
    """
    
    config, asset_class = get_asset_config(symbol)
    
    # 1. FILTRO DE INDIVIDUALIDADE 0: JANELA DE TEMPO ÓTIMA (LIQUIDEZ - ESTÁGIO 1)
    if not is_optimal_time_to_trade(symbol):
        return None
        
    # 2. FILTRO DE REGIME (POPPERIANO) - DEVE PASSAR PRIMEIRO
    if not is_trending_regime(symbol, 'H4'):
        return None
    
    # 3. OBTENÇÃO DE DADOS
    # Otimização: Obter todos os dados em 3 timeframes
    timeframes = {'H4': mt5.TIMEFRAME_H4, 'H1': mt5.TIMEFRAME_H1, 'M5': mt5.TIMEFRAME_M5}
    dfs = {}
    
    for tf_name, tf_mt5 in timeframes.items():
        rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, 100)
        if rates is None: return None
        dfs[tf_name] = pd.DataFrame(rates)

    h4_df, h1_df, m5_df = dfs['H4'], dfs['H1'], dfs['M5']
    
    # 3. IDENTIFICAR TENDÊNCIA PRINCIPAL (H4)
    h4_ma20 = h4_df['close'].rolling(20).mean().iloc[-1]
    h4_ma50 = h4_df['close'].rolling(50).mean().iloc[-1]
    
    if h4_ma20 > h4_ma50: primary_trend = "BUY"
    elif h4_ma20 < h4_ma50: primary_trend = "SELL"
    else: return None # Tendência indefinida

    # 5. CONFIRMAÇÃO (H1) - Cruzamento de MAs (Requer Confluência)
    h1_ma20 = h1_df['close'].rolling(20).mean().iloc[-1]
    h1_ma50 = h1_df['close'].rolling(50).mean().iloc[-1]
    
    h1_trend_direction = "BUY" if h1_ma20 > h1_ma50 else "SELL"
    
    # Lógica de Confluência: H4 e H1 devem concordar estritamente
    if primary_trend != h1_trend_direction:
        logger.debug(json.dumps({
            "event": "trend_conflict",
            "symbol": symbol,
            "h4_trend": primary_trend,
            "h1_trend": h1_trend_direction,
            "message": "Tendências H4/H1 CONFLITANTES (Rejeitado)"
        }))
        return None
    
    # 6. SINAL DE ENTRADA (M5)
    m5_ma20 = m5_df['close'].rolling(20).mean().iloc[-1]
    current_price = m5_df['close'].iloc[-1]
    
    if primary_trend == "BUY" and current_price > m5_ma20:
        signal_type = "BUY"
    elif primary_trend == "SELL" and current_price < m5_ma20:
        signal_type = "SELL"
    else:
        return None
    
    # 7. CONFIRMAÇÃO FINAL (RSI DINÂMICO + Volume) - ESTÁGIO 2
    m5_rsi = calculate_rsi(m5_df)
    volume_avg = m5_df['tick_volume'].rolling(20).mean().iloc[-1]
    current_volume = m5_df['tick_volume'].iloc[-1]
    
    rsi_min, rsi_max = config["rsi_pullback_range"]
    
    # Filtro Pullback RSI (Dinâmico): RSI deve estar na zona de re-entrada (não extremos)
    if not (rsi_min < m5_rsi < rsi_max):
        logger.debug(json.dumps({
            "event": "rsi_filter_failed",
            "symbol": symbol,
            "rsi": round(m5_rsi, 1),
            "rsi_range": f"{rsi_min}-{rsi_max}",
            "message": f"RSI fora da zona de pullback dinâmico"
        }))
        return None

    # Filtro Volume: O sinal deve ser confirmado por um volume decente
    if current_volume < volume_avg * 0.8: 
        logger.debug(json.dumps({
            "event": "volume_filter_failed",
            "symbol": symbol,
            "current_volume": current_volume,
            "volume_threshold": round(volume_avg * 0.8, 0),
            "message": "Volume abaixo de 80% da média"
        }))
        return None
    
    # 8. CALCULAR SL/TP DINÂMICOS
    atr_value = calculate_atr(m5_df['high'], m5_df['low'], m5_df['close'])
    
    # Calcular ADX no H4 para rastreamento do AFR
    adx_at_entry = calculate_adx(pd.Series(h4_df['high']), pd.Series(h4_df['low']), pd.Series(h4_df['close']))
    
    # Obter asset_class para rastreamento do AFR
    _, asset_class = get_asset_config(symbol)
    
    if signal_type == "BUY":
        sl_price = current_price - (atr_value * config["atr_sl_multiplier"])
        tp_price = current_price + (atr_value * config["atr_tp_multiplier"])
    else:
        sl_price = current_price + (atr_value * config["atr_sl_multiplier"])
        tp_price = current_price - (atr_value * config["atr_tp_multiplier"])
        
    return {
        'symbol': symbol,
        'action': signal_type,
        'price': current_price,
        'sl': sl_price,
        'tp': tp_price,
        'atr': atr_value,
        'trend': primary_trend,
        'confidence': 0.95,
        'adx_at_entry': adx_at_entry,  # Para rastreamento do AFR
        'asset_class': asset_class  # Para rastreamento do AFR
    }

# ==============================================================================
# --- MÓDULO 6: REFORÇO ADAPTATIVO (AFR - Adaptive Filter Reinforcement) ---
# John von Neumann (Sistemas Modulares) + ML para otimização de Hiperparâmetros
# ==============================================================================

class AdaptiveReinforcementAgent:
    """
    Agente que usa o histórico de trades (Recompensa/Punição) para ajustar
    dinamicamente o min_adx_threshold de cada classe de ativo.
    """
    def __init__(self, risk_config: Dict[str, Any]):
        self.risk_config = risk_config
        self.q_table = self._load_learning_data()
        self.actions = [-1, 0, 1]  # Ajuste do ADX: [Diminuir, Manter, Aumentar]
        self.epsilon = 0.2  # Taxa de exploração (20% das vezes, tenta uma ação aleatória)
        logger.info(json.dumps({"event": "AFR_INITIALIZED", "message": "🧠 Agente de Reforço Adaptativo (AFR) Inicializado."}))

    def _load_learning_data(self) -> Dict[str, Dict[str, list]]:
        """Carrega os resultados anteriores do disco (simulando DB)."""
        if os.path.exists(LEARNING_FILE):
            try:
                with open(LEARNING_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(json.dumps({"event": "learning_load_error", "error": str(e)}))
        
        # Inicialização da tabela Q: Armazena o histórico de recompensas por (Estado, Ação)
        q_table = {}
        for asset_class in self.risk_config.keys():
            q_table[asset_class] = {str(action): [] for action in self.actions}
        return q_table

    def _save_learning_data(self):
        """Salva a tabela Q no disco."""
        try:
            with open(LEARNING_FILE, 'w') as f:
                json.dump(self.q_table, f, indent=4)
        except Exception as e:
            logger.error(json.dumps({"event": "learning_save_error", "error": str(e)}))

    def _get_q_value(self, asset_class: str, action: int) -> float:
        """Calcula o valor Q (Média de recompensas) para um (Estado, Ação)."""
        key = str(action)
        rewards = self.q_table.get(asset_class, {}).get(key, [])
        # Limita a memória para ser adaptativo ao *regime atual*
        recent_rewards = rewards[-MAX_MEMORY:] 
        
        if not recent_rewards:
            return 0.0
        return sum(recent_rewards) / len(recent_rewards)

    def report_trade_result(self, asset_class: str, adx_at_entry: float, result_profit_loss: float):
        """
        Recebe o feedback do trade e atualiza a tabela Q.
        """
        current_threshold = self.risk_config[asset_class]['min_adx_threshold']
        reward = 1.0 if result_profit_loss > 0 else -1.0  # Recompensa binária
        
        # Decidimos qual "Ação" esse trade *suportaria*
        if adx_at_entry >= current_threshold + 5:
            effective_action = 0  # Mantivemos o ADX, e funcionou
        elif adx_at_entry < current_threshold:
            effective_action = -1  # Talvez devêssemos ter diminuído o ADX para pegar esse trade (se loss)
        else:
            effective_action = 1  # Talvez devêssemos ter aumentado (se loss)
        
        # Usamos 0 (Manter) como a ação mais provável de ter sido a correta se o trade foi bom
        if reward > 0 and 0 in self.actions:
            self.q_table[asset_class][str(0)].append(reward)
        else:
            # Em caso de perda, penalizamos a ação menos recompensada recentemente
            self.q_table[asset_class][str(effective_action)].append(reward)
            
        self._save_learning_data()
        logger.info(json.dumps({
            "event": "AFR_TRADE_REPORTED",
            "asset_class": asset_class,
            "adx_at_entry": round(adx_at_entry, 1),
            "profit_loss": round(result_profit_loss, 2),
            "reward": reward
        }))

    def get_optimal_adx_adjustment(self, asset_class: str) -> int:
        """
        Calcula o melhor ajuste para o ADX (Melhor Ação) para o próximo ciclo.
        """
        if np.random.rand() < self.epsilon:
            # EXPLORAÇÃO: Escolhe uma ação aleatória
            action = int(np.random.choice(self.actions))
            logger.info(json.dumps({
                "event": "AFR_EXPLORATION",
                "asset_class": asset_class,
                "action": action,
                "message": "Escolhida ação aleatória (exploração)"
            }))
            return action
        else:
            # EXPLOTAÇÃO: Escolhe a ação com o maior Q-Value
            q_values = {action: self._get_q_value(asset_class, action) for action in self.actions}
            optimal_action = max(q_values, key=q_values.get)
            logger.info(json.dumps({
                "event": "AFR_EXPLOITATION",
                "asset_class": asset_class,
                "action": optimal_action,
                "q_value": round(q_values[optimal_action], 2),
                "message": "Escolhida ação ótima (exploração)"
            }))
            return int(optimal_action)
            
    def apply_adjustment(self, asset_class: str):
        """Aplica o ajuste de ADX escolhido na configuração do sistema."""
        adjustment = self.get_optimal_adx_adjustment(asset_class)
        
        current_adx = self.risk_config[asset_class]['min_adx_threshold']
        new_adx = current_adx + adjustment
        
        # Limite mínimo e máximo de ADX para evitar valores absurdos
        new_adx = max(15, min(35, new_adx))
        
        if new_adx != current_adx:
            self.risk_config[asset_class]['min_adx_threshold'] = new_adx
            logger.info(json.dumps({
                "event": "AFR_ADJUSTMENT_APPLIED",
                "asset_class": asset_class,
                "old_adx": current_adx,
                "new_adx": new_adx,
                "adjustment": adjustment
            }))
        
        return self.risk_config

# ==============================================================================
# --- MÓDULO 5: EXECUTOR PRINCIPAL E LOOP DE CONTROLE ---
# ==============================================================================

def get_filling_mode(symbol: str) -> int:
    """Detecta o modo de preenchimento suportado para o símbolo"""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return mt5.ORDER_FILLING_FOK  # Fallback seguro
    
    # Verificar quais modos são suportados
    filling_modes = []
    
    if symbol_info.filling_mode & mt5.SYMBOL_FILLING_FOK:
        filling_modes.append(mt5.ORDER_FILLING_FOK)
    if symbol_info.filling_mode & mt5.SYMBOL_FILLING_IOC:
        filling_modes.append(mt5.ORDER_FILLING_IOC)
    if symbol_info.filling_mode & mt5.SYMBOL_FILLING_RETURN:
        filling_modes.append(mt5.ORDER_FILLING_RETURN)
    
    # Prioridade: FOK > IOC > RETURN
    if mt5.ORDER_FILLING_FOK in filling_modes:
        return mt5.ORDER_FILLING_FOK
    elif mt5.ORDER_FILLING_IOC in filling_modes:
        return mt5.ORDER_FILLING_IOC
    elif mt5.ORDER_FILLING_RETURN in filling_modes:
        return mt5.ORDER_FILLING_RETURN
    else:
        # Fallback: tentar FOK primeiro
        return mt5.ORDER_FILLING_FOK

def execute_trade(signal: dict, account_balance: float, position_manager=None):
    """Executa a ordem no MetaTrader 5."""
    symbol = signal['symbol']
    action = signal['action']
    entry_price = signal['price']
    sl_price = signal['sl']
    tp_price = signal['tp']
    adx_value = signal.get('adx_at_entry', 0.0)  # ADX no momento da entrada
    asset_class = signal.get('asset_class', 'FX_MAJORS')  # Classe do ativo
    
    # 1. Calcular volume (posição adaptativa)
    volume = calculate_position_size(symbol, account_balance, sl_price, entry_price)
    
    if volume <= 0:
        logger.error(json.dumps({"event": "zero_volume", "symbol": symbol, "message": "Volume calculado é zero. Abortando trade."}))
        return

    # 2. Detectar modo de preenchimento correto
    filling_mode = get_filling_mode(symbol)
    
    # 3. Preparar requisição
    trade_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
    trade_action = mt5.TRADE_ACTION_DEAL
    
    request = {
        "action": trade_action,
        "symbol": symbol,
        "volume": volume,
        "type": trade_type,
        "price": entry_price, # Usar preço atual (não limitado)
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 20, # Desvio máximo em pontos
        "magic": 789012,
        "comment": f"Prometheus_v5.1_{action}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode,  # Usar modo detectado automaticamente
    }

    # 4. Enviar ordem
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        ticket = result.order
        logger.info(json.dumps({
            "event": "order_executed",
            "symbol": symbol,
            "action": action,
            "volume": volume,
            "entry_price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "ticket": ticket,
            "filling_mode": filling_mode
        }))
        
        # Registrar posição no PositionManager para rastreamento do AFR
        if position_manager and adx_value > 0:
            position_manager.register_new_position(ticket, symbol, adx_value, asset_class)
    else:
        logger.error(json.dumps({
            "event": "order_failed",
            "symbol": symbol,
            "retcode": result.retcode,
            "comment": result.comment,
            "filling_mode_used": filling_mode
        }))
        
        # Tentar modo alternativo se FOK falhou
        if filling_mode == mt5.ORDER_FILLING_FOK and result.retcode == mt5.TRADE_RETCODE_INVALID_FILL:
            logger.info(json.dumps({
                "event": "retry_with_ioc",
                "symbol": symbol,
                "message": "Tentando IOC como modo alternativo"
            }))
            request["type_filling"] = mt5.ORDER_FILLING_IOC
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                ticket = result.order
                logger.info(json.dumps({
                    "event": "order_executed_retry",
                    "symbol": symbol,
                    "ticket": ticket,
                    "filling_mode": mt5.ORDER_FILLING_IOC
                }))
                # Registrar posição no PositionManager para rastreamento do AFR
                if position_manager and adx_value > 0:
                    position_manager.register_new_position(ticket, symbol, adx_value, asset_class)
            else:
                logger.error(json.dumps({
                    "event": "order_failed_retry",
                    "symbol": symbol,
                    "retcode": result.retcode,
                    "comment": result.comment
                }))

def update_heartbeat():
    """Atualiza o arquivo de heartbeat"""
    try:
        with open(HEARTBEAT_FILE, 'w') as f:
            f.write(str(time.time()))
    except Exception as e:
        logger.error(json.dumps({"event": "heartbeat_update_failed", "error": str(e)}))

def discover_cfd_stocks() -> List[str]:
    """Descobre automaticamente todas as ações (CFD STOCKS) do Market Watch"""
    if not mt5.initialize():
        return []
    
    all_symbols_info = mt5.symbols_get()
    if all_symbols_info is None:
        return []
    
    cfd_stocks = []
    for symbol_info in all_symbols_info:
        symbol = symbol_info.name
        path = symbol_info.path.upper() if hasattr(symbol_info, 'path') else ""
        
        # Identificar stocks/CFD por padrões comuns
        is_stock = (
            "STOCK" in path or 
            "STOCKS" in path or
            "EQUITY" in path or
            "SHARE" in path or
            # Padrões de nomenclatura comuns de stocks
            any(x in symbol.upper() for x in [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", 
                "NFLX", "DIS", "JPM", "V", "MA", "PG", "JNJ", "WMT", 
                "HD", "MCD", "NKE", "SBUX", "COST", "BAC", "GS", "XOM",
                "CVX", "UNH", "ABBV", "PFE", "MRK", "TMO", "ABT", "COST"
            ]) or
            # Padrões como .US, .NASDAQ, .NYSE
            ".US" in symbol.upper() or
            ".NASDAQ" in symbol.upper() or
            ".NYSE" in symbol.upper()
        )
        
        if is_stock:
            cfd_stocks.append(symbol)
    
    logger.info(json.dumps({
        "event": "CFD_STOCKS_DISCOVERED",
        "count": len(cfd_stocks),
        "message": f"{len(cfd_stocks)} ações (CFD STOCKS) descobertas no Market Watch"
    }))
    
    return cfd_stocks

def main_control_loop():
    """Loop principal de execução do Prometheus v5.1."""
    
    # 1. INICIALIZAÇÃO DO MT5
    if not mt5.initialize():
        logger.critical(json.dumps({"event": "mt5_init_failed", "message": "Falha na inicialização do MT5. Verifique a instalação."}))
        return
    
    # 2. DESCOBRIR CFD STOCKS AUTOMATICAMENTE
    cfd_stocks_discovered = discover_cfd_stocks()
    if cfd_stocks_discovered:
        RISK_CONFIG_ASSET_CLASSES["CFD_STOCKS"]["symbols"] = cfd_stocks_discovered
        logger.info(json.dumps({
            "event": "CFD_STOCKS_ADDED",
            "count": len(cfd_stocks_discovered),
            "symbols": cfd_stocks_discovered[:20]  # Log dos primeiros 20
        }))
        
    # 3. DEFINIÇÃO DE ATIVOS A SEREM MONITORADOS (COMBINANDO CLASSES)
    # Lista única de todos os símbolos
    monitoring_symbols = [
        sym for config in RISK_CONFIG_ASSET_CLASSES.values() 
        for sym in config["symbols"]
    ]
    
    # Inicializar o Agente de Reforço Adaptativo (AFR)
    reinforcement_agent = AdaptiveReinforcementAgent(RISK_CONFIG_ASSET_CLASSES)
    
    # Inicializar o Position Manager para gestão de saídas (com referência ao AFR)
    manager = PositionManager(reinforcement_agent=reinforcement_agent)
    
    logger.info(json.dumps({
        "event": "PROMETHEUS_V6_STARTED",
        "monitoring_symbols": len(monitoring_symbols),
        "symbols": monitoring_symbols,
        "frequency": "M5 (5 minutos)",
        "afr_enabled": True,
        "message": "🧠 Sistema v6.0 com Reforço Adaptativo (AFR) ativado"
    }))
    
    # Loop de Execução
    cycle_count = 0
    while True:
        cycle_count += 1
        update_heartbeat()
        
        # 3. OBTENÇÃO DE DADOS DA CONTA
        account_info = mt5.account_info()
        if account_info is None:
            logger.error(json.dumps({"event": "account_info_failed", "message": "Falha ao obter dados da conta."}))
            time.sleep(60)
            continue
            
        balance = account_info.balance
        
        logger.info(json.dumps({
            "event": "PRODUCTION_CYCLE_START",
            "cycle": cycle_count,
            "timestamp": datetime.datetime.now().isoformat(),
            "balance": balance
        }))
        
        # 4. GESTÃO DE POSIÇÕES (PRIMEIRA PRIORIDADE: REDUZIR RISCO)
        manager.manage_open_positions()
        
        # 5. GERAÇÃO DE SINAIS (SEGUNDA PRIORIDADE: ENTRADA)
        positions = mt5.positions_get()
        open_positions_count = len(positions) if positions else 0
        
        logger.info(json.dumps({
            "event": "open_positions_count",
            "count": open_positions_count
        }))

        for symbol in monitoring_symbols:
            # Não abre mais trades se já tiver muitas posições (limite arbitrário para controle)
            if open_positions_count >= 10:
                logger.warning(json.dumps({"event": "max_positions_reached", "count": open_positions_count, "limit": 10}))
                break 

            # Verificar se já há posição aberta para este símbolo (para evitar over-trading)
            if positions and any(pos.symbol == symbol for pos in positions):
                continue

            try:
                # Aplicar ajuste do AFR antes de gerar sinais
                config, asset_class = get_asset_config(symbol)
                reinforcement_agent.apply_adjustment(asset_class)
                
                signal = generate_balanced_signals(symbol)
                
                if signal:
                    logger.info(json.dumps({
                        "event": "valid_signal_generated",
                        "symbol": symbol,
                        "action": signal['action'],
                        "price": signal['price'],
                        "sl": signal['sl'],
                        "tp": signal['tp'],
                        "adx_at_entry": round(signal.get('adx_at_entry', 0), 1),
                        "asset_class": asset_class
                    }))
                    execute_trade(signal, balance, position_manager=manager)
                
            except Exception as e:
                logger.error(json.dumps({
                    "event": "signal_generation_error",
                    "symbol": symbol,
                    "error": str(e)
                }))
                
        # 6. TEMPO DE ESPERA (Rodar a cada 5 minutos, sincronizado com o Timeframe de entrada)
        logger.info(json.dumps({
            "event": "PRODUCTION_CYCLE_COMPLETE",
            "cycle": cycle_count,
            "next_cycle_in": "5 minutos"
        }))
        time.sleep(300) # Espera 5 minutos

if __name__ == '__main__':
    try:
        logger.info(json.dumps({"event": "MASTER_START", "message": "="*80}))
        logger.info(json.dumps({"event": "MASTER_START", "message": "PROMETHEUS v5.1 - MÓDULO DE CONTROLE E EXECUÇÃO"}))
        logger.info(json.dumps({"event": "MASTER_START", "message": "Arquitetura: Popper (Filtros) + Von Neumann (Módulos)"}))
        logger.info(json.dumps({"event": "MASTER_START", "message": "="*80}))
        main_control_loop()
    except KeyboardInterrupt:
        logger.info(json.dumps({"event": "MASTER_SHUTDOWN", "message": "Sistema interrompido pelo usuário."}))
    except Exception as e:
        logger.critical(json.dumps({"event": "FATAL_ERROR", "error": str(e)}))
        import traceback
        logger.critical(json.dumps({"event": "FATAL_ERROR_TRACEBACK", "traceback": traceback.format_exc()}))

