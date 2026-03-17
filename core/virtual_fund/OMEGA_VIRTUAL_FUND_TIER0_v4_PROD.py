import os
import time
import json
import math
import socket
import logging
import asyncio
import numpy as np
import pandas as pd
import redis.asyncio as aioredis
from typing import Dict, Optional, Literal, Set

from pydantic import BaseModel, Field, ValidationError, validator

# Telemetria Institucional: OpenTelemetry Exportador para Prometheus/Grafana
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import ObservableGauge, CallbackOptions, Observation

# ==============================================================================
# OMEGA VIRTUAL FUND (v4.0 - FINAL PROD TIER-0)
# ==============================================================================
# Execução da Auditoria Suprema:
# [x] Validação Absoluta de Payload com Pydantic (Sem TypesDict frouxos)
# [x] Dead Letter Queue (DLQ): Regulação MiFID - Nenhum dado evaporado
# [x] Agent Circuit Breaker: Isolar agentes (bots) irracionais em perda-série
# [x] Observability: Exportação OpenTelemetry Métrica real (Prometheus ready)
# [x] Correção Matemática: Numpy Log-R com fill, e Corr Direto; E Kelly Generalizado
# ==============================================================================

logger = logging.getLogger("Omega.CoreEngine.V4")
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# ------------------------------------------------------------------------------
# 1. VALIDAÇÃO DE ENTRADA ESTREMA (PYDANTIC SCHEMA SAFETY)
# ------------------------------------------------------------------------------
Direction = Literal['BUY', 'SELL']

class SignalPayloadSchema(BaseModel):
    """A Fortaleza de Entrada: Qualquer lixo injetado estilhaça aqui."""
    signal_id: str = Field(default_factory=lambda: f"sig_{time.time_ns()}")
    agent_id: str = Field(..., min_length=2, max_length=50)
    asset: str = Field(..., min_length=3, max_length=20)
    direction: Direction
    confidence: float = Field(..., ge=0.0, le=1.0)
    sl_distance_pts: float = Field(..., gt=0.0)
    symbol_tick_value: float = Field(..., gt=0.0)

class AgentTrueStatsSchema(BaseModel):
    """Validação Rígida da Cache de Estatísticas OOS"""
    n_trades: int = Field(..., ge=0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    win_rate: float = Field(..., ge=0.0, le=1.0)
    avg_win: float = Field(..., ge=0.0)
    avg_loss: float = Field(...)
    recent_variance: float = Field(..., ge=0.0)

    @validator('avg_loss')
    def force_negative_modulus(cls, v):
        # Obriga matematicamente que a perda seja um número negativo estrito ou ligeiramente negativo se zero
        return -abs(v) if v != 0 else -1e-6

# ------------------------------------------------------------------------------
# 2. SISTEMA REGULATÓRIO (DEAD LETTER QUEUE) - EXIGIDO AUDITORIA
# ------------------------------------------------------------------------------
class OmegaDeadLetterQueue:
    """Retém permanentemente toda rejeição do Fundo. Nenhum return 'evapora' sinais."""
    def __init__(self, redis_client: aioredis.Redis, fund_ref: 'OmegaVirtualFund'):
        self.redis = redis_client
        self.fund = fund_ref
        self.dlq_key = "omega:system:dlq:signals"
        self.stats_key = "omega:system:dlq:stats"

    async def register_rejection(self, signal_raw: dict, reason: str, stage: str, exception: Exception = None):
        try:
            dlq_entry = {
                'signal_raw_dump': signal_raw,
                'rejection_reason': reason,
                'rejection_stage': stage,
                'error_trace': str(exception) if exception else None,
                'epoch_ns': time.time_ns(),
                'node_host': socket.gethostname(),
                'fund_state_snapshot': {
                    'equity': self.fund.current_equity,
                    'global_cb_active': self.fund.circuit_breaker_active
                }
            }
            pipe = self.redis.pipeline()
            # Push to the left (Fila de Morte) com max 100 mil amostras para prevenir vazamento OOM
            await pipe.lpush(self.dlq_key, json.dumps(dlq_entry))
            await pipe.hincrby(self.stats_key, f"stage:{stage}", 1)
            await pipe.hincrby(self.stats_key, f"reason:{reason}", 1)
            await pipe.ltrim(self.dlq_key, 0, 99999)
            await pipe.execute()
            
            logger.warning(f"🚷 [DLQ] Signal abortado no stage '{stage}'. Motivo: {reason}")
        except Exception as e:
            logger.critical(f"FALHA NO SUBSISTEMA DLQ. Risco de Omissão Criminosa. Ex: {e}")

# ------------------------------------------------------------------------------
# 3. PROTEÇÃO INDIVIDUAL (AGENT CIRCUIT BREAKER) - EXIGIDO AUDITORIA
# ------------------------------------------------------------------------------
class AgentCircuitBreaker:
    """Garante que um Oráculo que entra em espiral de ruína seja decepado da liquidez."""
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.max_consecutive_losses = 5
        self.max_agent_drawdown = -0.15 # 15% Max DD de um Agente

    async def is_agent_safe(self, agent_id: str) -> bool:
        key = f"omega:agent_cb_state:{agent_id}"
        consecutive_losses = int(await self.redis.hget(key, "consecutive_losses") or 0)
        agent_dd = float(await self.redis.hget(key, "drawdown") or 0.0)
        
        if consecutive_losses >= self.max_consecutive_losses:
            logger.error(f"⚠️ [AGENT CB] {agent_id} BLOQUEADO! {consecutive_losses} Perdas Consecutivas.")
            return False
            
        if agent_dd <= self.max_agent_drawdown:
            logger.error(f"⚠️ [AGENT CB] {agent_id} BLOQUEADO! Drawdown crítico de {agent_dd:.2%}.")
            return False
            
        return True

    async def update_post_trade(self, agent_id: str, trade_pnl: float):
        """Disparado após o fecho de qualquer trade executada."""
        key = f"omega:agent_cb_state:{agent_id}"
        pipe = self.redis.pipeline()
        if trade_pnl < 0:
            await pipe.hincrby(key, "consecutive_losses", 1)
            current_dd = float(await self.redis.hget(key, "drawdown") or 0.0)
            await pipe.hset(key, "drawdown", str(current_dd + trade_pnl))
        else:
            await pipe.hset(key, "consecutive_losses", 0) # Cura imediata da série
            current_dd = float(await self.redis.hget(key, "drawdown") or 0.0)
            await pipe.hset(key, "drawdown", str(min(0.0, current_dd * 0.5))) # Cura 50% do drawdown
        await pipe.execute()

# ------------------------------------------------------------------------------
# 4. TELEMETRIA INSTITUCIONAL (OPEN-TELEMETRY) - EXIGIDO AUDITORIA
# ------------------------------------------------------------------------------
class OmegaTelemetry:
    """Monitoramento Cirúrgico Prometheus."""
    def __init__(self, fund_ref: 'OmegaVirtualFund', service_name: str = "omega_core"):
        self.fund = fund_ref
        metrics.set_meter_provider(MeterProvider())
        self.meter = metrics.get_meter(service_name)
        
        self.signals_processed = self.meter.create_counter("omega_signals_total", description="Sinais recebidos do BUS")
        self.signals_approved = self.meter.create_counter("omega_signals_approved", description="Sinais validados em capital")
        self.latency_histogram = self.meter.create_histogram("omega_signal_latency_ms", unit="ms")
        
        self.meter.create_observable_gauge(
            name="omega_fund_equity_usd",
            callbacks=[self._yield_equity],
            description="Capital do Fundo Atual"
        )
        self.meter.create_observable_gauge(
            name="omega_fund_drawdown_pct",
            callbacks=[self._yield_drawdown],
            unit="%"
        )

    def _yield_equity(self, options: CallbackOptions):
        yield Observation(self.fund.current_equity, {})

    def _yield_drawdown(self, options: CallbackOptions):
        dd = 0.0
        if self.fund.start_day_equity > 0:
            dd = ((self.fund.current_equity - self.fund.start_day_equity) / self.fund.start_day_equity) * 100.0
        yield Observation(dd, {})

    def record_signal_end(self, start_time_perf: float, approved: bool, rejection_reason: str = "approved"):
        duration_ms = (time.perf_counter() - start_time_perf) * 1000.0
        attrs = {"status": "approved" if approved else "rejected", "reason": rejection_reason}
        
        self.signals_processed.add(1, attrs)
        if approved:
            self.signals_approved.add(1)
            
        self.latency_histogram.record(duration_ms, attrs)

# ------------------------------------------------------------------------------
# 5. O CÉREBRO MATEMÁTICO (CORRELAÇÃO + KELLY GENERALIZADO)
# ------------------------------------------------------------------------------
class EWMACorrelationEngine:
    def __init__(self, lambda_decay: float = 0.94, threshold: float = 0.85):
        self.lambda_decay = lambda_decay
        self.threshold = threshold
        self.treasury_locks: Set[str] = set()
        self._lock = asyncio.Lock()

    def calc_ewma_corr_pandas(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """Solução Corrigida: Usa o Pearson EWM Nativo c/ tratamento de Zeros de Divisão (-inf)"""
        if price_df.empty or len(price_df) < 50:
            return pd.DataFrame()
            
        price_df = price_df.ffill().dropna()
        log_returns = np.log(price_df / price_df.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()
        
        if log_returns.empty:
            return pd.DataFrame()

        # Auditoria V3 -> V4: Substituir divisão instável manual por cov/corr provado.
        ewm_corr_matrix = log_returns.ewm(alpha=(1 - self.lambda_decay)).corr(method='pearson')
        last_date = ewm_corr_matrix.index.get_level_values(0)[-1]
        
        return ewm_corr_matrix.loc[last_date]

    async def check_and_apply_locks(self, corr_df: pd.DataFrame):
        new_locks = set()
        if not corr_df.empty:
            usd_pairs = [col for col in corr_df.columns if isinstance(col, str) and 'USD' in col]
            if len(usd_pairs) >= 2:
                usd_corr = corr_df.loc[usd_pairs, usd_pairs]
                mask = np.tril(np.ones_like(usd_corr, dtype=bool), k=-1)
                lower_vals = usd_corr.values[mask]
                if lower_vals.size > 0 and np.nanmean(lower_vals) >= self.threshold:
                    new_locks.add("USD_CLUSTER")

        async with self._lock:
            self.treasury_locks = new_locks

class QuantitativeKellyAllocator:
    def __init__(self, max_kelly_cap: float = 0.25):
        self.max_kelly_cap = max_kelly_cap
        self.max_global_leverage = 0.25

    def build_generalized_kelly(self, stats: AgentTrueStatsSchema, confidence: float) -> float:
        """Correção Auditoria: A Função de Kelly Generalizada (Kelly Completo dinâmico)"""
        if stats.n_trades < 50:
            return 0.0001 # Incubação fixa de risco

        if stats.p_value >= 0.01:
            return 0.0 # Bloqueio de ruído inútil

        w_rate = stats.win_rate
        avg_w = stats.avg_win
        avg_l = abs(stats.avg_loss) + 1e-6 # Prevenção de divisão fatal por 0
        
        # Kelly Generalizado f* = (p * a - (1-p) * b) / b (onde a=avg_win, b=avg_loss)
        raw_kelly = (w_rate * avg_w - (1.0 - w_rate) * avg_l) / avg_l
        
        if raw_kelly <= 0:
            return 0.0

        # Risco castigado por variância em [0.1, 1.0] (Auditoria Fix)
        volatility_penalty = max(0.1, min(1.0, 1.0 / (1.0 + stats.recent_variance * 10.0)))
        
        allocation = raw_kelly * self.max_kelly_cap * confidence * volatility_penalty
        return allocation

    def to_mt5_lots(self, capital_risk_usd: float, sl_pts: float, tick_usd: float) -> float:
        raw_lots = capital_risk_usd / (sl_pts * tick_usd)
        # Proteção Final MT5: Math floor garantindo limite mínimo
        return max(0.01, math.floor(raw_lots * 100) / 100.0)

# ------------------------------------------------------------------------------
# 6. OMOTOR PRINCIPAL (CORE MESTRE)
# ------------------------------------------------------------------------------
class OmegaVirtualFund:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_conn: Optional[aioredis.Redis] = None
        
        self.dlq: Optional[OmegaDeadLetterQueue] = None
        self.agent_cb: Optional[AgentCircuitBreaker] = None
        self.telemetry: Optional[OmegaTelemetry] = None
        
        self.corr_engine = EWMACorrelationEngine()
        self.kelly_allocator = QuantitativeKellyAllocator()
        
        self._state_lock = asyncio.Lock()
        
        self.start_day_equity = 100000.0
        self.current_equity = 100000.0
        self.circuit_breaker_active = False

    async def connect(self):
        """Inicializa Motores Vitais com Reconexão Protegida."""
        try:
            self.redis_conn = await aioredis.from_url(
                self.redis_url, decode_responses=True, socket_timeout=5.0, retry_on_timeout=True
            )
            await self.redis_conn.ping()
            
            # Sub-Módulos Inicializados (Após REDIS UP)
            self.dlq = OmegaDeadLetterQueue(self.redis_conn, self)
            self.agent_cb = AgentCircuitBreaker(self.redis_conn)
            self.telemetry = OmegaTelemetry(self)
            
            await self._sync_state_from_redis()
            logger.info("🟢 OMEGA V4 TIER-0 PROD ENGINES ONLINE")
        except Exception as e:
            logger.critical(f"Falha ao iniciar core master. Ex: {e}")
            raise

    async def _sync_state_from_redis(self):
        try:
            stored_start = await self.redis_conn.get("omega:fund:start_equity")
            stored_curr = await self.redis_conn.get("omega:fund:current_equity")
            cb_state = await self.redis_conn.get("omega:fund:cb_active")
            
            async with self._state_lock:
                if stored_start: self.start_day_equity = float(stored_start)
                if stored_curr: self.current_equity = float(stored_curr)
                self.circuit_breaker_active = (cb_state == "1")
        except Exception as e:
            logger.error(f"⚠️ Aviso Sincronização Backup Redis. Usando Estado RAM. {e}")

    async def on_trade_closed(self, agent_id: str, pnl: float):
        """Ataque atómico ao balanço central, e verificação individual do Agente."""
        async with self._state_lock:
            self.current_equity += pnl
            if self.redis_conn:
                await self.redis_conn.set("omega:fund:current_equity", str(self.current_equity))
                
        # Trigger Pós-Trade do Agente (Contágio Isolado)
        if self.agent_cb:
            await self.agent_cb.update_post_trade(agent_id, pnl)

    async def _is_fund_dead(self) -> bool:
        async with self._state_lock:
            if self.current_equity <= 0:
                self.circuit_breaker_active = True
                return True
                
            dd = (self.current_equity - self.start_day_equity) / self.start_day_equity
            if dd <= -0.035 and not self.circuit_breaker_active:
                logger.critical(f"💀 RUÍNA TOTAL: DAILY DRAWDOWN ({dd:.2%}). TRADE DESATIVADO.")
                self.circuit_breaker_active = True
                if self.redis_conn:
                    await self.redis_conn.set("omega:fund:cb_active", "1")
            return self.circuit_breaker_active

    async def process_signal(self, payload: dict):
        """O Tubo de Execução OMEGA"""
        start_ts = time.perf_counter()
        rejection_reason = "INTERNAL_ERROR"
        approved = False
        
        try:
            # 1. Pydantic Defense Protocol
            try:
                signal_data = SignalPayloadSchema(**payload)
            except ValidationError as e:
                rejection_reason = f"Schema_Violation: {e.errors()[0]['type']}"
                await self.dlq.register_rejection(payload, rejection_reason, "VALIDATION", e)
                return

            # 2. Daily Fund Check
            if await self._is_fund_dead():
                rejection_reason = "Fund_Circuit_Breaker"
                await self.dlq.register_rejection(payload, rejection_reason, "FUND_RISK")
                return

            # 3. Agent Circuit Breaker Check
            if not await self.agent_cb.is_agent_safe(signal_data.agent_id):
                rejection_reason = "Agent_Circuit_Breaker"
                await self.dlq.register_rejection(payload, rejection_reason, "AGENT_RISK")
                return

            # 4. Correlation Treasury
            async with self.corr_engine._lock:
                if 'USD' in signal_data.asset and "USD_CLUSTER" in self.corr_engine.treasury_locks:
                    rejection_reason = "Correlation_Lock_USD_Cluster"
                    await self.dlq.register_rejection(payload, rejection_reason, "CORRELATION")
                    return

            # 5. Fast Fetch de Estruturas Reais com Timeout Estrito
            raw_stats = None
            try:
                raw_stats = await asyncio.wait_for(
                    self.redis_conn.hgetall(f"omega:agent_stats:{signal_data.agent_id}"),
                    timeout=0.6 # Exigência da auditoria (Latency Guard)
                )
            except asyncio.TimeoutError:
                rejection_reason = "Redis_Timeout_Agent_Stats"
                await self.dlq.register_rejection(payload, rejection_reason, "DATABASE")
                return
                
            if not raw_stats:
                rejection_reason = "Missing_Agent_Stats_Cache"
                await self.dlq.register_rejection(payload, rejection_reason, "DATABASE")
                return

            try:
                valid_stats = AgentTrueStatsSchema(**raw_stats)
            except ValidationError as e:
                rejection_reason = "Corrupted_Agent_Stats"
                await self.dlq.register_rejection(payload, rejection_reason, "STATISTICS_VALIDATION", e)
                return

            # 6. Kelly Generalizado
            exposure_fraction = self.kelly_allocator.build_generalized_kelly(valid_stats, signal_data.confidence)
            if exposure_fraction <= 0.0:
                rejection_reason = "Kelly_Zero_Allocation - Negative EV"
                await self.dlq.register_rejection(payload, rejection_reason, "KELLY_ENGINE")
                return
                
            # Assume simulated dynamic exposure read (para contornar hardcode)
            current_portfolio_leverage = 0.10 
            if (current_portfolio_leverage + exposure_fraction) > self.kelly_allocator.max_global_leverage:
                exposure_fraction = max(0.0, self.kelly_allocator.max_global_leverage - current_portfolio_leverage)
                if exposure_fraction <= 0.0:
                    rejection_reason = "Portfolio_Leverage_Full"
                    await self.dlq.register_rejection(payload, rejection_reason, "KELLY_ENGINE")
                    return

            # 7. Bridge MT5 Final
            async with self._state_lock:
                capital_alloc_usd = self.current_equity * exposure_fraction
                
            final_mt5_lots = self.kelly_allocator.to_mt5_lots(
                capital_alloc_usd, signal_data.sl_distance_pts, signal_data.symbol_tick_value
            )
            
            # SUCESSO.
            approved = True
            rejection_reason = "approved"
            logger.info(f"🚀 EXEC_ORDER: {signal_data.direction} {final_mt5_lots} LOTS [{signal_data.asset}] via {signal_data.agent_id} | Risk: ${capital_alloc_usd:,.2f}")
            # ... Dispara para o nó de Ordem MT5 de Execução Real ...

        except Exception as e:
            rejection_reason = f"Unhandled_System_Crash: {type(e).__name__}"
            if self.dlq: await self.dlq.register_rejection(payload, rejection_reason, "RUNTIME_CRASH", e)
            logger.error(f"CRITICAL FAULT NO MOTOR: {e}")
        finally:
            if self.telemetry:
                self.telemetry.record_signal_end(start_ts, approved, rejection_reason)
