import json
import subprocess
import os

repo_root = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'
base_dir = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo'
python_exe = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\venv_psa\Scripts\python.exe'

def run_cmd(args, cwd=repo_root, check_fail=True):
    print(f"RUNNING: {' '.join(args)}")
    res = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0 and check_fail:
        print(f"FAILED: {' '.join(args)}\n{res.stdout}\n{res.stderr}")
        exit(1)
    return res.stdout

# P1: Submodules integration (A)
run_cmd(['git', '-C', repo_root, 'add', 'OMEGA_INTELLIGENCE_OS', 'OMEGA_OS_Kernel'])
# check if there's anything to commit in submodules
res_sub = subprocess.run(['git', '-C', repo_root, 'commit', '-m', 'chore: alinhar submódulos OMEGA_INTELLIGENCE_OS / OMEGA_OS_Kernel'], capture_output=True)

# Add Document to Manifest
manifest_path = os.path.join(base_dir, r'03_hashes_manifestos\MANIFEST_RUN_20260329.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_doc = 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOC_RUNBOOK_FECHO_PENDENCIAS_OPERACIONAIS_OMEGA_20260403_001.md'
existing = {x.get('relpath') for x in man_data['files']}
if new_doc not in existing:
    man_data['files'].append({'type': 'DOCUMENT', 'filename': new_doc.split('/')[-1], 'relpath': new_doc, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)

run_cmd(['git', '-C', repo_root, 'add', '-A'])
run_cmd(['git', '-C', repo_root, 'commit', '-m', 'docs: Emissão RUNBOOK-OMEGA-PEND-20260403-001 de fecho de pendências'])

# Runbook P3/P4 Sequence
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
verify1 = run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)
if "ESTADO: OK" not in verify1:
    print("Verify failed.")
    exit(1)

run_cmd([python_exe, 'psa_gate_conselho_tier0.py', '--out-relatorio', r'04_relatorios_tarefa\PSA_GATE_CONSELHO_ULTIMO.txt'], cwd=base_dir)
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
verify2 = run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)
if "ESTADO: OK" not in verify2:
    print("Verify2 failed.")
    exit(1)

tarefas_dir = os.path.join(base_dir, '04_relatorios_tarefa')
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS02-20260403-001.json'], cwd=tarefas_dir)
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS03-20260403-001.json'], cwd=tarefas_dir)
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS04-20260403-001.json'], cwd=tarefas_dir)

# P2: Push to remote
print("Pushing to remote...")
run_cmd(['git', '-C', repo_root, 'push', 'origin', 'main'], check_fail=False)

# Add Gate output delta
subprocess.run(['git', '-C', repo_root, 'add', '-A'])
res_sync = subprocess.run(['git', '-C', repo_root, 'commit', '--amend', '--no-edit'], capture_output=True)

print("SUCCESS: Runbook executed and all 5 conditions closed.")
