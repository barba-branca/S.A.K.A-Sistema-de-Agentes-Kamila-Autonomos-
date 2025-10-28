from fastapi import FastAPI, Depends
from saka.shared.models import AnalysisRequest, TradeSignal, AthenaSentimentOutput
from saka.shared.security import get_api_key
import random

app = FastAPI(
    title="Athena (Sentiment Analysis Agent)",
    description="Analisa o sentimento do mercado a partir de notícias e redes sociais.",
    version="1.0.0"
)

@app.post("/analyze_sentiment",
            response_model=AthenaSentimentOutput,
            dependencies=[Depends(get_api_key)])
async def analyze_sentiment(request: AnalysisRequest):
    """
    Simula a análise de sentimento do mercado para um determinado ativo.
    """
    sentiment_score = random.uniform(-1, 1)
    confidence = random.uniform(0.5, 1.0)

    if sentiment_score > 0.1:
        signal = TradeSignal.BUY
    elif sentiment_score < -0.1:
        signal = TradeSignal.SELL
    else:
        signal = TradeSignal.HOLD

    return AthenaSentimentOutput(
        asset=request.asset,
        sentiment_score=sentiment_score,
        confidence=confidence,
        signal=signal
    )

@app.get("/health", summary="Endpoint de Health Check")
def health():
    """Endpoint público para health checks."""
    return {"status": "ok"}