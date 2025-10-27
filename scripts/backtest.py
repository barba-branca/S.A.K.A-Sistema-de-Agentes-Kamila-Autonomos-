import pandas as pd
import requests
import argparse
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações ---
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8080")
API_KEY = os.getenv("INTERNAL_API_KEY")

def load_data(filepath: str) -> pd.DataFrame:
    """
    Carrega os dados históricos de um arquivo CSV e os valida.
    """
    print(f"Carregando dados de: {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo de dados não encontrado em: {filepath}")

    df = pd.read_csv(filepath, parse_dates=['timestamp'])

    # Validação de colunas
    required_columns = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"O arquivo CSV deve conter as seguintes colunas: {required_columns}")

    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)

    print(f"Dados carregados com sucesso. Período: {df.index.min()} a {df.index.max()}. Total de {len(df)} registros.")
    return df

class Portfolio:
    """
    Gerencia o estado do portfólio, incluindo caixa, posições e trades.
    """
    def __init__(self, initial_cash=10000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}  # 'asset': {'units': float, 'entry_price': float}
        self.history = []
        self.total_value_history = []

    def update_value(self, current_prices: dict):
        """Calcula o valor total atual do portfólio."""
        total_position_value = 0
        for asset, data in self.positions.items():
            total_position_value += data['units'] * current_prices.get(asset, data['entry_price'])

        current_total_value = self.cash + total_position_value
        self.total_value_history.append(current_total_value)
        return current_total_value

    def execute_trade(self, asset: str, side: str, amount_usd: float, price: float):
        """Executa uma ordem de compra ou venda."""
        units = amount_usd / price

        if side == 'buy':
            if self.cash < amount_usd:
                print(f"AVISO: Caixa insuficiente para comprar {amount_usd:.2f} de {asset}. Ignorando ordem.")
                return

            self.cash -= amount_usd
            # Simplesmente adiciona à posição existente (média de preço não implementada para simplicidade)
            current_units = self.positions.get(asset, {}).get('units', 0)
            self.positions[asset] = {'units': current_units + units, 'entry_price': price}
            self.history.append({'date': price, 'asset': asset, 'side': 'buy', 'amount_usd': amount_usd, 'price': price})
            print(f"ORDEM EXECUTADA: Comprar {units:.6f} {asset} a ${price:.2f}")

        elif side == 'sell':
            if asset not in self.positions or self.positions[asset]['units'] < units:
                print(f"AVISO: Posição insuficiente para vender {units:.6f} de {asset}. Ignorando ordem.")
                return

            self.cash += amount_usd
            self.positions[asset]['units'] -= units
            if self.positions[asset]['units'] < 1e-6: # Limpeza de posições pequenas
                del self.positions[asset]
            self.history.append({'date': price, 'asset': asset, 'side': 'sell', 'amount_usd': amount_usd, 'price': price})
            print(f"ORDEM EXECUTADA: Vender {units:.6f} {asset} a ${price:.2f}")


def run_backtest(data_filepath: str):
    """
    Função principal para executar o backtest.
    """
    if not API_KEY:
        print("Erro: A variável de ambiente INTERNAL_API_KEY não está definida.")
        return

    headers = {"X-Internal-API-Key": API_KEY}
    historical_data = load_data(data_filepath)

    # Período de "aquecimento" para os indicadores técnicos (ex: RSI de 14 dias, MACD de 26 dias)
    warmup_period = 30

    if len(historical_data) < warmup_period:
        print("Erro: Dados históricos insuficientes para o período de aquecimento.")
        return

    print("\n--- Iniciando a Simulação de Backtesting ---")

    portfolio = Portfolio()

    # Itera sobre os dados, começando após o período de aquecimento
    for i in range(warmup_period, len(historical_data)):
        # Janela de dados para análise (passado)
        analysis_window = historical_data.iloc[i-warmup_period:i]
        # Dados do dia atual para execução e avaliação
        current_day_data = historical_data.iloc[i]
        current_date = current_day_data.name.date()
        current_price = current_day_data['close']

        # Prepara a requisição para o Orquestrador
        payload = {
            "asset": "BTC/USD",
            "historical_prices": analysis_window['close'].tolist()
        }

        print(f"\n[ {current_date} ] Preço Atual: ${current_price:.2f} | Valor do Portfólio: ${portfolio.update_value({'BTC/USD': current_price}):.2f}")

        try:
            response = requests.post(f"{ORCHESTRATOR_URL}/trigger_decision_cycle_sync", json=payload, headers=headers, timeout=45)
            response.raise_for_status()

            decision = response.json()
            print(f"Decisão da Kamila recebida: {decision.get('action')}. Motivo: {decision.get('reason')}")

            # Executa o trade no portfólio simulado
            if decision.get('action') == 'execute_trade':
                portfolio.execute_trade(
                    asset=decision['asset'],
                    side=decision['side'],
                    amount_usd=decision['amount_usd'],
                    price=current_price # Executa ao preço de fechamento do dia
                )

        except requests.exceptions.RequestException as e:
            print(f"Erro ao se comunicar com o Orquestrador: {e}")
            print("Verifique se os contêineres do S.A.K.A. estão rodando com 'docker compose up'.")
            break # Interrompe a simulação se a comunicação falhar

    print("\n--- Simulação de Backtesting Concluída ---")
    generate_performance_report(portfolio)


def generate_performance_report(portfolio: Portfolio):
    """Calcula e exibe as métricas de performance do backtest."""
    final_value = portfolio.total_value_history[-1]
    total_return_pct = ((final_value / portfolio.initial_cash) - 1) * 100

    print("\n--- Relatório de Performance ---")
    print(f"Período Analisado: {len(portfolio.total_value_history)} dias")
    print(f"Valor Inicial do Portfólio: ${portfolio.initial_cash:,.2f}")
    print(f"Valor Final do Portfólio:   ${final_value:,.2f}")
    print(f"Retorno Total: {total_return_pct:.2f}%")
    print("-" * 30)

    total_trades = len(portfolio.history)
    if total_trades == 0:
        print("Nenhum trade foi executado.")
        return

    # Calcular Taxa de Acerto (Win Rate)
    wins = 0
    trade_pnl = []
    # Simplificação: assumes que cada venda fecha uma compra anterior
    buy_trades = [t for t in portfolio.history if t['side'] == 'buy']
    sell_trades = [t for t in portfolio.history if t['side'] == 'sell']

    for sell in sell_trades:
        # Encontra a compra correspondente (simplificação: a primeira compra antes da venda)
        corresponding_buy = next((buy for buy in buy_trades if buy['date'] < sell['date']), None)
        if corresponding_buy:
            pnl = sell['amount_usd'] - corresponding_buy['amount_usd']
            trade_pnl.append(pnl)
            if pnl > 0:
                wins += 1
            buy_trades.remove(corresponding_buy) # Evita reutilizar a mesma compra

    win_rate = (wins / len(trade_pnl)) * 100 if trade_pnl else 0

    print(f"Total de Trades Executados: {total_trades}")
    print(f"Trades com Lucro/Prejuízo Calculado: {len(trade_pnl)}")
    print(f"Taxa de Acerto (Win Rate): {win_rate:.2f}%")
    print("-" * 30)

    # Calcular Drawdown Máximo
    value_history = pd.Series(portfolio.total_value_history)
    running_max = value_history.cummax()
    drawdown = (value_history - running_max) / running_max
    max_drawdown_pct = drawdown.min() * 100

    print(f"Drawdown Máximo: {max_drawdown_pct:.2f}%")
    print("--- Fim do Relatório ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa um backtest da estratégia de trading S.A.K.A.")
    parser.add_argument(
        "data_file",
        type=str,
        help="Caminho para o arquivo CSV com os dados históricos (ex: data/btc_usd_daily.csv)"
    )
    args = parser.parse_args()

    run_backtest(args.data_file)