from .synth_test_config import (
    TestOptions,
    OutputTest,
    SynthTestSpec,
    default_model_config_list,
    OutputTestResponse,
    SynthTestResponse,
    TransitionTestResponse,
)
from .synth_test_runner import test_prompt, test_length
from synth_machine.machine_config import ModelConfig
from synth_machine import Synth
from typing import List


def run_test(
    synth: Synth,
    test: OutputTest,
    llm_config_list: List[ModelConfig] = default_model_config_list,
) -> OutputTestResponse:
    try:
        output_result = synth.memory[test.output]
    except KeyError:
        raise Exception(
            f"Output key: {test.output}, doesn't exist in synth memory (keys: {synth.memory.keys()})"
        )

    match test.test:
        case TestOptions.prompt:
            return test_prompt(output_result, test.testcase, llm_config_list)
        case TestOptions.length:
            return test_length(output_result, test.testcase)
        case _:
            raise Exception(f"Test: '{test.test}' is not a valid test option")


def run_testset(synth: Synth, testset: SynthTestSpec) -> SynthTestResponse:
    testset_results = SynthTestResponse(
        transitions=[], passed=True, num_success=0, num_failure=0
    )
    for transition in testset.transitions:
        transition_response = TransitionTestResponse(
            trigger=transition.trigger,
            outputs=[],
            passed=True,
            num_success=0,
            num_failure=0,
        )
        for output_test in transition.outputs:
            output_response = run_test(synth, output_test, testset.llm_config_list)  # type: ignore
            if output_response.success:
                transition_response.num_success += 1
            else:
                transition_response.num_failure += 1
            transition_response.outputs.append(output_response)

        transition_response.passed = transition_response.num_failure == 0
        testset_results.num_success += transition_response.num_success
        testset_results.num_failure += transition_response.num_failure
        testset_results.transitions.append(transition_response)

    testset_results.passed = testset_results.num_failure == 0
    return testset_results
