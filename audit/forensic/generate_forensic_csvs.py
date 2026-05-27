#!/usr/bin/env python3
"""
CEO-FORENSIC-INTEGRITY-20260527
Gera: mtf_pyramid_trace.csv + asset_class_matrix.csv
"""
import json, csv, re, os, datetime
from collections import defaultdict

BASE = "C:/OMEGA_QUANTUM_LAB/SOURCE_CODE"
FEEDBACK_PATH = os.path.join(BASE, "audit/paper/trade_feedback.jsonl")
LOG_PATH      = os.path.join(BASE, "audit/paper/omega_24x7_runner.log")
OUT_DIR       = os.path.join(BASE, "audit/forensic")
os.makedirs(OUT_DIR, exist_ok=True)

NOW_UTC = datetime.datetime.utcnow()
CUTOFF  = NOW_UTC - datetime.timedelta(hours=24)

# ── 1. Ler trade_feedback.jsonl ──────────────────────────────────────────────
fb_entries = []
with open(FEEDBACK_PATH, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        # Filtrar últimas 24h baseado no campo ts ou detected_at_utc
        ts_str = d.get("ts") or d.get("detected_at_utc") or ""
        try:
            ts = datetime.datetime.fromisoformat(ts_str.replace("Z","+00:00"))
            ts_naive = ts.replace(tzinfo=None)
        except Exception:
            ts_naive = datetime.datetime(2000,1,1)
        if ts_naive >= CUTOFF:
            fb_entries.append(d)

print(f"trade_feedback entries últimas 24h: {len(fb_entries)}")

# ── 2. Ler log para obter dados por ticket ────────────────────────────────────
# Padrões no log
RE_OPEN   = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?FASE4 EXEC.*?symbol=(\w+).*?tf=(\w+).*?dir=([+-1]+|BUY|SELL).*?success=True.*?deal=(\d+)', re.IGNORECASE)
RE_TICKET = re.compile(r'ticket[=:#](\d{7,12})', re.IGNORECASE)
RE_PYRAMID= re.compile(r'pyramid.*?score[=: ]+(\w+)', re.IGNORECASE)
RE_PEAK   = re.compile(r'PEAK_DRAWDOWN.*?ticket.*?(\d{7,12})', re.IGNORECASE)
RE_TRAILING_EXIT = re.compile(r'TRAILING.*?(\d{7,12}).*?exit=True', re.IGNORECASE)
RE_ATR    = re.compile(r'(\w+)\s+[HM]\d.*?ATR.*?=\s*([\d.]+)', re.IGNORECASE)

# Index log lines com timestamp nas últimas 24h
log_lines_24h = []
CUTOFF_STR = CUTOFF.strftime("%Y-%m-%d %H:%M:%S")
print(f"Lendo log (pode demorar)...")
try:
    log_size = os.path.getsize(LOG_PATH)
    # Ler apenas os últimos 50MB para eficiência
    read_start = max(0, log_size - 52428800)
    with open(LOG_PATH, "rb") as f:
        f.seek(read_start)
        raw = f.read()
    log_text = raw.decode("utf-8", errors="replace")
    log_lines_24h = log_text.splitlines()
    print(f"  Linhas de log carregadas: {len(log_lines_24h)}")
except Exception as e:
    print(f"WARN log: {e}")
    log_lines_24h = []

# Extrair info de pyramiding do log
pyramid_info = {}   # ticket -> bool
peak_close   = set()  # tickets fechados por PEAK_DRAWDOWN
trail_close  = set()  # tickets fechados por TRAILING

for line in log_lines_24h:
    if "PYRAMID" in line or "pyramid" in line:
        m_t = RE_TICKET.search(line)
        if m_t:
            ticket = int(m_t.group(1))
            if "False" in line or "BLOCKED" in line or "skip" in line.lower():
                pyramid_info[ticket] = False
            elif "True" in line or "ADD" in line.upper():
                pyramid_info[ticket] = True
    if "PEAK_DRAWDOWN" in line:
        m_t = RE_TICKET.search(line)
        if m_t:
            peak_close.add(int(m_t.group(1)))
    if "TRAILING" in line and "exit=True" in line:
        m_t = RE_TICKET.search(line)
        if m_t:
            trail_close.add(int(m_t.group(1)))

print(f"  pyramid_info: {len(pyramid_info)} tickets | peak_close: {len(peak_close)} | trail_close: {len(trail_close)}")

# ── 3. Construir mtf_pyramid_trace.csv ───────────────────────────────────────
ASSET_CLASS = {
    "XAUUSD":"metals","XAGUSD":"metals",
    "EURUSD":"forex","GBPUSD":"forex","USDJPY":"forex","AUDUSD":"forex","USDCAD":"forex","USDCHF":"forex","NZDUSD":"forex",
    "EURJPY":"forex","GBPJPY":"forex","AUDJPY":"forex","CADJPY":"forex","CHFJPY":"forex",
    "US500":"indices","US100":"indices","US30":"indices","GER40":"indices","UK100":"indices",
    "BTCUSD":"crypto","ETHUSD":"crypto","SOLUSD":"crypto","XRPUSD":"crypto",
    "BNBUSD":"crypto","AVAXUSD":"crypto","ADAUSD":"crypto","LTCUSD":"crypto","DOGUSD":"crypto",
}

rows = []
for d in fb_entries:
    ticket  = d.get("position_ticket") or d.get("ticket") or 0
    asset   = d.get("symbol","?")
    ts_str  = d.get("ts") or d.get("detected_at_utc","")
    src     = d.get("signal_source") or "NONE"

    # direction
    direction = "?"
    pnl = d.get("pnl",0)

    # mtf_confluence_score — not recorded in trade_feedback (that's the finding)
    mtf_score = d.get("mtf_confluence_score", None)

    # timeframes_aligned — not recorded
    tf_aligned = d.get("timeframes_aligned", None)

    # entry_blocked_reason
    blocked = d.get("entry_blocked_reason", d.get("skip_reason", None))

    # pyramid evaluated
    pyr_eval = pyramid_info.get(ticket, None)

    # lots
    initial_lot = d.get("initial_lot") or d.get("lot",0)
    scaled_lot  = d.get("scaled_lot")  or d.get("lot",0)

    # exit_reason
    if ticket in peak_close:
        exit_reason = "PEAK_DRAWDOWN"
    elif ticket in trail_close:
        exit_reason = "TRAILING"
    else:
        exit_reason = d.get("exit_reason") or d.get("result") or "BROKER_CLOSE"

    rows.append({
        "ticket": ticket,
        "asset": asset,
        "signal_time": ts_str,
        "direction": direction,
        "mtf_confluence_score": mtf_score,
        "timeframes_aligned": tf_aligned,
        "entry_blocked_reason": blocked,
        "pyramid_score_evaluated": pyr_eval,
        "initial_lot": initial_lot,
        "scaled_lot": scaled_lot,
        "exit_reason": exit_reason,
    })

# Escrever CSV
out_csv = os.path.join(OUT_DIR, "mtf_pyramid_trace.csv")
fieldnames = ["ticket","asset","signal_time","direction","mtf_confluence_score",
              "timeframes_aligned","entry_blocked_reason","pyramid_score_evaluated",
              "initial_lot","scaled_lot","exit_reason"]
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)
print(f"mtf_pyramid_trace.csv: {len(rows)} linhas → {out_csv}")

# ── 4. asset_class_matrix.csv ────────────────────────────────────────────────
# Todas as entradas do feedback (não só 24h) para mostrar padrão sistémico
all_fb = []
with open(FEEDBACK_PATH, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            all_fb.append(json.loads(line))

matrix = defaultdict(lambda: {"total_signals":0,"correct_dir":0,"wrong_dir_late":0,"pyramid_active":0,"agent_ia":0,"momentum":0})
for d in all_fb:
    asset = d.get("symbol","?")
    cls   = ASSET_CLASS.get(asset, "other")
    r     = d.get("r_multiple",0) or 0
    src   = d.get("signal_source","") or ""
    matrix[cls]["total_signals"] += 1
    if r > 0:
        matrix[cls]["correct_dir"] += 1
    else:
        matrix[cls]["wrong_dir_late"] += 1
    t = d.get("position_ticket",0)
    if t and pyramid_info.get(t) == True:
        matrix[cls]["pyramid_active"] += 1
    if "AGENT_IA" in src:
        matrix[cls]["agent_ia"] += 1
    if "MOMENTUM" in src:
        matrix[cls]["momentum"] += 1

out_matrix = os.path.join(OUT_DIR, "asset_class_matrix.csv")
with open(out_matrix, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["asset_class","total_signals","correct_dir","wrong_dir_late","pyramid_active","agent_ia_source","momentum_source","pyramid_status"])
    for cls, m in sorted(matrix.items()):
        pyr_status = "ACTIVE" if m["pyramid_active"] > 0 else "INATIVO"
        w.writerow([cls, m["total_signals"], m["correct_dir"], m["wrong_dir_late"],
                    m["pyramid_active"], m["agent_ia"], m["momentum"], pyr_status])

print(f"asset_class_matrix.csv → {out_matrix}")

# ── 5. Summary estatístico para relatório ─────────────────────────────────────
print("\n=== SUMMARY FORENSE ===")
print(f"Total trades feedback: {len(all_fb)}")
print(f"Trades últimas 24h: {len(fb_entries)}")
print(f"mtf_confluence_score preenchido: {sum(1 for r in rows if r['mtf_confluence_score'] is not None)}")
print(f"timeframes_aligned preenchido: {sum(1 for r in rows if r['timeframes_aligned'] is not None)}")
print(f"pyramid_score_evaluated preenchido: {sum(1 for r in rows if r['pyramid_score_evaluated'] is not None)}")
print(f"exit_reason=PEAK_DRAWDOWN: {sum(1 for r in rows if r['exit_reason']=='PEAK_DRAWDOWN')}")
print(f"exit_reason=TRAILING: {sum(1 for r in rows if r['exit_reason']=='TRAILING')}")
print("\nMatrix:")
for cls, m in sorted(matrix.items()):
    print(f"  {cls:12s}: total={m['total_signals']:4d} | correct={m['correct_dir']:4d} | pyramid_active={m['pyramid_active']} | agent_ia={m['agent_ia']} | momentum={m['momentum']}")
print("=== FIM ===")
