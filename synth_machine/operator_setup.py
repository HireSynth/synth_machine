import logging
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional, Tuple
from jinja2 import Template, StrictUndefined
from synth_machine.executor_factory import get_executor
from synth_machine.executors.base import BaseExecutor
from synth_machine.machine_config import ModelConfig
from synth_machine.rag import RAGConfig
from synth_machine.synth_definition import Output, Input
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class SynthConfig:
    executor: BaseExecutor
    model_config: ModelConfig
    system_prompt: Optional[str]
    user_prompt: str


@dataclass
class ToolTokenUseage:
    execution: float
    multiplier: float


@dataclass
class ToolConfig:
    tool_id: str
    payload: dict
    output_mime_types: list[str]
    tool_path: str
    tokens: ToolTokenUseage


async def tool_setup(
    output_definition: Output, inputs: dict, id: str, tools: list
) -> Tuple[Optional[ToolConfig], Optional[str]]:
    tool_search = [tool for tool in tools if tool.name == output_definition.tool]
    if not tool_search:
        error = f"Tool not found: '{output_definition.tool}'. Available tools: {[tool.name for tool in tools]}"
        logging.error(error)
        return (None, error)
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
    return (
        ToolConfig(
            tool_id=tool.id,  # type: ignore
            payload=tool_payload,
            output_mime_types=output_mime_types,
            tool_path=tool_path,
            tokens=ToolTokenUseage(
                execution=tool.tokens_per_execution,
                multiplier=tokens_multiplied,
            ),
        ),
        None,
    )


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
            logging.error(f"Undefined variable in prompt: {e}")
            return ("", str(e))
        return (dedent(prompt).strip(), None)
    return ("", f"Prompt template not provided, got {prompt_template}")


def rag_query_setup(
    output_definition: Output, inputs: Input, default_rag_config: RAGConfig
) -> Tuple[Optional[dict], Optional[str]]:
    rag_prompt, prompt_err = prompt_for_transition(
        inputs=inputs,
        prompt_template=output_definition.rag,
    )
    if prompt_err:
        return (None, prompt_err)
    logging.debug(f"""RAG PROMPT: <<<{rag_prompt}>>>""")

    rag_config = RAGConfig(
        **(
            default_rag_config.dict() | output_definition.rag_config.dict()
            if output_definition.rag_config
            else default_rag_config.dict()
        )
    )
    return ({"query": rag_prompt, "config": rag_config}, None)


async def prompt_setup(
    output_definition: Output,
    inputs: dict,
    default_model_config: ModelConfig,
    transition_model_config: ModelConfig,
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
            default_model_config.model_dump()
            | transition_model_config.model_dump(exclude_none=True)
            | output_definition.config.model_dump(exclude_none=True)  # type: ignore
        )
    )

    logging.debug(f"Model config {model_config}")
    executor = get_executor(name=model_config.executor)  # type: ignore

    return (
        SynthConfig(
            executor=executor,
            model_config=model_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        ),
        None,
    )
