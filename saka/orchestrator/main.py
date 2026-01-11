import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from saka.shared.models import (
    AnalysisRequest, ConsolidatedDataInput, KamilaFinalDecision,
    SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput, AthenaSentimentOutput
)
from saka.shared.security import get_api_key
from saka.shared.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger("orchestrator")

app = FastAPI(title="S.A.K.A. Orchestrator")

URLS = {name: os.getenv(f"{name}_URL") for name in ["SENTINEL", "CRONOS", "ORION", "ATHENA", "KAMILA"]}
INTERNAL_API_HEADERS = {"X-Internal-API-Key": os.getenv("INTERNAL_API_KEY")}

async def get_kamila_decision(request: AnalysisRequest) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = {
            "SENTINEL": client.post(f"{URLS['SENTINEL']}/analyze", json=request.model_dump(), headers=INTERNAL_API_HEADERS),
            "CRONOS": client.post(f"{URLS['CRONOS']}/analyze", json=request.model_dump(), headers=INTERNAL_API_HEADERS),
            "ORION": client.post(f"{URLS['ORION']}/analyze_events", json=request.model_dump(), headers=INTERNAL_API_HEADERS),
            "ATHENA": client.post(f"{URLS['ATHENA']}/analyze_sentiment", json=request.model_dump(), headers=INTERNAL_API_HEADERS)
        }

        responses = await asyncio.gather(*tasks.values(), return_exceptions=True)

        results = {}
        for agent_name, response in zip(tasks.keys(), responses):
            if isinstance(response, Exception):
                logger.error("Falha na comunicação com agente", agent=agent_name, error=str(response))
                raise HTTPException(status_code=503, detail=f"Falha na comunicação com o agente {agent_name}")

            response.raise_for_status()
            results[agent_name] = response.json()
            logger.info("Análise recebida", agent=agent_name, analysis=results[agent_name])

        consolidated_input = ConsolidatedDataInput(
            asset=request.asset, current_price=request.historical_prices[-1],
            sentinel_analysis=SentinelRiskOutput(**results["SENTINEL"]),
            cronos_analysis=CronosTechnicalOutput(**results["CRONOS"]),
            orion_analysis=OrionMacroOutput(**results["ORION"]),
            athena_analysis=AthenaSentimentOutput(**results["ATHENA"])
        )

        logger.info("Enviando dados consolidados para Kamila", asset=request.asset)
        kamila_response = await client.post(f"{URLS['KAMILA']}/decide", json=consolidated_input.model_dump(), headers=INTERNAL_API_HEADERS)
        kamila_response.raise_for_status()
        return kamila_response.json()

@app.post("/trigger_decision_cycle_sync", response_model=KamilaFinalDecision, dependencies=[Depends(get_api_key)])
async def trigger_decision_cycle_sync(request: AnalysisRequest):
    logger.info("Requisição síncrona recebida", asset=request.asset)
    return await get_kamila_decision(request)

@app.post("/trigger_decision_cycle", status_code=202)
async def trigger_decision_cycle(request: AnalysisRequest, background_tasks: BackgroundTasks):
    logger.info("Requisição assíncrona recebida", asset=request.asset)
    async def wrapper():
        try:
            decision = await get_kamila_decision(request)
            logger.info("Fluxo de decisão em background concluído", decision=decision)
        except Exception as e:
            logger.error("Erro no fluxo de decisão em background", exc_info=e)
    background_tasks.add_task(wrapper)
    return {"message": "Ciclo de decisão iniciado."}

@app.get("/health")
def health(): return {"status": "ok"}
