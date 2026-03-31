"""
OMEGA V10.4 OMNIPRESENT - LIVE DEMO ORCHESTRATOR (PHASE 5 - CICLO 1)
====================================================================
Engenharia: PSA / Antigravity | Auditoria Tier-0
Versão: 1.3.0 — VitalSignsMonitor (flatline), Barra M1 fechada, --smoke / --bars

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
from collections import deque
from datetime import datetime
from importlib import import_module

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import psutil


class VitalSignsMonitor:
    """
    Detecção de "Flatline" (Cegueira Estatística).
    Impede que o sistema rode por horas com Z-Score travado em ~0.13.
    Mandato COO / AFC — bloqueio ativo até observabilidade mínima.
    """

    def __init__(self, window_size: int = 20, volatility_floor: float = 0.05) -> None:
        self.z_history: deque[float] = deque(maxlen=window_size)
        self.floor = volatility_floor
        self.alarm_raised = False

    def check_pulse(self, current_z: float) -> None:
        self.z_history.append(abs(float(current_z)))

        if len(self.z_history) == self.z_history.maxlen:
            std_dev = float(np.std(self.z_history))
            if std_dev < self.floor and not self.alarm_raised:
                self.alarm_raised = True
                raise SystemError(
                    "CRITICAL FAILURE: VITAL_SIGNS_FLATLINE.\n"
                    f"Z-Score stuck at ~{float(np.mean(self.z_history)):.3f} for {self.z_history.maxlen} bars.\n"
                    "Variance has collapsed. Check Initialization or Feed."
                )

        if len(self.z_history) >= 2 and float(np.std(self.z_history)) > self.floor:
            self.alarm_raised = False


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
SPAN_WARMUP = 500
LAMBDA = 0.9998
MIN_HOLD = 20
# Paridade RT-B / stress V10.5 SWING (não usar 3.75 aqui)
MIN_Z_ENTRY = 2.0
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
        ry = mt5.copy_rates_from_pos(ASSET_Y, mt5.TIMEFRAME_M1, 1, 20000)
        rx = mt5.copy_rates_from_pos(ASSET_X, mt5.TIMEFRAME_M1, 1, 20000)

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

        vitals = VitalSignsMonitor(window_size=30, volatility_floor=0.05)
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
                
            # Trava Antifraude de MT5 (Atraso de liquidez XAG vs XAU)
            if r1x[0][0] != current_t:
                continue

            last_bar_time = current_t
            start_t = time.perf_counter()

            y_v, x_v = r1y[0][4], r1x[0][4]
            server_dt = datetime.fromtimestamp(current_t)
            wall_dt = datetime.now()
            drift_sec = (wall_dt - server_dt).total_seconds()
            ts_str = server_dt.isoformat()

            s, z, _y_h = self.motor.step(y_v, x_v)
            vitals.check_pulse(z)

            side = "FLAT"
            if z >= MIN_Z_ENTRY:
                side = "SHORT"
            elif z <= -MIN_Z_ENTRY:
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
