import json
import csv

# 1. Update CSV
csv_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa\MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv'
new_row = ['SOL-20260403-002', 'TAR-PHFS03-001', 'PH-FS-03', 'Normalizar execucao demo log', 'REQ-UNICO-040', 'PRF-PHFS03-20260403-001', 'PASS', 'DEC-20260403-002', 'c3ea3be41d5e3f538e14afb3eb1b78ad9fa4b045', '2026-04-03T20:34:00Z', 'PSA', 'Gerado MAP-DEMO-TBL_v1.md']
with open(csv_path, 'a', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(new_row)

# 2. Append JSONL
log_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\PSA_RUN_LOG.jsonl'
log_entry = {
    'ts_utc': '2026-04-03T20:35:00Z',
    'run_id': 'PS-20260403-PHFS03-c3ea3be',
    'phase': 'PH-FS-03',
    'git_head': 'c3ea3be41d5e3f538e14afb3eb1b78ad9fa4b045',
    'action': 'phase_complete',
    'artifact': '04_relatorios_tarefa/MAP-DEMO-TBL_v1.md',
    'metrics': {'req_id': 'REQ-UNICO-040'},
    'command': 'None'
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(log_entry) + '\n')

# 3. Update Manifest
manifest_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json'
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_entries = [
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOCUMENTO_OFICIAL_ENVIO_PSA_MANDATO_EXECUCAO.md',
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/MAP-DEMO-TBL_v1.md',
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/templates_auditoria_psa/prova_PRF-PHFS03-20260403-001.json'
]
existing = {x.get('relpath') for x in man_data['files']}
for ne in new_entries:
    if ne not in existing:
        man_data['files'].append({'type': 'DOCUMENT', 'filename': ne, 'relpath': ne, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)
