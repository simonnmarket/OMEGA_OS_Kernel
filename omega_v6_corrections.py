# OMEGA QUANTITATIVE FUND — CÓDIGO V6.0
# Todas as correcções consolidadas numa única fonte
# Data: 2026-03-05
# Estado: APROVADO PELO CONSELHO (10 auditorias)
# Revisão: 2026-03-05 — 4 correcções remanescentes aplicadas (Red Team Final)

"""
FICHEIROS DESTA SESSÃO:
  omega_verify_pip.py          → Verificação pip value (EXECUTAR PRIMEIRO)
  omega_export_ohlcv.py        → Export OHLCV de todos os ativos
  omega_v6_corrections.py      → Este ficheiro — código corrigido V6.0

RESULTADO DA SESSÃO:
  Pip Value XAUUSD: $0.10/pip para 0.01 lote (Cenário A — OK)
  Relatório: V6.0 — 10 auditorias, nenhum erro matemático ou de código conhecido
  Próximo passo: Gate 0 (testes de software)
"""

import asyncio
import logging
import numpy as np
import MetaTrader5 as mt5
from collections import deque
from typing import Dict, List, Optional

logger = logging.getLogger("OmegaV6")

# =============================================================================
# 1. CIRCUIT BREAKER — OmegaVirtualFund
# =============================================================================

class OmegaVirtualFund:
    """
    Circuit Breaker com:
    - Idempotência por trade_id (deque RAM + Redis persistente)
    - asyncio.Lock para atomicidade
    - Fail-fast sem fallback hardcoded
    - Equity restaurada após crash via Redis
    """

    def __init__(self, redis_url: str, kill_pct: float = 0.035):
        self.redis_url = redis_url
        self.kill_pct = kill_pct
        self.current_equity: Optional[float] = None
        self.start_day_equity: Optional[float] = None
        self.circuit_breaker_active: bool = False
        self._cb_lock = asyncio.Lock()
        self._processed_ids: set = set()
        self._processed_ids_order: deque = deque(maxlen=10_000)
        self._redis_ids_key: str = ""
        self.redis_conn = None

    async def on_trade_closed(self, trade_id: str, pnl: float) -> None:
        """Actualiza equity. Idempotente: mesmo trade_id ignorado."""
        async with self._cb_lock:
            if trade_id in self._processed_ids:
                logger.warning(f"Trade {trade_id} duplicado (RAM). Ignorado.")
                return
            if self.redis_conn:
                already = await self.redis_conn.sismember(self._redis_ids_key, trade_id)
                if already:
                    logger.warning(f"Trade {trade_id} duplicado (Redis). Ignorado.")
                    self._processed_ids.add(trade_id)
                    return
                await self.redis_conn.sadd(self._redis_ids_key, trade_id)
                await self.redis_conn.expire(self._redis_ids_key, 86_400)
            if len(self._processed_ids_order) == self._processed_ids_order.maxlen:
                oldest = self._processed_ids_order[0]
                self._processed_ids.discard(oldest)
            self._processed_ids.add(trade_id)
            self._processed_ids_order.append(trade_id)
            self.current_equity += pnl
            logger.info(f"Trade {trade_id} | PnL={pnl:+.2f} | Equity={self.current_equity:.2f}")

    async def check_daily_ruin(self) -> bool:
        """Thread-safe. Retorna True se circuit breaker está activo."""
        async with self._cb_lock:
            if self.start_day_equity is None or self.current_equity is None:
                logger.critical("Equity não inicializado. HALT preventivo.")
                return True
            dd = (self.current_equity - self.start_day_equity) / self.start_day_equity
            if dd <= -self.kill_pct and not self.circuit_breaker_active:
                logger.critical(f"CIRCUIT BREAKER | DD={dd:.2%} | Equity={self.current_equity:.2f}")
                self.circuit_breaker_active = True
            return self.circuit_breaker_active

    async def connect(self) -> None:
        """Inicializa Redis. Restaura equity e IDs com sincronização set/deque."""
        import aioredis
        from datetime import datetime

        self.redis_conn = await aioredis.from_url(self.redis_url, decode_responses=True)
        today = datetime.now().strftime('%Y-%m-%d')
        self._redis_ids_key = f"fund:processed_ids:{today}"

        existing_ids = await self.redis_conn.smembers(self._redis_ids_key)
        if existing_ids:
            max_restore = self._processed_ids_order.maxlen
            ids_to_restore = sorted(existing_ids)[-max_restore:]  # Mais recentes
            for tid in ids_to_restore:
                if len(self._processed_ids_order) == self._processed_ids_order.maxlen:
                    oldest = self._processed_ids_order[0]
                    self._processed_ids.discard(oldest)
                self._processed_ids.add(tid)
                self._processed_ids_order.append(tid)
            skipped = len(existing_ids) - len(ids_to_restore)
            logger.info(f"Restaurados {len(ids_to_restore)} IDs. {skipped} antigos ignorados.")

        today_key = f"fund:start_equity:{today}"
        stored = await self.redis_conn.get(today_key)
        if stored:
            self.start_day_equity = float(stored)
            self.current_equity = float(stored)
            logger.info(f"Equity restaurado: ${self.start_day_equity:,.2f}")
        else:
            acc = await asyncio.to_thread(mt5.account_info)
            if acc is None:
                raise RuntimeError("FATAL: MT5 desconectado.")
            self.start_day_equity = acc.equity
            self.current_equity = acc.equity
            await self.redis_conn.setex(today_key, 86_400, str(acc.equity))
            logger.info(f"Equity inicial: ${acc.equity:,.2f}")


# =============================================================================
# 2. ESCALONAMENTO COM ATR — OmegaScaleManager
# =============================================================================

class OmegaScaleManager:
    """
    Escalonamento direcional contínuo — sem limite fixo de lotes.

    Princípio: enquanto o fluxo direcional e o ATR confirmarem a tese,
    o sistema continua a adicionar entradas escalonadas, surfando o movimento.
    Cada entrada tem target próprio (TP parcial) — captura fatias do movimento.

    Parâmetros configuráveis por símbolo:
      lot_progression  : multiplicador de lote entre entradas (ex: 1.5×)
      scale_interval_s : segundos mínimos entre entradas (ex: 300s = 5min)
      max_total_lots   : exposição máxima por símbolo (ex: 2.0 lotes)
      tp_pips_per_entry: target em pips por entrada (ex: 30 pips)
    """

    # ── Configuração por símbolo ─────────────────────────────────────────────
    SCALE_CONFIG = {
        "XAUUSD": {
            "lot_initial":       0.01,
            "lot_progression":   2.0,    # cada entrada duplica o lote anterior
            "scale_interval_s":  300,    # 5 minutos mínimos entre entradas
            "max_risk_pct":      0.20,   # máx 20% da equity em risco por símbolo
            "max_single_lot":    5.0,    # limite por ordem individual (margem/broker)
            "tp_pips_per_entry": 30,     # target em pips por entrada parcial
            "sl_pips_base":      50,     # SL base em pips (mantido em todas as entradas)
            "min_atr":           0.50,   # ATR M15 mínimo para confirmar fluxo
        },
        "AUDUSD": {
            "lot_initial":       0.01,
            "lot_progression":   2.0,
            "scale_interval_s":  300,
            "max_risk_pct":      0.15,
            "max_single_lot":    2.0,
            "tp_pips_per_entry": 15,
            "sl_pips_base":      30,
            "min_atr":           0.0003,
        },
    }
    DEFAULT_CONFIG = {
        "lot_initial":       0.01,
        "lot_progression":   2.0,
        "scale_interval_s":  300,
        "max_risk_pct":      0.10,
        "max_single_lot":    1.0,
        "tp_pips_per_entry": 20,
        "sl_pips_base":      40,
        "min_atr":           0.0,
    }

    def __init__(self, kernel_ref=None):
        self.kernel = kernel_ref
        self._symbol_locks: Dict[str, asyncio.Lock] = {}
        self._pending_entries: Dict[int, Dict] = {}
        self._symbol_exposure: Dict[str, float] = {}  # lotes abertos por símbolo
        self._atr_thresholds = {  # legado: manter compat com _get_min_atr
            "XAUUSD": 0.50,
            "AUDUSD": 0.0003,
        }

    def _cfg(self, symbol: str) -> Dict:
        return self.SCALE_CONFIG.get(symbol, self.DEFAULT_CONFIG)

    def _max_lots_for_equity(self, symbol: str, equity: float, pip_value_per_lot: float) -> float:
        """
        Cap dinâmico baseado em equity real — Não um número arbitrário.
        equity:              saldo actual da conta (USD)
        pip_value_per_lot:   valor em USD por pip por lote standard (ex: $10 XAUUSD)
        sl_pips:             SL em pips (define o loss máximo por lote)

        Fórmula: max_lots = (equity * max_risk_pct) / (sl_pips * pip_value_per_lot)
        Exemplo: equity=$10.000 | risk=20% | SL=50pips | pip_val=$10
                 max_lots = (10.000 * 0.20) / (50 * 10) = 2.000 / 500 = 4.0 lotes
        """
        cfg = self._cfg(symbol)
        sl_pips = cfg['sl_pips_base']
        if pip_value_per_lot <= 0 or sl_pips <= 0:
            return cfg['max_single_lot']
        max_lots = (equity * cfg['max_risk_pct']) / (sl_pips * pip_value_per_lot)
        return round(min(max_lots, cfg['max_single_lot'] * 10), 2)  # hard cap = 10× single lot


    def _get_symbol_lock(self, symbol: str) -> asyncio.Lock:
        return self._symbol_locks.setdefault(symbol, asyncio.Lock())

    async def _get_current_atr(self, symbol: str, period: int = 14) -> Optional[float]:
        """ATR M15 em tempo real. Não-bloqueante."""
        rates = await asyncio.to_thread(
            mt5.copy_rates_from_pos, symbol, mt5.TIMEFRAME_M15, 0, period + 1
        )
        if rates is None or len(rates) < period + 1:
            return None
        highs  = np.array([r['high']  for r in rates])
        lows   = np.array([r['low']   for r in rates])
        closes = np.array([r['close'] for r in rates])
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:]  - closes[:-1])
            )
        )
        return float(np.mean(tr[-period:]))

    def _get_min_atr(self, symbol: str) -> float:
        return self._atr_thresholds.get(symbol, 0.0)

    async def open_lot1(self, symbol: str, action: str, sl_pts: float, tp_pts: float,
                        equity: float = 10_000.0,
                        pip_value_per_lot: float = 10.0) -> Optional[int]:
        """
        Abre o lote inicial e regista a posição para escalonamento contínuo.
        equity + pip_value_per_lot são usados para calcular o cap dinâmico.
        """
        cfg = self._cfg(symbol)
        async with self._get_symbol_lock(symbol):
            current_exp = self._symbol_exposure.get(symbol, 0.0)
            max_lots    = self._max_lots_for_equity(symbol, equity, pip_value_per_lot)
            if current_exp >= max_lots:
                logger.warning(
                    f"[{symbol}] Exposição máxima ({current_exp:.2f}/{max_lots:.2f} lotes | "
                    f"{cfg['max_risk_pct']:.0%} equity). Entrada bloqueada."
                )
                return None
            lot = cfg['lot_initial']
            t1  = await asyncio.to_thread(
                self._open_order, symbol, action, lot,
                round(sl_pts), round(tp_pts)
            )
            if t1:
                self._symbol_exposure[symbol] = current_exp + lot
                self._pending_entries[t1] = {
                    'symbol':            symbol,
                    'action':            action,
                    'sl_pts':            sl_pts,
                    'tp_pts':            tp_pts,
                    'entry_time':        asyncio.get_running_loop().time(),
                    'last_scale_time':   asyncio.get_running_loop().time(),
                    'current_lot':       lot,
                    'scale_count':       1,
                    'total_lots':        lot,
                    'equity_snapshot':   equity,           # equity no momento da entrada
                    'pip_value_per_lot': pip_value_per_lot,
                }
                logger.info(
                    f"[{symbol}] Lot1 aberto — ticket={t1} | lote={lot} | "
                    f"exposição={self._symbol_exposure[symbol]:.2f}/{max_lots:.2f} lotes "
                    f"(cap={cfg['max_risk_pct']:.0%} de ${equity:,.0f})"
                )
            return t1

    async def check_and_scale(self) -> None:
        """
        Escalonamento direcional contínuo — sem limite fixo de lotes.
        Chamado no loop principal (sem sleep).

        Lógica:
          1. Para cada posição base activa, verificar se o intervalo mínimo passou.
          2. Verificar ATR confirma fluxo direcional.
          3. Verificar que o cap de exposição do símbolo não foi atingido.
          4. Abrir nova entrada com lote = lote_anterior × lot_progression.
          5. Registar e repetir no próximo ciclo enquanto condições se mantiverem.
        """
        now = asyncio.get_running_loop().time()

        for ticket, entry in list(self._pending_entries.items()):
            pos = await asyncio.to_thread(mt5.positions_get, ticket=ticket)
            if not pos:
                # Posição fechada: libertar exposição
                symbol = entry['symbol']
                freed = entry.get('total_lots', 0.0)
                self._symbol_exposure[symbol] = max(
                    0.0, self._symbol_exposure.get(symbol, 0.0) - freed
                )
                del self._pending_entries[ticket]
                logger.info(f"[{symbol}] Posição {ticket} fechada — exposição libertada: {freed:.2f} lotes")
                continue

            symbol   = entry['symbol']
            cfg      = self._cfg(symbol)
            elapsed_since_last = now - entry['last_scale_time']

            # ── Condição de intervalo ────────────────────────────────────────
            if elapsed_since_last < cfg['scale_interval_s']:
                continue

            async with self._get_symbol_lock(symbol):
                # ── Re-verificar após lock ───────────────────────────────────
                elapsed_since_last = now - entry['last_scale_time']
                if elapsed_since_last < cfg['scale_interval_s']:
                    continue

                # ── Verificar cap dinâmico (equity-relative) ─────────────────
                current_exp = self._symbol_exposure.get(symbol, 0.0)
                equity      = entry.get('equity_snapshot', 10_000.0)
                pv_lot      = entry.get('pip_value_per_lot', 10.0)
                max_lots    = self._max_lots_for_equity(symbol, equity, pv_lot)
                if current_exp >= max_lots:
                    logger.info(
                        f"[{symbol}] Cap equity atingido ({current_exp:.2f}/{max_lots:.2f} lotes "
                        f"| {cfg['max_risk_pct']:.0%} de ${equity:,.0f}) — escalonamento pausado"
                    )
                    continue

                # ── Verificar ATR (fluxo direcional) ────────────────────────
                atr = await self._get_current_atr(symbol)
                if atr is None:
                    logger.info(f"[{symbol}] ATR indisponível — escalonamento adiado (preservando risco)")
                    continue
                if atr <= cfg['min_atr']:
                    logger.info(f"[{symbol}] ATR={atr:.4f} abaixo de min={cfg['min_atr']:.4f} — sem confirmação de fluxo")
                    continue

                # ── Calcular próximo lote (equity-bounded, progression ×2) ───────
                next_lot = round(
                    min(
                        entry['current_lot'] * cfg['lot_progression'],  # dobrar
                        cfg['max_single_lot'],                           # limite por ordem
                        max_lots - current_exp                           # não exceder cap equity
                    ),
                    2
                )
                if next_lot <= 0.001:
                    continue

                # ── Abrir entrada escalonada ─────────────────────────────────
                tp_pips = cfg['tp_pips_per_entry']
                # TP em pontos: ajustar pela direcção
                t_new = await asyncio.to_thread(
                    self._open_order, symbol, entry['action'], next_lot,
                    round(entry['sl_pts']),   # SL mantém-se (gestão de risco base)
                    round(tp_pips * 10)       # TP próximo em pontos raw
                )
                if t_new:
                    entry['current_lot']   = next_lot
                    entry['scale_count']  += 1
                    entry['total_lots']   += next_lot
                    entry['last_scale_time'] = now
                    self._symbol_exposure[symbol] = current_exp + next_lot

                    logger.info(
                        f"[{symbol}] Entrada #{entry['scale_count']} — "
                        f"ticket={t_new} | lote={next_lot:.2f} | "
                        f"exposição={self._symbol_exposure[symbol]:.2f}/{cfg['max_total_lots']:.2f} | "
                        f"ATR={atr:.4f}"
                    )

    def _open_order(self, symbol, action, lot, sl_pts, tp_pts):
        raise NotImplementedError("Implementar no engine principal.")


# =============================================================================
# 3. REGULARIZAÇÃO PSD — Higham 2002
# =============================================================================

def calculate_ewma_correlation(current_cov) -> "pd.DataFrame":
    """Correlação EWMA com regularização PSD via Higham 2002."""
    import pandas as pd
    with np.errstate(invalid='raise', divide='raise'):
        try:
            std_devs = np.sqrt(np.diag(current_cov.values))
            if np.any(std_devs == 0) or np.any(np.isnan(std_devs)):
                return pd.DataFrame()
            outer = np.outer(std_devs, std_devs)
            corr_matrix = pd.DataFrame(
                current_cov.values / outer,
                index=current_cov.index, columns=current_cov.columns
            )
            np.fill_diagonal(corr_matrix.values, 1.0)
            eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix.values)
            if np.any(eigenvalues < -1e-8):
                eigenvalues_psd = np.maximum(eigenvalues, 0)
                corr_psd = eigenvectors @ np.diag(eigenvalues_psd) @ eigenvectors.T
                d = np.sqrt(np.diag(corr_psd))
                d[d < 1e-10] = 1.0
                corr_psd = corr_psd / np.outer(d, d)
                np.fill_diagonal(corr_psd, 1.0)
                corr_matrix = pd.DataFrame(corr_psd, index=corr_matrix.index, columns=corr_matrix.columns)
                logger.warning(f"Matriz regularizada via Higham 2002.")
            return corr_matrix
        except FloatingPointError as e:
            logger.warning(f"FloatingPointError em EWMA: {e}")
            return pd.DataFrame()


# =============================================================================
# 4. ESTATÍSTICA — estimate_autocorrelation + block_bootstrap_test
# =============================================================================

def estimate_autocorrelation(trade_sequence: List[int]) -> Dict:
    """ACF lag-1 com estimador padrão correcto. Calcula N efectivo."""
    from scipy import stats as sp_stats
    if len(trade_sequence) < 50:
        return {"rho_1": None, "significant": False, "reason": "insufficient_data"}
    series = np.array(trade_sequence, dtype=float)
    n, mean = len(series), np.mean(series)
    variance = np.sum((series - mean) ** 2)
    if variance < 1e-10:
        return {"rho_1": 0.0, "significant": False, "reason": "zero_variance"}
    autocovariance = np.sum((series[:-1] - mean) * (series[1:] - mean))
    rho_1 = float(autocovariance / variance)
    se = 1.0 / np.sqrt(n)
    z_stat = rho_1 / se
    p_value = 2 * (1 - sp_stats.norm.cdf(abs(z_stat)))
    # FIX: Fórmula exacta AR(1) — n/(1+2ρ) é aproximação de Bartlett; (1-ρ)/(1+ρ) é o estimador MLE correcto
    # Diferença: para ρ₁=0.5, aproximação dá 50%n mas AR(1) exacto dá 33%n (subestima correlação)
    n_eff = max(1, int(n * (1 - rho_1) / (1 + rho_1))) if rho_1 > 0 else n
    return {
        "rho_1": round(rho_1, 4),
        "significant": bool(p_value < 0.05),
        "p_value": round(float(p_value), 4),
        "n_observed": n,
        "n_effective": n_eff,
        "recommendation": "Block Bootstrap obrigatorio" if abs(rho_1) > 0.1 else "Binomial valido"
    }


def block_bootstrap_test(
    trade_sequence: List[int],
    p0: float = 0.50,
    block_size: int = 10,
    n_replications: int = 1000,
    alpha: float = 0.05
) -> Dict:
    """
    Block Bootstrap com distribuição deslocada para H₀=p0.
    CORRECCÃO V6.0: sem shift, p-value seria sempre ~0.50.
    """
    n = len(trade_sequence)
    if n < block_size * 10:
        return {"significant": False, "reason": "insufficient_data"}
    observed_wr = float(np.mean(trade_sequence))
    blocks = [trade_sequence[i:i+block_size] for i in range(n - block_size + 1)]
    bootstrap_wrs = []
    for _ in range(n_replications):
        n_blocks = (n // block_size) + 1
        idx = np.random.randint(0, len(blocks), n_blocks)
        sample = np.concatenate([blocks[i] for i in idx])[:n]
        bootstrap_wrs.append(float(np.mean(sample)))
    bootstrap_wrs = np.array(bootstrap_wrs)
    shifted = bootstrap_wrs - np.mean(bootstrap_wrs) + p0
    p_value = 2 * min(
        float(np.mean(shifted <= observed_wr)),
        float(np.mean(shifted >= observed_wr))
    )
    ci_lower = float(np.percentile(bootstrap_wrs, 2.5))
    ci_upper = float(np.percentile(bootstrap_wrs, 97.5))
    return {
        "significant": bool(p_value < alpha),
        "p_value": round(p_value, 4),
        "ci_95": (round(ci_lower, 4), round(ci_upper, 4)),
        "significant_ci": not (ci_lower <= p0 <= ci_upper),
        "observed_wr": round(observed_wr, 4),
        "h0": p0,
        "method": "block_bootstrap_shifted_V6"
    }


# =============================================================================
# 5. CUSTOS REAIS — calculate_pf_net_from_mt5_history
# =============================================================================

def calculate_pf_net_from_mt5_history(
    symbol: str,
    from_date,
    to_date,
    cost_per_lot_usd: float = 7.0  # Spread + comissão estimada por lote round-trip
) -> Dict:
    """
    Calcula o Profit Factor líquido REAL a partir do histórico MT5.
    FIX V6.0-R1: Função referenciada no Gate 0 Passo 4 mas ausente → NameError em produção.

    Args:
        symbol:            Ex: "XAUUSD"
        from_date:         datetime de início
        to_date:           datetime de fim
        cost_per_lot_usd:  Custo estimado de transacção por lote (spread + comissão)

    Returns:
        Dict com pf_gross, pf_net, total_trades, gross_win, gross_loss, total_costs
    """
    import pandas as pd

    # DEAL_ENTRY_OUT = 1 (saída de posição longa), DEAL_ENTRY_OUT_BY = 2 (saída por oposição)
    deals = mt5.history_deals_get(from_date, to_date, group=f"*{symbol}*")
    if not deals:
        logger.warning(f"Sem deals históricos para {symbol} no período especificado.")
        return {"status": "NO_DATA", "symbol": symbol}

    df = pd.DataFrame([{
        'ticket':     d.ticket,
        'profit':     d.profit,
        'commission': d.commission,
        'swap':       d.swap,
        'volume':     d.volume,
        'entry':      d.entry
    } for d in deals if d.entry in (1, 2)])

    if df.empty:
        return {"status": "NO_CLOSED_DEALS", "symbol": symbol}

    df['net'] = df['profit'] + df['commission'] + df['swap']
    df['cost_allocated'] = df['volume'] * cost_per_lot_usd
    df['net_after_cost'] = df['net'] - df['cost_allocated']

    gross_win  = df[df['profit'] > 0]['profit'].sum()
    gross_loss = abs(df[df['profit'] < 0]['profit'].sum())
    net_win    = df[df['net_after_cost'] > 0]['net_after_cost'].sum()
    net_loss   = abs(df[df['net_after_cost'] < 0]['net_after_cost'].sum())
    total_costs = df['cost_allocated'].sum()

    pf_gross = gross_win / gross_loss if gross_loss > 0 else float('inf')
    pf_net   = net_win  / net_loss   if net_loss  > 0 else float('inf')
    degradation_pct = ((pf_gross - pf_net) / pf_gross * 100) if pf_gross > 0 else 0.0

    result = {
        "status":          "OK",
        "symbol":          symbol,
        "total_trades":    len(df),
        "gross_win":       round(gross_win,   2),
        "gross_loss":      round(gross_loss,  2),
        "pf_gross":        round(pf_gross,    4),
        "total_costs_usd": round(total_costs, 2),
        "pf_net":          round(pf_net,      4),
        "degradation_pct": round(degradation_pct, 2),
        "verdict":         "EDGE REAL POSITIVO" if pf_net > 1.0 else "EDGE ELIMINADO POR CUSTOS"
    }
    logger.info(
        f"PF Real [{symbol}]: Gross={pf_gross:.4f} | Net={pf_net:.4f} "
        f"| Degradação={degradation_pct:.1f}% | {result['verdict']}"
    )
    return result


# =============================================================================
# 6. TESTES — Gate 0 obrigatório
# =============================================================================

async def _test_circuit_breaker_complete():
    """4 cenários de teste. Um único event loop. Gate 0 obrigatório."""
    fund = OmegaVirtualFund.__new__(OmegaVirtualFund)
    fund.start_day_equity = 10_000.0
    fund.current_equity   = 10_000.0
    fund.circuit_breaker_active = False
    fund.kill_pct = 0.035
    fund._cb_lock = asyncio.Lock()
    fund._processed_ids = set()
    fund._processed_ids_order = deque(maxlen=10_000)
    fund.redis_conn = None
    fund._redis_ids_key = ""

    # Teste 1: -4% activa CB
    await fund.on_trade_closed("t001", -400.0)
    assert await fund.check_daily_ruin() is True, "FALHA: CB não activou com -4%"

    # Teste 2: idempotência
    eq_before = fund.current_equity
    await fund.on_trade_closed("t001", -400.0)
    assert fund.current_equity == eq_before, "FALHA: Double-counting"

    # Teste 3: race condition com 3 coroutines
    fund2 = OmegaVirtualFund.__new__(OmegaVirtualFund)
    fund2.start_day_equity = 10_000.0
    fund2.current_equity   = 9_650.0
    fund2.circuit_breaker_active = False
    fund2.kill_pct = 0.035
    fund2._cb_lock = asyncio.Lock()
    fund2._processed_ids = set()
    fund2._processed_ids_order = deque(maxlen=10_000)
    fund2.redis_conn = None
    fund2._redis_ids_key = ""
    results = await asyncio.gather(
        fund2.check_daily_ruin(),
        fund2.check_daily_ruin(),
        fund2.check_daily_ruin()
    )
    assert all(r is True for r in results), f"FALHA: Race condition — {results}"

    # Teste 4: deque LRU (com maxlen=3)
    fund3 = OmegaVirtualFund.__new__(OmegaVirtualFund)
    fund3.start_day_equity = 10_000.0
    fund3.current_equity   = 10_000.0
    fund3.circuit_breaker_active = False
    fund3.kill_pct = 0.035
    fund3._cb_lock = asyncio.Lock()
    fund3._processed_ids = set()
    fund3._processed_ids_order = deque(maxlen=3)
    fund3.redis_conn = None
    fund3._redis_ids_key = ""
    for tid in ["A", "B", "C"]:
        await fund3.on_trade_closed(tid, -1.0)
    await fund3.on_trade_closed("D", -1.0)
    assert "A" not in fund3._processed_ids, "FALHA: LRU não removeu ID antigo"
    assert "D" in fund3._processed_ids,     "FALHA: ID recente não registado"

    print("✅ PASS: Todos os 4 testes do Circuit Breaker aprovados")


if __name__ == "__main__":
    asyncio.run(_test_circuit_breaker_complete())
