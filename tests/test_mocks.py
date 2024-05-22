from typing import Optional

from synth_machine.machine_config import ModelConfig


class MockExecutor:
    @staticmethod
    def post_process(output):
        return output

    @staticmethod
    async def generate(
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ):
        yield ("", {"tokens": 5, "token_type": "input"})
        yield ("You are an automated chicken", {"tokens": 1, "token_type": "output"})


class MockJsonParseFailureExecutor:
    @staticmethod
    def post_process(output):
        return output

    @staticmethod
    async def generate(
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ):
        yield ('{"abc": "def"', {"tokens": 1, "token_type": "output"})


class MockJsonExecutor:
    @staticmethod
    def post_process(output):
        return output

    @staticmethod
    async def generate(
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ):
        yield ('{"abc": "def"}', {"tokens": 1, "token_type": "output"})
