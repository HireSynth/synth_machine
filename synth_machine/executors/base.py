from typing import AsyncGenerator, Optional

from synth_machine.machine_config import ModelConfig


# https://peps.python.org/pep-0318/#examples
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class BaseExecutor:
    @staticmethod
    def post_process(output: dict) -> dict:
        raise NotImplementedError

    def generate(
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ) -> AsyncGenerator:
        raise NotImplementedError
