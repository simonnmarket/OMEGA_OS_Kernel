"""
Padrão único OMEGA: identificar operações pelo campo `comment` (marca configurável).

- Marca atual: prefixo env `OMEGA_POSITION_MARK` (default "OV2|"), ou comentários
  legíveis que começam por OMEGA-V2-, OMEGA-AMI-, OMEGA_SCALE_.
- Compatível com posicionamento por pirâmide: comentários OMEGA_SCALE_* e/ou magic
  no intervalo OMEGA_SCALE_MAGIC_MIN .. OMEGA_SCALE_MAGIC_MAX (default 999111–999130).
- Legado apenas leitura: magic igual a `OMEGA_LEGACY_PRIMARY_MAGIC` (default "234001");
  definir env vazio para desativar esse reconhecimento.

Pedidos novos devem usar `build_v2_order_comment` ou comentários explicitamente cobertos
por `is_omega_managed_comment` — não é obrigatório enviar `magic` ao broker.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, List, Optional


def position_mark() -> str:
    return os.environ.get("OMEGA_POSITION_MARK", "OV2|")


def _legacy_primary_magic() -> Optional[int]:
    raw = os.environ.get("OMEGA_LEGACY_PRIMARY_MAGIC", "234001").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _scale_magic_bounds() -> tuple[int, int]:
    lo = int(os.getenv("OMEGA_SCALE_MAGIC_MIN", "999111"))
    hi = int(os.getenv("OMEGA_SCALE_MAGIC_MAX", "999130"))
    return (min(lo, hi), max(lo, hi))


def is_pyramid_scale_magic(magic: Optional[int]) -> bool:
    """True para camadas OmegaScaleManager (historial com magic por perna)."""
    if magic is None:
        return False
    lo, hi = _scale_magic_bounds()
    return lo <= magic <= hi


def is_omega_managed_comment(comment: Optional[str]) -> bool:
    """Marcas primárias OMEGA (comment) — entrada principal + escala nominal."""
    if not comment:
        return False
    c = comment.strip()
    mk = position_mark().strip()
    if mk and mk in c:
        return True
    if (
        c.startswith("OMEGA-V2-")
        or c.startswith("OMEGA-AMI-")
        or c.startswith("OMEGA_SCALE_")
        or c.startswith("OMEGA_LIVE_SIG")
        or c.startswith("OE_V5_")
        or "OMEGA_V550" in c
    ):
        return True
    return False


def is_omega_tracked_comment_magic(comment: Optional[str], magic: Optional[int]) -> bool:
    """OMEGA institucional: comment reconhecível OU pirâmide OU magic legado primário."""
    if is_omega_managed_comment(comment):
        return True
    if is_pyramid_scale_magic(magic):
        return True
    leg = _legacy_primary_magic()
    if leg is not None and magic is not None and int(magic) == leg:
        return True
    return False


def is_omega_tracked_position(position: Any) -> bool:
    """Aceita objeto MT5 Position ou dict (ex.: ._asdict())."""
    if isinstance(position, dict):
        cm = position.get("comment")
        mg = position.get("magic")
    else:
        cm = getattr(position, "comment", None)
        mg = getattr(position, "magic", None)
    return is_omega_tracked_comment_magic(
        cm if isinstance(cm, str) else None,
        mg,
    )


def is_omega_tracked_deal(deal: Any) -> bool:
    """Deal MT5: mesma política que posição (comment/magic pirâmide/legacy)."""
    cm = getattr(deal, "comment", None)
    mg = getattr(deal, "magic", None)
    cc = cm if isinstance(cm, str) else None
    return is_omega_tracked_comment_magic(cc, mg)


def filter_omega_tracked_positions(
    positions: Optional[List[Any]],
) -> List[Any]:
    if not positions:
        return []
    return [p for p in positions if is_omega_tracked_position(p)]


def omega_tracked_history_deals(
    deals: Optional[List[Any]],
) -> List[Any]:
    """Inclui todos os deals cujo position_id já teve entrada OMEGA (IN)."""
    if not deals:
        return []
    import MetaTrader5 as mt5

    omega_pids: set = set()
    for d in deals:
        if getattr(d, "entry", None) == mt5.DEAL_ENTRY_IN and is_omega_tracked_deal(d):
            omega_pids.add(d.position_id)
    return [d for d in deals if d.position_id in omega_pids]


def build_v2_order_comment(tf: str, direction: str) -> str:
    eid = uuid.uuid4().hex[:6]
    base = f"{position_mark()}{eid}|{tf}|{direction[:1].upper()}"
    return base[:31]


def human_tag_line() -> str:
    """Resumo para logs (substitui exibições antigas só com magic primário)."""
    leg = _legacy_primary_magic()
    lo, hi = _scale_magic_bounds()
    return (
        f"comment_mark={position_mark()!r} legacy_magic={leg} "
        f"scale_magic_range={lo}..{hi}"
    )
