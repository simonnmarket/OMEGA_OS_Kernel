import time
import psutil
import MetaTrader5 as mt5
import os

LOG_PATH = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\AUDITORIA_HEARTBEAT_LIVE.txt"

def log_status(msg):
    with open(LOG_PATH, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")

log_status("HEARTBEAT MONITOR START (PHASE 5 MASSIVE)")

while True:
    # 1. Check Python Engine
    found = False
    for proc in psutil.process_iter(['name', 'cmdline']):
        if proc.info['name'] == 'python.exe' and '11_live_demo_cycle_1.py' in str(proc.info['cmdline']):
            found = True
            break
    
    # 2. Check MT5 Connection
    if not mt5.initialize():
        log_status("[CRITICAL] MT5 Initialization failed")
    else:
        conn = mt5.terminal_info().connected
        acc = mt5.account_info().balance
        log_status(f"[HEALTH] Engine Alive: {found} | MT5 Connected: {conn} | Balance: {acc}")
        mt5.shutdown()
    
    time.sleep(1800) # Check every 30 mins
