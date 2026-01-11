from fastapi import FastAPI, Depends
from saka.shared.models import AnalysisRequest, OrionMacroOutput, MacroImpact
from saka.shared.security import get_api_key
from saka.shared.logging_config import configure_logging, get_logger
import random

configure_logging()
logger = get_logger("orion_cfo")

app = FastAPI(title="Orion (Macroeconomic Analyst)")

@app.post("/analyze_events", response_model=OrionMacroOutput, dependencies=[Depends(get_api_key)])
async def analyze_events(request: AnalysisRequest):
    logger.info("Recebida requisição de análise de eventos macro", asset=request.asset)

    if random.random() < 0.1:
        impact = MacroImpact.HIGH
        event_name = "Simulated High-Impact Event"
        summary = "Negociação bloqueada devido a evento macro de alto impacto."
        logger.warning("Evento de alto impacto detectado", event=event_name)
    else:
        impact = MacroImpact.LOW
        event_name = "No Major Events"
        summary = "Nenhum evento de alto impacto detectado."
        logger.info("Nenhum evento macro de alto impacto detectado.")

    return OrionMacroOutput(
        asset=request.asset, impact=impact,
        event_name=event_name, summary=summary
    )

@app.get("/health")
def health(): return {"status": "ok"}
