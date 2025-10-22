from fastapi import FastAPI

app = FastAPI(title="Orchestrator")

@app.get("/health")
def health():
    return {"status": "ok", "message": "Orchestrator está operacional."}