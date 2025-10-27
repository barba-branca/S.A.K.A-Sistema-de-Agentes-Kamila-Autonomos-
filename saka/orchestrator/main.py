import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from saka.shared.models import (
    AnalysisRequest, ConsolidatedDataInput, KamilaFinalDecision,
    ErrorResponse, AgentName, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput
)
from saka.shared.security import get_api_key

app = FastAPI(
    title="S.A.K.A. Orchestrator",
    description="Orquestra o fluxo de análise e decisão entre os agentes.",
    version="1.3.0" # Added Orion integration
)

# Carrega URLs
SENTINEL_URL = os.getenv("SENTINEL_URL")
CRONOS_URL = os.getenv("CRONOS_URL")
ORION_URL = os.getenv("ORION_URL")
KAMILA_URL = os.getenv("KAMILA_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
INTERNAL_API_HEADERS = {"X-Internal-API-Key": INTERNAL_API_KEY}


async def get_kamila_decision(request: AnalysisRequest) -> dict:
    """
    Executa o fluxo de análise completo e retorna a decisão da Kamila.
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Chama os agentes de análise em paralelo
        tasks = [
            client.post(f"{SENTINEL_URL}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{CRONOS_URL}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{ORION_URL}/analyze_events", json=request.dict(), headers=INTERNAL_API_HEADERS)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Validação e extração de dados
        agent_names = ["Sentinel", "Cronos", "Orion"]
        results = {}
        for i, r in enumerate(responses):
            agent_name = agent_names[i]
            if isinstance(r, Exception):
                raise HTTPException(status_code=503, detail=f"Falha na comunicação com o agente {agent_name}: {r}")
            try:
                r.raise_for_status()
                results[agent_name] = r.json()
            except httpx.HTTPStatusError as e:
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
            f"{KAMILA_URL}/decide",
            json=consolidated_input.dict(),
            headers=INTERNAL_API_HEADERS,
            timeout=30.0
        )
        kamila_response.raise_for_status()
        return kamila_response.json()


@app.post("/trigger_decision_cycle_sync", response_model=KamilaFinalDecision, dependencies=[Depends(get_api_key)])
async def trigger_decision_cycle_sync(request: AnalysisRequest):
    """Endpoint SÍNCRONO para o backtester."""
    print(f"Recebida requisição síncrona para: {request.asset}")
    return await get_kamila_decision(request)


@app.post("/trigger_decision_cycle", status_code=202)
async def trigger_decision_cycle(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Endpoint ASSÍNCRONO para operação normal."""
    print(f"Iniciando fluxo de decisão em background para o ativo: {request.asset}")

    async def decision_flow_wrapper():
        try:
            decision = await get_kamila_decision(request)
            print(f"Fluxo de decisão em background concluído para {request.asset}. Decisão: {decision.get('action')}")
        except Exception as e:
            print(f"[ERRO NO FLUXO EM BACKGROUND] Erro inesperado para {request.asset}. Detalhes: {e}")

    background_tasks.add_task(decision_flow_wrapper)
    return {"message": "Ciclo de decisão iniciado em background.", "asset": request.asset}


@app.get("/health", summary="Endpoint de Health Check")
def health():
    return {"status": "ok"}