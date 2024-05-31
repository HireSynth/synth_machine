import logging
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionNamedToolChoiceParam,
    ChatCompletionToolParam,
)

from synth_machine.executors.base import BaseExecutor, singleton
from synth_machine.machine_config import (
    ModelConfig,
    calculate_input_tokens,
)
from synth_machine.executors import OPENAI_API_KEY, DEBUG


@singleton
class OpenAIExecutor(BaseExecutor):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)  # type: ignore

    @staticmethod
    def post_process(output: dict) -> dict:
        return output.get("output", {})

    async def generate(
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ) -> AsyncGenerator:
        # PyRight doesn't understand the openai library has been updated
        messages = (
            [
                {"role": "system", "content": system_prompt},
            ]
            if system_prompt
            else []
        )
        messages.append(
            {"role": "user", "content": str(user_prompt)},
        )

        if function_calling := (json_schema and json_schema.get("type") != "string"):
            tools = [
                ChatCompletionToolParam(
                    {
                        "type": "function",
                        "function": {
                            "name": "output",
                            "parameters": {
                                "type": "object",
                                "properties": {"output": json_schema},
                                "required": ["output"],
                            },
                        },
                    }
                )
            ]
            tool_choice = ChatCompletionNamedToolChoiceParam(
                {"type": "function", "function": {"name": "output"}}
            )

            response = await self.client.chat.completions.create(
                model=model_config.llm_name,
                messages=messages,  # type: ignore
                temperature=model_config.temperature,
                stream=True,
                tools=tools,
                max_tokens=model_config.max_tokens,
                tool_choice=tool_choice,
                user=user,
            )
        else:
            response = await self.client.chat.completions.create(
                model=model_config.llm_name,
                messages=messages,  # type: ignore
                temperature=model_config.temperature,
                stream=True,
                max_tokens=model_config.max_tokens,
                user=user,
            )

        input_tokens = calculate_input_tokens(system_prompt, user_prompt)
        yield ("", {"tokens": input_tokens, "token_type": "input"})  # type: ignore

        logging.debug(f"OpenAI Response: {response}")
        async for chunk in response:
            if not chunk.choices[0].finish_reason:
                token = (
                    chunk.choices[0].delta.tool_calls[0].function.arguments
                    if function_calling
                    else chunk.choices[0].delta.content
                )
                if DEBUG:
                    print(token, end="", flush=True)
                else:
                    logging.debug({"token": token, "end": "", "flush": True})
                yield (token, {"tokens": 1, "token_type": "output"})  # type: ignore
            else:
                print()
