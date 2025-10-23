from fastapi import FastAPI
from pydantic import BaseModel

from saka.shared.models import GaiaPortfolioImpactAnalysis, GaiaPortfolioAdjustment

app = FastAPI(
    title="S.A.K.A. Gaia (Diversification)",
    description="Agente de gestão de portfólio e diversificação.",
    version="1.0.0"
)

# Portfólio simulado (em um sistema real, isso seria um estado persistente)
SIMULATED_PORTFOLIO = {
    "total_value_usd": 10000.0,
    "asset_allocation": {
        "BTC/USD": 4000.0, # 40%
        "ETH/USD": 3000.0, # 30%
        "USD_CASH": 3000.0  # 30%
    }
}

@app.post("/analyze_portfolio_impact", response_model=GaiaPortfolioAdjustment)
async def analyze_portfolio_impact(analysis_input: GaiaPortfolioImpactAnalysis):
    """
    Recebe uma proposta de trade e analisa seu impacto no portfólio.

    Lógica de placeholder: Se um trade proposto for maior que 1% do
    valor total do portfólio, ele é reduzido para 1% para evitar
    concentração de risco.
    """
    MAX_ALLOCATION_PER_TRADE = 0.01 # 1% do portfólio por trade
    max_trade_value = SIMULATED_PORTFOLIO["total_value_usd"] * MAX_ALLOCATION_PER_TRADE

    adjusted_amount = analysis_input.proposed_amount_usd
    reasoning = "O tamanho proposto para a operação está dentro dos limites de alocação."

    if analysis_input.proposed_amount_usd > max_trade_value:
        adjusted_amount = max_trade_value
        reasoning = (
            f"O valor proposto de ${analysis_input.proposed_amount_usd:.2f} excede o limite de alocação por trade. "
            f"Ajustado para ${adjusted_amount:.2f} (1% do portfólio)."
        )

    return GaiaPortfolioAdjustment(
        adjusted_amount_usd=adjusted_amount,
        reasoning=reasoning
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}