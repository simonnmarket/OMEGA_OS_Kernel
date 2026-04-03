import json
import sys

head_sha = sys.argv[1]
files = [
    r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa\prova_PRF-PHFS02-20260403-001.json',
    r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa\prova_PRF-PHFS03-20260403-001.json',
    r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa\prova_PRF-PHFS04-20260403-001.json'
]
for p in files:
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
    d['git_head'] = head_sha
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=4)
