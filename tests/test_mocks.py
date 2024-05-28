from typing import AsyncGenerator, Optional

from synth_machine.machine_config import ModelConfig
from synth_machine.executors.base import BaseExecutor


class MockExecutor(BaseExecutor):
    @staticmethod
    def post_process(output):
        return output

    async def generate(
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ) -> AsyncGenerator:
        yield ("", {"tokens": 5, "token_type": "input"})
        yield ("You are an automated chicken", {"tokens": 1, "token_type": "output"})


class MockJsonParseFailureExecutor(BaseExecutor):
    @staticmethod
    def post_process(output):
        return output

    async def generate(
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ) -> AsyncGenerator:
        yield ('{"abc": "def"', {"tokens": 1, "token_type": "output"})


class MockJsonExecutor(BaseExecutor):
    @staticmethod
    def post_process(output):
        return output

    async def generate(
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ) -> AsyncGenerator:
        yield ('{"abc": "def"}', {"tokens": 1, "token_type": "output"})
