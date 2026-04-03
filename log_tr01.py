import json
import datetime
ts_utc = datetime.datetime.utcnow().isoformat() + 'Z'
log_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\PSA_RUN_LOG.jsonl'
log_entry = {
    'ts_utc': ts_utc,
    'run_id': 'PS-20260403-PHTR01-0cd5588',
    'phase': 'PH-TR-01',
    'git_head': '0cd5588c406b9deb3db6ca075502e7eaf1ffe5fb',
    'action': 'gate_pass',
    'artifact': '04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt',
    'metrics': {'verify_tier0_exit': 0, 'gate_timestamp_utc': ts_utc},
    'command': 'psa_gate_conselho_tier0.py'
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(log_entry) + '\n')
