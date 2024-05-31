from pydantic import BaseModel, Field
from typing import List, Optional
import tiktoken


class ModelConfig(BaseModel):
    executor: str = "togetherai"
    llm_name: str = Field(
        alias="model_name", default="mistralai/Mixtral-8x7B-Instruct-v0.1"
    )
    max_tokens: int = 1024
    temperature: float = 0.8
    assistant_partial: str = ""
    partial_input: Optional[str] = None
    stop: List[str] = []
    tool_use: bool = False
    tool_options: Optional[List[dict]] = None


enc = tiktoken.get_encoding("cl100k_base")


@staticmethod
def calculate_input_tokens(
    system_prompt: Optional[str],
    user_prompt: Optional[str],
    assistant_partial: str = "",
) -> int:
    system_tokens = len(enc.encode(system_prompt)) if system_prompt else 0
    user_tokens = len(enc.encode(user_prompt)) if user_prompt else 0
    assistant_tokens = len(enc.encode(assistant_partial)) if assistant_partial else 0
    return system_tokens + user_tokens + assistant_tokens
