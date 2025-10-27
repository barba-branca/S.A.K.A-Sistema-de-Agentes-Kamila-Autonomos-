import pytest
from saka.agents.kamila_ceo.main import make_decision
from saka.shared.models import (
    ConsolidatedDataInput, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput,
    TradeSignal, MacroImpact
)

@pytest.mark.asyncio
async def test_kamila_orion_veto():
    """
    Testa se Kamila veta corretamente uma negociação quando Orion
    sinaliza um evento de alto impacto, mesmo com sinais de compra.
    """
    # Cenário: Todos os sinais são de compra, mas Orion veta.
    strong_buy_signal_data = ConsolidatedDataInput(
        asset="BTC/USD",
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25), # RSI indica forte sobrevenda
        orion_analysis=OrionMacroOutput(
            asset="BTC/USD",
            impact=MacroImpact.HIGH, # Orion veta a negociação
            event_name="CPI Report",
            summary="Negociação bloqueada devido a evento macroeconômico de alto impacto."
        )
    )

    decision = await make_decision(strong_buy_signal_data)

    assert decision.action == "hold"
    assert "VETO (Orion)" in decision.reason

@pytest.mark.asyncio
async def test_kamila_sentinel_veto_over_orion():
    """
    Testa se o veto do Sentinel tem prioridade sobre o do Orion.
    """
    high_risk_data = ConsolidatedDataInput(
        asset="BTC/USD",
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.8, volatility=0.06, can_trade=False, reason="Volatilidade muito alta"),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=50),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary="")
    )

    decision = await make_decision(high_risk_data)

    assert decision.action == "hold"
    assert "VETO (Sentinel)" in decision.reason

@pytest.mark.asyncio
async def test_kamila_buy_signal():
    """
    Testa se Kamila gera um sinal de compra quando todas as condições são favoráveis.
    """
    all_clear_data = ConsolidatedDataInput(
        asset="BTC/USD",
        sentinel_analysis=SentinelRiskOutput(asset="BTC/USD", risk_level=0.2, volatility=0.03, can_trade=True, reason=""),
        cronos_analysis=CronosTechnicalOutput(asset="BTC/USD", rsi=25),
        orion_analysis=OrionMacroOutput(asset="BTC/USD", impact=MacroImpact.LOW, event_name="", summary="")
    )

    decision = await make_decision(all_clear_data)

    assert decision.action == "execute_trade"
    assert decision.side == TradeSignal.BUY
    assert "SINAL DE COMPRA" in decision.reason