# Usa uma imagem oficial do Python como imagem base
FROM python:3.9-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia o arquivo de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código-fonte da aplicação do host para o contêiner.
COPY ./src /app/src

# Torna a porta 8000 disponível para fora deste contêiner
EXPOSE 8000

# Define a variável de ambiente
ENV PYTHONPATH=/app

# Executa a aplicação
CMD ["uvicorn", "src.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
