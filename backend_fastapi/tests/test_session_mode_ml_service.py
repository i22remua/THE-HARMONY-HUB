from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.session_mode_ml_service import (
    DEFAULT_MIN_SELECTED_MODE_PROBABILITY,
    get_model_card_summary,
    get_min_selected_mode_probability,
    mood_model_available,
)


class SessionModeMlServiceTest(unittest.TestCase):
    @patch(
        "app.services.session_mode_ml_service.get_model_quality_metadata",
        return_value={
            "decision_thresholds": {
                "min_selected_mode_probability": 0.73,
            }
        },
    )
    def test_uses_calibrated_selected_mode_probability_threshold(self, _mock_metadata) -> None:
        self.assertEqual(get_min_selected_mode_probability(), 0.73)

    @patch(
        "app.services.session_mode_ml_service.get_model_quality_metadata",
        return_value={},
    )
    def test_falls_back_to_neutral_probability_threshold(self, _mock_metadata) -> None:
        self.assertEqual(
            get_min_selected_mode_probability(),
            DEFAULT_MIN_SELECTED_MODE_PROBABILITY,
        )

    @patch("app.services.session_mode_ml_service.model_available", return_value=True)
    def test_mood_model_available_is_now_compatibility_alias(
        self,
        _mock_model_available,
    ) -> None:
        self.assertTrue(mood_model_available("neutral"))
        self.assertTrue(mood_model_available("triste"))
        self.assertTrue(mood_model_available("feliz"))

    @patch(
        "app.services.session_mode_ml_service.load_model_card",
        return_value={
            "model_type": "LogisticRegression",
            "trained_at": "2026-05-13T08:00:00+00:00",
            "quality_summary": {
                "quality_score": 74.2,
                "model_gate_passed": True,
                "model_readiness_reason": "model_gate_passed",
            },
            "coefficient_summary": {
                "top_positive_features": [{"label": "mood=triste", "coefficient": 0.82}],
                "top_negative_features": [{"label": "goal=foco", "coefficient": -0.41}],
            },
        },
    )
    def test_get_model_card_summary_returns_compact_payload(self, _mock_model_card) -> None:
        summary = get_model_card_summary()

        self.assertIsNotNone(summary)
        self.assertEqual(summary["model_type"], "LogisticRegression")
        self.assertEqual(summary["quality_score"], 74.2)
        self.assertTrue(summary["model_gate_passed"])
        self.assertEqual(summary["top_positive_features"][0]["label"], "mood=triste")

    @patch("app.services.session_mode_ml_service.load_model_card", return_value=None)
    def test_get_model_card_summary_returns_none_without_card(self, _mock_model_card) -> None:
        self.assertIsNone(get_model_card_summary())


if __name__ == "__main__":
    unittest.main()
