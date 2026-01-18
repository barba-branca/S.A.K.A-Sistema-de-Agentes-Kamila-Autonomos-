from fastapi import FastAPI, HTTPException, Depends
from saka.shared.models import AnalysisRequest, SentinelRiskOutput, ErrorResponse, AgentName
from saka.shared.security import get_api_key
import numpy as np

app = FastAPI(
    title="Sentinel (Risk Agent)",
    description="Calcula a volatilidade e avalia o risco de negociação.",
    version="1.1.0"
)

VOLATILITY_THRESHOLD = 0.05 # Variação diária de 5%

def calculate_risk_metrics(prices_list: list[float]) -> tuple[float, float, bool, str]:
    """
    Calcula as métricas de risco a partir de uma lista de preços.
    Retorna: (risk_level, volatility, can_trade, reason)
    """
    if not prices_list or len(prices_list) < 10:
         raise ValueError("Dados de preços históricos insuficientes. São necessários pelo menos 10 pontos.")

    # Optimization: Volatility is a short-term metric.
    # Truncate history to the last 500 periods to ensure O(1) performance.
    MAX_HISTORY = 500
    if len(prices_list) > MAX_HISTORY:
        prices_list = prices_list[-MAX_HISTORY:]

    prices = np.array(prices_list)
    returns = np.diff(prices) / prices[:-1]
    volatility = float(np.std(returns)) # Ensure float type

    can_trade = volatility <= VOLATILITY_THRESHOLD
    risk_level = min(volatility / (VOLATILITY_THRESHOLD * 2), 1.0)
    reason = f"Volatilidade calculada: {volatility:.4f}. Limite: {VOLATILITY_THRESHOLD:.4f}."

    return risk_level, volatility, can_trade, reason

@app.post("/analyze",
            response_model=SentinelRiskOutput,
            responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
            dependencies=[Depends(get_api_key)])
async def analyze_risk(request: AnalysisRequest):
    """
    Analisa o risco de um ativo calculando a volatilidade de seus preços.
    Este endpoint é protegido e requer uma chave de API interna.
    """
    try:
        risk_level, volatility, can_trade, reason = calculate_risk_metrics(request.historical_prices)

        return SentinelRiskOutput(
            asset=request.asset,
            risk_level=risk_level,
            volatility=volatility,
            can_trade=can_trade,
            reason=reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Bad Request",
                "details": str(e),
                "source_agent": AgentName.SENTINEL
            }
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
