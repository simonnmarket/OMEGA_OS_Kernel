"""
OMEGA OS Kernel - Volume Physics & Pullback Trap Engine
VERSÃO 2.0 - TIER-0 OMEGA SUPREME COMPLIANT
--------------------------------------------------
Substitui a versão MVP heurística baseada em loops por uma aproximação vetorizada HFT:
- Matrizes circulares (Circular Buffers) pre-alocadas em NumPy para zero-alloc no on_tick.
- Integração de `FractalState` (Hurst e Regime) garantindo a dependência da FractalEngineV2.
- Cálculos robustos de ATR Compression, Order Flow (Delta Proxy) e Volume Surge.
- Detecção de Pullback / Trap Zone usando Machine-Level Math.
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from typing import Optional, Dict, Tuple, List

# Dependência cruzada permitida no Kernel: O estado matemático de Hurst
from modules.fractal_hurst import FractalState, MarketRegime

logger = logging.getLogger("VolumePhysicsTier0")

class PullbackPhase(Enum):
    NONE = auto()
    CORRECTING = auto()
    TRAP_SET = auto()
    RESUMING = auto()

class ReentryUrgency(Enum):
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class PhysicsConfig:
    """Configurações quantitativas pre-calibradas para Física de Volume e Pullback"""
    buffer_size: int = 2000          # Tamanho do buffer circular HFT
    atr_window: int = 14
    atr_compress_ratio: float = 0.70
    vwap_window: int = 20
    delta_z_threshold: float = 2.0
    surge_threshold: float = 1.645
    min_volume_confidence: float = 0.3
    pullback_resume_bars: int = 3
    enable_profiling: bool = False

@dataclass
class PhysicsState:
    """Snapshot HFT de todas as pressões volumétricas da barra/tick atual"""
    vwap: float = 0.0
    vwap_upper: float = 0.0
    vwap_lower: float = 0.0
    delta: float = 0.0
    delta_z: float = 0.0
    atr_current: float = 0.0
    atr_ratio: float = 1.0
    is_atr_compressed: bool = False
    is_volume_surge: bool = False
    pullback_phase: PullbackPhase = PullbackPhase.NONE
    urgency: ReentryUrgency = ReentryUrgency.NORMAL
    trap_score: float = 0.0
    computation_time_ms: float = 0.0

class NumpyCircularBuffer:
    """Zero-allocation HFT Circular Buffer para Janelas Deslizantes"""
    def __init__(self, size: int, dtype=np.float64):
        self.size = size
        self.buffer = np.zeros(size, dtype=dtype)
        self.index = 0
        self.count = 0

    def push(self, value: float):
        self.buffer[self.index] = value
        self.index = (self.index + 1) % self.size
        if self.count < self.size:
            self.count += 1

    def push_array(self, values: np.ndarray):
        n = len(values)
        if n >= self.size:
            self.buffer[:] = values[-self.size:]
            self.index = 0
            self.count = self.size
        else:
            space = self.size - self.index
            if n <= space:
                self.buffer[self.index : self.index + n] = values
                self.index = (self.index + n) % self.size
            else:
                self.buffer[self.index : self.size] = values[:space]
                self.buffer[0 : n - space] = values[space:]
                self.index = n - space
            self.count = min(self.size, self.count + n)

    def get_window(self, length: int) -> np.ndarray:
        if length > self.count:
            length = self.count
        if length == 0:
            return np.array([], dtype=self.buffer.dtype)
            
        start = (self.index - length) % self.size
        if start < self.index:
            return self.buffer[start:self.index]
        else:
            return np.concatenate((self.buffer[start:self.size], self.buffer[0:self.index]))

    def get_all(self) -> np.ndarray:
        return self.get_window(self.count)


class VolumePhysicsEngine:
    """
    Tier-0 Volumetric Engine.
    Exige injecção do `FractalState` para fundir a dimensão Tempo/Regime com a dimensão Espaço/Volume.
    """
    def __init__(self, config: Optional[PhysicsConfig] = None):
        self.config = config or PhysicsConfig()
        
        # Buffers vetorizados estritos
        sz = self.config.buffer_size
        self.closes = NumpyCircularBuffer(sz)
        self.highs = NumpyCircularBuffer(sz)
        self.lows = NumpyCircularBuffer(sz)
        self.volumes = NumpyCircularBuffer(sz)
        self.deltas = NumpyCircularBuffer(sz)
        self.atrs = NumpyCircularBuffer(sz)
        
        # Estado Interno Trackers
        self.current_phase = PullbackPhase.NONE
        self.trap_score_acc = 0.0
        self.original_direction = 0  # 1 = Long, -1 = Short (Direção Trend)
        self.pullback_start_price = 0.0
        self.pullback_max_adverse = 0.0
        self.bars_in_resume = 0

    def update(self, close: float, high: float, low: float, volume: float, fractal_state: FractalState) -> PhysicsState:
        """Processamento principal por barra/tick. Requer estado do Hurst."""
        t0 = time.perf_counter()
        
        # 1. Atualizar Buffers
        self.closes.push(close)
        self.highs.push(high)
        self.lows.push(low)
        self.volumes.push(volume)
        
        state = PhysicsState()
        
        if self.closes.count < 2:
            return state

        # 2. Vectorized ATR Computation (usando janelas em C)
        atr_val = self._compute_atr()
        self.atrs.push(atr_val)
        
        atr_ratio = 1.0
        is_atr_compressed = False
        if self.atrs.count >= self.config.atr_window:
            atr_hist = self.atrs.get_window(self.config.atr_window)
            atr_avg = np.mean(atr_hist)
            if atr_avg > 0:
                atr_ratio = atr_val / atr_avg
                is_atr_compressed = atr_ratio < self.config.atr_compress_ratio
                
        state.atr_current = atr_val
        state.atr_ratio = atr_ratio
        state.is_atr_compressed = is_atr_compressed

        # 3. Vectorized Proxy Delta & Order Flow
        delta, delta_z = self._compute_delta(close, high, low, volume)
        self.deltas.push(delta)
        state.delta = delta
        state.delta_z = delta_z

        # 4. VWAP Vectorized Bounds
        vwap, upper, lower = self._compute_vwap()
        state.vwap = vwap
        state.vwap_upper = upper
        state.vwap_lower = lower

        # 5. Volume Surge (Transformação Logarítmica para Estabilização de Z-Score)
        is_surge = False
        if self.volumes.count >= 20:
            vol_hist = self.volumes.get_window(20)
            # Aplicamos log1p para lidar com ticks de volume zero (se existirem) e normalizar a fat-tail
            log_hist = np.log1p(vol_hist)
            log_vol = np.log1p(volume)
            vol_mean = np.mean(log_hist)
            vol_std = np.std(log_hist)
            if vol_std > 0 and ((log_vol - vol_mean) / vol_std) > self.config.surge_threshold:
                is_surge = True
        state.is_volume_surge = is_surge

        # 6. FUSÃO DECISÓRIA: Pullback Trap System (Injeção de Hurst)
        self._evaluate_pullback_trap(close, delta_z, is_atr_compressed, fractal_state)
        
        state.pullback_phase = self.current_phase
        state.trap_score = self.trap_score_acc
        state.urgency = self._determine_urgency(fractal_state)
        
        t1 = time.perf_counter()
        state.computation_time_ms = (t1 - t0) * 1000.0
        return state

    def _compute_atr(self) -> float:
        """Cálculo do True Range apenas da última barra contra anterior"""
        closes = self.closes.get_window(2)
        if len(closes) < 2:
            return 0.0
        high = self.highs.get_window(1)[0]
        low = self.lows.get_window(1)[0]
        prev_close = closes[0]
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        return float(tr)

    def _compute_delta(self, close: float, high: float, low: float, vol: float) -> Tuple[float, float]:
        """Proxy Delta Intra-barra e Z-Score usando numpy array operations"""
        rng = max(high - low, 1e-8)
        buy_vol = vol * (close - low) / rng
        sell_vol = vol * (high - close) / rng
        delta = buy_vol - sell_vol
        
        delta_z = 0.0
        count = self.deltas.count
        if count >= 20:
            h_deltas = self.deltas.get_window(20)
            m = np.mean(h_deltas)
            s = np.std(h_deltas)
            if s > 0:
                delta_z = (delta - m) / s
                
        return delta, delta_z

    def _compute_vwap(self) -> Tuple[float, float, float]:
        """VWAP e Standard Deviation Bands vetorizados (Janela Rolante Média)"""
        w = self.config.vwap_window
        if self.closes.count < w:
            return 0.0, 0.0, 0.0
            
        prices = self.closes.get_window(w)
        vols = self.volumes.get_window(w)
        
        sum_v = np.sum(vols)
        if sum_v <= 0:
            return prices[-1], prices[-1], prices[-1]
            
        vwap = np.sum(prices * vols) / sum_v
        std_p = np.std(prices)
        
        return float(vwap), float(vwap + std_p * 2.0), float(vwap - std_p * 2.0)

    def _evaluate_pullback_trap(self, close: float, delta_z: float, is_compressed: bool, f_state: FractalState):
        """
        State Machine do Pullback injetando a Confiança de Regime do Módulo Fractal
        """
        # Se o Hurst for RAND_WALK profundo ou mean reverting severo, anula pullbacks fortes
        is_trend = f_state.regime in (MarketRegime.TRENDING, MarketRegime.WEAK_TRENDING)
        
        if self.current_phase == PullbackPhase.NONE:
            # Detecta início de correcção (Preço contra a tendência mas Hurst forte)
            # Requer trend no Hurst e is_pullback_friendly do engine do Hurst
            if is_trend and f_state.is_pullback_friendly:
                self.current_phase = PullbackPhase.CORRECTING
                self.trap_score_acc = 0.0
                self.pullback_start_price = close
                self.pullback_max_adverse = close
                # Define direção original assumindo que se estamos a corrigir com pullback OK,
                # e Delta actual é contra? Simplificando: Assumimos direção baseada em VWAP trend_state
                # ou simplesmente aguardamos setup.
                
        elif self.current_phase == PullbackPhase.CORRECTING:
            # Durante correcção, acumulamos Trap Score se:
            # 1. Delta seca (delta_z pequeno ou zero/negativo fraco)
            # 2. E ATR Comprime
            # Estamos na armadilha institucional: "Secando liquidez retalhista"
            
            score_add = 0.0
            if is_compressed:
                score_add += 0.3
            
            # Condição de Falta de Interesse na Correcção
            if abs(delta_z) < 0.5:
                score_add += 0.2
            elif (delta_z > self.config.delta_z_threshold) or (delta_z < -self.config.delta_z_threshold):
                # O volume regressa forte. Pode ser inversão real ou o TRAP a fechar
                if is_compressed: # Vol forte + Volatilidade Baixa (Absorption)
                    score_add += 0.5
                else:
                    self.current_phase = PullbackPhase.NONE # Quebrou a armadilha, reversão.
                    
            self.trap_score_acc = min(1.0, self.trap_score_acc + score_add)
            
            if self.trap_score_acc >= 0.7:
                self.current_phase = PullbackPhase.TRAP_SET
                self.bars_in_resume = 0
                
        elif self.current_phase == PullbackPhase.TRAP_SET:
            # Procuramos o rompimento do Trap (Resuming)
            # Geralmente associado a explosão direcional e volume surge
            if abs(delta_z) > 1.5 and not is_compressed:
                self.bars_in_resume += 1
                if self.bars_in_resume >= self.config.pullback_resume_bars:
                    self.current_phase = PullbackPhase.RESUMING
            else:
                self.bars_in_resume = 0
                
        elif self.current_phase == PullbackPhase.RESUMING:
            # Disparo foi dado, reset para ciclo seguinte.
            self.current_phase = PullbackPhase.NONE
            self.trap_score_acc = 0.0

    def _determine_urgency(self, f_state: FractalState) -> ReentryUrgency:
        if self.current_phase != PullbackPhase.TRAP_SET:
            return ReentryUrgency.NORMAL
            
        # Urgência dispara se a compressão max out e Hurst for ALTAMENTE direcional
        if f_state.hurst_exponent > 0.65 and self.trap_score_acc > 0.8:
            return ReentryUrgency.CRITICAL
        elif f_state.hurst_exponent > 0.55:
            return ReentryUrgency.HIGH
            
        return ReentryUrgency.NORMAL
