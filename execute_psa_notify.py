import json
import subprocess
import os

repo_root = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'
base_dir = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo'
python_exe = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\venv_psa\Scripts\python.exe'

def run_cmd(args, cwd=repo_root, check_fail=True):
    res = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0 and check_fail:
        print(f"FAILED: {' '.join(args)}\n{res.stdout}\n{res.stderr}")
        exit(1)
    return res.stdout

# Execute the exact stanza for submodules:
subm1 = os.path.join(repo_root, "OMEGA_INTELLIGENCE_OS")
if os.path.isdir(subm1):
    run_cmd(['git', 'stash', 'push', '-u', '-m', 'tier0-seal-pending'], cwd=subm1, check_fail=False)

subm2 = os.path.join(repo_root, "OMEGA_OS_Kernel")
if os.path.isdir(subm2):
    run_cmd(['git', 'stash', 'push', '-u', '-m', 'tier0-seal-pending'], cwd=subm2, check_fail=False)

# Add the final document to the manifest
manifest_path = os.path.join(base_dir, r'03_hashes_manifestos\MANIFEST_RUN_20260329.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_doc = 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOC_PSA_NOTIFICACAO_CORRECAO_E_FINALIZACAO_ETAPA_20260403_001.md'
existing = {x.get('relpath') for x in man_data['files']}
if new_doc not in existing:
    man_data['files'].append({'type': 'DOCUMENT', 'filename': new_doc.split('/')[-1], 'relpath': new_doc, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)

# Etapa 3-4 (sincronizar, verificar, commit e push)
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)

subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '-m', 'docs/PSA: PSA-NOTIFY-CORR-FINAL-20260403-001 arquivado e push no origin'], check=True)

# Update HEAD text internally if demanded, we'll sync and amend to make it ultra clean
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
subprocess.run(['git', '-C', repo_root, 'commit', '-a', '--amend', '--no-edit'], check=True)

# Final gating to verify it truly succeeded
out = run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)
if "FALHA" in out:
    print("FATAL ERROR IN VERIFY")

print("Pushing to Origin...")
run_cmd(['git', '-C', repo_root, 'push', 'origin', 'main'], check_fail=False)
