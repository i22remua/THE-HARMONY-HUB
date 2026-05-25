from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.professional_playlist_model_service import (
    assemble_playlist,
    build_generation_profile,
)


class ProfessionalPlaylistModelServiceTest(unittest.TestCase):
    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={},
    )
    def test_build_generation_profile_assigns_deep_focus_subtype(self, _mock_prefs) -> None:
        profile = build_generation_profile(
            user_id="user_1",
            goal="foco",
            mood="neutral",
            stress_level=3,
            energy_level=3,
            noise_category="quiet",
            vocal_preference="instrumental",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_centrado",
            environment_context="biblioteca",
            use_environment=True,
        )

        self.assertEqual(profile["session_subtype"], "deep_focus")
        self.assertEqual(profile["activation_curve"], "flat")
        self.assertLessEqual(profile["target_vocal_presence"], 0.08)

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={},
    )
    def test_build_generation_profile_assigns_warm_companionship_subtype(self, _mock_prefs) -> None:
        profile = build_generation_profile(
            user_id="user_2",
            goal="energia",
            mood="triste",
            stress_level=4,
            energy_level=2,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="suave",
            exploration_preference="familiar",
            popularity_preference="mainstream",
            session_duration_min=15,
            desired_outcome="mas_acompanado",
            environment_context="transporte",
            use_environment=True,
        )

        self.assertEqual(profile["session_subtype"], "warm_companionship")
        self.assertEqual(profile["activation_curve"], "progressive")
        self.assertGreaterEqual(profile["target_vocal_presence"], 0.62)

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={},
    )
    def test_build_generation_profile_assigns_guided_focus_subtype(self, _mock_prefs) -> None:
        profile = build_generation_profile(
            user_id="user_guide",
            goal="foco",
            mood="neutral",
            stress_level=3,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=25,
            desired_outcome="mas_centrado",
            environment_context="biblioteca",
            use_environment=True,
        )

        self.assertEqual(profile["session_subtype"], "guided_focus")
        self.assertEqual(profile["activation_curve"], "flat")
        self.assertGreaterEqual(profile["target_vocal_presence"], 0.62)

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={},
    )
    def test_build_generation_profile_assigns_comfort_relaxation_subtype(self, _mock_prefs) -> None:
        profile = build_generation_profile(
            user_id="user_comfort",
            goal="relajacion",
            mood="neutral",
            stress_level=3,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="suave",
            exploration_preference="equilibrado",
            popularity_preference="alternativa",
            session_duration_min=25,
            desired_outcome="mas_calmado",
            environment_context="casa",
            use_environment=True,
        )

        self.assertEqual(profile["session_subtype"], "comfort_relaxation")
        self.assertEqual(profile["activation_curve"], "peak_then_settle")
        self.assertGreaterEqual(profile["target_vocal_presence"], 0.62)

    def test_assemble_playlist_progressive_curve_orders_energy_upwards(self) -> None:
        ranked_tracks = [
            {
                "uri": "spotify:track:1",
                "artists": ["Artist A"],
                "name": "Track 1",
                "duration_ms": 180000,
                "energy_feature": 0.82,
                "_score": 50.0,
            },
            {
                "uri": "spotify:track:2",
                "artists": ["Artist B"],
                "name": "Track 2",
                "duration_ms": 180000,
                "energy_feature": 0.32,
                "_score": 48.0,
            },
            {
                "uri": "spotify:track:3",
                "artists": ["Artist C"],
                "name": "Track 3",
                "duration_ms": 180000,
                "energy_feature": 0.58,
                "_score": 47.0,
            },
        ]

        selected = assemble_playlist(
            ranked_tracks=ranked_tracks,
            target_duration_ms=540000,
            max_tracks_per_artist=1,
            activation_curve="progressive",
            session_subtype="soft_activation",
        )

        self.assertEqual(
            [track["uri"] for track in selected],
            ["spotify:track:2", "spotify:track:3", "spotify:track:1"],
        )

    def test_assemble_playlist_respects_duration_instead_of_filling_to_twelve(self) -> None:
        ranked_tracks = [
            {
                "uri": f"spotify:track:{index}",
                "artists": [f"Artist {index}"],
                "name": f"Track {index}",
                "duration_ms": 300000,
                "energy_feature": 0.35,
                "_score": 100.0 - index,
            }
            for index in range(1, 13)
        ]

        selected = assemble_playlist(
            ranked_tracks=ranked_tracks,
            target_duration_ms=1800000,
            max_tracks_per_artist=1,
            activation_curve="flat",
            session_subtype="deep_focus",
        )

        self.assertLessEqual(len(selected), 7)
        self.assertGreaterEqual(len(selected), 6)
        self.assertLessEqual(
            sum(int(track["duration_ms"]) for track in selected),
            1890000,
        )

    def test_assemble_playlist_filters_instrumental_tracks_when_voice_is_required(self) -> None:
        ranked_tracks = [
            {
                "uri": "spotify:track:instrumental",
                "artists": ["Artist A"],
                "name": "Piano Ambient Study",
                "duration_ms": 180000,
                "instrumentalness": 0.91,
                "_score": 100.0,
            },
            {
                "uri": "spotify:track:voice_1",
                "artists": ["Artist B"],
                "name": "Warm Vocal Track",
                "duration_ms": 180000,
                "instrumentalness": 0.08,
                "vocal_presence_score": 0.88,
                "_score": 99.0,
            },
            {
                "uri": "spotify:track:voice_2",
                "artists": ["Artist C"],
                "name": "Another Vocal Track",
                "duration_ms": 180000,
                "lyrics_available": True,
                "_score": 98.0,
            },
        ]

        selected = assemble_playlist(
            ranked_tracks=ranked_tracks,
            target_duration_ms=360000,
            max_tracks_per_artist=1,
            activation_curve="flat",
            session_subtype="warm_companionship",
            vocal_preference="con_voz",
        )

        self.assertEqual(
            [track["uri"] for track in selected],
            ["spotify:track:voice_1", "spotify:track:voice_2"],
        )

    def test_assemble_playlist_filters_vocal_tracks_when_instrumental_is_required(self) -> None:
        ranked_tracks = [
            {
                "uri": "spotify:track:voice",
                "artists": ["Artist A"],
                "name": "Singer Songwriter Piece",
                "duration_ms": 180000,
                "instrumentalness": 0.05,
                "vocal_presence_score": 0.92,
                "_score": 100.0,
            },
            {
                "uri": "spotify:track:instrumental_1",
                "artists": ["Artist B"],
                "name": "Instrumental Focus Study",
                "duration_ms": 180000,
                "instrumentalness": 0.85,
                "_score": 99.0,
            },
            {
                "uri": "spotify:track:instrumental_2",
                "artists": ["Artist C"],
                "name": "Piano Soundscape",
                "duration_ms": 180000,
                "instrumentalness": 0.78,
                "_score": 98.0,
            },
        ]

        selected = assemble_playlist(
            ranked_tracks=ranked_tracks,
            target_duration_ms=360000,
            max_tracks_per_artist=1,
            activation_curve="flat",
            session_subtype="deep_focus",
            vocal_preference="instrumental",
        )

        self.assertEqual(
            [track["uri"] for track in selected],
            ["spotify:track:instrumental_1", "spotify:track:instrumental_2"],
        )

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={
            "feedback_count": 10,
            "session_positive_feedback_count": 7,
            "session_negative_feedback_count": 1,
            "stable_positive_feedback_count": 7,
            "stable_negative_feedback_count": 1,
            "session_preferred_genres": {"indie pop": 2.0},
            "stable_preferred_genres": {"pop": 3.0},
            "mood_learning_stats": {
                "neutral": {
                    "feedback_count": 8,
                    "positive_feedback_count": 7,
                    "negative_feedback_count": 1,
                    "preferred_genres": {"indie pop": 2.5, "pop": 1.5, "dance": 1.0},
                    "preferred_valence": 0.68,
                    "preferred_energy": 0.74,
                    "preferred_danceability": 0.78,
                }
            },
        },
    )
    def test_familiar_increases_learned_taste_weights_vs_discover(self, _mock_prefs) -> None:
        familiar_profile = build_generation_profile(
            user_id="user_3",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="familiar",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            environment_context="camino al trabajo",
            use_environment=True,
        )
        discover_profile = build_generation_profile(
            user_id="user_3",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="descubrir",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            environment_context="camino al trabajo",
            use_environment=True,
        )

        self.assertGreater(
            familiar_profile["session_taste_weight"],
            discover_profile["session_taste_weight"],
        )
        self.assertGreater(
            familiar_profile["stable_taste_weight"],
            discover_profile["stable_taste_weight"],
        )

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={
            "feedback_count": 8,
            "session_positive_feedback_count": 6,
            "session_negative_feedback_count": 0,
            "stable_positive_feedback_count": 6,
            "stable_negative_feedback_count": 0,
            "mood_learning_stats": {
                "neutral": {
                    "feedback_count": 6,
                    "positive_feedback_count": 6,
                    "negative_feedback_count": 0,
                    "preferred_genres": {"pop": 2.0, "dance": 1.0},
                    "preferred_valence": 0.7,
                    "preferred_energy": 0.8,
                    "preferred_danceability": 0.82,
                }
            },
        },
    )
    def test_consistent_positive_feedback_increases_learning_confidence(self, _mock_prefs) -> None:
        profile = build_generation_profile(
            user_id="user_consistent",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            environment_context="camino al trabajo",
            use_environment=True,
        )

        self.assertGreater(profile["session_learning_confidence"], 0.0)
        self.assertGreater(profile["stable_learning_confidence"], 0.0)
        self.assertGreater(profile["session_taste_weight"], 0.0)
        self.assertGreater(profile["stable_taste_weight"], 0.0)

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        side_effect=[
            {
                "feedback_count": 8,
                "session_positive_feedback_count": 6,
                "session_negative_feedback_count": 0,
                "stable_positive_feedback_count": 6,
                "stable_negative_feedback_count": 0,
                "mood_learning_stats": {
                    "neutral": {
                        "feedback_count": 6,
                        "positive_feedback_count": 6,
                        "negative_feedback_count": 0,
                        "preferred_genres": {"pop": 2.0, "dance": 1.0},
                        "preferred_valence": 0.7,
                        "preferred_energy": 0.8,
                        "preferred_danceability": 0.82,
                    }
                },
            },
            {
                "feedback_count": 8,
                "session_positive_feedback_count": 3,
                "session_negative_feedback_count": 3,
                "stable_positive_feedback_count": 3,
                "stable_negative_feedback_count": 3,
                "mood_learning_stats": {
                    "neutral": {
                        "feedback_count": 6,
                        "positive_feedback_count": 3,
                        "negative_feedback_count": 3,
                        "preferred_genres": {"pop": 1.0},
                        "preferred_valence": 0.58,
                        "preferred_energy": 0.63,
                        "preferred_danceability": 0.69,
                    }
                },
            },
        ],
    )
    def test_inconsistent_feedback_reduces_learning_weight(self, _mock_prefs) -> None:
        strong_profile = build_generation_profile(
            user_id="user_strong",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            environment_context="camino al trabajo",
            use_environment=True,
        )
        mixed_profile = build_generation_profile(
            user_id="user_mixed",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            environment_context="camino al trabajo",
            use_environment=True,
        )

        self.assertGreater(
            strong_profile["session_learning_confidence"],
            mixed_profile["session_learning_confidence"],
        )
        self.assertGreater(
            strong_profile["stable_learning_confidence"],
            mixed_profile["stable_learning_confidence"],
        )
        self.assertGreater(
            strong_profile["session_taste_weight"],
            mixed_profile["session_taste_weight"],
        )

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={
            "feedback_count": 10,
            "session_positive_feedback_count": 7,
            "session_negative_feedback_count": 1,
            "stable_positive_feedback_count": 7,
            "stable_negative_feedback_count": 1,
            "session_preferred_genres": {"indie pop": 2.0},
            "stable_preferred_genres": {"pop": 3.0},
            "mood_learning_stats": {
                "neutral": {
                    "feedback_count": 1,
                    "positive_feedback_count": 1,
                    "negative_feedback_count": 0,
                    "preferred_genres": {"pop": 1.0},
                    "preferred_valence": 0.62,
                    "preferred_energy": 0.68,
                    "preferred_danceability": 0.74,
                }
            },
        },
    )
    def test_mood_learning_gate_blocks_learned_taste_without_enough_evidence(
        self,
        _mock_prefs,
    ) -> None:
        profile = build_generation_profile(
            user_id="user_gate",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            environment_context="camino al trabajo",
            use_environment=True,
        )

        self.assertFalse(profile["mood_learning_gate_passed"])
        self.assertEqual(profile["taste_profile_mode"], "progressive_contextual")
        self.assertGreaterEqual(profile["session_taste_weight"], 0.0)
        self.assertGreater(profile["stable_taste_weight"], 0.0)
        self.assertLess(profile["mood_learning_application_factor"], 1.0)

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={
            "feedback_count": 25,
            "session_feedback_count": 13,
            "stable_feedback_count": 12,
            "session_positive_feedback_count": 12,
            "session_negative_feedback_count": 1,
            "stable_positive_feedback_count": 12,
            "stable_negative_feedback_count": 0,
            "session_preferred_genres": {"ambient": 2.0},
            "stable_preferred_genres": {"classical": 3.0},
            "mood_learning_stats": {
                "estresado": {
                    "feedback_count": 2,
                    "positive_feedback_count": 2,
                    "negative_feedback_count": 0,
                    "preferred_genres": {"ambient": 2.0, "classical": 1.0},
                    "preferred_valence": 0.45,
                    "preferred_energy": 0.38,
                    "preferred_danceability": 0.22,
                }
            },
        },
    )
    def test_feedback_count_prefers_real_session_count_and_keeps_stable_floor(
        self,
        _mock_prefs,
    ) -> None:
        profile = build_generation_profile(
            user_id="user_real_feedback",
            goal="relajacion",
            mood="estresado",
            stress_level=5,
            energy_level=2,
            noise_category="quiet",
            vocal_preference="instrumental",
            intensity_preference="suave",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=30,
            desired_outcome="mas_calmado",
            environment_context=None,
            use_environment=False,
        )

        self.assertEqual(profile["feedback_count"], 13)
        self.assertFalse(profile["mood_learning_gate_passed"])
        self.assertGreater(profile["stable_taste_weight"], 0.0)
        self.assertGreaterEqual(profile["stable_taste_weight"], profile["session_taste_weight"])

    @patch(
        "app.services.professional_playlist_model_service.get_user_generation_preferences",
        return_value={},
    )
    def test_mainstream_queries_depend_on_popularity_not_familiarity(self, _mock_prefs) -> None:
        familiar_alternative = build_generation_profile(
            user_id="user_4",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="familiar",
            popularity_preference="alternativa",
            session_duration_min=20,
            desired_outcome=None,
            environment_context="calle",
            use_environment=False,
        )
        balanced_mainstream = build_generation_profile(
            user_id="user_5",
            goal="energia",
            mood="neutral",
            stress_level=2,
            energy_level=3,
            noise_category="moderate",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mainstream",
            session_duration_min=20,
            desired_outcome=None,
            environment_context="calle",
            use_environment=False,
        )

        self.assertNotIn("popular upbeat pop", familiar_alternative["primary_queries"])
        self.assertIn("popular upbeat pop", balanced_mainstream["primary_queries"])


if __name__ == "__main__":
    unittest.main()
