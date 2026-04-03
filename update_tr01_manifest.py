import json
import subprocess
import datetime

# 1. Update Manifest
manifest_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json'
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_entries = [
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOCUMENTO_FINAL_EXECUCAO_E_CORRECOES_FASE_PH_TR01.md'
]
existing = {x.get('relpath') for x in man_data['files']}
for ne in new_entries:
    if ne not in existing:
        man_data['files'].append({'type': 'DOCUMENT', 'filename': ne, 'relpath': ne, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)
