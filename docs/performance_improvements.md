# Performance Improvements

This document tracks significant performance optimizations applied to the S.A.K.A. codebase.

## [2025-01-11] Cronos Agent: RSI Calculation Optimization

### 💡 What
Optimized the `calculate_manual_rsi` function in the `cronos_cycles` agent (`saka/agents/cronos_cycles/main.py`) by implementing dynamic data truncation.

The input price history is now truncated to a maximum length calculated as `max(500, period * 35)` before processing.

### 🎯 Why
The original implementation calculated the RSI using `pandas` on the entire provided history. As the system runs for longer periods, the history size in `AnalysisRequest` grows, leading to $O(N)$ performance degradation.
- **Problem:** Calculating RSI for 10,000 points took ~5ms, which scales linearly.
- **Constraint:** RSI uses an Exponential Moving Average (EMA), where older data points technically affect the result but their weight decays exponentially.
- **Solution:** Truncating the history to a sufficient window (e.g., 35x the period) ensures the error is below machine precision ($< 10^{-16}$) while capping the calculation time.

### 📊 Impact
The optimization converts the calculation from $O(N)$ to effectively $O(1)$ relative to the total history size.

**Benchmark Results (10,000 data points):**
- **Before:** ~4.91 ms per call
- **After:** ~1.75 ms per call
- **Improvement:** ~64% faster for this dataset size (and constant time for larger datasets).
- **Precision Loss:** 0.0 (below float precision).

### 🔬 Measurement
To verify this optimization, a benchmark script can be used:

```python
import time
import numpy as np
from saka.agents.cronos_cycles.main import calculate_manual_rsi

def benchmark():
    # Generate large history
    np.random.seed(42)
    prices = [100.0]
    for _ in range(10000):
        change = np.random.normal(0, 1)
        prices.append(prices[-1] + change)

    # Measure time
    start_time = time.time()
    for _ in range(100):
        calculate_manual_rsi(prices)
    end_time = time.time()

    print(f"Time per call: {(end_time - start_time) / 100 * 1000:.4f} ms")

if __name__ == "__main__":
    benchmark()
```
