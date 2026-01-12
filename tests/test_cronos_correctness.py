from saka.agents.cronos_cycles.main import calculate_manual_rsi
import pytest
import pandas as pd

def test_rsi_calculation_basic():
    """Test basic RSI calculation with a known small dataset."""
    # Simple uptrend
    prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0]
    # Not enough data for 14 periods + warm up, but function should run if len > period
    # Wait, the function requires len > period
    assert len(prices) > 14
    rsi = calculate_manual_rsi(prices)
    assert 0 <= rsi <= 100

def test_rsi_calculation_truncation_correctness():
    """Verify that truncation does not affect the result significantly."""
    # Generate a long list of prices
    import random
    random.seed(42)
    long_history = [100.0]
    for _ in range(2000):
        change = random.uniform(-1, 1)
        long_history.append(long_history[-1] + change)

    # Calculate with full history (simulated by bypassing truncation if we could,
    # but since we modified the code, we can't easily bypass it without mocking.
    # Instead, let's compare with a manual calculation using pandas directly here
    # mimicking the OLD behavior)

    series = pd.Series(long_history)
    delta = series.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    period = 14
    avg_gain = gains.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = losses.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi_full = 100 - (100 / (1 + rs))
    expected_rsi = rsi_full.iloc[-1]

    # Calculate with optimized function
    calculated_rsi = calculate_manual_rsi(long_history)

    # Difference should be negligible
    assert abs(calculated_rsi - expected_rsi) < 0.0001
