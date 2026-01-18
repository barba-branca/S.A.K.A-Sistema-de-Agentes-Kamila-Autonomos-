import time
import numpy as np
import sys
import os

# Ensure we can import from saka
sys.path.append(os.getcwd())

from saka.agents.sentinel_risk.main import calculate_risk_metrics

def benchmark_sentinel():
    # Setup
    sizes = [1000, 5000, 10000, 50000, 100000]

    print(f"Benchmarking Sentinel Risk Calculation")
    print("-" * 60)
    print(f"{'Size':<10} | {'Avg Time (ms)':<15}")
    print("-" * 60)

    for size in sizes:
        # Generate random walk
        prices = [100.0]
        for _ in range(size - 1):
            prices.append(prices[-1] * (1 + np.random.uniform(-0.01, 0.01)))

        # Measure
        start_time = time.time()
        iterations = 50
        for _ in range(iterations):
            calculate_risk_metrics(prices)
        end_time = time.time()
        avg_ms = (end_time - start_time) / iterations * 1000

        print(f"{size:<10} | {avg_ms:<15.4f}")

if __name__ == "__main__":
    benchmark_sentinel()
