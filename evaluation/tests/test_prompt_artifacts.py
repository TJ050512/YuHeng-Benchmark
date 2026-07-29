import json
from pathlib import Path
import unittest


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


class PromptArtifactTests(unittest.TestCase):
    def test_appendix_transcription_contract(self):
        payload = json.loads(
            (PROMPT_DIR / "appendix_prompt_transcription.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            payload["status"], "documentary_transcription_not_execution_log"
        )
        self.assertEqual(
            [field["key"] for field in payload["printed_output_contract"]],
            [
                "level_of_word",
                "level_of_picture",
                "association",
                "vague_methods",
                "cross_modal_safety",
                "final_risk_label",
            ],
        )
        self.assertIn(
            "Soft_Porn", payload["printed_output_contract"][1]["allowed_values"]
        )
        self.assertIn("weather this data", payload["verbatim_template"])

    def test_canonical_reference_is_separately_labeled(self):
        payload = json.loads(
            (PROMPT_DIR / "canonical_normalized_reference.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            payload["status"], "prospective_reference_not_historical_run_record"
        )
        self.assertEqual(payload["historical_alias_mapping"]["Soft_Porn"], "Suggestive")
        self.assertEqual(payload["historical_alias_mapping"]["Illegal"], "Violation")


if __name__ == "__main__":
    unittest.main()
