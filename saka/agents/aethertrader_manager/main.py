import os
import datetime
from fastapi import FastAPI, Depends, HTTPException
from binance.client import Client
from binance.exceptions import BinanceAPIException
from saka.shared.models import KamilaFinalDecision, TradeExecutionReceipt, TradeSignal
from saka.shared.security import get_api_key

app = FastAPI(title="Aethertrader (Execution Agent)")

binance_client: Client | None = None
@app.on_event("startup")
def startup_event():
    global binance_client
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

@app.post("/execute_trade", response_model=TradeExecutionReceipt, dependencies=[Depends(get_api_key)])
async def execute_trade(decision: KamilaFinalDecision):
    if not binance_client:
        raise HTTPException(status_code=503, detail="Aethertrader não conectado à Binance.")

    symbol = decision.asset.replace('/', '').upper().replace('USD', 'USDT')
    side = Client.SIDE_BUY if decision.side == TradeSignal.BUY else Client.SIDE_SELL

    try:
        avg_price = float(binance_client.get_avg_price(symbol=symbol)['price'])
        quantity = round(decision.amount_usd / avg_price, 5)

        test_order = binance_client.create_test_order(symbol=symbol, side=side, type=Client.ORDER_TYPE_MARKET, quantity=quantity)

        return TradeExecutionReceipt(
            order_id=f"test_{datetime.datetime.now().timestamp()}", status="test_success", asset=decision.asset,
            side=decision.side, executed_price=avg_price, executed_quantity=quantity,
            amount_usd=decision.amount_usd, timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            raw_response=test_order
        )
    except BinanceAPIException as e:
        raise HTTPException(status_code=400, detail=f"Erro da API da Binance: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health(): return {"status": "ok"}