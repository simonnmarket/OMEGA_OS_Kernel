import numpy as np
import pandas as pd
from scipy import stats

def hfd_test(series):
    n = len(series)
    k_max = 6
    lk = []
    for k in range(1, k_max + 1):
        lm = []
        for m in range(k):
            idx = np.arange(m, n, k)
            if len(idx) < 2: continue
            norm = (n - 1) / (int((n - 1 - m) / k) * k)
            l_m = np.sum(np.abs(np.diff(series[idx]))) * norm / k
            lm.append(l_m)
        if lm: lk.append(np.mean(lm))
    
    # log(1/k)
    x = np.log(1.0 / np.arange(1, len(lk) + 1))
    y = np.log(lk)
    slope, _, r2, _, _ = stats.linregress(x, y)
    return slope, 2.0 + slope # Testing the user's formula
    
rw = np.cumsum(np.random.normal(0, 1, 100))
s, h = hfd_test(rw)
print(f"RW Slope (log 1/k): {s:.4f} | Formula 2+s: {h:.4f}")

# Standard Higuchi D for RW is ~1.5.
# If slope is D, then D=1.5.
# If HFD = 2 + slope, then 2 + 1.5 = 3.5. WRONG.
# If HFD = 2 + slope and slope is negative... 
# Let's see what slope we get with log(1/k).
