"""
OMEGA v4.0 — AI Calibration Log
=================================
CEO Mandate 2026-05-26 | PSA Finding #3 (Q3)

Regista cada previsão do motor de IA (direction, confidence) e o resultado real
da posição, para calibração contínua e auditoria de edge.

CEO Q3: calibration_log obrigatório desde o primeiro trade em Demo.

Formato JSONL (uma entrada por linha) — permite análise incremental sem carregar
todo o ficheiro.

Métricas calculadas:
  - Win rate por confidence band (0.75-0.80, 0.80-0.90, >0.90)
  - Accuracy direcional (pred direction == real outcome)
  - Avg PnL por band (em pontos)
"""
from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("OMEGA.AiCalibration")

# ── Caminho do ficheiro de log ────────────────────────────────────────────────
_DEFAULT_LOG_DIR = Path(os.getenv(
    "OMEGA_AI_CALIB_DIR",
    "audit/ai_calibration"
))
_DEFAULT_LOG_FILE = _DEFAULT_LOG_DIR / "ai_calibration.jsonl"


@dataclass
class CalibrationEntry:
    """Uma entrada de calibração: previsão + resultado real."""
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ticket: int = 0
    symbol: str = ""
    pred_direction: int = 0          # +1 BUY, -1 SELL (previsão AI)
    pred_confidence: float = 0.0     # 0.0-1.0
    actual_direction: int = 0        # +1 BUY, -1 SELL (posição real)
    actual_pnl_pts: float = 0.0      # resultado em pontos
    outcome: str = ""                # "WIN" | "LOSS" | "NEUTRAL" | "PENDING"
    reason: str = ""                 # contexto (ex: "AI_REVERSAL", "TIMEOUT")


class AiCalibrationLog:
    """
    Log persistente de calibração IA.

    Thread-safe: escrita protegida por lock. Leitura via JSONL incremental.

    Usage:
        log = AiCalibrationLog()
        log.record_prediction(ticket=123, symbol="EURUSD",
                              pred_direction=1, pred_confidence=0.82,
                              actual_direction=1)
        # ... posição fecha
        log.record_outcome(ticket=123, actual_pnl_pts=340.0, outcome="WIN",
                           reason="PEAK_DRAWDOWN")
        stats = log.compute_stats()
    """

    def __init__(self, log_file: Optional[Path] = None) -> None:
        self._path = log_file or _DEFAULT_LOG_FILE
        self._lock = threading.Lock()
        self._pending: Dict[int, CalibrationEntry] = {}   # ticket → entry pendente

        # Criar directório se não existir
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            log.info("[AiCalib] Log path: %s", self._path)
        except Exception as e:
            log.warning("[AiCalib] Não foi possível criar dir de calibração: %s", e)

    # ── Interface pública ────────────────────────────────────────────────────

    def record_prediction(
        self,
        ticket: int,
        symbol: str,
        pred_direction: int,
        pred_confidence: float,
        actual_direction: int,
        reason: str = "",
    ) -> None:
        """
        Regista previsão AI (no momento da abertura/avaliação).

        Args:
            ticket: ticket MT5 da posição
            symbol: símbolo (ex: "EURUSD")
            pred_direction: direcção prevista pela AI (+1/-1)
            pred_confidence: confiança da AI (0-1)
            actual_direction: direcção real da posição (+1/-1)
            reason: contexto (ex: "AI_REVERSAL", "ENTRY_SIGNAL")
        """
        entry = CalibrationEntry(
            ticket=ticket,
            symbol=symbol,
            pred_direction=pred_direction,
            pred_confidence=round(pred_confidence, 4),
            actual_direction=actual_direction,
            outcome="PENDING",
            reason=reason,
        )
        with self._lock:
            self._pending[ticket] = entry
        log.debug("[AiCalib] Previsão registada #%d %s pred=%+d conf=%.2f",
                  ticket, symbol, pred_direction, pred_confidence)

    def record_outcome(
        self,
        ticket: int,
        actual_pnl_pts: float,
        outcome: str,
        reason: str = "",
    ) -> None:
        """
        Completa uma entrada com o resultado real e persiste em JSONL.

        Args:
            ticket: ticket MT5 fechado
            actual_pnl_pts: PnL final em pontos
            outcome: "WIN" | "LOSS" | "NEUTRAL"
            reason: razão de fecho
        """
        with self._lock:
            entry = self._pending.pop(ticket, None)

        if entry is None:
            # Criar entry mínima se não havia previsão registada
            entry = CalibrationEntry(
                ticket=ticket,
                outcome=outcome,
                reason=reason,
                actual_pnl_pts=round(actual_pnl_pts, 1),
            )
        else:
            entry.actual_pnl_pts = round(actual_pnl_pts, 1)
            entry.outcome = outcome
            if reason:
                entry.reason = reason

        self._append(entry)
        log.info("[AiCalib] Outcome #%d %s | pnl=%.1fpts outcome=%s conf=%.2f",
                 ticket, entry.symbol, actual_pnl_pts, outcome, entry.pred_confidence)

    def compute_stats(self) -> dict:
        """
        Calcula métricas de calibração das entradas persistidas.

        Returns:
            dict com win_rate, accuracy, avg_pnl, por confidence band
        """
        entries = self._load_all()
        if not entries:
            return {"total": 0, "bands": {}}

        bands = {
            "0.75-0.80": [],
            "0.80-0.90": [],
            ">0.90":     [],
            "all":       [],
        }

        for e in entries:
            if e.get("outcome") == "PENDING":
                continue
            c = e.get("pred_confidence", 0.0)
            correct = int(e.get("pred_direction", 0) == e.get("actual_direction", 0))
            pnl = e.get("actual_pnl_pts", 0.0)
            win = 1 if e.get("outcome") == "WIN" else 0
            rec = {"correct": correct, "pnl": pnl, "win": win}
            bands["all"].append(rec)
            if 0.75 <= c < 0.80:
                bands["0.75-0.80"].append(rec)
            elif 0.80 <= c < 0.90:
                bands["0.80-0.90"].append(rec)
            elif c >= 0.90:
                bands[">0.90"].append(rec)

        def summarise(recs: list) -> dict:
            if not recs:
                return {}
            n = len(recs)
            return {
                "n": n,
                "win_rate": round(sum(r["win"] for r in recs) / n, 3),
                "accuracy": round(sum(r["correct"] for r in recs) / n, 3),
                "avg_pnl_pts": round(sum(r["pnl"] for r in recs) / n, 1),
            }

        return {
            "total": len(bands["all"]),
            "bands": {k: summarise(v) for k, v in bands.items() if v},
        }

    # ── Persistência ─────────────────────────────────────────────────────────

    def _append(self, entry: CalibrationEntry) -> None:
        """Acrescenta uma linha JSONL ao ficheiro (append-only, thread-safe)."""
        try:
            with self._lock:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(entry)) + "\n")
        except Exception as e:
            log.warning("[AiCalib] Falha ao escrever JSONL: %s", e)

    def _load_all(self) -> List[dict]:
        """Carrega todas as entradas do ficheiro JSONL."""
        if not self._path.exists():
            return []
        entries = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            log.warning("[AiCalib] Erro ao ler JSONL: %s", e)
        return entries
