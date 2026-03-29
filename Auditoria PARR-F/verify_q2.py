import hashlib
import os

lp = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\02_logs_execucao"
out = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\03_hashes_manifestos\VERIFY_LOG.txt"
files = ["STRESS_2Y_SCALPING.csv", "STRESS_2Y_DAY_TRADE.csv", "STRESS_2Y_SWING_TRADE.csv"]

with open(out, 'w', encoding='utf-8') as f_out:
    for f in files:
        p = os.path.join(lp, f)
        if os.path.exists(p):
            h = hashlib.sha3_256(open(p, 'rb').read()).hexdigest()
            b = os.path.getsize(p)
            line = f"OK {f} {b} {h}\n"
            f_out.write(line)
            print(line.strip())
