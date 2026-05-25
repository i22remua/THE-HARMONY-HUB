from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Any

from app.services.msd_catalog_service import (
    get_cached_spotify_identity,
    normalize_text,
    persist_spotify_match,
)
from app.services.spotify_service import SpotifyRateLimitError, search_tracks


def _clean_title(value: str | None) -> str:
    text = normalize_text(value)
    text = re.sub(r"\b(remaster(ed)?|mono|stereo|radio edit|live|version)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_artist(value: str | None) -> str:
    text = normalize_text(value)
    text = re.sub(r"\b(feat|ft)\b.*", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.92
    return SequenceMatcher(None, a, b).ratio()


def _duration_alignment(catalog_duration_ms: int | None, spotify_duration_ms: int | None) -> float:
    if not catalog_duration_ms or not spotify_duration_ms:
        return 0.0
    diff = abs(int(catalog_duration_ms) - int(spotify_duration_ms))
    if diff <= 2500:
        return 1.0
    if diff <= 7000:
        return 0.7
    if diff <= 15000:
        return 0.35
    return 0.0


def compute_spotify_match_score(catalog_track: dict[str, Any], spotify_track: dict[str, Any]) -> float:
    catalog_title = _clean_title(catalog_track.get("name"))
    spotify_title = _clean_title(spotify_track.get("name"))
    title_score = _similarity(catalog_title, spotify_title)

    catalog_artist = _clean_artist(
        catalog_track.get("artist_name")
        or (catalog_track.get("artists", [None]) or [None])[0]
    )
    spotify_artists = [
        _clean_artist(artist)
        for artist in (spotify_track.get("artists", []) or [])
        if artist
    ]
    artist_score = max((_similarity(catalog_artist, artist) for artist in spotify_artists), default=0.0)
    duration_score = _duration_alignment(
        catalog_track.get("duration_ms"),
        spotify_track.get("duration_ms"),
    )
    popularity_bonus = min(0.08, max(0.0, float(spotify_track.get("popularity", 0) or 0) / 1000))

    return round(
        (title_score * 0.56)
        + (artist_score * 0.34)
        + (duration_score * 0.08)
        + popularity_bonus,
        4,
    )


def _query_variants(track: dict[str, Any]) -> list[str]:
    title = str(track.get("name", "") or "").strip()
    artist = str(
        track.get("artist_name")
        or (track.get("artists", [None]) or [None])[0]
        or ""
    ).strip()
    cleaned_title = _clean_title(title)

    variants = [
        f'track:"{title}" artist:"{artist}"' if title and artist else "",
        f"{title} {artist}".strip(),
        f"{cleaned_title} {artist}".strip() if cleaned_title and artist else "",
        cleaned_title,
    ]

    deduped: list[str] = []
    seen: set[str] = set()
    for item in variants:
        query = item.strip()
        if not query:
            continue
        key = query.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(query)
        if len(deduped) >= 3:
            break
    return deduped


async def search_best_spotify_match(
    *,
    access_token: str,
    track: dict[str, Any],
    market: str = "ES",
    per_query_limit: int = 5,
    min_score: float = 0.72,
) -> dict[str, Any] | None:
    best_match: dict[str, Any] | None = None
    best_score = 0.0

    for query in _query_variants(track):
        try:
            results = await search_tracks(
                access_token=access_token,
                query=query,
                limit=per_query_limit,
                market=market,
            )
        except SpotifyRateLimitError:
            raise
        except Exception:
            continue

        for result in results:
            score = compute_spotify_match_score(track, result)
            if score <= best_score:
                continue
            best_score = score
            best_match = {
                **result,
                "_spotify_match_score": round(score, 4),
                "_spotify_match_query": query,
            }

        if best_score >= 0.93:
            break

    if not best_match or best_score < min_score:
        return None
    return best_match


async def materialize_ranked_tracks_for_spotify(
    *,
    access_token: str,
    ranked_tracks: list[dict[str, Any]],
    market: str,
    min_candidates: int,
    max_searches: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    materialized: list[dict[str, Any]] = []
    stats = {
        "already_playable": 0,
        "cached_matches": 0,
        "fresh_matches": 0,
        "failed_matches": 0,
        "searches": 0,
        "rate_limited": False,
    }

    for track in ranked_tracks:
        if track.get("uri") and track.get("id"):
            materialized.append(track)
            stats["already_playable"] += 1
            if len(materialized) >= min_candidates:
                break
            continue

        cached_identity = get_cached_spotify_identity(track)
        if cached_identity and cached_identity.get("uri"):
            merged = dict(track)
            merged["id"] = cached_identity.get("id")
            merged["uri"] = cached_identity.get("uri")
            merged["spotify_track_id"] = cached_identity.get("id")
            merged["spotify_uri"] = cached_identity.get("uri")
            merged["spotify_url"] = cached_identity.get("spotify_url")
            if cached_identity.get("duration_ms"):
                merged["duration_ms"] = cached_identity.get("duration_ms")
            if cached_identity.get("popularity") is not None:
                merged["spotify_popularity"] = cached_identity.get("popularity")
            merged["_spotify_match_score"] = 1.0
            materialized.append(merged)
            stats["cached_matches"] += 1
            if len(materialized) >= min_candidates:
                break
            continue

        if stats["searches"] >= max_searches:
            break

        try:
            match = await search_best_spotify_match(
                access_token=access_token,
                track=track,
                market=market,
            )
        except SpotifyRateLimitError as exc:
            stats["rate_limited"] = True
            print(
                f"[SPOTIFY SEARCH] materialization abortada por rate limit. "
                f"query='{exc.query}'"
            )
            break
        stats["searches"] += 1

        if not match:
            stats["failed_matches"] += 1
            continue

        merged = dict(track)
        merged["id"] = match.get("id")
        merged["uri"] = match.get("uri")
        merged["spotify_track_id"] = match.get("id")
        merged["spotify_uri"] = match.get("uri")
        merged["spotify_url"] = match.get("spotify_url")
        merged["spotify_match"] = {
            "score": match.get("_spotify_match_score"),
            "query": match.get("_spotify_match_query"),
            "name": match.get("name"),
            "artists": match.get("artists", []),
        }
        merged["spotify_popularity"] = match.get("popularity")
        merged["album_name"] = merged.get("album_name") or match.get("album_name")
        if match.get("duration_ms"):
            merged["duration_ms"] = match.get("duration_ms")
        if merged.get("popularity", 0) == 0 and match.get("popularity") is not None:
            merged["popularity"] = match.get("popularity")

        persist_spotify_match(
            track,
            match,
            match_score=float(match.get("_spotify_match_score", 0.0) or 0.0),
        )

        materialized.append(merged)
        stats["fresh_matches"] += 1

        if len(materialized) >= min_candidates:
            break

    return materialized, stats
