from typing import AsyncGenerator, Optional

from synth_machine.machine_config import ModelConfig
from synth_machine.providers.base import BaseProvider


class MockProvider(BaseProvider):
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

class MockJsonParseFailureProvider(BaseProvider):
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


class MockJsonProvider(BaseProvider):
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

class MockProviderFactory:
    def __init__(self):
        super().__init__()
        self.providers = {
            "mock": MockProvider,
            "mock_json_parse_failure": MockJsonParseFailureProvider,
            "mock_json": MockJsonProvider,
             
        }
