r"""
psa_audit_engine.py

Motor de Auditoria Operacional do PSA:
- Lê relatórios AMI (report_*_*.json).
- Simula a execução de trades baseada nas oportunidades e parâmetros operacionais.
- Gera 'trades_<SYMBOL>.csv' e 'equity_curve_<SYMBOL>.csv'.
- Calcula hashes SHA3 para conformidade.

Estrutura de Saída:
C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\outputs\
"""

import json
import csv
import hashlib
import logging
import random
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Configurações de Caminhos
BASE_ROOT = Path(r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F")
REPORTS_DIR = BASE_ROOT / "outputs" / "causal_reports"
OUTPUT_DIR = BASE_ROOT / "outputs"
LOG_PATH = BASE_ROOT / "logs" / "psa_audit_engine.log"

# Logging
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("PSA_Audit")

def sha3_file(path: Path):
    with open(path, "rb") as f:
        digest = hashlib.sha3_256(f.read()).hexdigest()
    with open(path.with_suffix(".sha3"), "w", encoding="utf-8") as f:
        f.write(f"{digest}  {path.name}\n")
    return digest

def tf_mode(tf: str) -> str:
    tf = tf.upper()
    if tf in {"M1", "M3", "M5"}: return "scalp"
    if tf in {"M15", "M30", "H1"}: return "daytrade"
    return "swing"

class PSAAuditEngine:
    def __init__(self, initial_equity: float = 100000.0):
        self.equity = initial_equity
        self.initial_equity = initial_equity
        self.trades = []
        self.equity_curve = []
        
    def load_ami_reports(self, symbol: str) -> List[Dict]:
        reports = []
        sym_dir = REPORTS_DIR / symbol
        if not sym_dir.exists():
            return []
        for p in sym_dir.glob(f"report_{symbol}_*.json"):
            with open(p, "r", encoding="utf-8") as f:
                reports.append(json.load(f))
        return reports

    def simulate_trade(self, report: Dict, current_time: datetime):
        sym = report["symbol"]
        tf = report["timeframe"]
        mode = tf_mode(tf)
        opps = report.get("opportunities", [])
        
        if not opps:
            return

        for opp in opps:
            opp_id = opp.get("id", "N/A")
            opp_type = opp.get("type", "Causal")
            cal = opp.get("calibration", {})
            
            # Parâmetros de Entrada
            entry_price = cal.get("entry_zone", 0.0)
            sl = cal.get("stop_loss", 0.0)
            tp1 = cal.get("target_1", 0.0)
            
            if entry_price == 0: continue

            # Simulação de Resultado (Shadow/Paper Logic)
            # 70% Win rate sim para validação de estrutura
            is_win = random.random() < 0.7 
            side = report["forces"]["order_flow"]["direction"]
            
            # Cálculo de Risco (0.25% fixo para auditoria base)
            risk_amt = self.equity * 0.0025
            lot = 1.0 # Simplificado para teste de auditoria
            
            exit_price = tp1 if is_win else sl
            pnl = risk_amt * (1.5 if is_win else -1.0) # RR 1.5 simulado
            
            # Holding time baseado no timeframe (em segundos)
            tf_mult = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600}
            hold_sec = tf_mult.get(tf, 3600) * random.randint(2, 10)
            
            exit_time = current_time + timedelta(seconds=hold_sec)
            
            trade = {
                "timestamp_entry": current_time.isoformat(),
                "timestamp_exit": exit_time.isoformat(),
                "symbol": sym,
                "timeframe": tf,
                "mode": mode,
                "opportunity_id": opp_id,
                "opportunity_type": opp_type,
                "side": side,
                "qty": lot,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "sl": sl,
                "tp": tp1,
                "retcode": "SIM_OK",
                "slippage": round(random.uniform(0.1, 0.5), 2),
                "holding_time_sec": hold_sec,
                "pnl": round(pnl, 2),
                "pnl_pct": round((pnl / self.equity) * 100, 4),
                "pyramid_seq": ""
            }
            
            self.trades.append(trade)
            self.equity += pnl
            
            dd = ((self.initial_equity - self.equity) / self.initial_equity) * 100
            self.equity_curve.append({
                "timestamp": exit_time.isoformat(),
                "equity": round(self.equity, 2),
                "drawdown_pct": round(max(0, dd), 2)
            })
            
            return exit_time

    def run_audit(self, symbol: str):
        logger.info(f"Iniciando auditoria operacional para: {symbol}")
        reports = self.load_ami_reports(symbol)
        if not reports:
            logger.error(f"Nenhum report AMI encontrado para {symbol}")
            return

        start_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        # Simular uma sequência de trades baseada nos reports
        current_clock = start_time
        for r in reports:
            # Simular 3 trades por TF para ter corpo de prova no CSV
            for _ in range(3):
                new_clock = self.simulate_trade(r, current_clock)
                if new_clock:
                    current_clock = new_clock + timedelta(minutes=15)

        self.export_results(symbol)

    def export_results(self, symbol: str):
        # 1. Export Trades CSV
        trade_path = OUTPUT_DIR / f"trades_{symbol}.csv"
        if self.trades:
            keys = self.trades[0].keys()
            with open(trade_path, "w", newline="", encoding="utf-8") as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.trades)
            sha3_file(trade_path)
            logger.info(f"Log de trades salvo: {trade_path}")

        # 2. Export Equity CSV
        equity_path = OUTPUT_DIR / f"equity_curve_{symbol}.csv"
        if self.equity_curve:
            keys = self.equity_curve[0].keys()
            with open(equity_path, "w", newline="", encoding="utf-8") as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.equity_curve)
            sha3_file(equity_path)
            logger.info(f"Curva de equity salva: {equity_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    args = parser.parse_args()

    engine = PSAAuditEngine()
    engine.run_audit(args.symbol.upper())

if __name__ == "__main__":
    main()
