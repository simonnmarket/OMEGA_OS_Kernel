#!/usr/bin/env python3
"""
Verificação matinal — DEMO_LOG após corrida noturna (Fase E).

Uso:
  python verificar_demo_apos_noturno.py --csv "C:\\...\\DEMO_LOG_SWING_TRADE_YYYYMMDD_THHMM.csv"

Requisitos: pandas (ambiente do projeto).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser(description="Auditoria rápida de DEMO_LOG CSV")
    ap.add_argument("--csv", required=True, type=Path, help="Caminho para DEMO_LOG_*.csv")
    args = ap.parse_args()
    p = args.csv.resolve()
    if not p.is_file():
        print(f"ERRO: ficheiro não encontrado: {p}")
        return 1

    df = pd.read_csv(p)
    n = len(df)
    z_col = "z" if "z" in df.columns else None
    if not z_col:
        print("ERRO: coluna 'z' ausente.")
        print("Colunas:", list(df.columns))
        return 1

    z = pd.to_numeric(df[z_col], errors="coerce")
    z_abs = np.abs(z.dropna())

    sf = df["signal_fired"].astype(str).str.lower().isin(("true", "1")) if "signal_fired" in df.columns else None
    n_sig = int(sf.sum()) if sf is not None else -1

    print("=" * 60)
    print("VERIFICAÇÃO DEMO PÓS-NOTURNO — OMEGA")
    print("=" * 60)
    print(f"Ficheiro: {p}")
    print(f"Linhas de dados: {n}")
    if n_sig >= 0:
        print(f"signal_fired True: {n_sig}")
    print()
    print("[|Z| — estatísticas]")
    if len(z_abs) == 0:
        print("  (sem valores Z válidos)")
    else:
        print(f"  min:    {float(z_abs.min()):.6f}")
        print(f"  max:    {float(z_abs.max()):.6f}")
        print(f"  média:  {float(z_abs.mean()):.6f}")
        print(f"  P50:    {float(np.percentile(z_abs, 50)):.6f}")
        print(f"  P95:    {float(np.percentile(z_abs, 95)):.6f}")
        print(f"  P99:    {float(np.percentile(z_abs, 99)):.6f}")
    print()
    # Heurística simples (não substitui julgamento humano)
    if n == 0:
        print("STATUS: FALHA — log vazio.")
        return 2
    if len(z_abs) and float(z_abs.max()) < 1e-6:
        print("AVISO: |Z| efetivamente zero em todo o período — investigar feed/motor.")
    print("STATUS: Leitura OK — anexar este output ao RT-E.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
