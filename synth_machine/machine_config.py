from pydantic import BaseModel
from typing import List, Optional
import tiktoken


class ModelConfig(BaseModel):
    executor: Optional[str] = None
    llm_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    assistant_partial: Optional[str] = None
    partial_input: Optional[str] = None
    stop: Optional[List[str]] = None
    tool_use: Optional[bool] = None
    tool_options: Optional[List[dict]] = None


default_model_config = ModelConfig(
    # Default values
    executor="togetherai",
    llm_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
    max_tokens=1024,
    temperature=0.8,
    assistant_partial="",
    partial_input=None,
    stop=[],
    tool_use=False,
    tool_options=[],
)

enc = tiktoken.get_encoding("cl100k_base")


@staticmethod
def calculate_input_tokens(
    system_prompt: Optional[str],
    user_prompt: Optional[str],
    assistant_partial: Optional[str] = "",
) -> int:
    system_tokens = len(enc.encode(system_prompt)) if system_prompt else 0
    user_tokens = len(enc.encode(user_prompt)) if user_prompt else 0
    assistant_tokens = len(enc.encode(assistant_partial)) if assistant_partial else 0
    return system_tokens + user_tokens + assistant_tokens
