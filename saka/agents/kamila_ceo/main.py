import os
import httpx
from fastapi import FastAPI, Depends, HTTPException
from saka.shared.models import (
    ConsolidatedDataInput, KamilaFinalDecision, AgentName, TradeSignal, MacroImpact,
    GaiaPositionSizingRequest, GaiaPositionSizingResponse
)
from saka.shared.security import get_api_key

app = FastAPI(
    title="Kamila (CEO Agent)",
    description="Toma decisões de negociação com base em dados consolidados de outros agentes.",
    version="1.3.0" # Added Gaia integration for position sizing
)

GAIA_URL = os.getenv("GAIA_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
INTERNAL_API_HEADERS = {"X-Internal-API-Key": INTERNAL_API_KEY}

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput):
    """
    Lógica de decisão da Kamila, agora consultando Gaia para o dimensionamento da posição.
    """
    # 1. Veto de Risco do Sentinel
    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Sentinel): {data.sentinel_analysis.reason}")

    # 2. Veto de Evento Macroeconômico do Orion
    if data.orion_analysis.impact == MacroImpact.HIGH:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Orion): {data.orion_analysis.summary}")

    # 3. Lógica de Sinais Técnicos
    rsi = data.cronos_analysis.rsi
    trade_signal = None

    if rsi < 30:
        trade_signal = TradeSignal.BUY
    elif rsi > 70:
        trade_signal = TradeSignal.SELL

    # 4. Se houver um sinal, consultar Gaia para dimensionamento
    if trade_signal:
        try:
            async with httpx.AsyncClient() as client:
                gaia_request = GaiaPositionSizingRequest(asset=data.asset, entry_price=data.current_price)

                response = await client.post(
                    f"{GAIA_URL}/calculate_position_size",
                    json=gaia_request.model_dump(),
                    headers=INTERNAL_API_HEADERS,
                    timeout=10
                )
                response.raise_for_status()
                gaia_decision = GaiaPositionSizingResponse(**response.json())

                return KamilaFinalDecision(
                    action="execute_trade",
                    agent_target=AgentName.AETHERTRADER,
                    asset=data.asset,
                    trade_type="market",
                    side=trade_signal,
                    amount_usd=gaia_decision.amount_usd,
                    reason=f"SINAL DE {trade_signal.upper()}: RSI ({rsi:.2f}). {gaia_decision.reasoning}"
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Falha na comunicação com Gaia: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro durante o dimensionamento da posição com Gaia: {e}")

    # 5. Nenhuma condição atendida
    return KamilaFinalDecision(
        action="hold",
        reason=f"HOLD: Nenhum sinal claro. RSI ({rsi:.2f}) está neutro."
    )

@app.get("/health")
def health():
    return {"status": "ok"}