from fastapi import FastAPI
from saka.shared.models import TradeDecisionProposal, PolarisRecommendation

app = FastAPI(title="Polaris (Advisor)")

@app.post("/review", response_model=PolarisRecommendation)
async def review_trade_proposal(proposal: TradeDecisionProposal):
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
def health():
    return {"status": "ok"}