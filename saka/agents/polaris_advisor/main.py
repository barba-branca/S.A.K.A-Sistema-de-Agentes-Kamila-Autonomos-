from fastapi import FastAPI
from pydantic import BaseModel

from saka.shared.models import TradeDecisionProposal, PolarisRecommendation

app = FastAPI(
    title="S.A.K.A. Polaris (Advisor)",
    description="Agente conselheiro que revisa decisões de trade críticas.",
    version="1.0.0"
)

@app.post("/review", response_model=PolarisRecommendation)
async def review_trade_proposal(proposal: TradeDecisionProposal):
    """
    Recebe uma proposta de trade de Kamila e a revisa.

    Lógica de placeholder: Rejeita qualquer trade com valor acima de $500
    para simular uma política de aversão a alto risco.
    """
    RISK_AMOUNT_THRESHOLD = 500.0

    if proposal.amount_usd > RISK_AMOUNT_THRESHOLD:
        return PolarisRecommendation(
            decision_approved=False,
            confidence=0.95,
            remarks=f"Proposta negada. O valor de ${proposal.amount_usd} excede o limiar de risco de ${RISK_AMOUNT_THRESHOLD}."
        )

    return PolarisRecommendation(
        decision_approved=True,
        confidence=0.90,
        remarks="A proposta está dentro dos parâmetros de risco aceitáveis."
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}