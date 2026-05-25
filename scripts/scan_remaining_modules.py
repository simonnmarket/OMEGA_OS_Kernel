"""Varredura rápida dos 10 módulos restantes: sintaxe, importabilidade, tamanho."""
import sys, importlib.util, ast
sys.path.insert(0, ".")

modules_to_scan = [
    ("anomaly_detector",        "modules/anomaly_detector.py"),
    ("momentum_physics",        "modules/momentum_physics.py"),
    ("omega_confluence_engine", "modules/omega_confluence_engine.py"),
    ("omega_kernel_v5_1",       "modules/omega_kernel_v5_1_refined.py"),
    ("risk_circuit_breaker",    "modules/risk_circuit_breaker.py"),
    ("risk_valves_v31",         "modules/risk_valves_v31.py"),
    ("v_flow_microstructure",   "modules/v_flow_microstructure.py"),
    ("volume_physics",          "modules/volume_physics.py"),
    ("volume_profile",          "modules/volume_profile.py"),
    ("zone_navigator",          "modules/zone_navigator.py"),
]

header = f"{'Module':<28}  {'Syntax':>6}  {'Import':>20}  {'KB':>6}"
print(header)
print("-" * len(header))

results = []
for name, path in modules_to_scan:
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        size_kb = round(len(src) / 1024, 1)
        try:
            ast.parse(src)
            syntax = "OK"
        except SyntaxError as e:
            syntax = f"ERR:{e.lineno}"
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            import_st = "OK"
        except Exception as e:
            import_st = str(e)[:20]
        ready = syntax == "OK" and import_st == "OK"
        results.append((name, syntax, import_st, size_kb, ready))
        row = f"{name:<28}  {syntax:>6}  {import_st:>20}  {size_kb:>5.1f}KB"
        print(row)
    except Exception as e:
        print(f"{name:<28}  FILE_ERROR: {e}")

print("-" * len(header))
ready_count = sum(1 for r in results if r[4])
print(f"\nPRONTOS para integração: {ready_count}/{len(modules_to_scan)}")
print("\nPrioridade de integração sugerida:")
priorities = {
    "risk_circuit_breaker":    "P1 — RISK guardrail complementar ao RISK_GATE",
    "risk_valves_v31":         "P1 — Válvulas de risco (DD, exposure, daily limits)",
    "volume_profile":          "P2 — Volume profile: S/R dinâmico para TP/SL",
    "v_flow_microstructure":   "P2 — Microestrutura: fluxo de ordens institucional",
    "zone_navigator":          "P2 — Navigator de zonas de demanda/oferta",
    "momentum_physics":        "P3 — Motor de momentum físico (velocidade + aceleração)",
    "anomaly_detector":        "P3 — Detector de anomalia de mercado",
    "omega_confluence_engine": "P3 — Motor de confluência multi-fator",
    "volume_physics":          "P3 — Física de volume (Wyckoff-inspired)",
    "omega_kernel_v5_1":       "P4 — Kernel de orquestração v5.1 (complexo, aguardar)",
}
for name, _, _, _, ready in results:
    status = "READY" if ready else "NEEDS_FIX"
    prio = priorities.get(name, "?")
    print(f"  [{status}] {name:<28}  {prio}")
