import pytest
import httpx
from unittest.mock import AsyncMock
from fastapi import BackgroundTasks

from saka.agents.kamila_ceo.main import make_decision
from saka.shared.models import (
    ConsolidatedDataInput, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput,
    GaiaPositionSizingResponse, TradeSignal, MacroImpact
)

@pytest.mark.asyncio
async def test_kamila_sends_report_on_trade(mocker):
    """
    Testa se Kamila aciona o envio do relatório via WhatsApp quando
    uma decisão de 'execute_trade' é tomada.
    """
    # Mock da função de envio de relatório para ser um AsyncMock
    mock_send_report = mocker.patch('saka.agents.kamila_ceo.main.send_whatsapp_report', new_callable=AsyncMock)

    # Mock da chamada HTTP para o Gaia
    mock_gaia_response = GaiaPositionSizingResponse(asset="BTC/USD", amount_usd=150.0, reasoning="...")
    mock_response = mocker.MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_gaia_response.model_dump()

    mocker.patch(
        'httpx.AsyncClient.post',
        new_callable=AsyncMock,
        return_value=mock_response
    )

    # Cenário de sinal de compra claro
    strong_buy_signal_data = ConsolidatedDataInput(
        asset="BTC/USD",
        current_price=50000.0,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary="")
    )

    background_tasks = BackgroundTasks()
    decision = await make_decision(strong_buy_signal_data, background_tasks)

    # Executa as tarefas de background manualmente para o teste
    for task in background_tasks.tasks:
        await task.func(*task.args, **task.kwargs)

    # Verificações
    assert decision.action == "execute_trade"
    mock_send_report.assert_called_once()

    call_args, _ = mock_send_report.call_args
    report_body = call_args[0]
    assert "ALERTA S.A.K.A." in report_body
    assert "Ordem de BUY para BTC/USD" in report_body
    assert "$150.00" in report_body

@pytest.mark.asyncio
async def test_kamila_does_not_send_report_on_hold(mocker):
    """
    Testa se Kamila NÃO envia um relatório quando a decisão é 'hold'.
    """
    mock_send_report = mocker.patch('saka.agents.kamila_ceo.main.send_whatsapp_report', new_callable=AsyncMock)

    hold_data = ConsolidatedDataInput(
        asset="BTC/USD",
        current_price=50000.0,
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=50),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary="")
    )

    background_tasks = BackgroundTasks()
    decision = await make_decision(hold_data, background_tasks)

    assert decision.action == "hold"
    mock_send_report.assert_not_called()