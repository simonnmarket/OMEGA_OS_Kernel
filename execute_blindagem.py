import json
import subprocess
import os

repo_root = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'
base_dir = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo'
python_exe = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\venv_psa\Scripts\python.exe'

manifest_path = os.path.join(base_dir, r'03_hashes_manifestos\MANIFEST_RUN_20260329.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    man_data = json.load(f)

new_doc = 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOC_GOV_BLINDAGEM_ENCERRAMENTO_TIER0_PSA_20260327_FINAL.md'
existing = {x.get('relpath') for x in man_data['files']}
if new_doc not in existing:
    man_data['files'].append({'type': 'DOCUMENT', 'filename': new_doc.split('/')[-1], 'relpath': new_doc, 'bytes': 0, 'sha3_256_full': ''})

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(man_data, f, indent=4)

def run_cmd(args, cwd=repo_root):
    print(f"Running: {' '.join(args)}")
    res = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"ERROR: Return code {res.returncode}")
        print(res.stdout)
        print(res.stderr)
        exit(1)
    return res.stdout

print("BL-01: Documentos commitados ou prestes a ser.")
subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '-m', 'docs: GOV-PSA-BLIND-20260327-001 blindagem etapa Tier-0'])

print("BL-02: Sync")
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)

print("BL-03: Verify")
out = run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)
if "ESTADO: OK" not in out:
    print("Verify failed.")
    exit(1)

print("BL-04: Gate")
run_cmd([python_exe, 'psa_gate_conselho_tier0.py', '--out-relatorio', r'04_relatorios_tarefa\PSA_GATE_CONSELHO_ULTIMO.txt'], cwd=base_dir)

print("BL-05: Re-sync")
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)

print("BL-06: Validar PRFs")
tarefas_dir = os.path.join(base_dir, '04_relatorios_tarefa')
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS02-20260403-001.json'], cwd=tarefas_dir)
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS03-20260403-001.json'], cwd=tarefas_dir)
run_cmd([python_exe, 'psa_refutation_checklist.py', '--validate', r'templates_auditoria_psa\prova_PRF-PHFS04-20260403-001.json'], cwd=tarefas_dir)

print("BL-07: Gate sem --out-relatorio")
run_cmd([python_exe, 'psa_gate_conselho_tier0.py'], cwd=base_dir)

print("BL-08: Atualizar Doc MD com novo HEAD")
head_res = subprocess.run(['git', '-C', repo_root, 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
new_head = head_res.stdout.strip()

doc_path = os.path.join(base_dir, r'04_relatorios_tarefa\DOC_GOV_BLINDAGEM_ENCERRAMENTO_TIER0_PSA_20260327_FINAL.md')
with open(doc_path, 'r', encoding='utf-8') as f:
    doc_lines = f.readlines()
for i, line in enumerate(doc_lines):
    if "| **SHA de referência homologável** |" in line:
        doc_lines[i] = f"| **SHA de referência homologável** | {new_head} (ajustado ao commit atual) |\n"
with open(doc_path, 'w', encoding='utf-8') as f:
    f.writelines(doc_lines)

subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '--amend', '--no-edit'], check=True)

# Final sync against amended hash
run_cmd([python_exe, 'psa_sync_manifest_from_disk.py', '--set-git-commit-sha-from-head'], cwd=base_dir)
# Verify the final state
run_cmd([python_exe, 'verify_tier0_psa.py'], cwd=base_dir)

# Add that sync
subprocess.run(['git', '-C', repo_root, 'add', '-A'], check=True)
subprocess.run(['git', '-C', repo_root, 'commit', '--amend', '--no-edit'], check=True)

print("BL-09: Tagging")
subprocess.run(['git', '-C', repo_root, 'tag', '-a', 'psa-tier0-fecho-fin-sense-mvp-20260327', '-f', '-m', "PSA Tier-0 Final MVP Fin-Sense"], check=True)

print("SUCESSO ABSOLUTO.")
