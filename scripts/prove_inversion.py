#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prove_inversion.py — Diagnóstico Forense de Inversão de Sinal
==============================================================
ID        : OIS-DIAG-20260517-PROVE-INVERSION
Emitido   : 2026-05-17 (CEO + CKO recomendação, Tech Lead Q-003)
Referência: OMEGA-DIAG-SEMANA-11-15-MAI-2026

CRITÉRIOS DE ACEITE (definidos pelo CEO):
  < 40% concordância  → sinal INVERTIDO    → inverter BUY/SELL (requer aprovação)
  40–60% concordância → sinal ALEATÓRIO    → desactivar permanentemente
  > 60% concordância  → sinal CORRECTO     → problema de edge/regime, não de inversão

NOTA (Tech Lead Q-003): "concordância" = % de trades onde direcção executada gerou
PnL > 0 (proxy para direcção_prevista == direcção_correta do mercado).
Para conclusão definitiva de inversão, cruzar com decision_trace.jsonl se disponível.

USO:
  python scripts/prove_inversion.py
  python scripts/prove_inversion.py --source MOMENTUM_MT5
  python scripts/prove_inversion.py --source MOMENTUM_MT5 --jsonl path/custom.jsonl
"""

import json
import os
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone, timedelta

DEFAULT_JSONL = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/trade_feedback.jsonl")
DECISION_TRACE = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/decision_trace.jsonl")


def load_trades(jsonl_path: Path, source_filter: str = None,
                start_date: datetime = None) -> list:
    """
    Carrega trades do JSONL.

    AVISO RED TEAM (OIS-DIAG-20260517):
    Dados anteriores ao deploy do PSA-015 contêm duplicatas (43% do total).
    Usar --start-date com a data UTC de activação do PSA-015 para dados limpos.
    Avaliar com dados duplicados = lixo in, lixo out.
    """
    trades = []
    if not jsonl_path.exists():
        print(f"[ERRO] Ficheiro não encontrado: {jsonl_path}")
        return trades
    skipped_before_cutoff = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line)
            except json.JSONDecodeError:
                continue
            if t.get("event_type") != "position_closed":
                continue
            if source_filter and t.get("signal_source") != source_filter:
                continue
            # RT1: filtro temporal — excluir dados pré-PSA-015 (envenenados por duplicatas)
            if start_date is not None:
                ts_raw = t.get("ts") or t.get("timestamp") or t.get("close_time")
                if ts_raw:
                    try:
                        if isinstance(ts_raw, (int, float)):
                            trade_dt = datetime.fromtimestamp(float(ts_raw), tz=timezone.utc)
                        else:
                            trade_dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                        if trade_dt < start_date:
                            skipped_before_cutoff += 1
                            continue
                    except (ValueError, OSError):
                        pass  # timestamp inválido — incluir por precaução
            trades.append(t)
    if start_date is not None and skipped_before_cutoff > 0:
        print(f"  [FILTRO] {skipped_before_cutoff} trades excluídos (anteriores a {start_date.date()} — pré-PSA-015)")
    return trades


def load_decision_trace(trace_path: Path, source_filter: str = None) -> dict:
    """Carrega decision_trace.jsonl indexado por ticket para cruzamento."""
    trace = {}
    if not trace_path.exists():
        return trace
    with open(trace_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line)
                ticket = t.get("ticket") or t.get("position_ticket")
                if ticket:
                    trace[int(ticket)] = t
            except (json.JSONDecodeError, ValueError):
                continue
    return trace


def concordance_analysis(trades: list, trace: dict) -> dict:
    """
    Calcula concordância: % de trades onde direcção executada correspondeu
    a resultado positivo (proxy de correctividade do sinal).
    Se decision_trace disponível, usa signal_predicted_dir vs signal_executed_dir.
    """
    if not trades:
        return {}

    total = len(trades)
    wins = sum(1 for t in trades if float(t.get("pnl", 0)) > 0)
    losses = total - wins
    concordance_pct = wins / total if total > 0 else 0.0

    total_pnl = sum(float(t.get("pnl", 0)) for t in trades)
    inverted_pnl = -total_pnl

    # Cruzar com decision_trace se disponível
    trace_mismatches = 0
    trace_checked = 0
    for t in trades:
        ticket = t.get("position_ticket") or t.get("ticket")
        if ticket and int(ticket) in trace:
            tr = trace[int(ticket)]
            pred = tr.get("signal_predicted_dir") or tr.get("dir")
            exec_d = t.get("direction")
            if pred and exec_d:
                trace_checked += 1
                if pred.upper() != exec_d.upper():
                    trace_mismatches += 1

    # By regime
    by_regime = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})
    for t in trades:
        regime = t.get("regime", "UNKNOWN")
        by_regime[regime]["total"] += 1
        by_regime[regime]["pnl"] += float(t.get("pnl", 0))
        if float(t.get("pnl", 0)) > 0:
            by_regime[regime]["wins"] += 1

    # By asset
    by_asset = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})
    for t in trades:
        sym = t.get("symbol", "UNKNOWN")
        by_asset[sym]["total"] += 1
        by_asset[sym]["pnl"] += float(t.get("pnl", 0))
        if float(t.get("pnl", 0)) > 0:
            by_asset[sym]["wins"] += 1

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "concordance_pct": round(concordance_pct * 100, 2),
        "total_pnl": round(total_pnl, 2),
        "inverted_pnl": round(inverted_pnl, 2),
        "trace_checked": trace_checked,
        "trace_mismatches": trace_mismatches,
        "trace_mismatch_pct": round(trace_mismatches / trace_checked * 100, 2) if trace_checked > 0 else None,
        "by_regime": dict(by_regime),
        "by_asset": dict(by_asset),
    }


def apply_verdict(concordance_pct: float) -> tuple:
    """
    Aplica critérios de aceite definidos pelo CEO.
    Retorna (verdict_code, verdict_text, action_required).
    """
    if concordance_pct < 40.0:
        return (
            "INVERTIDO",
            f"Sinal INVERTIDO — concordância {concordance_pct:.1f}% < 40%",
            "Inverter BUY/SELL no gerador de sinal (requer aprovação CEO + A/B paper com N >= 30 trades pós-flag)"
        )
    elif concordance_pct <= 60.0:
        return (
            "ALEATORIO",
            f"Sinal ALEATÓRIO — concordância {concordance_pct:.1f}% entre 40-60%",
            # RT3: 'permanente' substituído — Red Team / Conselho (OIS-DIAG-20260517)
            "Desactivar por período indeterminado. "
            "Reactivação exige homologação explícita via A/B Test isolado "
            "(CN-Quant-T1 Phase 3) aprovado pelo Conselho."
        )
    else:
        return (
            "CORRECTO",
            f"Sinal CORRECTO — concordância {concordance_pct:.1f}% > 60%",
            "Problema é de edge/regime, não de inversão — investigar EDGE_GATE e regime filter"
        )


def print_report(source: str, result: dict, jsonl_path: Path):
    print("\n" + "=" * 70)
    print(f"  OMEGA PROVE INVERSION — {source}")
    print(f"  Fonte: {jsonl_path}")
    print(f"  Executado: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    c = result["concordance_pct"]
    verdict_code, verdict_text, action = apply_verdict(c)

    print(f"\n  TRADES        : {result['total_trades']}")
    print(f"  WINS          : {result['wins']}  ({c:.1f}%)")
    print(f"  LOSSES        : {result['losses']}")
    print(f"  PnL REAL      : ${result['total_pnl']:.2f}")
    print(f"  PnL INVERTIDO : ${result['inverted_pnl']:.2f}  (hipotético se sinal fosse oposto)")

    if result["trace_checked"] > 0:
        print(f"\n  DECISION TRACE: {result['trace_checked']} trades cruzados")
        print(f"  MISMATCHES    : {result['trace_mismatches']} ({result['trace_mismatch_pct']:.1f}%)")
    else:
        print(f"\n  DECISION TRACE: não disponível (decision_trace.jsonl ausente ou sem dados)")
        print(f"  NOTA          : concordância calculada via PnL proxy (wins/total)")

    print(f"\n{'─'*70}")
    print(f"  VEREDICTO     : {verdict_code}")
    print(f"  {verdict_text}")
    print(f"  ACÇÃO         : {action}")
    print(f"{'─'*70}")

    print(f"\n  POR REGIME:")
    for regime, d in sorted(result["by_regime"].items()):
        wr = d["wins"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"    {regime:<20} trades={d['total']:>4}  WR={wr:5.1f}%  PnL=${d['pnl']:+.2f}")

    print(f"\n  POR ACTIVO (top 10 por trades):")
    top_assets = sorted(result["by_asset"].items(), key=lambda x: x[1]["total"], reverse=True)[:10]
    for sym, d in top_assets:
        wr = d["wins"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"    {sym:<12} trades={d['total']:>4}  WR={wr:5.1f}%  PnL=${d['pnl']:+.2f}")

    print("\n" + "=" * 70 + "\n")
    return verdict_code


def main():
    parser = argparse.ArgumentParser(description="Diagnóstico forense de inversão de sinal OMEGA")
    parser.add_argument("--source", default="MOMENTUM_MT5",
                        help="signal_source a analisar (default: MOMENTUM_MT5)")
    parser.add_argument("--jsonl", default=str(DEFAULT_JSONL),
                        help="Caminho para trade_feedback.jsonl")
    parser.add_argument("--all-sources", action="store_true",
                        help="Analisar todas as fontes no ficheiro")
    parser.add_argument(
        "--start-date",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "RT1: Data UTC de corte (formato YYYY-MM-DD). "
            "Excluir dados anteriores ao deploy do PSA-015 para evitar contaminação por duplicatas. "
            "Exemplo: --start-date 2026-05-15"
        )
    )
    args = parser.parse_args()

    # RT1: parse do start_date
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            print(f"  [FILTRO ACTIVO] Apenas trades >= {start_date.date()} (pós-PSA-015)")
        except ValueError:
            print(f"[ERRO] --start-date formato inválido: '{args.start_date}' — usar YYYY-MM-DD")
            return
    else:
        print("  [AVISO RED TEAM] --start-date não definido. Dados pré-PSA-015 incluídos.")
        print("  Dados anteriores ao deploy PSA-015 contêm ~43% duplicatas — resultados enviesados.")
        print("  Usar: --start-date YYYY-MM-DD (data UTC do deploy PSA-015)\n")

    jsonl_path = Path(args.jsonl)
    trace = load_decision_trace(DECISION_TRACE)

    if args.all_sources:
        all_trades = load_trades(jsonl_path, start_date=start_date)
        sources = list({t.get("signal_source", "UNKNOWN") for t in all_trades})
        print(f"\n[INFO] Analisando {len(sources)} fontes: {sources}")
        verdicts = {}
        for src in sorted(sources):
            filtered = [t for t in all_trades if t.get("signal_source") == src]
            # N mínimo 30 para dados pós-PSA-015 (Red Team RT1); 5 para análise exploratória
            _n_min = 30 if start_date is not None else 5
            if len(filtered) < _n_min:
                print(f"\n  {src}: apenas {len(filtered)} trades — N < {_n_min} (mínimo para conclusão válida), skip")
                continue
            result = concordance_analysis(filtered, trace)
            verdict_code = print_report(src, result, jsonl_path)
            verdicts[src] = verdict_code

        print("\n  SUMÁRIO GERAL:")
        for src, v in sorted(verdicts.items()):
            print(f"    {src:<25} → {v}")
        print()
    else:
        trades = load_trades(jsonl_path, source_filter=args.source, start_date=start_date)
        if not trades:
            print(f"\n[ERRO] Nenhum trade encontrado para signal_source='{args.source}' em {jsonl_path}")
            return
        # PSA Council §3.2: N mínimo uniforme — aplica em single-source quando --start-date activo
        _n_min = 30 if start_date is not None else 5
        if len(trades) < _n_min:
            print(f"\n[AVISO] {args.source}: apenas {len(trades)} trades — N < {_n_min} (mínimo para conclusão válida pós-PSA-015)")
            print(f"  Resultado é exploratório. Aguardar N>={_n_min} trades antes de decisão operacional.")
        result = concordance_analysis(trades, trace)
        print_report(args.source, result, jsonl_path)


if __name__ == "__main__":
    main()
