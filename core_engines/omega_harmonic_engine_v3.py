"""
OMEGA INTELLIGENCE OS — Motor Harmônico V3
Referência: OMEGA-AMI-V3-2026-0320
Classificação: CORE ENGINE — Zero Subjetividade
"""
import pandas as pd
import numpy as np
import hashlib
import argparse
import logging
import json
import sys
import os
import traceback
from datetime import datetime, timezone

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("omega_harmonic_v3.log", encoding="utf-8")
    ]
)
log = logging.getLogger("OMEGA_V3")


# ─── Criptografia ─────────────────────────────────────────────────────────────
def sha3_256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha3_256(f.read()).hexdigest()

def sha3_256_bytes(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


# ─── Carregamento e Validação de Dados ────────────────────────────────────────
REQUIRED_LINHA  = {"time", "linha"}
REQUIRED_CANDLE = {"time", "open", "high", "low", "close", "tick_volume"}

def load_and_validate(path: str, required_cols: set, label: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"[{label}] Arquivo não encontrado: {path}")

    df = pd.read_csv(path)

    # Fallback: volume -> tick_volume
    if "tick_volume" not in df.columns and "volume" in df.columns:
        df.rename(columns={"volume": "tick_volume"}, inplace=True)
        log.info(f"[{label}] Coluna 'volume' renomeada para 'tick_volume' (fallback).")

    # Normalizar colunas lowercase
    df.columns = [c.strip().lower() for c in df.columns]

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"[{label}] Colunas obrigatórias ausentes: {missing}")

    df["time"] = pd.to_datetime(df["time"], utc=False, errors="coerce")
    if df["time"].isna().any():
        raise ValueError(f"[{label}] Timestamps inválidos detectados após parse.")

    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    log.info(f"[{label}] Carregado e validado: {len(df)} linhas.")
    return df


# ─── Merge Robusto ────────────────────────────────────────────────────────────
def robust_merge(df_ln: pd.DataFrame, df_cd: pd.DataFrame) -> pd.DataFrame:
    df_merged = pd.merge_asof(
        df_ln, df_cd,
        on="time",
        direction="nearest",
        tolerance=pd.Timedelta("1s")
    )

    n_null = df_merged["open"].isna().sum()
    if n_null == len(df_merged):
        raise ValueError("merge_asof: zero correspondências. Verifique tolerância de tempo ou dados.")
    if n_null > 0:
        log.warning(f"merge_asof: {n_null} linhas sem correspondência candle — descartadas.")
        df_merged.dropna(subset=["open", "close", "tick_volume"], inplace=True)

    df_merged.reset_index(drop=True, inplace=True)
    log.info(f"Merge concluído: {len(df_merged)} linhas úteis.")
    return df_merged


# ─── Indicadores ──────────────────────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame, harm_fast: int, harm_slow: int, lookback: int) -> pd.DataFrame:
    df["h_fast"]      = df["linha"].ewm(span=harm_fast, adjust=False).mean()
    df["h_slow"]      = df["linha"].ewm(span=harm_slow, adjust=False).mean()
    df["accel_hz"]    = df["linha"].pct_change(lookback) * 10000
    body              = (df["open"] - df["close"]).abs().clip(lower=0.0001)
    df["wyckoff_eff"] = df["tick_volume"] / body
    df["slope"]       = (df["linha"] - df["linha"].shift(lookback)) / lookback
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ─── Detecção de Eventos ──────────────────────────────────────────────────────
def detect_events(df: pd.DataFrame, lookback: int, lookahead: int, margin: float) -> tuple:
    events = []
    hits   = {"34": 0, "134": 0}
    breaks = {"34": 0, "134": 0}

    n = len(df)
    for i in range(lookback, n - lookahead):
        row       = df.iloc[i]
        linha_px  = row["linha"]
        future_px = df.iloc[i + lookahead]["linha"]
        slope     = row["slope"]

        # Filtro de lateralidade
        if abs(slope) < 0.0001:
            continue

        for h_name, h_val in [("34", row["h_fast"]), ("134", row["h_slow"])]:
            if abs(linha_px - h_val) > margin:
                continue

            fut_delta  = future_px - linha_px
            is_support = slope > 0      # vindo de baixo
            outcome    = "NEUTRO"

            if is_support:
                if future_px > linha_px:
                    outcome = "HIT/DEFESA"
                    hits[h_name] += 1
                elif fut_delta < -margin:
                    outcome = "BREAK/RUPTURA"
                    breaks[h_name] += 1
            else:  # resistência
                if future_px < linha_px:
                    outcome = "HIT/DEFESA"
                    hits[h_name] += 1
                elif fut_delta > margin:
                    outcome = "BREAK/RUPTURA"
                    breaks[h_name] += 1

            if outcome != "NEUTRO":
                events.append({
                    "timestamp":     str(row["time"]),
                    "level":         h_name,
                    "price_touch":   round(float(linha_px), 5),
                    "harm_value":    round(float(h_val), 5),
                    "accel_hz":      round(float(row["accel_hz"]), 4),
                    "wyckoff_ratio": round(float(row["wyckoff_eff"]), 4),
                    "outcome":       outcome,
                    "future_delta":  round(float(fut_delta), 5),
                    "lookahead_used": lookahead
                })

    return events, hits, breaks


# ─── Construção do Relatório ──────────────────────────────────────────────────
def build_report(symbol, timeframe, agent_ver, h_linha, h_candle,
                 events, hits, breaks) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    def stats(h_name):
        t = hits[h_name] + breaks[h_name]
        return {
            "total_touches": t,
            "hits":          hits[h_name],
            "breaks":        breaks[h_name],
            "hit_rate":      round(hits[h_name] / t * 100, 2) if t else 0.0,
            "break_rate":    round(breaks[h_name] / t * 100, 2) if t else 0.0
        }

    return {
        "asset":             symbol,
        "timeframe":         timeframe,
        "status":            "COMPLETED",
        "created_at":        now,
        "updated_at":        now,
        "agent_version":     agent_ver,
        "omega_integration": False,
        "checksum_sources":  {"linha": h_linha, "candle": h_candle},
        "engines": {
            "harmonic": {
                "metrics": {
                    "34_stats":  stats("34"),
                    "134_stats": stats("134")
                },
                "events": events
            }
        }
    }


# ─── Salvamento de Outputs ────────────────────────────────────────────────────
def save_outputs(report: dict, symbol: str, timeframe: str) -> str:
    json_bytes = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")
    final_hash = sha3_256_bytes(json_bytes)
    report["checksum"] = final_hash

    # Re-serializar com checksum embutido
    json_bytes = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")

    json_path = f"harmonic_events_{symbol}_{timeframe}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_bytes.decode("utf-8"))

    # CSV opcional
    if report["engines"]["harmonic"]["events"]:
        csv_path = f"harmonic_events_{symbol}_{timeframe}.csv"
        pd.DataFrame(report["engines"]["harmonic"]["events"]).to_csv(csv_path, index=False)
        log.info(f"CSV salvo: {csv_path}")

    return final_hash


# ─── Fail Safe ────────────────────────────────────────────────────────────────
def save_failed_report(symbol: str, timeframe: str, reason: str):
    fail = {
        "asset":      symbol,
        "timeframe":  timeframe,
        "status":     "FAILED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reason":     reason
    }
    json_bytes = json.dumps(fail, indent=2).encode("utf-8")
    fail["checksum"] = sha3_256_bytes(json_bytes)
    with open(f"harmonic_events_{symbol}_{timeframe}.json", "w") as f:
        json.dump(fail, f, indent=2)
    log.error(f"JSON FAILED salvo para {symbol} {timeframe}. Motivo: {reason}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Motor Harmônico OMEGA V3 — CQO/CKO Certified"
    )
    parser.add_argument("--symbol",     type=str,   required=True)
    parser.add_argument("--timeframe",  type=str,   required=True)
    parser.add_argument("--base_path",  type=str,   default=r"C:\OMEGA_PROJETO\OHLCV_DATA")
    parser.add_argument("--harm_fast",  type=int,   default=34)
    parser.add_argument("--harm_slow",  type=int,   default=134)
    parser.add_argument("--margin",     type=float, default=150.0)
    parser.add_argument("--lookback",   type=int,   default=3)
    parser.add_argument("--lookahead",  type=int,   default=5)
    args = parser.parse_args()

    AGENT_VER   = "ami_analyzer_v3.0"
    linha_path  = os.path.join(args.base_path, "grafico_linha",  f"{args.symbol}_{args.timeframe}.csv")
    candle_path = os.path.join(args.base_path, "grafico_candle", f"{args.symbol}_{args.timeframe}.csv")

    log.info("=" * 70)
    log.info(f"OMEGA Harmonic Engine V3 | {args.symbol} {args.timeframe}")
    log.info(f"harm_fast={args.harm_fast} | harm_slow={args.harm_slow} | margin={args.margin}")
    log.info("=" * 70)

    try:
        # Checksums de entrada
        h_linha  = sha3_256_file(linha_path)
        h_candle = sha3_256_file(candle_path)
        log.info(f"SHA3-256 linha:  {h_linha}")
        log.info(f"SHA3-256 candle: {h_candle}")

        # Carregamento
        df_ln = load_and_validate(linha_path,  REQUIRED_LINHA,  "LINHA")
        df_cd = load_and_validate(candle_path, REQUIRED_CANDLE, "CANDLE")

        # Merge
        df = robust_merge(df_ln, df_cd)
        if len(df) == 0:
            raise ValueError("DataFrame vazio após merge. Abortando.")

        # Indicadores
        df = compute_indicators(df, args.harm_fast, args.harm_slow, args.lookback)

        # Detecção
        events, hits, breaks = detect_events(df, args.lookback, args.lookahead, args.margin)
        log.info(f"Eventos detectados: {len(events)}")

        # Relatório
        report = build_report(
            args.symbol, args.timeframe, AGENT_VER,
            h_linha, h_candle, events, hits, breaks
        )

        final_hash = save_outputs(report, args.symbol, args.timeframe)

        t34  = hits["34"]  + breaks["34"]
        t134 = hits["134"] + breaks["134"]
        hr34  = round(hits["34"]  / t34  * 100, 2) if t34  else 0.0
        hr134 = round(hits["134"] / t134 * 100, 2) if t134 else 0.0

        log.info("-" * 70)
        log.info(f"EMA-34  | Toques: {t34:>6} | HIT: {hits['34']:>6} | BREAK: {breaks['34']:>6} | Hit Rate: {hr34:.2f}%")
        log.info(f"EMA-134 | Toques: {t134:>6} | HIT: {hits['134']:>6} | BREAK: {breaks['134']:>6} | Hit Rate: {hr134:.2f}%")
        log.info(f"Output JSON checksum (SHA3-256): {final_hash}")
        log.info("STATUS: COMPLETED")
        log.info("=" * 70)

    except Exception as exc:
        tb = traceback.format_exc()
        log.error(f"ERRO CRÍTICO: {exc}")
        log.error(tb)
        save_failed_report(args.symbol, args.timeframe, str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
