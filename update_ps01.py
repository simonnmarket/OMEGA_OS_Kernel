import json
import csv
import subprocess
import datetime

ts_utc = datetime.datetime.utcnow().isoformat() + 'Z'

# Get baseline HEAD
head_res = subprocess.run(['git', '-C', r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper', 'rev-parse', 'HEAD'], capture_output=True, text=True)
git_head = head_res.stdout.strip()

# 1. Update CSV Matrix
csv_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa\MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv'
new_row = ['SOL-20260403-004', 'TAR-PHPS01-001', 'PH-PS-01', 'Relatorio Piloto para Administracao', '—', '—', 'PASS', 'DEC-20260403-004', git_head, ts_utc, 'PSA', 'RPT-PILOTO-ADMINISTRACAO-20260403-001.md validado narrativamente.']
with open(csv_path, 'a', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(new_row)

# 2. Append JSONL
log_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\PSA_RUN_LOG.jsonl'
log_entry = {
    'ts_utc': ts_utc,
    'run_id': f'PS-20260403-PHPS01-{git_head[:7]}',
    'phase': 'PH-PS-01',
    'git_head': git_head,
    'action': 'phase_complete',
    'artifact': '04_relatorios_tarefa/RPT-PILOTO-ADMINISTRACAO-20260403-001.md',
    'metrics': {'status': 'RPT_EMITIDO'},
    'command': 'None'
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(log_entry) + '\n')

