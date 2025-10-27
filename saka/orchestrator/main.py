import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from saka.shared.models import AnalysisRequest, ConsolidatedDataInput, KamilaFinalDecision, ErrorResponse, AgentName, SentinelRiskOutput, CronosTechnicalOutput
from saka.shared.security import get_api_key

app = FastAPI(
    title="S.A.K.A. Orchestrator",
    description="Orquestra o fluxo de análise e decisão entre os agentes.",
    version="1.2.0" # Added sync endpoint for backtesting
)

# Carrega URLs e a chave de API a partir do .env
SENTINEL_URL = os.getenv("SENTINEL_URL")
CRONOS_URL = os.getenv("CRONOS_URL")
KAMILA_URL = os.getenv("KAMILA_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

# Prepara o cabeçalho de autenticação que será enviado para outros agentes
INTERNAL_API_HEADERS = {"X-Internal-API-Key": INTERNAL_API_KEY}


async def get_kamila_decision(request: AnalysisRequest) -> dict:
    """
    Função principal que executa o fluxo de análise e retorna a decisão da Kamila.
    Esta função é síncrona no sentido de que espera pela decisão final.
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Chama os agentes de análise em paralelo
        tasks = [
            client.post(f"{SENTINEL_URL}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS),
            client.post(f"{CRONOS_URL}/analyze", json=request.dict(), headers=INTERNAL_API_HEADERS)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        valid_responses = []
        for i, r in enumerate(responses):
            if isinstance(r, Exception):
                agent_name = "Sentinel" if i == 0 else "Cronos"
                raise HTTPException(status_code=503, detail=f"Falha na comunicação com o agente {agent_name}: {r}")
            try:
                r.raise_for_status()
                valid_responses.append(r)
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=502, detail=f"O agente {e.request.url} retornou um erro: {e.response.status_code} {e.response.text}")

        sentinel_data, cronos_data = [r.json() for r in valid_responses]

        consolidated_input = ConsolidatedDataInput(
            asset=request.asset,
            sentinel_analysis=SentinelRiskOutput(**sentinel_data),
            cronos_analysis=CronosTechnicalOutput(**cronos_data)
        )

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
    """
    Endpoint SÍNCRONO para o backtester.
    Executa o fluxo de decisão completo e retorna a decisão final da Kamila.
    """
    print(f"Recebida requisição síncrona para: {request.asset}")
    return await get_kamila_decision(request)


@app.post("/trigger_decision_cycle", status_code=202)
async def trigger_decision_cycle(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Endpoint ASSÍNCRONO para operação normal (live trading).
    Inicia o fluxo de decisão em background e retorna imediatamente.
    """
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
    """Endpoint público para health checks."""
    return {"status": "ok"}