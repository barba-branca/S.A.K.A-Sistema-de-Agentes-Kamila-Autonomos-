from fastapi import FastAPI
from pydantic import BaseModel

# Este import funcionará por causa da estrutura do projeto e do Dockerfile.base
from saka.shared.models import SentinelRiskOutput

app = FastAPI(
    title="S.A.K.A. Sentinel (Risk)",
    description="Agente de análise e monitoramento de risco (Placeholder).",
    version="1.0.0"
)

class RiskInput(BaseModel):
    asset: str

@app.post("/analyze_risk", response_model=SentinelRiskOutput)
async def analyze_risk(data: RiskInput):
    """
    Blueprint para análise de risco.

    Para esta versão, ele sempre retorna um resultado 'seguro' para
    não bloquear as decisões de Kamila.
    """
    return SentinelRiskOutput(
        asset=data.asset,
        risk_level=0.2,  # Risco baixo
        volatility=0.01, # Volatilidade baixa
        can_trade=True,  # Sempre permite o trade
        reason="Análise de risco de placeholder."
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}