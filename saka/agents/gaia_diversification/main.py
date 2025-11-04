from fastapi import FastAPI, Depends
from saka.shared.security import get_api_key
from saka.shared.models import GaiaPositionSizingRequest, GaiaPositionSizingResponse
from saka.shared.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger("gaia_diversification")

app = FastAPI(title="Gaia (Portfolio Management Agent)")

TOTAL_CAPITAL_USD = 10000.00
RISK_PER_TRADE_PCT = 0.02

@app.post("/calculate_position_size", response_model=GaiaPositionSizingResponse, dependencies=[Depends(get_api_key)])
async def calculate_position_size(request: GaiaPositionSizingRequest):
    logger.info("Recebida requisição de dimensionamento de posição", asset=request.asset)

    position_size_usd = TOTAL_CAPITAL_USD * RISK_PER_TRADE_PCT
    reasoning = f"Estratégia de Risco Fixo: {RISK_PER_TRADE_PCT:.0%} de ${TOTAL_CAPITAL_USD:,.2f}"

    logger.info("Dimensionamento de posição calculado", asset=request.asset, amount_usd=position_size_usd)

    return GaiaPositionSizingResponse(
        asset=request.asset, amount_usd=position_size_usd, reasoning=reasoning
    )

@app.get("/health")
def health(): return {"status": "ok"}
