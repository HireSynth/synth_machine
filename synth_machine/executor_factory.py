from synth_machine.executors.base import BaseExecutor
from synth_machine.executors.openai import OpenAIExecutor
from synth_machine.executors.togetherai import TogetherAIExecutor
from synth_machine.executors.anthropic import AnthropicExecutor
from synth_machine.executors.mock import MockExecutor


def get_executor(name: str) -> BaseExecutor:
    return {
        "openai": OpenAIExecutor(),
        "togetherai": TogetherAIExecutor(),
        "anthropic": AnthropicExecutor(),
        "mock": MockExecutor(),
    }[name]
