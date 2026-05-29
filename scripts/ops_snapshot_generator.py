#!/usr/bin/env python3
"""OPS Snapshot Generator — CEO-PSA-OPS-20260530 + CEO-ORDEM-THRESH-20260529"""
import json, re, os, sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

LOG_PATH = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/omega_24x7_runner.log")
SUMMARY_PATH = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/paper_summary.json")
LEDGER_PATH = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/positions_ledger.json")
SKIP_TABLE_PATH = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/skip_table.json")

def get_symbols_open():
    """Retorna lista de símbolos com posições abertas."""
    try:
        with open(LEDGER_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        positions = data.get('positions', {})
        symbols = set()
        for pos in positions.values():
            if isinstance(pos, dict) and pos.get('status') == 'open':
                symbols.add(pos.get('symbol', 'UNKNOWN'))
        return sorted(symbols)
    except Exception as e:
        return [f"ERROR:{e}"]

def get_realized_pnl():
    """Retorna realized PnL do ledger."""
    try:
        with open(LEDGER_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        return data.get('realized_pnl', 'N/A')
    except Exception as e:
        return f"ERROR:{e}"

def run_snapshot():
    if not LOG_PATH.exists():
        print("LOG nao encontrado")
        return

    # Read data sources
    try:
        with open(SUMMARY_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            summary = json.load(f)
    except:
        summary = {}

    try:
        with open(LEDGER_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            ledger = json.load(f)
    except:
        ledger = {}

    # Get latest executed/skipped from log (last 50 lines)
    last_exec = "N/A"
    last_skipped = "N/A"
    with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in reversed(lines[-50:]):
            if 'executed' in line and 'total_signals' not in line:
                last_exec = line.strip()
                break
        for line in reversed(lines[-50:]):
            if 'skipped' in line and 'total_signals' not in line:
                last_skipped = line.strip()
                break

    # G4 check: last SKIP (pre) after last reinicio
    # Find last reinicio marker
    last_restart = None
    with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in reversed(lines):
            if 'ROOT=' in line and 'mode=paper' in line:
                m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if m:
                    last_restart = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    break

    skip_62 = 0
    skip_65 = 0
    last_skip_line = "N/A"
    entries_frozen = 0
    model_dump = 0
    executed_gt0 = 0

    if last_restart:
        with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if m:
                    try:
                        ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                        if ts < last_restart:
                            continue
                    except:
                        pass
                if 'SKIP (pre)' in line:
                    last_skip_line = line.strip()[:250]
                    if '62.0%' in line:
                        skip_62 += 1
                    elif '65.0%' in line:
                        skip_65 += 1
                if 'executed' in line and 'total_signals' not in line:
                    val = re.search(r'executed\s*[:=]\s*(\d+)', line)
                    if val and int(val.group(1)) > 0:
                        executed_gt0 += 1
                if 'ENTRIES_FROZEN=1' in line:
                    entries_frozen += 1
                if 'model_dump' in line.lower() or "has no attribute" in line.lower():
                    model_dump += 1

    # G4 verdict
    if skip_62 > 0 or executed_gt0 > 0:
        g4 = 'PASS'
    elif skip_65 > 0:
        g4 = 'FAIL'
    else:
        g4 = 'CHECK (sem SKIP novo post-reinicio)'

    # ALERTS
    pos_n = ledger.get('n_positions', len(ledger.get('positions', {})))
    alerts = []
    if entries_frozen > 0:
        alerts.append(f"ALERTA: FREEZE={entries_frozen}")
    if model_dump > 0:
        alerts.append(f"ALERTA: MODEL_DUMP={model_dump}")
    if pos_n > 12:
        alerts.append(f"ALERTA: POS_N={pos_n} > 12")

    # Check runner alive (last log line within 5 min)
    runner_alive = True
    try:
        with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            last_line = None
            for line in f:
                last_line = line
            if last_line:
                m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', last_line)
                if m:
                    last_ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - last_ts).total_seconds() > 300:
                        runner_alive = False
                        alerts.append("ALERTA: RUNNER DOWN (log >5min)")
    except:
        pass

    # FLOW samples (last from log)
    flow_forex = "N/A"
    flow_crypto = "N/A"
    with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        for line in reversed(list(f)):
            if '[FLOW]' in line:
                if flow_forex == "N/A" and any(a in line for a in ['EURUSD','GBPUSD','USDJPY']):
                    flow_forex = line.strip()[:200]
                if flow_crypto == "N/A" and any(a in line for a in ['BTCUSD','ETHUSD']):
                    flow_crypto = line.strip()[:200]
            if flow_forex != "N/A" and flow_crypto != "N/A":
                break

    # Python proof output (G4 raw)
    python_proof = f"""# Python G4 Proof (CEO-ORDEM-THRESH-20260529)
# last_restart: {last_restart.isoformat() if last_restart else 'N/A'}
# skip_62: {skip_62}
# skip_65: {skip_65}
# executed_gt0: {executed_gt0}
# entries_frozen: {entries_frozen}
# model_dump: {model_dump}
# G4: {g4}
"""

    symbols_open = get_symbols_open()
    realized_pnl = get_realized_pnl()

    alerts_text = '\n'.join(alerts) if alerts else 'Nenhum'
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    report = f"""TS_UTC={ts}
EQUITY={summary.get('equity_demo', summary.get('equity', 'N/A'))}
POS_N={pos_n}
PNL_FLOAT={ledger.get('total_pnl_snapshot', 'N/A')}
REALIZED_PNL={realized_pnl}
SYMBOLS_OPEN={symbols_open}
FREEZE={entries_frozen}
MODEL_DUMP={model_dump}
TOP_SKIP_1={last_skip_line}
THRESH_HIT_RATE={g4}
FLOW_FOREX={flow_forex}
FLOW_CRYPTO={flow_crypto}
LOG_EXEC_SKIP={last_exec}
LOG_SKIPPED={last_skipped}

--- PYTHON PROOF ---
{python_proof}
--- ALERTS ---
{alerts_text}
"""

    print(report)

    # Save to forensic
    ts_file = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')
    out_path = Path(f"C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/forensic/OPS_SNAPSHOT_{ts_file}.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[Saved] {out_path}")

    # Also return alert status for monitoring
    return len(alerts) > 0

if __name__ == "__main__":
    has_alerts = run_snapshot()
    sys.exit(1 if has_alerts else 0)
