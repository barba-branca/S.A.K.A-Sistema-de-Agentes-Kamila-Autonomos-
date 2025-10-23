import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from saka.shared.models import (
    ConsolidatedDataInput,
    AthenaSentimentOutput,
    SentinelRiskOutput,
    CronosTechnicalOutput,
    OrionMacroOutput
)

app = FastAPI(title="S.A.K.A. Orchestrator")

KAMILA_URL = os.getenv("KAMILA_URL")
ATHENA_URL = os.getenv("ATHENA_URL")
SENTINEL_URL = os.getenv("SENTINEL_URL")
CRONOS_URL = os.getenv("CRONOS_URL")
ORION_URL = os.getenv("ORION_URL")

class CycleTriggerRequest(BaseModel):
    asset: str = "BTC/USD"

@app.post("/trigger_decision_cycle")
async def trigger_decision_cycle(request: CycleTriggerRequest):
    asset = request.asset
    async with httpx.AsyncClient() as client:
        try:
            tasks = [
                client.post(f"{ATHENA_URL}/analyze_sentiment", json={"asset": asset}),
                client.post(f"{SENTINEL_URL}/analyze_risk", json={"asset": asset}),
                client.post(f"{CRONOS_URL}/analyze_cycles", json={"asset": asset}),
                client.post(f"{ORION_URL}/analyze_macro", json={"market": "CRYPTO"})
            ]
            responses = await asyncio.gather(*tasks)
            for r in responses:
                r.raise_for_status()

            athena_data, sentinel_data, cronos_data, orion_data = [r.json() for r in responses]

            consolidated_data = ConsolidatedDataInput(
                asset=asset,
                athena_analysis=AthenaSentimentOutput(**athena_data),
                sentinel_analysis=SentinelRiskOutput(**sentinel_data),
                cronos_analysis=CronosTechnicalOutput(**cronos_data),
                orion_analysis=OrionMacroOutput(**orion_data)
            )

            kamila_response = await client.post(f"{KAMILA_URL}/decide", json=consolidated_data.dict(), timeout=15.0)
            kamila_response.raise_for_status()
            return kamila_response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com um agente: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no ciclo de decisão: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}