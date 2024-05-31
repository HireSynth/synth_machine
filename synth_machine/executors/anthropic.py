import json
import logging
from typing import AsyncGenerator, Optional
from synth_machine.executors.base import BaseExecutor, singleton
from synth_machine.machine_config import (
    ModelConfig,
    calculate_input_tokens,
)
import anthropic
import tiktoken
from synth_machine.executors import ANTHROPIC_API_KEY, DEBUG


@singleton
class AnthropicExecutor(BaseExecutor):
    def __init__(self) -> None:
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)  # type: ignore

    @staticmethod
    def post_process(output: dict) -> dict:
        return output

    async def generate(
        self,
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: str = "",
    ) -> AsyncGenerator:
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

            tool_response = await self.client.beta.tools.messages.create(
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
