from fastapi import FastAPI, HTTPException
import os
import httpx
from pydantic import BaseModel

from saka.shared.models import (
    ConsolidatedDataInput, KamilaFinalDecision, AgentName,
    TradeDecisionProposal, PolarisRecommendation, GaiaPortfolioImpactAnalysis,
    GaiaPortfolioAdjustment
)

app = FastAPI(title="Kamila (CEO)")

AETHERTRADER_URL = os.getenv("AETHERTRADER_URL")
POLARIS_URL = os.getenv("POLARIS_URL")
GAIA_URL = os.getenv("GAIA_URL")

class DecisionResponse(BaseModel):
    status: str
    details: dict

@app.post("/decide", response_model=DecisionResponse)
async def make_decision(data: ConsolidatedDataInput):
    if data.orion_analysis.impact == 'high':
        return {"status": "action_hold", "details": {"reason": "High macro impact event."}}

    trade_decision = None
    if data.athena_analysis.signal == 'buy' and data.athena_analysis.confidence >= 0.75 and data.cronos_analysis.rsi < 30:
        trade_decision = 'buy'
    elif data.athena_analysis.signal == 'sell' and data.athena_analysis.confidence >= 0.75 and data.cronos_analysis.rsi > 70:
        trade_decision = 'sell'

    if not trade_decision:
        return {"status": "action_hold", "details": {"reason": "Signal criteria not met."}}

    trade_proposal = TradeDecisionProposal(
        asset=data.asset, trade_type="market", side=trade_decision,
        amount_usd=100.0, reasoning="Initial proposal based on signals."
    )

    async with httpx.AsyncClient() as client:
        try:
            polaris_response = await client.post(f"{POLARIS_URL}/review", json=trade_proposal.dict(), timeout=10.0)
            polaris_response.raise_for_status()
            polaris_rec = PolarisRecommendation(**polaris_response.json())
            if not polaris_rec.decision_approved:
                return {"status": "trade_vetoed", "details": polaris_rec.dict()}

            gaia_input = GaiaPortfolioImpactAnalysis(asset=trade_proposal.asset, side=trade_proposal.side, proposed_amount_usd=trade_proposal.amount_usd)
            gaia_response = await client.post(f"{GAIA_URL}/analyze_portfolio_impact", json=gaia_input.dict(), timeout=10.0)
            gaia_response.raise_for_status()
            gaia_adjustment = GaiaPortfolioAdjustment(**gaia_response.json())

            final_decision = KamilaFinalDecision(
                action="execute_trade", agent_target=AgentName.AETHERTRADER,
                asset=data.asset, trade_type=trade_proposal.trade_type,
                side=trade_proposal.side, amount_usd=gaia_adjustment.adjusted_amount_usd
            )

            aethertrader_response = await client.post(f"{AETHERTRADER_URL}/execute_trade", json=final_decision.dict(), timeout=10.0)
            aethertrader_response.raise_for_status()
            return {"status": "trade_executed", "details": aethertrader_response.json()}
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Agent communication error: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}