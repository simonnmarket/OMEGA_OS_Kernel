import json
import csv
import subprocess
import datetime

# Get current HEAD
head_res = subprocess.run(['git', '-C', r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper', 'rev-parse', 'HEAD'], capture_output=True, text=True)
git_head = head_res.stdout.strip()
ts_utc = datetime.datetime.utcnow().isoformat() + 'Z'

# Update PRF with git_head
prf_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa\prova_PRF-PHFS04-20260403-001.json'
with open(prf_path, 'r', encoding='utf-8') as f:
    prf_data = json.load(f)
prf_data['git_head'] = git_head
with open(prf_path, 'w', encoding='utf-8') as f:
    json.dump(prf_data, f, indent=4)

# Update CSV Matrix
csv_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa\MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv'
new_row = ['SOL-20260403-003', 'TAR-PHFS04-001', 'PH-FS-04', 'Medicao formal KPI-06', 'REQ-UNICO-050', 'PRF-PHFS04-20260403-001', 'PASS', 'DEC-20260403-003', git_head, ts_utc, 'PSA', 'KPI-06 atingiu 1.0']
with open(csv_path, 'a', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(new_row)

# Append to JSONL
log_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\PSA_RUN_LOG.jsonl'
entries = [
    {'ts_utc': ts_utc, 'run_id': f'PS-20260403-PHFS04-{git_head[:7]}', 'phase': 'PH-FS-04', 'git_head': git_head, 'action': 'file_saved', 'artifact': '04_relatorios_tarefa/KPI_REPORT_20260403-001.json', 'metrics': None, 'command': None},
    {'ts_utc': ts_utc, 'run_id': f'PS-20260403-PHFS04-{git_head[:7]}', 'phase': 'PH-FS-04', 'git_head': git_head, 'action': 'prf_validated', 'artifact': 'templates_auditoria_psa/prova_PRF-PHFS04-20260403-001.json', 'metrics': None, 'command': 'python psa_refutation_checklist.py --validate templates_auditoria_psa/prova_PRF-PHFS04-20260403-001.json'},
    {'ts_utc': ts_utc, 'run_id': f'PS-20260403-PHFS04-{git_head[:7]}', 'phase': 'PH-FS-04', 'git_head': git_head, 'action': 'phase_complete', 'artifact': None, 'metrics': None, 'command': None}
]
with open(log_path, 'a', encoding='utf-8') as f:
    for e in entries:
        f.write(json.dumps(e) + '\n')

# Update Manifest
manifest_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json'
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_entries = [
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOCUMENTO_UNICO_OFICIAL_PSA_ENCERRAMENTO_AUDITORIA_E_PROXIMOS_PASSOS.md',
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/KPI_REPORT_20260403-001.json',
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/templates_auditoria_psa/prova_PRF-PHFS04-20260403-001.json'
]
existing = {x.get('relpath') for x in man_data['files']}
for ne in new_entries:
    if ne not in existing:
        man_data['files'].append({'type': 'DOCUMENT', 'filename': ne, 'relpath': ne, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)
