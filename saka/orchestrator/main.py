import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel

from saka.shared.models import ConsolidatedDataInput, AthenaSentimentOutput, SentinelRiskOutput, CronosTechnicalOutput

app = FastAPI(
    title="S.A.K.A. Orchestrator",
    description="Gerencia o fluxo de trabalho e a comunicação entre os agentes.",
    version="1.0.0"
)

# URLs dos agentes, injetadas via variáveis de ambiente
KAMILA_URL = os.getenv("KAMILA_URL")
ATHENA_URL = os.getenv("ATHENA_URL")
SENTINEL_URL = os.getenv("SENTINEL_URL")
CRONOS_URL = os.getenv("CRONOS_URL")

class CycleTriggerRequest(BaseModel):
    asset: str = "BTC/USD"

@app.post("/trigger_decision_cycle")
async def trigger_decision_cycle(request: CycleTriggerRequest):
    """
    Inicia um ciclo de decisão completo.
    1. Coleta dados dos agentes de análise (Athena, Sentinel).
    2. Consolida os dados.
    3. Envia os dados consolidados para Kamila tomar a decisão.
    """
    asset = request.asset
    print(f"Ciclo de decisão iniciado para o ativo: {asset}")

    async with httpx.AsyncClient() as client:
        try:
            # Coleta de dados em paralelo
            athena_task = client.post(f"{ATHENA_URL}/analyze_sentiment", json={"asset": asset})
            sentinel_task = client.post(f"{SENTINEL_URL}/analyze_risk", json={"asset": asset})
            cronos_task = client.post(f"{CRONOS_URL}/analyze_cycles", json={"asset": asset})

            responses = await asyncio.gather(athena_task, sentinel_task, cronos_task)

            # Validação e parsing das respostas
            athena_response, sentinel_response, cronos_response = responses
            athena_response.raise_for_status()
            sentinel_response.raise_for_status()
            cronos_response.raise_for_status()

            athena_data = AthenaSentimentOutput(**athena_response.json())
            sentinel_data = SentinelRiskOutput(**sentinel_response.json())
            cronos_data = CronosTechnicalOutput(**cronos_response.json())

            # Consolidação dos dados
            consolidated_data = ConsolidatedDataInput(
                asset=asset,
                athena_analysis=athena_data,
                sentinel_analysis=sentinel_data,
                cronos_analysis=cronos_data
            )

            print(f"Dados consolidados com sucesso para {asset}. Enviando para Kamila...")

            # Roteamento para Kamila
            kamila_response = await client.post(
                f"{KAMILA_URL}/decide",
                json=consolidated_data.dict(),
                timeout=15.0  # Timeout maior para a decisão
            )
            kamila_response.raise_for_status()

            print("Decisão recebida de Kamila.")
            return kamila_response.json()

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com um agente de análise: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro durante a coleta de dados: {e}")


@app.get("/health")
def health_check():
    """Verifica a saúde do serviço e a disponibilidade das URLs dos agentes."""
    return {
        "status": "ok",
        "kamila_url_configured": KAMILA_URL is not None,
        "athena_url_configured": ATHENA_URL is not None,
        "sentinel_url_configured": SENTINEL_URL is not None,
    }