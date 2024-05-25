from unittest import main
from unittest.mock import patch

from tests.test_synth_machine import SynthMachineTest


class SynthMachineFailureTests(SynthMachineTest):
    async def test_trigger(self):
        simple_transitions = self.helper.get_transistions("simple_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=simple_transitions,
            memory=self.FAKE_MEMORY,
        )
        with self.assertRaises(Exception) as context:
            self.assertEqual(
                str(context), "No transition: failedTransition exists at state: theme"
            )
        self.assertEqual(synth.current_state(), self.states[0]["name"])

    async def test_safety_flagged_failure(self):
        basic_transitions = self.helper.get_transistions("basic_transitions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=basic_transitions,
            memory=self.FAKE_MEMORY,
        )
        with patch("synth_machine.machine.prompt_setup", self.mock_prompt_setup):
            with patch(
                "synth_machine.safety.Safety.check",
                lambda self, text, provider, meta=None: {
                    "dangerous": {"flagged": True}
                },
            ):
                async for event in synth.streaming_trigger(
                    basic_transitions[0]["trigger"]
                ):
                    pass

        self.assertEqual(synth.current_state(), self.states[0]["name"])

    async def test_json_validation_parse_failure(self):
        json_validate_transistions = self.helper.get_transistions(
            "json_validate_transistions"
        )
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=json_validate_transistions,
            memory=self.FAKE_MEMORY,
        )
        validation_error_list = []
        with patch(
            "synth_machine.machine.prompt_setup",
            self.mock_json_prompt_parse_failure_setup,
        ):
            with patch(
                "synth_machine.safety.Safety.check",
                lambda self, text, provider, meta=None: {
                    "dangerous": {"flagged": False}
                },
            ):
                async for event in synth.streaming_trigger(
                    json_validate_transistions[0]["trigger"]
                ):
                    if event[0].startswith("OUTPUT_VALIDATION"):
                        validation_error_list.append(event)
        self.assertListEqual(
            validation_error_list,
            [
                ["OUTPUT_VALIDATION_FAILED", "output"],
            ],
        )

        self.assertEqual(synth.current_state(), self.states[0]["name"])

    async def test_json_validation_validate_failure(self):
        json_validate_transistions = self.helper.get_transistions(
            "json_validate_transistions"
        )
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=json_validate_transistions,
            memory=self.FAKE_MEMORY,
        )
        validation_error_list = []
        with patch(
            "synth_machine.machine.prompt_setup",
            self.mock_json_prompt_setup,
        ):
            with patch(
                "synth_machine.safety.Safety.check",
                lambda self, text, provider, meta=None: {
                    "dangerous": {"flagged": False}
                },
            ):
                async for event in synth.streaming_trigger(
                    json_validate_transistions[0]["trigger"]
                ):
                    if event[0].startswith("OUTPUT_VALIDATION"):
                        validation_error_list.append(event)
        self.assertListEqual(
            validation_error_list,
            [
                ["OUTPUT_VALIDATION_FAILED", "output"],
            ],
        )

        self.assertEqual(synth.current_state(), self.states[0]["name"])


if __name__ == "__main__":
    main()
