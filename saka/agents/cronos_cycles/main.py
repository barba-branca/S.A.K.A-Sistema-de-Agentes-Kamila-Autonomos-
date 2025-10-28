from fastapi import FastAPI, Depends, HTTPException
from saka.shared.models import AnalysisRequest, CronosTechnicalOutput, ErrorResponse, AgentName
from saka.shared.security import get_api_key
import pandas as pd

app = FastAPI(
    title="Cronos (Technical Analysis Agent)",
    description="Calcula indicadores técnicos (RSI, MACD) manualmente a partir de dados de preços.",
    version="2.1.0"
)

def calculate_manual_rsi(prices: pd.Series, period: int = 14) -> float:
    if len(prices) < period + 1:
        raise ValueError(f"Dados insuficientes para RSI. Necessita de {period + 1}, tem {len(prices)}.")
    delta = prices.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    avg_gain = gains.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = losses.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_manual_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> dict:
    if len(prices) < slow_period:
        raise ValueError(f"Dados insuficientes para MACD. Necessita de {slow_period}, tem {len(prices)}.")
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd_line": macd_line.iloc[-1],
        "signal_line": signal_line.iloc[-1],
        "histogram": histogram.iloc[-1],
        "is_bullish_crossover": histogram.iloc[-1] > 0 and histogram.iloc[-2] < 0,
        "is_bearish_crossover": histogram.iloc[-1] < 0 and histogram.iloc[-2] > 0,
    }

@app.post("/analyze",
            response_model=CronosTechnicalOutput,
            dependencies=[Depends(get_api_key)])
async def analyze_technical_indicators(request: AnalysisRequest):
    try:
        price_series = pd.Series(request.historical_prices, dtype=float)

        rsi_value = calculate_manual_rsi(price_series)
        macd_values = calculate_manual_macd(price_series)

        return CronosTechnicalOutput(
            asset=request.asset,
            rsi=rsi_value,
            **macd_values
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular indicadores: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}