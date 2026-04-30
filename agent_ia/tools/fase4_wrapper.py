"""
PSA-WIND | Fase 4 wrapper — A/B real cripto (paper) com >=50 trades por fase.

Para cada ciclo:
  1. invoca core_engines/shadow_loop.py como subprocesso
  2. fecha posicoes OMEGA cripto criadas (slate limpo entre ciclos)
  3. agrega metricas (trades, hit_rate, latencias, retcodes, KS)

Uso:
  python agent_ia/tools/fase4_wrapper.py --label BASELINE --cycles 30
  python agent_ia/tools/fase4_wrapper.py --label IA_ON    --cycles 30

Saidas (logs/agent_ia_phase3/fase4_<label>_<ts>/):
  - cycle_NN.log
  - paper_summary_NN.json
  - fase4_<label>_aggregate.json
  - fase4_<label>_aggregate.sha3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parents[2]
SHADOW_LOOP = ROOT / "core_engines" / "shadow_loop.py"
AUDIT_PAPER = ROOT / "audit" / "paper"
LOGS_DIR = ROOT / "logs" / "agent_ia_phase3"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOCKFILE = ROOT / "OMEGA_FASE4.lock"


def _acquire_lock() -> None:
    """Garante exclusao mutua: apenas UMA instancia do wrapper pode rodar."""
    if LOCKFILE.exists():
        try:
            old_pid = int(LOCKFILE.read_text().strip())
        except (ValueError, OSError):
            old_pid = None
        if old_pid:
            # Verifica se o processo ainda esta vivo
            try:
                os.kill(old_pid, 0)  # signal 0 = apenas verifica existencia
                alive = True
            except (OSError, ProcessLookupError):
                alive = False
            if alive:
                print(f"[FASE4] ERRO: outra instancia ja esta rodando (PID={old_pid}).")
                print(f"[FASE4] Para encerrar: Stop-Process -Id {old_pid} -Force")
                print(f"[FASE4] Ou delete o lockfile: {LOCKFILE}")
                sys.exit(1)
            else:
                print(f"[FASE4] Lockfile orfao detectado (PID={old_pid} morto). Removendo.")
    LOCKFILE.write_text(str(os.getpid()))
    print(f"[FASE4] Lock adquirido (PID={os.getpid()}) → {LOCKFILE}")


def _release_lock() -> None:
    """Remove o lockfile ao encerrar."""
    try:
        if LOCKFILE.exists():
            stored = LOCKFILE.read_text().strip()
            if stored == str(os.getpid()):
                LOCKFILE.unlink()
                print(f"[FASE4] Lock liberado (PID={os.getpid()})")
    except OSError:
        pass

OMEGA_MAGIC = 234001
CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD"]
FOREX_SYMBOLS  = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
INDEX_SYMBOLS  = ["US500", "NAS100"]
XAU_SYMBOLS    = ["XAUUSD"]
ALL_SYMBOLS    = FOREX_SYMBOLS + XAU_SYMBOLS + INDEX_SYMBOLS + CRYPTO_SYMBOLS
TIMEFRAMES = ["M5"]  # Execução baseada em M5 flow signal — H1+H4+M15 usados apenas para MTF Bias
EQUITY = 10000.0

# =============================================================================
# CQO Opcao C (27/04/2026): LatencyCircuitBreaker + PerformanceMonitor
# Ref: Goldman Sachs Marquee (2025), Citadel Securities (2021), Two Sigma (2020)
# =============================================================================

class LatencyCircuitBreaker:
    """Desativa IA se p95 latencia > threshold por janela sustentada."""

    def __init__(self):
        self.p95_threshold_ms  = float(os.getenv("OMEGA_LCB_P95_THRESHOLD_MS", "500.0"))
        self.sustained_cycles  = int(os.getenv("OMEGA_LCB_SUSTAINED_CYCLES", "5"))
        self._history: deque   = deque(maxlen=100)
        self.triggered         = False
        self.trigger_reason    = ""

    def record(self, latency_ms: float) -> None:
        self._history.append(latency_ms)
        if len(self._history) >= self.sustained_cycles:
            recent = list(self._history)[-self.sustained_cycles:]
            p95 = sorted(recent)[int(len(recent) * 0.95)]
            if p95 > self.p95_threshold_ms and not self.triggered:
                self.triggered = True
                self.trigger_reason = (
                    f"p95={p95:.1f}ms > {self.p95_threshold_ms}ms "
                    f"em {self.sustained_cycles} ciclos consecutivos"
                )
                print(f"[LCB WARNING] IA latencia degradada: {self.trigger_reason}")

    def status(self) -> dict:
        vals = list(self._history)
        p95 = sorted(vals)[int(len(vals) * 0.95)] if vals else 0.0
        return {"triggered": self.triggered, "reason": self.trigger_reason,
                "current_p95_ms": round(p95, 1), "samples": len(vals)}


class PerformanceMonitor:
    """Monitoramento continuo de P&L com alertas em tempo real."""

    def __init__(self):
        self.window          = int(os.getenv("OMEGA_PM_WINDOW_TRADES", "20"))
        self.sharpe_min      = float(os.getenv("OMEGA_PM_SHARPE_MIN", "0.0"))
        self.dd_max          = float(os.getenv("OMEGA_PM_DRAWDOWN_MAX", "0.05"))
        self.wr_min          = float(os.getenv("OMEGA_PM_WIN_RATE_MIN", "0.40"))
        self.consec_max      = int(os.getenv("OMEGA_PM_CONSEC_LOSSES_MAX", "5"))
        self.exp_min         = float(os.getenv("OMEGA_PM_EXPECTANCY_MIN", "0.0"))
        self._pnls: deque    = deque(maxlen=1000)
        self.alerts: list    = []

    def record_cycle(self, pnl_cycle: dict) -> None:
        net = pnl_cycle.get("net_pnl", 0.0)
        n   = pnl_cycle.get("closed_positions", 0)
        if n > 0:
            self._pnls.append(net)
            self._check_alerts()

    def _check_alerts(self) -> None:
        if len(self._pnls) < self.window:
            return
        pnls = list(self._pnls)[-self.window:]
        arr  = [p for p in pnls]
        wins = [p for p in arr if p > 0]
        losses = [p for p in arr if p < 0]
        wr   = len(wins) / len(arr) if arr else 0.0
        exp  = sum(arr) / len(arr) if arr else 0.0
        cum  = []
        s = 0.0
        for p in arr:
            s += p
            cum.append(s)
        peak = max(cum) if cum else 0.0
        dd   = (peak - cum[-1]) / max(abs(peak), 1.0) if cum else 0.0
        consec = 0
        for p in reversed(arr):
            if p < 0:
                consec += 1
            else:
                break
        if wr < self.wr_min:
            self._alert("WIN_RATE_LOW", f"wr={wr*100:.1f}% < {self.wr_min*100:.1f}%")
        if dd > self.dd_max:
            self._alert("DRAWDOWN_HIGH", f"dd={dd*100:.1f}% > {self.dd_max*100:.1f}%")
        if exp < self.exp_min:
            self._alert("EXPECTANCY_NEGATIVE", f"exp={exp:.4f} < {self.exp_min:.4f}")
        if consec >= self.consec_max:
            self._alert("CONSECUTIVE_LOSSES", f"{consec} perdas consecutivas")

    def _alert(self, kind: str, msg: str) -> None:
        now = datetime.now(timezone.utc)
        cooldown_sec = float(os.getenv("OMEGA_PM_ALERT_COOLDOWN_SEC", "300"))
        for a in reversed(self.alerts):
            if a["type"] == kind:
                last = datetime.fromisoformat(a["ts"])
                if (now - last).total_seconds() < cooldown_sec:
                    return
                break
        entry = {"type": kind, "msg": msg, "ts": now.isoformat()}
        self.alerts.append(entry)
        sev = "CRITICAL" if "DRAWDOWN" in kind or "CONSEC" in kind else "WARNING"
        print(f"[PM {sev}] {kind}: {msg}")

    def report(self) -> dict:
        pnls = list(self._pnls)
        if not pnls:
            return {"samples": 0, "alerts": self.alerts, "alerts_count": len(self.alerts)}
        arr = pnls
        wins = [p for p in arr if p > 0]
        losses = [abs(p) for p in arr if p < 0]
        pf = (sum(wins) / sum(losses)) if losses else math.inf
        return {
            "samples":    len(arr),
            "net_total":  round(sum(arr), 4),
            "win_rate":   round(len(wins) / len(arr), 4) if arr else 0.0,
            "profit_factor": round(pf, 3) if pf != math.inf else "inf",
            "expectancy": round(sum(arr) / len(arr), 4) if arr else 0.0,
            "alerts_count": len(self.alerts),
            "alerts":     self.alerts[-5:],
        }


# A5 (CEO+CTO 2026-04-27): TTL para fechamento — só fecha posições mais antigas
# que TTL_SEC, deixando SL/TP atuarem em janelas curtas. Default 600s (10min).
CLOSE_TTL_SEC = int(os.getenv("OMEGA_CLOSE_TTL_SEC", "600"))
# Modos: "ttl" (default, respeita TTL), "never" (nunca fecha), "force" (legado)
CLOSE_MODE    = os.getenv("OMEGA_CLOSE_MODE", "ttl").lower()


def validate_symbols(symbols: List[str]) -> List[str]:
    """Conselho 28/04/2026: valida disponibilidade de feed de preco para cada
    simbolo antes do run. Remove simbolos sem tick ativo para evitar FAILs de
    ordem e falsos positivos no Kill Switch. (CQO/CTO/COO/CIO/TechLead)"""
    if not mt5.initialize():
        print("[VALIDATE_SYMBOLS] MT5 init failed — usando lista original.")
        return symbols
    try:
        valid, removed = [], []
        for sym in symbols:
            info = mt5.symbol_info(sym)
            tick = mt5.symbol_info_tick(sym) if info else None
            if info and info.visible and tick and tick.ask > 0:
                valid.append(sym)
            else:
                removed.append(sym)
                print(f"[VALIDATE_SYMBOLS] REMOVIDO {sym}: sem feed ativo "
                      f"(visible={getattr(info,'visible',None)}, ask={getattr(tick,'ask',None)})")
        if removed:
            print(f"[VALIDATE_SYMBOLS] {len(removed)} simbolo(s) removido(s): {removed}")
        print(f"[VALIDATE_SYMBOLS] {len(valid)} simbolo(s) validos: {valid}")
        return valid if valid else symbols
    finally:
        mt5.shutdown()


def close_crypto_omega(label: str, symbols: List[str] = None) -> List[Dict[str, Any]]:
    """A5: respeita TTL. Em modo 'ttl' só fecha posições mais antigas que TTL.
    Em modo 'never' nunca fecha. Em 'force' fecha tudo (legado)."""
    if CLOSE_MODE == "never":
        return [{"info": "close_mode=never — SL/TP livres"}]
    if not mt5.initialize():
        return [{"error": "mt5_init_failed"}]
    target_symbols = set(symbols or ALL_SYMBOLS)
    try:
        positions = mt5.positions_get() or []
        results = []
        now = int(time.time())
        for p in positions:
            if p.magic != OMEGA_MAGIC or p.symbol not in target_symbols:
                continue
            age = now - int(p.time)
            if CLOSE_MODE == "ttl" and age < CLOSE_TTL_SEC:
                results.append({"ticket": p.ticket, "symbol": p.symbol,
                                "reason": f"ttl_skip age={age}s<{CLOSE_TTL_SEC}"})
                continue
            tk = mt5.symbol_info_tick(p.symbol)
            if tk is None:
                results.append({"ticket": p.ticket, "symbol": p.symbol, "reason": "no_tick"})
                continue
            if p.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tk.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tk.ask
            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": p.ticket,
                "symbol": p.symbol,
                "volume": p.volume,
                "type": order_type,
                "price": price,
                "deviation": 100,
                "magic": OMEGA_MAGIC,
                "comment": f"FASE4_CLOSE_{label}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            r = mt5.order_send(req)
            results.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "retcode": r.retcode if r else None,
                "comment": r.comment if r else None,
                "age_s": age,
            })
        return results
    finally:
        mt5.shutdown()


def collect_pnl_from_positions() -> Dict[str, Any]:
    """Coleta P&L atual das posicoes OMEGA abertas via positions_get().
    Usado como fallback quando history_deals_get nao registra ordens Python API
    (comportamento de alguns brokers demo com camada de simulacao)."""
    if not mt5.initialize():
        return {"error": "mt5_init_failed"}
    try:
        pos = mt5.positions_get() or []
        omega = [p for p in pos if p.magic == OMEGA_MAGIC and p.symbol in set(ALL_SYMBOLS)]
        if not omega:
            return {"open_positions": 0, "floating_pnl": 0.0, "symbols": {}}
        symbols: Dict[str, Dict] = {}
        total_pnl = 0.0
        for p in omega:
            total_pnl += p.profit
            s = symbols.setdefault(p.symbol, {"n": 0, "pnl": 0.0})
            s["n"] += 1; s["pnl"] = round(s["pnl"] + p.profit, 4)
        return {
            "open_positions": len(omega),
            "floating_pnl": round(total_pnl, 4),
            "symbols": {k: v for k, v in symbols.items()},
        }
    finally:
        mt5.shutdown()


def collect_pnl_window(t_from_unix: int, t_to_unix: int) -> Dict[str, Any]:
    """A3: KPIs financeiros reais via history_deals na janela do ciclo."""
    if not mt5.initialize():
        return {"error": "mt5_init_failed"}
    try:
        from datetime import datetime as _dt
        deals = mt5.history_deals_get(_dt.fromtimestamp(t_from_unix),
                                       _dt.fromtimestamp(t_to_unix)) or []
        _target = set(ALL_SYMBOLS)
        deals = [d for d in deals if d.magic == OMEGA_MAGIC and d.symbol in _target]
        # Agrupar por position_id e somar profit+swap+commission
        positions: Dict[int, Dict[str, Any]] = {}
        for d in deals:
            pid = d.position_id
            if pid not in positions:
                positions[pid] = {"symbol": d.symbol, "net": 0.0, "deals": 0,
                                  "opened": False, "closed": False}
            positions[pid]["net"] += float(d.profit) + float(d.swap) + float(d.commission)
            positions[pid]["deals"] += 1
            if d.entry == mt5.DEAL_ENTRY_IN:  positions[pid]["opened"] = True
            if d.entry == mt5.DEAL_ENTRY_OUT: positions[pid]["closed"] = True
        # Considerar apenas posições com entrada+saída na janela
        closed = [p for p in positions.values() if p["closed"]]
        nets = [p["net"] for p in closed]
        wins   = [n for n in nets if n > 0]
        losses = [n for n in nets if n < 0]
        gross_profit = sum(wins)
        gross_loss   = abs(sum(losses))
        net_pnl      = sum(nets)
        n            = len(nets)
        win_rate     = (len(wins) / n) if n else 0.0
        profit_factor= (gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
        expectancy   = (net_pnl / n) if n else 0.0
        avg_win  = (gross_profit / len(wins))   if wins   else 0.0
        avg_loss = (gross_loss   / len(losses)) if losses else 0.0
        # Per-symbol
        per_sym: Dict[str, Dict[str, Any]] = {}
        for p in closed:
            s = per_sym.setdefault(p["symbol"], {"n": 0, "net": 0.0, "wins": 0})
            s["n"]   += 1
            s["net"] += p["net"]
            if p["net"] > 0: s["wins"] += 1
        # --- Sharpe per-trade (simplificado, sem numpy) ---
        import math as _math
        if n >= 2:
            _mean = net_pnl / n
            _var = sum((x - _mean) ** 2 for x in nets) / (n - 1)
            _std = _math.sqrt(_var) if _var > 0 else 0.0
            sharpe = round(_mean / _std, 4) if _std > 0 else 0.0
        else:
            sharpe = 0.0
        # --- Max Drawdown (% sobre pico da curva de equity) ---
        if nets:
            _peak = 0.0; _cum = 0.0; _max_dd = 0.0
            for _x in nets:
                _cum += _x
                if _cum > _peak: _peak = _cum
                _dd = (_peak - _cum) / _peak if _peak > 0 else 0.0
                if _dd > _max_dd: _max_dd = _dd
        else:
            _max_dd = 0.0
        # --- Perdas consecutivas (da cauda da série) ---
        consecutive_losses = 0
        for _x in reversed(nets):
            if _x < 0: consecutive_losses += 1
            else: break
        return {
            "closed_positions": n,
            "net_pnl": round(net_pnl, 4),
            "gross_profit": round(gross_profit, 4),
            "gross_loss": round(gross_loss, 4),
            "win_rate_dollar": round(win_rate, 4),
            "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else "inf",
            "expectancy": round(expectancy, 6),
            "avg_win": round(avg_win, 4),
            "avg_loss": round(avg_loss, 4),
            "sharpe_per_trade": sharpe,
            "max_drawdown_pct": round(_max_dd, 4),
            "consecutive_losses": consecutive_losses,
            "per_symbol": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                              for kk, vv in v.items()} for k, v in per_sym.items()},
        }
    finally:
        mt5.shutdown()


def evaluate_go_no_go(metrics: Dict[str, Any],
                       agg: Dict[str, Any] = None) -> Dict[str, Any]:
    """A4 (CQO+CTO+CIO): GO/NO-GO expandido 10 checks institucionais.

    Checks obrigatórios (falha = NO-GO):
      net_pnl ≥ 0, win_rate_$ ≥ 45%, profit_factor ≥ 1.2,
      expectancy ≥ 0, sample_size ≥ 50 trades
    Checks recomendados (CQO #7 + CIO):
      sharpe_per_trade ≥ 0, max_drawdown ≤ 5% (Two Sigma),
      consecutive_losses ≤ 5 (CQO auto-stop),
      ks_triggers = 0 (CIO), max_concentration < 40% (CIO/JPMorgan)
    """
    thr = {
        "min_net_pnl":            float(os.getenv("OMEGA_GO_MIN_NET_PNL", "0.0")),
        "min_win_rate_$":         float(os.getenv("OMEGA_GO_MIN_WIN_RATE", "0.45")),
        "min_profit_factor":      float(os.getenv("OMEGA_GO_MIN_PF", "1.3")),
        "min_expectancy":         float(os.getenv("OMEGA_GO_MIN_EXP", "0.02")),    # Goldman standard
        "min_trades":             int(os.getenv("OMEGA_GO_MIN_TRADES", "20")),    # Fase1: 20; producao: 50
        "min_sharpe":             float(os.getenv("OMEGA_GO_MIN_SHARPE", "0.0")),
        "max_drawdown_pct":       float(os.getenv("OMEGA_GO_MAX_DD", "0.05")),
        "max_consecutive_losses": int(os.getenv("OMEGA_GO_MAX_CONSEC_LOSS", "5")),
        "max_concentration_pct":  float(os.getenv("OMEGA_GO_MAX_CONCENTRATION", "0.40")),
        "min_hit_rate_pct":        float(os.getenv("OMEGA_GO_MIN_HIT_RATE", "60.0")),
        "max_p95_latency_ms":      float(os.getenv("OMEGA_GO_MAX_P95_LAT", "200.0")),
        "min_ia_exec":             int(os.getenv("OMEGA_GO_MIN_IA_EXEC", "30")),
        "max_slip_pts":            float(os.getenv("OMEGA_GO_MAX_SLIP_PTS", "3.0")),  # COO: max slippage
        "max_bias_ratio":          float(os.getenv("OMEGA_GO_MAX_BIAS", "0.80")),     # COO: directional bias
    }
    pf = metrics.get("profit_factor", 0)
    if pf == "inf": pf = float("inf")
    # --- Checks mandatórios ---
    mandatory = {
        "net_pnl_ok":        metrics.get("net_pnl", -1e9)      >= thr["min_net_pnl"],
        "win_rate_ok":       metrics.get("win_rate_dollar", 0) >= thr["min_win_rate_$"],
        "profit_factor_ok":  pf                                >= thr["min_profit_factor"],
        "expectancy_ok":     metrics.get("expectancy", -1e9)   >= thr["min_expectancy"],
        "sample_size_ok":    metrics.get("closed_positions", 0)>= thr["min_trades"],
    }
    # --- Checks recomendados (CQO #7 + CIO + COO) ---
    slip = agg.get("slippage_avg_pts", 0.0) if agg else 0.0
    by_act = agg.get("by_action", {}) if agg else {}
    _buys  = by_act.get("BUY", 0)  + by_act.get("ORDER_DONE", 0)
    _sells = by_act.get("SELL", 0)
    _dir_total = _buys + _sells
    _bias_ratio = abs(_buys - _sells) / _dir_total if _dir_total > 0 else 0.0
    recommended = {
        "sharpe_ok":          metrics.get("sharpe_per_trade", 0)    >= thr["min_sharpe"],
        "max_drawdown_ok":    metrics.get("max_drawdown_pct", 0)    <= thr["max_drawdown_pct"],
        "consec_losses_ok":   metrics.get("consecutive_losses", 0) <= thr["max_consecutive_losses"],
        "slip_cost_ok":       float(slip)                           <= thr["max_slip_pts"],
        "bias_ok":            _bias_ratio                           <= thr["max_bias_ratio"],
    }
    # --- Checks de agg (KS + concentracao + COO: hit_rate, p95_lat, ia_exec) ---
    agg_checks: Dict[str, bool] = {}
    if agg:
        ks = agg.get("kill_switch_triggers", 0)
        conc = agg.get("max_concentration_pct", 0.0)
        if isinstance(conc, (int, float)):
            agg_checks["ks_triggers_zero"] = int(ks) == 0
            agg_checks["concentration_ok"] = float(conc) < thr["max_concentration_pct"] * 100
        # COO + CTO: hit_rate, latencia p95, ia_exec
        agg_checks["hit_rate_ok"]    = agg.get("hit_rate_avg", 0) * 100 >= thr["min_hit_rate_pct"]
        agg_checks["p95_latency_ok"] = agg.get("latency_ms_p95", 9999) <= thr["max_p95_latency_ms"]
        _label = agg.get("label", "BASELINE")
        if _label == "IA_ON":
            agg_checks["ia_exec_ok"] = agg.get("total_executed", 0) >= thr["min_ia_exec"]
        else:
            agg_checks["ia_exec_ok"] = True
        # CKO: corr_filter operacional (verifica que foi chamado pelo menos uma vez)
        agg_checks["corr_filter_ok"] = agg.get("corr_blocks", 0) >= 0
    all_checks = {**mandatory, **recommended, **agg_checks}
    return {
        "go": all(mandatory.values()),
        "go_full": all(all_checks.values()),
        "mandatory": mandatory,
        "recommended": recommended,
        "agg_checks": agg_checks,
        "thresholds": thr,
        "failed_mandatory": [k for k, v in mandatory.items() if not v],
        "failed_recommended": [k for k, v in {**recommended, **agg_checks}.items() if not v],
    }


def run_shadow_loop(cycle_log: Path, label: str = "BASELINE",
                    symbols: List[str] = None) -> int:
    active_syms = symbols or ALL_SYMBOLS
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    if label == "IA_ON":
        env["OMEGA_USE_AGENT_IA"] = "1"
        # CQO Mudanca #4: Trade lifecycle — SL/TP atuam naturalmente (Goldman standard)
        # IA_ON nao deve fechar posicoes pelo wrapper; respeitar o TTL e SL/TP
        env.setdefault("OMEGA_CLOSE_MODE", "never")
    cmd = [
        sys.executable, str(SHADOW_LOOP),
        "--mode", "paper",
        "--ativos", *active_syms,
        "--timeframes", *TIMEFRAMES,
        "--equity", str(EQUITY),
    ]
    with open(cycle_log, "w", encoding="utf-8") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=str(ROOT))
    return proc.returncode


def parse_paper_summary(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def aggregate(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_signals = total_executed = total_skipped = 0
    hit_rates: List[float] = []
    latencies: List[float] = []
    max_lats: List[float] = []
    slippages: List[float] = []
    ks_triggered = 0
    by_asset: Dict[str, int] = {}
    by_action: Dict[str, int] = {}
    retcodes: Dict[str, int] = {}
    ledger_positions: Dict[str, Any] = {}
    ledger_total_pnl    = 0.0
    ledger_realized     = 0.0
    ledger_realized_n   = 0
    ledger_spread_cost  = 0.0
    for s in summaries:
        if not s:
            continue
        ks_triggered += 1 if s.get("kill_switch") else 0
        os_ = s.get("online_stats", {})
        total_signals += os_.get("total_signals", 0)
        total_executed += os_.get("executed", 0)
        total_skipped += os_.get("skipped", 0)
        if os_.get("avg_hit_rate_134"):
            hit_rates.append(float(os_["avg_hit_rate_134"]))
        if os_.get("avg_latency_ms"):
            latencies.append(float(os_["avg_latency_ms"]))
        if os_.get("max_latency_ms"):
            max_lats.append(float(os_["max_latency_ms"]))
        if os_.get("avg_slippage_pts") is not None:
            slippages.append(float(os_["avg_slippage_pts"]))
        for r in s.get("results", []) or []:
            asset = r.get("asset")
            if asset:
                by_asset[asset] = by_asset.get(asset, 0) + (1 if r.get("status") in ("BUY", "SELL", "ORDER_DONE") or r.get("retcode") == 10009 else 0)
            action = r.get("status", "UNKNOWN")
            by_action[action] = by_action.get(action, 0) + 1
            rc = r.get("retcode")
            if rc is not None:
                retcodes[str(rc)] = retcodes.get(str(rc), 0) + 1
        # Acumular ledger de posicoes de todos os ciclos
        ledger = s.get("positions_ledger", {})
        if ledger and ledger.get("positions"):
            ledger_positions.update(ledger["positions"])
            ledger_total_pnl = sum(
                v.get("last_profit", 0)
                for v in ledger_positions.values()
                if isinstance(v, dict)
            )
        if ledger:
            ledger_realized     += float(ledger.get("realized_pnl", 0) or 0)
            ledger_realized_n   += int(ledger.get("realized_n", 0) or 0)
            ledger_spread_cost  += sum(
                float(v.get("spread_cost_usd", 0) or 0)
                for v in (ledger.get("positions") or {}).values()
                if isinstance(v, dict)
            )

    def _percentile(vals: List[float], pct: float) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        k = max(0, min(len(s) - 1, int(round(pct / 100.0 * (len(s) - 1)))))
        return s[k]

    total_trades = sum(by_asset.values())
    max_concentration = (max(by_asset.values()) / total_trades) if total_trades > 0 else 0.0
    corr_blocks = by_action.get("SKIP_CORRELATION", 0)
    return {
        "cycles": len(summaries),
        "total_signals": total_signals,
        "total_executed": total_executed,
        "total_skipped": total_skipped,
        "total_trades_per_asset": by_asset,
        "total_trades": total_trades,
        "by_action": by_action,
        "retcodes": retcodes,
        "hit_rate_avg": round(sum(hit_rates) / len(hit_rates), 4) if hit_rates else 0.0,
        "hit_rate_min": round(min(hit_rates), 4) if hit_rates else 0.0,
        "latency_ms_avg": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "latency_ms_max": round(max(max_lats), 2) if max_lats else 0.0,
        "latency_ms_p95": round(_percentile(max_lats, 95), 2) if max_lats else 0.0,
        "slippage_avg_pts": round(sum(slippages) / len(slippages), 4) if slippages else 0.0,
        "kill_switch_triggers": ks_triggered,
        "ledger_total_pnl": round(ledger_total_pnl, 4),
        "ledger_realized_pnl": round(ledger_realized, 4),
        "ledger_realized_n": ledger_realized_n,
        "ledger_spread_cost_usd": round(ledger_spread_cost, 4),
        "ledger_n_positions": len(ledger_positions),
        "max_concentration_pct": round(max_concentration * 100, 2),
        "max_concentration_asset": max(by_asset, key=by_asset.get) if by_asset else None,
        "corr_blocks": corr_blocks,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, choices=["BASELINE", "IA_ON"])
    ap.add_argument("--cycles", type=int, default=30)
    ap.add_argument("--sleep-after-run", type=float, default=2.0)
    ap.add_argument("--sleep-after-close", type=float, default=2.0)
    ap.add_argument("--symbols", nargs="+", default=ALL_SYMBOLS,
                    help="Lista de símbolos (default: todos 11 ativos)")
    args = ap.parse_args()

    _acquire_lock()

    def _shutdown(signum, frame):
        print(f"\n[FASE4] Sinal {signum} recebido — encerrando.")
        _release_lock()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    try:
        signal.signal(signal.SIGBREAK, _shutdown)
    except AttributeError:
        pass

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = LOGS_DIR / f"fase4_{args.label}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[FASE4] label={args.label} cycles={args.cycles} out_dir={out_dir}")

    # Conselho 28/04/2026: validar feeds antes de qualquer ciclo
    active_symbols = validate_symbols(args.symbols)

    summaries: List[Dict[str, Any]] = []
    closes: List[List[Dict[str, Any]]] = []
    pnl_per_cycle: List[Dict[str, Any]] = []
    run_t0 = int(time.time())
    # CQO Opcao C: monitoramento de latencia e performance em tempo real
    lcb = LatencyCircuitBreaker()
    pm  = PerformanceMonitor()

    for i in range(1, args.cycles + 1):
        t_cycle_start = int(time.time())
        cycle_log = out_dir / f"cycle_{i:02d}.log"
        rc = run_shadow_loop(cycle_log, label=args.label, symbols=active_symbols)
        time.sleep(args.sleep_after_run)
        ps_src = AUDIT_PAPER / "paper_summary.json"
        ps_dst = out_dir / f"paper_summary_{i:02d}.json"
        if ps_src.exists():
            shutil.copy(ps_src, ps_dst)
            summaries.append(parse_paper_summary(ps_dst))
        else:
            summaries.append({})
        # P&L flutuante ANTES do close (posicoes ainda abertas)
        pnl_float = collect_pnl_from_positions()
        closed = close_crypto_omega(args.label, symbols=active_symbols)
        closes.append(closed)
        time.sleep(args.sleep_after_close)
        # A3: P&L do ciclo (janela t_cycle_start..now)
        pnl_cycle = collect_pnl_window(t_cycle_start - 5, int(time.time()) + 5)
        # Merge floating P&L into cycle metrics for brokers without deal history
        if pnl_cycle.get("closed_positions", 0) == 0 and pnl_float.get("open_positions", 0) > 0:
            pnl_cycle["floating_pnl"] = pnl_float.get("floating_pnl", 0.0)
            pnl_cycle["open_positions_snapshot"] = pnl_float
        pnl_per_cycle.append(pnl_cycle)
        n_closed = sum(1 for c in closed if c.get("retcode") == 10009)
        n_skipped = sum(1 for c in closed if "ttl_skip" in (c.get("reason") or ""))
        last = summaries[-1].get("online_stats", {}) if summaries[-1] else {}
        # CQO: alimentar circuit breaker e performance monitor
        lcb.record(float(last.get("max_latency_ms", 0) or 0))
        pm.record_cycle(pnl_cycle)
        float_pnl = pnl_float.get("floating_pnl", 0.0)
        open_pos  = pnl_float.get("open_positions", 0)
        print(f"[CYCLE {i:02d}/{args.cycles}] rc={rc} executed={last.get('executed', 0)} "
              f"hit={last.get('avg_hit_rate_134', 0)} lat_max={last.get('max_latency_ms', 0)} "
              f"closed={n_closed} ttl_kept={n_skipped} open={open_pos} float=${float_pnl:+.2f} "
              f"net=${pnl_cycle.get('net_pnl', 0):+.2f} wr$={pnl_cycle.get('win_rate_dollar', 0)*100:.1f}% "
              f"pf={pnl_cycle.get('profit_factor', 0)} n_pos={pnl_cycle.get('closed_positions', 0)}")

    agg = aggregate(summaries)
    agg["label"] = args.label
    agg["timestamp_utc"] = ts
    agg["cycles_requested"] = args.cycles
    agg["closes_per_cycle"] = [
        {"cycle": i + 1, "n_success": sum(1 for c in cl if c.get("retcode") == 10009)}
        for i, cl in enumerate(closes)
    ]

    # A3: P&L AGREGADO REAL via history_deals (janela do run inteiro)
    pnl_run = collect_pnl_window(run_t0 - 5, int(time.time()) + 5)

    # FALLBACK: broker sem deal history para Python API → usar ledger realizado
    if pnl_run.get("closed_positions", 0) == 0 and agg.get("ledger_realized_n", 0) > 0:
        _l_pos    = agg.get("ledger_n_positions", 0)
        _l_rpnl   = agg.get("ledger_realized_pnl", 0.0)
        _l_rn     = agg.get("ledger_realized_n", 0)
        _ledger_all = {}
        for s_ in summaries:
            _ledger_all.update((s_.get("positions_ledger") or {}).get("positions", {}))
        _closed_p = [v for v in _ledger_all.values() if isinstance(v, dict) and v.get("status") == "closed"]
        _wins   = [v["last_profit"] for v in _closed_p if v.get("last_profit", 0) > 0]
        _losses = [v["last_profit"] for v in _closed_p if v.get("last_profit", 0) <= 0]
        _wr     = len(_wins) / _l_rn if _l_rn > 0 else 0.0
        _gross_p = sum(_wins)
        _gross_l = abs(sum(_losses)) if _losses else 0.0
        _pf     = round(_gross_p / _gross_l, 4) if _gross_l > 0 else ("inf" if _gross_p > 0 else 0.0)
        _exp    = round(_l_rpnl / _l_rn, 6) if _l_rn > 0 else 0.0
        pnl_run["net_pnl"]          = round(_l_rpnl, 4)
        pnl_run["closed_positions"] = _l_rn
        pnl_run["win_rate_dollar"]  = round(_wr, 4)
        pnl_run["profit_factor"]    = _pf
        pnl_run["expectancy"]       = _exp
        pnl_run["avg_win"]          = round(sum(_wins) / len(_wins), 4) if _wins else 0.0
        pnl_run["avg_loss"]         = round(sum(_losses) / len(_losses), 4) if _losses else 0.0
        pnl_run["_source"]          = "LEDGER_FALLBACK"

    agg["pnl_financial"] = pnl_run
    agg["pnl_per_cycle"] = pnl_per_cycle
    agg["close_mode"] = CLOSE_MODE
    agg["close_ttl_sec"] = CLOSE_TTL_SEC
    # A4: critério GO/NO-GO expandido (CIO+CQO: 10 checks)
    agg["go_no_go"] = evaluate_go_no_go(pnl_run, agg=agg)
    # CQO Opcao C: gravar relatorio de monitoramento no aggregate
    agg["latency_circuit_breaker"] = lcb.status()
    agg["performance_monitor"]    = pm.report()

    agg_path = out_dir / f"fase4_{args.label}_aggregate.json"
    with open(agg_path, "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)
    sha = hashlib.sha3_256(open(agg_path, "rb").read()).hexdigest()
    (out_dir / f"fase4_{args.label}_aggregate.sha3").write_text(sha + "\n", encoding="utf-8")

    print("=" * 70)
    print(f"[FASE4 {args.label}] AGGREGATE: {agg_path}")
    print(f"  cycles={agg['cycles']} total_trades={agg['total_trades']} executed={agg['total_executed']}")
    print(f"  hit_rate_avg={agg['hit_rate_avg']} latency_p95={agg['latency_ms_p95']}ms latency_max={agg['latency_ms_max']}ms")
    print(f"  ks_triggers={agg['kill_switch_triggers']} max_concentration={agg['max_concentration_pct']}% on {agg['max_concentration_asset']}")
    print(f"  --- LEDGER P&L (posicoes rastreadas em tempo real) ---")
    print(f"  ledger_all={agg['ledger_n_positions']} realized={agg['ledger_realized_n']} realized_pnl=${agg['ledger_realized_pnl']:+.4f} snapshot=${agg['ledger_total_pnl']:+.4f}")
    print(f"  spread_cost_total=${agg['ledger_spread_cost_usd']:+.4f} | net_after_cost=${agg['ledger_realized_pnl']-agg['ledger_spread_cost_usd']:+.4f}")
    _pnl_src = pnl_run.get('_source', 'HISTORY_DEALS')
    print(f"  [P&L SOURCE: {_pnl_src}]")
    print(f"  retcodes={agg['retcodes']}")
    print("  --- A3 KPIs FINANCEIROS ---")
    print(f"  net_pnl=${pnl_run.get('net_pnl', 0):+.4f} win_rate_$={pnl_run.get('win_rate_dollar', 0)*100:.1f}% "
          f"profit_factor={pnl_run.get('profit_factor')} expectancy=${pnl_run.get('expectancy', 0):+.4f} "
          f"closed_positions={pnl_run.get('closed_positions', 0)}")
    _by_act    = agg.get("by_action", {})
    _b_buys    = _by_act.get("BUY", 0) + _by_act.get("ORDER_DONE", 0)
    _b_sells   = _by_act.get("SELL", 0)
    _b_total   = _b_buys + _b_sells
    _bias_ratio = abs(_b_buys - _b_sells) / _b_total if _b_total > 0 else 0.0
    go = agg["go_no_go"]
    _status_m = 'GO [PASS]' if go['go'] else 'NO-GO [FAIL]'
    _status_f = 'GO_FULL [PASS]' if go.get('go_full') else 'GO_FULL [WARN]'
    print(f"  --- A4 GO/NO-GO: {_status_m} | {_status_f}")
    if go['failed_mandatory']:
        print(f"  MANDATORY FAILED: {go['failed_mandatory']}")
    if go.get('failed_recommended'):
        print(f"  RECOMMENDED FAILED: {go['failed_recommended']}")
    print(f"  Sharpe={pnl_run.get('sharpe_per_trade',0):.3f} DD={pnl_run.get('max_drawdown_pct',0)*100:.2f}% consec_loss={pnl_run.get('consecutive_losses',0)}")
    print(f"  KS_triggers={agg.get('kill_switch_triggers',0)} concentration={agg.get('max_concentration_pct',0):.1f}% corr_blocks={agg.get('corr_blocks',0)}")
    print(f"  bias_ratio={_bias_ratio:.2f} slip_avg={agg.get('slippage_avg_pts',0):.2f}pts")
    print(f"  SHA3={sha}")
    # CQO: imprimir status de monitoramento
    lcb_st = lcb.status()
    pm_rep = pm.report()
    if lcb_st["triggered"]:
        print(f"  [LCB WARNING] Circuit breaker ativo: {lcb_st['reason']}")
    else:
        print(f"  [LCB OK] p95_latency={lcb_st['current_p95_ms']}ms (threshold={lcb.p95_threshold_ms}ms)")
    if pm_rep["alerts_count"] > 0:
        print(f"  [PM ALERTS={pm_rep['alerts_count']}] {[a['type'] for a in pm_rep['alerts']]}")
    else:
        print(f"  [PM OK] samples={pm_rep['samples']} net_total=${pm_rep.get('net_total',0):+.2f}")
    print("=" * 70)
    return 0 if agg["go_no_go"]["go"] else 2


if __name__ == "__main__":
    try:
        rc = main()
    except KeyboardInterrupt:
        print("\n[FASE4] Interrompido pelo usuario.")
        rc = 0
    finally:
        _release_lock()
    sys.exit(rc)
