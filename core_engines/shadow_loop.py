#!/usr/bin/env python3
"""
OMEGA SHADOW / PAPER LOOP ENGINE v2.0
nebular-kuiper\core_engines\shadow_loop.py

SHADOW : gera sinais, loga, NÃO envia ordens.
PAPER  : simula execução demo (quanto ficaria a posição, slippage estimado,
         PnL teórico). Sem MT5 real — integrar broker API na fase live.

Kill switch  : DD diário ≥ 5% OU 3 falhas consecutivas.
Risco/trade  : ≤ 0,25% da equity (default 10.000 USD demo).
Max posições : 3 simultâneas.

Uso:
  # Shadow (sem ordens):
  python shadow_loop.py --mode shadow --ativos XAUUSD GBPUSD --timeframes H1 H4

  # Paper (simula execução demo):
  python shadow_loop.py --mode paper --ativos XAUUSD GBPUSD USDJPY AUDUSD AUDJPY \
                         ETHUSD US500 SOLUSD DOGUSD --timeframes H1 H4
"""

import argparse
import hashlib
import json
import logging
import os
import random
import subprocess
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
DEMO_EQUITY_USD    = 10_000.0   # Conta demo de referência
RISK_PER_TRADE_PCT = 0.0025     # 0,25% da equity por trade
MAX_POSITIONS      = 3          # Máximo de posições simultâneas
DD_DAILY_MAX       = 0.05       # 5% drawdown diário → kill switch
MAX_CONSEC_FAIL    = 3          # 3 falhas → kill switch

# ─── Guardrails ─────────────────────────────────────────────────────────────
TIER1_ASSETS = {
    "XAUUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY",
    "ETHUSD", "US500",  "SOLUSD", "DOGUSD",
}
HIT_RATE_MIN = 80.0
MACH_MAX     = 1.5

# ─── Slippage típico por classe de ativo (em pontos) ────────────────────────
SLIPPAGE_MAP = {
    "XAUUSD": (1.5, 4.0),   "EURUSD": (0.5, 1.5),   "GBPUSD": (0.5, 2.0),
    "USDJPY": (0.3, 1.0),   "AUDUSD": (0.5, 2.0),   "AUDJPY": (0.5, 2.0),
    "ETHUSD": (2.0, 8.0),   "BTCUSD": (5.0, 20.0),  "US500":  (0.3, 1.0),
    "US100":  (0.5, 2.0),   "SOLUSD": (1.0, 4.0),   "DOGUSD": (0.1, 0.5),
    "GER40":  (0.5, 2.0),   "HK50":   (1.0, 4.0),   "US30":   (0.5, 2.0),
}

# ─── Logging ────────────────────────────────────────────────────────────────
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


# ─── Carregar margens dinâmicas ───────────────────────────────────────────────
def load_dynamic_margins() -> dict:
    p = ROOT / "audit" / "dynamic_margins.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("margins", {})
    return {}


# ─── Guardrail Check ─────────────────────────────────────────────────────────
def check_guardrails(asset: str, tf: str,
                     hit_rate_134: float, mach: float,
                     dynamic_margins: dict) -> dict:
    reasons = []
    tier = "T1" if asset in TIER1_ASSETS else ("T2" if hit_rate_134 >= HIT_RATE_MIN else "T3")

    if hit_rate_134 < HIT_RATE_MIN:
        reasons.append(f"hit_rate_134={hit_rate_134:.2f}% < {HIT_RATE_MIN}%")
    if mach > MACH_MAX:
        reasons.append(f"Mach={mach:.2f} > {MACH_MAX}")
    if asset == "EURUSD":
        reasons.append("EURUSD: grafico_linha ausente")

    margin = 150.0
    dm = dynamic_margins.get(asset, {}).get(tf)
    if dm and isinstance(dm, dict):
        margin = float(dm.get("margin_dynamic", 150.0))

    return {
        "asset": asset, "timeframe": tf, "tier": tier,
        "hit_rate_134": hit_rate_134, "mach": mach,
        "margin_used": margin, "skip": len(reasons) > 0,
        "skip_reasons": reasons,
    }


# ─── Rodar Motor Harmônico ────────────────────────────────────────────────────
def run_harmonic(asset: str, tf: str, margin: float,
                 out_dir: Path) -> Optional[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    motor = CORE / "omega_harmonic_engine_v3.py"
    cmd = [sys.executable, str(motor),
           "--symbol", asset, "--timeframe", tf,
           "--base_path", str(OHLCV),
           "--margin", str(margin),
           "--lookback", "3", "--lookahead", "5"]
    try:
        t0 = time.perf_counter()
        r  = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=str(out_dir), timeout=300)
        latency = time.perf_counter() - t0
        if r.returncode != 0:
            log.error("[%s %s] Motor exit %d: %s",
                      asset, tf, r.returncode, r.stderr[:200])
            return None
        jf = out_dir / f"harmonic_events_{asset}_{tf}.json"
        if not jf.exists():
            log.error("[%s %s] JSON ausente: %s", asset, tf, jf)
            return None
        with open(jf, encoding="utf-8") as f:
            data = json.load(f)
        data["_latency_s"] = round(latency, 3)
        return data
    except Exception as e:
        log.error("[%s %s] Exceção motor: %s", asset, tf, e)
        return None


# ─── Price Engine ────────────────────────────────────────────────────────────
def get_price_result() -> dict:
    sys.path.insert(0, str(CORE))
    from omega_module_v553 import DCECalibratedPriceEngine, ModuleConfig
    engine = DCECalibratedPriceEngine(ModuleConfig())
    return engine.compute_price(Q=1000, PBoc=0.0, volume_anomaly=0.1)


# ─── Position Sizing (0,25% equity) ──────────────────────────────────────────
def calc_lot(equity: float, margin_pts: float,
             asset: str, price: float) -> Dict:
    """
    Risco máximo por trade: equity × 0.25%
    Stop loss estimado: 2 × margin (cobertura conservadora)
    Lote ajustado ao mínimo demo de 0.01
    """
    risk_usd    = equity * RISK_PER_TRADE_PCT
    stop_pts    = 2.0 * margin_pts                    # stop 2× margin
    pt_value    = price / 10_000.0 if price > 1000 else price / 100.0
    lot_raw     = risk_usd / (stop_pts * pt_value) if stop_pts * pt_value > 0 else 0.01
    lot         = max(0.01, round(lot_raw, 2))
    return {"lot": lot, "risk_usd": round(risk_usd, 2),
            "stop_pts": stop_pts, "pt_value": round(pt_value, 6)}


# ─── Simular Execução Demo ────────────────────────────────────────────────────
def simulate_paper_execution(asset: str, tf: str,
                              price: float, lot: float,
                              margin_pts: float) -> Dict:
    """
    Simula execução paper (sem MT5 real).
    Gera slippage realista, retcode e latência de rede estimada.
    NOTA: Substituir por chamada real à API MT5 na fase live.
    """
    slip_range   = SLIPPAGE_MAP.get(asset, (1.0, 5.0))
    slippage_pts = round(random.uniform(*slip_range), 2)
    latency_ms   = round(random.uniform(12, 80), 1)    # latência demo típica
    fill_price   = round(price + slippage_pts * 0.01, 5)
    retcode      = 10009                               # TRADE_RETCODE_DONE

    pnl_pts = round(random.uniform(-margin_pts * 0.5, margin_pts * 0.8), 2)
    pnl_usd = round(pnl_pts * lot * 0.01 * price / 1000, 2)

    return {
        "retcode":     retcode,
        "retcode_str": "TRADE_RETCODE_DONE",
        "fill_price":  fill_price,
        "slippage_pts": slippage_pts,
        "lot":         lot,
        "pnl_pts":     pnl_pts,
        "pnl_usd":     pnl_usd,
        "latency_ms":  latency_ms,
        "mode":        "PAPER_SIMULATION",
        "note":        "Substituir por API MT5 real na fase live",
    }


# ─── Construir AnalysisReport ─────────────────────────────────────────────────
def build_paper_report(asset: str, tf: str, mode: str,
                       harmonic: dict, price_data: dict,
                       guardrail: dict, execution: Optional[dict],
                       lot_info: Optional[dict]) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    m    = harmonic.get("engines", {}).get("harmonic", {}).get("metrics", {})
    s134 = m.get("134_stats", {})
    s34  = m.get("34_stats",  {})
    k134 = s134.get("hits", 0)
    n134 = s134.get("total_touches", 1)
    lb, ub = wilson_ic(k134, n134)

    report = {
        "mission_id":        f"PAPER-{asset}-{tf}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "asset":             asset,
        "timeframe":         tf,
        "status":            "COMPLETED",
        "mode":              mode,
        "created_at":        now,
        "agent_version":     "shadow_loop_v2.0",
        "omega_integration": True,
        "guardrail":         guardrail,
        "binomial_ic_95": {
            "hits": k134, "total": n134,
            "p_hat": round(k134 / max(n134, 1), 6),
            "lower_bound": round(lb, 6), "upper_bound": round(ub, 6),
            "interval": f"[{lb*100:.4f}%, {ub*100:.4f}%]",
        },
        "engines": {
            "harmonic": {"metrics": {"34_stats": s34, "134_stats": s134}},
            "price": {
                "price":                  price_data.get("price"),
                "base_price":             price_data.get("base_price"),
                "flash_crash_adjustment": price_data.get("flash_crash_adjustment"),
                "components":             price_data.get("components"),
                "metadata": {k: v for k, v in price_data.get("metadata", {}).items()
                             if k in ["params_checksum", "rmse_expected", "r_squared"]},
            },
        },
        "signal": {
            "action":       "SKIP" if guardrail["skip"] else ("PAPER_EXECUTE" if mode == "paper" else "MONITOR"),
            "skip_reasons": guardrail["skip_reasons"],
            "margin_used":  guardrail["margin_used"],
            "tier":         guardrail["tier"],
        },
        "execution": execution,
        "lot_info":  lot_info,
        "latency_motor_s": harmonic.get("_latency_s"),
    }

    jb = json.dumps(report, indent=2).encode("utf-8")
    report["checksum"] = sha3(jb)
    return report


# ─── Kill Switch ─────────────────────────────────────────────────────────────
class KillSwitch:
    def __init__(self, equity: float):
        self.equity       = equity
        self.daily_pnl    = 0.0
        self.consec_fail  = 0
        self.triggered    = False
        self.reason       = ""

    def update(self, success: bool, pnl_usd: float = 0.0) -> bool:
        if self.triggered:
            return True
        self.daily_pnl += pnl_usd
        if not success:
            self.consec_fail += 1
        else:
            self.consec_fail = 0
        dd_pct = abs(self.daily_pnl) / self.equity
        if dd_pct >= DD_DAILY_MAX:
            self.reason    = f"DD diário {dd_pct*100:.2f}% ≥ {DD_DAILY_MAX*100:.0f}%"
            self.triggered = True
            log.critical("💀 KILL SWITCH: %s — loop encerrado!", self.reason)
        if self.consec_fail >= MAX_CONSEC_FAIL:
            self.reason    = f"{self.consec_fail} falhas consecutivas"
            self.triggered = True
            log.critical("💀 KILL SWITCH: %s — loop encerrado!", self.reason)
        return self.triggered


# ─── Online Statistics ────────────────────────────────────────────────────────
class OnlineStats:
    def __init__(self):
        self.signals       = 0
        self.monitor_count = 0
        self.skip_count    = 0
        self.total_pnl     = 0.0
        self.total_slippage= 0.0
        self.latencies_ms  = []
        self.hr_observations = []

    def record(self, report: dict):
        action = report["signal"]["action"]
        self.signals += 1
        if "SKIP" in action:
            self.skip_count += 1
            return
        self.monitor_count += 1
        hr = report["engines"]["harmonic"]["metrics"]["134_stats"].get("hit_rate", 0)
        self.hr_observations.append(hr)
        ex = report.get("execution")
        if ex:
            self.total_pnl     += ex.get("pnl_usd", 0)
            self.total_slippage += ex.get("slippage_pts", 0)
            self.latencies_ms.append(ex.get("latency_ms", 0))

    def summary(self) -> dict:
        n  = max(len(self.hr_observations), 1)
        lm = self.latencies_ms or [0]
        return {
            "total_signals":    self.signals,
            "monitor":          self.monitor_count,
            "skipped":          self.skip_count,
            "avg_hit_rate_134": round(sum(self.hr_observations) / n, 4),
            "total_pnl_usd":    round(self.total_pnl, 2),
            "avg_slippage_pts": round(self.total_slippage / n, 3),
            "avg_latency_ms":   round(sum(lm) / len(lm), 1),
            "max_latency_ms":   round(max(lm), 1),
        }


# ─── Loop Principal ───────────────────────────────────────────────────────────
def run_loop(ativos: List[str], timeframes: List[str],
             mode: str, equity: float):

    log.info("=" * 72)
    log.info("OMEGA %s LOOP v2.0 | %d ativos × %d TFs | equity=USD %.2f",
             mode.upper(), len(ativos), len(timeframes), equity)
    log.info("Risk/trade=%.2f%% | MaxPos=%d | DD_max=%.0f%% | MaxFail=%d",
             RISK_PER_TRADE_PCT * 100, MAX_POSITIONS, DD_DAILY_MAX * 100, MAX_CONSEC_FAIL)
    log.info("Guardrails: HR134≥%.0f%% | Mach≤%.1f", HIT_RATE_MIN, MACH_MAX)
    log.info("=" * 72)

    dynamic_margins = load_dynamic_margins()
    price_data      = get_price_result()
    ks              = KillSwitch(equity)
    stats           = OnlineStats()
    open_positions  = 0
    skip_table      = []
    all_reports     = []

    for asset in ativos:
        for tf in timeframes:
            if ks.triggered:
                log.critical("[%s %s] KS ativo — abortando.", asset, tf)
                break

            log.info("[%s %s] ── Iniciando ciclo ──", asset, tf)
            t_cycle = time.perf_counter()

            # ── Guardrail preliminar (dados do Gama-Ray anteriores) ──
            prev_hr = 100.0
            rep_f = ROOT / "audit" / f"{asset}_{tf}" / f"AnalysisReport_{asset}_{tf}.json"
            if rep_f.exists():
                try:
                    with open(rep_f, encoding="utf-8") as f2:
                        prev = json.load(f2)
                    prev_hr = (prev.get("engines", {})
                               .get("harmonic", {})
                               .get("metrics", {})
                               .get("134_stats", {})
                               .get("hit_rate", 100.0))
                except Exception:
                    pass

            prelim = check_guardrails(asset, tf, prev_hr, 1.0, dynamic_margins)
            if prelim["skip"]:
                log.warning("[%s %s] SKIP (prelim) — %s", asset, tf, prelim["skip_reasons"])
                skip_table.append(prelim)
                dummy_report = {"asset": asset, "timeframe": tf, "status": "SKIP",
                                "signal": {"action": "SKIP",
                                           "skip_reasons": prelim["skip_reasons"],
                                           "tier": prelim["tier"],
                                           "margin_used": prelim["margin_used"]},
                                "engines": {"harmonic": {}, "price": {}},
                                "execution": None, "lot_info": None,
                                "binomial_ic_95": {}}
                stats.record(dummy_report)
                all_reports.append({"asset": asset, "timeframe": tf,
                                    "status": "SKIP", "reason": prelim["skip_reasons"]})
                continue

            # ── Verificar limite de posições ──
            if mode == "paper" and open_positions >= MAX_POSITIONS:
                log.warning("[%s %s] MAX_POSITIONS (%d) atingido — aguardando.",
                            asset, tf, MAX_POSITIONS)
                continue

            # ── Rodar Motor Harmônico V3 ──
            out_dir  = AUDIT_PAPER / f"{asset}_{tf}"
            harmonic = run_harmonic(asset, tf, prelim["margin_used"], out_dir)
            if harmonic is None:
                ks.update(success=False)
                all_reports.append({"asset": asset, "timeframe": tf, "status": "FAIL"})
                continue

            # ── Guardrail final com dados reais ──
            s134    = (harmonic.get("engines", {})
                       .get("harmonic", {})
                       .get("metrics", {})
                       .get("134_stats", {}))
            hr_real = s134.get("hit_rate", 0.0)
            guard   = check_guardrails(asset, tf, hr_real, 1.0, dynamic_margins)

            # ── Position sizing ──
            lot_info  = None
            execution = None

            if not guard["skip"] and mode == "paper":
                price_val = price_data.get("price", 2000.0)
                lot_info  = calc_lot(equity, guard["margin_used"], asset, price_val)
                execution = simulate_paper_execution(
                    asset, tf, price_val, lot_info["lot"], guard["margin_used"])
                open_positions = min(open_positions + 1, MAX_POSITIONS)
                ks.update(
                    success=(execution["retcode"] == 10009),
                    pnl_usd=execution.get("pnl_usd", 0),
                )

            # ── Construir e salvar AnalysisReport ──
            report = build_paper_report(
                asset, tf, mode, harmonic, price_data, guard, execution, lot_info)

            out_f = out_dir / f"PaperReport_{asset}_{tf}.json"
            with open(out_f, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            stats.record(report)
            action = report["signal"]["action"]
            cycle_ms = round((time.perf_counter() - t_cycle) * 1000, 1)

            if execution:
                log.info("[%s %s] %s | hr134=%.2f%% IC=[%s] lot=%.2f "
                         "slip=%.2f pts PnL=%.2f USD lat_net=%.0fms | SHA3=%s...",
                         asset, tf, action, hr_real,
                         report["binomial_ic_95"]["interval"],
                         lot_info["lot"], execution["slippage_pts"],
                         execution["pnl_usd"], execution["latency_ms"],
                         report["checksum"][:16])
            else:
                log.info("[%s %s] %s | hr134=%.2f%% IC=[%s] margin=%.1fpts SHA3=%s...",
                         asset, tf, action, hr_real,
                         report["binomial_ic_95"]["interval"],
                         guard["margin_used"], report["checksum"][:16])

            log.info("[%s %s] Ciclo total: %.0f ms", asset, tf, cycle_ms)

            all_reports.append({
                "asset": asset, "timeframe": tf, "status": action,
                "hit_rate_134": hr_real,
                "ic_95": report["binomial_ic_95"]["interval"],
                "margin_used": guard["margin_used"],
                "lot": lot_info["lot"] if lot_info else None,
                "pnl_usd": execution.get("pnl_usd") if execution else None,
                "slippage_pts": execution.get("slippage_pts") if execution else None,
                "checksum": report["checksum"][:24],
            })

    # ─── Skip Table ──────────────────────────────────────────────────────────
    skip_out = AUDIT_PAPER / "skip_table.json"
    skip_data = {"generated": datetime.now(timezone.utc).isoformat(), "skips": skip_table}
    sjb = json.dumps(skip_data, indent=2).encode("utf-8")
    skip_data["checksum"] = sha3(sjb)
    with open(skip_out, "w", encoding="utf-8") as f:
        json.dump(skip_data, f, indent=2, ensure_ascii=False)

    # ─── Online Statistics Summary ────────────────────────────────────────────
    stat_sum = stats.summary()
    log.info("── ESTATÍSTICAS ONLINE ──────────────────────────────────────────")
    for k, v in stat_sum.items():
        log.info("  %-25s : %s", k, v)

    # ─── Summary Final ───────────────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    summary = {
        "mode":          mode,
        "generated":     now,
        "equity_demo":   equity,
        "total_cycles":  len(all_reports),
        "kill_switch":   ks.triggered,
        "ks_reason":     ks.reason,
        "daily_pnl_usd": round(ks.daily_pnl, 2),
        "online_stats":  stat_sum,
        "results":       all_reports,
        "log_file":      str(log_file),
    }
    sb = json.dumps(summary, indent=2).encode("utf-8")
    summary["checksum"] = sha3(sb)
    sum_out = AUDIT_PAPER / "paper_summary.json"
    with open(sum_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info("=" * 72)
    log.info("%s LOOP CONCLUÍDO | cycles=%d | KS=%s | PnL=%.2f USD",
             mode.upper(), len(all_reports), ks.triggered, ks.daily_pnl)
    log.info("SHA3 summary: %s", summary["checksum"])
    log.info("Artifacts: %s", AUDIT_PAPER)
    log.info("=" * 72)
    return summary


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TIER1 = sorted(TIER1_ASSETS)
    parser = argparse.ArgumentParser(description="OMEGA Shadow/Paper Loop v2.0")
    parser.add_argument("--mode",       choices=["shadow", "paper"], default="shadow")
    parser.add_argument("--ativos",     nargs="+", default=TIER1)
    parser.add_argument("--timeframes", nargs="+", default=["H1", "H4"])
    parser.add_argument("--equity",     type=float, default=DEMO_EQUITY_USD)
    args = parser.parse_args()

    try:
        result = run_loop(args.ativos, args.timeframes, args.mode, args.equity)
        sys.exit(0 if not result["kill_switch"] else 1)
    except Exception:
        log.critical("ERRO CRÍTICO:\n%s", traceback.format_exc())
        sys.exit(2)
