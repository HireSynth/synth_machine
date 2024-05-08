from apps.synth_api.willow.executors.base import BaseExecutor
from apps.synth_api.willow.executors.openai import OpenAIExecutor
from apps.synth_api.willow.executors.vertex import VertexExecutor
from apps.synth_api.willow.executors.togetherai import TogetherAIExecutor
from apps.synth_api.willow.executors.anthropic import AnthropicExecutor


def get_executor(name: str) -> BaseExecutor:
    return {
        "openai": OpenAIExecutor(),
        "google": VertexExecutor(),
        "togetherai": TogetherAIExecutor(),
        "anthropic": AnthropicExecutor(),
    }[name]
