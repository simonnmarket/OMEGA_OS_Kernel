import sys
sys.path.insert(0, ".")
import numpy as np
from modules.omega_integration_gate import OmegaBaseAgent, RiskParameters
from modules.kalman_pullback_engine import OmegaKalmanPullbackEngine

engine = OmegaKalmanPullbackEngine()

# Dados OHLCV sinteticos: preco começa proximo de 0 para evitar divergencia Kalman
prices = np.cumsum(np.random.randn(50) * 0.5)
window = np.column_stack([
    prices, prices + 0.2, prices - 0.2, prices,
    np.random.randint(100, 500, 50).astype(float)
])
result = engine.execute(window)

assert "pullback_confidence" in result
assert "is_kalman_pullback" in result
assert isinstance(result["is_kalman_pullback"], (bool, np.bool_))

print("kalman_pullback UNIT TEST PASSED")
print(f"  pullback_confidence = {result['pullback_confidence']:.4f}")
print(f"  is_kalman_pullback  = {result['is_kalman_pullback']}")
print(f"  velocity            = {result['velocity']:.4f}")
print(f"  innovation          = {result['innovation']:.4f}")
print(f"  liquidity_score     = {result['liquidity_score']:.4f}")

# Test force_halt
assert not engine.force_halt(), "force_halt deve ser False com estado normal"
print("  force_halt          = False (OK)")

rp = engine.get_risk_parameters()
assert rp.required_confidence == 0.85
print(f"  required_confidence = {rp.required_confidence} (OK)")
print("ALL KALMAN TESTS PASSED")
