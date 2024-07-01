from typing import Optional, List
from synth_machine.machine_config import ModelConfig
from pydantic import BaseModel

try:
    from enum import StrEnum
except ImportError:
    # For python versions <3.11, using aenum for backward compatibility
    from aenum import StrEnum

default_model_config_list = [
    ModelConfig(executor="togetherai", llm_name="Qwen/Qwen2-72B-Instruct"),
    ModelConfig(executor="togetherai", llm_name="meta-llama/Llama-3-70b-chat-hf"),
    ModelConfig(
        executor="togetherai", llm_name="mistralai/Mixtral-8x22B-Instruct-v0.1"
    ),
]


class LengthOperators(StrEnum):  # type: ignore
    equals = "equals"
    greater_than = "greater_than"
    gt = "gt"
    less_than = "less_than"
    lt = "less_than"


class LengthTest(BaseModel):
    operator: LengthOperators
    test_value: int


class PromptTest(BaseModel):
    rule: str
    test_value: int = 2
    additional_variables: List[str] = []


class TestOptions(StrEnum):  # type: ignore
    length = "length"
    prompt = "prompt"


class OutputTest(BaseModel):
    output: str
    test: TestOptions
    testcase: PromptTest | LengthTest


class TransitionTest(BaseModel):
    trigger: str
    outputs: List[OutputTest]


class SynthTestSpec(BaseModel):
    transitions: List[TransitionTest]
    llm_config_list: Optional[List[ModelConfig]] = default_model_config_list


# Outputs
class ScoreOptions(StrEnum):  # type: ignore
    green = "green"
    yellow = "yellow"
    red = "red"


class IndividualPromptTestOutput(BaseModel):
    llm_name: str
    score: ScoreOptions
    explanation: str


class OutputTestResponse(BaseModel):
    test: TestOptions
    rule: str
    success: bool
    score: float
    test_error: bool = False
    message: Optional[str] = None
    results: Optional[List[IndividualPromptTestOutput]] = None


class TransitionTestResponse(BaseModel):
    trigger: str
    outputs: List[OutputTestResponse]
    passed: bool
    num_success: int
    num_failure: int
    num_test_errors: int = 0
    failure_rules: List[str] = []


class SynthTestResponse(BaseModel):
    transitions: List[TransitionTestResponse]
    passed: bool
    num_success: int
    num_failure: int
    num_test_errors: int = 0
    failure_rules: List[str] = []
