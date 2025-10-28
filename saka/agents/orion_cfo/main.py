from fastapi import FastAPI, Depends
from saka.shared.models import AnalysisRequest, OrionMacroOutput, MacroImpact
from saka.shared.security import get_api_key
import random

app = FastAPI(title="Orion (Macroeconomic Analyst)")

@app.post("/analyze_events", response_model=OrionMacroOutput, dependencies=[Depends(get_api_key)])
async def analyze_events(request: AnalysisRequest):
    if random.random() < 0.1:
        return OrionMacroOutput(
            asset=request.asset, impact=MacroImpact.HIGH,
            event_name="Simulated High-Impact Event",
            summary="Negociação bloqueada devido a evento macro de alto impacto."
        )
    return OrionMacroOutput(
        asset=request.asset, impact=MacroImpact.LOW,
        event_name="No Major Events",
        summary="Nenhum evento de alto impacto detectado."
    )

@app.get("/health")
def health(): return {"status": "ok"}