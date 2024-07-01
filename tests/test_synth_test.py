from synth_machine.experimental.synth_test.run import run_testset
from synth_machine.experimental.synth_test.synth_test_runner import (
    remove_before_char,
    remove_after_last_char,
)
from synth_machine.experimental.synth_test.synth_test_config import (
    SynthTestSpec,
    OutputTestResponse,
    IndividualPromptTestOutput,
    TransitionTestResponse,
    SynthTestResponse,
)
from synth_machine import Synth
from synth_machine.machine_config import ModelConfig
from unittest import TestCase
from unittest.mock import patch


def mock_generate(prompt, system_prompt, llm_config: ModelConfig):
    match llm_config.llm_name:
        case "Qwen/Qwen2-72B-Instruct":
            return (
                """Sure! Here is the result {"score": "green", "explanation": "The content is structured into three distinct sections as required by the rule: 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section is clearly labeled and provides a detailed analysis relevant to the topic. The rule is fully adhered to, and the content is well-organized."}""",
                False,
            )
        case "meta-llama/Llama-3-8b-chat-hf":
            return (
                """{"score": "green", "explanation": "The provided content meets the rule by clearly labeling and separating the required sections: 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section provides a detailed and informative analysis, demonstrating a thorough understanding of the topic. The content is well-structured, and the language is clear and concise."}""",
                False,
            )
        case "meta-llama/Llama-3-70b-chat-hf":
            return (
                """{"score": "yellow", "explanation": "The provided content includes clear sections labeled 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section provides a detailed and well-structured analysis of the given topic, demonstrating a strong understanding of the subject matter and the ability to communicate complex ideas effectively."}\nResult: {""",
                False,
            )
        case _:
            return "Broken response", True


class TestSynthTest(TestCase):
    def setup(self):
        self.synth = Synth(
            config={
                "states": [{"name": "state"}],
                "initial_state": "state",
                "transitions": [
                    {
                        "source": "state",
                        "dest": "state",
                        "trigger": "run",
                        "outputs": [
                            {
                                "key": "test_output",
                            }
                        ],
                    }
                ],
            }
        )
        self.synth.memory["test_output"] = """**DETAILED ANALYSIS**
===============
### Genre Analysis
-------------------

Indie punk is a genre characterized by its DIY ethos, raw energy, and anti-establishment sentiment. Typical lyrical themes in indie punk often revolve around social commentary, DIY ethics, and personal struggles. The genre frequently employs storytelling techniques, witty wordplay, and a strong focus on melody.
The provided lyrics snippet, "As I walk down the street," seems to deviate from the typical lyrical themes of indie punk. The theme of "club music style" is not directly related to the genre's typical concerns. However, the snippet's focus on personal experience and observational storytelling could be a good starting point for an indie punk track.
To align the lyrics with the genre, the artist could consider:

* Exploring themes of social commentary, such as the effects of gentrification or the struggles of working-class individuals, which are common in indie punk.
* Incorporating DIY ethics by focusing on personal experiences, observations, or struggles, which could be relatable to the indie punk audience.
* Using witty wordplay and clever storytelling techniques to make the lyrics more engaging and memorable."""

    def test_run_testset(self):
        self.setup()
        expected_output = SynthTestResponse(
            transitions=[
                TransitionTestResponse(
                    trigger="run",
                    outputs=[
                        OutputTestResponse(
                            test="prompt",
                            rule="Output test_output, Rule: There must be clear sections labelled 'Genre Analysis', 'Theme Interpretation' and 'Lyrics Analysis'",
                            success=True,
                            score=2.33,
                            test_error=False,
                            message=None,
                            results=[
                                IndividualPromptTestOutput(
                                    llm_name="Qwen/Qwen2-72B-Instruct",
                                    score="green",
                                    explanation="The content is structured into three distinct sections as required by the rule: 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section is clearly labeled and provides a detailed analysis relevant to the topic. The rule is fully adhered to, and the content is well-organized.",
                                ),
                                IndividualPromptTestOutput(
                                    llm_name="meta-llama/Llama-3-8b-chat-hf",
                                    score="green",
                                    explanation="The provided content meets the rule by clearly labeling and separating the required sections: 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section provides a detailed and informative analysis, demonstrating a thorough understanding of the topic. The content is well-structured, and the language is clear and concise.",
                                ),
                                IndividualPromptTestOutput(
                                    llm_name="meta-llama/Llama-3-70b-chat-hf",
                                    score="yellow",
                                    explanation="The provided content includes clear sections labeled 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section provides a detailed and well-structured analysis of the given topic, demonstrating a strong understanding of the subject matter and the ability to communicate complex ideas effectively.",
                                ),
                            ],
                        ),
                        OutputTestResponse(
                            test="length",
                            success=False,
                            score=1213.0,
                            results=None,
                            rule="Output: test_output, Length must be gt 2500",
                            test_error=False,
                            message=None,
                        ),
                    ],
                    passed=False,
                    num_success=1,
                    num_failure=1,
                    failure_rules=["Output: test_output, Length must be gt 2500"],
                )
            ],
            passed=False,
            num_success=1,
            num_failure=1,
            failure_rules=["Output: test_output, Length must be gt 2500"],
        )
        testset_spec = {
            "transitions": [
                {
                    "trigger": "run",
                    "outputs": [
                        {
                            "output": "test_output",
                            "test": "prompt",
                            "testcase": {
                                "rule": "There must be clear sections labelled 'Genre Analysis', 'Theme Interpretation' and 'Lyrics Analysis'",
                            },
                        },
                        {
                            "output": "test_output",
                            "test": "length",
                            "testcase": {"operator": "gt", "test_value": 2500},
                        },
                    ],
                }
            ],
            "llm_config_list": [
                {"llm_name": "Qwen/Qwen2-72B-Instruct"},
                {"llm_name": "meta-llama/Llama-3-8b-chat-hf"},
                {"llm_name": "meta-llama/Llama-3-70b-chat-hf"},
            ],
        }
        testset = SynthTestSpec(**testset_spec)

        with patch(
            "synth_machine.experimental.synth_test.synth_test_runner.generate",
            mock_generate,
        ):
            test_results = run_testset(synth=self.synth, testset=testset)

        self.assertEqual(expected_output, test_results)

    def test_remove_before_char(self):
        self.assertEqual(
            remove_before_char(
                """"Sure! Here is the result {"score": "green", "explanation": The content is structured into three distinct sections as required by the rule: 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section is clearly labeled and provides a detailed analysis relevant to the topic. The rule is fully adhered to, and the content is well-organized."}""",
                "{",
            ),
            """{"score": "green", "explanation": The content is structured into three distinct sections as required by the rule: 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section is clearly labeled and provides a detailed analysis relevant to the topic. The rule is fully adhered to, and the content is well-organized."}""",
        )

    def test_remove_after_last_char(self):
        self.assertEqual(
            remove_after_last_char(
                """{"score": "yellow", "explanation": "The provided content includes clear sections labeled 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section provides a detailed and well-structured analysis of the given topic, demonstrating a strong understanding of the subject matter and the ability to communicate complex ideas effectively."}\nResult: {""",
                "}",
            ),
            """{"score": "yellow", "explanation": "The provided content includes clear sections labeled 'Genre Analysis', 'Theme Interpretation', and 'Lyrics Analysis'. Each section provides a detailed and well-structured analysis of the given topic, demonstrating a strong understanding of the subject matter and the ability to communicate complex ideas effectively."}""",
        )


if __name__ == "__main__":
    import logging
    import unittest

    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
