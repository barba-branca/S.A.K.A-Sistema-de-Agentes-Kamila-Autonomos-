import pytest
from unittest.mock import AsyncMock, MagicMock

from saka.agents.kamila_ceo.main import make_decision
from saka.shared.models import (
    ConsolidatedDataInput, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput,
    AthenaSentimentOutput, TradeSignal, MacroImpact, PolarisApproval, GaiaPositionSizingResponse
)

# --- Dados de Mock para os Testes ---
POSITIVE_SENTIMENT = AthenaSentimentOutput(asset="BTC/USD", sentiment_score=0.5, confidence=0.8, signal=TradeSignal.BUY)
NEUTRAL_SENTIMENT = AthenaSentimentOutput(asset="BTC/USD", sentiment_score=0.05, confidence=0.8, signal=TradeSignal.HOLD)
MOCK_POLARIS_APPROVAL = PolarisApproval(decision_approved=True, remarks="Aprovado por Polaris.")
MOCK_GAIA_RESPONSE = GaiaPositionSizingResponse(asset="BTC/USD", amount_usd=150.0, reasoning="...")

@pytest.fixture
def mock_background_tasks(mocker):
    return mocker.MagicMock()

@pytest.fixture
def mock_polaris_and_gaia_calls(mocker):
    """Fixture para mockar as chamadas para Polaris e Gaia."""
    # Configura o mock para retornar respostas em sequência: primeiro Polaris, depois Gaia
    mock_post = AsyncMock(side_effect=[
        MagicMock(status_code=200, json=lambda: MOCK_POLARIS_APPROVAL.model_dump()),
        MagicMock(status_code=200, json=lambda: MOCK_GAIA_RESPONSE.model_dump())
    ])
    mocker.patch('httpx.AsyncClient.post', mock_post)
    return mock_post

@pytest.mark.asyncio
async def test_kamila_orion_veto(mock_background_tasks):
    test_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.HIGH, event_name="CPI", summary="Veto"),
        athena_analysis=POSITIVE_SENTIMENT
    )
    decision = await make_decision(test_data, mock_background_tasks)
    assert decision.action == "hold"
    assert "VETO (Orion)" in decision.reason

@pytest.mark.asyncio
async def test_kamila_sentinel_veto(mock_background_tasks):
    test_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.8, volatility=0.06, can_trade=False, reason="Volatilidade alta"),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=50),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=POSITIVE_SENTIMENT
    )
    decision = await make_decision(test_data, mock_background_tasks)
    assert decision.action == "hold"
    assert "VETO (Sentinel)" in decision.reason

@pytest.mark.asyncio
async def test_kamila_buy_signal_with_all_approvals(mock_background_tasks, mock_polaris_and_gaia_calls):
    test_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=POSITIVE_SENTIMENT
    )
    decision = await make_decision(test_data, mock_background_tasks)
    assert decision.action == "execute_trade"
    assert decision.side == TradeSignal.BUY
    assert "Aprovado por Polaris" in decision.reason
    assert mock_polaris_and_gaia_calls.call_count == 2

@pytest.mark.asyncio
async def test_kamila_buy_signal_vetoed_by_sentiment(mock_background_tasks, mock_polaris_and_gaia_calls):
    test_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=NEUTRAL_SENTIMENT
    )
    decision = await make_decision(test_data, mock_background_tasks)
    assert decision.action == "hold"
    assert "não confirmado pelo sentimento" in decision.reason
    assert mock_polaris_and_gaia_calls.call_count == 0