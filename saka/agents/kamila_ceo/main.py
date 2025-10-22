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
    # --- Lógica de Decisão Baseada em Regras ---
    athena_signal = data.athena_analysis.signal
    athena_confidence = data.athena_analysis.confidence

    print(f"Kamila processando dados para {data.asset}: Sinal='{athena_signal}', Confiança={athena_confidence:.2f}")

    # Definir o limiar de confiança para executar um trade
    CONFIDENCE_THRESHOLD = 0.75

    if athena_signal != 'hold' and athena_confidence >= CONFIDENCE_THRESHOLD:
        # Se o sinal não for 'hold' e a confiança for alta, preparar a ordem
        final_decision = KamilaFinalDecision(
            action="execute_trade",
            agent_target=AgentName.AETHERTRADER,
            asset=data.asset,
            trade_type="market",
            side=athena_signal,  # 'buy' ou 'sell'
            amount_usd=100.0
        )

        print(f"Decisão: EXECUTAR TRADE. Enviando ordem para Aethertrader: {final_decision.dict()}")

        # Fazer a chamada de API para o Aethertrader para executar o trade
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AETHERTRADER_URL}/execute_trade",
                    json=final_decision.dict(),
                    timeout=10.0
                )
                response.raise_for_status()

                receipt = response.json()
                print(f"Trade executado com sucesso. Recibo: {receipt}")

                return {
                    "status": "trade_executed",
                    "details": receipt
                }

        except httpx.RequestError as e:
            print(f"Erro ao se comunicar com Aethertrader: {e}")
            raise HTTPException(status_code=503, detail=f"Aethertrader indisponível: {e}")
        except Exception as e:
            print(f"Erro inesperado durante a execução: {e}")
            raise HTTPException(status_code=500, detail="Erro interno ao executar trade.")
    else:
        # Se o sinal for 'hold' ou a confiança for baixa, nenhuma ação é tomada
        reason = f"sinal de '{athena_signal}' com confiança insuficiente ({athena_confidence:.2f} < {CONFIDENCE_THRESHOLD})"
        if athena_signal == 'hold':
            reason = "sinal de 'hold' recebido de Athena"

        print(f"Decisão: MANTER (HOLD). Motivo: {reason}.")
        return {
            "status": "action_hold",
            "details": {
                "reason": reason,
                "asset": data.asset
            }
        }

@app.get("/health")
def health():
    return {"status": "ok"}