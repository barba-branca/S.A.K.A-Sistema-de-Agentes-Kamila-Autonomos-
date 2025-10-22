from fastapi import FastAPI
import sys
from pydantic import BaseModel

sys.path.append('../')
from shared.models import AthenaSentimentOutput, TradeSignal

app = FastAPI(title="Athena (Sentiment)")

class SentimentRequest(BaseModel):
    asset: str

@app.post("/analyze_sentiment", response_model=AthenaSentimentOutput)
async def analyze_sentiment(request: SentimentRequest):
    """
    Endpoint de placeholder para a análise de sentimento de Athena.
    Retorna um resultado simulado.
    """
    return AthenaSentimentOutput(
        asset=request.asset,
        sentiment_score=0.8,
        signal=TradeSignal.BUY,
        confidence=0.9,
        source_summary="Análise simulada baseada em fontes genéricas."
    )

@app.get("/health")
def health():
    return {"status": "ok"}