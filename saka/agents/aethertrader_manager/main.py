import os
import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from binance.client import Client
from binance.exceptions import BinanceAPIException

from saka.shared.models import KamilaFinalDecision, TradeExecutionReceipt, TradeSignal
from saka.shared.security import get_api_key
from saka.database import models, database

app = FastAPI(
    title="Aethertrader (Execution Agent)",
    description="Executa ordens de trade e as salva no banco de dados.",
    version="2.2.0" # Added DB persistence
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
    # ... (código de inicialização omitido por brevidade) ...
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not all([api_key, api_secret]):
        print("AVISO: Credenciais da Binance não configuradas.")
        return
    try:
        binance_client = Client(api_key, api_secret, testnet=True)
        binance_client.ping()
        print("Cliente da Binance (Testnet) conectado.")
    except Exception as e:
        print(f"ERRO: Falha ao conectar com a Binance: {e}")

@app.post("/execute_trade",
            response_model=TradeExecutionReceipt,
            dependencies=[Depends(get_api_key)])
async def execute_trade(decision: KamilaFinalDecision, db: Session = Depends(get_db)):
    if not binance_client:
        raise HTTPException(status_code=503, detail="Aethertrader não conectado à Binance.")

    symbol = decision.asset.replace('/', '').upper().replace('USD', 'USDT')

    try:
        order_response = binance_client.order_market_buy(symbol=symbol, quoteOrderQty=decision.amount_usd)

        if order_response and order_response.get('status') == 'FILLED':
            # Processa a resposta
            executed_price = float(order_response.get('cummulativeQuoteQty')) / float(order_response.get('executedQty'))
            executed_quantity = float(order_response.get('executedQty'))
            order_id = str(order_response.get('orderId'))
            timestamp = datetime.datetime.fromtimestamp(order_response.get('transactTime') / 1000, tz=datetime.timezone.utc)

            # Cria o recibo Pydantic
            receipt = TradeExecutionReceipt(
                order_id=order_id, status="success", asset=decision.asset,
                side=decision.side, executed_price=executed_price, executed_quantity=executed_quantity,
                amount_usd=float(order_response.get('cummulativeQuoteQty')), timestamp=timestamp.isoformat(),
                raw_response=order_response
            )

            # Cria e salva o modelo do SQLAlchemy no banco de dados
            db_trade = models.Trade(
                order_id=receipt.order_id, status=receipt.status, asset=receipt.asset,
                side=receipt.side.value, executed_price=receipt.executed_price,
                executed_quantity=receipt.executed_quantity, amount_usd=receipt.amount_usd,
                timestamp=timestamp, raw_response=receipt.raw_response
            )
            db.add(db_trade)
            db.commit()
            db.refresh(db_trade)
            print(f"Trade salvo no banco de dados com ID: {db_trade.id}")

            return receipt
        else:
            raise HTTPException(status_code=500, detail=f"A ordem não foi preenchida. Status: {order_response.get('status')}")

    except BinanceAPIException as e:
        raise HTTPException(status_code=400, detail=f"Erro da API da Binance: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado no Aethertrader: {e}")

@app.get("/health")
def health(): return {"status": "ok"}