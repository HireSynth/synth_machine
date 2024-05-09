from src.executors.base import BaseExecutor
from src.executors.openai import OpenAIExecutor
from src.executors.vertex import VertexExecutor
from src.executors.togetherai import TogetherAIExecutor
from src.executors.anthropic import AnthropicExecutor


def get_executor(name: str) -> BaseExecutor:
    return {
        "openai": OpenAIExecutor(),
        "google": VertexExecutor(),
        "togetherai": TogetherAIExecutor(),
        "anthropic": AnthropicExecutor(),
    }[name]
