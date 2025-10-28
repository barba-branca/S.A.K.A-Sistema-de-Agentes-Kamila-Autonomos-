from fastapi import FastAPI, Depends
from saka.shared.security import get_api_key
from saka.shared.models import GaiaPositionSizingRequest, GaiaPositionSizingResponse

app = FastAPI(title="Gaia (Portfolio Management Agent)")

TOTAL_CAPITAL_USD = 10000.00
RISK_PER_TRADE_PCT = 0.02

@app.post("/calculate_position_size", response_model=GaiaPositionSizingResponse, dependencies=[Depends(get_api_key)])
async def calculate_position_size(request: GaiaPositionSizingRequest):
    position_size_usd = TOTAL_CAPITAL_USD * RISK_PER_TRADE_PCT
    reasoning = f"Estratégia de Risco Fixo: Arriscando {RISK_PER_TRADE_PCT:.0%} de ${TOTAL_CAPITAL_USD:,.2f}"
    return GaiaPositionSizingResponse(
        asset=request.asset, amount_usd=position_size_usd, reasoning=reasoning
    )

@app.get("/health")
def health(): return {"status": "ok"}