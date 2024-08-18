from unittest import IsolatedAsyncioTestCase
from tests.test_mocks import (
    MockProvider,
    MockJsonParseFailureProvider,
    MockJsonProvider,
)
from tests.test_helper import TestHelper
from tests.test_utils import json_file_loader
from synth_machine.machine_config import ModelConfig
from synth_machine.operator_setup import SynthConfig


class SynthMachineTest(IsolatedAsyncioTestCase):
    FAKE_MEMORY = {
        "a": "I AM CHICKEN",
        "b": "I AM DONKEY",
        "chat_history": [],
        "data": [
            {"a": "a"},
            {"a": "b"},
            {"a": "c"},
        ],
        "images": [{"z": "z"}, {"y": "y"}, {"x": "x"}],
        "fish": [{"fish": "fish"}],
        "acts_condensed": json_file_loader("./tests/fixtures/acts_condensed.json"),
    }

    def setUp(self):
        self.helper = TestHelper()
        self.states = self.helper.get_states()

    async def mock_prompt_setup(self, **kwargs):
        return (
            SynthConfig(
                **{
                    "model_config": ModelConfig(
                        provider="mock",
                    ),
                    "system_prompt": "",
                    "user_prompt": "",
                }
            ),
            None,
        )

    async def mock_text_prompt_setup(self, **kwargs):
        return (
            SynthConfig(
                **{
                    "model_config": ModelConfig(
                        provider="mock",
                    ),
                    "system_prompt": "",
                    "user_prompt": "",
                }
            ),
            None,
        )

    async def mock_json_prompt_setup(self, **kwargs):
        return (
            SynthConfig(
                **{
                    "model_config": ModelConfig(
                        Provider="mock",
                    ),
                    "system_prompt": "",
                    "user_prompt": "",
                }
            ),
            None,
        )

    async def mock_json_prompt_parse_failure_setup(self, **kwargs):
        return (
            SynthConfig(
                **{
                    "model_config": ModelConfig(
                        Provider="mock",
                    ),
                    "system_prompt": "",
                    "user_prompt": "",
                }
            ),
            None,
        )
