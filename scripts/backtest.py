import pandas as pd
import requests
import argparse
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Carrega o .env se existir, caso contrário, usa o .env.example
if os.path.exists('.env'):
    load_dotenv()
else:
    load_dotenv(dotenv_path='.env.example')

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8080")
API_KEY = os.getenv("INTERNAL_API_KEY")

def load_data(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo de dados não encontrado em: {filepath}")
    df = pd.read_csv(filepath, parse_dates=['timestamp'])
    required_columns = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"O arquivo CSV deve conter as seguintes colunas: {required_columns}")
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    return df

class Portfolio:
    def __init__(self, initial_cash=10000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}
        self.history = []
        self.total_value_history = []

    def update_value(self, current_prices: dict):
        total_position_value = 0
        for asset, data in self.positions.items():
            total_position_value += data['units'] * current_prices.get(asset, data['entry_price'])
        current_total_value = self.cash + total_position_value
        self.total_value_history.append(current_total_value)
        return current_total_value

    def execute_trade(self, asset: str, side: str, amount_usd: float, price: float, date):
        units = amount_usd / price
        if side == 'buy':
            if self.cash < amount_usd:
                return
            self.cash -= amount_usd
            current_units = self.positions.get(asset, {}).get('units', 0)
            self.positions[asset] = {'units': current_units + units, 'entry_price': price}
            self.history.append({'date': date, 'asset': asset, 'side': 'buy', 'amount_usd': amount_usd, 'price': price})
            print(f"ORDEM EXECUTADA: Comprar {units:.6f} {asset} a ${price:.2f}")
        elif side == 'sell':
            if asset not in self.positions or self.positions[asset]['units'] < units:
                return
            self.cash += amount_usd
            self.positions[asset]['units'] -= units
            if self.positions[asset]['units'] < 1e-6:
                del self.positions[asset]
            self.history.append({'date': date, 'asset': asset, 'side': 'sell', 'amount_usd': amount_usd, 'price': price})
            print(f"ORDEM EXECUTADA: Vender {units:.6f} {asset} a ${price:.2f}")

def run_backtest(data_filepath: str):
    if not API_KEY:
        print("Erro: A variável de ambiente INTERNAL_API_KEY não está definida.")
        return
    headers = {"X-Internal-API-Key": API_KEY}
    historical_data = load_data(data_filepath)
    warmup_period = 30 # Período para aquecimento dos indicadores
    if len(historical_data) < warmup_period:
        print("Erro: Dados históricos insuficientes para o período de aquecimento.")
        return

    print("\n--- Iniciando a Simulação de Backtesting ---")
    portfolio = Portfolio()
    for i in range(warmup_period, len(historical_data)):
        analysis_window = historical_data.iloc[i-warmup_period:i]
        current_day_data = historical_data.iloc[i]
        current_date = current_day_data.name.date()
        current_price = current_day_data['close']
        payload = {"asset": "BTC/USD", "historical_prices": analysis_window['close'].tolist()}

        print(f"\n[ {current_date} ] Preço Atual: ${current_price:.2f} | Valor do Portfólio: ${portfolio.update_value({'BTC/USD': current_price}):.2f}")

        try:
            response = requests.post(f"{ORCHESTRATOR_URL}/trigger_decision_cycle_sync", json=payload, headers=headers, timeout=45)
            response.raise_for_status()
            decision = response.json()
            print(f"Decisão da Kamila: {decision.get('action')}. Motivo: {decision.get('reason')}")
            if decision.get('action') == 'execute_trade':
                portfolio.execute_trade(
                    asset=decision['asset'], side=decision['side'],
                    amount_usd=decision['amount_usd'], price=current_price,
                    date=current_day_data.name
                )
        except requests.exceptions.RequestException as e:
            print(f"Erro ao se comunicar com o Orquestrador: {e}")
            break

    print("\n--- Simulação de Backtesting Concluída ---")
    generate_performance_report(portfolio, historical_data)
    plot_performance(portfolio, historical_data, warmup_period)

def generate_performance_report(portfolio: Portfolio, full_data: pd.DataFrame):
    if not portfolio.total_value_history:
        print("Nenhuma simulação foi executada.")
        return

    final_value = portfolio.total_value_history[-1]
    total_return_pct = ((final_value / portfolio.initial_cash) - 1) * 100
    buy_and_hold_return_pct = ((full_data['close'].iloc[-1] / full_data['close'].iloc[0]) - 1) * 100

    print("\n--- Relatório de Performance ---")
    print(f"Período Analisado: {len(portfolio.total_value_history)} dias")
    print(f"Valor Inicial do Portfólio: ${portfolio.initial_cash:,.2f}")
    print(f"Valor Final do Portfólio:   ${final_value:,.2f}")
    print(f"Retorno Total (Estratégia S.A.K.A.): {total_return_pct:.2f}%")
    print(f"Retorno Total (Buy and Hold):      {buy_and_hold_return_pct:.2f}%")
    print("-" * 30)

    total_trades = len(portfolio.history)
    if total_trades == 0:
        print("Nenhum trade foi executado.")
        return

    wins = 0
    trade_pnl = []
    buy_trades = [t for t in portfolio.history if t['side'] == 'buy']
    sell_trades = [t for t in portfolio.history if t['side'] == 'sell']

    for sell in sell_trades:
        corresponding_buy = next((buy for buy in buy_trades if buy['date'] < sell['date']), None)
        if corresponding_buy:
            pnl = sell['amount_usd'] - corresponding_buy['amount_usd']
            trade_pnl.append(pnl)
            if pnl > 0: wins += 1
            buy_trades.remove(corresponding_buy)

    win_rate = (wins / len(trade_pnl)) * 100 if trade_pnl else 0
    print(f"Total de Trades Executados: {total_trades}")
    print(f"Taxa de Acerto (Win Rate): {win_rate:.2f}%")
    print("-" * 30)

    value_history = pd.Series(portfolio.total_value_history)
    daily_returns = value_history.pct_change().dropna()

    running_max = value_history.cummax()
    drawdown = (value_history - running_max) / running_max
    max_drawdown_pct = drawdown.min() * 100

    sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5) if daily_returns.std() != 0 else 0

    print(f"Drawdown Máximo: {max_drawdown_pct:.2f}%")
    print(f"Índice de Sharpe (Anualizado): {sharpe_ratio:.2f}")
    print("--- Fim do Relatório ---")


def plot_performance(portfolio: Portfolio, full_data: pd.DataFrame, warmup_period: int):
    """
    Gera e salva um gráfico comparando a performance da estratégia com Buy and Hold.
    """
    if not portfolio.total_value_history:
        return

    # Prepara os dados do gráfico
    dates = full_data.index[warmup_period:]
    strategy_values = portfolio.total_value_history

    # Calcula a curva de capital do Buy and Hold
    initial_price = full_data['close'].iloc[warmup_period]
    buy_and_hold_values = portfolio.initial_cash * (full_data['close'][warmup_period:] / initial_price)

    # Cria o gráfico
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 8))

    ax.plot(dates, strategy_values, label='Estratégia S.A.K.A.', color='royalblue', linewidth=2)
    ax.plot(dates, buy_and_hold_values, label='Buy and Hold', color='gray', linestyle='--', linewidth=2)

    # Adiciona marcadores de trade
    buy_dates = [t['date'] for t in portfolio.history if t['side'] == 'buy']
    sell_dates = [t['date'] for t in portfolio.history if t['side'] == 'sell']
    buy_prices = [v for t in buy_dates if (v := portfolio.total_value_history[dates.get_loc(t)])]
    sell_prices = [v for t in sell_dates if (v := portfolio.total_value_history[dates.get_loc(t)])]

    ax.plot(buy_dates, buy_prices, '^', color='lime', markersize=10, label='Compras')
    ax.plot(sell_dates, sell_prices, 'v', color='red', markersize=10, label='Vendas')

    # Formatação
    ax.set_title('Performance da Estratégia S.A.K.A. vs. Buy and Hold', fontsize=18)
    ax.set_xlabel('Data', fontsize=12)
    ax.set_ylabel('Valor do Portfólio ($)', fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True)

    # Formata o eixo Y para mostrar valores em dólar
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'${y:,.0f}'))

    # Salva o gráfico
    output_filename = 'backtest_performance.png'
    plt.savefig(output_filename)
    print(f"\nGráfico de performance salvo em: {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa um backtest da estratégia S.A.K.A.")
    parser.add_argument("data_file", type=str, help="Caminho para o arquivo CSV de dados.")
    args = parser.parse_args()
    run_backtest(args.data_file)