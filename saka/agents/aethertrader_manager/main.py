import uuid
import random
from fastapi import FastAPI
from datetime import datetime, timezone
from saka.shared.models import KamilaFinalDecision, TradeExecutionReceipt

app = FastAPI(title="Aethertrader (Manager)")

@app.post("/execute_trade", response_model=TradeExecutionReceipt)
async def execute_trade(order: KamilaFinalDecision):
    hypothetical_market_price = 70000.00
    slippage = random.uniform(-0.001, 0.001)
    executed_price = hypothetical_market_price * (1 + slippage)
    return TradeExecutionReceipt(
        trade_id=f"trade_{uuid.uuid4()}",
        status="success",
        executed_price=round(executed_price, 2),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/health")
def health():
    return {"status": "ok"}