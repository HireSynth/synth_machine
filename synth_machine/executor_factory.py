from synth_machine.executors.base import BaseExecutor
from synth_machine.executors.lorem import LoremExecutor
from typing import Dict
import os


EXECUTORS: Dict[str, BaseExecutor] = {"lorem": LoremExecutor()}
if "OPENAI_API_KEY" in os.environ.keys():
    try:
        from synth_machine.executors.openai import OpenAIExecutor

        EXECUTORS["openai"] = OpenAIExecutor()
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Please install synth_machine with extra 'openai'")
if "ANTHROPIC_API_KEY" in os.environ.keys():
    try:
        from synth_machine.executors.anthropic import AnthropicExecutor

        EXECUTORS["anthropic"] = AnthropicExecutor()
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Please install synth_machine with extra 'anthropic'")
if "TOGETHER_API_KEY" in os.environ.keys():
    try:
        from synth_machine.executors.togetherai import TogetherAIExecutor

        EXECUTORS["togetherai"] = TogetherAIExecutor()
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "Please install synth_machine with extra 'togetherai'"
        )


def get_executor(name: str) -> BaseExecutor:
    return EXECUTORS[name]
