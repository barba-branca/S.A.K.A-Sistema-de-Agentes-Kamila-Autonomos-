from fastapi import FastAPI, Depends, HTTPException
from saka.shared.models import AnalysisRequest, SentinelRiskOutput
from saka.shared.security import get_api_key
from saka.shared.logging_config import configure_logging, get_logger
import numpy as np

configure_logging()
logger = get_logger("sentinel_risk")

app = FastAPI(title="Sentinel (Risk Agent)")

VOLATILITY_THRESHOLD = 0.05

@app.post("/analyze", response_model=SentinelRiskOutput, dependencies=[Depends(get_api_key)])
async def analyze_risk(request: AnalysisRequest):
    logger.info("Recebida requisição de análise de risco", asset=request.asset)
    if not request.historical_prices or len(request.historical_prices) < 10:
        logger.warning("Análise de risco falhou: dados insuficientes", asset=request.asset)
        raise HTTPException(status_code=400, detail="Dados insuficientes para análise de risco.")
    try:
        prices = np.array(request.historical_prices)
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        can_trade = volatility <= VOLATILITY_THRESHOLD

        if not can_trade:
            logger.warning("ALERTA DE ALTO RISCO: Volatilidade excede o limiar.",
                           asset=request.asset, volatility=volatility, threshold=VOLATILITY_THRESHOLD)
        else:
            logger.info("Análise de risco concluída, volatilidade dentro dos limites.",
                        asset=request.asset, volatility=volatility)

        return SentinelRiskOutput(
            asset=request.asset,
            risk_level=min(volatility / (VOLATILITY_THRESHOLD * 2), 1.0),
            volatility=volatility,
            can_trade=can_trade,
            reason=f"Volatilidade: {volatility:.4f}"
        )
    except Exception as e:
        logger.error("Erro inesperado na análise de risco", asset=request.asset, exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health(): return {"status": "ok"}
