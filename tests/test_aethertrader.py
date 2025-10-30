import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
import datetime

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
    mock_binance_client.reset_mock() # Garante que os mocks são limpos entre os testes

# Mock de uma resposta de ordem de mercado preenchida da Binance
MOCK_FILLED_ORDER_RESPONSE = {
    "symbol": "BTCUSDT",
    "orderId": 28,
    "status": "FILLED",
    "cummulativeQuoteQty": "150.00000000", # Valor total em USDT
    "executedQty": "0.00500000", # Quantidade total em BTC
    "fills": [
        {
            "price": "30000.00000000",
            "qty": "0.00500000",
            "commission": "0.00000500",
            "commissionAsset": "BTC",
            "tradeId": 56
        }
    ],
    "transactTime": int(datetime.datetime.now().timestamp() * 1000)
}

@pytest.mark.asyncio
async def test_execute_buy_order_success():
    """
    Testa uma execução de ordem de compra bem-sucedida, validando o processamento da resposta.
    """
    mock_binance_client.order_market_buy.return_value = MOCK_FILLED_ORDER_RESPONSE

    decision = KamilaFinalDecision(
        action="execute_trade", side=TradeSignal.BUY, asset="BTC/USD", amount_usd=150.0,
        agent_target="aethertrader_manager", trade_type="market", reason="Test"
    )

    receipt = await execute_trade(decision)

    mock_binance_client.order_market_buy.assert_called_once_with(symbol='BTCUSDT', quoteOrderQty=150.0)

    assert receipt.status == "success"
    assert receipt.order_id == "28"
    assert receipt.executed_price == 30000.0 # 150.0 / 0.005
    assert receipt.executed_quantity == 0.005
    assert receipt.amount_usd == 150.0
    assert receipt.raw_response == MOCK_FILLED_ORDER_RESPONSE

@pytest.mark.asyncio
async def test_sell_order_is_simulated():
    """
    Testa se a ordem de venda ainda é uma simulação (pois não temos a lógica de quantidade).
    """
    mock_binance_client.create_test_order.return_value = {}

    decision = KamilaFinalDecision(
        action="execute_trade", side=TradeSignal.SELL, asset="BTC/USD", amount_usd=150.0,
        agent_target="aethertrader_manager", trade_type="market", reason="Test"
    )

    receipt = await execute_trade(decision)

    mock_binance_client.order_market_buy.assert_not_called()
    assert receipt.status == "test_success"
    assert "simulated_sell" in receipt.order_id