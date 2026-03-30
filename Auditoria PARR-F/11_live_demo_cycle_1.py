"""
OMEGA V10.4 OMNIPRESENT - LIVE DEMO ORCHESTRATOR (PHASE 5 - CICLO 1)
====================================================================
Engenharia: PSA / Antigravity | Auditoria Tier-0
Versão: 1.2.0 — Barra M1 fechada (copy_rates_from_pos ... 1, 1), --smoke / --bars

Uso:
  python 11_live_demo_cycle_1.py --smoke
  python 11_live_demo_cycle_1.py
  python 11_live_demo_cycle_1.py --bars 2000
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from datetime import datetime
from importlib import import_module

import MetaTrader5 as mt5
import pandas as pd
import psutil

# PATHS: núcleo + gateway (10_mt5_* em Auditoria PARR-F)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_PATH = os.path.join(BASE_DIR, "omega_core_validation")
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from online_rls_ewma import OnlineRLSEWMACausalZ

gateway_v104 = import_module("10_mt5_gateway_V10_4_OMNIPRESENT")
ExecutionManagerV104 = gateway_v104.ExecutionManagerV104

# CONFIGURAÇÕES CICLO 1
ASSET_Y, ASSET_X = "XAUUSD", "XAGUSD"
PROFILE = "SWING_TRADE"
SPAN_WARMUP = 200
LAMBDA = 0.9998
MIN_HOLD = 20
LOT_SIZE = 0.01

parser = argparse.ArgumentParser(description="Ciclo 1 demo — log SHA3 por linha (G5).")
parser.add_argument("--smoke", action="store_true", help="Executa apenas 10 barras M1 (teste de fumo).")
parser.add_argument("--bars", type=int, default=500, help="Número de barras M1 após warm-up (default 500).")
args = parser.parse_args()

DEMO_LIMIT_BARS = 10 if args.smoke else args.bars
DEMO_DATE = datetime.now().strftime("%Y%m%d")
DEMO_TIME = datetime.now().strftime("%H%M")
EVIDENCIA_DIR = os.path.join(CORE_PATH, f"evidencia_demo_{DEMO_DATE}")
os.makedirs(EVIDENCIA_DIR, exist_ok=True)

# Geração de Nome Único (Evita Sobrescrita Indevida - Aviso PSA)
DEMO_LOG_PATH = os.path.join(EVIDENCIA_DIR, f"DEMO_LOG_{PROFILE}_{DEMO_DATE}_T{DEMO_TIME}.csv")


class OmegaLiveCycle:
    def __init__(self) -> None:
        self.motor = OnlineRLSEWMACausalZ(forgetting=LAMBDA, ewma_span=SPAN_WARMUP)
        self.executor = ExecutionManagerV104(mode="DEMO_LIVE", min_hold_bars=MIN_HOLD)
        self.process = psutil.Process(os.getpid())
        self.bars_processed = 0

    def warm_up(self) -> bool:
        print(f"[*] AQUECENDO MOTOR {PROFILE}...")
        ry = mt5.copy_rates_from_pos(ASSET_Y, mt5.TIMEFRAME_M1, 1, 1000)
        rx = mt5.copy_rates_from_pos(ASSET_X, mt5.TIMEFRAME_M1, 1, 1000)

        if ry is None or rx is None or len(ry) == 0:
            print("[ERRO] Falha no aquecimento (Sem dados MT5). Check Connection.")
            return False

        df_y = pd.DataFrame(ry)
        df_x = pd.DataFrame(rx)
        df = pd.merge(df_y, df_x, on="time", suffixes=("_y", "_x")).sort_values("time")

        for _, row in df.iterrows():
            self.motor.step(row["close_y"], row["close_x"])

        print(f"[OK] Motor aquecido com {len(df)} barras sincronizadas.")
        return True

    def run_cycle(self) -> None:
        if not mt5.initialize():
            print("[ERRO] Falha ao iniciar MT5.")
            return

        if not self.warm_up():
            mt5.shutdown()
            return

        with open(DEMO_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(
                "ts,y,x,spread,z,beta,signal_fired,order_filled,ram_mb,cpu_pct,proc_ms,opp_cost,sha3_256\n"
            )

        print(f"\n[LIVE] CICLO 1 INICIADO (Mode={'SMOKE' if args.smoke else 'CYCLE'})")
        print(f"[*] CONTA: 5100***** | ALVO: {DEMO_LIMIT_BARS} barras")
        print(f"[*] LOG: {DEMO_LOG_PATH}")

        last_bar_time = 0

        while self.bars_processed < DEMO_LIMIT_BARS:
            time.sleep(1)

            # Barra M1 já fechada (pos 1, count 1) — evita duplicar barra em formação
            r1y = mt5.copy_rates_from_pos(ASSET_Y, mt5.TIMEFRAME_M1, 1, 1)
            r1x = mt5.copy_rates_from_pos(ASSET_X, mt5.TIMEFRAME_M1, 1, 1)

            if r1y is None or r1x is None or len(r1y) == 0:
                continue

            current_t = r1y[0][0]
            if current_t == last_bar_time:
                continue

            last_bar_time = current_t
            start_t = time.perf_counter()

            y_v, x_v = r1y[0][4], r1x[0][4]
            server_dt = datetime.fromtimestamp(current_t)
            wall_dt = datetime.now()
            drift_sec = (wall_dt - server_dt).total_seconds()
            ts_str = server_dt.isoformat()

            s, z, _y_h = self.motor.step(y_v, x_v)

            side = "FLAT"
            if z >= 3.75:
                side = "SHORT"
            elif z <= -3.75:
                side = "LONG"

            eng = self.executor.manage(side, y_v, x_v, z, self.bars_processed)

            proc_time = (time.perf_counter() - start_t) * 1000
            ram_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_pct = psutil.cpu_percent()

            beta = self.motor.rls.theta[1]
            log_line = (
                f"{ts_str},{y_v},{x_v},{s:.6f},{z:.4f},{beta:.6f},"
                f"{eng['signal_fired']},{eng['order_filled']},{ram_mb:.1f},{cpu_pct:.1f},"
                f"{proc_time:.3f},{eng['opportunity_cost']:.2f}"
            )
            h = hashlib.sha3_256(log_line.encode("utf-8")).hexdigest()

            with open(DEMO_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"{log_line},{h}\n")

            self.bars_processed += 1
            print(
                f"\r[DEMO] {self.bars_processed}/{DEMO_LIMIT_BARS} | Z: {z:.2f} | Drift: {drift_sec:.0f}s | Spread: {s:.4f}  ",
                end="",
            )

            err = mt5.last_error()
            if err[0] not in (0, 1):
                print(f"\n[CRÍTICO] MT5 Error: {err}")
                break

        print(f"\n[FINISH] CICLO CONCLUÍDO.")
        mt5.shutdown()


if __name__ == "__main__":
    node = OmegaLiveCycle()
    node.run_cycle()
