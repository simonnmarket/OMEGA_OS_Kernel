#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA OS KERNEL - TIER 0
================================================================================
O Cérebro Supremo: Integrador Mestre do BAU_DO_TESOURO (Sistemas Institucionais)
================================================================================
"""

import os
import sys
import json
import time
from pathlib import Path
import importlib.util

# -----------------------------------------------------------------------------
# 1. MAPEAMENTO DE PASTAS (BAU_DO_TESOURO)
# -----------------------------------------------------------------------------
PROJ_PATH = Path(__file__).parent.resolve()
BAU_PATH = Path(r"C:\Users\Lenovo\BAU_DO_TESOURO")

MODULES = {
    "RISK_ENGINE": BAU_PATH / "01_RISK_ENGINE" / "codigo",
    "AGENT_SYSTEM": BAU_PATH / "02_AGENT_SYSTEM" / "agentes",
    "ORCHESTRATOR": BAU_PATH / "03_ORCHESTRATOR",
    "STRATEGIES": BAU_PATH / "04_STRATEGIES",
    "REUSABLE": BAU_PATH / "08_REUSABLE"
}

# Injetar os caminhos no sys.path para importação natural
for name, p in MODULES.items():
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# -----------------------------------------------------------------------------
# 2. CARREGAMENTO DINÂMICO DOS MÓDULOS DE ELITE
# -----------------------------------------------------------------------------
def load_module(name, file_name):
    """Carrega dinamicamente módulos para bypass de cache e controle absoluto"""
    target_path = MODULES[name] / file_name
    if not target_path.exists():
        raise FileNotFoundError(f"[CORE ERROR] Ficheiro crítico não encontrado: {target_path}")
    
    spec = importlib.util.spec_from_file_location(name, str(target_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class OmegaKernel:
    """
    O Kernel OMEGA: Orchestrador global.
    Carrega, Inicializa e Roda os 3 pilares simultaneamente.
    """
    def __init__(self):
        self.print_banner()
        print(">> INICIALIZANDO KERNEL OMEGA TIER-0...")
        
        # Pilares
        self.risk_engine = None
        self.agents = None
        self.orchestrator = None
        self.strategies = {}
        
        self._boot_sequence()

    def print_banner(self):
        print("""
================================================================================
   ██████╗ ███╗   ███╗███████╗ ██████╗  █████╗      ██████╗ ███████╗
  ██╔═══██╗████╗ ████║██╔════╝██╔════╝ ██╔══██╗    ██╔═══██╗██╔════╝
  ██║   ██║██╔████╔██║█████╗  ██║  ███╗███████║    ██║   ██║███████╗
  ██║   ██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║    ██║   ██║╚════██║
  ╚██████╔╝██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║    ╚██████╔╝███████║
   ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝     ╚═════╝ ╚══════╝
================================================================================
          SISTEMA OPERACIONAL INSTÂNCIADO - MODO INSTITUCIONAL
================================================================================
""")

    def _boot_sequence(self):
        # 1. RISK ENGINE
        try:
            print("[1/4] Carregando OMEGA Risk Engine... ", end="")
            risk_mod = load_module("RISK_ENGINE", "risk_engine_v4.0.py")
            # Inicializa a classe RiskEngine (com limite 15% kill switch)
            self.risk_engine = risk_mod.RiskEngine(kill_switch_threshold=0.15)
            print("OK. (Var Paramétrico/MonteCarlo integrados)")
        except Exception as e:
            print(f"FALHA! {e}")
            sys.exit(1)

        # 2. AGENT SYSTEM
        try:
            print("[2/4] Despertando 7 Agentes AI Ollama... ", end="")
            agent_mod = load_module("AGENT_SYSTEM", "aurora_full_power_v4.0.py")
            if not (BAU_PATH / '05_DATABASE').exists():
                (BAU_PATH / '05_DATABASE').mkdir()
            
            db_path = str(BAU_PATH / '05_DATABASE' / 'learning.db')
            self.agents_db = agent_mod.LearningDatabase(db_path=db_path)
            print(f"OK. (Consenso e Veto ativados. Learning DB: {db_path})")
        except Exception as e:
            print(f"AVISO! {e} - Prosseguindo sem agentes locais disponíveis.")

        # 3. ORCHESTRATOR (Prometheus)
        try:
            print("[3/4] Iniciando Position Manager & Filtragem Múltipla... ", end="")
            orch_mod = load_module("ORCHESTRATOR", "prometheus_master_control_v5.1.py")
            self.prometheus_controller = orch_mod
            self.position_manager = orch_mod.PositionManager()
            print("OK. (Trailing Stop e Break-Even ativos)")
        except Exception as e:
            print(f"FALHA! {e}")
            sys.exit(1)

        # 4. STRATEGIES (O Arsenal que acabamos de montar)
        try:
            print("[4/4] Carregando o Arsenal de Estratégias (TIER-0)... ")
            strat_files = [f for f in os.listdir(MODULES["STRATEGIES"]) if f.endswith('.py')]
            for sf in strat_files:
                strat_name = sf.replace('.py', '')
                try:
                    self.strategies[strat_name] = load_module("STRATEGIES", sf)
                    print(f"      [+] {strat_name} carregado com sucesso.")
                except Exception as ex:
                    print(f"      [-] Falha ao carregar {strat_name}: {ex}")
            print("      Carregamento de estratégias concluído.")
        except Exception as e:
            print(f"FALHA! {e}")
            sys.exit(1)
            
        print("\n>> BOOT CONCLUÍDO COM SUCESSO. SISTEMA BLINDADO.\n")

    def execute_mt5_order(self, symbol, action, volume, sl_points, tp_points):
        import MetaTrader5 as mt5
        info = mt5.symbol_info(symbol)
        if not info: return False
        
        point = info.point
        price = mt5.symbol_info_tick(symbol).ask if action == 'BUY' else mt5.symbol_info_tick(symbol).bid
        
        if action == 'BUY':
            sl = price - (sl_points * point)
            tp = price + (tp_points * point)
            order_type = mt5.ORDER_TYPE_BUY
        else:
            sl = price + (sl_points * point)
            tp = price - (tp_points * point)
            order_type = mt5.ORDER_TYPE_SELL
            
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 999111,
            "comment": "OMEGA_LIVE_SIG",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = mt5.order_send(request)
        if res.retcode != mt5.TRADE_RETCODE_DONE:
            request["type_filling"] = mt5.ORDER_FILLING_RETURN
            res = mt5.order_send(request)
            
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"      [$$$] ORDEM REAL EXECUTADA! Ticket: {res.order} | {action} {symbol} @ {price}")
            return True
        else:
            print(f"      [!!!] Falha na execução da ordem: {res.comment} (Code: {res.retcode})")
            return False

    def run_live(self):
        """Loop Principal de Execução em Tempo Real"""
        print("="*60)
        print(" OMEGA KERNEL - INICIANDO EXECUÇÃO LIVE COM METATRADER 5")
        print("="*60)
        
        import MetaTrader5 as mt5
        if not mt5.initialize():
            print("[-] Falha ao inicializar o MetaTrader 5:", mt5.last_error())
            return
            
        print("[*] INICIANDO STRESS TEST: Mapeando múltiplos mercados...")
        all_symbols = mt5.symbols_get()
        if all_symbols:
            # Filtro ávido: Moedas, Cryptos Destaque e Ouros
            ativas = [s.name for s in all_symbols if ('USD' in s.name or 'EUR' in s.name or 'JPY' in s.name or 'BTC' in s.name or 'ETH' in s.name or 'XAU' in s.name)]
            # Retiramos duplicações e limitamos aos 40 ativos mais robustos para não haver 'Rate Limit' imediato do MT5
            ativas = list(set(ativas))[:40]
        else:
            ativas = ["EURUSD", "BTCUSD", "XAUUSD", "USDJPY"]

        symbols_to_trade = []
        print(f"[*] Solicitando acesso da Corretora para {len(ativas)} ativos...")
        for s in ativas:
            if mt5.symbol_select(s, True):
                info = mt5.symbol_info(s)
                if info and info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                    symbols_to_trade.append(s)
                
        if not symbols_to_trade:
             print("[-] Nenhum ativo principal encontrado. Tentando fallback local...")
             symbols_to_trade.append(mt5.symbols_get()[0].name)
             mt5.symbol_select(symbols_to_trade[0], True)
             
        print(f"[+] 🚀 STRESS TEST ONLINE: Motor V8 engrenado em {len(symbols_to_trade)} ativos de forma simultânea!\n")
        
        # Instanciar Estratégias
        print("[+] Conectando Estratégias aos Ativos...")
        strat_instances = []
        for sym in symbols_to_trade:
            if 'gorila_sacramento' in self.strategies:
                strat_instances.append(self.strategies['gorila_sacramento'].GorilaSacramento(symbol=sym))
            if 'vasco_mamede_falha' in self.strategies:
                strat_instances.append(self.strategies['vasco_mamede_falha'].VascoSegundaFalha(symbol=sym))
            if 'nasa_strategy' in self.strategies:
                strat_instances.append(self.strategies['nasa_strategy'].NasaIntegratedStrategy(symbol=sym))
            if 'raiox_waves' in self.strategies:
                strat_instances.append(self.strategies['raiox_waves'].RaioXWaveStrategy(symbol=sym))
            if 'fimathe_core' in self.strategies:
                strat_instances.append(self.strategies['fimathe_core'].FimatheCoreStrategy(symbol=sym))
            if 'pullback_v6' in self.strategies:
                strat_instances.append(self.strategies['pullback_v6'].PullbackDetector(symbol=sym))
        
        cycles = 0
        while True:
            try:
                cycles += 1
                print(f"\n[Ciclo {cycles} - {time.strftime('%H:%M:%S')}] Varredura do Mercado...")
                
                if self.risk_engine:
                    status = self.risk_engine.get_health_status()
                    if status.get('status') != 'OPERATIONAL':
                        print("!!! KILL SWITCH ATIVADO !!! ABORTANDO TRADING !!!")
                        break
                        
                if self.position_manager:
                    # Executa a avaliação em tempo real das posições abertas no MT5
                    # Move para Break-Even ou atualiza o Trailing Stop dinamicamente
                    self.position_manager.manage_open_positions()

                for strat in strat_instances:
                     try:
                         sym = strat.symbol
                         name = strat.__class__.__name__
                         
                         if name == 'GorilaSacramento':
                             sig = strat.run_gorila_analysis()
                             status = sig['status']
                             print(f"   -> [{sym}] [Gorila] Status: {status}")
                             if status != "NO_SIGNAL":
                                 action = "BUY" if "LONG" in status else "SELL"
                                 self.execute_mt5_order(sym, action, 0.01, 150, 300)
                                 
                         elif name == 'VascoSegundaFalha':
                             sig = strat.execute()
                             status = sig['status']
                             print(f"   -> [{sym}] [Vasco] Status: {status}")
                             if status != "NO_SIGNAL":
                                 action = "BUY" if "LONG" in status else "SELL"
                                 self.execute_mt5_order(sym, action, 0.01, 100, 500)
                                 
                         elif name == 'NasaIntegratedStrategy':
                             sig = strat.execute()
                             status = sig['status']
                             print(f"   -> [{sym}] [NASA] Status: {status}")
                             if status != "NO_SIGNAL":
                                 action = "BUY" if "LONG" in status else "SELL"
                                 print(f"      [~] Confiança: {sig.get('confidence', 0):.2f} | Motivo: {sig.get('reasons', '')}")
                                 self.execute_mt5_order(sym, action, 0.01, int(sig.get('atr', 2)*2/0.00001), int(sig.get('atr', 2)*3.5/0.00001))
                                 
                         elif name == 'RaioXWaveStrategy':
                             sig = strat.execute()
                             status = sig['status']
                             print(f"   -> [{sym}] [RaioX] Status: {status}")
                             if status != "NO_SIGNAL":
                                 action = "BUY" if "LONG" in status else "SELL"
                                 print(f"      [~] Onda: {sig.get('wave_type')} | Momentum: {sig.get('momentum'):.5f}")
                                 self.execute_mt5_order(sym, action, 0.01, 120, 350)
                                 
                         elif name == 'FimatheCoreStrategy':
                             sig = strat.execute()
                             status = sig['status']
                             print(f"   -> [{sym}] [Fimathe] Status: {status}")
                             if status != "NO_SIGNAL":
                                 action = "BUY" if "LONG" in status else "SELL"
                                 range_pontos = int(sig.get('canal_range', 0.001) / mt5.symbol_info(sym).point)
                                 print(f"      [~] Canal Range: {range_pontos} pts | ATR Dinâmico: {sig.get('atr', 0):.5f}")
                                 self.execute_mt5_order(sym, action, 0.01, max(30, range_pontos), max(60, range_pontos * 2))

                         elif name == 'PullbackDetector':
                             sig = strat.execute()
                             status = sig['status']
                             print(f"   -> [{sym}] [Pullback] Status: {status}")
                             if status != "NO_SIGNAL":
                                 action = "BUY" if "LONG" in status else "SELL"
                                 print(f"      [~] 🔬 Edge de: {sig.get('confidence',0)*100:.1f}% | Força M15: {sig.get('strength'):.5f}")
                                 atr_pts = int(sig.get('atr', 20) / mt5.symbol_info(sym).point)
                                 self.execute_mt5_order(sym, action, 0.01, max(40, int(atr_pts * 1.5)), max(80, int(atr_pts * 3.5)))

                     except Exception as e:
                         pass # Skip errors on uninitialized ticks
                         
                time.sleep(15)  # Throttle para Live Data
            except KeyboardInterrupt:
                print("\n>> Desligamento seguro iniciado pelo utilizador (SIGINT).")
                mt5.shutdown()
                break
            except Exception as e:
                print(f"\n[ERRO CRITICO] {e} -- Reiniciando o loop...")
                time.sleep(5)

if __name__ == '__main__':
    kernel = OmegaKernel()
    kernel.run_live()
