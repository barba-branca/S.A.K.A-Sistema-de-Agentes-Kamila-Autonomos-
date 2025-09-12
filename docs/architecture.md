# Arquitetura do Sistema S.A.K.A.

Este documento fornece uma visão geral detalhada da arquitetura do sistema S.A.K.A., seus componentes principais e o fluxo de comunicação entre eles.

## Visão Geral de Alto Nível

S.A.K.A. é projetado como um sistema distribuído de múltiplos agentes. A arquitetura é centrada em um **Orquestrador** central que gerencia uma frota de **Agentes** especializados. Cada componente (o orquestrador e cada agente) executa em seu próprio contêiner Docker isolado, garantindo escalabilidade e separação de responsabilidades.

Os princípios fundamentais da arquitetura são:
-   **Modularidade:** Cada agente é uma unidade autocontida com um propósito específico.
-   **Escalabilidade:** A natureza conteinerizada permite executar múltiplas instâncias de agentes ou adicionar novos agentes facilmente.
-   **Coordenação Centralizada:** O Orquestrador atua como um hub de descoberta de serviços e comunicação, evitando um emaranhado de conexões diretas de agente para agente.
-   **Comunicação Orientada a Eventos:** Os agentes reagem primariamente a mensagens e eventos, permitindo operações assíncronas.

### Fluxograma do Sistema

O sistema segue uma estrutura hierárquica onde Kamila (CEO) coordena os outros agentes. O Orquestrador facilita a comunicação e o gerenciamento desses agentes.

*(O usuário forneceu uma imagem de fluxograma que ilustra essa estrutura. Kamila está no topo, recebendo informações de Orion (CFO) e consultando Polaris. Orion, por sua vez, obtém dados de Sentinel (Risco), Gaia (Diversificação) e Aethertrader. Aethertrader é auxiliado por Athena (Sentimento) e Hermes (Execução). O Orquestrador é um serviço central que interage com todos os agentes para gerenciamento e logs.)*

## Componentes Principais

### 1. Orquestrador

O Orquestrador é o sistema nervoso central do S.A.K.A. É uma aplicação FastAPI com várias responsabilidades chave:

-   **Registro de Agentes:** Mantém uma lista dinâmica de todos os agentes ativos, incluindo seus IDs, nomes e endpoints de API.
-   **Descoberta de Serviços:** Quando um agente deseja se comunicar com outro, ele pergunta ao Orquestrador a localização do alvo.
-   **Roteamento de Mensagens:** Expõe um endpoint (`/agents/{target_agent_id}/message`) que permite aos agentes enviar mensagens uns aos outros sem precisar saber seus endereços de rede diretos. O Orquestrador encaminha a mensagem para o agente correto.
-   **Gerenciamento do Ciclo de Vida do Agente:** O Orquestrador é projetado para ser o componente através do qual Kamila eventualmente criará e encerrará outros agentes automaticamente.

### 2. Agentes

Cada agente é uma aplicação Python construída sobre a classe `BaseAgent`. Esta classe base fornece a funcionalidade comum necessária para operar dentro do ecossistema S.A.K.A.

-   **Classe `BaseAgent`:** Encontrada em `src/core/agent.py`, esta classe fornece:
    -   Um servidor FastAPI integrado para receber mensagens.
    -   Um método `register_with_orchestrator()` para anunciar sua presença.
    -   Um método `send_message()` para se comunicar com outros agentes através do Orquestrador.

-   **Agentes Especializados:** Cada agente herda de `BaseAgent` e implementa sua própria lógica específica, principalmente dentro do método `handle_message`.

#### Funções dos Agentes:

-   **Kamila (CEO):** A principal agente de tomada de decisão. Ela coordena os outros agentes, valida estratégias e é responsável por enviar relatórios diários.
-   **Polaris (Conselheiro):** Um conselheiro estratégico. Kamila consulta Polaris antes de executar decisões críticas.
-   **Orion (CFO/Analista Macro):** Analisa dados macroeconômicos, notícias e relatórios financeiros para fornecer insumos estratégicos.
-   **Aethertrader (Gerente de Trades):** Responsável por executar os trades que foram aprovados por Kamila.
-   **Athena (Analista de Sentimento):** Varre notícias e mídias sociais para avaliar o sentimento do mercado.
-   **Sentinel (Gerente de Risco):** Monitora o portfólio em busca de riscos, gerenciando stop-loss e exposição geral.
-   **Hermes (Otimizador de Execução):** Um agente especialista que auxilia Aethertrader a encontrar a maneira ideal de executar um trade, minimizando o slippage.
-   **Cronos (Analista Temporal):** Analisa ciclos de mercado e timing para evitar operar em condições desfavoráveis.
-   **Gaia (Gerente de Diversificação):** Gerencia um portfólio diversificado separado para gerar receita passiva e reduzir o drawdown geral.

## Fluxo de Comunicação Entre Agentes

1.  **Registro:** Quando um agente é iniciado, ele chama `register_with_orchestrator()`, enviando seu ID, nome e endpoint (ex: `http://kamila:8000`) para o Orquestrador.
2.  **Envio de Mensagem:** O Agente A quer enviar uma mensagem para o Agente B.
3.  O Agente A chama seu próprio método `send_message("agent-b", {"key": "value"})`.
4.  Este método constrói uma requisição POST para o endpoint do Orquestrador: `http://orchestrator:8000/agents/agent-b/message`.
5.  **Encaminhamento da Mensagem:** O Orquestrador recebe a requisição. Ele procura por "agent-b" em seu registro para encontrar seu endpoint (ex: `http://agent-b:8000`).
6.  O Orquestrador encaminha a mensagem fazendo uma requisição POST para `http://agent-b:8000/message`.
7.  **Recepção da Mensagem:** O servidor FastAPI integrado do Agente B recebe a mensagem em seu endpoint `/message`.
8.  O método `handle_message` no Agente B é acionado, permitindo que ele processe a mensagem e tome uma atitude.
