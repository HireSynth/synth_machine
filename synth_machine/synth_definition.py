from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from synth_machine.machine_config import ModelConfig


class Loop(BaseModel):
    matrix: list[dict] = []


class Interface(BaseModel):
    componentName: str
    key: str
    ui_params: Optional[dict] = None


class State(BaseModel):
    interface: Optional[List[Interface]] = None
    name: str


class Input(BaseModel):
    description: Optional[str] = None
    examples: Optional[List[str]] = None
    key: str
    schema_dict: Optional[dict] = Field(alias="schema", default=None)
    ui_params: Optional[dict] = None
    ui_type: Optional[str] = None


class Output(BaseModel):
    append: Optional[List[str]] = None
    input_name_map: Optional[dict] = None
    key: str
    config: Optional[ModelConfig] = Field(alias="model_config", default=None)
    prompt: Optional[str] = None
    reset: Optional[bool] = None
    schema_dict: Optional[dict] = Field(alias="schema", default=None)
    system_prompt: Optional[str] = None
    tool: Optional[str] = None
    loop: Optional[Loop] = None
    jinja: Optional[str] = None
    interleave: Optional[list] = None
    route: Optional[str] = None
    jq: Optional[str] = None

    @model_validator(mode="before")
    def check_prompts_schema(cls, values):
        if values.get("prompt", False) or values.get("system_prompt", False):
            if not values.get("schema", False):
                raise ValueError(
                    f"All prompts require schema to set. Not set on: {values['key']}",
                )
        return values

    @model_validator(mode="before")
    def check_tool_route(cls, values):
        if values.get("tool", False):
            if not values.get("route", False):
                raise ValueError(
                    f"All tools require `route` to be set, not set on: {values['key']}",
                )
        return values


class Transition(BaseModel):
    after: Optional[str] = None
    default: Optional[bool] = None
    dest: str
    inputs: Optional[List[Input]] = []
    outputs: Optional[List[Output]] = []
    source: str
    trigger: str
    config: Optional[ModelConfig] = Field(alias="model_config", default={})


class ShareProfile(BaseModel):
    description: Optional[str] = None
    image: Optional[str] = None
    name: Optional[str] = None


class SynthDefinition(BaseModel):
    default_model_config: Optional[ModelConfig] = ModelConfig()
    initial_memory: dict = {}
    initial_state: str
    shareProfile: Optional[ShareProfile] = None
    states: List[State]
    transitions: List[Transition]

    @model_validator(mode="after")
    def check_initial_state(cls, values):
        states = values.states
        initial_state = values.initial_state
        state_names = [state.name for state in states]
        if initial_state not in state_names:
            raise ValueError(
                f"initial_state {initial_state} is not a valid state name. Must be one of {state_names}"
            )
        transitions = values.transitions
        triggers = [t.trigger for t in transitions]
        for transition in transitions:
            if transition.after is None:
                continue
            if "memory_key" in str(transition.after):
                continue
            if str(transition.after) not in triggers:
                raise ValueError(
                    f"After value {str(transition.after)} is not part of available triggers {triggers}"
                )
        return values
