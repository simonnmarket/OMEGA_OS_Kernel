import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

class OmegaMacroAgent007:
    """
    Agente 007 (James Bond) - Inteligência Intermarket Institucional.
    Procura anomalias e convergências entre Classes de Ativos (Forex, Metais, Ações, Energia).
    "Licence to Kill" - Pode vetar operações se houver divergência macro grave.
    """
    def __init__(self):
        self.logger = logging.getLogger("Agent_007")
        self.lookback = 48 # Velas de H1 para calcular ciclo (2 dias)
        self.macro_symbols = {
            'US500': 'Risk On/Off (Equities)',
            'XAUUSD': 'Safe Haven / Real Yield Proxy',
            'USOIL+': 'Petro-Currency Driver'
        }
        
        # O que o Agent 007 espera em tempos de NORMALIDADE
        # +1 = movem juntos | -1 = movem no sentido inverso
        self.expected_correlations = {
            ('AUDUSD', 'US500'): 0.70,   # Se Ações sobem, AUD tende a subir
            ('USDCAD', 'USOIL+'): -0.60, # Se Petróleo sobe, USDCAD cai (CAD forte)
            ('USDJPY', 'US500'): 0.60,   # Risco alto = JPY Vendido = USDJPY Sobe
            ('EURUSD', 'XAUUSD'): 0.50,  # EUR e Ouro normalmente movem-se contra o Dólar
            ('USDJPY', 'XAUUSD'): -0.60  # Bond Yield sobe = JPY e Ouro Pressionados
        }

    def fetch_data(self, symbol, timeframe=mt5.TIMEFRAME_H1, count=100) -> pd.DataFrame:
        if not mt5.symbol_select(symbol, True):
            return pd.DataFrame()
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df[['close']]

    def scan_environment(self) -> dict:
        """
        Gera um Dossier de Informações Macro para o Conselho OMEGA
        """
        dossier = {}
        data_cache = {}
        
        # 1. Obter dados dos Majors e Macros
        syms_to_fetch = set([pair[0] for pair in self.expected_correlations.keys()] + list(self.macro_symbols.keys()))
        for sym in syms_to_fetch:
            data_cache[sym] = self.fetch_data(sym, mt5.TIMEFRAME_H1, self.lookback)
            
        print("\n   🕵️‍♂️ [AGENT 007] Intermarket Intelligence Scan...")    
        
        # 2. Analisar as Correlações Reais vs Esperadas
        for (pair, macro), expected in self.expected_correlations.items():
            if data_cache.get(pair).empty or data_cache.get(macro).empty:
                continue
                
            df_pair = data_cache[pair]
            df_macro = data_cache[macro]
            
            # Alinhar os DataFrames por Time (inner join p/ garantir)
            df_merged = pd.merge(df_pair, df_macro, left_index=True, right_index=True, suffixes=('_pair', '_macro'))
            
            if len(df_merged) < self.lookback * 0.5:
                continue
                
            # Calcular Correlação Rolling Pearson dos últimos 48 períodos
            actual_corr = df_merged['close_pair'].corr(df_merged['close_macro'])
            
            # Avaliar Anomalia
            divergence = actual_corr - expected
            
            status = "CONVERGENTE"
            level = "OK"
            
            # Se deviar mais de 0.8 do esperado, é Caos/Anomalia de Liquidez
            if abs(divergence) > 0.8:
                status = "DIVERGÊNCIA INSTITUCIONAL (ANOMALIA)"
                level = "CRITICAL"
            elif abs(divergence) > 0.5:    
                status = "QUEBRA DE CORRELAÇÃO"
                level = "WARNING"
                
            dossier[pair] = {
                'macro_anchor': macro,
                'expected': expected,
                'actual': round(actual_corr, 2),
                'divergence': round(divergence, 2),
                'status': status,
                'level': level
            }
            
            log_c = f"      └─ {pair} vs {macro}: Exp [{expected:.2f}] | Real [{actual_corr:.2f}] -> {status}"
            if level == "CRITICAL":
                print(f"{log_c} 🚨")
            elif level == "WARNING":
                print(f"{log_c} ⚠️")
            else:
                print(f"{log_c} ✅")
                
        # 3. Snapshot Direcional das Macros para Contexto Final
        contextual_bias = {}
        for m_sym, m_desc in self.macro_symbols.items():
            df_m = data_cache.get(m_sym)
            if not df_m.empty:
                ret = (df_m['close'].iloc[-1] / df_m['close'].iloc[0]) - 1
                bias = "BULLISH 📈" if ret > 0 else "BEARISH 📉"
                contextual_bias[m_sym] = f"{m_desc}: {bias} ({ret*100:.2f}%)"
                print(f"      [007 Macro Anchor] {m_sym} -> {contextual_bias[m_sym]}")

        return {'correlations': dossier, 'context': contextual_bias}

    def assess_trade_safety(self, symbol, action, dossier):
        """
        O Agente 007 usa o Dossier para vetar ou dar Green Light a um sinal.
        """
        if symbol not in dossier['correlations']:
            return True, "No Macro Coverage"
            
        data = dossier['correlations'][symbol]
        
        # Se houver divergência Institucional (ex: Petróleo a Desabar mas CAD estranhamente forte)
        if data['level'] == 'CRITICAL':
            return False, f"007 VETO: Mercado Manipulado/Descorrelacionado ({data['macro_anchor']} Anchor)"
            
        # Hardcoded Rules de Ouro da Goldman:
        bias = dossier['context']
        if symbol == 'USDJPY' and action == 'SELL':
            # Se formos vender JPY, mas o US500 (Risco) estiver super Bullish
            # O USDJPY deve subir com apetite ao risco. Vender é lutar contra a maré institucional.
            if 'US500' in bias and 'BULLISH' in bias.get('US500', ''):
                # Mas olhamos para a correlação, se estiver positiva como esperado
                if data['actual'] > 0.4:
                    return False, "007 VETO: Short USDJPY with Risk-ON Macro."
        
        return True, "007 LICENSE GRANTED"

if __name__ == '__main__':
    if mt5.initialize():
        agent = OmegaMacroAgent007()
        dossier = agent.scan_environment()
        
        # Testar Veto
        safe, msg = agent.assess_trade_safety('USDJPY', 'SELL', dossier)
        print(f"\n   [TESTE DE VETO] USDJPY SELL -> {msg}")
        mt5.shutdown()
