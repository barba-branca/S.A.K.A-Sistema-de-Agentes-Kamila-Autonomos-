from fastapi import FastAPI, Depends
from saka.shared.security import get_api_key
from saka.shared.models import TradeProposal, PolarisApproval
import random

app = FastAPI(
    title="Polaris (Advisor Agent)",
    description="Fornece uma camada final de revisão e aprovação para decisões de trade críticas.",
    version="1.0.0"
)

@app.post("/review_trade",
            response_model=PolarisApproval,
            dependencies=[Depends(get_api_key)])
async def review_trade(proposal: TradeProposal):
    """
    Simula a revisão de uma proposta de trade.
    Aprova 95% das propostas e rejeita 5% para simular uma revisão crítica.
    """
    if random.random() < 0.95:
        return PolarisApproval(
            decision_approved=True,
            remarks="Proposta de trade alinhada com as diretrizes de risco. Aprovada."
        )
    else:
        return PolarisApproval(
            decision_approved=False,
            remarks="VETO DO ADVISOR: Proposta de trade rejeitada devido a um fator de risco não capturado (simulado)."
        )

@app.get("/health", summary="Endpoint de Health Check")
def health():
    """Endpoint público para health checks."""
    return {"status": "ok"}