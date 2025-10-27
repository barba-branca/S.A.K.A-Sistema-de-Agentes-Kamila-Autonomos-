from fastapi import FastAPI, HTTPException, Depends
from saka.shared.models import AnalysisRequest, SentinelRiskOutput, ErrorResponse, AgentName
from saka.shared.security import get_api_key
import numpy as np

app = FastAPI(
    title="Sentinel (Risk Agent)",
    description="Calcula a volatilidade e avalia o risco de negociação.",
    version="1.1.0" # Version bump
)

VOLATILITY_THRESHOLD = 0.05 # Variação diária de 5%

@app.post("/analyze",
            response_model=SentinelRiskOutput,
            responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
            dependencies=[Depends(get_api_key)]) # <-- Protege este endpoint
async def analyze_risk(request: AnalysisRequest):
    """
    Analisa o risco de um ativo calculando a volatilidade de seus preços.
    Este endpoint é protegido e requer uma chave de API interna.
    """
    if not request.historical_prices or len(request.historical_prices) < 10:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Bad Request",
                "details": "Dados de preços históricos insuficientes. São necessários pelo menos 10 pontos.",
                "source_agent": AgentName.SENTINEL
            }
        )

    try:
        prices = np.array(request.historical_prices)
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)

        can_trade = volatility <= VOLATILITY_THRESHOLD
        risk_level = min(volatility / (VOLATILITY_THRESHOLD * 2), 1.0)

        return SentinelRiskOutput(
            asset=request.asset,
            risk_level=risk_level,
            volatility=volatility,
            can_trade=can_trade,
            reason=f"Volatilidade calculada: {volatility:.4f}. Limite: {VOLATILITY_THRESHOLD:.4f}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "details": str(e),
                "source_agent": AgentName.SENTINEL
            }
        )

@app.get("/health", summary="Endpoint de Health Check")
def health():
    """Endpoint público para health checks. Não requer autenticação."""
    return {"status": "ok"}