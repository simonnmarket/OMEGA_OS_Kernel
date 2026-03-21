#!/usr/bin/env python3
"""
psa_run_ami_calibration.py

Script único para o PSA:
- Lê relatórios AMI já gerados (report_*_*.json) em uma pasta de entrada.
- Extrai mach_number, confidence_score e opportunities (se estiverem em report_json).
- Gera recomendações operacionais (risk/SL/TP) por símbolo/TF.
- Salva saída, hash SHA3-256 e log na árvore da Auditoria PARR-F.

Uso (padrões já apontam para a árvore do PSA):
  python psa_run_ami_calibration.py

Ou especificando caminhos:
  python psa_run_ami_calibration.py --reports_dir "<pasta com reports AMI>" --output "<arquivo de saída>"
"""

import argparse
import json
import logging
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

# Raiz PSA
BASE_ROOT = Path(r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F")
# Nota: Ajustado para refletir a pasta de saída do batch runner anterior para compatibilidade automática
DEFAULT_REPORTS_DIR = BASE_ROOT / "outputs" / "causal_reports"  
DEFAULT_OUTPUT_PATH = BASE_ROOT / "outputs" / "ami_ops_calibration.json"
DEFAULT_LOG_PATH = BASE_ROOT / "logs" / "psa_run_ami_calibration.log"

# Logging
DEFAULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DEFAULT_LOG_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def load_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    reports = []
    loaded, skipped = 0, 0
    if not reports_dir.exists():
        logger.error(f"Diretorio de relatorios nao encontrado: {reports_dir}")
        return []
        
    for path in reports_dir.rglob("report_*_*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "symbol" not in data or "timeframe" not in data:
                logger.warning(f"Schema inválido (sem symbol/timeframe): {path}")
                skipped += 1
                continue
            # Se houver report_json serializado, tentar extrair opportunities e mach/confidence
            if "report_json" in data and isinstance(data["report_json"], str):
                try:
                    rj = json.loads(data["report_json"])
                    if "opportunities" not in data and "opportunities" in rj:
                        data["opportunities"] = rj["opportunities"]
                    if "mach_number" not in data and "mach_number" in rj:
                        data["mach_number"] = rj["mach_number"]
                    if "confidence_score" not in data and "confidence_score" in rj:
                        data["confidence_score"] = rj["confidence_score"]
                except Exception:
                    pass
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


def tf_mode(tf: str) -> str:
    tf = tf.upper()
    if tf in {"M1", "M3", "M5"}:
        return "scalp"
    if tf in {"M15", "M30", "H1"}:
        return "daytrade"
    if tf in {"H4", "D1", "W1", "MN1"}:
        return "swing"
    return "unknown"


def risk_reco(mach: float, status: str) -> float:
    status = (status or "").lower()
    if status == "abort_mission" or mach > 1.5:
        return 0.0
    if status == "alert" or mach > 1.2:
        return 0.10
    if mach > 1.0:
        return 0.15
    return 0.25


def max_positions(mode: str) -> int:
    if mode == "scalp":
        return 15
    if mode == "daytrade":
        return 10
    if mode == "swing":
        return 5
    return 5


def sl_tp_reco(opps: List[Dict[str, Any]]) -> Dict[str, Any]:
    if opps:
        opp = opps[0]
        cal = opp.get("calibration", {})
        return {
            "entry_zone": cal.get("entry_zone"),
            "stop_loss": cal.get("stop_loss"),
            "target_1": cal.get("target_1"),
            "target_2": cal.get("target_2"),
            "max_exposure_pct": cal.get("max_exposure_pct"),
            "timing_candles": cal.get("timing_candles"),
            "rr_suggested": {"tp1_rr": 1.5, "tp2_rr": 3.0},
        }
    return {
        "entry_zone": None,
        "stop_loss": None,
        "target_1": None,
        "target_2": None,
        "max_exposure_pct": None,
        "timing_candles": None,
        "rr_suggested": {"tp1_rr": 1.5, "tp2_rr": 3.0},
    }


def analyze_reports(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    recos = []
    sym_summary = defaultdict(lambda: {"count": 0, "mach": [], "confidence": [], "status": defaultdict(int)})

    for r in reports:
        sym = r.get("symbol")
        tf = r.get("timeframe")
        status = (r.get("status") or "").lower()
        mach = r.get("mach_number") or 0.0
        conf = r.get("confidence_score") or 0.0
        opps = r.get("opportunities") or []

        mode = tf_mode(tf)
        risk = risk_reco(mach, status)
        mp = max_positions(mode)
        sltp = sl_tp_reco(opps)

        recos.append({
            "symbol": sym,
            "timeframe": tf,
            "mode": mode,
            "status": status,
            "mach_number": mach,
            "confidence_score": conf,
            "risk_per_trade_pct": risk,
            "max_positions": mp,
            "sl_tp": sltp,
            "opportunities": len(opps),
        })

        sym_summary[sym]["count"] += 1
        sym_summary[sym]["mach"].append(mach)
        sym_summary[sym]["confidence"].append(conf)
        sym_summary[sym]["status"][status] += 1

    summary_out = {}
    for sym, vals in sym_summary.items():
        summary_out[sym] = {
            "count": vals["count"],
            "mach_mean": sum(vals["mach"]) / len(vals["mach"]) if vals["mach"] else 0.0,
            "confidence_mean": sum(vals["confidence"]) / len(vals["confidence"]) if vals["confidence"] else 0.0,
            "status_counts": dict(vals["status"]),
        }

    return {"recommendations": recos, "summary": summary_out}


def main():
    parser = argparse.ArgumentParser(description="PSA AMI Ops Calibration (leitura de reports AMI)")
    parser.add_argument("--reports_dir", type=str, default=str(DEFAULT_REPORTS_DIR), help="Pasta base dos relatórios AMI (recursiva)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH), help="Arquivo de saída")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir).resolve()
    output_path = Path(args.output).resolve()

    reports = load_reports(reports_dir)
    if not reports:
        logger.error(f"Nenhum relatório válido encontrado em {reports_dir}")
        return

    out_data = analyze_reports(reports)
    out_data["metadata"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "psa_run_ami_calibration_v1.0",
        "reports_dir": str(reports_dir),
        "n_reports_processed": len(reports),
        "output_path": str(output_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    with open(output_path, "rb") as f:
        digest = hashlib.sha3_256(f.read()).hexdigest()
    hash_path = output_path.with_suffix(".sha3")
    with open(hash_path, "w", encoding="utf-8") as f:
        f.write(f"{digest}  {output_path.name}\n")

    logger.info(f"AMI ops calibration salva em: {output_path}")
    logger.info(f"SHA3-256: {digest}")
    logger.info(f"Hash salvo em: {hash_path}")


if __name__ == "__main__":
    main()
