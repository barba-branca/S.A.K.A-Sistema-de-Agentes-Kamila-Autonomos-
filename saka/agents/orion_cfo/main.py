from fastapi import FastAPI
from pydantic import BaseModel
import random

from saka.shared.models import OrionMacroOutput

app = FastAPI(
    title="S.A.K.A. Orion (CFO)",
    description="Agente de análise macroeconômrica.",
    version="1.0.0"
)

class AnalysisRequest(BaseModel):
    market: str

@app.post("/analyze_macro", response_model=OrionMacroOutput)
async def analyze_macro(request: AnalysisRequest):
    """
    Simula a análise de eventos econômicos.
    """
    possible_events = [
        ("CPI_REPORT", "Relatório de Inflação (CPI) divulgado."),
        ("FED_MEETING", "Reunião do Comitê Federal de Mercado Aberto (FOMC)."),
        ("NO_MAJOR_EVENT", "Nenhum evento macroeconômico de grande impacto no radar.")
    ]
    event_name, event_summary = random.choice(possible_events)
    impact = "low"
    if event_name != "NO_MAJOR_EVENT":
        impact = random.choice(["low", "medium", "high"])

    return OrionMacroOutput(
        economic_indicator=event_name,
        impact=impact,
        summary=event_summary
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}