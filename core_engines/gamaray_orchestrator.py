#!/usr/bin/env python3
"""
OPERAÇÃO GAMA-RAY — Varredura Harmônica Multi-Ativo / Multi-Timeframe
OMEGA Intelligence OS | OMEGA-AMI-V3-GAMARAY-2026-0320
Raiz: nebular-kuiper\core_engines\gamaray_orchestrator.py

Responsabilidades:
  1. Iterar sobre todos os pares (ativo, timeframe) disponíveis em OHLCV_DATA.
  2. Rodar omega_harmonic_engine_v3 para cada combinação.
  3. Integrar saída do DCE Price Engine (omega_module_v553) em engines.price.
  4. Calcular IC Binomial 95% (Wilson) para cada hit_rate_134.
  5. Sinalizar "Ativo Caótico" se hit_rate_134 < 80% E Mach > 1.5.
  6. Gerar AnalysisReport JSON + Markdown por combinação em audit/{ATIVO}_{TF}/.
  7. Gerar relatório consolidado: gamaray_summary.json + gamaray_summary.md.
  8. SHA3-256 em todos os outputs.

Uso:
  python gamaray_orchestrator.py
  python gamaray_orchestrator.py --ativos XAUUSD BTCUSD --timeframes H1 H4
  python gamaray_orchestrator.py --base_path C:\OMEGA_PROJETO\OHLCV_DATA
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
from math import sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("gamaray_orchestrator.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("GAMARAY")

# ─── Caminhos ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent          # nebular-kuiper\
CORE = Path(__file__).resolve().parent                 # nebular-kuiper\core_engines\
BASE_PATH_DEFAULT = Path(r"C:\OMEGA_PROJETO\OHLCV_DATA")
AUDIT_ROOT = ROOT / "audit"

# ─── Ativos e Timeframes padrão ─────────────────────────────────────────────
DEFAULT_ATIVOS = [
    "XAUUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD",
    "USDJPY", "AUDUSD", "AUDJPY", "US500", "US100",
    "US30", "GER40", "HK50", "SOLUSD", "DOGUSD",
]
DEFAULT_TFS = ["D1", "H4", "H1", "M15"]


# ─── IC Binomial Wilson (95%) ────────────────────────────────────────────────
def wilson_ic(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Retorna (lower_bound, upper_bound) do IC Wilson 95%."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom  = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


# ─── Checksum SHA3-256 ───────────────────────────────────────────────────────
def sha3(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


# ─── Price Engine V553 ───────────────────────────────────────────────────────
def get_price_engine():
    sys.path.insert(0, str(CORE))
    from omega_module_v553 import DCECalibratedPriceEngine, ModuleConfig
    return DCECalibratedPriceEngine(ModuleConfig())


# ─── Rodar Motor Harmônico V3 ─────────────────────────────────────────────────
def run_harmonic(symbol: str, timeframe: str, base_path: Path,
                 margin: float, lookback: int, lookahead: int,
                 out_dir: Path) -> Optional[Dict]:
    """Executa omega_harmonic_engine_v3.py e retorna o JSON de resultado."""
    out_dir.mkdir(parents=True, exist_ok=True)
    motor = CORE / "omega_harmonic_engine_v3.py"

    cmd = [
        sys.executable, str(motor),
        "--symbol", symbol,
        "--timeframe", timeframe,
        "--base_path", str(base_path),
        "--margin", str(margin),
        "--lookback", str(lookback),
        "--lookahead", str(lookahead),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(out_dir), timeout=300
        )
        if result.returncode != 0:
            log.error("[%s %s] Motor retornou exit %d: %s",
                      symbol, timeframe, result.returncode, result.stderr[:300])
            return None

        # Ler JSON gerado
        json_file = out_dir / f"harmonic_events_{symbol}_{timeframe}.json"
        if not json_file.exists():
            log.error("[%s %s] JSON de output não encontrado: %s", symbol, timeframe, json_file)
            return None

        with open(json_file, encoding="utf-8") as f:
            return json.load(f)

    except subprocess.TimeoutExpired:
        log.error("[%s %s] Timeout (>300s)", symbol, timeframe)
        return None
    except Exception as e:
        log.error("[%s %s] Erro ao rodar motor: %s", symbol, timeframe, e)
        return None


# ─── Gerar AnalysisReport ─────────────────────────────────────────────────────
def build_report(symbol: str, timeframe: str,
                 harmonic_data: Dict, price_engine,
                 mach_number: float = 1.0) -> Dict:
    now = datetime.now(timezone.utc).isoformat()
    metrics = harmonic_data.get("engines", {}).get("harmonic", {}).get("metrics", {})
    s134 = metrics.get("134_stats", {})
    s34  = metrics.get("34_stats",  {})

    hits_134  = s134.get("hits", 0)
    total_134 = s134.get("total_touches", 1)
    hr_134    = s134.get("hit_rate", 0.0)
    lb, ub    = wilson_ic(hits_134, total_134)

    # Price engine
    try:
        price_out = price_engine.compute_price(Q=1000, PBoc=0.0, volume_anomaly=0.1)
        price_block = {
            "price":                  price_out["price"],
            "base_price":             price_out["base_price"],
            "flash_crash_adjustment": price_out["flash_crash_adjustment"],
            "components":             price_out["components"],
            "metadata": {k: v for k, v in price_out["metadata"].items()
                         if k in ["params_checksum", "rmse_expected", "r_squared"]},
        }
    except Exception as e:
        log.warning("[%s %s] Price engine falhou: %s", symbol, timeframe, e)
        price_block = {"error": str(e)}

    # Classificação flutter / trajetória
    flutter = "medium"
    if hr_134 >= 99:  flutter = "low"
    elif hr_134 >= 95: flutter = "medium"
    elif hr_134 >= 80: flutter = "high"
    else:              flutter = "critical"

    is_chaotic = hr_134 < 80.0 and mach_number > 1.5
    status = "COMPLETED" if harmonic_data.get("status") == "COMPLETED" else "FAILED"

    report = {
        "mission_id":        f"GAMARAY-{symbol}-{timeframe}-20260320",
        "asset":             symbol,
        "timeframe":         timeframe,
        "period_start":      str(harmonic_data.get("period_start", "")),
        "period_end":        str(harmonic_data.get("period_end", "")),
        "data_points":       harmonic_data.get("data_points", 0),
        "status":            status,
        "created_at":        now,
        "updated_at":        now,
        "agent_version":     "ami_analyzer_v3.0",
        "omega_integration": False,
        "confidence_score":  round(hr_134, 2),
        "mach_number":       mach_number,
        "dominant_cycle":    "34H" if hr_134 >= 95 else "UNDEFINED",
        "flutter_risk":      flutter,
        "trajectory_phase":  "descending",
        "is_chaotic":        is_chaotic,
        "checksum_sources":  harmonic_data.get("checksum_sources", {}),
        "binomial_ic_95": {
            "hits":          hits_134,
            "total":         total_134,
            "p_hat":         round(hits_134 / max(total_134, 1), 6),
            "lower_bound":   round(lb, 6),
            "upper_bound":   round(ub, 6),
            "interval":      f"[{lb*100:.4f}%, {ub*100:.4f}%]",
        },
        "engines": {
            "harmonic": {
                "metrics": {
                    "34_stats":  s34,
                    "134_stats": s134,
                }
            },
            "price": price_block,
        },
    }

    json_bytes = json.dumps(report, indent=2).encode("utf-8")
    report["checksum"] = sha3(json_bytes)
    report["report_json"] = json.dumps(report, indent=2)

    # Markdown
    md = f"""# GAMARAY — {symbol} {timeframe}
**Mission ID:** {report["mission_id"]}
**Status:** `{status}` | **Chaotic Flag:** `{"❌ YES" if is_chaotic else "✅ NO"}`
**Generated:** {now}

## Motores Harmônicos (V3)

| Nível   | Toques  | HIT    | BREAK | Hit Rate   |
|---------|---------|--------|-------|------------|
| EMA-34  | {s34.get("total_touches",0):,} | {s34.get("hits",0):,} | {s34.get("breaks",0)} | **{s34.get("hit_rate",0)}%** |
| EMA-134 | {total_134:,} | {hits_134:,} | {s134.get("breaks",0)} | **{hr_134}%** |

## IC Binomial 95% (EMA-134)
```
p_hat  = {report["binomial_ic_95"]["p_hat"]:.6f} ({hr_134}%)
IC 95% = {report["binomial_ic_95"]["interval"]}
```

## DCE Price Engine V5.5.3
**Preço calibrado:** {price_block.get("price", "N/A")} | **R²:** {price_block.get("metadata", {}).get("r_squared", "N/A")}

## Veredicto
**Flutter:** {flutter.upper()} | **Mach:** {mach_number} | **SHA3:** `{report["checksum"][:32]}...`
"""
    report["report_markdown"] = md
    return report


# ─── Orquestrador Principal ────────────────────────────────────────────────────
def orchestrate(ativos: List[str], timeframes: List[str], base_path: Path,
                margin: float, lookback: int, lookahead: int):
    log.info("=" * 70)
    log.info("OPERAÇÃO GAMA-RAY | %d ativos × %d timeframes = %d combinações",
             len(ativos), len(timeframes), len(ativos) * len(timeframes))
    log.info("=" * 70)

    price_engine = get_price_engine()
    summary = []
    success = fail = chaotic = 0

    for symbol in ativos:
        for tf in timeframes:
            log.info("[%s %s] Iniciando...", symbol, tf)
            out_dir = AUDIT_ROOT / f"{symbol}_{tf}"

            harmonic = run_harmonic(symbol, tf, base_path, margin, lookback, lookahead, out_dir)
            if harmonic is None:
                log.error("[%s %s] FALHOU — pulando.", symbol, tf)
                fail += 1
                summary.append({"asset": symbol, "timeframe": tf, "status": "FAILED"})
                continue

            report = build_report(symbol, tf, harmonic, price_engine)
            is_c = report.get("is_chaotic", False)

            # Salvar JSON
            out_json = out_dir / f"AnalysisReport_{symbol}_{tf}.json"
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            # Salvar Markdown
            out_md = out_dir / f"AnalysisReport_{symbol}_{tf}.md"
            with open(out_md, "w", encoding="utf-8") as f:
                f.write(report["report_markdown"])

            s = report["engines"]["harmonic"]["metrics"]
            log.info(
                "[%s %s] ✅ hr34=%.2f%% hr134=%.2f%% IC=[%s] chaotic=%s | SHA3=%s...",
                symbol, tf,
                s["34_stats"].get("hit_rate", 0),
                s["134_stats"].get("hit_rate", 0),
                report["binomial_ic_95"]["interval"],
                is_c,
                report["checksum"][:16],
            )

            summary.append({
                "asset":         symbol,
                "timeframe":     tf,
                "status":        report["status"],
                "hit_rate_34":   s["34_stats"].get("hit_rate"),
                "hit_rate_134":  s["134_stats"].get("hit_rate"),
                "ic_95":         report["binomial_ic_95"]["interval"],
                "is_chaotic":    is_c,
                "mach_number":   report["mach_number"],
                "checksum":      report["checksum"],
            })

            success += 1
            if is_c:
                chaotic += 1
                log.warning("[%s %s] ⚠️ ATIVO CAÓTICO: hr134=%.2f%% Mach=%.2f",
                            symbol, tf, s["134_stats"].get("hit_rate", 0), report["mach_number"])

    # ─── Relatório Consolidado ──────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    gamaray_summary = {
        "operation":   "GAMA-RAY",
        "generated":   now,
        "total":       success + fail,
        "success":     success,
        "failed":      fail,
        "chaotic":     chaotic,
        "results":     summary,
    }
    sb = json.dumps(gamaray_summary, indent=2).encode("utf-8")
    gamaray_summary["checksum"] = sha3(sb)

    out_summary = AUDIT_ROOT / "gamaray_summary.json"
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(gamaray_summary, f, indent=2, ensure_ascii=False)

    # Markdown consolidado
    rows = "\n".join(
        f"| {r['asset']} | {r['timeframe']} | {r['status']} | "
        f"{r.get('hit_rate_34','—')} | {r.get('hit_rate_134','—')} | "
        f"{r.get('ic_95','—')} | {'⚠️' if r.get('is_chaotic') else '✅'} |"
        for r in summary
    )
    md_summary = f"""# OPERAÇÃO GAMA-RAY — Relatório Consolidado
**Gerado:** {now}
**Total:** {success+fail} | **Sucesso:** {success} | **Falhas:** {fail} | **Caóticos:** {chaotic}

| Ativo | TF | Status | HR-34 | HR-134 | IC 95% | Flag |
|---|---|---|---|---|---|---|
{rows}

**SHA3-256 deste relatório:** `{gamaray_summary["checksum"]}`
"""
    out_md_summary = AUDIT_ROOT / "gamaray_summary.md"
    with open(out_md_summary, "w", encoding="utf-8") as f:
        f.write(md_summary)

    log.info("=" * 70)
    log.info("GAMA-RAY CONCLUÍDA | Sucesso: %d | Falhas: %d | Caóticos: %d", success, fail, chaotic)
    log.info("Summary JSON: %s | SHA3: %s", out_summary, gamaray_summary["checksum"])
    log.info("=" * 70)
    return gamaray_summary


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OPERAÇÃO GAMA-RAY — Varredura Harmônica Multi-Ativo")
    parser.add_argument("--ativos",     nargs="+", default=DEFAULT_ATIVOS)
    parser.add_argument("--timeframes", nargs="+", default=DEFAULT_TFS)
    parser.add_argument("--base_path",  default=str(BASE_PATH_DEFAULT))
    parser.add_argument("--margin",     type=float, default=150.0)
    parser.add_argument("--lookback",   type=int,   default=3)
    parser.add_argument("--lookahead",  type=int,   default=5)
    args = parser.parse_args()

    try:
        result = orchestrate(
            ativos=args.ativos,
            timeframes=args.timeframes,
            base_path=Path(args.base_path),
            margin=args.margin,
            lookback=args.lookback,
            lookahead=args.lookahead,
        )
        sys.exit(0 if result["failed"] == 0 else 1)
    except Exception:
        log.error("ERRO CRÍTICO:\n%s", traceback.format_exc())
        sys.exit(2)
