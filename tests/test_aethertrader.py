import pytest
from unittest.mock import MagicMock
import datetime

from saka.agents.aethertrader_manager.main import execute_trade
from saka.shared.models import KamilaFinalDecision, TradeSignal
from saka.database import models

mock_binance_client = MagicMock()

@pytest.fixture(autouse=True)
def override_binance_client(mocker):
    mocker.patch('saka.agents.aethertrader_manager.main.binance_client', mock_binance_client)
    mock_binance_client.ping.return_value = {}
    mock_binance_client.reset_mock()

MOCK_FILLED_ORDER_RESPONSE = {
    "symbol": "BTCUSDT", "orderId": 28, "status": "FILLED",
    "cummulativeQuoteQty": "150.00000000", "executedQty": "0.00500000",
    "transactTime": int(datetime.datetime.now().timestamp() * 1000)
}

@pytest.mark.asyncio
async def test_execute_trade_and_save_to_db(mocker):
    mock_binance_client.order_market_buy.return_value = MOCK_FILLED_ORDER_RESPONSE
    mock_db_session = MagicMock()

    decision = KamilaFinalDecision(
        action="execute_trade", side=TradeSignal.BUY, asset="BTC/USD", amount_usd=150.0,
        agent_target="aethertrader_manager", trade_type="market", reason="Test"
    )

    await execute_trade(decision, db=mock_db_session)

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    saved_trade = mock_db_session.add.call_args[0][0]
    assert isinstance(saved_trade, models.Trade)
    assert saved_trade.order_id == "28"

@pytest.mark.asyncio
async def test_execute_trade_api_error_does_not_save(mocker):
    from fastapi import HTTPException
    mock_binance_client.order_market_buy.side_effect = Exception("Erro de API simulado")
    mock_db_session = MagicMock()

    decision = KamilaFinalDecision(
        action="execute_trade", side=TradeSignal.BUY, asset="BTC/USD", amount_usd=150.0,
        agent_target="aethertrader_manager", trade_type="market", reason="Test"
    )

    with pytest.raises(HTTPException) as excinfo:
        await execute_trade(decision, db=mock_db_session)

    assert excinfo.value.status_code == 500
    assert "Erro de API simulado" in str(excinfo.value.detail)
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()