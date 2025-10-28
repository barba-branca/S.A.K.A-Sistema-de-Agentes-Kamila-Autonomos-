from fastapi import FastAPI, Depends
from saka.shared.security import get_api_key
from saka.shared.models import TradeProposal, PolarisApproval
import random

app = FastAPI(title="Polaris (Advisor Agent)")

@app.post("/review_trade", response_model=PolarisApproval, dependencies=[Depends(get_api_key)])
async def review_trade(proposal: TradeProposal):
    if random.random() < 0.95:
        return PolarisApproval(decision_approved=True, remarks="Proposta Aprovada pelo Advisor.")
    else:
        return PolarisApproval(decision_approved=False, remarks="VETO DO ADVISOR: Proposta Rejeitada (simulado).")

@app.get("/health")
def health(): return {"status": "ok"}