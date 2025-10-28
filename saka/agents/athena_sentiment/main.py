from fastapi import FastAPI, Depends
from saka.shared.models import AnalysisRequest, TradeSignal, AthenaSentimentOutput
from saka.shared.security import get_api_key
import random

app = FastAPI(title="Athena (Sentiment Analysis Agent)")

@app.post("/analyze_sentiment", response_model=AthenaSentimentOutput, dependencies=[Depends(get_api_key)])
async def analyze_sentiment(request: AnalysisRequest):
    sentiment_score = random.uniform(-1, 1)
    if sentiment_score > 0.1: signal = TradeSignal.BUY
    elif sentiment_score < -0.1: signal = TradeSignal.SELL
    else: signal = TradeSignal.HOLD
    return AthenaSentimentOutput(
        asset=request.asset, sentiment_score=sentiment_score,
        confidence=random.uniform(0.5, 1.0), signal=signal
    )

@app.get("/health")
def health(): return {"status": "ok"}