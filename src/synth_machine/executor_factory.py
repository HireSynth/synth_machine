from synth_machine.executors.base import BaseExecutor
from synth_machine.executors.openai import OpenAIExecutor
from synth_machine.executors.togetherai import TogetherAIExecutor
from synth_machine.executors.anthropic import AnthropicExecutor


def get_executor(name: str) -> BaseExecutor:
    return {
        "openai": OpenAIExecutor(),
        "togetherai": TogetherAIExecutor(),
        "anthropic": AnthropicExecutor(),
    }[name]
