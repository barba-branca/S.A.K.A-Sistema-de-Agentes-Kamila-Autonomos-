from fastapi import FastAPI, HTTPException
import os
import httpx
import sys
from pydantic import BaseModel

from saka.shared.models import ConsolidatedDataInput, KamilaFinalDecision, AgentName

app = FastAPI(title="Kamila (CEO)")

# URLs dos outros agentes
AETHERTRADER_URL = os.getenv("AETHERTRADER_URL", "http://aethertrader-manager:8000")

class DecisionResponse(BaseModel):
    status: str
    details: dict

@app.post("/decide", response_model=DecisionResponse)
async def make_decision(data: ConsolidatedDataInput):
    """
    Endpoint de placeholder para a lógica de decisão de Kamila.
    A lógica de chamada ao Aethertrader será adicionada aqui mais tarde.
    """
    # --- Lógica de Decisão Multifatorial ---
    athena_signal = data.athena_analysis.signal
    athena_confidence = data.athena_analysis.confidence
    cronos_rsi = data.cronos_analysis.rsi

    print(
        f"Kamila processando dados para {data.asset}: "
        f"Sinal Athena='{athena_signal}', Confiança={athena_confidence:.2f}, RSI Cronos={cronos_rsi:.2f}"
    )

    CONFIDENCE_THRESHOLD = 0.75
    RSI_OVERSOLD = 30.0
    RSI_OVERBOUGHT = 70.0

    trade_decision = None
    reason = "Critérios não atendidos."

    if athena_signal == 'buy' and athena_confidence >= CONFIDENCE_THRESHOLD and cronos_rsi < RSI_OVERSOLD:
        reason = f"Sinal de COMPRA forte (confiança {athena_confidence:.2f}) e ativo SOBREVENDIDO (RSI {cronos_rsi:.2f})."
        trade_decision = 'buy'
    elif athena_signal == 'sell' and athena_confidence >= CONFIDENCE_THRESHOLD and cronos_rsi > RSI_OVERBOUGHT:
        reason = f"Sinal de VENDA forte (confiança {athena_confidence:.2f}) e ativo SOBRECOMPRADO (RSI {cronos_rsi:.2f})."
        trade_decision = 'sell'
    else:
        # Lógica para HOLD
        if athena_signal == 'hold':
            reason = "Sinal de Athena é 'hold'."
        elif athena_confidence < CONFIDENCE_THRESHOLD:
            reason = f"Confiança de Athena ({athena_confidence:.2f}) abaixo do limiar."
        elif athena_signal == 'buy' and cronos_rsi >= RSI_OVERSOLD:
            reason = f"Sinal de compra, mas RSI ({cronos_rsi:.2f}) não indica sobrevenda."
        elif athena_signal == 'sell' and cronos_rsi <= RSI_OVERBOUGHT:
            reason = f"Sinal de venda, mas RSI ({cronos_rsi:.2f}) não indica sobrecompra."

        print(f"Decisão: MANTER (HOLD). Motivo: {reason}")
        return {"status": "action_hold", "details": {"reason": reason, "asset": data.asset}}

    # Se uma decisão de trade foi tomada, preparar e enviar a ordem
    final_decision = KamilaFinalDecision(
        action="execute_trade",
        agent_target=AgentName.AETHERTRADER,
        asset=data.asset,
        trade_type="market",
        side=trade_decision,
        amount_usd=100.0
    )

    print(f"Decisão: EXECUTAR TRADE ({trade_decision.upper()}). Motivo: {reason}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{AETHERTRADER_URL}/execute_trade", json=final_decision.dict(), timeout=10.0)
            response.raise_for_status()
            receipt = response.json()
            print(f"Trade executado com sucesso. Recibo: {receipt}")
            return {"status": "trade_executed", "details": receipt}
    except httpx.RequestError as e:
        print(f"Erro ao se comunicar com Aethertrader: {e}")
        raise HTTPException(status_code=503, detail=f"Aethertrader indisponível: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}