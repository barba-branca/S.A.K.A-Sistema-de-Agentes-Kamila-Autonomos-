from fastapi import FastAPI
from saka.shared.models import GaiaPortfolioImpactAnalysis, GaiaPortfolioAdjustment

app = FastAPI(title="Gaia (Diversification)")

SIMULATED_PORTFOLIO = {
    "total_value_usd": 10000.0,
    "asset_allocation": {"BTC/USD": 4000.0, "ETH/USD": 3000.0, "USD_CASH": 3000.0}
}

@app.post("/analyze_portfolio_impact", response_model=GaiaPortfolioAdjustment)
async def analyze_portfolio_impact(analysis_input: GaiaPortfolioImpactAnalysis):
    MAX_ALLOCATION_PER_TRADE = 0.01
    max_trade_value = SIMULATED_PORTFOLIO["total_value_usd"] * MAX_ALLOCATION_PER_TRADE
    adjusted_amount = analysis_input.proposed_amount_usd
    reasoning = "O tamanho proposto para a operação está dentro dos limites de alocação."
    if analysis_input.proposed_amount_usd > max_trade_value:
        adjusted_amount = max_trade_value
        reasoning = f"Valor proposto de ${analysis_input.proposed_amount_usd:.2f} excede o limite. Ajustado para ${adjusted_amount:.2f}."
    return GaiaPortfolioAdjustment(adjusted_amount_usd=adjusted_amount, reasoning=reasoning)

@app.get("/health")
def health():
    return {"status": "ok"}