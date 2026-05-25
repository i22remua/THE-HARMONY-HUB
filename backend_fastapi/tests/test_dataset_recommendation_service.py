from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

import app.services.msd_catalog_service as msd_catalog_service
from app.services.dataset_recommendation_service import select_dataset_candidates


class DatasetRecommendationServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.catalog_path = Path(self.temp_dir.name) / "msd_test_catalog.jsonl"
        rows = [
            {
                "msd_track_id": "focus_1",
                "title": "Deep Focus Piano",
                "artist_name": "Calm Artist",
                "duration": 210.0,
                "tempo": 72,
                "energy_estimated": 0.34,
                "valence_estimated": 0.52,
                "danceability_estimated": 0.18,
                "instrumentalness_estimated": 0.91,
                "acousticness_estimated": 0.74,
                "semantic_tags": ["focus", "ambient", "instrumental"],
                "genre": "ambient",
                "focus_score": 0.92,
                "calm_score": 0.80,
                "uplift_score": 0.18,
                "cluster": "focus_cluster",
                "popularity_proxy": 58,
            },
            {
                "msd_track_id": "energy_1",
                "title": "Night Club Booster",
                "artist_name": "Party Artist",
                "duration": 205.0,
                "tempo": 128,
                "energy_estimated": 0.88,
                "valence_estimated": 0.79,
                "danceability_estimated": 0.84,
                "instrumentalness_estimated": 0.02,
                "semantic_tags": ["dance", "energy", "party"],
                "genre": "edm",
                "focus_score": 0.05,
                "calm_score": 0.04,
                "uplift_score": 0.94,
                "cluster": "energy_cluster",
                "popularity_proxy": 72,
            },
            {
                "msd_track_id": "focus_2",
                "title": "Study Strings",
                "artist_name": "Preferred Artist",
                "duration": 198.0,
                "tempo": 76,
                "energy_estimated": 0.38,
                "valence_estimated": 0.48,
                "danceability_estimated": 0.22,
                "instrumentalness_estimated": 0.87,
                "semantic_tags": ["study", "instrumental", "focus"],
                "genre": "classical",
                "focus_score": 0.83,
                "calm_score": 0.71,
                "uplift_score": 0.20,
                "cluster": "focus_cluster",
                "popularity_proxy": 45,
            },
        ]
        with self.catalog_path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")

        os.environ["MSD_CATALOG_PATH"] = str(self.catalog_path)
        msd_catalog_service._LOCAL_CATALOG_CACHE["path"] = None
        msd_catalog_service._LOCAL_CATALOG_CACHE["mtime"] = None
        msd_catalog_service._LOCAL_CATALOG_CACHE["tracks"] = []

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("MSD_CATALOG_PATH", None)

    def test_select_dataset_candidates_prioritizes_focus_alignment(self) -> None:
        profile = {
            "goal": "foco",
            "mood": "neutral",
            "seed_genres": ["ambient", "classical"],
            "primary_queries": ["deep focus instrumental", "study ambient"],
            "target_energy": 0.36,
            "target_valence": 0.50,
            "target_danceability": 0.20,
            "vocal_preference": "instrumental",
            "intensity_preference": "suave",
            "popularity_preference": "mixta",
        }

        candidates = select_dataset_candidates(
            profile=profile,
            affinity_context={"preferred_artist_names": ["Preferred Artist"]},
            limit=5,
        )

        self.assertGreaterEqual(len(candidates), 2)
        top_ids = [candidates[0]["msd_track_id"], candidates[1]["msd_track_id"]]
        self.assertCountEqual(top_ids, ["focus_1", "focus_2"])
        self.assertTrue(all(item["selection_source"] == "msd_catalog" for item in candidates[:2]))
        self.assertNotIn("energy_1", [item["msd_track_id"] for item in candidates[:2]])

    def test_select_dataset_candidates_soft_companionship_avoids_hard_energy(self) -> None:
        companionship_catalog = Path(self.temp_dir.name) / "companionship_catalog.jsonl"
        rows = [
            {
                "msd_track_id": "warm_1",
                "title": "Warm Familiar Pop",
                "artist_name": "Gentle Artist",
                "duration": 205.0,
                "tempo": 102,
                "energy_estimated": 0.58,
                "valence_estimated": 0.61,
                "danceability_estimated": 0.46,
                "instrumentalness_estimated": 0.0,
                "semantic_tags": ["warm", "comfort", "soft vocal", "indie"],
                "genre": "indie pop",
                "focus_score": 0.1,
                "calm_score": 0.34,
                "uplift_score": 0.71,
                "warmth_score": 0.92,
                "steadiness_score": 0.82,
                "vocal_presence_score": 0.91,
                "supportiveness_score": 0.94,
                "tension_score": 0.10,
                "activation_style": "progressive",
                "cluster": "energy_indie",
                "popularity_proxy": 66,
            },
            {
                "msd_track_id": "hard_1",
                "title": "Titanium Firework Anthem",
                "artist_name": "Big Room Artist",
                "duration": 240.0,
                "tempo": 126,
                "energy_estimated": 0.88,
                "valence_estimated": 0.72,
                "danceability_estimated": 0.79,
                "instrumentalness_estimated": 0.0,
                "semantic_tags": ["anthem", "edm", "dance", "party"],
                "genre": "edm",
                "focus_score": 0.05,
                "calm_score": 0.03,
                "uplift_score": 0.93,
                "warmth_score": 0.30,
                "steadiness_score": 0.56,
                "vocal_presence_score": 0.89,
                "supportiveness_score": 0.41,
                "tension_score": 0.48,
                "activation_style": "peak",
                "cluster": "energy_power",
                "popularity_proxy": 84,
            },
        ]
        with companionship_catalog.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")

        os.environ["MSD_CATALOG_PATH"] = str(companionship_catalog)
        msd_catalog_service._LOCAL_CATALOG_CACHE["path"] = None
        msd_catalog_service._LOCAL_CATALOG_CACHE["mtime"] = None
        msd_catalog_service._LOCAL_CATALOG_CACHE["tracks"] = []

        profile = {
            "goal": "energia",
            "mood": "triste",
            "desired_outcome": "mas_acompanado",
            "seed_genres": ["pop", "dance", "edm"],
            "primary_queries": ["warm familiar pop", "gentle positive pop"],
            "target_energy": 0.60,
            "target_valence": 0.62,
            "target_danceability": 0.48,
            "vocal_preference": "con_voz",
            "intensity_preference": "suave",
            "popularity_preference": "mainstream",
            "session_subtype": "warm_companionship",
            "activation_curve": "progressive",
            "target_warmth": 0.88,
            "target_steadiness": 0.72,
            "target_vocal_presence": 0.82,
        }

        candidates = select_dataset_candidates(
            profile=profile,
            affinity_context={},
            limit=5,
        )

        self.assertEqual(candidates[0]["msd_track_id"], "warm_1")
        self.assertEqual(candidates[1]["msd_track_id"], "hard_1")

    def test_select_dataset_candidates_uses_functional_scores_for_deep_focus(self) -> None:
        functional_catalog = Path(self.temp_dir.name) / "functional_catalog.jsonl"
        rows = [
            {
                "msd_track_id": "focus_strong",
                "title": "Steady Focus Field",
                "artist_name": "Minimal Artist",
                "duration": 210.0,
                "tempo": 70,
                "energy_estimated": 0.34,
                "valence_estimated": 0.48,
                "danceability_estimated": 0.12,
                "instrumentalness_estimated": 0.96,
                "semantic_tags": ["focus", "instrumental", "study"],
                "genre": "ambient",
                "focus_score": 0.86,
                "calm_score": 0.82,
                "uplift_score": 0.14,
                "warmth_score": 0.34,
                "steadiness_score": 0.94,
                "vocal_presence_score": 0.04,
                "supportiveness_score": 0.76,
                "tension_score": 0.10,
                "activation_style": "flat",
                "cluster": "focus_cluster",
                "popularity_proxy": 52,
            },
            {
                "msd_track_id": "focus_weak",
                "title": "Nervous Focus Field",
                "artist_name": "Bright Artist",
                "duration": 210.0,
                "tempo": 70,
                "energy_estimated": 0.34,
                "valence_estimated": 0.48,
                "danceability_estimated": 0.12,
                "instrumentalness_estimated": 0.96,
                "semantic_tags": ["focus", "instrumental", "study"],
                "genre": "ambient",
                "focus_score": 0.86,
                "calm_score": 0.82,
                "uplift_score": 0.14,
                "warmth_score": 0.34,
                "steadiness_score": 0.58,
                "vocal_presence_score": 0.04,
                "supportiveness_score": 0.54,
                "tension_score": 0.42,
                "activation_style": "peak",
                "cluster": "focus_cluster",
                "popularity_proxy": 52,
            },
        ]
        with functional_catalog.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")

        os.environ["MSD_CATALOG_PATH"] = str(functional_catalog)
        msd_catalog_service._LOCAL_CATALOG_CACHE["path"] = None
        msd_catalog_service._LOCAL_CATALOG_CACHE["mtime"] = None
        msd_catalog_service._LOCAL_CATALOG_CACHE["tracks"] = []

        profile = {
            "goal": "foco",
            "mood": "neutral",
            "seed_genres": ["ambient"],
            "primary_queries": ["deep focus instrumental"],
            "target_energy": 0.34,
            "target_valence": 0.48,
            "target_danceability": 0.12,
            "vocal_preference": "instrumental",
            "intensity_preference": "media",
            "popularity_preference": "mixta",
            "session_subtype": "deep_focus",
            "activation_curve": "flat",
            "target_warmth": 0.34,
            "target_steadiness": 0.90,
            "target_vocal_presence": 0.05,
        }

        candidates = select_dataset_candidates(
            profile=profile,
            affinity_context={},
            limit=5,
        )

        self.assertEqual(candidates[0]["msd_track_id"], "focus_strong")
        self.assertEqual(candidates[1]["msd_track_id"], "focus_weak")


if __name__ == "__main__":
    unittest.main()
