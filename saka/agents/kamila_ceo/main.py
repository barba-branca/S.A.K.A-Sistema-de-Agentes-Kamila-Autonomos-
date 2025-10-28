import os
import httpx
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from saka.shared.models import (
    ConsolidatedDataInput, KamilaFinalDecision, AgentName, TradeSignal, MacroImpact, TradeType,
    GaiaPositionSizingRequest, GaiaPositionSizingResponse, AthenaSentimentOutput,
    TradeProposal, PolarisApproval
)
from saka.shared.security import get_api_key
from saka.shared.reporting import send_whatsapp_report

app = FastAPI(
    title="Kamila (CEO Agent)",
    description="Toma decisões de negociação e envia relatórios.",
    version="1.6.1" # Bug fix in decision logic
)

GAIA_URL = os.getenv("GAIA_URL")
POLARIS_URL = os.getenv("POLARIS_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
INTERNAL_API_HEADERS = {"X-Internal-API-Key": INTERNAL_API_KEY}

@app.post("/decide",
            response_model=KamilaFinalDecision,
            dependencies=[Depends(get_api_key)])
async def make_decision(data: ConsolidatedDataInput, background_tasks: BackgroundTasks):
    """
    Lógica de decisão da Kamila, com fluxo hierárquico corrigido.
    """
    # 1. Vetos de Risco
    if not data.sentinel_analysis.can_trade:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Sentinel): {data.sentinel_analysis.reason}")
    if data.orion_analysis.impact == MacroImpact.HIGH:
        return KamilaFinalDecision(action="hold", reason=f"VETO (Orion): {data.orion_analysis.summary}")

    # 2. Geração de Sinal e Filtros
    rsi = data.cronos_analysis.rsi
    sentiment_score = data.athena_analysis.sentiment_score

    # Condição de Compra: RSI baixo E sentimento positivo
    is_buy_signal = rsi < 30 and sentiment_score > 0.1
    # Condição de Venda: RSI alto E sentimento negativo
    is_sell_signal = rsi > 70 and sentiment_score < -0.1

    final_signal = None
    if is_buy_signal:
        final_signal = TradeSignal.BUY
    elif is_sell_signal:
        final_signal = TradeSignal.SELL
    else:
        # Se nenhuma condição de trade for atendida, a decisão é HOLD.
        reason = f"HOLD: Nenhum sinal claro ou confirmado. RSI={rsi:.2f}, Sentimento={sentiment_score:.2f}"
        # Adiciona o motivo do filtro de sentimento se aplicável
        if rsi < 30 and not is_buy_signal:
            reason = f"HOLD: Sinal de compra do Cronos (RSI={rsi:.2f}) não confirmado pelo sentimento do Athena (Score={sentiment_score:.2f})."
        elif rsi > 70 and not is_sell_signal:
            reason = f"HOLD: Sinal de venda do Cronos (RSI={rsi:.2f}) não confirmado pelo sentimento do Athena (Score={sentiment_score:.2f})."
        return KamilaFinalDecision(action="hold", reason=reason)

    # 3. Se houver um sinal final, submeter para revisão do Polaris
    try:
        async with httpx.AsyncClient() as client:
            proposal_reason = f"Sinal de {final_signal.upper()} (RSI={rsi:.2f}) confirmado por Sentimento (Score={sentiment_score:.2f})."
            trade_proposal = TradeProposal(
                asset=data.asset, side=final_signal, trade_type=TradeType.MARKET,
                entry_price=data.current_price, reasoning=proposal_reason
            )

            polaris_response = await client.post(f"{POLARIS_URL}/review_trade", json=trade_proposal.model_dump(), headers=INTERNAL_API_HEADERS, timeout=10)
            polaris_response.raise_for_status()
            polaris_approval = PolarisApproval(**polaris_response.json())

            if not polaris_approval.decision_approved:
                return KamilaFinalDecision(action="hold", reason=polaris_approval.remarks)

            # 4. Se aprovado, consultar Gaia para dimensionamento
            gaia_request = GaiaPositionSizingRequest(asset=data.asset, entry_price=data.current_price)
            gaia_response = await client.post(f"{GAIA_URL}/calculate_position_size", json=gaia_request.model_dump(), headers=INTERNAL_API_HEADERS, timeout=10)
            gaia_response.raise_for_status()
            gaia_decision = GaiaPositionSizingResponse(**gaia_response.json())

            final_decision = KamilaFinalDecision(
                action="execute_trade", agent_target=AgentName.AETHERTRADER, asset=data.asset,
                trade_type=TradeType.MARKET, side=final_signal, amount_usd=gaia_decision.amount_usd,
                reason=f"{proposal_reason} Aprovado por Polaris. {gaia_decision.reasoning}"
            )

            report_body = f"🚨 ALERTA S.A.K.A. 🚨\n\nOrdem de {final_signal.upper()} para {data.asset} AUTORIZADA.\n\nValor: ${gaia_decision.amount_usd:,.2f}\nMotivo: {final_decision.reason}"
            background_tasks.add_task(send_whatsapp_report, report_body)

            return final_decision

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Falha na comunicação com um agente de suporte (Polaris ou Gaia): {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante a fase de revisão/dimensionamento: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}