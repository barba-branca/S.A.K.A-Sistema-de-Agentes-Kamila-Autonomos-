from fastapi import FastAPI, Depends
from saka.shared.security import get_api_key
from saka.shared.models import TradeProposal, PolarisApproval
from saka.shared.logging_config import configure_logging, get_logger
import random

configure_logging()
logger = get_logger("polaris_advisor")

app = FastAPI(title="Polaris (Advisor Agent)")

@app.post("/review_trade", response_model=PolarisApproval, dependencies=[Depends(get_api_key)])
async def review_trade(proposal: TradeProposal):
    logger.info("Recebida proposta de trade para revisão", asset=proposal.asset, side=proposal.side)

    if random.random() < 0.95:
        remarks = "Proposta de trade alinhada com as diretrizes de risco. Aprovada."
        logger.info("Proposta de trade APROVADA", asset=proposal.asset)
        return PolarisApproval(decision_approved=True, remarks=remarks)
    else:
        remarks = "VETO DO ADVISOR: Proposta de trade rejeitada (simulado)."
        logger.warning("Proposta de trade REJEITADA", asset=proposal.asset, reason=remarks)
        return PolarisApproval(decision_approved=False, remarks=remarks)

@app.get("/health")
def health(): return {"status": "ok"}
