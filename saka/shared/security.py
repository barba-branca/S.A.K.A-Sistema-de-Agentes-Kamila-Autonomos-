import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

# Define o nome do cabeçalho que conterá a chave da API
API_KEY_HEADER_NAME = "X-Internal-API-Key"

# Cria um objeto de segurança que sabe como extrair a chave do cabeçalho
api_key_header_scheme = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)

# Lê a chave de API "verdadeira" das variáveis de ambiente
# O .env já é carregado pelo docker-compose
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

async def get_api_key(api_key_header: str = Security(api_key_header_scheme)):
    """
    Dependência do FastAPI que valida a chave de API recebida no header.

    Compara a chave recebida com a chave armazenada de forma segura nas
    variáveis de ambiente.

    Levanta uma exceção HTTPException 401 se as chaves não corresponderem.
    """
    if not INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chave de API interna não configurada no servidor."
        )

    if api_key_header != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou ausente."
        )