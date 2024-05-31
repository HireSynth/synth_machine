from typing import AsyncGenerator, Optional

from synth_machine.executors.base import BaseExecutor, singleton
from synth_machine.machine_config import (
    ModelConfig,
    calculate_input_tokens,
)
import random
import asyncio


@singleton
class LoremExecutor(BaseExecutor):
    def __init__(self) -> None:
        self.word_catalog = [
            "lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
            "sed",
            "do",
            "eiusmod",
            "tempor",
            "incididunt",
            "ut",
            "labore",
            "et",
            "dolore",
            "magna",
            "aliqua",
            "ut",
            "enim",
            "ad",
            "minim",
            "veniam",
            "quis",
            "nostrud",
            "exercitation",
            "ullamco",
            "laboris",
            "nisi",
            "ut",
            "aliquip",
            "ex",
            "ea",
            "commodo",
            "consequat",
            "duis",
            "aute",
            "irure",
            "dolor",
            "in",
            "reprehenderit",
            "in",
            "voluptate",
            "velit",
            "esse",
            "cillum",
            "dolore",
            "eu",
            "fugiat",
            "nulla",
            "pariatur",
            "excepteur",
            "sint",
            "occaecat",
            "cupidatat",
            "non",
            "proident",
            "sunt",
            "in",
            "culpa",
            "qui",
            "officia",
            "deserunt",
            "mollit",
            "anim",
            "id",
            "est",
            "laborum",
        ]
        self.default_word_count = 50

    @staticmethod
    def post_process(output: dict) -> dict:
        return output.get("output", {})

    async def generate_lorem_sentence(self, word_count):
        # Generates realistic looking sentence sequences.
        for i in range(word_count):
            token = random.choice(self.word_catalog)
            await asyncio.sleep(0.05)
            if i == 0:
                yield f"{token.capitalize()} "
            elif i % 10 == 0:
                yield f"{token}. "
            elif (i - 1) % 10 == 0:
                yield f"{token.capitalize()} "
            elif i == (word_count - 1):
                yield f"{token}."
            else:
                yield f"{token} "

    async def generate(  # type: ignore
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: Optional[str] = None,
    ) -> AsyncGenerator[str, dict]:
        input_tokens = calculate_input_tokens(system_prompt, user_prompt)
        yield ("", {"tokens": input_tokens, "token_type": "input"})  # type: ignore

        async for token in self.generate_lorem_sentence(model_config.max_tokens):
            yield (token, {"tokens": 1, "token_type": "output"})  # type: ignore
