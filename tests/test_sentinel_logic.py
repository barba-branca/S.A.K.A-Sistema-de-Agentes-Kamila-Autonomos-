import pytest
import numpy as np
from saka.agents.sentinel_risk.main import calculate_risk_metrics

def test_sentinel_calculation_accuracy():
    """
    Testa se o cálculo da volatilidade está correto para um conjunto pequeno de dados.
    """
    # Exemplo simples: Preços constantes -> Volatilidade 0
    prices = [100.0] * 20
    _, volatility, _, _ = calculate_risk_metrics(prices)
    assert volatility == 0.0

    # Exemplo simples 2: Preços oscilando de forma conhecida
    # [100, 101, 100, 101, ...]
    # Returns: [0.01, -0.0099, 0.01, ...]
    prices = [100.0 if i % 2 == 0 else 101.0 for i in range(20)]
    _, volatility, _, _ = calculate_risk_metrics(prices)

    # Expected: diffs are 1, -1, 1, -1...
    # returns are 1/100, -1/101, 1/100, -1/101
    returns = []
    for i in range(len(prices)-1):
        returns.append((prices[i+1] - prices[i]) / prices[i])

    expected_vol = float(np.std(returns))
    assert abs(volatility - expected_vol) < 1e-9

def test_sentinel_truncation_logic():
    """
    Testa se a função aceita listas grandes sem erro e se a otimização de truncamento
    resulta em um valor calculado baseado nos últimos 500 itens.
    """
    # Cria uma lista de 1000 itens.
    # Primeiros 500 itens são muito voláteis.
    # Últimos 500 itens são estáveis (volatilidade 0).

    volatile_part = [100.0 + ((-1)**i)*10 for i in range(500)] # 110, 90, 110, 90...
    stable_part = [100.0] * 500

    prices = volatile_part + stable_part

    # Se calcular com tudo, volatilidade seria alta.
    # Se truncar para os últimos 500 (stable_part), volatilidade deve ser 0.

    _, volatility, _, _ = calculate_risk_metrics(prices)

    # Com a otimização, ele deve olhar apenas para os últimos 500 itens (stable_part).
    # Portanto, a volatilidade deve ser 0.
    assert volatility == 0.0

def test_sentinel_insufficient_data():
    """
    Testa se levanta erro com poucos dados.
    """
    prices = [100.0, 101.0, 102.0] # 3 itens
    with pytest.raises(ValueError, match="Dados de preços históricos insuficientes"):
        calculate_risk_metrics(prices)
