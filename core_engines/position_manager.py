"""
OMEGA v3.2 — Position Manager
==============================
P0-CICC-20260521: Tracks positions from entry to final close.
Match by position_ticket (MT5 native ID), NOT by magic.
Writes ONE feedback line per position (not per partial) with partials[] array.

Ref: PSA-EXEC-FINAL-MADRUGADA-20260521-v3 | CKO Ficheiro 2
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from dataclasses import dataclass, field

OMEGA_MAGIC = 234001
INVALID_EXIT_REASONS = {"UNKNOWN", "UNKNOWN_NO_DEAL", "UNKNOWN_NO_HISTORY", "OPEN"}

log = logging.getLogger("omega.position_manager")


@dataclass
class PositionTracker:
    position_ticket: int
    entry_ticket: int
    entry_magic: int
    entry_comment: str
    symbol: str
    direction: str          # "BUY" or "SELL"
    entry_price: float
    entry_lot: float        # ORIGINAL — never mutated
    entry_time: str         # ISO format
    partials: List[dict] = field(default_factory=list)
    total_realized_pnl: float = 0.0
    remaining_lot: float = 0.0
    exit_reason: str = "OPEN"
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None

    def record_partial(self, deal_ticket: int, lot: float, price: float,
                       pnl: float, reason: str) -> None:
        self.partials.append({
            "deal_ticket": deal_ticket,
            "lot": round(lot, 2),
            "price": round(price, 5),
            "pnl": round(pnl, 4),
            "reason": reason,
            "time": datetime.now(timezone.utc).isoformat(),
        })
        self.total_realized_pnl = round(self.total_realized_pnl + pnl, 4)
        self.remaining_lot = round(self.remaining_lot - lot, 2)
        if self.remaining_lot < 0.0001:
            self.remaining_lot = 0.0
            self.exit_reason = reason
            self.exit_time = datetime.now(timezone.utc).isoformat()
            self.exit_price = price

    @property
    def is_closed(self) -> bool:
        return self.remaining_lot < 0.0001

    @property
    def outcome(self) -> str:
        if not self.is_closed:
            return "OPEN"
        if self.total_realized_pnl > 0.01:
            return "WIN"
        elif self.total_realized_pnl < -0.01:
            return "LOSS"
        return "BE"

    def to_feedback_dict(self) -> dict:
        """One line per POSITION with partials array — P0-2 format."""
        return {
            "event":             "position_closed",
            "position_ticket":   self.position_ticket,
            "entry_ticket":      self.entry_ticket,
            "symbol":            self.symbol,
            "direction":         self.direction,
            "entry_price":       self.entry_price,
            "entry_lot":         self.entry_lot,
            "entry_time":        self.entry_time,
            "entry_magic":       self.entry_magic,
            "entry_comment":     self.entry_comment,
            "partials":          self.partials,
            "total_realized_pnl": self.total_realized_pnl,
            "remaining_lot":     self.remaining_lot,
            "exit_reason":       self.exit_reason,
            "exit_time":         self.exit_time,
            "exit_price":        self.exit_price,
            "outcome":           self.outcome,
            "ts":                datetime.now(timezone.utc).isoformat(),
        }


class PositionManager:
    """
    Manages all open positions. Writes ONE feedback line per position.
    Resolves P0-2: match by position_ticket, not magic.
    """

    def __init__(self, feedback_path: Optional[str] = None):
        self._positions: Dict[int, PositionTracker] = {}
        self._feedback_path = feedback_path or "audit/paper/trade_feedback.jsonl"
        self._written: set = set()

    def register_open(self, position_ticket: int, entry_ticket: int,
                      entry_magic: int, entry_comment: str, symbol: str,
                      direction: str, entry_price: float, entry_lot: float,
                      entry_time: Optional[str] = None) -> PositionTracker:
        """Register a new position at entry."""
        if position_ticket in self._positions:
            log.warning("PositionManager: ticket %d already registered — skipping", position_ticket)
            return self._positions[position_ticket]
        tracker = PositionTracker(
            position_ticket=position_ticket,
            entry_ticket=entry_ticket,
            entry_magic=entry_magic,
            entry_comment=entry_comment,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            entry_lot=entry_lot,
            entry_time=entry_time or datetime.now(timezone.utc).isoformat(),
            remaining_lot=entry_lot,
        )
        self._positions[position_ticket] = tracker
        log.info("[PositionManager] OPEN: %s #%d %s %.2f @ %.5f magic=%d",
                 symbol, position_ticket, direction, entry_lot, entry_price, entry_magic)
        return tracker

    def register_partial(self, position_ticket: int, deal_ticket: int,
                         lot: float, price: float, pnl: float,
                         reason: str = "PARTIAL") -> Optional[PositionTracker]:
        """Record a partial close event."""
        tracker = self._positions.get(position_ticket)
        if tracker is None:
            log.warning("[PositionManager] partial: ticket %d not tracked", position_ticket)
            return None
        tracker.record_partial(deal_ticket, lot, price, pnl, reason)
        log.info("[PositionManager] PARTIAL: %s #%d lot=%.2f pnl=%.4f rem=%.2f",
                 tracker.symbol, position_ticket, lot, pnl, tracker.remaining_lot)
        return tracker

    def register_close(self, position_ticket: int, deal_ticket: int,
                       lot: float, price: float, pnl: float,
                       reason: str = "CLOSE") -> Optional[PositionTracker]:
        """Record final close and write feedback."""
        tracker = self.register_partial(position_ticket, deal_ticket, lot, price, pnl, reason)
        if tracker and tracker.is_closed:
            self._write_feedback(tracker)
        return tracker

    def _write_feedback(self, tracker: PositionTracker) -> None:
        """Write ONE feedback line per position to trade_feedback.jsonl."""
        if tracker.position_ticket in self._written:
            return
        if tracker.exit_reason in INVALID_EXIT_REASONS:
            log.warning("[PositionManager] exit_reason '%s' invalid — não escrever feedback",
                        tracker.exit_reason)
            return
        try:
            row = json.dumps(tracker.to_feedback_dict(), ensure_ascii=False)
            with open(self._feedback_path, "a", encoding="utf-8") as f:
                f.write(row + "\n")
            self._written.add(tracker.position_ticket)
            log.info("[PositionManager] FEEDBACK: #%d %s pnl=%.4f outcome=%s reason=%s",
                     tracker.position_ticket, tracker.symbol,
                     tracker.total_realized_pnl, tracker.outcome, tracker.exit_reason)
        except OSError as e:
            log.error("[PositionManager] feedback write failed: %s", e)

    def get(self, position_ticket: int) -> Optional[PositionTracker]:
        return self._positions.get(position_ticket)

    def all_open(self) -> List[PositionTracker]:
        return [t for t in self._positions.values() if not t.is_closed]

    def timeline_validate(self, position_ticket: int) -> List[str]:
        """P0-6: Validate position timeline — monotonic volume, no duplicate deals."""
        issues = []
        tracker = self._positions.get(position_ticket)
        if tracker is None:
            return [f"ticket {position_ticket} not tracked"]
        seen_deals = set()
        cum_lot = 0.0
        for i, p in enumerate(tracker.partials):
            dt = p["deal_ticket"]
            if dt in seen_deals:
                issues.append(f"duplicate deal_ticket {dt} at partial {i}")
            seen_deals.add(dt)
            cum_lot = round(cum_lot + p["lot"], 2)
            if cum_lot > tracker.entry_lot + 0.001:
                issues.append(f"cumulative lot {cum_lot} > entry_lot {tracker.entry_lot} at partial {i}")
        return issues
