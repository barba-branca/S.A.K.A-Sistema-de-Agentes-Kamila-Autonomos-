import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_HEADER_NAME = "X-Internal-API-Key"
api_key_header_scheme = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

async def get_api_key(api_key_header: str = Security(api_key_header_scheme)):
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