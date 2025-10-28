import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from saka.agents.kamila_ceo.main import make_decision
from saka.shared.models import (
    ConsolidatedDataInput, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput,
    AthenaSentimentOutput, TradeSignal, MacroImpact, GaiaPositionSizingResponse, PolarisApproval
)

# --- Dados de Mock ---
MOCK_POLARIS_APPROVAL = PolarisApproval(decision_approved=True, remarks="Aprovado")
MOCK_GAIA_RESPONSE = GaiaPositionSizingResponse(asset="BTC/USD", amount_usd=150.0, reasoning="...")
POSITIVE_SENTIMENT = AthenaSentimentOutput(asset="BTC/USD", sentiment_score=0.5, confidence=0.8, signal=TradeSignal.BUY)

@pytest.fixture
def mock_background_tasks(mocker):
    return mocker.MagicMock()

@pytest.mark.asyncio
async def test_kamila_calls_gaia_after_polaris_approval(mocker, mock_background_tasks):
    """
    Testa se Kamila chama Gaia corretamente APÓS receber a aprovação do Polaris.
    """
    # Configura o mock para retornar a aprovação do Polaris e depois a resposta do Gaia
    mock_post = AsyncMock(side_effect=[
        MagicMock(status_code=200, json=lambda: MOCK_POLARIS_APPROVAL.model_dump()),
        MagicMock(status_code=200, json=lambda: MOCK_GAIA_RESPONSE.model_dump())
    ])
    mocker.patch('httpx.AsyncClient.post', mock_post)

    test_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=POSITIVE_SENTIMENT
    )

    decision = await make_decision(test_data, mock_background_tasks)

    assert mock_post.call_count == 2
    assert "review_trade" in mock_post.call_args_list[0].args[0]
    assert "calculate_position_size" in mock_post.call_args_list[1].args[0]
    assert decision.action == "execute_trade"
    assert decision.amount_usd == MOCK_GAIA_RESPONSE.amount_usd

@pytest.mark.asyncio
async def test_kamila_does_not_call_gaia_on_veto(mocker, mock_background_tasks):
    """
    Testa se Kamila NÃO chama Gaia (ou Polaris) se a negociação for vetada pelo Sentinel.
    """
    mock_post = mocker.patch('httpx.AsyncClient.post', new_callable=AsyncMock)

    vetoed_data = ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.9, volatility=0.08, can_trade=False, reason="Risco alto"),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=POSITIVE_SENTIMENT
    )

    decision = await make_decision(vetoed_data, mock_background_tasks)

    mock_post.assert_not_called()
    assert decision.action == "hold"
    assert "VETO (Sentinel)" in decision.reason