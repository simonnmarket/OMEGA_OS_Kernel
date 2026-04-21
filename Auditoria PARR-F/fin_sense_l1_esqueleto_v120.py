import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import psycopg2
import psycopg2.extras

logger = logging.getLogger("FIN_SENSE.L1")

class FinSenseL1Layer:
    """
    Camada L1 - Integração Direta com PostgreSQL (Produção/DSN Real).
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        self._dsn = dsn or os.environ.get("FIN_SENSE_DSN", "").strip()
        self._view = os.environ.get("FIN_SENSE_L1_VIEW", "v_omega_l1_features").strip()

    def compute_metrics(self, symbol: str) -> Dict[str, Any]:
        if not self._dsn:
            return self._no_data(symbol, ["FIN_SENSE_DSN_NOT_SET"])

        sql = f"""
            SELECT
                symbol,
                var_95_usd,
                cvar_95_usd,
                regime_data,
                momentum_1m_pct,
                effective_spread
            FROM {self._view}
            WHERE symbol = %s
            LIMIT 1
        """

        try:
            conn = psycopg2.connect(self._dsn)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (symbol,))
                row = cur.fetchone()
            conn.close()
        except Exception as e:
            return self._no_data(symbol, [f"POSTGRES_ERROR:{e}"])

        if not row:
            return self._no_data(symbol, ["NO_RECENT_ROW"])

        record = {k: row[k] for k in row}
        canonical = json.dumps(record, sort_keys=True, default=str, ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        regime_val = str(record.get("regime_data") or "UNKNOWN")
        momentum_val = float(record.get("momentum_1m_pct") or 0.0)
        
        cynical_errors = []
        if regime_val in ["HIGH_VOLATILITY", "KILL_SWITCH"]:
            cynical_errors.append(f"DEAD_MAN_OUT: Regime Inaceitável ({regime_val})")
        elif abs(momentum_val) < 0.80:
            cynical_errors.append(f"CÍNICO_HOLD: Momentum insignificante ({momentum_val} < 0.80)")

        return {
            "symbol": record.get("symbol", symbol),
            "var_95_usd": float(record.get("var_95_usd") or 0.0),
            "cvar_95_usd": float(record.get("cvar_95_usd") or 0.0),
            "regime_data": regime_val,
            "momentum_1m_pct": momentum_val,
            "effective_spread": float(record.get("effective_spread") or 0.0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provenance_sha256": digest,
            "errors": cynical_errors,
            "extras": {
                "source": "FIN_SENSE_DSN",
                "engine": "PostgreSQL"
            },
        }

    def _no_data(self, symbol: str, errors: List[str]) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "var_95_usd": float("nan"),
            "cvar_95_usd": float("nan"),
            "regime_data": "NO_DATA_AVAILABLE",
            "momentum_1m_pct": 0.0,
            "effective_spread": float("nan"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provenance_sha256": "",
            "errors": errors,
            "extras": {"source": "FIN_SENSE_DSN"}
        }
