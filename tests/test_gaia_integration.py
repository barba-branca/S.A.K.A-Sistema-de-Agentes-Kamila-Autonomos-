import pytest
import httpx
from unittest.mock import AsyncMock

from saka.agents.kamila_ceo.main import make_decision
from saka.shared.models import (
    ConsolidatedDataInput, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput,
    TradeSignal, MacroImpact, GaiaPositionSizingResponse
)

# Mock para a resposta do Gaia
MOCK_GAIA_RESPONSE = GaiaPositionSizingResponse(
    asset="BTC/USD",
    amount_usd=150.0,
    reasoning="Estratégia de dimensionamento de posição de valor fixo para BTC/USD."
)

def create_mock_response(status_code: int, json_data: dict) -> httpx.Response:
    """Cria um objeto httpx.Response completo com um request manequim."""
    mock_request = httpx.Request(method="POST", url="http://mock.url/calculate_position_size")
    return httpx.Response(status_code=status_code, json=json_data, request=mock_request)


@pytest.mark.asyncio
async def test_kamila_calls_gaia_on_buy_signal(mocker):
    """
    Testa se Kamila chama Gaia quando recebe um sinal de compra
    e usa o valor retornado por Gaia na decisão final.
    """
    strong_buy_signal_data = ConsolidatedDataInput(
        asset="BTC/USD",
        current_price=50000.0,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary="")
    )

    # Mock da chamada HTTP para o Gaia, agora usando a função helper
    mock_async_client = mocker.patch('httpx.AsyncClient')
    mock_instance = mock_async_client.return_value.__aenter__.return_value
    mock_instance.post.return_value = create_mock_response(200, MOCK_GAIA_RESPONSE.model_dump())

    decision = await make_decision(strong_buy_signal_data)

    mock_instance.post.assert_called_once()
    assert "calculate_position_size" in mock_instance.post.call_args[0][0]

    assert decision.action == "execute_trade"
    assert decision.side == TradeSignal.BUY
    assert decision.amount_usd == MOCK_GAIA_RESPONSE.amount_usd
    assert MOCK_GAIA_RESPONSE.reasoning in decision.reason

@pytest.mark.asyncio
async def test_kamila_does_not_call_gaia_on_veto(mocker):
    """
    Testa se Kamila NÃO chama Gaia se a negociação for vetada pelo Sentinel.
    """
    vetoed_data = ConsolidatedDataInput(
        asset="BTC/USD",
        current_price=50000.0,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.9, volatility=0.08, can_trade=False, reason="Risco alto"),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary="")
    )

    mock_async_client = mocker.patch('httpx.AsyncClient')
    mock_instance = mock_async_client.return_value.__aenter__.return_value

    decision = await make_decision(vetoed_data)

    mock_instance.post.assert_not_called()
    assert decision.action == "hold"
    assert "VETO (Sentinel)" in decision.reason