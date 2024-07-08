import json
import logging
import itertools
import uuid
from json.decoder import JSONDecodeError
from typing import List, Optional

from jsonschema import validate  # type: ignore
from jsonschema.exceptions import ValidationError  # type: ignore
from object_store import ObjectStore
from partial_json_parser import loads, OBJ
from transitions import Machine

from synth_machine.operator_setup import (
    prompt_setup,
    prompt_for_transition,
    tool_setup,
    rag_query_setup,
)
from synth_machine.runners import (
    jq_runner,
    tool_runner,
    STORAGE_PREFIX,
    STORAGE_OPTIONS,
)
from synth_machine.cost import BaseCost
from synth_machine.tools import Tool
from synth_machine.synth_definition import (
    Output,
    Input,
    Transition,
    synth_definition_setup,
)
from synth_machine.rag import RAG

try:
    from enum import StrEnum
except ImportError:
    # For python versions <3.11, using aenum for backward compatibility
    from aenum import StrEnum


class Model:
    pass


class TransitionError(Exception):
    pass


class YieldTasks(StrEnum):  # type: ignore
    CHUNK = "CHUNK"
    MODEL_CONFIG = "MODEL_CONFIG"
    SET_MEMORY = "SET_MEMORY"
    SET_ACTIVE_OUTPUT = "SET_ACTIVE_OUTPUT"


class FailureState(StrEnum):  # type: ignore
    FAILED = "FAILED"
    LOOP_FAILURE = "LOOP_FAILED"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"
    NOT_IMPLEMENTED = "NOT IMPLEMENTED"


class PostProcessTasks(StrEnum):  # type: ignore
    JQ = "jq"


class OperationPriority(StrEnum):  # type: ignore
    APPEND = "append"
    INTERLEAVE = "interleave"
    JINJA = "jinja"
    PROMPT = "prompt"
    RESET = "reset"
    UDF = "udf"
    TOOL = "tool"
    RAG = "rag"


class Synth(BaseCost):
    JSONSCHEMA_PRELUDE = {"$schema": "http://json-schema.org/draft-04/schema#"}

    def __init__(
        self,
        config: dict,
        memory: dict = {},
        store: ObjectStore = ObjectStore(STORAGE_PREFIX, STORAGE_OPTIONS),
        user: str = str(uuid.uuid4()),
        session_id: str = str(uuid.uuid4()),
        tools: List[Tool] = [],
        rag_runner: Optional[RAG] = None,
        user_defined_functions: dict = {},
    ) -> None:
        self.config = synth_definition_setup(config)
        self.user = user
        self.session_id = session_id
        if user_defined_functions:
            logging.warning(
                "Experimental: User Defined Functions are ran at the users risk!"
            )
            self.user_defined_functions = user_defined_functions
        else:
            self.user_defined_functions = {}
        self.transitions = list(
            map(
                lambda t: {
                    "trigger": t.trigger,
                    "source": t.source,
                    "dest": t.dest,
                },
                self.config.transitions,
            )
        )
        self.state_names = list(map(lambda s: s.name, self.config.states))
        self.memory: dict = self.config.initial_memory | memory
        self._model = Model()
        self.default_model_config = self.config.default_model_config
        self._machine = Machine(
            auto_transitions=False,
            initial=self.config.initial_state,
            model=self._model,
            states=self.state_names,
            transitions=self.transitions,
        )
        self.buffer = {}
        self.store = store
        self.tools = tools
        self.rag_runner = rag_runner

    def current_state(self) -> str:
        return self._model.state  # type: ignore

    def interfaces_for_available_triggers(
        self, state: Optional[str] = None
    ) -> List[Transition]:
        return [
            transition
            for transition in self.config.transitions
            if transition.trigger
            in self._machine.get_triggers(state or self.current_state())
        ]

    def get_raw_state(self, state: str):
        return [s for s in self.config.states if s.name == state][0]

    def machine_update(self, transition, set_active_trigger=False, state=None):
        return [
            "MACHINE_UPDATE",
            self.interfaces_for_available_triggers(state=state or transition.dest),
            self.memory,
            self.current_state(),
            transition.trigger if set_active_trigger else "",
        ]

    async def post_process(
        self, output_key: str, output_definition: Output, chunk: str
    ):
        new_buffer = f"{self.buffer.get(output_key, '')}{chunk}"
        if new_buffer != self.buffer.get(output_key, ""):
            self.buffer[output_key] = new_buffer
            try:
                result = self.memory | loads(str(self.buffer[output_key]), OBJ).output
            except Exception:
                result = self.memory
        else:
            result = self.memory
        operation_list = [
            operation
            for operation in PostProcessTasks  # type: ignore
            if getattr(output_definition, operation, None)
        ]
        operation = operation_list[0] if operation_list else None
        match operation:
            case PostProcessTasks.JQ:
                jq_result = jq_runner(
                    getattr(output_definition, operation),
                    result,
                    output_definition.schema_dict,
                )
                if jq_result:
                    self.memory[output_key] = jq_result
                    yield [PostProcessTasks.JQ, output_key, jq_result]
                yield []
            case _:
                yield []

    async def run_task(
        self,
        inputs: Input,
        transition: Transition,
        output_key: str,
        output_definition: Output,
        retries: int = 3,
        loop: bool = False,
    ):
        yield [YieldTasks.SET_ACTIVE_OUTPUT, output_key]
        schema = output_definition.schema_dict

        # TODO: find a nicer way to ensure tests don't reference the finished memory object out of order
        yield [
            YieldTasks.SET_MEMORY,
            output_key,
            json.loads(json.dumps(self.memory.get(output_key, {}))),
        ]

        predicted = ""
        predicted_json = ""

        operation_list = [
            operation
            for operation in OperationPriority  # type: ignore
            if getattr(output_definition, operation, None)
        ]
        operation = operation_list[0] if operation_list else None
        match operation:
            case OperationPriority.UDF:
                logging.debug(f"Custom user defined function for output: {output_key}")

                if output_definition.udf not in self.user_defined_functions.keys():
                    yield [
                        FailureState.FAILED,
                        output_key,
                        f"Method: {output_definition.udf} not in registered user defined functions: {self.user_defined_functions.keys()}",
                    ]
                self.memory[output_key] = self.user_defined_functions[
                    output_definition.udf
                ](self.memory)

            case OperationPriority.RAG:
                logging.debug(f"RAG retrieval for output: {output_key}")
                match output_definition.operation:
                    # TODO: Add "chunk" and "embed" cases to create dynamic RAG
                    case "query":
                        rag_config, err = rag_query_setup(
                            output_definition, inputs, self.config.default_rag_config
                        )
                        if err or not rag_config:
                            logging.error(f"RAG query setup failure: {err}")
                            yield [FailureState.FAILED, output_key, err]
                            return

                        self.memory[output_key] = await self.rag_runner.query(  # type: ignore
                            rag_config["query"], rag_config["config"]
                        )
                    case _:
                        yield [
                            FailureState.NOT_IMPLEMENTED,
                            output_key,
                            f"RAG Operation: {output_definition.get('operation')} not implemented yet",
                        ]
            case OperationPriority.JINJA:
                template, _ = prompt_for_transition(
                    inputs=inputs, prompt_template=output_definition.jinja
                )
                self.memory[output_key] = template
                yield [
                    YieldTasks.SET_MEMORY,
                    output_key,
                    json.loads(json.dumps(template)),
                ]
            case OperationPriority.INTERLEAVE:
                keys = [
                    self.memory.get(x)
                    for x in getattr(
                        output_definition, OperationPriority.INTERLEAVE, ""
                    )
                    if self.memory.get(x)
                ]
                output = []
                for zipped in itertools.zip_longest(*keys):  # type: ignore
                    temp = {}
                    for key in zipped:
                        if key is None:
                            pass
                        elif isinstance(key, dict):
                            temp = {**temp, **key}
                        else:
                            temp[str(OperationPriority.INTERLEAVE)] = key
                    output.append(temp)
                self.memory[output_key] = output
                yield [
                    YieldTasks.SET_MEMORY,
                    output_key,
                    json.loads(json.dumps(keys)),
                ]
            case OperationPriority.TOOL:
                tool_config, err = await tool_setup(
                    tools=self.tools,
                    output_definition=output_definition,
                    inputs=inputs,
                    id=str(self.session_id),
                )
                if err or not tool_config:
                    logging.error(err)
                    yield [FailureState.FAILED, output_key, err]
                    return
                logging.info(f"Tool config: {tool_config}")
                predicted_json = await tool_runner(
                    store=self.store, tool_config=tool_config
                )

                if not predicted_json:
                    yield [
                        FailureState.FAILED,
                        output_key,
                        f"Failed to call tool {tool_config}",
                    ]

                logging.debug(f"Tool output: {predicted_json}")
                if loop:
                    self.memory[output_key].append(predicted_json)
                    logging.debug(
                        f"➕ Tool Appended {output_key}:{self.memory[output_key]}"
                    )

                else:
                    self.memory[output_key] = predicted_json
                    logging.debug(
                        f"💾 Tool Saved {output_key}:{self.memory[output_key]}"
                    )

                token_cost = tool_config.tokens.execution
                token_usage = await self.record_tool_token_usage(
                    self.user, self.session_id, tool_config, token_cost
                )
                yield [
                    "TOOL_OUTPUT",
                    output_key,
                    token_usage,
                    tool_config.tool_id,
                ]
                yield [
                    YieldTasks.SET_MEMORY,
                    output_key,
                    json.loads(json.dumps(predicted_json)),
                ]
            case OperationPriority.PROMPT:
                llm_config, err = await prompt_setup(
                    output_definition=output_definition,
                    inputs=inputs,
                    default_model_config=self.default_model_config,
                    transition_model_config=transition.config,  # type: ignore
                )
                if err or not llm_config:
                    logging.error(err)
                    yield [FailureState.FAILED, output_key, err]
                    return

                while True:
                    executor = {"executor": llm_config.model_config.executor}
                    yield [YieldTasks.MODEL_CONFIG, output_key, executor]
                    logging.debug(
                        f"🤖 Execution started ({llm_config.model_config.executor})"
                    )
                    llm_name = llm_config.model_config.llm_name
                    tokens = {
                        "input": 0,
                        "output": 0,
                    }
                    async for token, token_info in llm_config.executor.generate(
                        user_prompt=llm_config.user_prompt,
                        system_prompt=llm_config.system_prompt,
                        json_schema=schema,
                        model_config=llm_config.model_config,
                        user=self.user,
                    ):
                        predicted = f"{predicted}{str(token)}"
                        stage = token_info.get("token_type", "output")
                        tokens_used = token_info.get("tokens")
                        token_cost_per_chunk = await self.calculate_chunk_cost(
                            stage, llm_config, tokens_used
                        )

                        tokens[stage] += token_cost_per_chunk
                        yield [
                            str(YieldTasks.CHUNK),
                            output_key,
                            token,
                            token_cost_per_chunk,
                            tokens_used,
                            stage,
                            llm_name,
                        ]
                    await self.record_prompt_token_usage(
                        self.user,
                        self.session_id,
                        llm_config,
                        input_tokens=tokens.get("input", 0),
                        output_tokens=tokens.get("output", 0),
                    )  # type: ignore
                    logging.debug("🤖 Execution complete")

                    logging.debug(f"{predicted.strip()}")

                    if schema and schema.get("type") == "string":
                        predicted_json = predicted
                    else:
                        try:
                            predicted_json = llm_config.executor.post_process(
                                json.loads(predicted.strip())
                            )  # type: ignore
                            validate(
                                instance=predicted_json,
                                schema=self.JSONSCHEMA_PRELUDE | schema,  # type: ignore
                            )

                        except (
                            ValidationError,
                            JSONDecodeError,
                        ) as e:
                            logging.error(f"❌ Failed validation with {e}")
                            if retries > 0:
                                logging.warn(f"🔁 Retrying, {retries} left")
                                predicted = ""
                                predicted_json = ""
                                retries -= 1
                                continue
                            yield [
                                FailureState.OUTPUT_VALIDATION_FAILED,
                                output_key,
                            ]
                            self._model.state = transition.source  # type: ignore
                            return
                    logging.debug("✅ Validated")
                    yield [
                        "OUTPUT_VALIDATION_SUCCEEDED",
                        output_key,
                    ]
                    if loop:
                        self.memory[output_key].append(predicted_json)
                        logging.debug(
                            f"➕ LLM Appended {output_key}:{self.memory[output_key]}"
                        )
                    else:
                        self.memory[output_key] = predicted_json
                        logging.debug(
                            f"💾 LLM Saved {output_key}:{self.memory[output_key]}"
                        )
                    return
            case OperationPriority.APPEND:
                memory_keys = getattr(output_definition, operation, [])

                if self.memory.get(output_key) is None:
                    self.memory[output_key] = []
                for memory_key in memory_keys:
                    item = self.memory.get(memory_key)
                    if item is not None:
                        self.memory[output_key].append(item)
                yield [
                    YieldTasks.SET_MEMORY,
                    output_key,
                    json.loads(json.dumps(self.memory.get(output_key))),
                ]
            case OperationPriority.RESET:
                if isinstance(self.memory[output_key], list):
                    self.memory[output_key] = []
                elif isinstance(self.memory[output_key], str):
                    self.memory[output_key] = ""
                else:
                    self.memory[output_key] = {}
            case _:
                return  # output is a NOOP
        yield ["OUTPUT_COMPLETED", output_key]

    async def execute_output(
        self,
        inputs,
        transition,
        output_key,
        output_definition,
        post_process_tasks,
        loop=False,
    ):
        logging.info(f"Starting output: {transition.trigger}.{output_key}")
        async for event in self.run_task(
            inputs=inputs,
            transition=transition,
            output_key=output_key,
            output_definition=output_definition,
            loop=loop,
        ):
            if event and len(event) > 3 and event[0] in YieldTasks.CHUNK:
                for (
                    post_process_key,
                    post_process_definition,
                ) in post_process_tasks:
                    post_process = self.post_process(
                        output_key=post_process_key,
                        output_definition=post_process_definition,
                        chunk=event[2],
                    )
                    if post_process:
                        async for post_process_event in post_process:
                            yield post_process_event
            yield event
        logging.info(f"Complete output: {transition.trigger}.{output_key}")

    async def execute_for_trigger(self, initial_trigger):
        transition = self._transition_for_trigger(initial_trigger)
        # State-level loop, facilitates 'after' on transition
        while True:
            # Show interface for the *next* state
            yield self.machine_update(transition=transition, set_active_trigger=True)

            post_process_tasks = [
                (output_definition.key, output_definition)
                for output_definition in transition.outputs
                for post_processing_task in PostProcessTasks  # type: ignore
                if getattr(output_definition, post_processing_task, None)
            ]
            for output_definition in transition.outputs:
                output_key = output_definition.key
                inputs = {
                    input_item.key: self.memory.get(input_item.key)
                    for input_item in transition.inputs
                }
                loop = output_definition.loop
                if loop is not None:
                    self.memory[output_key] = []
                    for matrix in loop.matrix:
                        for loop_var, memory_key_looped in matrix.items():
                            if isinstance(memory_key_looped, list):
                                loop = memory_key_looped
                            else:
                                loop = self.memory.get(memory_key_looped, [])
                            for item in loop:
                                loop_inputs = {
                                    **inputs,
                                    loop_var: item,
                                }
                                yield ["INPUTS", loop_inputs]
                                async for event in self.execute_output(
                                    inputs=loop_inputs,
                                    transition=transition,
                                    output_key=output_key,
                                    output_definition=output_definition,
                                    post_process_tasks=post_process_tasks,
                                    loop=True,
                                ):
                                    yield event
                                    if (
                                        event
                                        and len(event) > 1
                                        and event[0] in FailureState._member_names_
                                    ):
                                        return
                else:
                    yield ["INPUTS", inputs]
                    async for event in self.execute_output(
                        inputs=inputs,
                        transition=transition,
                        output_key=output_key,
                        output_definition=output_definition,
                        post_process_tasks=post_process_tasks,
                    ):
                        yield event
                        if (
                            event
                            and len(event) > 1
                            and event[0] in FailureState._member_names_
                        ):
                            return
                for (
                    post_process_key,
                    post_process_definition,
                ) in post_process_tasks:
                    post_process = self.post_process(
                        output_key=post_process_key,
                        output_definition=post_process_definition,
                        chunk="",
                    )
                    if post_process:
                        async for post_process_event in post_process:
                            yield post_process_event

            self._model.trigger(transition.trigger)  # type: ignore
            yield ["TRANSITION_COMPLETED", transition.trigger]

            if after := transition.after:
                if "memory_key:" in after:
                    memory_key = after.split(":")[1]
                    if self.memory.get(memory_key):
                        transition = self._transition_for_trigger(
                            self.memory[memory_key]
                        )
                    else:
                        logging.error(f"❌ Memory key {memory_key} not found")
                else:
                    transition = self._transition_for_trigger(after)
            else:
                break
        yield self.machine_update(transition=transition)

    def _transition_for_trigger(self, trigger: str):
        return [
            transition
            for transition in self.config.transitions
            if transition.trigger == trigger
        ][0]

    async def streaming_trigger(self, trigger: str, params: Optional[dict] = None):
        if params is not None and len(params) > 0:
            self.memory = self.memory | params

        async for event in self.execute_for_trigger(initial_trigger=trigger):  # type: ignore
            yield event

    async def trigger(self, trigger: str, params: dict = {}):
        filtered_transition = list(
            filter(
                lambda transition: transition.trigger == trigger,
                self.interfaces_for_available_triggers(),
            )
        )
        if not len(filtered_transition):
            raise TransitionError(
                f"No transition: {trigger} exists at state: {self.current_state()}"
            )
        transition_outputs = [val.key for val in filtered_transition[0].outputs]  # type: ignore

        async for value in self.streaming_trigger(trigger, params=params):
            logging.debug(value)
            if value and value[0] == FailureState.FAILED:
                logging.error(f"Failure: {value}")

        return {output: self.memory[output] for output in transition_outputs}
