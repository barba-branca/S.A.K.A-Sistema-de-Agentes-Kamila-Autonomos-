import pytest
from unittest.mock import AsyncMock, MagicMock

from saka.agents.kamila_ceo.main import make_decision
from saka.shared.models import (
    ConsolidatedDataInput, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput,
    AthenaSentimentOutput, TradeSignal, MacroImpact, PolarisApproval, GaiaPositionSizingResponse
)

POSITIVE_SENTIMENT = AthenaSentimentOutput(asset="BTC/USD", sentiment_score=0.5, confidence=0.8, signal=TradeSignal.BUY)
CRONOS_BUY_SIGNAL = CronosTechnicalOutput(asset="BTC/USD", rsi=25, macd_line=1, signal_line=0, histogram=1, is_bullish_crossover=True, is_bearish_crossover=False)
CRONOS_NO_MACD_SIGNAL = CronosTechnicalOutput(asset="BTC/USD", rsi=25, macd_line=0, signal_line=1, histogram=-1, is_bullish_crossover=False, is_bearish_crossover=False)

@pytest.fixture
def mock_background_tasks(mocker):
    return mocker.MagicMock()

@pytest.fixture
def mock_approval_flow(mocker):
    mocker.patch('httpx.AsyncClient.post', AsyncMock(side_effect=[
        MagicMock(status_code=200, json=lambda: PolarisApproval(decision_approved=True, remarks="").model_dump()),
        MagicMock(status_code=200, json=lambda: GaiaPositionSizingResponse(asset="BTC/USD", amount_usd=150.0, reasoning="").model_dump())
    ]))

@pytest.mark.asyncio
async def test_kamila_buy_signal_with_confluence(mock_background_tasks, mock_approval_flow):
    test_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CRONOS_BUY_SIGNAL,
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=POSITIVE_SENTIMENT
    )
    decision = await make_decision(test_data, mock_background_tasks)
    assert decision.action == "execute_trade"
    assert decision.side == TradeSignal.BUY

@pytest.mark.asyncio
async def test_kamila_no_signal_if_macd_is_missing(mock_background_tasks):
    test_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CRONOS_NO_MACD_SIGNAL, # Sem cruzamento MACD
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=POSITIVE_SENTIMENT
    )
    decision = await make_decision(test_data, mock_background_tasks)
    assert decision.action == "hold"