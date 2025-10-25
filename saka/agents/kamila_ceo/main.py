from fastapi import FastAPI, Depends
from saka.shared.models import ConsolidatedDataInput, KamilaFinalDecision, AgentName, TradeSignal
from saka.shared.security import get_api_key

app = FastAPI(
    title="Kamila (CEO Agent)",
    description="Toma decisões de negociação com base em dados consolidados de outros agentes.",
    version="1.0.0" # Reverted to base version
)

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput):
    """
    Lógica de decisão da Kamila.
    """
    # Veto de Risco do Sentinel
    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(
            action="hold",
            reason=f"VETO: Sentinel bloqueou a negociação. {data.sentinel_analysis.reason}"
        )

    # Lógica de placeholder, já que não há outros sinais
    return KamilaFinalDecision(
        action="execute_trade",
        agent_target=AgentName.AETHERTRADER,
        asset=data.asset,
        trade_type="market",
        side=TradeSignal.BUY,
        amount_usd=100.0,
        reason="Sinal de placeholder. Risco aceitável."
    )

@app.get("/health")
def health():
    return {"status": "ok"}