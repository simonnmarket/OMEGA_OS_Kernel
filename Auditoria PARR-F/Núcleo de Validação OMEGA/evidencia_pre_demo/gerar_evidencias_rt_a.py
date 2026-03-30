#!/usr/bin/env python3
"""
Gera evidências objetivas para RT-A (Fase A — Custódia).

Uso (na raiz nebular-kuiper ou qualquer cwd):
  python gerar_evidencias_rt_a.py
  python gerar_evidencias_rt_a.py --out 04_relatorios_tarefa/RT_A_EVIDENCIAS_AUTO_20260331.md

Saída: texto/markdown em stdout e opcionalmente em ficheiro.
Requisitos: apenas biblioteca standard (csv, hashlib, subprocess).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_REPO = _SCRIPT_DIR.parent.parent.parent
REPO_ROOT = Path(os.environ.get("NEBULAR_KUIPER_ROOT", _DEFAULT_REPO)).resolve()
EVIDENCIA = _SCRIPT_DIR
LOGS = EVIDENCIA / "02_logs_execucao"
MANIFEST_DIR = EVIDENCIA / "03_hashes_manifestos"
VERIFY_SCRIPT = EVIDENCIA / "verify_tier0_psa.py"

STRESS_NAMES = (
    "STRESS_2Y_SWING_TRADE.csv",
    "STRESS_2Y_DAY_TRADE.csv",
    "STRESS_2Y_SCALPING.csv",
)


def _sha3_file(p: Path) -> str:
    h = hashlib.sha3_256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _git_head() -> str:
    r = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (r.stdout or "").strip() if r.returncode == 0 else "(git indisponível)"


def _run_verify() -> tuple[int, str]:
    if not VERIFY_SCRIPT.is_file():
        return 1, f"FALHA: {VERIFY_SCRIPT} não encontrado.\n"
    r = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def _parse_bool(s: str) -> bool:
    return s.strip().lower() in ("true", "1", "yes")


def _stress_stats(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"erro": f"ficheiro em falta: {path}"}
    n = 0
    fired = 0
    z_ge = 0
    z_vals: list[float] = []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "signal_fired" not in reader.fieldnames:
            return {"erro": "coluna signal_fired ausente"}
        z_col = "z" if "z" in reader.fieldnames else None
        for row in reader:
            n += 1
            if _parse_bool(row.get("signal_fired", "")):
                fired += 1
            if z_col:
                try:
                    z = float(row[z_col])
                    z_vals.append(z)
                    if abs(z) >= 3.75:
                        z_ge += 1
                except (TypeError, ValueError):
                    pass
    z_min = min(z_vals) if z_vals else float("nan")
    z_max = max(z_vals) if z_vals else float("nan")
    wild = sum(1 for z in z_vals if abs(z) > 1e6)
    return {
        "rows": n,
        "signal_fired_true": fired,
        "rows_abs_z_ge_3_75": z_ge,
        "z_min": z_min,
        "z_max": z_max,
        "rows_abs_z_gt_1e6": wild,
    }


def build_report() -> str:
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"# Evidências automáticas — RT-A (Custódia)\n")
    lines.append(f"**Gerado:** `{now}` (UTC)\n")
    lines.append(f"**REPO_ROOT:** `{REPO_ROOT}`\n")
    lines.append(f"**evidencia_pre_demo:** `{EVIDENCIA}`\n")
    lines.append("\n## Git\n")
    lines.append(f"- `git rev-parse HEAD`: `{_git_head()}`\n")

    lines.append("\n## Inventário — manifestos\n")
    if MANIFEST_DIR.is_dir():
        manifests = sorted(MANIFEST_DIR.glob("*.json"))
        if not manifests:
            lines.append("- *(nenhum .json em 03_hashes_manifestos)*\n")
        else:
            lines.append("| Ficheiro | Bytes | SHA3-256 (prefixo) |\n")
            lines.append("|----------|-------|---------------------|\n")
            for m in manifests:
                b = m.stat().st_size
                h = _sha3_file(m)
                lines.append(f"| `{m.name}` | {b} | `{h[:24]}…` |\n")
    else:
        lines.append("- *(pasta 03_hashes_manifestos em falta)*\n")

    lines.append("\n## Ficheiros de stress — bytes + SHA3-256 + contagens\n")
    lines.append(
        "| Ficheiro | Bytes | SHA3-256 | Linhas | signal_fired True | abs(z)>=3.75 | abs(z)>1e6 |\n"
    )
    lines.append("|----------|-------|----------|--------|-------------------|--------------|------------|\n")
    for name in STRESS_NAMES:
        p = LOGS / name
        if not p.is_file():
            lines.append(f"| `{name}` | — | — | — | — | — | — |\n")
            continue
        b = p.stat().st_size
        h = _sha3_file(p)
        st = _stress_stats(p)
        if "erro" in st:
            lines.append(f"| `{name}` | {b} | `{h[:16]}…` | *{st['erro']}* | | | |\n")
            continue
        lines.append(
            f"| `{name}` | {b} | `{h}` | {st['rows']} | {st['signal_fired_true']} | "
            f"{st['rows_abs_z_ge_3_75']} | {st['rows_abs_z_gt_1e6']} |\n"
        )

    lines.append("\n### Notas de leitura\n")
    lines.append(
        "- `signal_fired True` e contagens com abs(z)>=3.75 devem coincidir se o gateway ligar sinal ao limiar 3.75.\n"
    )
    lines.append("- Valores com abs(z)>1e6 indicam possível instabilidade numérica pontual.\n")

    lines.append("\n## verify_tier0_psa.py\n")
    code, out = _run_verify()
    lines.append(f"- **Exit code:** `{code}`\n")
    lines.append("\n```text\n")
    lines.append(out.rstrip() + "\n")
    lines.append("```\n")

    lines.append("\n## Próximo passo (humano)\n")
    lines.append(
        "1. Copiar este conteúdo para o RT-A oficial ou anexar como evidência.\n"
        "2. Redigir reconciliação textual com qualquer relatório externo que alegue zero sinais.\n"
        "3. Se `verify` falhar, alinhar manifesto e `git_commit_sha` antes de concluir a Fase A.\n"
    )
    return "".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Evidências RT-A — custódia")
    ap.add_argument(
        "--out",
        type=Path,
        help="Gravar relatório neste ficheiro (UTF-8)",
    )
    args = ap.parse_args()
    text = build_report()
    print(text, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"\n[OK] Escrito: {args.out.resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
