# Plano de Integração B3 (Bolsa Brasileira) no S.A.K.A.

Este documento detalha o roteiro técnico para permitir que o sistema S.A.K.A. opere no mercado de ações brasileiro (B3) além do mercado de criptomoedas.

## 1. Visão Geral da Arquitetura

A integração exigirá uma abordagem híbrida, pois a B3 não oferece APIs REST abertas e gratuitas como as exchanges de criptomoedas (Binance). A solução recomendada é utilizar o **MetaTrader 5 (MT5)** como gateway de execução.

### Fluxo Proposto
1.  **Kamila (CEO)** decide comprar `PETR4`.
2.  **Orquestrador** envia a decisão para o **Aethertrader**.
3.  **Aethertrader** detecta que o ativo não é cripto (padrão `XXXX3` ou `XXXX4`).
4.  **Aethertrader** usa um adaptador para se comunicar com uma instância do Terminal MetaTrader 5 rodando em ambiente Windows (ou via Wine).

## 2. Componentes Afetados

### A. Aethertrader (Execução)
O agente `aethertrader_manager` precisa evoluir de um script simples para um gerenciador de estratégias de execução multi-mercado.

*   **Padrão Adapter:** Implementar uma interface `ExchangeAdapter`.
    *   `BinanceAdapter`: Mantém a lógica atual.
    *   `MT5Adapter`: Nova classe usando a biblioteca `MetaTrader5`.
*   **Requisito de Infraestrutura:** O MT5 precisa rodar em um ambiente com GUI (Windows Server ou Linux com Wine/X11). Para contêineres Docker Linux puros, a solução comum é ter um serviço "satélite" rodando em uma máquina Windows que expõe uma API HTTP para o Aethertrader, ou rodar o Aethertrader diretamente no Windows.

### B. Fontes de Dados (Data Feed)
Cripto opera 24/7. B3 opera das 10h às 17h/18h.

*   **Cronos & Sentinel:** Precisam validar se o mercado está aberto antes de processar sinais.
*   **Provedor de Dados:**
    *   *Histórico:* Utilizar `yfinance` (Yahoo Finance) para baixar dados diários de ações B3 (ex: `PETR4.SA`).
    *   *Real-Time:* O próprio MT5 fornece ticks em tempo real. O Aethertrader pode consultar o MT5 para obter o preço atual (`ask`/`bid`) antes de executar.

## 3. Roteiro de Implementação

### Fase 1: Preparação do Ambiente
1.  Instalar Terminal MetaTrader 5 (fornecido pela corretora XP, Rico, Genial, etc.).
2.  Habilitar "Algo Trading" e permitir importações de DLL (se necessário) no MT5.
3.  Instalar biblioteca Python: `pip install MetaTrader5`.

### Fase 2: Atualização do Código (Aethertrader)
Criar a lógica de roteamento de ordens:

```python
# Pseudo-código para o Adapter
if "BTC" in asset or "ETH" in asset:
    execute_binance(asset, side, amount)
elif asset.endswith("3") or asset.endswith("4") or asset.endswith("11"):
    execute_mt5_b3(asset, side, amount)
```

### Fase 3: Gerenciamento de Horários (Cronos)
Implementar uma verificação de "Market Open" para evitar sinais falsos ou rejeição de ordens fora do pregão.

```python
from datetime import datetime, time

def is_b3_open():
    now = datetime.now().time()
    return time(10, 0) <= now <= time(17, 55)
```

## 4. Considerações de Risco
*   **Leilões:** A B3 tem leilões de abertura e fechamento onde a liquidez muda. O Sentinel deve evitar operar nesses horários (16:55 - 17:00).
*   **Lotes:** Ações na B3 são negociadas em lotes de 100 (padrão) ou fracionário (`F` no final, ex: `PETR4F`). O adaptador deve converter o `amount_usd` para a quantidade de lotes correta.

## 5. Próximos Passos
Aprovar este plano e iniciar a criação do `MT5Adapter` no diretório `saka/shared/adapters/`.
