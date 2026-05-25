from __future__ import annotations

import unittest

from app.services.msd_catalog_service import merge_catalog_tracks


class MsdCatalogServiceTest(unittest.TestCase):
    def test_merge_catalog_tracks_deduplicates_by_catalog_id(self) -> None:
        local_tracks = [
            {"catalog_track_id": "track_1", "name": "Song A", "artists": ["Artist A"]},
        ]
        firestore_tracks = [
            {"catalog_track_id": "track_1", "name": "Song A", "artists": ["Artist A"]},
            {"catalog_track_id": "track_2", "name": "Song B", "artists": ["Artist B"]},
        ]

        merged = merge_catalog_tracks(local_tracks, firestore_tracks)

        self.assertEqual([track["catalog_track_id"] for track in merged], ["track_1", "track_2"])

    def test_merge_catalog_tracks_deduplicates_by_identity_when_id_missing(self) -> None:
        local_tracks = [
            {"name": "Free Mind", "artist_name": "Tems", "artists": ["Tems"]},
        ]
        firestore_tracks = [
            {"title": "Free Mind", "artist_name": "Tems", "artists": ["Tems"]},
            {"title": "Firestone", "artist_name": "Kygo", "artists": ["Kygo"]},
        ]

        merged = merge_catalog_tracks(local_tracks, firestore_tracks)

        self.assertEqual(len(merged), 2)


if __name__ == "__main__":
    unittest.main()
