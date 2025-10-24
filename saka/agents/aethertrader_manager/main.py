from fastapi import FastAPI, Depends
from saka.shared.models import KamilaFinalDecision, TradeExecutionReceipt, TradeSignal
from saka.shared.security import get_api_key
import datetime
import uuid

app = FastAPI(title="Aethertrader (Execution Agent)")

@app.post("/execute_trade",
            response_model=TradeExecutionReceipt,
            dependencies=[Depends(get_api_key)])
async def execute_trade(decision: KamilaFinalDecision):
    """
    Lógica de execução de trade (placeholder).
    Recebe uma decisão final da Kamila e simula a execução.
    """
    print(f"Aethertrader recebeu ordem para {decision.side} {decision.asset}")

    # A integração real com a API da exchange (ex: Binance) viria aqui.

    return TradeExecutionReceipt(
        trade_id=str(uuid.uuid4()),
        status="success",
        asset=decision.asset,
        side=decision.side,
        executed_price=50000.0, # Preço simulado
        amount_usd=decision.amount_usd,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@app.get("/health")
def health():
    return {"status": "ok"}