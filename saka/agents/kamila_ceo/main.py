from fastapi import FastAPI, Depends
from saka.shared.models import ConsolidatedDataInput, KamilaFinalDecision, AgentName, TradeSignal, MacroImpact
from saka.shared.security import get_api_key

app = FastAPI(
    title="Kamila (CEO Agent)",
    description="Toma decisões de negociação com base em dados consolidados de outros agentes.",
    version="1.2.0" # Added Orion's veto logic
)

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput):
    """
    Lógica de decisão da Kamila, agora incorporando o veto macroeconômico do Orion.
    """
    # 1. Veto de Risco do Sentinel (Prioridade Máxima)
    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(
            action="hold",
            reason=f"VETO (Sentinel): {data.sentinel_analysis.reason}"
        )

    # 2. Veto de Evento Macroeconômico do Orion (Segunda Prioridade)
    if data.orion_analysis.impact == MacroImpact.HIGH:
        return KamilaFinalDecision(
            action="hold",
            reason=f"VETO (Orion): {data.orion_analysis.summary}"
        )

    # 3. Lógica de Sinais Técnicos (Apenas se não houver vetos)
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

    # 4. Nenhuma condição atendida
    return KamilaFinalDecision(
        action="hold",
        reason=f"HOLD: Nenhum sinal claro. RSI ({rsi:.2f}) está neutro. Impacto macro: {data.orion_analysis.impact}."
    )

@app.get("/health")
def health():
    return {"status": "ok"}