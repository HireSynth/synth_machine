import os
import logging
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionNamedToolChoiceParam,
    ChatCompletionToolParam,
)

from src.executors.base import BaseExecutor
from src.synth_machine_configs import (
    ModelConfig,
    calculate_input_tokens,
)
from core.settings import DEBUG


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)  # type: ignore


class OpenAIExecutor(BaseExecutor):
    @staticmethod
    def post_process(output: dict) -> dict:
        return output.get("output", {})

    async def generate(  # type: ignore
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: Optional[str],
    ) -> AsyncGenerator[str, dict]:
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

            response = await openai_client.chat.completions.create(
                model=model_config.model_name,
                messages=messages,  # type: ignore
                temperature=model_config.temperature,
                stream=True,
                tools=tools,
                max_tokens=model_config.max_tokens,
                tool_choice=tool_choice,
                user=user,
            )
        else:
            response = await openai_client.chat.completions.create(
                model=model_config.model_name,
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
