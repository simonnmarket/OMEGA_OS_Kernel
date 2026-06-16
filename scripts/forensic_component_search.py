"""
FORENSIC COMPONENT SEARCH — OMEGA SYSTEM RECOVERY v1.0
Busca componentes criticos em nebular-kuiper vs SOURCE_CODE atual.
"""
import os, re, json, hashlib
from pathlib import Path
from datetime import datetime

NEBULAR = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
SOURCE  = r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"

CRITICAL_COMPONENTS = {
    "calendario_economico": {
        "keywords": ["calendar","economic","forexfactory","investing","dailyfx","news_event","fomc","nfp","boj","macro_pause"],
        "priority": "CRITICAL", "integration_point": "Edge Gate → news pause"
    },
    "order_block": {
        "keywords": ["order_block","orderblock","ob_detect","liquidity_zone","institutional_order","supply_zone","demand_zone"],
        "priority": "HIGH", "integration_point": "Entry confirmation"
    },
    "walk_forward_oos": {
        "keywords": ["walk_forward","out_of_sample","oos_test","wf_validation","walk_forward_oos"],
        "priority": "HIGH", "integration_point": "Backtest validation"
    },
    "pullback_engine": {
        "keywords": ["pullback","retracement","pullback_engine","retest","fib_retracement","omega_pullback"],
        "priority": "HIGH", "integration_point": "Entry logic refinement"
    },
    "mfa_engine": {
        "keywords": ["mfa_engine","multi_factor","omega_mfa","factor_score","composite_signal"],
        "priority": "HIGH", "integration_point": "Signal aggregation"
    },
    "integration_gate": {
        "keywords": ["integration_gate","omega_integration","gate_pass","pre_trade_gate"],
        "priority": "HIGH", "integration_point": "Pre-trade validation"
    },
    "trailing_stop": {
        "keywords": ["trailing","trail_stop","atr_trail","chandelier","dynamic_sl","break_even_trail"],
        "priority": "MEDIUM", "integration_point": "Position management"
    },
    "dashboard": {
        "keywords": ["dashboard","grafana","kibana","streamlit","flask","fastapi","plotly","web_monitor"],
        "priority": "MEDIUM", "integration_point": "Monitoring"
    },
    "regime_classifier": {
        "keywords": ["regime","market_regime","trending","ranging","volatility_regime","hurst","fractal"],
        "priority": "MEDIUM", "integration_point": "Strategy selection"
    },
    "genesis_core": {
        "keywords": ["genesis","quantum","neural","optimization","intelligence_os","omega_os_kernel"],
        "priority": "HIGH", "integration_point": "Next-gen architecture"
    }
}

def sha3(path):
    h = hashlib.sha3_256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except:
        return "ERROR"

def read_preview(path, max_bytes=3000):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except:
        return ""

def scan_path(base, exts=(".py",".json",".md",".txt",".yaml",".yml"), max_depth=6):
    result = []
    b = Path(base)
    if not b.exists():
        return result
    def _walk(p, depth):
        if depth > max_depth:
            return
        try:
            for item in p.iterdir():
                try:
                    if item.is_file() and item.suffix.lower() in exts:
                        result.append(item)
                    elif item.is_dir():
                        _walk(item, depth + 1)
                except (OSError, PermissionError):
                    pass
        except (OSError, PermissionError):
            pass
    _walk(b, 0)
    return result

def search_keywords(content, keywords):
    cl = content.lower()
    hits = [k for k in keywords if k.lower() in cl]
    return hits

print("=" * 72)
print("  OMEGA FORENSIC COMPONENT SEARCH — 2026-04-29")
print("=" * 72)

print(f"\n[SCAN] nebular-kuiper ...", end=" ")
nebular_files = scan_path(NEBULAR)
print(f"{len(nebular_files)} arquivos")

print(f"[SCAN] SOURCE_CODE ...", end=" ")
source_files = scan_path(SOURCE)
print(f"{len(source_files)} arquivos")

# Indexar SOURCE_CODE para comparação
source_index = {}
for f in source_files:
    source_index[f.name] = {"path": str(f), "hash": sha3(str(f))}

# Resultado forense
report = {
    "gerado_em": datetime.now().isoformat(),
    "nebular_total_files": len(nebular_files),
    "source_total_files":  len(source_files),
    "components": {},
    "exclusive_nebular": [],   # Existe SOMENTE em nebular (não integrado)
    "conflicts": [],           # Mesmo nome, hash diferente
}

print("\n[BUSCA] Componentes críticos...\n")

for comp_name, cfg in CRITICAL_COMPONENTS.items():
    found_nebular = []
    for f in nebular_files:
        if f.suffix not in (".py", ".txt", ".md"):
            continue
        content = read_preview(str(f))
        hits = search_keywords(content, cfg["keywords"])
        if hits:
            in_source = f.name in source_index
            found_nebular.append({
                "file":     str(f.relative_to(NEBULAR)),
                "abs":      str(f),
                "size_kb":  round(f.stat().st_size / 1024, 1),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"),
                "hash":     sha3(str(f)),
                "keywords_hit": hits,
                "in_source_code": in_source,
            })

    found_nebular.sort(key=lambda x: (-x["size_kb"], x["modified"]))

    status = "ENCONTRADO" if found_nebular else "NAO_ENCONTRADO"
    not_integrated = [x for x in found_nebular if not x["in_source_code"]]
    best = found_nebular[0] if found_nebular else None

    report["components"][comp_name] = {
        "priority": cfg["priority"],
        "integration_point": cfg["integration_point"],
        "status": status,
        "total_instances": len(found_nebular),
        "not_integrated": len(not_integrated),
        "best_candidate": best,
    }

    icon = "✅" if found_nebular and not not_integrated else ("⚠️" if not_integrated else "❌")
    print(f"  {icon} {comp_name:<25} [{cfg['priority']:<8}] "
          f"{'encontrado: ' + str(len(found_nebular)) + ' arquivo(s), ' + str(len(not_integrated)) + ' nao integrado(s)' if found_nebular else 'NAO ENCONTRADO'}")
    if best and not best["in_source_code"]:
        print(f"       → CANDIDATO: {best['file']} ({best['size_kb']}KB, {best['modified']})")

# Identificar arquivos exclusivos do nebular (potencialmente valiosos)
print("\n[ANÁLISE] Arquivos Python exclusivos do nebular (não presentes no SOURCE_CODE)...")
exclusive = []
for f in nebular_files:
    if f.suffix != ".py":
        continue
    if f.name in source_index:
        nb_hash = sha3(str(f))
        src_hash = source_index[f.name]["hash"]
        if nb_hash != src_hash:
            report["conflicts"].append({
                "name": f.name,
                "nebular": str(f),
                "source": source_index[f.name]["path"],
                "nebular_hash": nb_hash,
                "source_hash": src_hash,
                "nebular_size_kb": round(f.stat().st_size/1024, 1),
            })
    else:
        size_kb = round(f.stat().st_size / 1024, 1)
        if size_kb > 2.0:  # Apenas arquivos relevantes (> 2KB)
            content = read_preview(str(f), 500)
            exclusive.append({
                "file": f.name,
                "path": str(f.relative_to(NEBULAR)),
                "size_kb": size_kb,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"),
                "preview": content[:200].replace("\n", " ")
            })

exclusive.sort(key=lambda x: -x["size_kb"])
report["exclusive_nebular"] = exclusive[:30]  # Top 30 maiores

print(f"\n  Top 15 arquivos exclusivos do nebular (maior potencial):")
print(f"  {'ARQUIVO':<45} {'TAMANHO':>8}  {'DATA'}")
print("  " + "-" * 68)
for e in exclusive[:15]:
    print(f"  {e['file']:<45} {e['size_kb']:>6.1f}KB  {e['modified']}")

print(f"\n  Conflitos (mesmo nome, hash diferente): {len(report['conflicts'])}")
for c in report["conflicts"][:5]:
    print(f"  ⚠️  {c['name']}: nebular({c['nebular_size_kb']}KB) vs source")

# Salvar relatório
out = r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\logs\forensic_report_20260429.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n[REPORT] Salvo: {out}")

# Resumo final
found_total = sum(1 for c in report["components"].values() if c["status"] == "ENCONTRADO")
not_integrated_total = sum(c["not_integrated"] for c in report["components"].values())
print("\n" + "=" * 72)
print("  RESUMO EXECUTIVO")
print("=" * 72)
print(f"  Componentes encontrados:      {found_total}/{len(CRITICAL_COMPONENTS)}")
print(f"  Instâncias não integradas:    {not_integrated_total}")
print(f"  Arquivos exclusivos nebular:  {len(exclusive)}")
print(f"  Conflitos de versão:          {len(report['conflicts'])}")
print("=" * 72)
