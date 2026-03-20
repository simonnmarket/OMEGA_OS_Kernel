import asyncio
import time

class MockRedis:
    def __init__(self):
        self.data = {}
        # Simulando uma latência de rede ultrabaixa para o Localhost Redis (10 milissegundos)
        self.latency = 0.01 

    async def set(self, key, value):
        # PONTO CRÍTICO: Aqui o Event Loop do Python troca de contexto (yield control)!
        await asyncio.sleep(self.latency) 
        self.data[key] = value

class FlawedFund:
    """Fundo AMADOR (Sem Locks). Demonstra o erro que o Auditor Red Team provou ser fatal."""
    def __init__(self):
        self.current_equity = 100000.0
        self.redis_conn = MockRedis()

    async def on_trade_closed_flawed(self, pnl: float):
        # 1. Lê estado atual
        temp_equity = self.current_equity
        # 2. Adiciona PnL
        new_equity = temp_equity + pnl
        
        # 3. I\O de Base de dados (AQUI ACONTECE A COLISÃO DE THREADS)
        await self.redis_conn.set("fund", str(new_equity))
        
        # 4. Grava localmente APÓS base de dados
        self.current_equity = new_equity

class Tier0Fund:
    """Fundo TIER-0 (Com Locks Assíncronos). É o código NOVO blindado."""
    def __init__(self):
        self.current_equity = 100000.0
        self.redis_conn = MockRedis()
        self._state_lock = asyncio.Lock() # O ESCUDO

    async def on_trade_closed_tier0(self, pnl: float):
        async with self._state_lock:
            temp_equity = self.current_equity
            new_equity = temp_equity + pnl
            await self.redis_conn.set("fund", str(new_equity))
            self.current_equity = new_equity

async def run_stress_test():
    # Cenário de Alta Frequência (HFT): 50 fechos de Posição em simultâneo (Milissegundo exato).
    # Cada posição traz um Pnl exato de $100.00
    trades_simultaneas = [100.0 for _ in range(50)]
    # Equity Esperado no fim: 100.000 + (50 * 100) = $105.000,00

    print("\n" + "="*70)
    print(" INICIANDO TESTE DE STRESS INSTITUCIONAL: RACE CONDITIONS (50 TRADES)")
    print("="*70)

    # ---------------------------------------------------------
    # 1. O DESASTRE DO CÓDIGO ANTIGO (AMADOR)
    # ---------------------------------------------------------
    amador = FlawedFund()
    tasks_amador = [amador.on_trade_closed_flawed(pnl) for pnl in trades_simultaneas]
    
    t0 = time.perf_counter()
    await asyncio.gather(*tasks_amador)
    t1 = time.perf_counter()

    print(f"\n❌ [CÓDIGO ANTIGO / S-LOCKS]\n   Lucro injetado: +$5000.00")
    print(f"   Capital Mágico Final: ${amador.current_equity:,.2f}  <-- ERRO MATEMÁTICO FATAL")
    if amador.current_equity != 105000:
        perda = 105000 - amador.current_equity
        print(f"   ⚠️ RESULTADO: O Fundo 'estalou' e apagou ${perda:,.2f} de lucro no vazio.")
        print(f"      Motivo: 50 tarefas leram $100.000 ao mesmo tempo. Ninguém guardou a fila.")

    # ---------------------------------------------------------
    # 2. A PERFEIÇÃO DO CÓDIGO TIER-0 (ATUAL)
    # ---------------------------------------------------------
    tier0 = Tier0Fund()
    tasks_tier0 = [tier0.on_trade_closed_tier0(pnl) for pnl in trades_simultaneas]
    
    t2 = time.perf_counter()
    await asyncio.gather(*tasks_tier0)
    t3 = time.perf_counter()

    print(f"\n✅ [OMEGA TIER-0 v3 / C-LOCKS]\n   Lucro injetado: +$5000.00")
    print(f"   Capital Auditado Final: ${tier0.current_equity:,.2f}")
    if tier0.current_equity == 105000:
        print(f"   🛡️ RESULTADO: Matemática inabalável. O Lock barrou fisicamente o 'Double-Spending'.")
        print(f"      Tempo de fila dinâmico gerido harmonicamente: {(t3-t2):.4f} segundos.")
    print("="*70 + "\n")

if __name__ == "__main__":
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_stress_test())
