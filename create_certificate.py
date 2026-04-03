import json
import subprocess
import os

repo_root = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'
base_dir = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo'
python_exe = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\venv_psa\Scripts\python.exe'

manifest_path = os.path.join(base_dir, r'03_hashes_manifestos\MANIFEST_RUN_20260329.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_doc = 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/CERTIFICADO_FINAL_BLINDAGEM_TIER0_PSA.md'
existing = {x.get('relpath') for x in man_data['files']}
if new_doc not in existing:
    man_data['files'].append({'type': 'DOCUMENT', 'filename': new_doc.split('/')[-1], 'relpath': new_doc, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)

def run_cmd(args, cwd=repo_root):
    res = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"FAILED: {' '.join(args)}\n{res.stdout}\n{res.stderr}")
        exit(1)

# Sync and verify
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)
run_cmd([python_exe, 'psa_gate_conselho_tier0.py', '--out-relatorio', r'04_relatorios_tarefa\PSA_GATE_CONSELHO_ULTIMO.txt'], cwd=base_dir)
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)

# Commit
subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '-m', 'docs: Emissão do CERTIFICADO_FINAL_BLINDAGEM_TIER0_PSA.md [CHORE-FINAL]'], check=True)

# Delete existing tag and recreate at HEAD
subprocess.run(['git', '-C', repo_root, 'tag', '-d', 'psa-tier0-fecho-fin-sense-mvp-20260327'], check=True)
subprocess.run(['git', '-C', repo_root, 'tag', '-a', 'psa-tier0-fecho-fin-sense-mvp-20260327', '-m', 'PSA Tier-0 Final MVP Fin-Sense', 'HEAD'], check=True)
