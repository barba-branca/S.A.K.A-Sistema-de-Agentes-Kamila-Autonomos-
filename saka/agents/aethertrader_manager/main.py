import os
import datetime
from fastapi import FastAPI, Depends, HTTPException
from binance.client import Client
from binance.exceptions import BinanceAPIException

from saka.shared.models import KamilaFinalDecision, TradeExecutionReceipt, ErrorResponse, AgentName, TradeSignal
from saka.shared.security import get_api_key

app = FastAPI(
    title="Aethertrader (Execution Agent)",
    description="Executa ordens de trade na corretora (Binance Testnet).",
    version="1.2.0" # Refined execution receipt
)

# --- Configuração do Cliente Binance ---
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

binance_client: Client | None = None

@app.on_event("startup")
def startup_event():
    global binance_client
    if not all([BINANCE_API_KEY, BINANCE_API_SECRET]):
        print("AVISO: Credenciais da Binance não configuradas.")
        return
    try:
        binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)
        binance_client.ping()
        print("Cliente da Binance (Testnet) inicializado e conectado com sucesso.")
    except Exception as e:
        print(f"ERRO: Falha ao inicializar o cliente da Binance: {e}")
        binance_client = None


@app.post("/execute_trade",
            response_model=TradeExecutionReceipt,
            dependencies=[Depends(get_api_key)])
async def execute_trade(decision: KamilaFinalDecision):
    if not binance_client:
        raise HTTPException(status_code=503, detail="Serviço indisponível: Aethertrader não está conectado à Binance.")

    # Converte o símbolo para o formato da Binance (ex: BTC/USD -> BTCUSDT)
    symbol = decision.asset.replace('/', '').upper()
    if 'USD' in symbol and not 'USDT' in symbol:
        symbol = symbol.replace('USD', 'USDT')

    side = Client.SIDE_BUY if decision.side == TradeSignal.BUY else Client.SIDE_SELL

    try:
        avg_price_info = binance_client.get_avg_price(symbol=symbol)
        current_price = float(avg_price_info['price'])
        quantity = round(decision.amount_usd / current_price, 5)

        print(f"Preparando ordem de teste: {side} {quantity} {symbol}")

        # Em um ambiente real, seria `create_order`.
        # A resposta de `create_test_order` é apenas `{}`.
        test_order_response = binance_client.create_test_order(
            symbol=symbol,
            side=side,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )

        print(f"Ordem de teste para {symbol} enviada com sucesso.")

        # Simula o recibo com os novos campos
        return TradeExecutionReceipt(
            order_id=f"test_{datetime.datetime.now().timestamp()}",
            status="test_success",
            asset=decision.asset,
            side=decision.side,
            executed_price=current_price,
            executed_quantity=quantity,
            amount_usd=decision.amount_usd,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            raw_response=test_order_response
        )

    except BinanceAPIException as e:
        raise HTTPException(status_code=400, detail=f"Erro da API da Binance: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado no Aethertrader: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}