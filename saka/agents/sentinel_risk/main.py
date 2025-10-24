from fastapi import FastAPI
from saka.shared.models import SentinelRiskOutput, SentinelRequest

app = FastAPI(title="Sentinel (Risk)")

@app.post("/analyze_risk", response_model=SentinelRiskOutput)
async def analyze_risk(data: SentinelRequest):
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