import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from saka.shared.models import AnalysisRequest, ConsolidatedDataInput, KamilaFinalDecision, ErrorResponse, AgentName
from saka.shared.security import get_api_key

app = FastAPI(
    title="S.A.K.A. Orchestrator",
    description="Orquestra o fluxo de análise e decisão entre os agentes.",
    version="1.0.0"
)

# Carrega URLs e a chave de API a partir do .env
SENTINEL_URL = os.getenv("SENTINEL_URL")
KAMILA_URL = os.getenv("KAMILA_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

# Prepara o cabeçalho de autenticação que será enviado para outros agentes
INTERNAL_API_HEADERS = {"X-Internal-API-Key": INTERNAL_API_KEY}


async def run_decision_flow(request: AnalysisRequest):
    """
    Esta função roda em background. Ela coordena as chamadas para os agentes
    de análise, consolida os dados e envia para a Kamila.
    """
    print(f"Iniciando fluxo de decisão em background para o ativo: {request.asset}")

    async with httpx.AsyncClient() as client:
        try:
            # Chama os agentes de análise em paralelo
            sentinel_task = client.post(
                f"{SENTINEL_URL}/analyze",
                json=request.dict(),
                headers=INTERNAL_API_HEADERS
            )
            # Adicione outras tarefas de análise aqui (athena_task, cronos_task, etc.)

            responses = await asyncio.gather(sentinel_task) # Adicione outras tarefas aqui

            # Valida as respostas
            for r in responses:
                r.raise_for_status()

            sentinel_data = responses[0].json()

            # Consolida os dados para a Kamila
            consolidated_input = ConsolidatedDataInput(
                asset=request.asset,
                sentinel_analysis=sentinel_data
                # Adicione outros outputs de análise aqui
            )

            # Envia os dados consolidados para a Kamila
            kamila_response = await client.post(
                f"{KAMILA_URL}/decide",
                json=consolidated_input.dict(),
                headers=INTERNAL_API_HEADERS,
                timeout=30.0 # Timeout maior para a decisão da Kamila
            )
            kamila_response.raise_for_status()

            final_decision = kamila_response.json()
            print(f"Fluxo de decisão concluído para {request.asset}. Decisão: {final_decision.get('action')}")

        except httpx.RequestError as e:
            print(f"[ERRO NO FLUXO] Erro de comunicação com o agente: {e.request.url}. Detalhes: {e}")
        except Exception as e:
            print(f"[ERRO NO FLUXO] Erro inesperado durante o fluxo de decisão para {request.asset}. Detalhes: {e}")


@app.post("/trigger_decision_cycle", status_code=202)
async def trigger_decision_cycle(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    # O próprio orquestrador também pode ser protegido
    # api_key: str = Depends(get_api_key)
):
    """
    Recebe uma solicitação para iniciar um ciclo de decisão.
    Retorna uma resposta imediata e inicia o fluxo de trabalho em background.
    """
    background_tasks.add_task(run_decision_flow, request)
    return {
        "message": "Ciclo de decisão iniciado em background.",
        "asset": request.asset
    }

@app.get("/health", summary="Endpoint de Health Check")
def health():
    """Endpoint público para health checks."""
    return {"status": "ok"}