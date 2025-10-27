from fastapi import FastAPI, Depends, HTTPException
from saka.shared.models import AnalysisRequest, CronosTechnicalOutput, ErrorResponse, AgentName
from saka.shared.security import get_api_key
import pandas as pd

app = FastAPI(
    title="Cronos (Manual RSI Agent)",
    description="Calcula o RSI (Índice de Força Relativa) manualmente a partir de dados de preços.",
    version="1.3.0" # Reverted to simpler EMA formula
)

def calculate_manual_rsi(prices: list[float], period: int = 14) -> float:
    """
    Calcula o RSI manualmente para uma dada lista de preços usando EMA.
    """
    if len(prices) < period + 1:
        raise ValueError("Dados insuficientes para calcular o RSI para o período especificado.")

    series = pd.Series(prices)
    delta = series.diff()

    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Usa média móvel exponencial (EMA) para suavização
    avg_gain = gains.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = losses.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    last_valid_rsi = rsi.last_valid_index()
    if last_valid_rsi is None:
        raise ValueError("Não foi possível calcular um valor de RSI válido.")

    return rsi[last_valid_rsi]


@app.post("/analyze",
            response_model=CronosTechnicalOutput,
            responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
            dependencies=[Depends(get_api_key)])
async def analyze_rsi(request: AnalysisRequest):
    """
    Recebe uma lista de preços e retorna o RSI de 14 períodos.
    """
    try:
        rsi_value = calculate_manual_rsi(request.historical_prices)
        return CronosTechnicalOutput(asset=request.asset, rsi=rsi_value)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "Bad Request", "details": str(e), "source_agent": AgentName.CRONOS}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "details": str(e), "source_agent": AgentName.CRONOS}
        )

@app.get("/health", summary="Endpoint de Health Check")
def health():
    """Endpoint público para health checks."""
    return {"status": "ok"}