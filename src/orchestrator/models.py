from pydantic import BaseModel
from typing import Optional

class Agent(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    endpoint: str

    class Config:
        frozen = True
