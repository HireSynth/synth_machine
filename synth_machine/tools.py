from pydantic import BaseModel


class Tool(BaseModel):
    name: str
    api_endpoint: str
    api_spec: dict
    id: int = -1
    tokens_per_execution: float = 0
    token_multiplier: float = 0
