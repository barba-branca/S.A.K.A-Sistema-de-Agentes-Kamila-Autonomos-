import time
import random
import sys
import os

# Ensure saka module is in path
sys.path.append(os.getcwd())

from saka.agents.cronos_cycles.main import calculate_manual_rsi

def generate_prices(n):
    return [random.uniform(100, 200) for _ in range(n)]

def test_rsi_performance():
    sizes = [1000, 5000, 10000, 50000, 100000]
    print(f"{'Size':<10} | {'Time (s)':<10} | {'RSI Value':<10}")
    print("-" * 35)

    for n in sizes:
        prices = generate_prices(n)
        start_time = time.time()
        rsi = calculate_manual_rsi(prices)
        end_time = time.time()
        print(f"{n:<10} | {end_time - start_time:<10.6f} | {rsi:.2f}")

if __name__ == "__main__":
    test_rsi_performance()
