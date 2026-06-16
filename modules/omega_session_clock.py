#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 OMEGA SESSION CLOCK — Relógio canónico (iteração incremental)
=============================================================================
ID: MOD-SESSION-CLOCK-001 | Tier: TIER-0 (governaça temporal)

Este módulo evolui por fases; esta versão inclui:
  - Config dataclass + from_env
  - ComponentState + compute_from_bars (compatível com registo de módulos OMEGA)
  - Cache de overrides de feriados (evita I/O repetido ao disco)
  - Etiquetas UTC / OMEGA_BERLIN / BROKER / TERMINAL_LOCAL + sessões em UTC
  - NYSE / LSE mínimos para auditoria de confluência

Persistência recomendada: sempre `ts_utc` com sufixo Z nos JSONL.
=============================================================================
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore[misc, assignment]


class TimeRef(str, Enum):
    UTC = "UTC"
    OMEGA_BERLIN = "OMEGA_BERLIN"
    BROKER = "BROKER"
    TERMINAL_LOCAL = "TERMINAL_LOCAL"


@dataclass
class SessionClockConfig:
    """Parâmetros ortogonais do relógio (substitui kwargs soltos)."""

    policy_tz: str = "Europe/Berlin"
    broker_tz: str = ""
    broker_offset_minutes: Optional[int] = None
    terminal_tz: str = ""
    source_root: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SessionClockConfig":
        bo: Optional[int] = None
        raw = os.getenv("OMEGA_BROKER_OFFSET_MINUTES")
        if raw:
            try:
                bo = int(raw)
            except ValueError:
                bo = None
        return cls(
            policy_tz=os.getenv("OMEGA_POLICY_TZ", "Europe/Berlin"),
            broker_tz=os.getenv("OMEGA_BROKER_TZ", "") or "",
            broker_offset_minutes=bo,
            terminal_tz=os.getenv("OMEGA_TERMINAL_TZ", "") or "",
            source_root=os.getenv("OMEGA_SOURCE_ROOT") or None,
        )


@dataclass
class ClockSnapshot:
    ts_utc: datetime
    iso_utc: str
    iso_omega_berlin: str
    iso_broker: str
    iso_terminal_local: str
    omega_session_utc: str
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def audit_line(self) -> str:
        return (
            f"ts_utc={self.iso_utc} | {TimeRef.OMEGA_BERLIN.value}={self.iso_omega_berlin} | "
            f"{TimeRef.BROKER.value}={self.iso_broker} | {TimeRef.TERMINAL_LOCAL.value}={self.iso_terminal_local} | "
            f"OMEGA_SESSION={self.omega_session_utc}"
        )


@dataclass
class ComponentState:
    """Contrato OMEGA mínimo para utilitários (sem direção de trade)."""

    is_valid: bool
    direction: int
    strength: float
    n_bars: int
    meta: Dict[str, Any] = field(default_factory=dict)


# --- Sessões OMEGA (UTC) ---
_SESSION_WINDOWS_UTC: Tuple[Tuple[int, int, str], ...] = (
    (0, 8, "ASIA"),
    (8, 13, "LONDON"),
    (13, 17, "INTERSESSION"),
    (17, 21, "OVERLAP"),
    (21, 24, "CLOSED"),
)

_VENUE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "NYSE": {
        "tz": "America/New_York",
        "open_local": (9, 30),
        "close_local": (16, 0),
        "holidays_iso": [
            "2026-01-01",
            "2026-01-19",
            "2026-02-16",
            "2026-04-03",
            "2026-05-25",
            "2026-07-03",
            "2026-09-07",
            "2026-11-26",
            "2026-12-25",
        ],
    },
    "LSE": {
        "tz": "Europe/London",
        "open_local": (8, 0),
        "close_local": (16, 30),
        "holidays_iso": [
            "2026-01-01",
            "2026-04-03",
            "2026-05-04",
            "2026-05-25",
            "2026-12-25",
            "2026-12-28",
        ],
    },
}

# Cache: (path_resolvido, mtime) -> dict de overrides
_holiday_override_cache: Dict[Tuple[str, float], Dict[str, List[str]]] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_zone(name: str) -> Optional[Any]:
    if not name or ZoneInfo is None:
        return None
    try:
        return ZoneInfo(name)
    except Exception:
        return None


def _to_iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    u = dt.astimezone(timezone.utc)
    return u.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def _to_iso_tz(dt: datetime, tz: Any) -> str:
    if tz is None:
        return _to_iso_z(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).isoformat(timespec="seconds")


def resolve_omega_session_utc_hour(hour_utc: int) -> str:
    h = hour_utc % 24
    for start, end, name in _SESSION_WINDOWS_UTC:
        if start <= h < end:
            return name
    return "UNKNOWN"


def resolve_omega_session(ts_utc: datetime) -> str:
    return resolve_omega_session_utc_hour(ts_utc.astimezone(timezone.utc).hour)


def _load_holiday_overrides(source_root: Optional[Path] = None) -> Dict[str, List[str]]:
    """
    Lê config/omega_session_clock.json uma vez por versão do ficheiro (mtime).
    Evita leituras repetidas no hot path quando vários venues consultam o mesmo instante.
    """
    root = source_root or Path.cwd()
    p = root / "config" / "omega_session_clock.json"
    if not p.is_file():
        return {}
    try:
        key = (str(p.resolve()), p.stat().st_mtime)
    except OSError:
        return {}
    hit = _holiday_override_cache.get(key)
    if hit is not None:
        return hit
    out: Dict[str, List[str]] = {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        for k, v in (data.get("holidays") or {}).items():
            if isinstance(v, list) and all(isinstance(x, str) for x in v):
                out[str(k).upper()] = list(v)
    except Exception:
        out = {}
    _holiday_override_cache[key] = out
    return out


def venue_is_holiday(
    venue: str,
    d: date,
    source_root: Optional[Path] = None,
    overrides: Optional[Dict[str, List[str]]] = None,
) -> bool:
    key = venue.upper()
    meta = _VENUE_DEFAULTS.get(key)
    if not meta:
        return False
    iso = d.isoformat()
    if iso in meta.get("holidays_iso", []):
        return True
    extra = overrides if overrides is not None else _load_holiday_overrides(source_root)
    return iso in extra.get(key, [])


def venue_session_status(
    venue: str,
    ts_utc: datetime,
    source_root: Optional[Path] = None,
    overrides: Optional[Dict[str, List[str]]] = None,
) -> str:
    key = venue.upper()
    meta = _VENUE_DEFAULTS.get(key)
    if not meta:
        return "UNKNOWN_VENUE"
    tz = _safe_zone(str(meta["tz"]))
    if tz is None:
        return "NO_TZ"
    local = ts_utc.astimezone(tz)
    d = local.date()
    ov = overrides if overrides is not None else _load_holiday_overrides(source_root)
    if venue_is_holiday(key, d, source_root, ov):
        return "HOLIDAY"
    if local.weekday() >= 5:
        return "CLOSED"
    oh, om = meta["open_local"]
    ch, cm = meta["close_local"]
    t_open = time(oh, om)
    t_close = time(ch, cm)
    tt = local.timetz().replace(tzinfo=None)
    if t_open <= tt < t_close:
        return "OPEN"
    return "CLOSED"


class OmegaSessionClock:
    """Relógio canónico — instanciar por processo ou injectar."""

    def __init__(
        self,
        config: Optional[SessionClockConfig] = None,
        *,
        policy_tz: Optional[str] = None,
        broker_tz: Optional[str] = None,
        broker_offset_minutes: Optional[int] = None,
        terminal_tz: Optional[str] = None,
        source_root: Optional[Path] = None,
    ) -> None:
        if config is not None:
            self._cfg = config
        else:
            bo = broker_offset_minutes
            if bo is None and os.getenv("OMEGA_BROKER_OFFSET_MINUTES"):
                try:
                    bo = int(os.getenv("OMEGA_BROKER_OFFSET_MINUTES", ""))
                except ValueError:
                    bo = None
            sr = str(source_root) if source_root is not None else (os.getenv("OMEGA_SOURCE_ROOT") or None)
            self._cfg = SessionClockConfig(
                policy_tz=policy_tz or os.getenv("OMEGA_POLICY_TZ", "Europe/Berlin"),
                broker_tz=broker_tz or os.getenv("OMEGA_BROKER_TZ", "") or "",
                broker_offset_minutes=bo,
                terminal_tz=terminal_tz or os.getenv("OMEGA_TERMINAL_TZ", "") or "",
                source_root=sr,
            )
        self._root = Path(self._cfg.source_root) if self._cfg.source_root else source_root
        if self._root is None:
            self._root = Path.cwd()

        self._zi_policy = _safe_zone(self._cfg.policy_tz)
        self._zi_broker = _safe_zone(self._cfg.broker_tz) if self._cfg.broker_tz else None
        self._zi_terminal = _safe_zone(self._cfg.terminal_tz) if self._cfg.terminal_tz else None
        self._broker_offset = self._cfg.broker_offset_minutes

        # Uma leitura agregada de overrides por mtime (reutiliza cache global por ficheiro)
        self._holiday_overrides = _load_holiday_overrides(self._root)

    @classmethod
    def from_config(cls, config: SessionClockConfig) -> "OmegaSessionClock":
        return cls(config=config)

    def now_utc(self) -> datetime:
        return _utc_now()

    def snapshot(self, at: Optional[datetime] = None) -> ClockSnapshot:
        ts = at or self.now_utc()
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts = ts.astimezone(timezone.utc)

        iso_utc = _to_iso_z(ts)
        if self._zi_policy:
            iso_berlin = _to_iso_tz(ts, self._zi_policy)
        else:
            iso_berlin = iso_utc + " (FALLBACK_NO_ZONEINFO)"

        if self._zi_broker:
            iso_broker = _to_iso_tz(ts, self._zi_broker)
        elif self._broker_offset is not None:
            br = ts + timedelta(minutes=self._broker_offset)
            iso_broker = _to_iso_z(br) + f" (OFFSET_{self._broker_offset}m_vs_UTC)"
        else:
            iso_broker = iso_utc + " (BROKER_TZ_UNSET_ASSUME_UTC)"

        if self._zi_terminal:
            iso_term = _to_iso_tz(ts, self._zi_terminal)
        else:
            iso_term = datetime.now().astimezone().isoformat(timespec="seconds")

        sess = resolve_omega_session(ts)
        labels = {
            TimeRef.UTC.value: iso_utc,
            TimeRef.OMEGA_BERLIN.value: iso_berlin,
            TimeRef.BROKER.value: iso_broker,
            TimeRef.TERMINAL_LOCAL.value: iso_term,
        }
        return ClockSnapshot(
            ts_utc=ts,
            iso_utc=iso_utc,
            iso_omega_berlin=iso_berlin,
            iso_broker=iso_broker,
            iso_terminal_local=iso_term,
            omega_session_utc=sess,
            labels=labels,
        )

    def venue_snapshot(self, ts_utc: Optional[datetime] = None) -> Dict[str, str]:
        ts = ts_utc or self.now_utc()
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts = ts.astimezone(timezone.utc)
        return {
            v: venue_session_status(v, ts, self._root, self._holiday_overrides)
            for v in _VENUE_DEFAULTS
        }

    def audit_bundle(self, at: Optional[datetime] = None) -> Dict[str, Any]:
        snap = self.snapshot(at)
        venues = self.venue_snapshot(snap.ts_utc)
        return {
            "ts_utc": snap.iso_utc,
            "time_refs": snap.labels,
            "omega_session_utc": snap.omega_session_utc,
            "venue_status": venues,
            "audit_stamp": snap.audit_line(),
        }

    def compute_from_bars(self, df: Any = None, symbol: str = "UNKNOWN") -> ComponentState:
        """
        Interface OMEGA: o relógio não processa OHLCV; devolve saúde + snapshot actual.
        `df` ignorado (reservado para futuras extensões, ex. alinhar a barra do broker).
        """
        try:
            snap = self.snapshot()
            bundle = self.audit_bundle(snap.ts_utc)
            return ComponentState(
                is_valid=True,
                direction=0,
                strength=1.0,
                n_bars=0,
                meta={
                    "component": "omega_session_clock",
                    "symbol": symbol,
                    "ts_utc": snap.iso_utc,
                    "omega_session_utc": snap.omega_session_utc,
                    "audit_stamp": snap.audit_line(),
                    "venue_status": bundle.get("venue_status"),
                },
            )
        except Exception as e:
            return ComponentState(
                is_valid=False,
                direction=0,
                strength=0.0,
                n_bars=0,
                meta={"error": str(e), "symbol": symbol},
            )


def register_module() -> Dict[str, Any]:
    return {
        "OmegaSessionClock": OmegaSessionClock,
        "SessionClockConfig": SessionClockConfig,
        "ClockSnapshot": ClockSnapshot,
        "ComponentState": ComponentState,
        "TimeRef": TimeRef,
        "resolve_omega_session": resolve_omega_session,
        "venue_session_status": venue_session_status,
    }


def run_self_test() -> bool:
    errors: List[str] = []

    t = datetime(2026, 6, 1, 14, 0, 0, tzinfo=timezone.utc)
    if resolve_omega_session(t) != "INTERSESSION":
        errors.append("T01 INTERSESSION")

    t2 = datetime(2026, 6, 1, 18, 0, 0, tzinfo=timezone.utc)
    if resolve_omega_session(t2) != "OVERLAP":
        errors.append("T02 OVERLAP")

    clk = OmegaSessionClock(
        policy_tz="Europe/Berlin",
        broker_tz="UTC",
        terminal_tz="UTC",
    )
    s = clk.snapshot(t)
    if "Z" not in s.iso_utc:
        errors.append("T03 Z")

    vb = clk.venue_snapshot(t)
    if "NYSE" not in vb:
        errors.append("T04 NYSE")

    b = clk.audit_bundle(t)
    if "BROKER" not in b.get("audit_stamp", ""):
        errors.append("T05 BROKER stamp")

    st = clk.compute_from_bars(None, "TST")
    if not st.is_valid or st.direction != 0:
        errors.append("T06 compute_from_bars")

    cfg = SessionClockConfig.from_env()
    clk2 = OmegaSessionClock.from_config(cfg)
    if clk2.snapshot().iso_utc[-1] != "Z":
        errors.append("T07 from_env")

    if errors:
        for e in errors:
            print(f"[FAIL] {e}", file=sys.stderr)
        return False
    print("[OK] omega_session_clock self-test passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_self_test() else 1)
