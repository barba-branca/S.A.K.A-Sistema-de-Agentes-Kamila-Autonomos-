from fastapi import FastAPI, HTTPException
import os
import httpx
import sys
from pydantic import BaseModel

# Adiciona o caminho para encontrar o módulo 'shared'
sys.path.append('../')
from shared.models import ConsolidatedDataInput, KamilaFinalDecision, AgentName

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
    # Lógica de decisão (placeholder)
    print(f"Kamila recebeu dados para {data.asset}. Sentimento: {data.athena_analysis.signal}")

    # Placeholder: Sempre decide comprar
    final_decision = KamilaFinalDecision(
        action="execute_trade",
        agent_target=AgentName.AETHERTRADER,
        asset=data.asset,
        trade_type="market",
        side="buy",
        amount_usd=100.0
    )

    # Fazer a chamada de API para o Aethertrader para executar o trade
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AETHERTRADER_URL}/execute_trade",
                json=final_decision.dict(),
                timeout=10.0
            )
            response.raise_for_status()  # Lança uma exceção para respostas 4xx/5xx

            receipt = response.json()
            print(f"Trade executado com sucesso pelo Aethertrader. Recibo: {receipt}")

            return {
                "status": "trade_executed",
                "details": receipt
            }

    except httpx.RequestError as e:
        print(f"Erro ao tentar se comunicar com o Aethertrader: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Não foi possível executar o trade. O agente Aethertrader está indisponível. Erro: {e}"
        )
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a execução do trade: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar a execução do trade.")

@app.get("/health")
def health():
    return {"status": "ok"}