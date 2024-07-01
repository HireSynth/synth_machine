import logging
from typing import AsyncGenerator, Optional
from synth_machine.executors.base import BaseExecutor, singleton
from synth_machine.machine_config import (
    ModelConfig,
    calculate_input_tokens,
)
from synth_machine.executors import ANTHROPIC_API_KEY, DEBUG
from magika import Magika
import anthropic
import json
import base64
import httpx
import time


@singleton
class AnthropicExecutor(BaseExecutor):
    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)  # type: ignore
        self.magika = Magika()

    @staticmethod
    def post_process(output: dict) -> dict:
        return output

    async def get_image(self, url, retry: int = 2):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response
            except (
                httpx.RequestError,
                httpx.HTTPStatusError,
                httpx.TimeoutException,
            ) as err:
                if retry == 0:
                    raise err
                else:
                    time.sleep(0.5)
                    return await self.get_image(url, retry - 1)

    async def generate(  # type: ignore
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: Optional[str],
    ) -> AsyncGenerator[str, dict]:
        if model_config.image_url:
            response = await self.get_image(model_config.image_url)

            image_bytes = response.content
            if "Content-Type" in response.headers:
                image_media_type = response.headers["Content-Type"]
            else:
                image_media_type = self.magika.identify_bytes(image_bytes).dl.mime_type
            logging.debug(f"Image Media Type: {image_media_type}")
            image_data = base64.b64encode(image_bytes).decode("utf-8")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ]
        else:
            messages = [{"role": "user", "content": user_prompt}]

        if model_config.assistant_partial != "":
            # Anthropic supports assistant prefilling instead of system prompt
            messages.append(
                {"role": "assistant", "content": model_config.assistant_partial}
            )

        prompt_tokens = calculate_input_tokens(
            system_prompt, user_prompt, model_config.assistant_partial
        )
        yield (
            model_config.partial_input
            if model_config.partial_input is not None
            else model_config.assistant_partial,
            {
                "tokens": prompt_tokens + (395 if model_config.tool_use else 0),
                "token_type": "input",
            },
        )  # type: ignore

        wrapper = False
        if model_config.tool_use:  # type: ignore
            if model_config.tool_options is None:
                if json_schema["type"] == "array":  # type: ignore
                    logging.info("Using tool with wrapper")
                    wrapper = True
                    json_schema = {
                        "type": "object",
                        "properties": {
                            "output": {"type": "array", "items": json_schema.copy()}  # type: ignore
                        },
                    }
                tools = [
                    {
                        "name": "required_tool",
                        "description": "You must use this tool.",
                        "input_schema": json_schema,
                    }
                ]
            else:
                tools = model_config.tool_options

            tool_response = await self.client.messages.create(
                model=model_config.llm_name,
                system=system_prompt,
                max_tokens=model_config.max_tokens,
                messages=messages,
                tools=tools,
            )
            response_content = tool_response.content

            if len(response_content) == 1:
                output = response_content[0].input
                cot_response = ""
            else:
                output = response_content[1].input
                cot_response = response_content[0].text

            if wrapper:
                output = output["output"]

            yield (
                json.dumps(output),
                {
                    "tokens": calculate_input_tokens(str(output), cot_response),
                    "token_type": "output",
                },
            )  # type: ignore
        else:
            response = await self.client.messages.create(
                model=model_config.llm_name,
                system=system_prompt,
                messages=messages,  # type: ignore
                max_tokens=model_config.max_tokens,
                stream=True,
                metadata={"user_id": user},
                stop_sequences=model_config.stop,
            )  # type: ignore

            logging.debug(f"Anthropic Response: {response}")
            async for chunk in response:
                if chunk.type == "content_block_delta":
                    token = chunk.delta.text
                    if DEBUG:
                        print(token, end="", flush=True)
                    else:
                        logging.debug({"token": token, "end": "", "flush": True})
                    yield (token, {"tokens": 1, "token_type": "output"})  # type: ignore
                else:
                    print()
