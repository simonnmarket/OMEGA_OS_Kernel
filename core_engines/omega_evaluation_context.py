"""
OMEGA — contexto temporal e peso de evidência para avaliação (regra CIO/CEO).

Objectivo: cada run/ciclo fica etiquetado com data, dia da semana, semana ISO, ano,
hora UTC e um peso de interpretabilidade fixo por dia — para, na revisão posterior,
não confundir evidência de fim‑de‑semana (ex.: crypto) com dias úteis (cross‑asset).

O peso é intrínseco ao calendário UTC (não se ajusta por conveniência operacional).
Override opcional só para auditoria/teste controlado:
  OMEGA_EVAL_EVIDENCE_WEIGHT_OVERRIDE=0.5
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

# Python weekday: Monday=0 … Sunday=6 (ISO‑like)
_DIA_PT = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

# Peso 0.0–1.0: capacidade agregada de um dia suportar conclusões multi‑classe / sessões.
# Fim‑de‑semana < 1.0 reflecte que paper dominado por crypto não substitui segunda com FX/XAU.
_EVIDENCE_WEIGHT_BY_WEEKDAY = (
    1.00,  # seg
    1.00,  # ter
    1.00,  # qua
    1.00,  # qui
    0.92,  # sex — rollover / fechos parciais por classe
    0.42,  # sáb — evidência parcial (regra CIO: crypto / infra)
    0.38,  # dom — idem
)


def _tier_for_weekday(wd: int) -> str:
    if wd < 4:
        return "WEEKDAY_CORE"
    if wd == 4:
        return "FRIDAY_ROLLOVER"
    return "WEEKEND_PARTIAL"


def build_evaluation_context(now: datetime | None = None) -> Dict[str, Any]:
    """
    Retorna dict JSON‑serializável com carimbo temporal e peso de evidência.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    wd = int(now.weekday())
    iso = now.isocalendar()
    iso_year, iso_week, iso_wday = int(iso[0]), int(iso[1]), int(iso[2])

    weight = float(_EVIDENCE_WEIGHT_BY_WEEKDAY[wd])
    override_raw = os.getenv("OMEGA_EVAL_EVIDENCE_WEIGHT_OVERRIDE", "").strip()
    override_applied = False
    if override_raw:
        try:
            weight = max(0.0, min(1.0, float(override_raw)))
            override_applied = True
        except ValueError:
            pass

    return {
        "rule_id": "OIS-EVAL-CALENDAR-v1",
        "timezone": "UTC",
        "utc_iso": now.isoformat(),
        "date_utc": now.strftime("%Y-%m-%d"),
        "time_utc": now.strftime("%H:%M:%S"),
        "weekday_iso_0_mon": wd,
        "dia_semana_pt": _DIA_PT[wd],
        "iso_week": iso_week,
        "iso_week_year": iso_year,
        "iso_weekday_1_mon_7_sun": iso_wday,
        "gregorian_year": now.year,
        "evidence_tier": _tier_for_weekday(wd),
        "evidence_weight": round(weight, 4),
        "evidence_weight_override_applied": override_applied,
        "evidence_note_pt": (
            "Peso 1.0 = dia útil núcleo (interpretação cross‑asset plena). "
            "Peso <1 (sex/fim‑semana) = evidência útil mas não substitui validação em dia núcleo; "
            "ver plano CIO (crypto sábado vs portefólio segunda)."
        ),
    }


def format_eval_log_line(ctx: Dict[str, Any]) -> str:
    """Uma linha compacta para logs (grep-friendly)."""
    return (
        f"date={ctx.get('date_utc')} dow={ctx.get('weekday_iso_0_mon')} "
        f"iso_w{ctx.get('iso_week')}/{ctx.get('iso_week_year')} "
        f"tier={ctx.get('evidence_tier')} weight={ctx.get('evidence_weight')}"
    )
