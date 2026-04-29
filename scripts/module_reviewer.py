"""
MODULE REVIEWER — NEBULAR OMEGA_OS_KERNEL MODULES
Quality control before integration. Referencia: Two Sigma Code Review Standards.
"""
import ast, json, os
from pathlib import Path

NEBULAR_MODULES = Path(r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\OMEGA_OS_Kernel\modules")

MODULES = [
    "risk_metrics.py",
    "fractal_hurst.py",
    "kalman_pullback_engine.py",
    "zone_navigator.py",
    "lot_calculator.py",
    "momentum_physics.py",
    "volume_profile.py",
    "volume_physics.py",
    "anomaly_detector.py",
    "v_flow_microstructure.py",
    "risk_valves_v31.py",
    "squeeze_detector.py",
    "fimathe_core.py",
    "backtest_engine.py",
    "omega_confluence_engine.py",
    "omega_parr_f_engine.py",
    "omega_kernel_v5_1_refined.py",
]

# Existing SOURCE_CODE modules (to check for overlap)
SOURCE_CODE = Path(r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE")
existing = set(p.name for p in SOURCE_CODE.rglob("*.py"))

PRIORITY_MAP = {
    "risk_metrics.py":           ("CRITICAL", "Calcula VaR, CVaR, Sharpe, Calmar — preenche gap da avaliação institucional"),
    "fractal_hurst.py":          ("HIGH",     "Hurst exponent para classificação de regime — melhora edge gate"),
    "kalman_pullback_engine.py": ("HIGH",     "Kalman pullback detection — melhora timing de entrada"),
    "zone_navigator.py":         ("HIGH",     "Suporte/resistência institucional — confirmação de zona"),
    "lot_calculator.py":         ("MEDIUM",   "LotCalc mais completo — comparar com LotCalculatorV2"),
    "momentum_physics.py":       ("MEDIUM",   "Análise física de momentum — signal refinement"),
    "volume_profile.py":         ("MEDIUM",   "Volume profile — quality of entry"),
    "volume_physics.py":         ("MEDIUM",   "Microestrutura de volume"),
    "anomaly_detector.py":       ("MEDIUM",   "Detecção de anomalias — complementa VAE do OmegaQuantumBrain"),
    "v_flow_microstructure.py":  ("MEDIUM",   "Order flow microstructure"),
    "risk_valves_v31.py":        ("MEDIUM",   "Válvulas dinâmicas de risco"),
    "squeeze_detector.py":       ("LOW",      "Squeeze de volatilidade — signal filter"),
    "fimathe_core.py":           ("LOW",      "Matemática Fibonacci — suporte aos harmônicos"),
    "backtest_engine.py":        ("LOW",      "Motor de backtest — avaliar separadamente"),
    "omega_confluence_engine.py":("LOW",      "Engine de confluência — verificar overlap com MFAEngine"),
    "omega_parr_f_engine.py":    ("LOW",      "PARR-F engine — já existe versão em SOURCE_CODE"),
    "omega_kernel_v5_1_refined.py":("LOW",    "Kernel v5.1 — pode sobrescrever lógica atual"),
}

def check_module(filepath: Path) -> dict:
    name = filepath.name
    if not filepath.exists():
        return {"name": name, "status": "FILE_NOT_FOUND", "readiness": "BLOCKED"}

    size_kb = round(filepath.stat().st_size / 1024, 1)
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except:
        return {"name": name, "status": "UNREADABLE", "readiness": "BLOCKED"}

    checks = {}
    issues = []
    notes = []

    # 1. Sintaxe válida
    try:
        ast.parse(content)
        checks["syntax_ok"] = True
    except SyntaxError as e:
        checks["syntax_ok"] = False
        issues.append(f"SyntaxError: {e}")

    # 2. Dependências externas
    import_lines = [l.strip() for l in content.splitlines() if l.strip().startswith(("import ", "from "))]
    external_deps = []
    stdlib = {"os","sys","re","json","time","math","logging","datetime","typing","dataclasses",
              "enum","collections","abc","pathlib","hashlib","threading","copy","warnings",
              "itertools","functools","contextlib","io","struct","random"}
    for line in import_lines:
        parts = line.replace("from ", "").replace("import ", "").split()[0].split(".")[0]
        if parts not in stdlib:
            external_deps.append(parts)
    known_safe = {"numpy","pandas","scipy","sklearn","statsmodels","MetaTrader5",
                  "torch","numba","matplotlib","seaborn"}
    unsafe = [d for d in external_deps if d not in known_safe and not d.startswith("omega")]
    checks["deps_safe"] = len(unsafe) == 0
    if unsafe:
        issues.append(f"Deps nao verificadas: {unsafe}")

    # 3. Dependência de omega_integration_gate (pode ser standalone?)
    has_gate = "omega_integration_gate" in content
    has_try_except = ("try:" in content and "ImportError" in content and "omega_integration_gate" in content)
    checks["standalone_capable"] = (not has_gate) or has_try_except
    if has_gate and not has_try_except:
        issues.append("Requer omega_integration_gate SEM fallback — precisa adaptação")
        notes.append("Copiar omega_integration_gate.py também, ou refatorar herança")

    # 4. Error handling
    checks["has_error_handling"] = "try:" in content and "except" in content

    # 5. Sem secrets hardcoded
    secret_patterns = ["password=", "api_key=", "secret=", "token=", "AUTH_"]
    found_secrets = [p for p in secret_patterns if p.lower() in content.lower()]
    checks["no_secrets"] = len(found_secrets) == 0
    if found_secrets:
        issues.append(f"Possível secret: {found_secrets}")

    # 6. Funções/classes documentadas
    try:
        tree = ast.parse(content)
        classes = [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
        documented = sum(1 for n in classes if ast.get_docstring(n))
        checks["documented"] = documented > 0
    except:
        checks["documented"] = False

    # Calcular readiness
    critical_checks = ["syntax_ok", "deps_safe", "standalone_capable", "no_secrets"]
    blocking_fails = [k for k in critical_checks if not checks.get(k)]

    if not blocking_fails:
        readiness = "READY"
    elif blocking_fails == ["standalone_capable"] and has_gate and not has_try_except:
        readiness = "READY_WITH_ADAPTER"
    else:
        readiness = "NEEDS_REVIEW"

    # Já existe no source?
    in_source = name in existing

    priority, purpose = PRIORITY_MAP.get(name, ("UNKNOWN", "—"))

    return {
        "name": name,
        "size_kb": size_kb,
        "priority": priority,
        "purpose": purpose,
        "checks": checks,
        "issues": issues,
        "notes": notes,
        "readiness": readiness,
        "already_in_source": in_source,
        "external_deps": list(set(external_deps)),
        "needs_integration_gate": has_gate,
        "has_standalone_fallback": has_try_except,
    }

print("=" * 78)
print("  MODULE QUALITY REVIEW — NEBULAR OMEGA_OS_KERNEL/modules")
print("=" * 78)
print(f"  {'MÓDULO':<35} {'PRIO':<10} {'SIZE':>6}  {'READINESS':<20} {'ISSUES'}")
print("  " + "-" * 74)

results = []
for mod_name in MODULES:
    fp = NEBULAR_MODULES / mod_name
    r = check_module(fp)
    results.append(r)

    icon = {"READY": "✅", "READY_WITH_ADAPTER": "⚡", "NEEDS_REVIEW": "⚠️", "BLOCKED": "❌", "FILE_NOT_FOUND": "?"}.get(r["readiness"], "?")
    src_tag = " [JA EM SOURCE]" if r["already_in_source"] else ""
    issue_count = len(r.get("issues", []))
    issue_txt = f"{issue_count} issue(s)" if issue_count else "OK"

    print(f"  {icon} {r['name']:<33} {r.get('priority','?'):<10} {r.get('size_kb',0):>5.1f}KB  {r['readiness']:<20} {issue_txt}{src_tag}")

print()
ready    = [r for r in results if r["readiness"] == "READY"]
adapter  = [r for r in results if r["readiness"] == "READY_WITH_ADAPTER"]
review   = [r for r in results if r["readiness"] == "NEEDS_REVIEW"]

print(f"  ✅ READY:              {len(ready)}")
print(f"  ⚡ READY_WITH_ADAPTER: {len(adapter)}")
print(f"  ⚠️  NEEDS_REVIEW:       {len(review)}")

print("\n  PLANO DE INTEGRAÇÃO (ordem de prioridade):")
print("  " + "-" * 74)
priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
for prio in priority_order:
    group = [r for r in results if r.get("priority") == prio and r["readiness"] in ("READY", "READY_WITH_ADAPTER") and not r["already_in_source"]]
    for r in group:
        adapter_note = " [+omega_integration_gate]" if r["readiness"] == "READY_WITH_ADAPTER" else ""
        print(f"  [{prio}] {r['name']:<35} → {r['purpose']}{adapter_note}")

# Salvar
out = r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\logs\module_review_report.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n  Relatório salvo: {out}")
print("=" * 78)
