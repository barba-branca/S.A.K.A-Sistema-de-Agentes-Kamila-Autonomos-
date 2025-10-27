from fastapi import FastAPI, Depends
from saka.shared.models import AnalysisRequest, ErrorResponse, AgentName
from saka.shared.security import get_api_key
import random

app = FastAPI(
    title="Orion (Macroeconomic Analyst)",
    description="Analisa o calendário macroeconômico em busca de eventos de alto impacto.",
    version="1.0.0"
)

# Em um sistema real, isso seria uma chamada a uma API de calendário econômico.
# Aqui, simulamos o resultado para fins de arquitetura.
@app.post("/analyze_events", dependencies=[Depends(get_api_key)])
async def analyze_events(request: AnalysisRequest):
    """
    Simula a análise de eventos macroeconômicos.
    Retorna um nível de impacto que pode ser usado como veto.
    """
    # Simula que em 10% dos dias há um evento de alto impacto (ex: CPI, FOMC)
    if random.random() < 0.1:
        return {
            "asset": request.asset,
            "impact": "high",
            "event_name": "Simulated High-Impact Event (e.g., CPI Report)",
            "summary": "Negociação bloqueada devido a evento macroeconômico de alto impacto."
        }

    return {
        "asset": request.asset,
        "impact": "low",
        "event_name": "No Major Events",
        "summary": "Nenhum evento de alto impacto detectado."
    }

@app.get("/health", summary="Endpoint de Health Check")
def health():
    """Endpoint público para health checks."""
    return {"status": "ok"}