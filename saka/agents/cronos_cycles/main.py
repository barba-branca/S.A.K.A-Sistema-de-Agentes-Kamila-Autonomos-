from fastapi import FastAPI
from pydantic import BaseModel
import random
from saka.shared.models import CronosTechnicalOutput

app = FastAPI(title="Cronos (Cycles)")

class AnalysisRequest(BaseModel):
    asset: str

@app.post("/analyze_cycles", response_model=CronosTechnicalOutput)
async def analyze_cycles(request: AnalysisRequest):
    simulated_rsi = random.uniform(10.0, 90.0)
    return CronosTechnicalOutput(
        asset=request.asset,
        rsi=round(simulated_rsi, 2),
        summary=f"Análise técnica simulada. RSI de 14 dias: {simulated_rsi:.2f}"
    )

@app.get("/health")
def health():
    return {"status": "ok"}