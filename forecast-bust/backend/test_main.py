import os
import unittest


os.environ.setdefault("DATABASE_URL", "sqlite://")

from backend import main


def make_row(region, lead_day):
    region_offset = 12 if region == "Odisha" else 0
    return {
        "lead_day": lead_day,
        "rainfall_forecast": 48.0 + lead_day + region_offset,
        "previous_forecast": 45.0,
        "historical_mae": 6.0,
        "weather_variability": 0.4,
        "forecast_revision": 3.0 + lead_day,
        "forecast_stability": 1 / (4 + lead_day),
        "weather_regime": "Monsoon",
    }


class ExplainabilityTests(unittest.TestCase):
    def test_explanation_uses_selected_region_and_lead_day(self):
        original_get_region_data = main.get_region_data
        try:
            main.get_region_data = make_row
            day_one = main.explain_prediction("Coastal Andhra", 1)
            other_region = main.explain_prediction("Odisha", 10)
        finally:
            main.get_region_data = original_get_region_data

        self.assertEqual(len(day_one["top_factors"]), 5)
        self.assertEqual(len(other_region["top_factors"]), 5)
        self.assertTrue(
            all(
                {
                    "feature",
                    "value",
                    "shap_impact",
                    "direction",
                    "explanation",
                }
                <= set(factor)
                for factor in day_one["top_factors"]
            )
        )
        self.assertEqual(day_one["factors"], day_one["top_factors"])
        self.assertGreaterEqual(len(day_one["reliability_reasons"]), 5)
        self.assertNotEqual(
            day_one["top_factors"][0]["explanation"],
            other_region["top_factors"][0]["explanation"],
        )
        self.assertTrue(
            all(
                abs(day_one["top_factors"][index]["shap_impact"])
                >= abs(day_one["top_factors"][index + 1]["shap_impact"])
                for index in range(4)
            )
        )


if __name__ == "__main__":
    unittest.main()
