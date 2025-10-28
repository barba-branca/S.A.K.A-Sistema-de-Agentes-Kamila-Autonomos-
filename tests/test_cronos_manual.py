import pytest
import pandas as pd
from saka.agents.cronos_cycles.main import calculate_manual_rsi, calculate_manual_macd

def test_manual_rsi_calculation():
    """
    Testa a função de cálculo manual do RSI contra um valor conhecido.
    """
    prices = [
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64
    ]
    price_series = pd.Series(prices)
    expected_rsi = 53.64

    calculated_rsi = calculate_manual_rsi(price_series, period=14)

    assert abs(calculated_rsi - expected_rsi) < 0.6

def test_rsi_insufficient_data():
    """
    Testa se a função levanta um ValueError quando há dados insuficientes.
    """
    prices = [45.0, 46.0, 47.0]
    price_series = pd.Series(prices)
    with pytest.raises(ValueError, match="Dados insuficientes"):
        calculate_manual_rsi(price_series, period=14)

def test_macd_insufficient_data():
    """
    Testa se a função MACD levanta um erro com dados insuficientes.
    """
    prices = [45.0] * 20 # Menos de 26 períodos
    price_series = pd.Series(prices)
    with pytest.raises(ValueError, match="Dados insuficientes"):
        calculate_manual_macd(price_series)