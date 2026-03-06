import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Import os módulos OMEGA OS Kernel atualizados
from modules.fractal_hurst import FractalEngineV2, FractalConfig, MarketRegime
from modules.volume_physics import VolumePhysicsEngine, PhysicsConfig

def test_live_engines():
    print("=== OMEGA OS KERNEL: LIVE DATA INTEGRATION TEST ===")
    
    if not mt5.initialize():
        print("[-] Falha ao inicializar o MT5. Verifica se está aberto e logado.")
        return

    print(f"[+] MT5 Inicializado. Versão: {mt5.version()}")
    
    # Ativo e Timeframe para teste
    symbol = "EURUSD"
    if not mt5.symbol_select(symbol, True):
        symbols = mt5.symbols_get()
        if symbols:
            symbol = symbols[0].name
            mt5.symbol_select(symbol, True)
            
    print(f"[*] Ativo Selecionado: {symbol}")
    
    # Obter dados OHLCV recentes (ex: M15)
    num_bars = 2000
    print(f"[*] A obter últimas {num_bars} barras M15 para {symbol}...")
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, num_bars)
    
    if rates is None or len(rates) == 0:
        print("[-] Falha ao obter dados.")
        mt5.shutdown()
        return
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f"[+] Obtidas {len(df)} barras com sucesso.")
    print("[-] Iniciando processamento através dos Motores Tier-0...")
    
    # Inicializar os Motores
    fractal_engine = FractalEngineV2(FractalConfig(enable_profiling=True))
    volume_engine = VolumePhysicsEngine(PhysicsConfig(enable_profiling=True))
    
    start_t = time.perf_counter()
    
    # Para o teste ao vivo, simulamos o feed de dados tick a tick / barra a barra
    # Primeiramente aquecemos o Fractal com a série do fecho
    prices = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    volumes = df['tick_volume'].values # Usando tick volume como proxy
    
    print("[*] A calcular Estado Fractal Inicial (Hurst / Regimes)...")
    fractal_state = fractal_engine.analyze_series(prices)
    
    print(f"\n[+] Resultado FractalEngineV2:")
    print(f"    - Hurst Exponent: {fractal_state.hurst_exponent:.4f} (Confiança: {fractal_state.hurst_confidence:.2f})")
    print(f"    - Regime: {fractal_state.regime.name}")
    print(f"    - É Pullback Friendly? {fractal_state.is_pullback_friendly}")
    print(f"    - Estacionário (ADF)? {fractal_state.is_stationary}")
    print(f"    - Dimensão Fractal (Higuchi): {fractal_state.fractal_dimension:.4f}")
    print(f"    - Correlação de Dimensão: {fractal_state.correlation_dimension:.4f}")
    
    print("\n[*] A aquecer VolumePhysicsEngine com série histórica...")
    
    latest_physics_state = None
    for i in range(len(df)):
        # Atualizamos o motor de volume sequencialmente (simulando stream de mercado em tempo real)
        # Injetamos sempre o estado fractal. Num ambiente produtivo real o fractal é calculado a x ticks ou barras.
        latest_physics_state = volume_engine.update(
            close=prices[i],
            high=highs[i],
            low=lows[i],
            volume=volumes[i],
            fractal_state=fractal_state
        )
        
    end_t = time.perf_counter()
    
    print(f"\n[+] Resultado VolumePhysicsEngine (Estado Atual):")
    if latest_physics_state:
        print(f"    - VWAP Atual: {latest_physics_state.vwap:.5f}")
        print(f"    - Z-Score Delta: {latest_physics_state.delta_z:.3f}")
        print(f"    - ATR Comprimido? {latest_physics_state.is_atr_compressed} (Ratio: {latest_physics_state.atr_ratio:.2f})")
        print(f"    - Pico de Volume (Surge)? {latest_physics_state.is_volume_surge}")
        print(f"    - Pullback Phase Ativa: {latest_physics_state.pullback_phase.name}")
        print(f"    - Nível de Urgência: {latest_physics_state.urgency.name}")
        print(f"    - Trap Score: {latest_physics_state.trap_score:.2f}")
    
    print(f"\n[+] Teste Finalizado. Tempo total de processamento: {(end_t - start_t)*1000:.2f} ms")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_live_engines()
