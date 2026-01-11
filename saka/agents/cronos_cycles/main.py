from fastapi import FastAPI, Depends, HTTPException
from saka.shared.models import AnalysisRequest, CronosTechnicalOutput, ErrorResponse, AgentName
from saka.shared.security import get_api_key
from saka.shared.logging_config import configure_logging, get_logger
import pandas as pd

configure_logging()
logger = get_logger("cronos_cycles")

app = FastAPI(
    title="Cronos (Technical Analysis Agent)",
    description="Calcula indicadores técnicos (RSI, MACD) manualmente.",
    version="2.1.0"
)

def calculate_manual_rsi(prices: pd.Series, period: int = 14) -> float:
    # ... (lógica omitida por brevidade) ...
    if len(prices) < period + 1: raise ValueError(f"Dados insuficientes para RSI.")
    delta = prices.diff()
    gains = delta.where(delta > 0, 0); losses = -delta.where(delta < 0, 0)
    avg_gain = gains.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = losses.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return (100 - (100 / (1 + rs))).iloc[-1]

def calculate_manual_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    # ... (lógica omitida por brevidade) ...
    if len(prices) < slow: raise ValueError(f"Dados insuficientes para MACD.")
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": macd_line.iloc[-1], "signal_line": signal_line.iloc[-1],
        "histogram": histogram.iloc[-1],
        "is_bullish_crossover": histogram.iloc[-1] > 0 and histogram.iloc[-2] < 0,
        "is_bearish_crossover": histogram.iloc[-1] < 0 and histogram.iloc[-2] > 0,
    }

@app.post("/analyze", response_model=CronosTechnicalOutput, dependencies=[Depends(get_api_key)])
async def analyze_technical_indicators(request: AnalysisRequest):
    logger.info("Recebida requisição de análise técnica", asset=request.asset)
    try:
        price_series = pd.Series(request.historical_prices, dtype=float)
        rsi_value = calculate_manual_rsi(price_series)
        macd_values = calculate_manual_macd(price_series)
        logger.info("Análise técnica concluída", asset=request.asset, rsi=rsi_value, macd_histogram=macd_values['histogram'])
        return CronosTechnicalOutput(asset=request.asset, rsi=rsi_value, **macd_values)
    except ValueError as e:
        logger.warning("Análise falhou devido a dados insuficientes", asset=request.asset, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erro inesperado ao calcular indicadores", asset=request.asset, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular indicadores: {e}")

@app.get("/health")
def health(): return {"status": "ok"}
