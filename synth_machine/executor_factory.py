from synth_machine.executors.base import BaseExecutor
from synth_machine.executors.openai import OpenAIExecutor
from synth_machine.executors.togetherai import TogetherAIExecutor
from synth_machine.executors.anthropic import AnthropicExecutor
from synth_machine.executors.lorem import LoremExecutor
from typing import Dict
import os


def get_executor(name: str) -> BaseExecutor:
    base_executor_runners: Dict[str, BaseExecutor] = {"lorem": LoremExecutor()}
    if "OPEN_API_KEY" in os.environ.keys():
        base_executor_runners["openai"] = OpenAIExecutor()
    if "ANTHROPIC_API_KEY" in os.environ.keys():
        base_executor_runners["anthropic"] = AnthropicExecutor()
    if "TOGETHER_API_KEY" in os.environ.keys():
        base_executor_runners["togetherai"] = TogetherAIExecutor()
    return base_executor_runners[name]
