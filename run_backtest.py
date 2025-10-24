import pandas as pd
import httpx
import asyncio
import os

from saka.data_processor import load_and_prepare_data
from saka.shared.models import KamilaFinalDecision

# --- Configurações do Backtest ---
INITIAL_CAPITAL = 10000.0
DATA_FILE_PATH = 'data/Gemini_BTCUSD_d.csv'
ORCHESTRATOR_URL = "http://localhost:8000"

async def run_backtest():
    """
    Função principal que executa o backtest.
    """
    # 1. Carregar Dados
    # ------------------
    data_path = 'data/sample_data.csv' if not os.path.exists(DATA_FILE_PATH) else DATA_FILE_PATH
    full_data = load_and_prepare_data(data_path)
    if full_data is None:
        return

    # 2. Inicializar Portfólio e Histórico
    # ------------------------------------
    portfolio = {'cash': INITIAL_CAPITAL, 'btc_holding': 0.0, 'total_value': INITIAL_CAPITAL}
    trade_history = []
    portfolio_history = []

    print("\n--- Iniciando Backtest ---")
    print(f"Capital Inicial: ${INITIAL_CAPITAL:,.2f}")

    # 3. Loop Principal do Backtest
    # -----------------------------
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(15, len(full_data)):
            current_date = full_data.index[i]
            current_price = full_data['close'].iloc[i]
            historical_prices = full_data['close'].iloc[:i+1].tolist()

            print(f"\n--- Processando Dia: {current_date.date()} | Preço BTC: ${current_price:,.2f} ---")

            try:
                response = await client.post(
                    f"{ORCHESTRATOR_URL}/trigger_decision_cycle",
                    json={"asset": "BTC/USD", "historical_prices": historical_prices}
                )
                response.raise_for_status()
                decision_result = response.json()

                if decision_result.get('status') == 'trade_executed':
                    trade_details = decision_result['details']
                    final_order = KamilaFinalDecision(**trade_details)
                    trade_amount_usd = final_order.amount_usd

                    if final_order.side == 'buy':
                        if portfolio['cash'] >= trade_amount_usd:
                            btc_bought = trade_amount_usd / current_price
                            portfolio['cash'] -= trade_amount_usd
                            portfolio['btc_holding'] += btc_bought
                            trade_history.append({'date': current_date, 'side': 'buy', 'amount': btc_bought, 'price': current_price})
                            print(f"  ORDEM DE COMPRA EXECUTADA: {btc_bought:.6f} BTC")
                        else:
                            print("  COMPRA FALHOU: Saldo de caixa insuficiente.")

                    elif final_order.side == 'sell':
                        btc_to_sell = trade_amount_usd / current_price
                        if portfolio['btc_holding'] >= btc_to_sell:
                            portfolio['cash'] += trade_amount_usd
                            portfolio['btc_holding'] -= btc_to_sell
                            trade_history.append({'date': current_date, 'side': 'sell', 'amount': btc_to_sell, 'price': current_price})
                            print(f"  ORDEM DE VENDA EXECUTADA: {btc_to_sell:.6f} BTC")
                        else:
                            print("  VENDA FALHOU: Saldo de BTC insuficiente.")
                else:
                    print(f"  AÇÃO: HOLD. Motivo: {decision_result.get('details', {}).get('reason', 'N/A')}")

            except httpx.RequestError as e:
                print(f"  ERRO: Não foi possível se comunicar com o Orquestrador: {e}")
                break

            portfolio['total_value'] = portfolio['cash'] + (portfolio['btc_holding'] * current_price)
            portfolio_history.append({'date': current_date, 'total_value': portfolio['total_value']})

    # 4. Gerar Relatório Final
    # ------------------------
    print("\n--- Backtest Concluído ---")

    final_price = full_data['close'].iloc[-1]
    final_value = portfolio['cash'] + (portfolio['btc_holding'] * final_price)
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    print("\n--- Performance Geral ---")
    print(f"Período Analisado: {full_data.index.min().date()} a {full_data.index.max().date()}")
    print(f"Capital Inicial: ${INITIAL_CAPITAL:,.2f}")
    print(f"Valor Final do Portfólio: ${final_value:,.2f}")
    print(f"Retorno Total: {total_return:.2f}%")
    print(f"Total de Trades Realizados: {len(trade_history)}")

    if not portfolio_history:
        print("Nenhum histórico de portfólio para analisar o Drawdown.")
        return

    # Calcular Drawdown Máximo
    portfolio_df = pd.DataFrame(portfolio_history).set_index('date')
    portfolio_df['peak'] = portfolio_df['total_value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['total_value'] - portfolio_df['peak']) / portfolio_df['peak']
    max_drawdown = portfolio_df['drawdown'].min()

    print(f"Drawdown Máximo: {max_drawdown:.2%}")

    # Calcular Taxa de Acerto (Win Rate)
    if len(trade_history) > 1:
        wins = 0
        num_closed_trades = 0
        for i in range(len(trade_history) - 1):
            trade = trade_history[i]
            next_trade = trade_history[i+1]
            if trade['side'] == 'buy' and next_trade['side'] == 'sell':
                num_closed_trades += 1
                profit = (next_trade['price'] - trade['price']) * trade['amount']
                if profit > 0:
                    wins += 1
        win_rate = (wins / num_closed_trades) * 100 if num_closed_trades > 0 else 0
        print(f"Taxa de Acerto (em {num_closed_trades} trades fechados): {win_rate:.2f}%")

if __name__ == "__main__":
    asyncio.run(run_backtest())