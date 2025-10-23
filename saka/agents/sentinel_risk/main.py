from fastapi import FastAPI
from pydantic import BaseModel
from saka.shared.models import SentinelRiskOutput

app = FastAPI(title="Sentinel (Risk)")

class RiskInput(BaseModel):
    asset: str

@app.post("/analyze_risk", response_model=SentinelRiskOutput)
async def analyze_risk(data: RiskInput):
    return SentinelRiskOutput(
        asset=data.asset,
        risk_level=0.2,
        volatility=0.01,
        can_trade=True,
        reason="Análise de risco de placeholder."
    )

@app.get("/health")
def health():
    return {"status": "ok"}