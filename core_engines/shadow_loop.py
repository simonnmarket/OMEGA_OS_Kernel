#!/usr/bin/env python3
"""
OMEGA SHADOW / PAPER LOOP ENGINE v3.0 — MT5 REAL INTEGRADO
nebular-kuiper\core_engines\shadow_loop.py

SHADOW : gera sinais, loga, NÃO envia ordens (zero risco).
PAPER  : envia ordens reais para conta DEMO via MetaTrader5 API.
         Kill switch: DD diário ≥ 5% OU 3 retcodes de falha consecutivos.

Retcodes MT5 monitorados:
  10009 TRADE_RETCODE_DONE     ← sucesso
  10004 TRADE_RETCODE_REQUOTE  ← re-quote (slippage)
  10006 TRADE_RETCODE_REJECT   ← rejeitado pelo broker
  10007 TRADE_RETCODE_CANCEL   ← cancelado pelo cliente
  10010 TRADE_RETCODE_PLACED   ← ordem colocada
  10013 TRADE_RETCODE_INVALID  ← parâmetros inválidos
  10016 TRADE_RETCODE_INVALID_STOPS ← SL/TP inválidos
  10019 TRADE_RETCODE_NO_MONEY ← fundos insuficientes
  10030 TRADE_RETCODE_LIMIT_ORDERS ← limite de ordens atingido

Uso:
  python shadow_loop.py --mode shadow --ativos XAUUSD GBPUSD --timeframes H1 H4
  python shadow_loop.py --mode paper  --ativos XAUUSD GBPUSD USDJPY AUDUSD AUDJPY \
                                               ETHUSD US500 SOLUSD DOGUSD \
                                       --timeframes H1 H4 --equity 10000
"""

import argparse
import hashlib
import json
import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ─── Caminhos ───────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent
CORE        = Path(__file__).resolve().parent
OHLCV       = Path(r"C:\OMEGA_PROJETO\OHLCV_DATA")
AUDIT_PAPER = ROOT / "audit" / "paper"
AUDIT_PAPER.mkdir(parents=True, exist_ok=True)

# ─── Configuração de Risco ───────────────────────────────────────────────────
DEMO_EQUITY_USD    = 10_000.0
RISK_PER_TRADE_PCT = 0.0025     # 0,25% por trade
MAX_POSITIONS      = 3
DD_DAILY_MAX       = 0.05       # 5% kill switch
MAX_CONSEC_FAIL    = 3
OMEGA_MAGIC        = 234001     # ID do EA OMEGA

# ─── Guardrails ─────────────────────────────────────────────────────────────
TIER1_ASSETS = {
    "XAUUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY",
    "ETHUSD", "US500",  "SOLUSD", "DOGUSD",
}
HIT_RATE_MIN = 80.0
MACH_MAX     = 1.5

# ─── Retcodes MT5 ────────────────────────────────────────────────────────────
RETCODE_OK   = {10009, 10010}   # DONE, PLACED
RETCODE_WARN = {10004}          # REQUOTE — logar mas não falhar
RETCODE_FAIL = {10006, 10007, 10013, 10016, 10019, 10030}

RETCODE_DESC = {
    10004: "REQUOTE",       10006: "REJECT",
    10007: "CANCEL",        10009: "DONE",
    10010: "PLACED",        10013: "INVALID_REQUEST",
    10016: "INVALID_STOPS", 10019: "NO_MONEY",
    10030: "LIMIT_ORDERS",  10014: "TOO_MANY_REQ",
}

# ─── Logging ─────────────────────────────────────────────────────────────────
ts_str   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
log_file = AUDIT_PAPER / f"paper_loop_{ts_str}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("PAPER")


# ─── SHA3-256 ────────────────────────────────────────────────────────────────
def sha3(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


# ─── Wilson IC ────────────────────────────────────────────────────────────────
def wilson_ic(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0: return 0.0, 1.0
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    m = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return max(0.0, c - m), min(1.0, c + m)


# ─── Margens Dinâmicas ───────────────────────────────────────────────────────
def load_dynamic_margins() -> dict:
    p = ROOT / "audit" / "dynamic_margins.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("margins", {})
    return {}


# ─── MT5 — Inicialização e Shutdown ─────────────────────────────────────────
def mt5_init() -> bool:
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            log.error("MT5 initialize() falhou: %s", mt5.last_error())
            return False
        info = mt5.terminal_info()
        log.info("MT5 conectado | build=%s | trade_allowed=%s | connected=%s",
                 info.build if info else "?",
                 info.trade_allowed if info else "?",
                 info.connected if info else "?")
        return True
    except ImportError:
        log.error("MetaTrader5 package não instalado. Execute: pip install MetaTrader5")
        return False


def mt5_shutdown():
    try:
        import MetaTrader5 as mt5
        mt5.shutdown()
    except Exception:
        pass


# ─── MT5 — Verificar Requisição Antes de Enviar (OrderCheck) ────────────────
def mt5_check_order(request: dict) -> Optional[dict]:
    import MetaTrader5 as mt5
    result = mt5.order_check(request)
    if result is None:
        log.warning("order_check retornou None: %s", mt5.last_error())
        return None
    r = result._asdict()
    if r["retcode"] != 0:
        log.warning("order_check FAIL retcode=%d comment=%s", r["retcode"], r.get("comment"))
    else:
        log.info("order_check OK | margin=%.2f balance=%.2f equity=%.2f free_margin=%.2f",
                 r.get("margin", 0), r.get("balance", 0),
                 r.get("equity", 0), r.get("margin_free", 0))
    return r


# ─── MT5 — Enviar Ordem Real (Demo) ─────────────────────────────────────────
def mt5_send_order(asset: str, tf: str, lot: float,
                   sl_pts: float, tp_pts: float) -> Dict:
    """
    Envia ordem de compra a mercado via mt5.order_send().
    Usa TRADE_ACTION_DEAL + ORDER_TYPE_BUY.
    Retorna dict com retcode, deal, price, slippage, latência, etc.
    NOTA: Somente conta DEMO. Guardrails já foram aplicados antes desta chamada.
    """
    import MetaTrader5 as mt5

    tick = mt5.symbol_info_tick(asset)
    sym  = mt5.symbol_info(asset)
    if tick is None or sym is None:
        log.error("[%s] symbol_info_tick falhou", asset)
        return {"retcode": -1, "retcode_str": "NO_TICK", "error": "symbol_info_tick returned None"}

    price    = tick.ask
    point    = sym.point
    digits   = sym.digits
    sl_price = round(price - sl_pts * point, digits)
    tp_price = round(price + tp_pts * point, digits)

    # Selecionar filling mode suportado pelo broker (bit 0=FOK, bit 1=IOC, bit 2=RETURN)
    fm = sym.filling_mode if sym else 3
    if fm & 2:    filling = mt5.ORDER_FILLING_IOC     # IOC — preferido para demo
    elif fm & 1:  filling = mt5.ORDER_FILLING_FOK     # FOK — alternativa
    else:         filling = mt5.ORDER_FILLING_RETURN  # RETURN — fallback

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       asset,
        "volume":       lot,
        "type":         mt5.ORDER_TYPE_BUY,
        "price":        price,
        "sl":           sl_price,
        "tp":           tp_price,
        "deviation":    20,
        "magic":        OMEGA_MAGIC,
        "comment":      f"OMEGA-AMI-{tf}",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": filling,
    }
    log.info("[%s %s] filling_mode=%d → tipo=%s", asset, tf, fm,
             {mt5.ORDER_FILLING_IOC: "IOC", mt5.ORDER_FILLING_FOK: "FOK",
              mt5.ORDER_FILLING_RETURN: "RETURN"}.get(filling, str(filling)))

    # Pre-check
    check = mt5_check_order(request)
    if check and check.get("retcode", 0) not in (0, 10009):
        log.warning("[%s %s] order_check retcode=%d — enviando mesmo assim (demo)",
                    asset, tf, check.get("retcode", -1))

    t0     = time.perf_counter()
    result = mt5.order_send(request)
    lat_ms = round((time.perf_counter() - t0) * 1000, 1)

    if result is None:
        err = mt5.last_error()
        log.error("[%s %s] order_send retornou None: %s", asset, tf, err)
        return {"retcode": -1, "retcode_str": "NULL_RESULT", "error": str(err),
                "latency_ms": lat_ms}

    r = result._asdict()
    retcode     = r.get("retcode", -1)
    retcode_str = RETCODE_DESC.get(retcode, f"UNKNOWN_{retcode}")
    slippage    = round(abs(r.get("price", price) - price) / point, 2)

    out = {
        "retcode":          retcode,
        "retcode_str":      retcode_str,
        "success":          retcode in RETCODE_OK,
        "deal":             r.get("deal", 0),
        "order":            r.get("order", 0),
        "fill_price":       r.get("price", price),
        "ask_at_send":      price,
        "sl_price":         sl_price,
        "tp_price":         tp_price,
        "volume_confirmed": r.get("volume", lot),
        "slippage_pts":     slippage,
        "comment":          r.get("comment", ""),
        "request_id":       r.get("request_id", 0),
        "latency_ms":       lat_ms,
        "mode":             "MT5_DEMO_REAL",
    }

    if out["success"]:
        log.info("[%s %s] ✅ ORDER DONE | deal=%d price=%.5f slip=%.2fpts lat=%dms",
                 asset, tf, out["deal"], out["fill_price"], out["slippage_pts"], lat_ms)
    elif retcode in RETCODE_WARN:
        log.warning("[%s %s] ⚠️ REQUOTE | bid=%.5f ask=%.5f", asset, tf,
                    r.get("bid", 0), r.get("ask", 0))
    else:
        log.error("[%s %s] ❌ ORDER FAIL | retcode=%d (%s) | %s",
                  asset, tf, retcode, retcode_str, out["comment"])

    return out


# ─── Rodar Motor Harmônico ────────────────────────────────────────────────────
def run_harmonic(asset: str, tf: str, margin: float, out_dir: Path) -> Optional[dict]:
    import subprocess
    out_dir.mkdir(parents=True, exist_ok=True)
    motor = CORE / "omega_harmonic_engine_v3.py"
    cmd   = [sys.executable, str(motor),
             "--symbol", asset, "--timeframe", tf,
             "--base_path", str(OHLCV),
             "--margin", str(margin),
             "--lookback", "3", "--lookahead", "5"]
    try:
        t0 = time.perf_counter()
        r  = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=str(out_dir), timeout=300)
        lat = time.perf_counter() - t0
        if r.returncode != 0:
            log.error("[%s %s] Motor V3 exit %d: %s", asset, tf, r.returncode, r.stderr[:200])
            return None
        jf = out_dir / f"harmonic_events_{asset}_{tf}.json"
        if not jf.exists():
            return None
        with open(jf, encoding="utf-8") as f:
            data = json.load(f)
        data["_latency_s"] = round(lat, 3)
        return data
    except Exception as e:
        log.error("[%s %s] Exceção motor: %s", asset, tf, e)
        return None


# ─── Price Engine ────────────────────────────────────────────────────────────
def get_price_result() -> dict:
    sys.path.insert(0, str(CORE))
    from omega_module_v553 import DCECalibratedPriceEngine, ModuleConfig
    return DCECalibratedPriceEngine(ModuleConfig()).compute_price(
        Q=1000, PBoc=0.0, volume_anomaly=0.1)


# ─── Guardrail Check ─────────────────────────────────────────────────────────
def check_guardrails(asset: str, tf: str, hr: float,
                     mach: float, dm: dict) -> dict:
    reasons = []
    if hr < HIT_RATE_MIN:    reasons.append(f"hit_rate_134={hr:.2f}% < {HIT_RATE_MIN}%")
    if mach > MACH_MAX:      reasons.append(f"Mach={mach:.2f} > {MACH_MAX}")
    if asset == "EURUSD":    reasons.append("EURUSD: grafico_linha ausente")
    margin = 150.0
    d = dm.get(asset, {}).get(tf)
    if d and isinstance(d, dict): margin = float(d.get("margin_dynamic", 150.0))
    tier   = "T1" if asset in TIER1_ASSETS else ("T2" if hr >= HIT_RATE_MIN else "T3")
    return {"asset": asset, "timeframe": tf, "tier": tier,
            "hit_rate_134": hr, "mach": mach, "margin_used": margin,
            "skip": len(reasons) > 0, "skip_reasons": reasons}


# ─── Position Sizing ─────────────────────────────────────────────────────────
def calc_lot(equity: float, margin_pts: float, price: float) -> Dict:
    risk_usd  = equity * RISK_PER_TRADE_PCT
    stop_pts  = 2.0 * margin_pts
    pt_val    = price / 10_000.0 if price > 1000 else price / 100.0
    lot       = max(0.01, round(risk_usd / max(stop_pts * pt_val, 0.001), 2))
    return {"lot": lot, "risk_usd": round(risk_usd, 2),
            "stop_pts": stop_pts, "pt_value": round(pt_val, 6)}


# ─── Build AnalysisReport ───────────────────────────────────────────────────
def build_report(asset, tf, mode, harmonic, price_data, guard, exec_result, lot_info) -> dict:
    now  = datetime.now(timezone.utc).isoformat()
    m    = harmonic.get("engines", {}).get("harmonic", {}).get("metrics", {})
    s134 = m.get("134_stats", {}); s34 = m.get("34_stats", {})
    k, n = s134.get("hits", 0), s134.get("total_touches", 1)
    lb, ub = wilson_ic(k, n)
    report = {
        "mission_id":        f"PAPER-{asset}-{tf}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "asset": asset, "timeframe": tf, "status": "COMPLETED",
        "mode": mode, "created_at": now, "agent_version": "shadow_loop_v3.0",
        "omega_integration": True, "guardrail": guard,
        "binomial_ic_95": {
            "hits": k, "total": n,
            "p_hat": round(k / max(n, 1), 6),
            "lower_bound": round(lb, 6), "upper_bound": round(ub, 6),
            "interval": f"[{lb*100:.4f}%, {ub*100:.4f}%]",
        },
        "engines": {
            "harmonic": {"metrics": {"34_stats": s34, "134_stats": s134}},
            "price": {
                "price":   price_data.get("price"),
                "base_price": price_data.get("base_price"),
                "flash_crash_adjustment": price_data.get("flash_crash_adjustment"),
                "metadata": {k2: v2 for k2, v2 in price_data.get("metadata", {}).items()
                             if k2 in ["params_checksum", "rmse_expected", "r_squared"]},
            },
        },
        "signal": {
            "action":       "SKIP" if guard["skip"] else ("MT5_PAPER_EXECUTE" if mode == "paper" else "MONITOR"),
            "skip_reasons": guard["skip_reasons"],
            "margin_used":  guard["margin_used"],
            "tier":         guard["tier"],
        },
        "execution": exec_result,
        "lot_info":  lot_info,
        "latency_motor_s": harmonic.get("_latency_s"),
    }
    jb = json.dumps(report, indent=2).encode("utf-8")
    report["checksum"] = sha3(jb)
    return report


# ─── Kill Switch ─────────────────────────────────────────────────────────────
class KillSwitch:
    def __init__(self, equity: float):
        self.equity = equity; self.daily_pnl = 0.0
        self.consec_fail = 0; self.triggered = False; self.reason = ""
    def update(self, success: bool, pnl_usd: float = 0.0) -> bool:
        if self.triggered: return True
        self.daily_pnl += pnl_usd
        if not success: self.consec_fail += 1
        else:           self.consec_fail = 0
        if abs(self.daily_pnl) / self.equity >= DD_DAILY_MAX:
            self.reason = f"DD diário {abs(self.daily_pnl)/self.equity*100:.2f}% ≥ {DD_DAILY_MAX*100:.0f}%"
            self.triggered = True; log.critical("💀 KILL SWITCH: %s", self.reason)
        if self.consec_fail >= MAX_CONSEC_FAIL:
            self.reason = f"{self.consec_fail} falhas consecutivas"
            self.triggered = True; log.critical("💀 KILL SWITCH: %s", self.reason)
        return self.triggered


# ─── Online Statistics ────────────────────────────────────────────────────────
class OnlineStats:
    def __init__(self):
        self.signals = 0; self.executed = 0; self.skipped = 0
        self.pnl = 0.0; self.slippage = []; self.latencies = []; self.hrs = []
    def record(self, report: dict):
        self.signals += 1
        action = report["signal"]["action"]
        if "SKIP" in action: self.skipped += 1; return
        self.executed += 1
        hr = report["engines"]["harmonic"]["metrics"]["134_stats"].get("hit_rate", 0)
        self.hrs.append(hr)
        ex = report.get("execution") or {}
        self.slippage.append(ex.get("slippage_pts", 0))
        self.latencies.append(ex.get("latency_ms", 0))
    def summary(self) -> dict:
        n = max(len(self.hrs), 1)
        return {
            "total_signals":    self.signals,
            "executed":         self.executed,
            "skipped":          self.skipped,
            "avg_hit_rate_134": round(sum(self.hrs) / n, 4) if self.hrs else 0,
            "avg_slippage_pts": round(sum(self.slippage) / max(len(self.slippage), 1), 3),
            "avg_latency_ms":   round(sum(self.latencies) / max(len(self.latencies), 1), 1),
            "max_latency_ms":   round(max(self.latencies, default=0), 1),
        }


# ─── Loop Principal ───────────────────────────────────────────────────────────
def run_loop(ativos: List[str], timeframes: List[str], mode: str, equity: float):
    log.info("=" * 72)
    log.info("OMEGA %s LOOP v3.0 | %d ativos × %d TFs | equity=USD %.2f",
             mode.upper(), len(ativos), len(timeframes), equity)
    log.info("Risk/trade=%.2f%% | MaxPos=%d | DD_max=%.0f%% | MT5_MAGIC=%d",
             RISK_PER_TRADE_PCT * 100, MAX_POSITIONS, DD_DAILY_MAX * 100, OMEGA_MAGIC)
    log.info("=" * 72)

    mt5_connected = False
    if mode == "paper":
        mt5_connected = mt5_init()
        if not mt5_connected:
            log.critical("MT5 não disponível. Abortando modo paper.")
            return {"error": "MT5 não conectado", "kill_switch": True}

    dm       = load_dynamic_margins()
    price_d  = get_price_result()
    ks       = KillSwitch(equity)
    stats    = OnlineStats()
    open_pos = 0
    skip_tbl = []
    results  = []

    try:
        for asset in ativos:
            for tf in timeframes:
                if ks.triggered:
                    log.critical("[%s %s] KS ativo — abortando.", asset, tf); break

                log.info("[%s %s] ── Ciclo ──", asset, tf)

                # Guardrail pré-motor
                prev_hr = 100.0
                rep_f = ROOT / "audit" / f"{asset}_{tf}" / f"AnalysisReport_{asset}_{tf}.json"
                if rep_f.exists():
                    try:
                        with open(rep_f, encoding="utf-8") as f2:
                            prev = json.load(f2)
                        prev_hr = (prev.get("engines", {}).get("harmonic", {})
                                   .get("metrics", {}).get("134_stats", {})
                                   .get("hit_rate", 100.0))
                    except Exception: pass

                guard = check_guardrails(asset, tf, prev_hr, 1.0, dm)
                if guard["skip"]:
                    log.warning("[%s %s] SKIP (pre) — %s", asset, tf, guard["skip_reasons"])
                    skip_tbl.append(guard)
                    dummy = {"asset": asset, "timeframe": tf, "status": "SKIP",
                             "signal": {"action": "SKIP",
                                        "skip_reasons": guard["skip_reasons"],
                                        "tier": guard["tier"],
                                        "margin_used": guard["margin_used"]},
                             "engines": {"harmonic": {"metrics": {"134_stats": {}}},
                                         "price": {}},
                             "execution": None, "lot_info": None, "binomial_ic_95": {}}
                    stats.record(dummy); ks.update(True)
                    results.append({"asset": asset, "timeframe": tf, "status": "SKIP",
                                    "reasons": guard["skip_reasons"]}); continue

                if mode == "paper" and open_pos >= MAX_POSITIONS:
                    log.warning("[%s %s] MAX_POSITIONS=%d atingido.", asset, tf, MAX_POSITIONS); continue

                # Motor Harmônico V3
                out_dir  = AUDIT_PAPER / f"{asset}_{tf}"
                harmonic = run_harmonic(asset, tf, guard["margin_used"], out_dir)
                if harmonic is None:
                    ks.update(False)
                    results.append({"asset": asset, "timeframe": tf, "status": "FAIL"}); continue

                # Guardrail final
                s134    = (harmonic.get("engines", {}).get("harmonic", {})
                           .get("metrics", {}).get("134_stats", {}))
                hr_real = s134.get("hit_rate", 0.0)
                guard   = check_guardrails(asset, tf, hr_real, 1.0, dm)

                # Execução
                lot_info = exec_result = None

                if not guard["skip"] and mode == "paper" and mt5_connected:
                    import MetaTrader5 as mt5
                    tick     = mt5.symbol_info_tick(asset)
                    price_mt = tick.ask if tick else price_d.get("price", 2000.0)
                    lot_info = calc_lot(equity, guard["margin_used"], price_mt)
                    exec_result = mt5_send_order(
                        asset, tf, lot_info["lot"],
                        sl_pts=guard["margin_used"] * 2,
                        tp_pts=guard["margin_used"] * 2)
                    success = exec_result.get("success", False)
                    open_pos = min(open_pos + (1 if success else 0), MAX_POSITIONS)
                    ks.update(success, 0.0)   # PnL real será monitorado via posições abertas
                elif not guard["skip"] and mode == "shadow":
                    log.info("[%s %s] MONITOR | hr134=%.2f%% | margin=%.1fpts | NO ORDER",
                             asset, tf, hr_real, guard["margin_used"])
                    ks.update(True)

                report = build_report(asset, tf, mode, harmonic, price_d, guard,
                                      exec_result, lot_info)
                out_f = out_dir / f"PaperReport_{asset}_{tf}.json"
                with open(out_f, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                stats.record(report)
                action = report["signal"]["action"]
                if exec_result:
                    log.info("[%s %s] %s | hr134=%.2f%% IC=%s lot=%.2f slip=%.2f lat=%dms | SHA3=%s...",
                             asset, tf, action, hr_real,
                             report["binomial_ic_95"]["interval"],
                             lot_info["lot"],
                             exec_result.get("slippage_pts", 0),
                             exec_result.get("latency_ms", 0),
                             report["checksum"][:16])
                else:
                    log.info("[%s %s] %s | hr134=%.2f%% IC=%s | SHA3=%s...",
                             asset, tf, action, hr_real,
                             report["binomial_ic_95"]["interval"],
                             report["checksum"][:16])

                results.append({
                    "asset": asset, "timeframe": tf, "status": action,
                    "hit_rate_134": hr_real,
                    "ic_95": report["binomial_ic_95"]["interval"],
                    "margin_used": guard["margin_used"],
                    "lot": lot_info["lot"] if lot_info else None,
                    "retcode": exec_result.get("retcode") if exec_result else None,
                    "slippage_pts": exec_result.get("slippage_pts") if exec_result else None,
                    "checksum": report["checksum"][:24],
                })
    finally:
        if mt5_connected:
            mt5_shutdown()
            log.info("MT5 desconectado.")

    # Skip table
    skip_out  = AUDIT_PAPER / "skip_table.json"
    skip_data = {"generated": datetime.now(timezone.utc).isoformat(), "skips": skip_tbl}
    skip_data["checksum"] = sha3(json.dumps(skip_data, indent=2).encode("utf-8"))
    with open(skip_out, "w", encoding="utf-8") as f:
        json.dump(skip_data, f, indent=2, ensure_ascii=False)

    # Stats
    stat_sum = stats.summary()
    log.info("── ESTATÍSTICAS ONLINE ──────────────────────────────────────")
    for k, v in stat_sum.items(): log.info("  %-25s : %s", k, v)

    # Summary
    now = datetime.now(timezone.utc).isoformat()
    summary = {
        "mode": mode, "generated": now, "equity_demo": equity,
        "total_cycles": len(results),
        "kill_switch": ks.triggered, "ks_reason": ks.reason,
        "online_stats": stat_sum, "results": results,
        "log_file": str(log_file),
    }
    sb = json.dumps(summary, indent=2).encode("utf-8")
    summary["checksum"] = sha3(sb)
    sum_out = AUDIT_PAPER / "paper_summary.json"
    with open(sum_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info("=" * 72)
    log.info("%s LOOP CONCLUÍDO | cycles=%d | KS=%s", mode.upper(), len(results), ks.triggered)
    log.info("SHA3 summary: %s", summary["checksum"])
    log.info("Artifacts: %s", AUDIT_PAPER)
    log.info("=" * 72)
    return summary


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OMEGA Shadow/Paper Loop v3.0 — MT5 Real")
    parser.add_argument("--mode",       choices=["shadow", "paper"], default="shadow")
    parser.add_argument("--ativos",     nargs="+", default=sorted(TIER1_ASSETS))
    parser.add_argument("--timeframes", nargs="+", default=["H1", "H4"])
    parser.add_argument("--equity",     type=float, default=DEMO_EQUITY_USD)
    args = parser.parse_args()
    try:
        r = run_loop(args.ativos, args.timeframes, args.mode, args.equity)
        sys.exit(0 if r and not r.get("kill_switch") else 1)
    except Exception:
        log.critical("ERRO CRÍTICO:\n%s", traceback.format_exc())
        sys.exit(2)
