from fastapi import FastAPI
from pydantic import BaseModel
import random
from saka.shared.models import AthenaSentimentOutput, TradeSignal

app = FastAPI(title="Athena (Sentiment)")

class SentimentRequest(BaseModel):
    asset: str

@app.post("/analyze_sentiment", response_model=AthenaSentimentOutput)
async def analyze_sentiment(request: SentimentRequest):
    simulated_score = random.uniform(-1.0, 1.0)
    simulated_confidence = random.uniform(0.4, 0.99)
    if simulated_score > 0.3:
        signal = TradeSignal.BUY
    elif simulated_score < -0.3:
        signal = TradeSignal.SELL
    else:
        signal = TradeSignal.HOLD
    return AthenaSentimentOutput(
        asset=request.asset,
        sentiment_score=simulated_score,
        signal=signal,
        confidence=simulated_confidence,
        source_summary="Análise simulada dinâmica."
    )

@app.get("/health")
def health():
    return {"status": "ok"}