import os
import httpx
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from saka.shared.models import (
    ConsolidatedDataInput, KamilaFinalDecision, AgentName, TradeSignal, MacroImpact,
    GaiaPositionSizingRequest, GaiaPositionSizingResponse, AthenaSentimentOutput
)
from saka.shared.security import get_api_key
from saka.shared.reporting import send_whatsapp_report

app = FastAPI(
    title="Kamila (CEO Agent)",
    description="Toma decisões de negociação e envia relatórios.",
    version="1.5.0" # Added Athena sentiment filter
)

GAIA_URL = os.getenv("GAIA_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
INTERNAL_API_HEADERS = {"X-Internal-API-Key": INTERNAL_API_KEY}

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput, background_tasks: BackgroundTasks):
    """
    Lógica de decisão da Kamila, agora usando o sentimento do Athena como filtro.
    """
    # 1. Vetos de Risco
    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Sentinel): {data.sentinel_analysis.reason}")
    if data.orion_analysis.impact == MacroImpact.HIGH:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Orion): {data.orion_analysis.summary}")

    # 2. Geração de Sinal Técnico
    rsi = data.cronos_analysis.rsi
    technical_signal = None
    if rsi < 30:
        technical_signal = TradeSignal.BUY
    elif rsi > 70:
        technical_signal = TradeSignal.SELL

    if not technical_signal:
        return KamilaFinalDecision(action="hold", reason=f"HOLD: Nenhum sinal técnico claro. RSI ({rsi:.2f}) está neutro.")

    # 3. Filtro de Confirmação de Sentimento
    sentiment_score = data.athena_analysis.sentiment_score
    if technical_signal == TradeSignal.BUY and sentiment_score < 0.1:
        return KamilaFinalDecision(action="hold", reason=f"HOLD: Sinal de compra do Cronos (RSI={rsi:.2f}) não confirmado pelo sentimento do Athena (Score={sentiment_score:.2f}).")
    if technical_signal == TradeSignal.SELL and sentiment_score > -0.1:
        return KamilaFinalDecision(action="hold", reason=f"HOLD: Sinal de venda do Cronos (RSI={rsi:.2f}) não confirmado pelo sentimento do Athena (Score={sentiment_score:.2f}).")

    # 4. Se o sinal passou por todos os filtros, consultar Gaia para dimensionamento
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

            final_decision = KamilaFinalDecision(
                action="execute_trade",
                agent_target=AgentName.AETHERTRADER,
                asset=data.asset,
                trade_type="market",
                side=technical_signal,
                amount_usd=gaia_decision.amount_usd,
                reason=f"SINAL DE {technical_signal.upper()} (RSI={rsi:.2f}) confirmado por Sentimento (Score={sentiment_score:.2f}). {gaia_decision.reasoning}"
            )

            report_body = (
                f"🚨 ALERTA S.A.K.A. 🚨\n\n"
                f"Ordem de {technical_signal.upper()} para {data.asset} autorizada.\n\n"
                f"Valor: ${gaia_decision.amount_usd:,.2f}\n"
                f"Motivo: {final_decision.reason}"
            )
            background_tasks.add_task(send_whatsapp_report, report_body)

            return final_decision

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Falha na comunicação com Gaia: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante o dimensionamento da posição com Gaia: {e}")