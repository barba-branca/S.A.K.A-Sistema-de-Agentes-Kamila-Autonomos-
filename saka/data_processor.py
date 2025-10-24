import pandas as pd
from typing import Optional

def load_and_prepare_data(filepath: str) -> Optional[pd.DataFrame]:
    """
    Carrega dados históricos de um arquivo CSV e os prepara para backtesting.
    """
    try:
        df = pd.read_csv(filepath, skiprows=1) # Pula o cabeçalho original que tem nomes de coluna ruins
        df.columns = ['unix', 'date', 'symbol', 'open', 'high', 'low', 'close', 'volume_btc', 'volume_usd']
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(ascending=True, inplace=True)
        print(f"Dados carregados e preparados com sucesso de '{filepath}'.")
        return df
    except FileNotFoundError:
        print(f"Erro: O arquivo de dados '{filepath}' não foi encontrado.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro ao processar os dados: {e}")
        return None

if __name__ == '__main__':
    sample_df = load_and_prepare_data('data/sample_data.csv')
    if sample_df is not None:
        print("\n--- Amostra dos Dados Preparados ---")
        print(sample_df.head())
        print("\n--- Informações do DataFrame ---")
        sample_df.info()