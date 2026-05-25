"""
OMEGA v3.2 — MT5 Order Manager
================================
P0-CICC-20260521: Single responsibility — ALL order_send calls go through here.
Every call — entry, partial close, full close — sets magic + comment.
MT5 does NOT inherit these from the original position.

Ref: PSA-EXEC-FINAL-MADRUGADA-20260521-v3 | CKO Ficheiro 1
"""
import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional

import MetaTrader5 as mt5

OMEGA_MAGIC = int(os.getenv("OMEGA_MAGIC_NUMBER", "234001"))
COMMENT_PREFIX = "OV2|"

log = logging.getLogger("omega.order_manager")


class OrderSendResult:
    """Standardized result from any order_send call."""
    __slots__ = ("success", "retcode", "comment", "order", "deal",
                 "position", "volume", "price")

    def __init__(self, success: bool, retcode: int = -1, comment: str = "",
                 order: int = 0, deal: int = 0, position: int = 0,
                 volume: float = 0.0, price: float = 0.0):
        self.success = success
        self.retcode = retcode
        self.comment = comment
        self.order = order
        self.deal = deal
        self.position = position
        self.volume = volume
        self.price = price

    @property
    def is_done(self) -> bool:
        return self.retcode == mt5.TRADE_RETCODE_DONE

    def __repr__(self) -> str:
        return (f"OrderSendResult(success={self.success}, retcode={self.retcode}, "
                f"deal={self.deal}, pos={self.position}, vol={self.volume:.2f})")


def _build_comment(*parts: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%H%M%S")
    inner = "|".join(p for p in parts if p)
    return (COMMENT_PREFIX + ts + "|" + inner)[:31]


def _send(request: dict) -> OrderSendResult:
    """Execute mt5.order_send and return standardized result. P0-5: always check retcode."""
    result = mt5.order_send(request)
    if result is None:
        log.error("order_send returned None: %s", mt5.last_error())
        return OrderSendResult(False, comment="MT5_NONE")
    ok = result.retcode == mt5.TRADE_RETCODE_DONE
    return OrderSendResult(
        success=ok,
        retcode=result.retcode,
        comment=getattr(result, "comment", ""),
        order=getattr(result, "order", 0),
        deal=getattr(result, "deal", 0),
        position=getattr(result, "position", request.get("position", 0)),
        volume=getattr(result, "volume", request.get("volume", 0.0)),
        price=getattr(result, "price", request.get("price", 0.0)),
    )


# =============================================================================
# ENTRY
# =============================================================================

def send_entry(symbol: str, direction: str, lot: float, price: float,
               sl: float, tp: float, timeframe: str, source: str,
               comment_override: str = "") -> OrderSendResult:
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    sym = mt5.symbol_info(symbol)
    fm = sym.filling_mode if sym else 3
    if fm & 2:    filling = mt5.ORDER_FILLING_IOC
    elif fm & 1:  filling = mt5.ORDER_FILLING_FOK
    else:         filling = mt5.ORDER_FILLING_RETURN
    request = {
        "action":        mt5.TRADE_ACTION_DEAL,
        "symbol":        symbol,
        "volume":        lot,
        "type":          order_type,
        "price":         price,
        "sl":            sl,
        "tp":            tp,
        "deviation":     20,
        "magic":         OMEGA_MAGIC,
        "comment":       comment_override or _build_comment(timeframe, direction[0], source),
        "type_time":     mt5.ORDER_TIME_GTC,
        "type_filling":  filling,
    }
    result = _send(request)
    if result.is_done:
        log.info("ENTRY OK: order=%d deal=%d pos=%d %s %s lot=%.2f @ %.5f magic=%d",
                 result.order, result.deal, result.position,
                 symbol, direction, lot, price, OMEGA_MAGIC)
    else:
        log.error("ENTRY FAIL: %s %s lot=%.2f retcode=%d '%s'",
                  symbol, direction, lot, result.retcode, result.comment)
    return result


# =============================================================================
# PARTIAL CLOSE — P0-1 FIX: magic + comment MUST be set
# =============================================================================

def send_partial_close(symbol: str, position_ticket: int, direction: str,
                       close_lot: float, price: float, reason: str) -> OrderSendResult:
    """
    P0-1 FIX: MT5 does NOT inherit magic/comment from the original position.
    Every partial close MUST explicitly set these fields.
    """
    order_type = mt5.ORDER_TYPE_SELL if direction == "BUY" else mt5.ORDER_TYPE_BUY
    sym = mt5.symbol_info(symbol)
    fm = sym.filling_mode if sym else 3
    if fm & 2:    filling = mt5.ORDER_FILLING_IOC
    elif fm & 1:  filling = mt5.ORDER_FILLING_FOK
    else:         filling = mt5.ORDER_FILLING_RETURN
    request = {
        "action":        mt5.TRADE_ACTION_DEAL,
        "symbol":        symbol,
        "volume":        close_lot,
        "type":          order_type,
        "position":      position_ticket,
        "price":         price,
        "deviation":     20,
        "magic":         OMEGA_MAGIC,
        "comment":       _build_comment("PARTIAL", reason),
        "type_time":     mt5.ORDER_TIME_GTC,
        "type_filling":  filling,
    }
    result = _send(request)
    if result.is_done:
        log.info("PARTIAL OK: deal=%d pos=%d lot=%.2f @ %.5f reason=%s magic=%d",
                 result.deal, position_ticket, close_lot, price, reason, OMEGA_MAGIC)
    else:
        log.error("PARTIAL FAIL: pos=%d lot=%.2f retcode=%d '%s'",
                  position_ticket, close_lot, result.retcode, result.comment)
    return result


# =============================================================================
# FULL CLOSE — P0-1 FIX: same as partial
# =============================================================================

def send_full_close(symbol: str, position_ticket: int, direction: str,
                    close_lot: float, price: float, reason: str) -> OrderSendResult:
    order_type = mt5.ORDER_TYPE_SELL if direction == "BUY" else mt5.ORDER_TYPE_BUY
    sym = mt5.symbol_info(symbol)
    fm = sym.filling_mode if sym else 3
    if fm & 2:    filling = mt5.ORDER_FILLING_IOC
    elif fm & 1:  filling = mt5.ORDER_FILLING_FOK
    else:         filling = mt5.ORDER_FILLING_RETURN
    request = {
        "action":        mt5.TRADE_ACTION_DEAL,
        "symbol":        symbol,
        "volume":        close_lot,
        "type":          order_type,
        "position":      position_ticket,
        "price":         price,
        "deviation":     20,
        "magic":         OMEGA_MAGIC,
        "comment":       _build_comment("CLOSE", reason),
        "type_time":     mt5.ORDER_TIME_GTC,
        "type_filling":  filling,
    }
    result = _send(request)
    if result.is_done:
        log.info("CLOSE OK: deal=%d pos=%d lot=%.2f @ %.5f reason=%s magic=%d",
                 result.deal, position_ticket, close_lot, price, reason, OMEGA_MAGIC)
    else:
        log.error("CLOSE FAIL: pos=%d lot=%.2f retcode=%d '%s'",
                  position_ticket, close_lot, result.retcode, result.comment)
    return result


# =============================================================================
# MODIFY SL/TP (trailing, breakeven)
# =============================================================================

def send_modify_sltp(position_ticket: int, symbol: str, sl: float,
                     tp: float, reason: str) -> OrderSendResult:
    request = {
        "action":    mt5.TRADE_ACTION_SLTP,
        "symbol":    symbol,
        "position":  position_ticket,
        "sl":        sl,
        "tp":        tp,
    }
    result = _send(request)
    if result.is_done:
        log.info("MODIFY OK: pos=%d SL=%.5f TP=%.5f (%s)", position_ticket, sl, tp, reason)
    else:
        log.error("MODIFY FAIL: pos=%d retcode=%d '%s'",
                  position_ticket, result.retcode, result.comment)
    return result
