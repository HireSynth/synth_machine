from typing import AsyncGenerator, Optional

from synth_machine.machine_config import ModelConfig


class BaseExecutor:
    @staticmethod
    def post_process(output: dict) -> dict:
        raise NotImplementedError

    async def generate(
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: Optional[str],
    ) -> AsyncGenerator[str, dict]:
        raise NotImplementedError
