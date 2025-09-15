# Usa uma imagem oficial do Python como imagem base
FROM python:3.9-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Argumento para o nome do agente, que será passado durante o build
ARG AGENT_NAME

# Define uma variável de ambiente a partir do argumento de build.
# Isso torna o nome do agente disponível em tempo de execução.
ENV AGENT_NAME=${AGENT_NAME}

# Copia o arquivo de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código-fonte da aplicação
COPY ./src /app/src

# Define o python path
ENV PYTHONPATH=/app

# Executa o agente especificado usando um shell para substituir a variável de ambiente
CMD ["/bin/sh", "-c", "python -u -m src.agents.${AGENT_NAME}.main"]
