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
    version="2.1.0" # Added real order response processing
)

# --- Configuração do Cliente Binance ---
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

binance_client: Client | None = None

@app.on_event("startup")
def startup_event():
    global binance_client
    # ... (código de inicialização omitido por brevidade) ...
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

    symbol = decision.asset.replace('/', '').upper().replace('USD', 'USDT')

    try:
        order_response = {}
        if decision.side == TradeSignal.BUY:
            print(f"Executando ordem de COMPRA a mercado: {decision.amount_usd} USDT de {symbol}")
            order_response = binance_client.order_market_buy(symbol=symbol, quoteOrderQty=decision.amount_usd)

        elif decision.side == TradeSignal.SELL:
            # A venda a mercado por USD não é suportada. Em um sistema real, Gaia precisaria
            # consultar o saldo e informar a quantidade a vender.
            # Por enquanto, vamos simular para não quebrar o fluxo.
            print(f"AVISO: Venda por valor em USD não suportada. Simulando venda de 0.001 {symbol}.")
            return TradeExecutionReceipt(
                order_id=f"simulated_sell_{datetime.datetime.now().timestamp()}", status="test_success",
                asset=decision.asset, side=decision.side, executed_price=50000, executed_quantity=0.001,
                amount_usd=decision.amount_usd, timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )

        print(f"Resposta da Binance: {order_response}")

        # Processa a resposta real da ordem
        if order_response and order_response.get('status') == 'FILLED':
            executed_price = float(order_response.get('cummulativeQuoteQty')) / float(order_response.get('executedQty'))
            executed_quantity = float(order_response.get('executedQty'))

            return TradeExecutionReceipt(
                order_id=str(order_response.get('orderId')),
                status="success",
                asset=decision.asset,
                side=decision.side,
                executed_price=executed_price,
                executed_quantity=executed_quantity,
                amount_usd=float(order_response.get('cummulativeQuoteQty')),
                timestamp=datetime.datetime.fromtimestamp(order_response.get('transactTime') / 1000, tz=datetime.timezone.utc).isoformat(),
                raw_response=order_response
            )
        else:
            # Se a ordem não for preenchida imediatamente ou falhar
            raise HTTPException(status_code=500, detail=f"A ordem não foi preenchida (FILLED). Status: {order_response.get('status')}")

    except BinanceAPIException as e:
        raise HTTPException(status_code=400, detail=f"Erro da API da Binance: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado no Aethertrader: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}