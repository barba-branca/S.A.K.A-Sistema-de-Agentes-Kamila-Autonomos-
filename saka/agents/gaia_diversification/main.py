from fastapi import FastAPI, Depends
from saka.shared.security import get_api_key
from saka.shared.models import GaiaPositionSizingRequest, GaiaPositionSizingResponse

app = FastAPI(
    title="Gaia (Portfolio Management Agent)",
    description="Calcula o dimensionamento da posição para novas ordens de trade.",
    version="1.1.0" # Implemented realistic sizing logic
)

# --- Configurações de Gerenciamento de Risco (Simuladas) ---
TOTAL_CAPITAL_USD = 10000.00
RISK_PER_TRADE_PCT = 0.02 # Arriscar 2% do capital por trade

@app.post("/calculate_position_size",
            response_model=GaiaPositionSizingResponse,
            dependencies=[Depends(get_api_key)])
async def calculate_position_size(request: GaiaPositionSizingRequest):
    """
    Calcula o tamanho da posição com base em uma regra de risco fixo.
    """
    # Calcula o valor em USD a ser arriscado no trade
    amount_to_risk_usd = TOTAL_CAPITAL_USD * RISK_PER_TRADE_PCT

    # Em um sistema real, usaríamos o 'stop_loss_price' para calcular o número de unidades.
    # Ex: units = amount_to_risk_usd / (entry_price - stop_loss_price)
    # E então, amount_usd = units * entry_price.
    # Para esta simulação, vamos definir o tamanho da posição como o valor a ser arriscado.
    position_size_usd = amount_to_risk_usd

    reasoning = (
        f"Estratégia de Risco Fixo: Arriscando {RISK_PER_TRADE_PCT:.0%} de "
        f"${TOTAL_CAPITAL_USD:,.2f} = ${position_size_usd:,.2f}"
    )

    return GaiaPositionSizingResponse(
        asset=request.asset,
        amount_usd=position_size_usd,
        reasoning=reasoning
    )

@app.get("/health", summary="Endpoint de Health Check")
def health():
    """Endpoint público para health checks."""
    return {"status": "ok"}