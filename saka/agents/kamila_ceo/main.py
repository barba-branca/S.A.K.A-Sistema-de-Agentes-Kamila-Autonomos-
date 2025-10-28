import os
import httpx
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from saka.shared.models import (
    ConsolidatedDataInput, KamilaFinalDecision, AgentName, TradeSignal, MacroImpact, TradeType,
    GaiaPositionSizingRequest, GaiaPositionSizingResponse,
    TradeProposal, PolarisApproval
)
from saka.shared.security import get_api_key
from saka.shared.reporting import send_whatsapp_report

app = FastAPI(
    title="Kamila (CEO Agent)",
    description="Toma decisões de negociação e envia relatórios.",
    version="1.7.0"
)

GAIA_URL = os.getenv("GAIA_URL")
POLARIS_URL = os.getenv("POLARIS_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
INTERNAL_API_HEADERS = {"X-Internal-API-Key": INTERNAL_API_KEY}

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput, background_tasks: BackgroundTasks):
    # 1. Vetos de Risco
    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Sentinel): {data.sentinel_analysis.reason}")
    if data.orion_analysis.impact == MacroImpact.HIGH:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Orion): {data.orion_analysis.summary}")

    # 2. Geração de Sinal por Confluência
    cronos = data.cronos_analysis
    athena = data.athena_analysis
    is_buy_signal = cronos.rsi < 35 and cronos.is_bullish_crossover and athena.sentiment_score > 0.1
    is_sell_signal = cronos.rsi > 65 and cronos.is_bearish_crossover and athena.sentiment_score < -0.1

    final_signal = None
    if is_buy_signal: final_signal = TradeSignal.BUY
    elif is_sell_signal: final_signal = TradeSignal.SELL
    else:
        return KamilaFinalDecision(action="hold", reason=f"HOLD: Nenhuma confluência de sinais encontrada.")

    # 3. Revisão do Polaris
    try:
        async with httpx.AsyncClient() as client:
            proposal_reason = f"Sinal de {final_signal.upper()} por confluência."
            trade_proposal = TradeProposal(
                asset=data.asset, side=final_signal, trade_type=TradeType.MARKET,
                entry_price=data.current_price, reasoning=proposal_reason
            )
            polaris_response = await client.post(f"{POLARIS_URL}/review_trade", json=trade_proposal.model_dump(), headers=INTERNAL_API_HEADERS)
            polaris_response.raise_for_status()
            polaris_approval = PolarisApproval(**polaris_response.json())
            if not polaris_approval.decision_approved:
                return KamilaFinalDecision(action="hold", reason=polaris_approval.remarks)

            # 4. Dimensionamento do Gaia
            gaia_request = GaiaPositionSizingRequest(asset=data.asset, entry_price=data.current_price)
            gaia_response = await client.post(f"{GAIA_URL}/calculate_position_size", json=gaia_request.model_dump(), headers=INTERNAL_API_HEADERS)
            gaia_response.raise_for_status()
            gaia_decision = GaiaPositionSizingResponse(**gaia_response.json())

            # 5. Decisão Final e Relatório
            final_decision = KamilaFinalDecision(
                action="execute_trade", agent_target=AgentName.AETHERTRADER, asset=data.asset,
                trade_type=TradeType.MARKET, side=final_signal, amount_usd=gaia_decision.amount_usd,
                reason=f"{proposal_reason} | {polaris_approval.remarks} | {gaia_decision.reasoning}"
            )
            report_body = f"🚨 S.A.K.A. 🚨\n\nOrdem de {final_signal.upper()} para {data.asset} AUTORIZADA.\n\nValor: ${gaia_decision.amount_usd:,.2f}"
            background_tasks.add_task(send_whatsapp_report, report_body)
            return final_decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na fase de revisão/dimensionamento: {e}")

@app.get("/health")
def health(): return {"status": "ok"}