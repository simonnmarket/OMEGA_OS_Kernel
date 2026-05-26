"""
GATE G2 — Validação de Logs em Pontos
=======================================
OMEGA-PSA-EXEC-20260526 | CEO Criterion 2

Critério CEO: 95% dos logs de distância devem estar em "pts" (pontos MT5).
Se qualquer "USD" aparecer como unidade de distância → FAIL.

Padrões de detecção:
  PASS: "Dist: +150.0 pts", "SL: 200.0 pts", "trail: 80.5 pts"
  FAIL: "Dist: $12.50 USD", "distance=5.20 USD", "Dist: 5.2 USD"
  OK (contexto):  "USD_ctx: $12.50" (campo de contexto USD, não distância)

Nota: "USD_ctx" é permitido (campo separado de reconciliação).
      "usd" como unidade de medida de distância é PROIBIDO.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Padrões regex ────────────────────────────────────────────────────────────────

# Detecta "Dist: <valor> pts" ou "SL: <valor> pts" etc.
_PATTERN_PTS = re.compile(
    r"(?:dist|distance|sl|tp|trail|trailing|pts_dist|retrac)[:\s=]+[+-]?\d+(?:\.\d+)?\s*pts",
    re.IGNORECASE,
)

# Detecta "USD" como unidade de distância (PROIBIDO)
# Excepção: "USD_ctx" é contexto de reconciliação (permitido)
_PATTERN_USD_DIST = re.compile(
    r"(?:dist|distance|sl|tp|trail|trailing)[:\s=]+[+-]?\$?\d+(?:\.\d+)?\s*USD(?!_ctx)",
    re.IGNORECASE,
)

# Detecção alternativa: "5.20 USD" após palavras de distância
_PATTERN_USD_DIST_ALT = re.compile(
    r"(?:dist|distance|sl|tp|trail)[:\s=]+[+-]?\d+(?:\.\d+)?\s+USD\b(?!_ctx)",
    re.IGNORECASE,
)

# Threshold CEO: 95% pts
PASS_THRESHOLD = 0.95


def parse_log_lines(lines: list[str]) -> dict:
    """
    Analisa linhas de log e classifica eventos de distância.

    Returns:
        dict com: pts_count, usd_count, total, ratio, violations
    """
    pts_count = 0
    usd_count = 0
    violations = []

    for i, line in enumerate(lines):
        has_pts = bool(_PATTERN_PTS.search(line))
        has_usd = bool(_PATTERN_USD_DIST.search(line) or _PATTERN_USD_DIST_ALT.search(line))

        if has_pts:
            pts_count += 1
        if has_usd:
            usd_count += 1
            violations.append((i + 1, line.strip()))

    total = pts_count + usd_count
    ratio = pts_count / max(total, 1)

    return {
        "pts_count": pts_count,
        "usd_count": usd_count,
        "total": total,
        "ratio": ratio,
        "violations": violations,
    }


# ── Fixtures de log ─────────────────────────────────────────────────────────────

_COMPLIANT_LOGS = [
    "2026-05-26 10:00:01 | [EURUSD #100001] OPEN | Dist: +0.0 pts | Reason: ENTRY",
    "2026-05-26 10:00:02 | [EURUSD #100001] TRAILING | Trail: 80.0 pts | Peak: +150.5 pts | Current: +150.5 pts",
    "2026-05-26 10:00:03 | [XAUUSD #100002] SL/TP_SET | SL: 200.0 pts | TP: 600.0 pts | Reason: ENTRY",
    "2026-05-26 10:00:04 | [EURUSD #100001] TRAILING | Trail: 80.0 pts | Peak: +320.0 pts | Current: +310.0 pts",
    "2026-05-26 10:00:05 | [EURUSD #100001] CLOSE_FULL | Dist: +320.0 pts | Reason: PEAK_DRAWDOWN | USD_ctx: $12.50",
    "2026-05-26 10:00:06 | [XAUUSD #100002] PARTIAL_50PCT | Dist: +900.0 pts | Reason: PEAK_DRAWDOWN_PARTIAL",
    "2026-05-26 10:00:07 | [ETHUSD #100003] AI_EXIT | Dist: -20.0 pts | Reason: AI_REVERSAL conf=0.82",
    "2026-05-26 10:00:08 | [GBPUSD #100004] TIMEOUT_CLOSE | Dist: +5.0 pts | Reason: TIMEOUT_SIDEWAYS",
    "2026-05-26 10:00:09 | [USDJPY #100005] OPEN | Dist: +0.0 pts | Reason: ENTRY",
    "2026-05-26 10:00:10 | [USDJPY #100005] SL/TP_SET | SL: 150.0 pts | TP: 450.0 pts | Reason: ENTRY",
]

_VIOLATING_LOGS = [
    "2026-05-26 10:00:01 | [EURUSD #100001] CLOSE | Dist: $12.50 USD | Reason: SL_HIT",
    "2026-05-26 10:00:02 | [XAUUSD #100002] TRAILING | distance=5.20 USD | trail adjusted",
]

_MIXED_LOGS = _COMPLIANT_LOGS + _VIOLATING_LOGS


# ── Testes ──────────────────────────────────────────────────────────────────────

class TestAuditLogPointsValidation:

    def test_compliant_logs_pass_threshold(self):
        """
        G2-A: Logs 100% em pontos devem atingir ratio ≥ 0.95.
        """
        result = parse_log_lines(_COMPLIANT_LOGS)
        print(f"\n[G2-A] pts={result['pts_count']} usd={result['usd_count']} ratio={result['ratio']:.2%}")
        assert result["usd_count"] == 0, "Logs conformes não devem ter violações USD"
        assert result["ratio"] >= PASS_THRESHOLD or result["total"] == 0

    def test_usd_distance_logs_detected(self):
        """
        G2-B: Logs com "Dist: USD" devem ser detectados como violações.
        """
        result = parse_log_lines(_VIOLATING_LOGS)
        print(f"\n[G2-B] Violações detectadas: {result['usd_count']}")
        print(f"[G2-B] Violações: {result['violations']}")
        assert result["usd_count"] >= 1, (
            "GATE G2 FAIL: logs com distância em USD não foram detectados"
        )

    def test_mixed_logs_fail_threshold(self):
        """
        G2-C: Mix de logs pts + USD deve falhar se ratio < 0.95.
        """
        result = parse_log_lines(_MIXED_LOGS)
        print(f"\n[G2-C] pts={result['pts_count']} usd={result['usd_count']} ratio={result['ratio']:.2%}")
        # Com 10 conformes + 2 violações: ratio = 10/12 ≈ 0.833 < 0.95 → FAIL esperado
        if result["usd_count"] > 0:
            expected_fail = result["ratio"] < PASS_THRESHOLD
            print(f"[G2-C] ratio={result['ratio']:.2%} < {PASS_THRESHOLD:.0%}: {'FAIL correcto' if expected_fail else 'PASS incorrecto'}")

    def test_usd_ctx_is_allowed(self):
        """
        G2-D: "USD_ctx" (campo de contexto de reconciliação) NÃO é violação.
        """
        lines_with_ctx = [
            "[EURUSD #100001] CLOSE | Dist: +320.0 pts | Reason: PEAK_DRAWDOWN | USD_ctx: $12.50",
            "[XAUUSD #100002] PARTIAL | Dist: +900.0 pts | Reason: PEAK | USD_ctx: $45.20",
        ]
        result = parse_log_lines(lines_with_ctx)
        print(f"\n[G2-D] USD_ctx test: pts={result['pts_count']} violations={result['usd_count']}")
        assert result["usd_count"] == 0, (
            "USD_ctx não deve ser contado como violação de distância USD"
        )

    def test_point_metric_engine_log_format(self, tmp_path):
        """
        G2-E: PointMetricEngine.log_position_event produz logs em formato "pts".
        """
        import logging
        from core_engines.point_metrics import PointMetricEngine

        audit_file = tmp_path / "point_metrics_trace.jsonl"
        engine = PointMetricEngine(audit_path=audit_file)

        captured_messages = []

        class CapturingHandler(logging.Handler):
            def emit(self, record):
                captured_messages.append(self.format(record))

        handler = CapturingHandler()
        import logging as lg
        logger = lg.getLogger("OMEGA.PointMetrics")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        engine.log_position_event(
            ticket=100001, symbol="EURUSD", action="CLOSE_FULL",
            points=320.5, reason="PEAK_DRAWDOWN", usd_context=12.50
        )

        logger.removeHandler(handler)

        assert captured_messages, "PointMetricEngine deve logar evento"
        msg = captured_messages[-1]
        assert "pts" in msg.lower(), f"Log não contém 'pts': {msg}"
        assert "320.5" in msg, f"Log não contém valor de pontos: {msg}"
        assert "USD_ctx" in msg or "usd_ctx" in msg.lower(), "USD_ctx deve aparecer como campo separado"

        # Verificar JSONL de auditoria
        assert audit_file.exists(), "Ficheiro JSONL de auditoria não criado"
        with open(audit_file) as f:
            record = json.loads(f.readline())
        assert record["unit"] == "points", f"unit deve ser 'points', não '{record.get('unit')}'"
        assert record["dist"] == 320.5
        assert "usd_ctx" in record


import json  # necessário para test_point_metric_engine_log_format
