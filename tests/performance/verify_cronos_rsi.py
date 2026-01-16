import time
import pandas as pd
import numpy as np
import sys
import os

# Ensure we can import from saka
sys.path.append(os.getcwd())

from saka.agents.cronos_cycles.main import calculate_manual_rsi

def benchmark_rsi():
    # Setup
    period = 14
    truncation_limit = max(500, period * 35) # 500

    # Generate large dataset
    sizes = [1000, 5000, 10000, 50000]

    print(f"Benchmarking RSI calculation (Period: {period})")
    print("-" * 80)
    print(f"{'Size':<10} | {'Full Time (ms)':<15} | {'Trunc Time (ms)':<15} | {'RSI Diff':<10}")
    print("-" * 80)

    for size in sizes:
        # Generate random walk to be more realistic than uniform noise
        prices = [100.0]
        for _ in range(size - 1):
            prices.append(prices[-1] * (1 + np.random.uniform(-0.01, 0.01)))

        # Measure Full
        start_time = time.time()
        iterations = 20
        for _ in range(iterations):
            rsi_full = calculate_manual_rsi(prices, period)
        end_time = time.time()
        full_avg_ms = (end_time - start_time) / iterations * 1000

        # Measure Truncated (Simulated optimization)
        # We slice before calling the function to simulate the overhead reduction
        # The overhead of slicing is negligible compared to pandas operations
        start_time = time.time()
        for _ in range(iterations):
            truncated_prices = prices[-truncation_limit:] if len(prices) > truncation_limit else prices
            rsi_trunc = calculate_manual_rsi(truncated_prices, period)
        end_time = time.time()
        trunc_avg_ms = (end_time - start_time) / iterations * 1000

        # Calculate difference in RSI result
        rsi_full_val = calculate_manual_rsi(prices, period)
        truncated_prices_val = prices[-truncation_limit:] if len(prices) > truncation_limit else prices
        rsi_trunc_val = calculate_manual_rsi(truncated_prices_val, period)
        diff = abs(rsi_full_val - rsi_trunc_val)

        print(f"{size:<10} | {full_avg_ms:<15.4f} | {trunc_avg_ms:<15.4f} | {diff:.8f}")

if __name__ == "__main__":
    benchmark_rsi()
