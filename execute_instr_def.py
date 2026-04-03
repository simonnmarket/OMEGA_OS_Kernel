import json
import subprocess
import os

repo_root = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'
base_dir = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo'
python_exe = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\venv_psa\Scripts\python.exe'

# 1. Update manifest entries
manifest_path = os.path.join(base_dir, r'03_hashes_manifestos\MANIFEST_RUN_20260329.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_doc = 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/INSTR_PSA_DEFINITIVA_EXECUCAO_TIER0_20260403_001.md'
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
    return res.stdout

# 2. Add and Commit
subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '-m', 'docs/chore: INSTR-PSA-DEF-20260403-001 mitigação definitiva ciclo manifesto heads'], check=True)

# 3. Apply the 3 PSA rules exactly once.
print("syncing...")
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)

print("verifying...")
out = run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)
if "ESTADO: OK" not in out:
    print("Verification failed unexpectedly!")
    exit(1)

# Because verify succeeded but gave warning logically (since we synced, probably no warning), we commit the sync metadata
subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '--amend', '--no-edit'], check=True)

print("Success with definitive Fix!")
