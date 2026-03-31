#!/usr/bin/env python3
"""
PSA — Gate único Tier-0 + métricas objectivas (Conselho / Compliance).

Executa em sequência:
  1) git rev-parse HEAD
  2) audit_trade_count.py no STRESS_V10_5_SWING_TRADE.csv (métricas numéricas)
  3) verify_tier0_psa.py (manifesto + ficheiros + gateway)

Critério de sucesso: passos 2 e 3 com código de saída 0.

Uso (na raiz nebular-kuiper):
  python psa_gate_conselho_tier0.py
  python psa_gate_conselho_tier0.py --repo-root "D:\\path\\nebular-kuiper"
  python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_ULTIMO.txt

Variável: NEBULAR_KUIPER_ROOT (opcional).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_REPO = _SCRIPT_DIR.parent.parent.parent


def _run(
    argv: list[str],
    cwd: Path,
    label: str,
) -> tuple[int, str]:
    r = subprocess.run(
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, f"=== {label} (exit {r.returncode}) ===\n{out}\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="PSA Gate Conselho Tier-0")
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=Path(os.environ.get("NEBULAR_KUIPER_ROOT", _DEFAULT_REPO)).resolve(),
        help="Raiz do repositório nebular-kuiper",
    )
    ap.add_argument(
        "--out-relatorio",
        type=Path,
        default=None,
        help="Opcional: gravar relatório texto (caminho relativo ao repo ou absoluto)",
    )
    args = ap.parse_args()

    repo = args.repo_root.resolve()
    os.environ["NEBULAR_KUIPER_ROOT"] = str(repo)

    evid = repo / "Auditoria PARR-F" / "Núcleo de Validação OMEGA" / "evidencia_pre_demo"
    audit_py = evid / "audit_trade_count.py"
    verify_py = evid / "verify_tier0_psa.py"
    stress_csv = evid / "02_logs_execucao" / "STRESS_V10_5_SWING_TRADE.csv"
    py = sys.executable

    blocks: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1) Git HEAD
    r_git = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    head = (r_git.stdout or "").strip()
    blocks.append(f"=== GIT HEAD (exit {r_git.returncode}) ===\n{head or '(indisponível)'}\n")

    # 2) audit_trade_count
    if not audit_py.is_file():
        print(f"ERRO: não encontrado: {audit_py}", file=sys.stderr)
        return 2
    code_a, out_a = _run(
        [py, str(audit_py), "--csv", str(stress_csv), "--expect-rows", "100000", "--min-signals", "1"],
        cwd=repo,
        label="audit_trade_count.py STRESS_V10_5",
    )
    blocks.append(out_a)

    # 3) verify_tier0
    if not verify_py.is_file():
        print(f"ERRO: não encontrado: {verify_py}", file=sys.stderr)
        return 2
    code_v, out_v = _run([py, str(verify_py)], cwd=repo, label="verify_tier0_psa.py")
    blocks.append(out_v)

    report = (
        f"PSA_GATE_CONSELHO_TIER0\n"
        f"timestamp_utc: {ts}\n"
        f"repo_root: {repo}\n"
        f"stress_csv: {stress_csv}\n\n"
        + "\n".join(blocks)
        + f"\n--- RESUMO ---\n"
        f"audit_trade_count exit: {code_a}\n"
        f"verify_tier0_psa exit: {code_v}\n"
        f"GATE_GLOBAL: {'PASS' if (code_a == 0 and code_v == 0) else 'FAIL'}\n"
    )

    print(report)

    if args.out_relatorio:
        out_p = args.out_relatorio
        if not out_p.is_absolute():
            out_p = (evid / out_p).resolve() if not str(out_p).startswith("..") else (repo / out_p).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(report, encoding="utf-8")
        print(f"Relatório gravado: {out_p}")

    return 0 if (code_a == 0 and code_v == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
