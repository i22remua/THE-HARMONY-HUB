from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.spotify_track_matching_service import (
    compute_spotify_match_score,
    materialize_ranked_tracks_for_spotify,
    search_best_spotify_match,
)


class SpotifyTrackMatchingServiceTest(unittest.IsolatedAsyncioTestCase):
    def test_match_score_handles_remaster_noise(self) -> None:
        catalog_track = {
            "name": "Song Name (Remastered 2011)",
            "artist_name": "The Artist",
            "duration_ms": 200000,
        }
        spotify_track = {
            "name": "Song Name",
            "artists": ["The Artist"],
            "duration_ms": 201200,
            "popularity": 68,
        }

        score = compute_spotify_match_score(catalog_track, spotify_track)
        self.assertGreaterEqual(score, 0.9)

    async def test_search_best_spotify_match_prefers_title_plus_artist(self) -> None:
        catalog_track = {
            "name": "Song Name (Remastered 2011)",
            "artist_name": "The Artist",
            "duration_ms": 200000,
        }

        async def fake_search_tracks(access_token: str, query: str, limit: int, market: str):
            return [
                {
                    "id": "wrong",
                    "name": "Different Song",
                    "uri": "spotify:track:wrong",
                    "artists": ["Another Artist"],
                    "duration_ms": 198000,
                    "popularity": 80,
                },
                {
                    "id": "right",
                    "name": "Song Name",
                    "uri": "spotify:track:right",
                    "artists": ["The Artist"],
                    "duration_ms": 201000,
                    "popularity": 67,
                },
            ]

        with patch(
            "app.services.spotify_track_matching_service.search_tracks",
            side_effect=fake_search_tracks,
        ):
            match = await search_best_spotify_match(
                access_token="token",
                track=catalog_track,
                market="ES",
            )

        self.assertIsNotNone(match)
        self.assertEqual(match["id"], "right")
        self.assertGreaterEqual(match["_spotify_match_score"], 0.9)

    async def test_materialize_ranked_tracks_uses_cached_identity_before_searching(self) -> None:
        ranked_tracks = [
            {
                "catalog_track_id": "cached_1",
                "name": "Cached Song",
                "artist_name": "Known Artist",
                "artists": ["Known Artist"],
                "spotify_track_id": "cached_spotify_id",
                "spotify_uri": "spotify:track:cached_spotify_id",
                "duration_ms": 190000,
            },
            {
                "catalog_track_id": "fresh_1",
                "name": "Fresh Song",
                "artist_name": "New Artist",
                "artists": ["New Artist"],
                "duration_ms": 200000,
            },
        ]

        async def fake_search_best_spotify_match(**kwargs):
            return {
                "id": "fresh_spotify_id",
                "uri": "spotify:track:fresh_spotify_id",
                "name": "Fresh Song",
                "artists": ["New Artist"],
                "duration_ms": 201000,
                "popularity": 51,
                "_spotify_match_score": 0.95,
                "_spotify_match_query": "Fresh Song New Artist",
            }

        with patch(
            "app.services.spotify_track_matching_service.search_best_spotify_match",
            side_effect=fake_search_best_spotify_match,
        ), patch(
            "app.services.spotify_track_matching_service.persist_spotify_match",
            return_value=None,
        ):
            materialized, stats = await materialize_ranked_tracks_for_spotify(
                access_token="token",
                ranked_tracks=ranked_tracks,
                market="ES",
                min_candidates=2,
                max_searches=3,
            )

        self.assertEqual(len(materialized), 2)
        self.assertEqual(materialized[0]["uri"], "spotify:track:cached_spotify_id")
        self.assertEqual(materialized[1]["uri"], "spotify:track:fresh_spotify_id")
        self.assertEqual(stats["cached_matches"], 1)
        self.assertEqual(stats["fresh_matches"], 1)


if __name__ == "__main__":
    unittest.main()
