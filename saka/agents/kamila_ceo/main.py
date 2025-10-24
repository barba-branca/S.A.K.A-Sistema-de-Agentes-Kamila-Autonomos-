from fastapi import FastAPI, Depends
from saka.shared.models import ConsolidatedDataInput, KamilaFinalDecision, AgentName
from saka.shared.security import get_api_key

app = FastAPI(title="Kamila (CEO Agent)")

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput):
    """
    Lógica de decisão da Kamila (placeholder).
    Recebe dados consolidados e retorna a decisão final.
    """
    # Lógica de decisão principal viria aqui.
    # Ex: if data.sentinel_analysis.can_trade and ...

    print(f"Kamila recebeu dados para {data.asset}. Risco do Sentinel: {data.sentinel_analysis.risk_level:.2f}")

    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(
            action="hold",
            reason=f"Decisão de HOLD devido ao veto do Sentinel: {data.sentinel_analysis.reason}"
        )

    # Se todas as condições forem atendidas, envia para execução.
    return KamilaFinalDecision(
        action="execute_trade",
        agent_target=AgentName.AETHERTRADER,
        asset=data.asset,
        trade_type="market",
        side="buy", # Lógica para decidir o lado viria aqui
        amount_usd=100.0, # Lógica de dimensionamento viria aqui
        reason="Sinal de compra forte com risco aceitável."
    )

@app.get("/health")
def health():
    return {"status": "ok"}