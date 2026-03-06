import unittest
import numpy as np
import logging
from modules.fractal_hurst import FractalEngineV2, MarketRegime

# Suprimir logs durante os testes
logging.getLogger("FractalEngineTier0").setLevel(logging.CRITICAL)

class TestFractalHurst(unittest.TestCase):
    def setUp(self):
        self.engine = FractalEngineV2()
        # Seed para consistência nos testes
        np.random.seed(42)

    def test_trending_market(self):
        # Série com retornos autocorrelacionados positivamente (Persistência, H > 0.5)
        raw_noise = np.random.normal(0, 1, 300)
        persistent_steps = np.convolve(raw_noise, np.ones(20)/20, mode='valid')
        trend_prices = 100 + np.cumsum(persistent_steps)
        
        state = self.engine.analyze_series(trend_prices)
        
        # Pode ser TRENDING ou WEAK_TRENDING, mas H > 0.55
        self.assertGreater(state.hurst_exponent, 0.55)
        self.assertIn(state.regime, [MarketRegime.TRENDING, MarketRegime.WEAK_TRENDING])
        self.assertFalse(state.is_pullback_friendly)

    def test_mean_reverting_market(self):
        # A nova engine V2 (Tier-0) primeiro deriva log-returns dos preços passados para achar o Hurst. 
        # Portanto, para criar antipersistência, o ruído tem de ser injetado nos "retornos", 
        # mas gerando um oscilador AR(1) com um phi negativo forte nos próprios retornos.
        np.random.seed(42)
        noise = np.random.normal(0, 1, 1000)
        returns = np.zeros(1000)
        for i in range(1, 1000):
            returns[i] = -0.7 * returns[i-1] + noise[i]
        
        # Converte de volta para uma série de preços cumulativa 
        mean_rev_prices = 100 * np.exp(np.cumsum(returns / 100))
        
        state = self.engine.analyze_series(mean_rev_prices)
        
        self.assertLess(state.hurst_exponent, 0.45)

    def test_random_walk_market(self):
        # Série puramente aleatória (Ruído branco, H ~ 0.5)
        # Semente fixa para garantir estabilidade no range de Random Walk (~0.5)
        np.random.seed(42)
        random_steps = np.random.normal(0, 1, 1000)
        random_walk_prices = 100 + np.cumsum(random_steps)
        
        state = self.engine.analyze_series(random_walk_prices)
        
        # O Random Walk puro aproxima-se de H = 0.5, mas pode oscilar.
        self.assertGreaterEqual(state.hurst_exponent, 0.4)
        self.assertLessEqual(state.hurst_exponent, 0.6)
        self.assertIn(state.regime, [MarketRegime.RANDOM_WALK, MarketRegime.WEAK_TRENDING, MarketRegime.WEAK_MEAN_REVERTING])
        self.assertFalse(state.is_pullback_friendly)
        
    def test_insufficient_data(self):
        short_series = np.array([1, 2, 3, 4, 5])
        state = self.engine.analyze_series(short_series)
        self.assertEqual(state.regime, MarketRegime.UNKNOWN)

if __name__ == '__main__':
    unittest.main()
