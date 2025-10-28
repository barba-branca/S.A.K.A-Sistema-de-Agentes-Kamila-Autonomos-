import pytest
from unittest.mock import AsyncMock, MagicMock

from saka.agents.kamila_ceo.main import make_decision
from saka.shared.models import (
    ConsolidatedDataInput, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput,
    AthenaSentimentOutput, TradeSignal, MacroImpact, PolarisApproval, GaiaPositionSizingResponse
)

# --- Dados de Mock para os Testes ---
POSITIVE_SENTIMENT = AthenaSentimentOutput(asset="BTC/USD", sentiment_score=0.5, confidence=0.8, signal=TradeSignal.BUY)
MOCK_GAIA_RESPONSE = GaiaPositionSizingResponse(asset="BTC/USD", amount_usd=150.0, reasoning="...")

@pytest.fixture
def mock_background_tasks(mocker):
    return mocker.MagicMock()

@pytest.fixture
def base_test_data():
    """Retorna um objeto de dados de entrada com sinais favoráveis."""
    return ConsolidatedDataInput(
        asset="BTC/USD", current_price=50000,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary=""),
        athena_analysis=POSITIVE_SENTIMENT
    )

@pytest.mark.asyncio
async def test_kamila_proceeds_on_polaris_approval(mocker, mock_background_tasks, base_test_data):
    """
    Testa se o fluxo continua para Gaia quando Polaris aprova o trade.
    """
    # Mock para a resposta de aprovação do Polaris
    polaris_approval = PolarisApproval(decision_approved=True, remarks="Aprovado")
    # Mock para a resposta do Gaia
    gaia_response = MOCK_GAIA_RESPONSE

    # Configura o mock do cliente HTTP para retornar as respostas em ordem
    mock_post = AsyncMock(side_effect=[
        MagicMock(status_code=200, json=lambda: polaris_approval.model_dump()),
        MagicMock(status_code=200, json=lambda: gaia_response.model_dump())
    ])
    mocker.patch('httpx.AsyncClient.post', mock_post)

    decision = await make_decision(base_test_data, mock_background_tasks)

    # Verificações
    assert mock_post.call_count == 2 # Garante que tanto Polaris quanto Gaia foram chamados
    assert "review_trade" in mock_post.call_args_list[0].args[0]
    assert "calculate_position_size" in mock_post.call_args_list[1].args[0]

    assert decision.action == "execute_trade"
    assert "Aprovado por Polaris" in decision.reason

@pytest.mark.asyncio
async def test_kamila_stops_on_polaris_veto(mocker, mock_background_tasks, base_test_data):
    """
    Testa se o fluxo é interrompido quando Polaris rejeita o trade.
    """
    # Mock para a resposta de rejeição do Polaris
    polaris_rejection = PolarisApproval(decision_approved=False, remarks="VETO DO ADVISOR")

    mock_post = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: polaris_rejection.model_dump()))
    mocker.patch('httpx.AsyncClient.post', mock_post)

    decision = await make_decision(base_test_data, mock_background_tasks)

    # Verificações
    mock_post.assert_called_once() # Garante que apenas Polaris foi chamado
    assert "review_trade" in mock_post.call_args_list[0].args[0]

    assert decision.action == "hold"
    assert "VETO DO ADVISOR" in decision.reason