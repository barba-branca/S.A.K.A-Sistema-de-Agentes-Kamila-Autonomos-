import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from saka.agents.aethertrader_manager.main import execute_trade
from saka.shared.models import KamilaFinalDecision, TradeSignal

# Mock para o cliente da Binance
mock_binance_client = MagicMock()

@pytest.fixture(autouse=True)
def override_binance_client(mocker):
    """
    Sobrescreve o cliente global da Binance com um mock para todos os testes.
    """
    mocker.patch('saka.agents.aethertrader_manager.main.binance_client', mock_binance_client)
    mock_binance_client.ping.return_value = {}

@pytest.mark.asyncio
async def test_execute_trade_success():
    """
    Testa uma execução de trade bem-sucedida.
    """
    mock_binance_client.reset_mock() # Reseta o mock antes de cada teste
    mock_binance_client.get_avg_price.return_value = {'price': '50000.00'}
    mock_binance_client.create_test_order.return_value = {'test': 'order_data'}

    decision = KamilaFinalDecision(
        action="execute_trade", agent_target="aethertrader_manager", asset="BTC/USD",
        trade_type="market", side=TradeSignal.BUY, amount_usd=200.0, reason="Test"
    )

    receipt = await execute_trade(decision)

    mock_binance_client.get_avg_price.assert_called_with(symbol='BTCUSDT')
    mock_binance_client.create_test_order.assert_called_once()

    call_args = mock_binance_client.create_test_order.call_args[1]
    assert call_args['symbol'] == 'BTCUSDT'
    assert call_args['side'] == 'BUY'
    assert call_args['quantity'] == 0.004

    assert receipt.status == "test_success"
    assert receipt.executed_price == 50000.0

@pytest.mark.asyncio
async def test_execute_trade_generic_error():
    """
    Testa o tratamento de erro genérico quando a biblioteca da Binance falha.
    """
    mock_binance_client.reset_mock()
    # Simula um erro genérico na chamada da API
    mock_binance_client.get_avg_price.side_effect = Exception("Erro de conexão simulado")

    decision = KamilaFinalDecision(
        action="execute_trade", agent_target="aethertrader_manager", asset="INVALID/ASSET",
        trade_type="market", side=TradeSignal.BUY, amount_usd=100.0, reason="Test"
    )

    with pytest.raises(HTTPException) as excinfo:
        await execute_trade(decision)

    assert excinfo.value.status_code == 500
    assert "Erro de conexão simulado" in str(excinfo.value.detail)