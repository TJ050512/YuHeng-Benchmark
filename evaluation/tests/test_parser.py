import unittest

from yuheng_eval.parsing import parse_model_output


class ParserTests(unittest.TestCase):
    def test_embedded_json_and_aliases(self):
        parsed = parse_model_output(
            'analysis\n```json\n{"level of word":"Teasing","level of picture":"Normal",'
            '"association":"图文含义相关。","vague methods":"Polysemy",'
            '"cross modal safety":"No","final risk label":"Illegal"}\n```'
        )
        self.assertEqual(parsed["level_of_word"], "Suggestive")
        self.assertEqual(parsed["level_of_picture"], "Normal")
        self.assertEqual(parsed["final_risk_label"], "Violation")

    def test_printed_soft_porn_alias_is_accepted(self):
        parsed = parse_model_output(
            '{"level_of_word":"Normal","level_of_picture":"Soft_Porn",'
            '"association":"图像单独具有暗示性。","vague_methods":"None",'
            '"cross_modal_safety":"No","final_risk_label":"Suggestive"}'
        )
        self.assertEqual(parsed["level_of_picture"], "Suggestive")

    def test_invalid_vague_method_is_failure(self):
        with self.assertRaises(ValueError):
            parse_model_output(
                '{"level_of_word":"Normal","level_of_picture":"Normal",'
                '"association":"说明。","vague_methods":"Unknown",'
                '"cross_modal_safety":"No","final_risk_label":"Normal"}'
            )

    def test_invalid_output_is_failure(self):
        with self.assertRaises(ValueError):
            parse_model_output("not json")

    def test_incomplete_json_is_failure(self):
        with self.assertRaises(ValueError):
            parse_model_output('{"level_of_word":"Normal"}')


if __name__ == "__main__":
    unittest.main()
