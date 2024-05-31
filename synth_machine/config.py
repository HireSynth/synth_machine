import logging
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional, Tuple
from jinja2 import Template, StrictUndefined

from synth_machine.executor_factory import get_executor
from synth_machine.executors.base import BaseExecutor
from synth_machine.machine_config import ModelConfig
from synth_machine.synth_definition import Output, Input
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class SynthConfig:
    executor: BaseExecutor
    model_config: ModelConfig
    system_prompt: Optional[str]
    user_prompt: str


async def tool_setup(
    output_definition: Output, inputs: dict, id: str, user: str, tools: list
) -> dict:
    tool_search = [tool for tool in tools if tool.name == output_definition.tool]
    if not tool_search:
        logging.warning(
            f"Tool not found: '{output_definition.tool}'. Available tools: {[tool.name for tool in tools]}"
        )
        return {}
    tool = tool_search[0]
    tool_path = f"{tool.api_endpoint}{output_definition.route}"
    output_mime_types = [
        response_mime
        for response_mime in tool.api_spec["paths"][output_definition.route]["post"][
            "responses"
        ]["200"]["content"].keys()
        if response_mime != "application/json"
    ]
    # TODO: add back in validation using the api spec response schema.

    tool_payload = {
        key: (
            inputs[value]
            if value in inputs.keys()
            else Template(value, undefined=StrictUndefined).render(**inputs)
        )
        for key, value in output_definition.input_name_map.items()  # type: ignore
    }

    if tool.token_multiplier != 0:
        raw_tokens = sum([len(enc.encode(value)) for value in tool_payload.values()])
        tokens_multiplied = raw_tokens * tool.token_multiplier
    else:
        tokens_multiplied = 0

    logging.debug(f"Tool payload: {tool_payload}")
    return {
        "tool_id": tool.id,  # type: ignore
        "owner": user,
        "payload": tool_payload,
        "output_mime_types": output_mime_types,
        "tool_path": tool_path,
        "tokens": {
            "execution": tool.tokens_per_execution,
            "multiplier": tokens_multiplied,
        },
    }


def prompt_for_transition(
    inputs: Optional[dict], prompt_template: Optional[str]
) -> Tuple[str, Optional[str]]:
    if prompt_template:
        try:
            prompt = Template(
                prompt_template,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=StrictUndefined,
            ).render(
                **inputs  # type: ignore
            )
        except Exception as e:
            logging.warning(f"Undefined variable in prompt: {e}")
            return ("", str(e))
        return (dedent(prompt).strip(), None)
    return ("", f"Prompt template not provided, got {prompt_template}")


async def prompt_setup(
    output_definition: Output, inputs: Input, default_model_config: dict
) -> Tuple[Optional[SynthConfig], Optional[str]]:
    user_prompt_template = output_definition.prompt
    user_prompt, prompt_err = prompt_for_transition(
        inputs=inputs,
        prompt_template=user_prompt_template,
    )
    if prompt_err:
        return (None, prompt_err)
    logging.debug(f"""User PROMPT: <<<{user_prompt}>>>""")

    system_prompt_template = output_definition.system_prompt
    if system_prompt_template:
        system_prompt, system_err = prompt_for_transition(
            inputs=inputs,
            prompt_template=system_prompt_template,
        )
        if system_err:
            return (None, system_err)
    else:
        system_prompt = None
    logging.debug(f"""System PROMPT: <<<{system_prompt}>>>""")

    model_config = ModelConfig(
        **(
            default_model_config | output_definition.config.dict()
            if output_definition.config
            else default_model_config
        )
    )

    logging.debug(f"Model config {model_config}")
    executor = get_executor(name=model_config.executor)

    return (
        SynthConfig(
            executor=executor,
            model_config=model_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        ),
        None,
    )
