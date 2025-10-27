from fastapi import FastAPI, Depends
from saka.shared.models import ConsolidatedDataInput, KamilaFinalDecision, AgentName, TradeSignal
from saka.shared.security import get_api_key

app = FastAPI(
    title="Kamila (CEO Agent)",
    description="Toma decisões de negociação com base em dados consolidados de outros agentes.",
    version="1.1.0"
)

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput):
    """
    Lógica de decisão da Kamila, usando o RSI do Cronos.
    """
    # 1. Veto de Risco do Sentinel
    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(
            action="hold",
            reason=f"VETO: Sentinel bloqueou a negociação. {data.sentinel_analysis.reason}"
        )

    # 2. Lógica de Decisão Baseada em RSI
    rsi = data.cronos_analysis.rsi

    if rsi < 30:
        return KamilaFinalDecision(
            action="execute_trade",
            agent_target=AgentName.AETHERTRADER,
            asset=data.asset,
            trade_type="market",
            side=TradeSignal.BUY,
            amount_usd=100.0,
            reason=f"SINAL DE COMPRA: RSI ({rsi:.2f}) indica ativo sobrevendido."
        )

    if rsi > 70:
        return KamilaFinalDecision(
            action="execute_trade",
            agent_target=AgentName.AETHERTRADER,
            asset=data.asset,
            trade_type="market",
            side=TradeSignal.SELL,
            amount_usd=100.0,
            reason=f"SINAL DE VENDA: RSI ({rsi:.2f}) indica ativo sobrecomprado."
        )

    # 3. Nenhuma condição atendida
    return KamilaFinalDecision(
        action="hold",
        reason=f"HOLD: Nenhum sinal claro. RSI ({rsi:.2f}) está neutro."
    )

@app.get("/health")
def health():
    return {"status": "ok"}