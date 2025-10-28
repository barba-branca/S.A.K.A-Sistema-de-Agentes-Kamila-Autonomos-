import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from saka.shared.models import (
    AnalysisRequest, ConsolidatedDataInput, KamilaFinalDecision,
    SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput, AthenaSentimentOutput
)
from saka.shared.security import get_api_key

app = FastAPI(title="S.A.K.A. Orchestrator")

# URLs e Chave de API
URLS = {
    "SENTINEL": os.getenv("SENTINEL_URL"), "CRONOS": os.getenv("CRONOS_URL"),
    "ORION": os.getenv("ORION_URL"), "ATHENA": os.getenv("ATHENA_URL"),
    "KAMILA": os.getenv("KAMILA_URL")
}
INTERNAL_API_HEADERS = {"X-Internal-API-Key": os.getenv("INTERNAL_API_KEY")}

async def get_kamila_decision(request: AnalysisRequest) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = [
            client.post(f"{URLS['SENTINEL']}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{URLS['CRONOS']}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{URLS['ORION']}/analyze_events", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{URLS['ATHENA']}/analyze_sentiment", json=request.dict(), headers=INTERNAL_API_HEADERS)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for i, r in enumerate(responses):
            agent_name = list(URLS.keys())[i]
            if isinstance(r, Exception): raise HTTPException(status_code=503, detail=f"Falha na comunicação com {agent_name}: {r}")
            r.raise_for_status()
            results[agent_name] = r.json()

        consolidated_input = ConsolidatedDataInput(
            asset=request.asset, current_price=request.historical_prices[-1],
            sentinel_analysis=SentinelRiskOutput(**results["SENTINEL"]),
            cronos_analysis=CronosTechnicalOutput(**results["CRONOS"]),
            orion_analysis=OrionMacroOutput(**results["ORION"]),
            athena_analysis=AthenaSentimentOutput(**results["ATHENA"])
        )

        kamila_response = await client.post(f"{URLS['KAMILA']}/decide", json=consolidated_input.dict(), headers=INTERNAL_API_HEADERS)
        kamila_response.raise_for_status()
        return kamila_response.json()

@app.post("/trigger_decision_cycle_sync", response_model=KamilaFinalDecision, dependencies=[Depends(get_api_key)])
async def trigger_decision_cycle_sync(request: AnalysisRequest):
    return await get_kamila_decision(request)

@app.post("/trigger_decision_cycle", status_code=202)
async def trigger_decision_cycle(request: AnalysisRequest, background_tasks: BackgroundTasks):
    async def wrapper():
        try:
            await get_kamila_decision(request)
        except Exception as e:
            print(f"ERRO NO FLUXO EM BACKGROUND: {e}")
    background_tasks.add_task(wrapper)
    return {"message": "Ciclo de decisão iniciado."}

@app.get("/health")
def health(): return {"status": "ok"}