#!/usr/bin/env python3
"""
omega_turing_calibrate.py

Agrupa relatórios causais (gerados pelo omega_turing_batch.py) e produz
um arquivo de calibração agregada por símbolo e timeframe.

Entrada:
  - reports/causal/**/report_<SYMBOL>_<TF>.json

Saída:
  - reports/causal/calibration_params.json
    Contém estatísticas resumidas por símbolo/TF e sinais de viés/riscos.

Uso:
  python omega_turing_calibrate.py
  python omega_turing_calibrate.py --reports_dir ./reports/causal --output ./reports/causal/calibration_params.json
"""

import argparse
import json
import logging
import hashlib
import math
from collections import defaultdict, Counter
from pathlib import Path
from statistics import mean
from typing import Dict, List, Any
from datetime import datetime, timezone
from scipy import stats

# Novas raízes (auditoria central)
BASE_ROOT = Path("C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria PARR-F")
DEFAULT_REPORTS_DIR = BASE_ROOT / "outputs" / "causal_reports"
DEFAULT_OUTPUT_PATH = BASE_ROOT / "outputs" / "calibration_params.json"
DEFAULT_LOG_PATH = BASE_ROOT / "logs" / "omega_turing_calibrate.log"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DEFAULT_LOG_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def safe_mean(vals: List[float]) -> float:
    return mean(vals) if vals else 0.0


def sign_bias(directions: List[str], threshold: float = 0.5) -> str:
    """
    Retorna bullish/bearish apenas se a proporção superar threshold; caso contrário, neutral.
    """
    c = Counter(directions)
    total = sum(c.values())
    if total == 0:
        return "neutral"
    bull = c.get("bullish", 0) / total
    bear = c.get("bearish", 0) / total
    if bull >= threshold and bull > bear:
        return "bullish"
    if bear >= threshold and bear > bull:
        return "bearish"
    return "neutral"


def load_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    reports = []
    loaded, skipped = 0, 0
    if not reports_dir.exists():
        logger.error(f"Diretorio de relatorios nao existe: {reports_dir}")
        return []
        
    for path in reports_dir.rglob("report_*_*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validação mínima
            if "symbol" not in data or "timeframe" not in data:
                logger.warning(f"Schema inválido (sem symbol/timeframe): {path}")
                skipped += 1
                continue
            reports.append(data)
            loaded += 1
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido em {path}: {e}")
            skipped += 1
        except Exception as e:
            logger.error(f"Erro ao carregar {path}: {type(e).__name__}: {e}")
            skipped += 1
    logger.info(f"Carregados: {loaded} | Ignorados: {skipped}")
    return reports


def aggregate(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    agg: Dict[tuple, Dict[str, List]] = defaultdict(lambda: defaultdict(list))

    for r in reports:
        sym = r.get("symbol")
        tf = r.get("timeframe")
        forces = r.get("forces", {})
        if not sym or not tf:
            continue

        of = forces.get("order_flow", {})
        vf = forces.get("volume_force", {})
        mf = forces.get("momentum_force", {})
        en = forces.get("energy", {})

        agg[(sym, tf)]["order_flow_mag"].append(float(of.get("magnitude", 0.0)))
        if of.get("direction"):
            agg[(sym, tf)]["order_flow_dir"].append(of.get("direction"))

        agg[(sym, tf)]["volume_ratio"].append(float(vf.get("volume_ratio", 0.0)))
        if vf.get("wyckoff"):
            agg[(sym, tf)]["wyckoff"].append(vf.get("wyckoff"))

        agg[(sym, tf)]["momentum_accel"].append(float(mf.get("acceleration", 0.0)))
        if mf.get("direction"):
            agg[(sym, tf)]["momentum_dir"].append(mf.get("direction"))

        agg[(sym, tf)]["energy_kin"].append(float(en.get("kinetic", 0.0)))
        agg[(sym, tf)]["energy_pot"].append(float(en.get("potential", 0.0)))

    summary: Dict[str, Any] = {}
    for (sym, tf), vals in agg.items():
        of_bias = sign_bias(vals.get("order_flow_dir", []))
        mom_bias = sign_bias(vals.get("momentum_dir", []))
        wyc = Counter(vals.get("wyckoff", []))
        wyc_top = wyc.most_common(1)[0][0] if wyc else "neutral"

        of_mags = vals.get("order_flow_mag", [])
        of_mean = safe_mean(of_mags)
        of_ic95 = None
        if len(of_mags) >= 30:
            sem = stats.sem(of_mags)
            ic = stats.t.interval(0.95, len(of_mags) - 1, loc=of_mean, scale=sem)
            of_ic95 = {"lower": float(ic[0]), "upper": float(ic[1])}

        summary.setdefault(sym, {})
        summary[sym][tf] = {
            "count": len(of_mags),
            "order_flow_mag_mean": float(of_mean),
            "order_flow_mag_ic95": of_ic95,
            "order_flow_mag_n": len(of_mags),
            "order_flow_bias": of_bias,
            "volume_ratio_mean": float(safe_mean(vals.get("volume_ratio", []))),
            "volume_ratio_n": len(vals.get("volume_ratio", [])),
            "wyckoff_mode": wyc_top,
            "wyckoff_counts": dict(wyc),
            "momentum_accel_mean": float(safe_mean(vals.get("momentum_accel", []))),
            "momentum_bias": mom_bias,
            "energy_kin_mean": float(safe_mean(vals.get("energy_kin", []))),
            "energy_pot_mean": float(safe_mean(vals.get("energy_pot", []))),
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description="Agregador de relatórios causais para calibração")
    parser.add_argument("--reports_dir", type=str, default=str(DEFAULT_REPORTS_DIR), help="Pasta base dos relatórios")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH), help="Arquivo de saída")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir).resolve()
    output_path = Path(args.output).resolve()
    
    # Garantir pastas
    output_path.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Iniciando Calibracao Turing...")
    reports = load_reports(reports_dir)
    if not reports:
        logger.error(f"Nenhum relatório válido encontrado em {reports_dir}")
        return

    summary = aggregate(reports)

    output_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "omega_turing_calibrate_v1.1",
            "n_reports_processed": len(reports),
            "reports_dir": str(reports_dir),
            "output_path": str(output_path),
        },
        "calibration": summary,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # SHA3-256 do output
    with open(output_path, "rb") as f:
        output_hash = hashlib.sha3_256(f.read()).hexdigest()
    hash_path = output_path.with_suffix(".sha3")
    with open(hash_path, "w", encoding="utf-8") as f:
        f.write(f"{output_hash}  {output_path.name}\n")

    logger.info(f"Calibração agregada salva em: {output_path}")
    logger.info(f"SHA3-256 do output: {output_hash}")
    logger.info(f"Hash salvo em: {hash_path}")


if __name__ == "__main__":
    main()
