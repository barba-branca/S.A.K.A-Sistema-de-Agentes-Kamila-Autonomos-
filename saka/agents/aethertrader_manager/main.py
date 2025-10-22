import uuid
import random
from fastapi import FastAPI, HTTPException, Body
from datetime import datetime, timezone
import logging
import sys

# Adiciona o caminho para encontrar o módulo 'shared'
sys.path.append('../')
from shared.models import KamilaFinalDecision, TradeExecutionReceipt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="S.A.K.A. Aethertrader (Manager)",
    description="Agente de execução de trades. Recebe ordens e interage com as corretoras.",
    version="1.0.0"
)

@app.post("/execute_trade", response_model=TradeExecutionReceipt)
async def execute_trade(order: KamilaFinalDecision = Body(...)):
    """
    Recebe e executa uma ordem de trade final de Kamila.
    A execução é simulada.
    """
    logger.info(f"Recebida ordem de execução: {order.dict()}")

    trade_id = f"trade_{uuid.uuid4()}"
    status = "success"

    hypothetical_market_price = 70000.00
    slippage = random.uniform(-0.001, 0.001)
    executed_price = hypothetical_market_price * (1 + slippage)

    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(f"Ordem {order.action} de {order.amount_usd} USD de {order.asset} executada. Trade ID: {trade_id}")

    receipt = TradeExecutionReceipt(
        trade_id=trade_id,
        status=status,
        executed_price=round(executed_price, 2),
        timestamp=timestamp
    )

    return receipt

@app.get("/health")
def health_check():
    """Verifica a saúde do serviço."""
    return {"status": "ok", "message": "Aethertrader está operacional."}