import MetaTrader5 as mt5

class OmegaScaleManager:
    """
    SISTEMA OMEGA TIER-0: Escalonamento Multi-Timeframe Progressivo (M1/M3)
    Gere lotes dinâmicos (0.01 -> 0.015 -> 0.02) dividindo o SL.
    Este módulo substitui o execute_mt5_order normal para operações de alta confiança.
    """
    def __init__(self, kernel_ref):
        self.kernel = kernel_ref
        self.max_escalonamentos = 3
        self.lotes_progressivos = [0.01, 0.01, 0.02] # Ajustado para MT5 Minimum Lot (0.01 passo)
        
    def execute_progressive_scale(self, symbol, action, base_sl_pts, base_tp_pts):
        """
        Divide a entrada em 3 fragmentos com SL curto para baratear custo e surfar a tendência.
        """
        import MetaTrader5 as mt5
        info = mt5.symbol_info(symbol)
        if not info: return False
        
        point = info.point
        price = mt5.symbol_info_tick(symbol).ask if action == 'BUY' else mt5.symbol_info_tick(symbol).bid
        
        # O Baseline Original mandava Lote 0.04 com SL = 30 pts.
        # Nós vamos mandar 3 lotes:
        # Lote 1: (0.01) SL 10 pts (Stop Curto / Barato)
        # Lote 2: (0.01) SL 15 pts
        # Lote 3: (0.02) SL 25 pts
        
        # A BASE_SL já foi calculada como (ATR * 1.5) no Kernel (Goldman Math).
        # Multiplicamos o Stop para proteger dos ruídos da Hantec Demo e Real.
        sl_distances = [
            base_sl_pts,                   # Lote 1: Stop original (1.5x ATR)
            int(base_sl_pts * 1.25),       # Lote 2: Stop mais largo
            int(base_sl_pts * 1.50)        # Lote 3: Stop Máximo de Defesa
        ]
        
        tp_distances = [
            int(base_tp_pts * 0.5), # Lote 1: TP Curto e rápido (Scalp)
            base_tp_pts,            # Lote 2: TP original (3.0x ATR)
            int(base_tp_pts * 1.5)  # Lote 3: TP para surfar (4.5x ATR)
        ]

        print(f"      [🚀] INICIANDO PROTOCOLO DE ESCALONAMENTO MULTI-TIMEFRAME ({symbol})")
        tickets_abertos = []
        
        for i in range(3):
            vol = self.lotes_progressivos[i]
            sl_pts = sl_distances[i]
            tp_pts = tp_distances[i]
            
            if action == 'BUY':
                sl = price - (sl_pts * point)
                tp = price + (tp_pts * point)
                order_type = mt5.ORDER_TYPE_BUY
            else:
                sl = price + (sl_pts * point)
                tp = price - (tp_pts * point)
                order_type = mt5.ORDER_TYPE_SELL
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": vol,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 999111 + i, # Magicos separados para gestão
                "comment": f"OMEGA_SCALE_{i+1}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            res = mt5.order_send(request)
            if res.retcode != mt5.TRADE_RETCODE_DONE:
                request["type_filling"] = mt5.ORDER_FILLING_RETURN
                res = mt5.order_send(request)
                
            if res.retcode == mt5.TRADE_RETCODE_DONE:
                tickets_abertos.append(res.order)
                print(f"         └─ Lote {i+1}: {vol} vol | SL: {sl_pts}pts | TP: {tp_pts}pts -> TICKET: {res.order}")
            else:
                print(f"         └─ Falha no Lote {i+1}: {res.comment}")
                
        return tickets_abertos
