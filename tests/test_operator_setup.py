from unittest import IsolatedAsyncioTestCase
from synth_machine.synth_definition import Output
from synth_machine import operator_setup
from synth_machine.machine_config import ModelConfig
from synth_machine.providers.lorem import LoremProvider


class TestConfig(IsolatedAsyncioTestCase):
    async def test_prompt_setup_model_config(self):
        synth_config, err = await operator_setup.prompt_setup(
            output_definition=Output(
                key="test",
                model_config=ModelConfig(temperature=0.3),
                prompt="Count to 10",
                schema={"type": "string"},
            ),
            inputs={},
            default_model_config=ModelConfig(
                llm_name="test_llm",
                max_tokens=1,
                temperature=0.8,
                assistant_partial="",
                partial_input=None,
                stop=[],
                tool_use=False,
                tool_options=[],
            ),
            transition_model_config=ModelConfig(temperature=0.4, max_tokens=100),
        )

        self.assertFalse(err)
        self.assertEqual(
            operator_setup.SynthConfig(
                model_config=ModelConfig(
                    llm_name="test_llm",
                    max_tokens=100,
                    temperature=0.3,
                    assistant_partial="",
                    stop=[],
                    tool_use=False,
                    tool_options=[],
                ),
                system_prompt=None,
                user_prompt="Count to 10",
            ),
            synth_config,
        )

    async def test_prompt_setup_model_config_only_default(self):
        default_model_config = ModelConfig(
            llm_name="test_llm",
            max_tokens=1,
            temperature=0.8,
            assistant_partial="",
            partial_input=None,
            stop=[],
            tool_use=False,
            tool_options=[],
        )
        synth_config, err = await operator_setup.prompt_setup(
            output_definition=Output(
                key="test",
                prompt="Count to 10",
                schema={"type": "string"},
            ),
            inputs={},
            default_model_config=default_model_config,
            transition_model_config=ModelConfig(),
        )

        self.assertFalse(err)
        self.assertEqual(
            operator_setup.SynthConfig(
                model_config=default_model_config,
                system_prompt=None,
                user_prompt="Count to 10",
            ),
            synth_config,
        )
