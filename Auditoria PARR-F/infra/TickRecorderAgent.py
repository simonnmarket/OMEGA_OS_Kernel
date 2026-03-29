"""
TickRecorderAgent — OMEGA Infrastructure Layer (V8.2 FOUNDATION)
Refatoração MACE-MAX | CFO Audit-1.0 Compliance
"""

import asyncio
import time
import logging
import struct
from datetime import datetime, timezone, timedelta
from typing import Optional
import MetaTrader5 as mt5
import redis.asyncio as aioredis
import asyncpg
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor

# ─── CONSTANTES ────────────────────────────────────────────────────────────────
REDIS_STREAM_KEY   = "omega:ticks:raw"
REDIS_MAX_LEN      = 50_000          # ~50MB RAM máximo
BATCH_SIZE         = 10_000          # MODIFICADO-CFO: Aumentado para tolerância NFP Volatility
BATCH_INTERVAL_S   = 3.0             
NTP_DRIFT_MAX_MS   = 50              
SYMBOLS            = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
HEARTBEAT_KEY      = "omega:agent:heartbeat"
CURSOR_FILE        = "cursor_last_id.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
log = logging.getLogger("TickRecorderAgent")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ticks (
    id              BIGSERIAL    PRIMARY KEY,
    symbol          VARCHAR(12)  NOT NULL,
    server_time_utc TIMESTAMPTZ  NOT NULL,
    local_time_utc  TIMESTAMPTZ  NOT NULL,
    latency_ms      SMALLINT     NOT NULL,
    bid             NUMERIC(12,5) NOT NULL,
    ask             NUMERIC(12,5) NOT NULL,
    spread_pts      SMALLINT     NOT NULL,
    last            NUMERIC(12,5),
    volume          INTEGER,
    volume_real     NUMERIC(14,2),
    flags           SMALLINT,
    bid_low         NUMERIC(12,5),
    bid_high        NUMERIC(12,5),
    ask_low         NUMERIC(12,5),
    ask_high        NUMERIC(12,5),
    last_low        NUMERIC(12,5),
    last_high       NUMERIC(12,5),
    session         VARCHAR(8),   
    is_synthetic    BOOLEAN DEFAULT FALSE
) PARTITION BY RANGE (server_time_utc);
"""

INSERT_SQL = """
INSERT INTO ticks (
    symbol, server_time_utc, local_time_utc, latency_ms,
    bid, ask, spread_pts, last, volume, volume_real, flags,
    bid_low, bid_high, ask_low, ask_high, last_low, last_high,
    session, is_synthetic
) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
"""

def _session(dt: datetime) -> str:
    h = dt.hour
    if 7 <= h < 16:  return "LONDON"
    if 13 <= h < 22: return "NY"
    if 0 <= h < 7:   return "ASIA"
    return "OFF"

def _spread_pts(bid: float, ask: float, symbol: str) -> int:
    multiplier = 100 if "XAU" in symbol else 100000
    return round((ask - bid) * multiplier)

class TickRecorderAgent:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis_url  = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._running    = False
        self._tick_count = 0
        self._err_count  = 0

    async def _connect_redis(self):
        self._redis = await aioredis.from_url(
            self._redis_url,
            socket_connect_timeout=3,
            socket_keepalive=True,
            health_check_interval=30,
        )
        await self._redis.ping()
        log.info("Redis conectado.")

    def _connect_mt5(self) -> bool:
        if not mt5.initialize():
            log.error(f"MT5 init falhou: {mt5.last_error()}")
            return False
        for s in SYMBOLS:
            mt5.symbol_select(s, True)
        log.info(f"MT5 conectado: {mt5.terminal_info().name}")
        return True

    async def _heartbeat(self):
        """MODIFICADO-CFO: Watchdog Heartbeat. Escreve vivo a cada 5 seg."""
        while self._running:
            await self._redis.set(HEARTBEAT_KEY, datetime.now(timezone.utc).isoformat(), ex=15)
            await asyncio.sleep(5)

    async def _capture_symbol(self, symbol: str):
        prev_time = 0
        loop = asyncio.get_running_loop()
        # Thread pool reservado para I/O bloquante da DLL MT5
        with ThreadPoolExecutor(max_workers=len(SYMBOLS)) as pool:
            while self._running:
                # MODIFICADO-CFO: MT5 DLL request runs in executor para evitar latência no Event Loop
                tick = await loop.run_in_executor(pool, mt5.symbol_info_tick, symbol)
                if tick is None:
                    self._err_count += 1
                    await asyncio.sleep(0.01)
                    continue

                if tick.time_msc == prev_time:
                    await asyncio.sleep(0.001)
                    continue
                prev_time = tick.time_msc

                local_ts  = datetime.now(timezone.utc)
                server_ts = datetime.fromtimestamp(tick.time_msc / 1000, tz=timezone.utc)
                latency   = int((local_ts.timestamp() - server_ts.timestamp()) * 1000)

                if abs(latency) > NTP_DRIFT_MAX_MS * 10:
                    log.warning(f"Clock drift detectado: {latency}ms — tick rejeitado")
                    continue

                payload = {
                    "sym":  symbol,
                    "st":   server_ts.isoformat(),
                    "lt":   local_ts.isoformat(),
                    "lat":  str(latency),
                    "bid":  str(tick.bid),
                    "ask":  str(tick.ask),
                    "sp":   str(_spread_pts(tick.bid, tick.ask, symbol)),
                    "last": str(tick.last),
                    "vol":  str(tick.volume),
                    "volr": str(tick.volume_real),
                    "fl":   str(tick.flags),
                    "blo":  str(tick.bid_low),
                    "bhi":  str(tick.bid_high),
                    "alo":  str(tick.ask_low),
                    "ahi":  str(tick.ask_high),
                    "llo":  str(tick.last_low),
                    "lhi":  str(tick.last_high),
                    "sess": _session(server_ts),
                }

                await self._redis.xadd(
                    REDIS_STREAM_KEY,
                    payload,
                    maxlen=REDIS_MAX_LEN,
                    approximate=True,
                )
                self._tick_count += 1

                if self._tick_count % 10_000 == 0:
                    log.info(f"[{symbol}] {self._tick_count} ticks | erros: {self._err_count}")

                await asyncio.sleep(0)  

    async def run(self):
        await self._connect_redis()
        if not self._connect_mt5():
            raise RuntimeError("MT5 indisponível.")
        self._running = True
        tasks = [asyncio.create_task(self._capture_symbol(s)) for s in SYMBOLS]
        tasks.append(asyncio.create_task(self._heartbeat()))
        log.info(f"TickRecorderAgent ativo: {SYMBOLS}")
        await asyncio.gather(*tasks)

    async def stop(self):
        self._running = False
        mt5.shutdown()
        if self._redis:
            await self._redis.aclose()


# ─── BATCH WORKER (PROCESSANDO TUDO SEM DUPLICADAS) ───────────────────────────────────
class TickBatchWorker:
    def __init__(self, redis_url: str, pg_dsn: str):
        self._redis_url = redis_url
        self._pg_dsn    = pg_dsn
        self._last_id   = "0"
        self._redis: Optional[aioredis.Redis] = None
        self._pg: Optional[asyncpg.Pool] = None
        self._load_cursor() # MODIFICADO-CFO: Persistência de Buffer (anti-repetição)

    def _load_cursor(self):
        if os.path.exists(CURSOR_FILE):
            with open(CURSOR_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    self._last_id = content
                    log.info(f"Cursor recuperado do disco: {self._last_id}")

    def _save_cursor(self):
        with open(CURSOR_FILE, "w") as f:
            f.write(str(self._last_id))

    async def _connect_and_partition(self):
        self._redis = await aioredis.from_url(self._redis_url)
        self._pg    = await asyncpg.create_pool(self._pg_dsn, min_size=2, max_size=4)
        async with self._pg.acquire() as conn:
            await conn.execute(CREATE_TABLE_SQL)
            
            # MODIFICADO-CFO: Criação automática de partições (Anti table-bloat de 30 dias)
            today = datetime.now(timezone.utc).strftime("%Y_%m_%d")
            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
            today_bound = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            part_sql = f"""
            CREATE TABLE IF NOT EXISTS ticks_{today} 
            PARTITION OF ticks FOR VALUES FROM ('{today_bound}') TO ('{tomorrow}');
            """
            await conn.execute(part_sql)
            
        log.info("BatchWorker conectado e particionamento diário OK.")

    def _parse_row(self, msg_id: str, fields: dict) -> tuple:
        f = fields
        return (
            f[b"sym"].decode(),
            datetime.fromisoformat(f[b"st"].decode()),
            datetime.fromisoformat(f[b"lt"].decode()),
            int(f[b"lat"]),
            float(f[b"bid"]),
            float(f[b"ask"]),
            int(f[b"sp"]),
            float(f[b"last"]) if f[b"last"] != b"0.0" else None,
            int(f[b"vol"]),
            float(f[b"volr"]),
            int(f[b"fl"]),
            float(f[b"blo"]) if f[b"blo"] != b"0.0" else None,
            float(f[b"bhi"]) if f[b"bhi"] != b"0.0" else None,
            float(f[b"alo"]) if f[b"alo"] != b"0.0" else None,
            float(f[b"ahi"]) if f[b"ahi"] != b"0.0" else None,
            float(f[b"llo"]) if f[b"llo"] != b"0.0" else None,
            float(f[b"lhi"]) if f[b"lhi"] != b"0.0" else None,
            f[b"sess"].decode(),
            False,
        )

    async def _flush(self):
        messages = await self._redis.xread(
            {REDIS_STREAM_KEY: self._last_id},
            count=BATCH_SIZE, # MODIFICADO-CFO: 10.000 tolerância NFP
            block=0,
        )
        if not messages:
            return

        _, entries = messages[0]
        if not entries:
            return

        rows = []
        for msg_id, fields in entries:
            try:
                rows.append(self._parse_row(msg_id, fields))
            except Exception as e:
                log.warning(f"Parse error em {msg_id}: {e}")

        if rows:
            async with self._pg.acquire() as conn:
                await conn.executemany(INSERT_SQL, rows)

            self._last_id = entries[-1][0].decode()
            self._save_cursor() # MODIFICADO-CFO: Salvar id por sync flush
            log.info(f"Flush: {len(rows)} ticks → PostgreSQL | cursor: {self._last_id}")

    async def run(self):
        await self._connect_and_partition()
        log.info("BatchWorker ativo.")
        while True:
            try:
                await self._flush()
            except Exception as e:
                log.error(f"Flush error: {e}")
            await asyncio.sleep(BATCH_INTERVAL_S)

if __name__ == "__main__":
    print("V8.2 Infrastructure Node OMEGA. Use import.")
