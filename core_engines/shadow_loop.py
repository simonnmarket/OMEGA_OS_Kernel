#!/usr/bin/env python3
"""
OMEGA SHADOW/PAPER LOOP ENGINE
OMEGA Intelligence OS | nebular-kuiper\core_engines\shadow_loop.py

Modo SHADOW  : gera sinais, loga, NÃO envia ordens.
Modo PAPER   : envia ordens demo (lote 0.01) com kill switch.
Kill switch  : DD diário >= 5% OU 3 falhas consecutivas.

Uso:
  python shadow_loop.py --mode shadow --ativos XAUUSD GBPUSD --timeframes H1
  python shadow_loop.py --mode paper  --ativos XAUUSD --timeframes H1 H4
"""

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from math import sqrt

# ─── Caminhos ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
CORE = Path(__file__).resolve().parent
OHLCV = Path(r"C:\OMEGA_PROJETO\OHLCV_DATA")
SHADOW_AUDIT = ROOT / "audit" / "shadow"
SHADOW_AUDIT.mkdir(parents=True, exist_ok=True)

# ─── Logging duplo (stdout + arquivo) ───────────────────────────────────────
log_file = SHADOW_AUDIT / f"shadow_loop_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("SHADOW")

# ─── Guardrails ─────────────────────────────────────────────────────────────
TIER1_ASSETS = {
    "XAUUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY",
    "ETHUSD", "US500", "SOLUSD", "DOGUSD",
}
HIT_RATE_MIN = 80.0      # % — abaixo disso: skip
MACH_MAX     = 1.5       # Mach > 1.5: skip
DD_DAILY_MAX = 0.05      # 5% drawdown diário: kill switch
MAX_CONSEC_FAIL = 3      # 3 falhas consecutivas: kill switch

# ─── Margens dinâmicas (carregadas do JSON gerado pelo ATR) ─────────────────
def load_dynamic_margins():
    p = ROOT / "audit" / "dynamic_margins.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("margins", {})
    return {}

# ─── Guardrails — verificar se pode operar ─────────────────────────────────
def check_guardrails(asset: str, timeframe: str,
                     hit_rate_134: float, mach: float,
                     dynamic_margins: dict) -> dict:
    reasons = []

    if asset in TIER1_ASSETS:
        tier = "T1"
    elif hit_rate_134 >= HIT_RATE_MIN:
        tier = "T2"
    else:
        tier = "T3"
        reasons.append(f"hit_rate_134={hit_rate_134:.2f}% < {HIT_RATE_MIN}%")

    if mach > MACH_MAX:
        reasons.append(f"Mach={mach:.2f} > {MACH_MAX}")

    if asset == "EURUSD":
        reasons.append("EURUSD: grafico_linha ausente — aguardando dados")

    margin = 150.0  # default
    dm = dynamic_margins.get(asset, {}).get(timeframe)
    if dm and isinstance(dm, dict):
        margin = dm.get("margin_dynamic", 150.0)

    skip = len(reasons) > 0
    return {
        "asset":        asset,
        "timeframe":    timeframe,
        "tier":         tier,
        "hit_rate_134": hit_rate_134,
        "mach":         mach,
        "margin_used":  margin,
        "skip":         skip,
        "skip_reasons": reasons,
    }

# ─── Rodar Motor Harmônico V3 ─────────────────────────────────────────────────
def run_harmonic(asset: str, timeframe: str, margin: float) -> dict | None:
    out_dir = SHADOW_AUDIT / f"{asset}_{timeframe}"
    out_dir.mkdir(parents=True, exist_ok=True)
    motor = CORE / "omega_harmonic_engine_v3.py"

    cmd = [
        sys.executable, str(motor),
        "--symbol", asset,
        "--timeframe", timeframe,
        "--base_path", str(OHLCV),
        "--margin", str(margin),
        "--lookback", "3",
        "--lookahead", "5",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=str(out_dir), timeout=300)
        if r.returncode != 0:
            log.error("[%s %s] Motor V3 falhou (exit %d): %s",
                      asset, timeframe, r.returncode, r.stderr[:200])
            return None
        jf = out_dir / f"harmonic_events_{asset}_{timeframe}.json"
        if not jf.exists():
            log.error("[%s %s] JSON não encontrado: %s", asset, timeframe, jf)
            return None
        with open(jf, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error("[%s %s] Exceção motor: %s", asset, timeframe, e)
        return None

# ─── Integrar Price Engine ────────────────────────────────────────────────────
def get_price_result():
    sys.path.insert(0, str(CORE))
    from omega_module_v553 import DCECalibratedPriceEngine, ModuleConfig
    engine = DCECalibratedPriceEngine(ModuleConfig())
    return engine.compute_price(Q=1000, PBoc=0.0, volume_anomaly=0.1)

# ─── Gerar AnalysisReport com ambos engines ────────────────────────────────────
def build_shadow_report(asset: str, timeframe: str,
                        harmonic: dict, price: dict,
                        guardrail: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    m = harmonic.get("engines", {}).get("harmonic", {}).get("metrics", {})
    s134 = m.get("134_stats", {})
    s34  = m.get("34_stats",  {})

    report = {
        "mission_id":       f"SHADOW-{asset}-{timeframe}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "asset":            asset,
        "timeframe":        timeframe,
        "status":           "COMPLETED" if harmonic.get("status") == "COMPLETED" else "FAILED",
        "created_at":       now,
        "agent_version":    "shadow_loop_v1.0",
        "omega_integration": True,
        "mode":             "shadow",
        "guardrail":        guardrail,
        "engines": {
            "harmonic": {
                "metrics": {"34_stats": s34, "134_stats": s134}
            },
            "price": {
                "price":                  price.get("price"),
                "base_price":             price.get("base_price"),
                "flash_crash_adjustment": price.get("flash_crash_adjustment"),
                "components":             price.get("components"),
                "metadata": {k: v for k, v in price.get("metadata", {}).items()
                             if k in ["params_checksum", "rmse_expected", "r_squared"]},
            }
        },
        "signal": {
            "action":       "SKIP" if guardrail["skip"] else "MONITOR",
            "skip_reasons": guardrail["skip_reasons"],
            "margin_used":  guardrail["margin_used"],
            "tier":         guardrail["tier"],
        },
    }
    jb = json.dumps(report, indent=2).encode("utf-8")
    report["checksum"] = hashlib.sha3_256(jb).hexdigest()
    return report

# ─── Kill Switch ─────────────────────────────────────────────────────────────
class KillSwitch:
    def __init__(self):
        self.consec_fail = 0
        self.daily_loss  = 0.0
        self.triggered   = False

    def check(self, success: bool, pnl_pct: float = 0.0) -> bool:
        if self.triggered:
            return True
        if not success:
            self.consec_fail += 1
        else:
            self.consec_fail = 0
        self.daily_loss += pnl_pct
        if self.consec_fail >= MAX_CONSEC_FAIL:
            log.critical("KILL SWITCH: %d falhas consecutivas — loop encerrado", self.consec_fail)
            self.triggered = True
        if abs(self.daily_loss) >= DD_DAILY_MAX:
            log.critical("KILL SWITCH: DD diário %.2f%% >= %.0f%% — loop encerrado",
                         self.daily_loss*100, DD_DAILY_MAX*100)
            self.triggered = True
        return self.triggered

# ─── Loop Principal ───────────────────────────────────────────────────────────
def run_shadow_loop(ativos, timeframes, mode="shadow"):
    log.info("=" * 70)
    log.info("OMEGA SHADOW LOOP | mode=%s | %d ativos × %d TFs", mode, len(ativos), len(timeframes))
    log.info("Guardrail: hit_rate_134 >= %.0f%% | Mach <= %.1f | DD <= %.0f%% | MaxConsecFail=%d",
             HIT_RATE_MIN, MACH_MAX, DD_DAILY_MAX*100, MAX_CONSEC_FAIL)
    log.info("=" * 70)

    dynamic_margins = load_dynamic_margins()
    price_result    = get_price_result()
    kill            = KillSwitch()
    skip_table      = []
    reports         = []
    success_count   = fail_count = skip_count = 0

    for asset in ativos:
        for tf in timeframes:
            if kill.triggered:
                log.critical("[%s %s] KILL SWITCH ativo — abortando.", asset, tf)
                break

            log.info("[%s %s] Iniciando ciclo...", asset, tf)

            # Guardrail preliminar — sem rodar motor
            prelim = check_guardrails(asset, tf, 100.0, 1.0, dynamic_margins)
            if asset not in TIER1_ASSETS and asset != "EURUSD":
                # Carrega hit_rate real do gamaray se disponível
                rep_f = ROOT / "audit" / f"{asset}_{tf}" / f"AnalysisReport_{asset}_{tf}.json"
                if rep_f.exists():
                    with open(rep_f, encoding="utf-8") as f2:
                        prev = json.load(f2)
                    hr = prev.get("engines", {}).get("harmonic", {}).get("metrics", {}).get("134_stats", {}).get("hit_rate", 100.0)
                    prelim = check_guardrails(asset, tf, hr, 1.0, dynamic_margins)

            if prelim["skip"]:
                log.warning("[%s %s] SKIP — %s", asset, tf, prelim["skip_reasons"])
                skip_count += 1
                skip_table.append(prelim)
                reports.append({"asset": asset, "timeframe": tf, "status": "SKIP",
                                 "reasons": prelim["skip_reasons"]})
                kill.check(success=True)
                continue

            # Rodar motor harmônico
            harmonic = run_harmonic(asset, tf, prelim["margin_used"])
            if harmonic is None:
                fail_count += 1
                if kill.check(success=False):
                    break
                continue

            # Guardrail final com dados reais
            s134 = harmonic.get("engines", {}).get("harmonic", {}).get("metrics", {}).get("134_stats", {})
            hr_real = s134.get("hit_rate", 0.0)
            guardrail = check_guardrails(asset, tf, hr_real, 1.0, dynamic_margins)

            report = build_shadow_report(asset, tf, harmonic, price_result, guardrail)

            # Salvar relatório
            out_dir = SHADOW_AUDIT / f"{asset}_{tf}"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_f = out_dir / f"ShadowReport_{asset}_{tf}.json"
            with open(out_f, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            action = report["signal"]["action"]
            log.info("[%s %s] %s | hr134=%.2f%% | margin=%.1f | SHA3=%s...",
                     asset, tf, action, hr_real, guardrail["margin_used"], report["checksum"][:16])

            success_count += 1
            reports.append({"asset": asset, "timeframe": tf, "status": action,
                             "hit_rate_134": hr_real, "margin_used": guardrail["margin_used"],
                             "checksum": report["checksum"]})
            kill.check(success=True)

    # ─── Tabela de Skips ────────────────────────────────────────────────────
    skip_out = SHADOW_AUDIT / "skip_table.json"
    skip_data = {"generated": datetime.now(timezone.utc).isoformat(), "skips": skip_table}
    sjb = json.dumps(skip_data, indent=2).encode("utf-8")
    skip_data["checksum"] = hashlib.sha3_256(sjb).hexdigest()
    with open(skip_out, "w", encoding="utf-8") as f:
        json.dump(skip_data, f, indent=2, ensure_ascii=False)

    # ─── Summary ────────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    summary = {
        "mode":         mode,
        "generated":    now,
        "total":        success_count + fail_count + skip_count,
        "completed":    success_count,
        "failed":       fail_count,
        "skipped":      skip_count,
        "kill_switch":  kill.triggered,
        "log_file":     str(log_file),
        "results":      reports,
    }
    sb = json.dumps(summary, indent=2).encode("utf-8")
    summary["checksum"] = hashlib.sha3_256(sb).hexdigest()
    sum_out = SHADOW_AUDIT / "shadow_summary.json"
    with open(sum_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info("=" * 70)
    log.info("SHADOW LOOP CONCLUÍDO | OK=%d SKIP=%d FAIL=%d | KS=%s",
             success_count, skip_count, fail_count, kill.triggered)
    log.info("SHA3 summary: %s", summary["checksum"])
    log.info("Artifacts: %s", SHADOW_AUDIT)
    log.info("=" * 70)
    return summary


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    DEFAULT_ATIVOS = list(TIER1_ASSETS) + ["BTCUSD", "US100", "US30", "GER40", "HK50", "EURUSD"]
    DEFAULT_TFS    = ["H1", "H4"]

    parser = argparse.ArgumentParser(description="OMEGA Shadow/Paper Loop Engine")
    parser.add_argument("--mode",       choices=["shadow", "paper"], default="shadow")
    parser.add_argument("--ativos",     nargs="+", default=DEFAULT_ATIVOS)
    parser.add_argument("--timeframes", nargs="+", default=DEFAULT_TFS)
    args = parser.parse_args()

    try:
        result = run_shadow_loop(args.ativos, args.timeframes, args.mode)
        sys.exit(0 if not result["kill_switch"] else 1)
    except Exception:
        log.critical("ERRO CRÍTICO:\n%s", traceback.format_exc())
        sys.exit(2)
