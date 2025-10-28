from fastapi import FastAPI, Depends, HTTPException
from saka.shared.models import AnalysisRequest, SentinelRiskOutput
from saka.shared.security import get_api_key
import numpy as np

app = FastAPI(title="Sentinel (Risk Agent)")

VOLATILITY_THRESHOLD = 0.05

@app.post("/analyze", response_model=SentinelRiskOutput, dependencies=[Depends(get_api_key)])
async def analyze_risk(request: AnalysisRequest):
    if not request.historical_prices or len(request.historical_prices) < 10:
        raise HTTPException(status_code=400, detail="Dados insuficientes para análise de risco.")
    try:
        prices = np.array(request.historical_prices)
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        can_trade = volatility <= VOLATILITY_THRESHOLD
        risk_level = min(volatility / (VOLATILITY_THRESHOLD * 2), 1.0)
        return SentinelRiskOutput(
            asset=request.asset, risk_level=risk_level, volatility=volatility,
            can_trade=can_trade, reason=f"Volatilidade: {volatility:.4f}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health(): return {"status": "ok"}