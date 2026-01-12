import httpx
import asyncio
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from saka.shared.models import (
    AnalysisRequest, ConsolidatedDataInput, KamilaFinalDecision,
    ErrorResponse, AgentName, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput
)
from saka.shared.security import get_api_key
from saka.config.config import settings
from saka.shared.logging_config import setup_logging

# Configura o logging estruturado
setup_logging()
logger = structlog.get_logger(__name__)

app = FastAPI(
    title="S.A.K.A. Orchestrator",
    description="Orquestra o fluxo de análise e decisão entre os agentes.",
    version="1.3.1" # Optimized configuration and logging
)

INTERNAL_API_HEADERS = {"X-Internal-API-Key": settings.INTERNAL_API_KEY}


async def get_kamila_decision(request: AnalysisRequest) -> dict:
    """
    Executa o fluxo de análise completo e retorna a decisão da Kamila.
    """
    async with httpx.AsyncClient(timeout=settings.DEFAULT_TIMEOUT) as client:
        # Chama os agentes de análise em paralelo
        tasks = [
            client.post(f"{settings.SENTINEL_URL}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{settings.CRONOS_URL}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{settings.ORION_URL}/analyze_events", json=request.dict(), headers=INTERNAL_API_HEADERS)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Validação e extração de dados
        agent_names = ["Sentinel", "Cronos", "Orion"]
        results = {}
        for i, r in enumerate(responses):
            agent_name = agent_names[i]
            if isinstance(r, Exception):
                logger.error("communication_failure", agent=agent_name, error=str(r))
                raise HTTPException(status_code=503, detail=f"Falha na comunicação com o agente {agent_name}: {r}")
            try:
                r.raise_for_status()
                results[agent_name] = r.json()
            except httpx.HTTPStatusError as e:
                logger.error("agent_error", agent=agent_name, url=str(e.request.url), status=e.response.status_code, body=e.response.text)
                raise HTTPException(status_code=502, detail=f"O agente {agent_name} ({e.request.url}) retornou um erro: {e.response.status_code} {e.response.text}")

        # Consolidação dos dados
        consolidated_input = ConsolidatedDataInput(
            asset=request.asset,
            sentinel_analysis=SentinelRiskOutput(**results["Sentinel"]),
            cronos_analysis=CronosTechnicalOutput(**results["Cronos"]),
            orion_analysis=OrionMacroOutput(**results["Orion"])
        )

        # Obter decisão da Kamila
        kamila_response = await client.post(
            f"{settings.KAMILA_URL}/decide",
            json=consolidated_input.dict(),
            headers=INTERNAL_API_HEADERS,
            timeout=settings.KAMILA_TIMEOUT
        )
        kamila_response.raise_for_status()
        return kamila_response.json()


@app.post("/trigger_decision_cycle_sync", response_model=KamilaFinalDecision, dependencies=[Depends(get_api_key)])
async def trigger_decision_cycle_sync(request: AnalysisRequest):
    """Endpoint SÍNCRONO para o backtester."""
    logger.info("sync_decision_cycle_started", asset=request.asset)
    result = await get_kamila_decision(request)
    logger.info("sync_decision_cycle_completed", asset=request.asset, decision=result.get('action'))
    return result


@app.post("/trigger_decision_cycle", status_code=202)
async def trigger_decision_cycle(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Endpoint ASSÍNCRONO para operação normal."""
    logger.info("async_decision_cycle_initiated", asset=request.asset)

    async def decision_flow_wrapper():
        try:
            decision = await get_kamila_decision(request)
            logger.info("async_decision_cycle_completed", asset=request.asset, decision=decision.get('action'))
        except Exception as e:
            logger.error("async_decision_cycle_failed", asset=request.asset, error=str(e))

    background_tasks.add_task(decision_flow_wrapper)
    return {"message": "Ciclo de decisão iniciado em background.", "asset": request.asset}


@app.get("/health", summary="Endpoint de Health Check")
def health():
    return {"status": "ok"}
