import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("CORRELATION_FILTER")

# ---------------------------------------------------------------------------
# Mapa estático de pares de alta correlação por classe de ativo.
# Regra de bloqueio: mesma direção em ativo correlacionado = dupla exposição
# direcional = BLOQUEADO. Direção oposta (hedge) = PERMITIDO.
#
# Referências: Bridgewater All Weather (max 10%/ativo), JPMorgan (max 30%/classe),
#              Citadel (Pearson > 0.70 = correlacionado).
# ---------------------------------------------------------------------------
CORR_PAIRS: Dict[str, List[str]] = {
    # FOREX: pares negativamente correlacionados com USD (movem juntos)
    "EURUSD": ["GBPUSD", "AUDUSD"],
    "GBPUSD": ["EURUSD", "AUDUSD"],
    "AUDUSD": ["EURUSD", "GBPUSD"],
    # FOREX: pares positivamente correlacionados com USD
    "USDJPY": ["USDCAD", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY"],
    "USDCAD": ["USDJPY"],
    # JPY CROSSES: correlacionadas entre si (carry-trade theme)
    # Nota: fora do cluster mode, bloqueia dupla exposição em crosses JPY.
    # No cluster mode (cluster_allowed=True), o bloqueio é suprimido.
    "EURJPY": ["GBPJPY", "AUDJPY", "CADJPY", "CHFJPY"],
    "GBPJPY": ["EURJPY", "AUDJPY", "CADJPY", "CHFJPY"],
    "AUDJPY": ["EURJPY", "GBPJPY", "CADJPY", "CHFJPY"],
    "CADJPY": ["EURJPY", "GBPJPY", "AUDJPY", "CHFJPY"],
    "CHFJPY": ["EURJPY", "GBPJPY", "AUDJPY", "CADJPY"],
    # CRYPTO: alta correlação interna (BTC/ETH/SOL movem em conjunto)
    "BTCUSD": ["ETHUSD", "SOLUSD", "DOGUSD"],
    "ETHUSD": ["BTCUSD", "SOLUSD", "DOGUSD"],
    "SOLUSD": ["BTCUSD", "ETHUSD"],
    "DOGUSD": ["BTCUSD", "ETHUSD"],
    # INDICES: índices de equity EUA movem juntos
    "US500":  ["NAS100"],
    "NAS100": ["US500"],
    # METALS: ouro e prata correlacionados
    "XAUUSD": ["XAGUSD"],
    "XAGUSD": ["XAUUSD"],
}

# Grupo JPY Cluster — quando cluster_allowed=True, os membros deste grupo
# podem operar simultaneamente na mesma direção (intencionalmente correlacionados).
JPY_CLUSTER_GROUP: set = {"USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY"}

# MT5 position type constants (importação defensiva)
_MT5_BUY  = 0
_MT5_SELL = 1


class CorrelationFilter:
    """
    Filtro de Correlação de Portfolio - OMEGA v9.0 (PSA-approved)

    Duas camadas de proteção:
    1. Johansen (legado CEO v8.2) — cointegração estatística XAUUSD/XAGUSD/DXY
    2. Direction-aware Pearson map — bloqueia dupla exposição direcional em
       pares de alta correlação para todos os 11 ativos multi-classe.

    API backward-compatible: should_trade(asset, positions, direction=None)
    """

    def __init__(self):
        self.johansen_db_path = (
            Path(__file__).resolve().parent.parent.parent
            / "Auditoria PARR-F"
            / "johansen_test_results.json"
        )
        self._cache: Dict[str, List[Dict]] = {}
        self._load_johansen_state()

    def _load_johansen_state(self) -> None:
        """Carrega resultados do teste de Johansen (cobertura XAUUSD)."""
        try:
            if self.johansen_db_path.exists():
                with open(self.johansen_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for pair in data.get("pairs_tested", []):
                    if "XAUUSD" in pair.get("asset_A", ""):
                        self._cache.setdefault("XAUUSD", []).append({
                            "asset_B": pair.get("asset_B"),
                            "cointegrated": pair.get("cointegrated", True),
                            "trace_statistic": pair.get("trace_statistic", 0.0),
                        })
                log.info("[JOHANSEN] DB carregado. %d anchors.", len(self._cache))
            else:
                log.warning("[JOHANSEN] DB nao encontrado — check Johansen ignorado.")
        except Exception as exc:
            log.error("[JOHANSEN] Erro ao carregar: %s", exc)

    def should_trade(
        self,
        asset: str,
        open_positions: Optional[List[Dict]] = None,
        direction: Optional[str] = None,
        cluster_allowed: bool = False,
    ) -> bool:
        """
        Retorna True se o trade proposto NAO cria risco de correlacao excessiva.

        Args:
            asset:          Simbolo do ativo a ser negociado.
            open_positions: Lista de posicoes abertas (dicts _asdict() do MT5).
                            DEVE conter TODAS as posicoes OMEGA rastreadas (modules.mt5_position_tag),
                            nao apenas as do ativo atual.
            direction:      'BUY' ou 'SELL' — direcao proposta para o novo trade.

        Regras:
          - Mesma direcao em ativo correlacionado (Pearson >= 0.70) -> BLOCK
          - Direcao oposta (hedge natural) -> ALLOW
          - Sem direction ou sem posicoes -> ALLOW (nao ha contexto para bloquear)
          - Johansen falhou (cointegrated=False) -> BLOCK (legado CEO v8.2)
        """
        asset_up = asset.upper()
        open_positions = open_positions or []

        # --- Camada 1: Johansen (legado — cobertura XAUUSD) ---
        if asset_up in self._cache:
            for p in self._cache[asset_up]:
                if not p.get("cointegrated", True):
                    log.warning(
                        "[CORR][JOHANSEN] BLOCKED %s — dissociacao macroeconomica "
                        "frente a %s (trace=%.3f)",
                        asset, p["asset_B"], p.get("trace_statistic", 0),
                    )
                    return False

        # --- Camada 2: Direction-aware correlation map ---
        if not direction or not open_positions:
            return True

        corr_assets = CORR_PAIRS.get(asset_up, [])
        if not corr_assets:
            return True

        # JPY CLUSTER EXEMPTION: se cluster_allowed=True e o ativo pertence ao
        # cluster JPY, supprime o bloqueio entre membros do cluster (intencionalmente
        # correlacionados — carry-trade simultâneo aprovado pelo Conselho 28/04/2026).
        if cluster_allowed and asset_up in JPY_CLUSTER_GROUP:
            log.info(
                "[CORR][CLUSTER] ALLOWED %s %s — JPY cluster mode ativo (correlação intencional).",
                asset, direction,
            )
            return True

        # Monta mapa simbolo -> direcao das posicoes abertas
        open_dirs: Dict[str, str] = {}
        for pos in open_positions:
            sym = str(pos.get("symbol", "")).upper()
            pos_type = pos.get("type", -1)
            if pos_type == _MT5_BUY:
                open_dirs[sym] = "BUY"
            elif pos_type == _MT5_SELL:
                open_dirs[sym] = "SELL"

        proposed_dir = direction.upper()
        for corr in corr_assets:
            # No cluster mode, não bloqueamos cruzamentos intra-cluster JPY
            if cluster_allowed and corr.upper() in JPY_CLUSTER_GROUP and asset_up in JPY_CLUSTER_GROUP:
                continue
            existing_dir = open_dirs.get(corr.upper())
            if existing_dir and existing_dir == proposed_dir:
                log.warning(
                    "[CORR][DIRECTION] BLOCKED %s %s — posicao %s %s ja aberta "
                    "(dupla exposicao direcional correlacionada).",
                    asset, proposed_dir, corr, existing_dir,
                )
                return False

        return True
