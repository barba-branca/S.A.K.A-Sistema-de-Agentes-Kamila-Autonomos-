from fastapi import FastAPI
from pydantic import BaseModel
import random

# Este import funcionará por causa da estrutura do projeto e do Dockerfile.base
from saka.shared.models import CronosTechnicalOutput

app = FastAPI(
    title="S.A.K.A. Cronos (Cycles)",
    description="Agente de análise de ciclos temporais e indicadores técnicos.",
    version="1.0.0"
)

class AnalysisRequest(BaseModel):
    asset: str

@app.post("/analyze_cycles", response_model=CronosTechnicalOutput)
async def analyze_cycles(request: AnalysisRequest):
    """
    Blueprint para análise técnica.

    Nesta versão, ele simula o cálculo do RSI (Índice de Força Relativa).
    - RSI > 70 é geralmente considerado 'sobrecomprado' (sinal de venda).
    - RSI < 30 é geralmente considerado 'sobrevendido' (sinal de compra).
    """
    simulated_rsi = random.uniform(10.0, 90.0)

    return CronosTechnicalOutput(
        asset=request.asset,
        rsi=round(simulated_rsi, 2),
        summary=f"Análise técnica simulada. RSI de 14 dias: {simulated_rsi:.2f}"
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}