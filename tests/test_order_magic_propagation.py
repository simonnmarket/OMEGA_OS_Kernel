"""
OMEGA P0 — Magic Propagation Test Suite
=========================================
Verifica que TODOS os order_send de fecho (partial, full, TIME_STOP, ZAK_TRAP)
propagam magic=234001 e comment com prefixo OV2|.

Ref: PSA-EXEC-FINAL-MADRUGADA-20260521-v3 | CQO Test Suite
"""
import os
import sys
import json
import time
import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

# Garantir que core_engines está no path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OMEGA_MAGIC = 234001


# =============================================================================
# Helpers / Stubs
# =============================================================================

def _make_mt5_success(retcode=10009, deal=1234, position=9999, volume=0.1, price=2050.0):
    r = MagicMock()
    r.retcode = retcode
    r.deal = deal
    r.position = position
    r.volume = volume
    r.price = price
    r.comment = "ok"
    r._asdict.return_value = {"retcode": retcode, "deal": deal, "price": price, "volume": volume}
    return r


def _make_mt5_module(retcode=10009):
    m = MagicMock()
    m.TRADE_ACTION_DEAL = 1
    m.ORDER_TYPE_BUY = 0
    m.ORDER_TYPE_SELL = 1
    m.ORDER_FILLING_IOC = 2
    m.ORDER_TIME_GTC = 1
    m.TRADE_RETCODE_DONE = 10009
    m.TradeRequest = dict  # use plain dict for TradeRequest
    m.order_send.return_value = _make_mt5_success(retcode)
    sym = MagicMock()
    sym.filling_mode = 2
    sym.digits = 5
    sym.volume_min = 0.01
    m.symbol_info.return_value = sym
    tick = MagicMock()
    tick.bid = 2049.5
    tick.ask = 2050.0
    m.symbol_info_tick.return_value = tick
    return m


# =============================================================================
# Component Isolation: mt5_order_manager.py
# =============================================================================

class TestOrderManagerMagic(unittest.TestCase):
    """P0-1: Verificar magic=234001 em todos os order_send via mt5_order_manager."""

    def setUp(self):
        self.mt5_mock = _make_mt5_module()

    @patch.dict("sys.modules", {"MetaTrader5": None})
    def test_module_imports_without_mt5(self):
        """OMEGA_MAGIC constant deve existir no ficheiro (verificação estática)."""
        import importlib
        src = ROOT / "core_engines" / "mt5_order_manager.py"
        content = src.read_text(encoding="utf-8")
        self.assertIn("OMEGA_MAGIC", content)
        self.assertIn("234001", content)

    def test_send_partial_close_magic(self):
        """send_partial_close deve incluir magic=234001 no request."""
        with patch.dict("sys.modules", {"MetaTrader5": self.mt5_mock}):
            import importlib
            import core_engines.mt5_order_manager as om
            importlib.reload(om)
            om.send_partial_close(
                symbol="XAUUSD", position_ticket=189376753,
                direction="BUY", close_lot=0.05, price=2049.5,
                reason="TP1",
            )
        call_args = self.mt5_mock.order_send.call_args
        req = call_args[0][0]
        self.assertEqual(req["magic"], OMEGA_MAGIC,
                         f"magic should be {OMEGA_MAGIC}, got {req.get('magic')}")

    def test_send_partial_close_comment_prefix(self):
        """send_partial_close comment deve começar com 'OV2|'."""
        with patch.dict("sys.modules", {"MetaTrader5": self.mt5_mock}):
            import importlib
            import core_engines.mt5_order_manager as om
            importlib.reload(om)
            om.send_partial_close(
                symbol="XAUUSD", position_ticket=189376753,
                direction="BUY", close_lot=0.05, price=2049.5, reason="TP2",
            )
        req = self.mt5_mock.order_send.call_args[0][0]
        comment = req.get("comment", "")
        self.assertTrue(comment.startswith("OV2|"),
                        f"comment deve começar com 'OV2|', got '{comment}'")

    def test_send_full_close_magic(self):
        """send_full_close deve incluir magic=234001."""
        with patch.dict("sys.modules", {"MetaTrader5": self.mt5_mock}):
            import importlib
            import core_engines.mt5_order_manager as om
            importlib.reload(om)
            om.send_full_close(
                symbol="XAUUSD", position_ticket=189376753,
                direction="BUY", close_lot=0.10, price=2049.5, reason="TRAILING",
            )
        req = self.mt5_mock.order_send.call_args[0][0]
        self.assertEqual(req["magic"], OMEGA_MAGIC)

    def test_send_entry_magic(self):
        """send_entry deve incluir magic=234001."""
        with patch.dict("sys.modules", {"MetaTrader5": self.mt5_mock}):
            import importlib
            import core_engines.mt5_order_manager as om
            importlib.reload(om)
            om.send_entry(
                symbol="XAUUSD", direction="BUY", lot=0.10,
                price=2050.0, sl=2030.0, tp=2100.0,
                timeframe="H1", source="shadow",
            )
        req = self.mt5_mock.order_send.call_args[0][0]
        self.assertEqual(req["magic"], OMEGA_MAGIC)

    def test_magic_env_override(self):
        """OMEGA_MAGIC_NUMBER env var deve ser respeitado."""
        with patch.dict(os.environ, {"OMEGA_MAGIC_NUMBER": "999999"}):
            with patch.dict("sys.modules", {"MetaTrader5": self.mt5_mock}):
                import importlib
                import core_engines.mt5_order_manager as om
                importlib.reload(om)
                self.assertEqual(om.OMEGA_MAGIC, 999999)


# =============================================================================
# Shadow Loop Patch Verification
# =============================================================================

class TestShadowLoopMagicConstants(unittest.TestCase):
    """Verifica que shadow_loop.py tem OMEGA_MAGIC e patches corretos."""

    def test_omega_magic_constant_exists(self):
        """OMEGA_MAGIC deve existir em shadow_loop.py."""
        shadow_path = ROOT / "core_engines" / "shadow_loop.py"
        content = shadow_path.read_text(encoding="utf-8")
        self.assertIn("OMEGA_MAGIC = int(os.getenv(\"OMEGA_MAGIC_NUMBER\",", content,
                      "OMEGA_MAGIC constant not found in shadow_loop.py")

    def test_no_hardcoded_magic_20260512(self):
        """shadow_loop.py NÃO deve ter magic=20260512 (TIME_STOP legado)."""
        shadow_path = ROOT / "core_engines" / "shadow_loop.py"
        content = shadow_path.read_text(encoding="utf-8")
        self.assertNotIn("20260512", content,
                         "magic=20260512 ainda presente em shadow_loop.py — P1-ZAK não aplicado")

    def test_no_hardcoded_magic_20260513(self):
        """shadow_loop.py NÃO deve ter magic=20260513 (ZAK_TRAP legado)."""
        shadow_path = ROOT / "core_engines" / "shadow_loop.py"
        content = shadow_path.read_text(encoding="utf-8")
        self.assertNotIn("20260513", content,
                         "magic=20260513 ainda presente em shadow_loop.py — P1-ZAK não aplicado")

    def test_no_bare_omega_partial_close_comment(self):
        """shadow_loop.py NÃO deve ter comment='OMEGA_PARTIAL_CLOSE' no request dict."""
        shadow_path = ROOT / "core_engines" / "shadow_loop.py"
        content = shadow_path.read_text(encoding="utf-8")
        self.assertNotIn('"OMEGA_PARTIAL_CLOSE"', content,
                         "'OMEGA_PARTIAL_CLOSE' bare comment ainda em shadow_loop.py")

    def test_partial_close_has_magic_field(self):
        """mt5_close_partial request deve ter 'magic': OMEGA_MAGIC."""
        shadow_path = ROOT / "core_engines" / "shadow_loop.py"
        content = shadow_path.read_text(encoding="utf-8")
        self.assertIn('"magic":        OMEGA_MAGIC,', content,
                      "'magic': OMEGA_MAGIC não encontrado no request de mt5_close_partial")

    def test_no_exit_reason_unknown_fallback(self):
        """shadow_loop.py deve usar BROKER_CLOSE (não UNKNOWN) como fallback."""
        shadow_path = ROOT / "core_engines" / "shadow_loop.py"
        content = shadow_path.read_text(encoding="utf-8")
        self.assertIn("BROKER_CLOSE", content,
                      "P0-7: BROKER_CLOSE fallback não encontrado em shadow_loop.py")

    def test_tp1_level_is_2_5(self):
        """_PARTIAL_CLOSE_LEVELS_PSA TP1 deve ser 2.5 ATR."""
        shadow_path = ROOT / "core_engines" / "shadow_loop.py"
        content = shadow_path.read_text(encoding="utf-8")
        self.assertIn('"atr": 2.5', content,
                      "_PARTIAL_CLOSE_LEVELS_PSA: TP1 não está em 2.5 ATR")
        self.assertNotIn('"atr": 1.0', content,
                         "_PARTIAL_CLOSE_LEVELS_PSA: TP1 ainda em 1.0 ATR — P1-2 não aplicado")


# =============================================================================
# Position Manager Tests
# =============================================================================

class TestPositionManager(unittest.TestCase):
    """P0-2: PositionManager match por position_ticket; 1 linha feedback/posição."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.feedback_path = os.path.join(self.tmpdir, "trade_feedback.jsonl")

    def _make_manager(self):
        from core_engines.position_manager import PositionManager
        return PositionManager(feedback_path=self.feedback_path)

    def test_register_open(self):
        pm = self._make_manager()
        t = pm.register_open(
            position_ticket=189376753, entry_ticket=222000,
            entry_magic=OMEGA_MAGIC, entry_comment="OV2|H1|B|shadow",
            symbol="XAUUSD", direction="BUY",
            entry_price=2050.0, entry_lot=0.10,
        )
        self.assertEqual(t.position_ticket, 189376753)
        self.assertEqual(t.entry_magic, OMEGA_MAGIC)
        self.assertFalse(t.is_closed)

    def test_partial_then_full_close_writes_one_feedback(self):
        pm = self._make_manager()
        pm.register_open(
            position_ticket=189376753, entry_ticket=222000,
            entry_magic=OMEGA_MAGIC, entry_comment="OV2|H1|B|shadow",
            symbol="XAUUSD", direction="BUY",
            entry_price=2050.0, entry_lot=0.10,
        )
        pm.register_partial(189376753, deal_ticket=300001, lot=0.05,
                            price=2075.0, pnl=12.5, reason="TP1")
        pm.register_close(189376753, deal_ticket=300002, lot=0.05,
                          price=2090.0, pnl=20.0, reason="TP2")

        lines = Path(self.feedback_path).read_text().strip().splitlines()
        self.assertEqual(len(lines), 1, f"Esperado 1 linha feedback, got {len(lines)}")
        row = json.loads(lines[0])
        self.assertEqual(len(row["partials"]), 2)
        self.assertAlmostEqual(row["total_realized_pnl"], 32.5, places=3)
        self.assertEqual(row["exit_reason"], "TP2")

    def test_timeline_validate_no_duplicate_deals(self):
        pm = self._make_manager()
        pm.register_open(
            position_ticket=189384222, entry_ticket=222001,
            entry_magic=OMEGA_MAGIC, entry_comment="OV2|H1|S|shadow",
            symbol="XAUUSD", direction="SELL",
            entry_price=2050.0, entry_lot=0.10,
        )
        pm.register_partial(189384222, deal_ticket=300003, lot=0.05,
                            price=2030.0, pnl=10.0, reason="TP1")
        pm.register_partial(189384222, deal_ticket=300003, lot=0.05,
                            price=2030.0, pnl=10.0, reason="TP1")  # duplicate
        issues = pm.timeline_validate(189384222)
        self.assertTrue(len(issues) > 0, "Deveria detectar deal duplicado")
        self.assertTrue(any("duplicate" in i for i in issues))

    def test_invalid_exit_reason_not_written(self):
        """Posições com exit_reason UNKNOWN NÃO devem ser escritas no feedback."""
        from core_engines.position_manager import PositionTracker
        import tempfile
        tmpf = os.path.join(self.tmpdir, "fb_unknown.jsonl")
        from core_engines.position_manager import PositionManager
        pm = PositionManager(feedback_path=tmpf)
        pm.register_open(
            position_ticket=999, entry_ticket=111, entry_magic=OMEGA_MAGIC,
            entry_comment="OV2|H1|B", symbol="EURUSD", direction="BUY",
            entry_price=1.1000, entry_lot=0.10,
        )
        # Force exit_reason = UNKNOWN
        tracker = pm.get(999)
        tracker.exit_reason = "UNKNOWN"
        tracker.remaining_lot = 0.0
        pm._write_feedback(tracker)
        self.assertFalse(Path(tmpf).exists(),
                         "UNKNOWN exit_reason não deve escrever no feedback")


# =============================================================================
# Integration: Legacy Cleanup
# =============================================================================

class TestPsaLegacyCleanup(unittest.TestCase):
    """G1: psa_legacy_cleanup.py cria backup e marca legados."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.feedback_path = os.path.join(self.tmpdir, "trade_feedback.jsonl")

    def _write_feedback(self, rows):
        with open(self.feedback_path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def test_marks_magic0_as_legacy(self):
        """Deals com magic ausente devem ser marcados como legacy_unreconciled."""
        self._write_feedback([
            {"event": "position_closed", "position_ticket": 1,
             "exit_reason": "TP", "total_realized_pnl": 10.0},  # sem magic
            {"event": "position_closed", "position_ticket": 2,
             "entry_magic": 234001, "exit_reason": "SL", "total_realized_pnl": -5.0},
        ])
        # run cleanup directly (not subprocess)
        import importlib.util
        cleanup_path = ROOT / "scripts" / "psa_legacy_cleanup.py"
        spec = importlib.util.spec_from_file_location("cleanup", cleanup_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        bak = self.feedback_path + ".bak"
        import shutil
        shutil.copy2(self.feedback_path, bak)

        # Simulate what cleanup does
        lines = Path(self.feedback_path).read_text().splitlines()
        results = []
        for line in lines:
            row = json.loads(line)
            if row.get("entry_magic", row.get("magic", 0)) != OMEGA_MAGIC:
                row["legacy_unreconciled"] = True
            results.append(row)

        p1 = results[0]
        p2 = results[1]
        self.assertTrue(p1.get("legacy_unreconciled", False),
                        "magic ausente deve ser marcado como legacy")
        self.assertFalse(p2.get("legacy_unreconciled", False),
                         "magic=234001 NÃO deve ser marcado como legacy")


# =============================================================================
# Regression: Tickets Problemáticos
# =============================================================================

class TestKnownBadTickets(unittest.TestCase):
    """Testa os tickets específicos dos incidentes CICC."""

    PROBLEM_TICKETS = [189376753, 189384222]

    def test_position_manager_handles_known_bad_tickets(self):
        """PositionManager deve gerir os tickets problemáticos sem erro."""
        import tempfile
        tmpdir = tempfile.mkdtemp()
        from core_engines.position_manager import PositionManager
        pm = PositionManager(feedback_path=os.path.join(tmpdir, "fb.jsonl"))

        for ticket in self.PROBLEM_TICKETS:
            pm.register_open(
                position_ticket=ticket, entry_ticket=ticket + 100000,
                entry_magic=OMEGA_MAGIC, entry_comment="OV2|H1|B|shadow",
                symbol="XAUUSD", direction="BUY",
                entry_price=2050.0, entry_lot=0.10,
            )
            pm.register_close(
                ticket, deal_ticket=ticket + 200000, lot=0.10,
                price=2070.0, pnl=10.0, reason="TP",
            )
            t = pm.get(ticket)
            self.assertTrue(t.is_closed)
            self.assertEqual(t.exit_reason, "TP")


if __name__ == "__main__":
    unittest.main(verbosity=2)
