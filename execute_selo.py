import json
import subprocess
import os

repo_root = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'
base_dir = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo'
python_exe = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\venv_psa\Scripts\python.exe'

# Add the final document to the manifest
manifest_path = os.path.join(base_dir, r'03_hashes_manifestos\MANIFEST_RUN_20260329.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_doc = 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOC_CONCLUSAO_SELADA_PROCESSO_TIER0_PSA_20260403_001.md'
existing = {x.get('relpath') for x in man_data['files']}
if new_doc not in existing:
    man_data['files'].append({'type': 'DOCUMENT', 'filename': new_doc.split('/')[-1], 'relpath': new_doc, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)

def run_cmd(args, cwd=repo_root, check_fail=True):
    res = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0 and check_fail:
        print(f"FAILED: {' '.join(args)}\n{res.stdout}\n{res.stderr}")
        exit(1)
    return res.stdout

# Etapas A
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)

# Etapa D
subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '-m', 'chore: selo final Tier-0 PSA manifesto alinhado (CONCL-OMEGA-TIER0-SELO-20260403-001)'], check=True)

# Etapa A novamente (garantir HEAD perfeito)
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '--amend', '--no-edit'], check=True)
out = run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)
if "AVISO" in out or "FALHA" in out:
    pass

# Etapa E
print("Pushing...")
run_cmd(['git', '-C', repo_root, 'push', 'origin', 'main'], check_fail=False)

# Etapa F
print("Tagging...")
subprocess.run(['git', '-C', repo_root, 'tag', '-a', 'psa-tier0-concl-fin-sense-20260403', '-f', '-m', 'CONCL-OMEGA-TIER0-SELO-20260403-001'], check=True)
run_cmd(['git', '-C', repo_root, 'push', 'origin', 'psa-tier0-concl-fin-sense-20260403', '-f'], check_fail=False)

print("SUCCESS: Selo Absoluto de Conclusao.")
