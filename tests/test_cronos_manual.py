import pytest
from saka.agents.cronos_cycles.main import calculate_manual_rsi

def test_manual_rsi_calculation():
    """
    Testa a função de cálculo manual do RSI contra um valor conhecido.
    """
    # Série de preços de exemplo.
    prices = [
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64
    ]

    # Valor de RSI de 14 períodos para esta série, calculado com uma fonte de referência.
    expected_rsi = 53.64

    # Calcula o RSI com a nossa função
    calculated_rsi = calculate_manual_rsi(prices, period=14)

    # Compara os valores com uma tolerância razoável para diferenças de arredondamento
    assert abs(calculated_rsi - expected_rsi) < 0.6

def test_rsi_insufficient_data():
    """
    Testa se a função levanta um ValueError quando há dados insuficientes.
    """
    prices = [45.0, 46.0, 47.0] # Apenas 3 pontos
    with pytest.raises(ValueError, match="Dados insuficientes"):
        calculate_manual_rsi(prices, period=14)