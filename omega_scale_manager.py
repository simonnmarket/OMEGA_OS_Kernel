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
        import omega_regime_detector
        info = mt5.symbol_info(symbol)
        if not info: return False
        
        point = info.point
        price = mt5.symbol_info_tick(symbol).ask if action == 'BUY' else mt5.symbol_info_tick(symbol).bid
        
        # 1. Auditoria de Regime de Mercado (Numeia Safe-Mode Ported)
        regime_detector = omega_regime_detector.MarketRegimeDetector()
        regime_status = regime_detector.detect_regime(symbol)
        
        risk_factor = regime_status.get('risk_factor', 1.0)
        state_log = regime_status.get('state', 'UNKNOWN')
        
        print(f"      [REGIME] {symbol} -> {state_log} | Risk Factor: x{risk_factor} | Vol Z: {regime_status.get('volatility_z')} | ADX: {regime_status.get('adx')}")
        
        # Kelly Criterion Adaptativo (Physics HFT SONAR Inspired)
        # f* = (Edge / Volatilide^2) * Kelly_Fraction
        # Aqui convertemos de forma simples: Confiança da Operação versus a Volatilidade
        # Sem ordem certa do motor ML, usamos 0.50 como Edge standard.
        edge_standard = 0.50 
        vol_penalization = max(1.0, abs(regime_status.get('volatility_z', 0))) 
        
        kelly_fraction = 0.25 # Conservador Institucional 
        kelly_multiplier = (edge_standard / vol_penalization) * kelly_fraction
        
        # Combinar Kelly Fractional com a proteção base de Risco do Numeia
        final_multiplier = risk_factor * max(0.5, min(1.5, kelly_multiplier * 4))
        
        lotes_ajustados = [max(0.01, round(vol * final_multiplier, 2)) for vol in self.lotes_progressivos]
        
        if state_log == "CHAOTIC":
             print(f"      [SAFE-MODE] Mercado Caótico (Vol Z: {vol_penalization:.1f}). Kelly Score e Numeia ativados. Lotes mitigados.")
        
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
            vol = lotes_ajustados[i]
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
                
            # Determinando dinamicamente o Filling Mode suportado pela Corretora (Para evitar bug BTCEUR)
            filling_type = mt5.ORDER_FILLING_FOK # Default
            if info.filling_mode & 1:
                filling_type = mt5.ORDER_FILLING_FOK
            elif info.filling_mode & 2:
                filling_type = mt5.ORDER_FILLING_IOC
            else:
                filling_type = mt5.ORDER_FILLING_RETURN

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
                "type_filling": filling_type,
            }
            
            res = mt5.order_send(request)
            if res.retcode != mt5.TRADE_RETCODE_DONE:
                # Fallback de segurança Hantec
                request["type_filling"] = mt5.ORDER_FILLING_IOC if filling_type == mt5.ORDER_FILLING_FOK else mt5.ORDER_FILLING_RETURN
                res = mt5.order_send(request)
                
            if res.retcode == mt5.TRADE_RETCODE_DONE:
                tickets_abertos.append(res.order)
                print(f"         └─ Lote {i+1}: {vol} vol | SL: {sl_pts}pts | TP: {tp_pts}pts -> TICKET: {res.order}")
            else:
                print(f"         └─ Falha no Lote {i+1}: {res.comment}")
                
        return tickets_abertos
