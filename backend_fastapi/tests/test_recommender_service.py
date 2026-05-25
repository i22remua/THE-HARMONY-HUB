from __future__ import annotations

import unittest
from unittest.mock import patch

from app.schemas.recommendation import RecommendationRequest
from app.services.recommender_service import generate_recommendation


class RecommenderServiceTest(unittest.TestCase):
    @patch("app.services.recommender_service.session_model_available", return_value=False)
    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={
            "feedback_count": 9,
            "session_positive_feedback_count": 7,
            "session_negative_feedback_count": 1,
            "stable_positive_feedback_count": 7,
            "stable_negative_feedback_count": 1,
            "session_preferred_genres": {"ambient": 2.0},
            "stable_preferred_genres": {"classical": 3.0},
            "mood_learning_stats": {
                "neutral": {
                    "feedback_count": 8,
                    "positive_feedback_count": 7,
                    "negative_feedback_count": 1,
                    "preferred_genres": {
                        "ambient": 2.0,
                        "classical": 1.0,
                        "minimal": 1.0,
                    },
                    "preferred_valence": 0.46,
                    "preferred_energy": 0.34,
                    "preferred_danceability": 0.21,
                }
            },
        },
    )
    def test_generate_recommendation_exposes_learning_trace(
        self,
        _mock_prefs,
        _mock_model_available,
    ) -> None:
        payload = RecommendationRequest(
            mood="neutral",
            goal="foco",
            stress_level=3,
            energy_level=3,
            noise_category="quiet",
            vocal_preference="instrumental",
            intensity_preference="media",
            exploration_preference="familiar",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_centrado",
            use_environment=True,
        )

        result = generate_recommendation(payload)

        self.assertEqual(result.feedback_count, 9)
        self.assertGreater(result.session_taste_weight, 0.0)
        self.assertGreater(result.stable_taste_weight, 0.0)
        self.assertIn(result.taste_profile_mode, {"session_weighted", "stable_weighted"})

    @patch("app.services.recommender_service.session_model_available", return_value=False)
    @patch("app.services.recommender_service.build_generation_profile")
    def test_generate_recommendation_uses_spotify_user_id_for_learning_lookup(
        self,
        mock_build_generation_profile,
        _mock_model_available,
    ) -> None:
        mock_build_generation_profile.return_value = {
            "recommended_mode": "energia_neutral_media",
            "target_energy": 0.7,
            "target_valence": 0.62,
            "target_bpm_range": "95-120",
            "feedback_count": 4,
            "session_taste_weight": 0.22,
            "stable_taste_weight": 0.12,
            "taste_profile_mode": "session_weighted",
        }

        payload = RecommendationRequest(
            mood="neutral",
            goal="energia",
            spotify_user_id="spotify_user_123",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            use_environment=True,
        )

        generate_recommendation(payload)

        self.assertTrue(mock_build_generation_profile.called)
        self.assertEqual(
            mock_build_generation_profile.call_args.kwargs["user_id"],
            "spotify_user_123",
        )

    @patch("app.services.recommender_service.session_model_available", return_value=True)
    def test_generate_recommendation_enables_ml_when_global_model_is_available(
        self,
        _mock_model_available,
    ) -> None:
        payload = RecommendationRequest(
            mood="neutral",
            goal="energia",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            use_environment=True,
        )

        result = generate_recommendation(payload)

        self.assertTrue(result.ml_enabled)

    @patch(
        "app.services.recommender_service.get_model_card_summary",
        return_value={
            "model_type": "LogisticRegression",
            "quality_score": 74.2,
            "model_gate_passed": True,
        },
    )
    @patch("app.services.recommender_service.session_model_available", return_value=False)
    def test_generate_recommendation_exposes_model_card_summary(
        self,
        _mock_model_available,
        _mock_model_card_summary,
    ) -> None:
        payload = RecommendationRequest(
            mood="neutral",
            goal="foco",
            stress_level=3,
            energy_level=3,
            noise_category="quiet",
            vocal_preference="instrumental",
            intensity_preference="media",
            exploration_preference="familiar",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_centrado",
            use_environment=True,
        )

        result = generate_recommendation(payload)

        self.assertIsNotNone(result.model_card_summary)
        self.assertEqual(result.model_card_summary["model_type"], "LogisticRegression")
        self.assertIsNone(result.ml_explanation)


if __name__ == "__main__":
    unittest.main()
