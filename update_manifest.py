import json
import hashlib
import os
import subprocess

def sha3(p):
    s = hashlib.sha3_256()
    with open(p, 'rb') as f: s.update(f.read())
    return s.hexdigest()

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, cwd=r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper').strip()

# 1. Add everything EXCEPT MANIFEST and RT_E
run_cmd('git add "Auditoria PARR-F"')

# 2. Commit 
try:
    run_cmd('git commit -m "MANDATO VITALSIGNS: Cycle 2 e Pacote PSA"')
except Exception as e:
    pass

head1 = run_cmd('git rev-parse HEAD')

# 3. Update RT_E
rt_p = r'Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\RT_E_VITALSIGNS_MANDATO_20260331.md'
abs_rt_p = os.path.join(r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper', rt_p)
with open(abs_rt_p, 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('*(preencher após commit).*', head1)
with open(abs_rt_p, 'w', encoding='utf-8') as f:
    f.write(text)

# We also need to add all modified files to the manifest
mfst = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json'

with open(mfst, 'r', encoding='utf-8') as f:
    data = json.load(f)

def upd_file(relpath, ttype, abs_path):
    global data
    if not os.path.exists(abs_path):
        return
    for x in data['files']:
        if x.get('relpath') == relpath.replace('\\', '/'):
            x['sha3_256_full'] = sha3(abs_path)
            x['bytes'] = os.path.getsize(abs_path)
            return
    data['files'].append({
        'type': ttype,
        'filename': os.path.basename(relpath),
        'relpath': relpath.replace('\\', '/'),
        'bytes': os.path.getsize(abs_path),
        'sha3_256_full': sha3(abs_path)
    })

base_repo = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper'

upd_file('Auditoria PARR-F/11_live_demo_cycle_1.py', 'CODE_VERSION', os.path.join(base_repo, 'Auditoria PARR-F/11_live_demo_cycle_1.py'))
upd_file('Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/audit_trade_count.py', 'CODE_VERSION', os.path.join(base_repo, 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/audit_trade_count.py'))
upd_file('Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/PACOTE_PSA_OMEGA_VERDADE_UNIFICADA_20260331.md', 'DOCUMENT', os.path.join(base_repo, 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/PACOTE_PSA_OMEGA_VERDADE_UNIFICADA_20260331.md'))
upd_file('Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/RT_E_VITALSIGNS_MANDATO_20260331.md', 'DOCUMENT', os.path.join(base_repo, 'Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/RT_E_VITALSIGNS_MANDATO_20260331.md'))

with open(mfst, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

# 5. Amend the commit to include the actual files
run_cmd('git add "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/RT_E_VITALSIGNS_MANDATO_20260331.md"')
run_cmd('git commit --amend --no-edit')

# 6. Read new HEAD, update manifest git_commit_sha but do not commit
head2 = run_cmd('git rev-parse HEAD')
data['git_commit_sha'] = head2
with open(mfst, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print('Success. NEW HEAD:', head2)
