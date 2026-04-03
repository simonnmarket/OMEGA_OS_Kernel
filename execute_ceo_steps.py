import json
import subprocess
import os

repo_root = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'
base_dir = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo'
python_exe = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\venv_psa\Scripts\python.exe'

# STEP-01: Ensure template exists
tpl_path = os.path.join(base_dir, r'04_relatorios_tarefa\templates_auditoria_psa\prova_TEMPLATE_PREENCHER.json')
if not os.path.exists(tpl_path):
    with open(tpl_path, 'w', encoding='utf-8') as f:
        f.write('{\n  "proof_id": "PREENCHER",\n  "req_id": "PREENCHER",\n  "doc_ref": "PREENCHER",\n  "fase": "PREENCHER",\n  "titulo_curto": "PREENCHER",\n  "artefacto_obrigatorio": "PREENCHER",\n  "comando_ou_predicado": "PREENCHER",\n  "resultado_esperado": "PREENCHER",\n  "resultado_actual": "PREENCHER",\n  "veredito": "FAIL",\n  "bloqueador": "Isto eh um template",\n  "git_head": "0000000000000000000000000000000000000000",\n  "ts_utc": "1970-01-01T00:00:00Z"\n}')

# Add new files to manifest explicitly BEFORE sync
manifest_path = os.path.join(base_dir, r'03_hashes_manifestos\MANIFEST_RUN_20260329.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_entries = [
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOCUMENTO_OFICIAL_PSA_MANDATO_EXECUCAO_PERMANENTE_E_ENCERRAMENTO_CEO.md',
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOCUMENTO_OFC_CEO_FECHO_AUDITORIA_PSA.md',
    'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/templates_auditoria_psa/prova_TEMPLATE_PREENCHER.json'
]
existing = {x.get('relpath') for x in man_data['files']}
for ne in new_entries:
    if ne not in existing:
        man_data['files'].append({'type': 'DOCUMENT', 'filename': ne.split('/')[-1], 'relpath': ne, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)


def run_cmd(args, cwd=repo_root):
    print(f"Running: {' '.join(args)}")
    res = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"ERROR: Return code {res.returncode}")
        print(res.stderr)
    return res.returncode

# STEP-02
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)

# STEP-03
run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)

# STEP-04
run_cmd([python_exe, 'psa_gate_conselho_tier0.py', '--out-relatorio', r'04_relatorios_tarefa\PSA_GATE_CONSELHO_ULTIMO.txt'], cwd=base_dir)

# STEP-05 (Re-sync after gate generated)
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)

# STEP-06
tarefas_dir = os.path.join(base_dir, '04_relatorios_tarefa')
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS02-20260403-001.json'], cwd=tarefas_dir)
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS03-20260403-001.json'], cwd=tarefas_dir)
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS04-20260403-001.json'], cwd=tarefas_dir)

# STEP-07
run_cmd([python_exe, 'psa_gate_conselho_tier0.py'], cwd=base_dir)

