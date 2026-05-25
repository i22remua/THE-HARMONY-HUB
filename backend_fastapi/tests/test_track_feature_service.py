from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.track_feature_service import enrich_track_with_features


class TrackFeatureServiceTest(unittest.TestCase):
    @patch(
        "app.services.track_feature_service.get_track_features",
        return_value={
            "bpm": 121,
            "danceability": 0.81,
            "energy_feature": 0.74,
            "valence_feature": 0.79,
            "instrumentalness": 0.0,
            "acousticness": 0.12,
            "matched_source": "track_features",
            "matched_by": "name_field",
            "labels": ["dance"],
        },
    )
    def test_enrich_track_preserves_existing_msd_features(self, _mock_features) -> None:
        track = {
            "id": "spotify_1",
            "catalog_track_id": "energy_047",
            "msd_track_id": "TR-123",
            "name": "Walking On A Dream",
            "artists": ["Empire of the Sun"],
            "bpm": 126,
            "danceability": 0.69,
            "energy_feature": 0.73,
            "valence_feature": 0.83,
            "instrumentalness": 0.0,
            "acousticness": 0.08,
            "_feature_source": "msd_catalog",
            "_feature_match": "catalog_track_id",
            "labels": ["energy", "indie"],
        }

        enriched = enrich_track_with_features(track)

        self.assertEqual(enriched["_feature_source"], "msd_catalog")
        self.assertEqual(enriched["_feature_match"], "catalog_track_id")
        self.assertEqual(enriched["bpm"], 126)
        self.assertAlmostEqual(enriched["danceability"], 0.69)
        self.assertIn("energy", enriched["labels"])
        self.assertIn("dance", enriched["labels"])

    @patch(
        "app.services.track_feature_service.get_track_features",
        return_value={
            "bpm": 124,
            "danceability": 0.83,
            "energy_feature": 0.74,
            "valence_feature": 0.79,
            "instrumentalness": 0.0,
            "acousticness": 0.07,
            "matched_source": "msd_catalog",
            "matched_by": "catalog_track_id",
            "labels": ["energy", "dance"],
        },
    )
    def test_enrich_track_keeps_origin_when_cache_is_msd_backed(self, _mock_features) -> None:
        track = {
            "id": "spotify_2",
            "name": "This Girl",
            "artists": ["Kungs"],
        }

        enriched = enrich_track_with_features(track)

        self.assertEqual(enriched["_feature_source"], "msd_catalog")
        self.assertEqual(enriched["_feature_match"], "catalog_track_id")
        self.assertEqual(enriched["bpm"], 124)
        self.assertAlmostEqual(enriched["energy_feature"], 0.74)


if __name__ == "__main__":
    unittest.main()
