import pandas as pd
import numpy as np
import time
import os

# Dummy import removed
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'OMEGA_INTELLIGENCE_OS'))
# Inline fallback so the POC runs perfectly
class MLAdaptiveBivariateAgent:
        def __init__(self, name):
            self.name = name
            self.learning_rate = 0.05 # Accelerated for visual proof
            self.transition_table = {
                "horizontal_weight": 0.5, 
                "vertical_weight": 0.5,
                "trap_recognition_bias": 0.0
            }
            
        def read_bivariate_tape(self, time_evolution, cost_structure, detected_symbol):
            score = (time_evolution * self.transition_table["horizontal_weight"]) + \
                    (cost_structure * self.transition_table["vertical_weight"]) + \
                    self.transition_table["trap_recognition_bias"]
            return score

        def bivariate_feedback_loop(self, previous_symbol, real_outcome, prediction_error):
            if real_outcome == -1: # Armadilha
                self.transition_table["trap_recognition_bias"] -= self.learning_rate
                self.transition_table["horizontal_weight"] -= (self.learning_rate * 2)
                self.transition_table["vertical_weight"] += self.learning_rate
            elif real_outcome == 1: # Sucesso puro
                self.transition_table["horizontal_weight"] += self.learning_rate
                self.transition_table["trap_recognition_bias"] += (self.learning_rate / 2)

            # Normalize
            total_w = abs(self.transition_table["horizontal_weight"]) + abs(self.transition_table["vertical_weight"])
            if total_w == 0: total_w = 1
            self.transition_table["horizontal_weight"] /= total_w
            self.transition_table["vertical_weight"] /= total_w

def load_history():
    path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M5.csv"
    if not os.path.exists(path): return None
    df = pd.read_csv(path, sep='\t')
    if len(df.columns) < 5: df = pd.read_csv(path)
    col_map = {c: c.lower().replace('<', '').replace('>', '') for c in df.columns}
    df.rename(columns=col_map, inplace=True)
    return df

def run_turing_machine_proof():
    print("="*80)
    print(" 🧠 MÁQUINA DE TURING OMEGA - APRENDIZADO BIVARIADO ATIVO 🧠")
    print(" (Horizontal x Vertical Feedback Loop - XAUUSD M5)")
    print("="*80)
    
    df = load_history()
    if df is None: return
    
    # Processamos os últimos 2000 candles para uma demonstração densa
    df = df.tail(2000).reset_index(drop=True)
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    vols = df['tick_volume'].values if 'tick_volume' in df.columns else df['vol'].values
    
    # Pre-computar Horizontal (Smooth DEMA Momentum) e Vertical (Volume Surge)
    df['line_vector'] = df['close'].ewm(span=14).mean()
    df['momentum_hz'] = df['line_vector'].diff(3) / df['line_vector'].shift(3) * 1000 # Horizontal Acceleration
    df['vol_avg'] = df['tick_volume'].rolling(20).mean() if 'tick_volume' in df.columns else df['vol'].rolling(20).mean()
    df['cost_structure_vt'] = vols / df['vol_avg'] # Vertical Mass Concentration
    df.fillna(0, inplace=True)
    
    hz_array = df['momentum_hz'].values
    vt_array = df['cost_structure_vt'].values
    
    agent = MLAdaptiveBivariateAgent("TURING_READER_01")
    
    trades = 0
    wins = 0
    losses = 0
    
    print("| [*] Iniciando Leitura da Fita...\n")
    
    for i in range(50, len(df) - 10): # -10 para poder olhar o futuro (resultado real)
        hz = hz_array[i]
        vt = vt_array[i]
        
        # Só despertamos o agente quando algo anômalo for gravado na fita
        if abs(hz) > 0.5 and vt > 1.5:
            symbol = "BULL_THRUST" if hz > 0 else "BEAR_THRUST"
            
            # 1. O Agente lê a fita e dá um Score baseado em seus pesos neurais atuais
            score = agent.read_bivariate_tape(hz, vt, symbol)
            
            # Se a convicção do agente for forte, ele aciona o rastro
            if abs(score) > 0.6:
                # 2. Avaliamos a realidade 6 barras no futuro (Cerca de 30 mins)
                future_px = closes[i+6]
                current_px = closes[i]
                
                # Se foi Bull Thrust, o preço subiu?
                if symbol == "BULL_THRUST":
                    real_outcome = 1 if future_px > current_px + 0.5 else -1
                else:
                    real_outcome = 1 if future_px < current_px - 0.5 else -1
                
                prediction_error = abs((future_px - current_px) / current_px)
                
                if real_outcome == 1:
                    wins += 1
                    status = "✅ SUCESSO"
                else:
                    losses += 1
                    status = "❌ ARMADILHA (TRAP)"
                    
                trades += 1
                
                print(f"[BARRA {i}] Símbolo Lido: {symbol} | Score: {score:.2f} | Métrica HZ: {hz:.2f} | Métrica VT: {vt:.2f}")
                print(f" -> Resultado Real: {status}")
                
                # 3. O Feedback do Reforço Positivo/Negativo altera a tabela da Máquina Turing
                agent.bivariate_feedback_loop(symbol, real_outcome, prediction_error)
                print(f" -> Ponderação Aprendida | Horizontal (Tempo): {agent.transition_table['horizontal_weight']:.2f} | Vertical (Custo): {agent.transition_table['vertical_weight']:.2f}")
                print("-" * 60)
                
    print("\n" + "="*80)
    print(" 🏁 RELATÓRIO DO APRENDIZADO DE MÁQUINA BIVARIADO")
    print("="*80)
    print(f"| Entradas Totais Lidas: {trades}")
    win_rate = (wins/trades)*100 if trades > 0 else 0
    print(f"| Taxa de Predição:      {win_rate:.1f}%")
    print(f"| Pesos Neurais Finais:")
    print(f"|  -> Confiança na Horizontal (Momento/Rompimento): {agent.transition_table['horizontal_weight']:.2f}")
    print(f"|  -> Confiança na Vertical (Custo/Volume Profile): {agent.transition_table['vertical_weight']:.2f}")
    print(f"|  -> Ceticismo/Viés de Armadilha de Liquidez:      {agent.transition_table['trap_recognition_bias']:.3f} (Negativo = Medo Intenção Oculta)")
    print("="*80)
    
if __name__ == "__main__":
    run_turing_machine_proof()
