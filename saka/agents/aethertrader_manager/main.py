import os
import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from binance.client import Client
from binance.exceptions import BinanceAPIException

from saka.shared.models import KamilaFinalDecision, TradeExecutionReceipt, TradeSignal
from saka.shared.security import get_api_key
from saka.database import models, database
from saka.shared.logging_config import configure_logging, get_logger

# Configura o logging estruturado
configure_logging()
logger = get_logger("aethertrader")

app = FastAPI(
    title="Aethertrader (Execution Agent)",
    description="Executa ordens de trade e as salva no banco de dados.",
    version="2.2.0"
)

# --- Configuração do Cliente Binance ---
binance_client: Client | None = None

# --- Dependência do Banco de Dados ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    global binance_client
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not all([api_key, api_secret]):
        logger.warning("Credenciais da Binance não configuradas. A execução de ordens está desativada.")
        return
    try:
        binance_client = Client(api_key, api_secret, testnet=True)
        binance_client.ping()
        logger.info("Cliente da Binance (Testnet) inicializado e conectado com sucesso.")
    except Exception as e:
        logger.error("Falha ao inicializar o cliente da Binance", exc_info=e)

@app.post("/execute_trade", response_model=TradeExecutionReceipt, dependencies=[Depends(get_api_key)])
async def execute_trade(decision: KamilaFinalDecision, db: Session = Depends(get_db)):
    if not binance_client:
        logger.error("Tentativa de executar trade sem cliente da Binance conectado.")
        raise HTTPException(status_code=503, detail="Aethertrader não está conectado à Binance.")

    symbol = decision.asset.replace('/', '').upper().replace('USD', 'USDT')

    try:
        order_response = binance_client.order_market_buy(symbol=symbol, quoteOrderQty=decision.amount_usd)

        logger.info("Resposta da ordem da Binance recebida", order_response=order_response)

        if order_response and order_response.get('status') == 'FILLED':
            executed_price = float(order_response.get('cummulativeQuoteQty')) / float(order_response.get('executedQty'))
            executed_quantity = float(order_response.get('executedQty'))
            order_id = str(order_response.get('orderId'))
            timestamp = datetime.datetime.fromtimestamp(order_response.get('transactTime') / 1000, tz=datetime.timezone.utc)

            receipt = TradeExecutionReceipt(
                order_id=order_id, status="success", asset=decision.asset,
                side=decision.side, executed_price=executed_price, executed_quantity=executed_quantity,
                amount_usd=float(order_response.get('cummulativeQuoteQty')), timestamp=timestamp.isoformat(),
                raw_response=order_response
            )

            # Prepara os dados para o modelo do banco, garantindo que 'side' seja uma string
            db_trade_data = receipt.model_dump(exclude={"raw_response", "side"})
            db_trade = models.Trade(**db_trade_data, side=receipt.side.value)
            db.add(db_trade)
            db.commit()
            db.refresh(db_trade)
            logger.info("Trade salvo no banco de dados", trade_id=db_trade.id, order_id=order_id)

            return receipt
        else:
            logger.error("A ordem não foi preenchida (FILLED)", order_status=order_response.get('status'))
            raise HTTPException(status_code=500, detail=f"A ordem não foi preenchida. Status: {order_response.get('status')}")

    except BinanceAPIException as e:
        logger.error("Erro da API da Binance ao executar a ordem", exc_info=e)
        raise HTTPException(status_code=400, detail=f"Erro da API da Binance: {e}")
    except Exception as e:
        logger.error("Erro inesperado no Aethertrader", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Erro inesperado no Aethertrader: {e}")

@app.get("/health")
def health(): return {"status": "ok"}
