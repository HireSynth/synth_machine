import json
import os

from synth_machine.machine import Synth, BaseCost, SynthParser
from tests.test_mocks import MockProviderFactory

class TestHelper:
    def __init__(self) -> None:
        self.transition = {}
        self.states = []
        fixture_path = os.path.join(os.curdir, "tests", "fixtures")
        for dirpath, dirnames, filenames in os.walk(fixture_path):
            for json_filename in filenames:
                filename = json_filename.removesuffix(".json")
                with open(os.path.join(dirpath, json_filename)) as f:
                    if "states" in filename:
                        self.states = json.load(f)
                    else:
                        self.transition[filename] = json.load(f)

    def get_states(self) -> list:
        return self.states

    def get_transistions(self, name: str) -> list:
        return self.transition.get(name, [])
    
    def create_synth_machine(
        self, initial_state: str, states: list, transitions: list, memory: dict
    ) -> Synth:
                
        class MockSynth(Synth, BaseCost, SynthParser, MockProviderFactory):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
                
        return MockSynth(
            config={
                "initial_state": initial_state,
                "states": states,
                "transitions": transitions,
            },
            memory=memory,
        )
