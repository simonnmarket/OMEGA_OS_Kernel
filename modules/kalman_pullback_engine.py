import numpy as np
from omega_integration_gate import OmegaBaseAgent, RiskParameters

class OmegaKalmanPullbackEngine(OmegaBaseAgent):
    """
    Advanced State-Space Engine for Pullback Detection (O.I.G V3.0)
    Integrates Kalman Filtering with Volume-Weighted Liquidity Density.
    Replaces heuristic pullback models with High-Frequency Stochastic Control.
    """
    def __init__(self, dt=1.0, process_noise=0.1, measurement_noise=1.0):
        super().__init__()
        self.dt = dt
        self.A = np.array([[1, dt, 0.5*dt**2],
                           [0, 1, dt],
                           [0, 0, 1]], dtype=float)
        self.H = np.array([[1, 0, 0]], dtype=float)
        self.Q = np.eye(3, dtype=float) * process_noise
        self.R = np.array([[measurement_noise]], dtype=float)
        self.P = np.eye(3, dtype=float)
        self.x = np.zeros((3, 1), dtype=float)
        
        # Bayesian Liquidity Memory: {price_bin: cumulative_energy}
        self.liquidity_nodes = {}
        
        self.last_price = None

    def _hash_core_logic(self) -> str:
        return "KALMAN_STOCHASTIC_STATE_SPACE_V1_0"

    def get_risk_parameters(self) -> RiskParameters:
        return RiskParameters(
            max_drawdown_limit=0.05,
            latency_tolerance_ms=10.0,
            required_confidence=0.85
        )
        
    def force_halt(self) -> bool:
        """Emergency stop if state vector diverges."""
        return np.max(np.abs(self.x)) > 1e6

    def _update_liquidity_density(self, price, volume, aggression_delta):
        """Calculates the Action Functional of the Institutional Footprint."""
        # Bin size for XAUUSD (e.g., nearest $1.0)
        price_bin = round(price, 0)
        # Energy = Volume * Delta (Directional Force)
        energy = volume * np.abs(aggression_delta) if aggression_delta != 0 else volume * 0.5
        self.liquidity_nodes[price_bin] = self.liquidity_nodes.get(price_bin, 0.0) + float(energy)

    def _filter_state(self, measured_price):
        """Kalman Prediction/Correction Cycle."""
        # Predict
        self.x = np.dot(self.A, self.x)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q
        
        # Update
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R
        S_inv = np.linalg.inv(S)
        K = np.dot(np.dot(self.P, self.H.T), S_inv)
        y = measured_price - np.dot(self.H, self.x) # Innovation (Surprise)
        self.x = self.x + np.dot(K, y)
        self.P = self.P - np.dot(np.dot(K, self.H), self.P)
        
        return float(self.x[0,0]), float(self.x[1,0]), float(y[0,0])

    def execute(self, window_data: np.ndarray, context: dict = None) -> dict:
        """
        window_data: OHLCV array.
        Returns the probability of a Pullback Reversal (P_rev) at the current candle.
        """
        current_close = float(window_data[-1, 3])
        current_vol = float(window_data[-1, 4]) # Vol is index 4 in our [O, H, L, C, V] array
        
        
        # Calculate recent delta for liquidity energy update
        if self.last_price is None:
            delta = 0.0
        else:
            delta = current_close - self.last_price
        self.last_price = current_close
            
        self._update_liquidity_density(current_close, current_vol, delta)
        
        est_price, velocity, innovation = self._filter_state(current_close)
        
        # 1. Identify Order Flow Exhaustion (OFE)
        # Pullback requirement: Velocity approaches zero, Innovation is minimal (No surprise)
        # If market is trending up linearly, innovation is 0. If it snaps back, innovation spikes.
        ofe_index = 1.0 / (1.0 + np.abs(velocity) + np.abs(innovation))
        
        # 2. Map Price to Liquidity Node (The 'Muralha')
        price_bin = round(current_close, 0)
        node_energy = self.liquidity_nodes.get(price_bin, 0)
        max_energy = max(self.liquidity_nodes.values()) if self.liquidity_nodes else 1.0
        liquidity_score = node_energy / max_energy
        
        # 3. Pullback Confidence Score (Bayesian Posterior)
        # High score if: OFE is high AND Liquidity Score is high AND Velocity is Decelerating
        pullback_confidence = ofe_index * liquidity_score * 0.5
        
        # Also determine if innovation is massive (structural break)
        structural_break = np.abs(innovation) > (np.abs(velocity) * 8.0) and np.abs(innovation) > 1.5
        
        return {
            "est_price": est_price,
            "velocity": velocity,
            "innovation": innovation,
            "liquidity_score": liquidity_score,
            "pullback_confidence": pullback_confidence,
            "is_structural_break": structural_break,
            "is_kalman_pullback": pullback_confidence > 0.01 and not structural_break
        }
