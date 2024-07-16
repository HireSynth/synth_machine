from unittest import TestCase
from synth_machine.synth_parser import SynthParser


class TestSynthParse(TestCase):
    def test_json_parse(self):
        parser = SynthParser()

        self.assertEqual(
            parser.parse["json"]('{"abc": "def", "hij": ["k", "l", "m"]}'),
            {"abc": "def", "hij": ["k", "l", "m"]},
        )

    def test_xml_parse(self):
        parser = SynthParser()

        self.assertEqual(
            parser.parse["xml"]("<def><h>aab</h></def>"), {"def": {"h": "aab"}}
        )
        self.assertEqual(
            parser.parse["xml"]("<def><h>aab</h><aa>et"),
            {"def": {"h": "aab", "aa": "et"}},
        )

    def test_code_parse(self):
        parser = SynthParser()

        self.assertEqual(
            parser.parse["code"]("""seuas tsnaeo ce asmqt the sencqw
            stne eau tea euth
            ```python
            import ABC
            
            abc = ABC()
            ```
            rcoua ausnth ewa 
            """),
            """import ABC
            
            abc = ABC()""",
        )
        self.assertEqual(
            parser.parse["code"]("""seuas tsnaeo ce asmqt the sencqw
            stne eau tea euth
            ```python
            import ABC
            
            abc = ABC()
            ```
            rcoua ausnth ewa 
            ```
            ab
            ```
            """),
            """import ABC
            
            abc = ABC()""",
        )
        self.assertEqual(
            parser.parse["code"]("""
            ``````
            """),
            "",
        )
        self.assertEqual(
            parser.parse["code"]("""
            ```python
            import abc 
            """),
            "import abc",
        )


if __name__ == "__main__":
    import logging
    import unittest

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
