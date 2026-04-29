"""OMEGA FULL AUDIT — Ghost scan + deal history + ordens abertas."""
import MetaTrader5 as mt5
import psutil
import os
import sys
from datetime import datetime, timezone, timedelta

OMEGA_MAGIC = 234001
EXT_MAGIC   = 999111

print("=" * 70)
print("OMEGA FULL AUDIT — %s" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
print("=" * 70)

# ─── 1. GHOST PYTHON PROCESSES ──────────────────────────────────────────────
print("\n[1] PROCESSOS PYTHON EM BACKGROUND:")
current_pid = os.getpid()
omega_keywords = ["shadow_loop", "fase4_wrapper", "omega", "agent_ia", "shadow"]
found_ghosts = []
for proc in psutil.process_iter(["pid", "name", "cmdline", "status"]):
    try:
        if proc.info["pid"] == current_pid:
            continue
        name = (proc.info["name"] or "").lower()
        cmd  = " ".join(proc.info["cmdline"] or []).lower()
        is_python = "python" in name or "python" in cmd
        is_omega  = any(kw in cmd for kw in omega_keywords)
        if is_python:
            mark = "  <<< OMEGA GHOST" if is_omega else ""
            print("  PID=%d [%s] %s%s" % (
                proc.info["pid"], proc.info["status"],
                cmd[:80], mark))
            if is_omega:
                found_ghosts.append(proc.info["pid"])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if found_ghosts:
    print("  GHOST PIDS ENCONTRADOS: %s — TERMINANDO..." % found_ghosts)
    for pid in found_ghosts:
        try:
            p = psutil.Process(pid)
            p.terminate()
            print("  TERMINADO PID=%d" % pid)
        except Exception as e:
            print("  ERRO ao terminar PID=%d: %s" % (pid, e))
else:
    print("  NENHUM processo ghost OMEGA encontrado. LIMPO.")

# ─── 2. MT5 CONTA E POSICOES ─────────────────────────────────────────────────
print("\n[2] CONTA MT5:")
if not mt5.initialize():
    print("  MT5 FAIL:", mt5.last_error())
    sys.exit(1)

acct = mt5.account_info()
print("  Login=%d | Servidor=%s | Balance=%.2f | Equity=%.2f | Moeda=%s" % (
    acct.login, acct.server, acct.balance, acct.equity, acct.currency))

all_pos = mt5.positions_get()
omega_pos = [p for p in (all_pos or []) if p.magic == OMEGA_MAGIC]
ext_pos   = [p for p in (all_pos or []) if p.magic == EXT_MAGIC]
other_pos = [p for p in (all_pos or []) if p.magic not in (OMEGA_MAGIC, EXT_MAGIC)]

print("  Posicoes abertas: total=%d | OMEGA=%d | ExternoEA=%d | Outros=%d" % (
    len(all_pos or []), len(omega_pos), len(ext_pos), len(other_pos)))

for p in omega_pos:
    age = int(datetime.now(timezone.utc).timestamp()) - int(p.time)
    print("  [OMEGA] %s #%d profit=%.4f vol=%.2f age=%ds" % (
        p.symbol, p.ticket, p.profit, p.volume, age))

# ─── 3. HISTORY ORDERS (alternativa a deals) ─────────────────────────────────
print("\n[3] HISTORY ORDERS OMEGA (ultimas 4h):")
now    = datetime.now(timezone.utc)
t_from = now - timedelta(hours=4)

orders = mt5.history_orders_get(t_from, now) or []
omega_ord = [o for o in orders if o.magic == OMEGA_MAGIC]
print("  Total orders 4h: %d | OMEGA: %d" % (len(orders), len(omega_ord)))

by_sym = {}
for o in omega_ord:
    by_sym[o.symbol] = by_sym.get(o.symbol, 0) + 1
    ts = datetime.fromtimestamp(o.time_setup, tz=timezone.utc).strftime("%H:%M:%S")
    state_map = {1:"STARTED",2:"PLACED",3:"CANCELED",4:"PARTIAL",5:"FILLED",6:"REJECTED",7:"EXPIRED"}
    state = state_map.get(o.state, str(o.state))
    print("  [%s] %s #%d state=%s vol=%.2f price=%.5f" % (
        ts, o.symbol, o.ticket, state, o.volume_current, o.price_open))

if by_sym:
    print("  Por simbolo: %s" % by_sym)

# ─── 4. HISTORY DEALS OMEGA ──────────────────────────────────────────────────
print("\n[4] HISTORY DEALS OMEGA (ultimas 4h):")
deals = mt5.history_deals_get(t_from, now) or []
omega_d = [d for d in deals if d.magic == OMEGA_MAGIC]
print("  Total deals 4h: %d | OMEGA: %d" % (len(deals), len(omega_d)))

for d in omega_d[-20:]:
    ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
    entry_map = {0:"IN", 1:"OUT", 2:"INOUT"}
    print("  [%s] %s ticket=%d entry=%s profit=%.4f magic=%d" % (
        ts, d.symbol, d.ticket, entry_map.get(d.entry,"?"), d.profit, d.magic))

# ─── 5. FLOATING P&L ATUAL ───────────────────────────────────────────────────
print("\n[5] P&L FLUTUANTE OMEGA ATUAL:")
total_float = sum(p.profit for p in omega_pos)
print("  Posicoes OMEGA abertas: %d | Float P&L: $%.4f" % (len(omega_pos), total_float))

mt5.shutdown()
print("\n" + "=" * 70)
print("AUDIT COMPLETO.")
print("=" * 70)
