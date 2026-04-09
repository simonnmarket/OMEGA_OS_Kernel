"""
L1 FIN-SENSE — esqueleto v1.2.0 (contrato TIER-0)
ID: REQ-PARRF-DIRETRIZES-CRITICAS-CODIGO-TIER0-V120-20260411

- Sem credenciais no código: usar env FIN_SENSE_DSN
- SQL: VIEW configurável (FIN_SENSE_L1_VIEW) — ajustar ao DDL real do Conselho
- Não assume colunas analíticas em tabela de ticks RAW sem documentação
- provenance_sha256: JSON canónico (sorted keys) das colunas lidas

Agentes IA: não copiar SQL literal sem validar DDL em staging.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("FIN_SENSE.L1")


class FinSenseL1Layer:
    """
    Implementa o contrato compute_metrics(symbol) -> dict alinhado ao orquestrador v1.2.0.
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        self._dsn = dsn or os.environ.get("FIN_SENSE_DSN", "").strip()
        raw_view = os.environ.get(
            "FIN_SENSE_L1_VIEW",
            "v_omega_l1_features_by_symbol",
        ).strip()
        if not raw_view.replace("_", "").isalnum():
            raise ValueError("FIN_SENSE_L1_VIEW: apenas [a-zA-Z0-9_]")
        self._view = raw_view

    def compute_metrics(self, symbol: str) -> Dict[str, Any]:
        if not self._dsn:
            logger.warning("FIN_SENSE_DSN vazio — NO_DATA")
            return self._no_data(symbol, ["FIN_SENSE_DSN_NOT_SET"])

        try:
            import psycopg2  # type: ignore
            import psycopg2.extras  # type: ignore
        except ImportError:
            return self._no_data(symbol, ["PSYCOPG2_NOT_INSTALLED"])

        sql = f"""
            SELECT
                symbol,
                var_95_usd,
                cvar_95_usd,
                regime_data,
                momentum_1m_pct,
                effective_spread,
                source_batch_id,
                computed_at
            FROM {self._view}
            WHERE symbol = %s
            ORDER BY computed_at DESC NULLS LAST
            LIMIT 1
        """

        try:
            conn = psycopg2.connect(self._dsn)
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, (symbol,))
                    row = cur.fetchone()
            finally:
                conn.close()
        except Exception as e:
            logger.exception("Postgres L1 falhou")
            return self._no_data(symbol, [f"POSTGRES_ERROR:{e}"])

        if not row:
            return self._no_data(symbol, ["NO_RECENT_ROW"])

        record = {k: row[k] for k in row}
        canonical = json.dumps(record, sort_keys=True, default=str, ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return {
            "symbol": record.get("symbol", symbol),
            "var_95_usd": float(record["var_95_usd"]) if record.get("var_95_usd") is not None else float("nan"),
            "cvar_95_usd": float(record["cvar_95_usd"]) if record.get("cvar_95_usd") is not None else float("nan"),
            "regime_data": str(record.get("regime_data") or "UNKNOWN"),
            "momentum_1m_pct": float(record["momentum_1m_pct"] or 0.0),
            "effective_spread": float(record["effective_spread"]) if record.get("effective_spread") is not None else float("nan"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provenance_sha256": digest,
            "errors": [],
            "extras": {
                "source_batch_id": record.get("source_batch_id"),
                "computed_at": str(record.get("computed_at")) if record.get("computed_at") else None,
                "view": self._view,
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
        }
