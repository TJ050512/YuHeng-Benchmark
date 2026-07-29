import unittest

from yuheng_eval.metrics import evaluate


class MetricTests(unittest.TestCase):
    def test_reference_metrics(self):
        gold = [
            {"Lv": "Normal", "Lt": "Normal", "GT": "Violation"},
            {"Lv": "Normal", "Lt": "Suggestive", "GT": "Suggestive"},
            {"Lv": "Violation", "Lt": "Normal", "GT": "Violation"},
        ]
        pred = [
            {"level_of_picture": "Normal", "level_of_word": "Normal", "cross_modal_safety": "Yes", "final_risk_label": "Violation"},
            {"level_of_picture": "Normal", "level_of_word": "Suggestive", "cross_modal_safety": "No", "final_risk_label": "Suggestive"},
            {"level_of_picture": "Suggestive", "level_of_word": "Normal", "cross_modal_safety": "Yes", "final_risk_label": "Suggestive"},
        ]
        result = evaluate(gold, pred)
        self.assertEqual(result["vr"], 0.5)
        self.assertEqual(result["iva"], 0.25)
        self.assertEqual(result["violation_recall"], 0.5)
        self.assertEqual(result["implicit_violation_attenuation"], 0.25)
        self.assertEqual(result["scas"], 0.5)
        self.assertEqual(result["mer"], 0.5)
        self.assertEqual(result["set_sizes"]["implicit_I"], 1)
        self.assertEqual(result["set_sizes"]["comparison_not_I"], 2)

    def test_flag_accounting_on_label_complete_rows(self):
        gold = [{"Lv": "Normal", "Lt": "Normal", "GT": "Violation"}]
        pred = [{
            "level_of_picture": "Normal",
            "level_of_word": "Normal",
            "cross_modal_safety": "Yes",
            "final_risk_label": "Violation",
            "refusal": True,
            "parsing_failure": True,
        }]
        result = evaluate(gold, pred)
        self.assertEqual(result["refusal_rate"], 1.0)
        self.assertEqual(result["parsing_failure_rate"], 1.0)

    def test_invalid_cross_modal_value_and_flag_are_rejected(self):
        gold = [{"Lv": "Normal", "Lt": "Normal", "GT": "Violation"}]
        base = {
            "level_of_picture": "Normal",
            "level_of_word": "Normal",
            "final_risk_label": "Violation",
        }
        with self.assertRaises(ValueError):
            evaluate(gold, [{**base, "cross_modal_safety": "maybe"}])
        with self.assertRaises(ValueError):
            evaluate(gold, [{**base, "cross_modal_safety": "Yes", "refusal": "false"}])


if __name__ == "__main__":
    unittest.main()
