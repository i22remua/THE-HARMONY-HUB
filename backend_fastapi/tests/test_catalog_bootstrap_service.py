from __future__ import annotations

import unittest

from app.services.catalog_bootstrap_service import build_bootstrap_catalog_track


class CatalogBootstrapServiceTest(unittest.TestCase):
    def test_builds_from_dense_audio_row(self) -> None:
        track = {
            "track_id": "abc123",
            "title": "Calm Down",
            "artist_name": "Rema",
            "genre": "latin pop",
            "popularity": 88,
            "duration_ms": 210000,
            "danceability": 0.8,
            "energy": 0.6,
            "acousticness": 0.09,
            "instrumentalness": 0.0,
            "liveness": 0.11,
            "speechiness": 0.04,
            "valence": 0.72,
            "tempo": 107,
        }

        result = build_bootstrap_catalog_track(track, source="test_external")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["spotify_track_id"], "abc123")
        self.assertEqual(result["genre"], "latin pop")
        self.assertEqual(result["selection_source"], "msd_catalog")

    def test_builds_from_sparse_textual_row(self) -> None:
        track = {
            "track_id": "focus_text_1",
            "title": "Intense concentration",
            "artist_name": "Binaural Dreams",
            "labels": ["focus", "binaural", "study"],
            "duration_ms": 152000,
        }

        result = build_bootstrap_catalog_track(track, source="test_external")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertGreater(float(result["instrumentalness"]), 0.7)
        self.assertIn("focus", result["semantic_tags"])


if __name__ == "__main__":
    unittest.main()
