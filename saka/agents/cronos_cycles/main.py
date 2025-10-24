from fastapi import FastAPI
from typing import List
import pandas as pd
from saka.shared.models import CronosTechnicalOutput, CronosRequest

app = FastAPI(title="Cronos (Cycles)")

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period:
        return 50.0
    series = pd.Series(prices)
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]
    return last_rsi if pd.notna(last_rsi) else 50.0

@app.post("/analyze_cycles", response_model=CronosTechnicalOutput)
async def analyze_cycles(request: CronosRequest):
    rsi_value = calculate_rsi(request.close_prices)
    return CronosTechnicalOutput(
        asset=request.asset,
        rsi=round(rsi_value, 2),
        summary=f"RSI de 14 dias calculado: {rsi_value:.2f}"
    )

@app.get("/health")
def health():
    return {"status": "ok"}