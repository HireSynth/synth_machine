from unittest import main
from unittest.mock import patch
from synth_machine.user_defined_functions import udf
from tests.test_synth_machine import SynthMachineTest


class SynthMachineSuccessTest(SynthMachineTest):
    async def test_trigger(self):
        simple_transitions = self.helper.get_transistions("simple_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=simple_transitions,
            memory=self.FAKE_MEMORY,
        )
        self.assertEqual(await synth.trigger(simple_transitions[0]["trigger"]), {})
        self.assertEqual(synth.current_state(), self.states[1]["name"])

    async def test_user_defined_functions(self):
        @udf
        def duplicate_string(memory):
            return memory["test_string"] + memory["test_string"]

        udf_transitions = self.helper.get_transistions("udf_transitions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=udf_transitions,
            memory=self.FAKE_MEMORY,
        )
        synth.user_defined_functions = {"duplicate_string": duplicate_string}
        self.assertEqual(
            await synth.trigger(
                udf_transitions[0]["trigger"], params={"test_string": "hello"}
            ),
            {"duplicate": "hellohello"},
        )

    async def test_if_simple_synth_moves_between_states(self):
        simple_transitions = self.helper.get_transistions("simple_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=simple_transitions,
            memory=self.FAKE_MEMORY,
        )
        async for _ in synth.streaming_trigger(simple_transitions[0]["trigger"]):
            pass
        self.assertEqual(synth.current_state(), self.states[1]["name"])

        async for _ in synth.streaming_trigger(simple_transitions[1]["trigger"]):
            pass
        self.assertEqual(synth.current_state(), self.states[2]["name"])

    async def test_loop_synth(self):
        loop_transitions = self.helper.get_transistions("loop_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=loop_transitions,
            memory=self.FAKE_MEMORY,
        )
        with patch("synth_machine.machine.prompt_setup", self.mock_prompt_setup):
            async for event in synth.streaming_trigger(loop_transitions[0]["trigger"]):
                pass
        self.assertEqual(synth.current_state(), self.states[1]["name"])
        self.assertEqual(
            synth.memory["loop"],
            [
                "You are an automated chicken",
                "You are an automated chicken",
                "You are an automated chicken",
            ],
        )

    async def test_append(self):
        append_transistions = self.helper.get_transistions("append_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=append_transistions,
            memory=self.FAKE_MEMORY,
        )
        expected = [
            [self.FAKE_MEMORY["a"]],
            [self.FAKE_MEMORY["a"], self.FAKE_MEMORY["a"], self.FAKE_MEMORY["b"]],
            [
                self.FAKE_MEMORY["a"],
                *(self.FAKE_MEMORY["a"], self.FAKE_MEMORY["b"]) * 2,
            ],
        ]
        for count, transition in enumerate(append_transistions):
            async for _ in synth.streaming_trigger(
                transition.get("trigger")  # type: ignore
            ):
                pass
            self.assertEqual(synth.memory.get("chat_history"), expected[count])
        self.assertEqual(synth.memory.get("chat_history"), expected[-1])

    async def test_params_overwrite_memory(self):
        simple_transitions = self.helper.get_transistions("simple_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=simple_transitions,
            memory=self.FAKE_MEMORY,
        )
        overwrite = {"a": "I AM FISH"}
        async for _ in synth.streaming_trigger(
            simple_transitions[0].get("trigger"),  # type: ignore
            overwrite,
        ):
            pass
        self.assertEqual(synth.memory["a"], overwrite["a"])

    async def test_interleave(self):
        interleave_transitions = self.helper.get_transistions("interleave_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=interleave_transitions,
            memory=self.FAKE_MEMORY,
        )
        expected = [
            {"a": "a", "fish": "fish", "z": "z"},
            {"a": "b", "y": "y"},
            {"a": "c", "x": "x"},
        ]
        async for _ in synth.streaming_trigger(
            interleave_transitions[0].get("trigger"),  # type: ignore
        ):
            pass
        self.assertEqual(synth.memory["interleaved"], expected)

    async def test_jq(self):
        jq_transitions = self.helper.get_transistions("jq_transistions")
        synth = self.helper.create_synth_machine(
            initial_state=self.states[0]["name"],
            states=self.states,
            transitions=jq_transitions,
            memory=self.FAKE_MEMORY,
        )
        async for _yield in synth.streaming_trigger(
            jq_transitions[0].get("trigger"),  # type: ignore
        ):
            pass
            # print(_yield)
        self.assertEqual(len(synth.memory["flattened"]), 30)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    main()
