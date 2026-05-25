from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata
from typing import Any

from app.core.config import (
    MSD_CATALOG_PATH,
    MSD_MATCH_CACHE_COLLECTION,
    MSD_TRACKS_COLLECTION,
)
from app.services.firestore_service import get_firestore_client

_LOCAL_CATALOG_CACHE: dict[str, Any] = {
    "path": None,
    "mtime": None,
    "tracks": [],
}


def _catalog_path() -> str:
    return os.getenv("MSD_CATALOG_PATH", MSD_CATALOG_PATH)


def _tracks_collection_name() -> str:
    return os.getenv("MSD_TRACKS_COLLECTION", MSD_TRACKS_COLLECTION)


def _match_cache_collection_name() -> str:
    return os.getenv("MSD_MATCH_CACHE_COLLECTION", MSD_MATCH_CACHE_COLLECTION)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _safe_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "si"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return bool(value)


def _pick_first(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "," in text:
            return [part.strip() for part in text.split(",") if part.strip()]
        return [text]
    return [str(value).strip()]


def _unique_preserve(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for item in items:
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)

    return result


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"\(.*?\)", " ", normalized)
    normalized = re.sub(r"\[.*?\]", " ", normalized)
    normalized = re.sub(r"\bfeat\.?\b.*", " ", normalized)
    normalized = re.sub(r"\bft\.?\b.*", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _build_catalog_search_text(data: dict[str, Any]) -> str:
    parts = [
        data.get("name"),
        " ".join(data.get("artists", [])),
        data.get("album_name"),
        data.get("genre"),
        " ".join(data.get("genres", [])),
        data.get("cluster"),
        data.get("activation_style"),
        " ".join(data.get("labels", [])),
        " ".join(data.get("semantic_tags", [])),
    ]
    return normalize_text(" ".join(str(part or "") for part in parts))


def _coerce_duration_ms(value: Any) -> int:
    numeric = _safe_float(value)
    if numeric is None:
        return 0
    if numeric <= 0:
        return 0
    if numeric < 10000:
        return int(numeric * 1000)
    return int(numeric)


def _stable_catalog_id(msd_track_id: str | None, title: str, artist: str) -> str:
    if msd_track_id:
        return str(msd_track_id)
    digest = hashlib.sha1(f"{title}::{artist}".encode("utf-8")).hexdigest()[:16]
    return f"catalog_{digest}"


def normalize_catalog_track(raw: dict[str, Any], *, source: str) -> dict[str, Any]:
    title = _pick_first(raw.get("title"), raw.get("name"), raw.get("track_name")) or ""
    artists = _coerce_list(
        _pick_first(
            raw.get("artists"),
            raw.get("artist_names"),
        )
    )
    primary_artist = _pick_first(
        raw.get("artist_name"),
        raw.get("artist"),
        artists[0] if artists else None,
    ) or ""
    if not artists and primary_artist:
        artists = [str(primary_artist)]

    msd_track_id = _pick_first(
        raw.get("msd_track_id"),
        raw.get("track_id"),
        raw.get("trackid"),
    )
    catalog_track_id = _pick_first(
        raw.get("catalog_track_id"),
        raw.get("_firestore_document_id"),
        msd_track_id,
    )
    catalog_track_id = _stable_catalog_id(
        str(msd_track_id) if msd_track_id else None,
        str(title),
        str(primary_artist),
    ) if not catalog_track_id else str(catalog_track_id)

    genre = _pick_first(raw.get("genre"), raw.get("primary_genre"))
    genres = _unique_preserve(
        _coerce_list(_pick_first(raw.get("genres"), raw.get("genre_tags")))
        + _coerce_list(genre)
    )
    semantic_tags = _unique_preserve(
        _coerce_list(raw.get("semantic_tags"))
        + _coerce_list(raw.get("tags"))
        + _coerce_list(raw.get("goal_tags"))
    )

    labels = _unique_preserve(
        semantic_tags
        + genres
        + _coerce_list(raw.get("labels"))
        + _coerce_list(raw.get("cluster"))
    )

    popularity = _safe_float(_pick_first(raw.get("popularity"), raw.get("popularity_proxy")))
    popularity_value = int(round(popularity)) if popularity is not None else 0

    normalized = {
        "catalog_track_id": catalog_track_id,
        "msd_track_id": str(msd_track_id) if msd_track_id else None,
        "_catalog_document_id": (
            str(raw.get("_firestore_document_id"))
            if raw.get("_firestore_document_id")
            else None
        ),
        "_catalog_source": source,
        "name": str(title).strip(),
        "title": str(title).strip(),
        "artists": artists,
        "artist_name": str(primary_artist).strip() if primary_artist else None,
        "album_name": _pick_first(raw.get("album_name"), raw.get("release_name")),
        "duration_ms": _coerce_duration_ms(
            _pick_first(raw.get("duration_ms"), raw.get("duration"))
        ),
        "bpm": _safe_float(_pick_first(raw.get("bpm"), raw.get("tempo"))),
        "tempo": _safe_float(_pick_first(raw.get("tempo"), raw.get("bpm"))),
        "danceability": _safe_float(
            _pick_first(raw.get("danceability"), raw.get("danceability_estimated"))
        ),
        "energy_feature": _safe_float(
            _pick_first(raw.get("energy_feature"), raw.get("energy"), raw.get("energy_estimated"))
        ),
        "valence_feature": _safe_float(
            _pick_first(raw.get("valence_feature"), raw.get("valence"), raw.get("valence_estimated"))
        ),
        "instrumentalness": _safe_float(
            _pick_first(raw.get("instrumentalness"), raw.get("instrumentalness_estimated"))
        ),
        "acousticness": _safe_float(
            _pick_first(raw.get("acousticness"), raw.get("acousticness_estimated"))
        ),
        "speechiness": _safe_float(raw.get("speechiness")),
        "liveness": _safe_float(raw.get("liveness")),
        "focus_score": _safe_float(raw.get("focus_score")),
        "calm_score": _safe_float(raw.get("calm_score")),
        "uplift_score": _safe_float(raw.get("uplift_score")),
        "warmth_score": _safe_float(raw.get("warmth_score")),
        "tension_score": _safe_float(raw.get("tension_score")),
        "steadiness_score": _safe_float(raw.get("steadiness_score")),
        "vocal_presence_score": _safe_float(raw.get("vocal_presence_score")),
        "emotional_weight_score": _safe_float(raw.get("emotional_weight_score")),
        "supportiveness_score": _safe_float(raw.get("supportiveness_score")),
        "activation_style": raw.get("activation_style"),
        "genre": genre,
        "genres": genres,
        "cluster": raw.get("cluster"),
        "labels": labels,
        "semantic_tags": semantic_tags,
        "popularity": popularity_value,
        "popularity_proxy": popularity_value,
        "explicit": _safe_bool(raw.get("explicit")) or False,
        "spotify_track_id": _pick_first(raw.get("spotify_track_id"), raw.get("spotify_id")),
        "spotify_uri": _pick_first(raw.get("spotify_uri"), raw.get("uri")),
        "spotify_url": raw.get("spotify_url"),
        "spotify_match": raw.get("spotify_match"),
        "source_dataset": _pick_first(raw.get("source_dataset"), "msd"),
        "selection_source": "msd_catalog",
        "_feature_source": "msd_catalog",
        "_feature_match": "catalog_track_id",
    }

    if normalized["spotify_track_id"] and not normalized["spotify_uri"]:
        normalized["spotify_uri"] = f"spotify:track:{normalized['spotify_track_id']}"

    normalized["_catalog_search_text"] = _build_catalog_search_text(normalized)
    return normalized


def _read_local_catalog_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    rows: list[dict[str, Any]] = []

    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                text = line.strip()
                if not text:
                    continue
                rows.append(json.loads(text))
        return rows

    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("tracks") or []
        return [row for row in items if isinstance(row, dict)]
    return []


def load_local_catalog(limit: int | None = None) -> list[dict[str, Any]]:
    path = Path(_catalog_path())
    if not path.exists():
        return []

    mtime = path.stat().st_mtime
    cache_valid = (
        _LOCAL_CATALOG_CACHE.get("path") == str(path)
        and _LOCAL_CATALOG_CACHE.get("mtime") == mtime
        and _LOCAL_CATALOG_CACHE.get("tracks")
    )
    if cache_valid:
        tracks = list(_LOCAL_CATALOG_CACHE.get("tracks", []))
        return tracks[:limit] if limit else tracks

    raw_rows = _read_local_catalog_file(path)
    tracks = [
        normalize_catalog_track(row, source="local_file")
        for row in raw_rows
        if isinstance(row, dict)
    ]

    _LOCAL_CATALOG_CACHE["path"] = str(path)
    _LOCAL_CATALOG_CACHE["mtime"] = mtime
    _LOCAL_CATALOG_CACHE["tracks"] = tracks

    return tracks[:limit] if limit else tracks


def load_firestore_catalog(limit: int = 2000) -> list[dict[str, Any]]:
    try:
        db = get_firestore_client()
        docs = db.collection(_tracks_collection_name()).limit(limit).stream()
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    for doc in docs:
        data = doc.to_dict() or {}
        data["_firestore_document_id"] = doc.id
        rows.append(normalize_catalog_track(data, source="firestore"))
    return rows


def _catalog_identity_key(track: dict[str, Any]) -> str:
    catalog_track_id = str(track.get("catalog_track_id") or "").strip()
    if catalog_track_id:
        return f"id::{catalog_track_id}"

    title = normalize_text(track.get("name") or track.get("title"))
    artist = normalize_text(track.get("artist_name") or " ".join(track.get("artists", [])))
    return f"identity::{title}::{artist}"


def merge_catalog_tracks(
    *track_groups: list[dict[str, Any]],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for group in track_groups:
        for track in group:
            key = _catalog_identity_key(track)
            if key in seen:
                continue
            seen.add(key)
            merged.append(track)
            if limit and len(merged) >= limit:
                return merged

    return merged


def load_catalog_tracks(limit: int | None = None) -> list[dict[str, Any]]:
    local_tracks = load_local_catalog(limit=None)
    explicit_local_catalog = bool(os.getenv("MSD_CATALOG_PATH"))
    if explicit_local_catalog and local_tracks:
        return local_tracks[:limit] if limit else local_tracks

    firestore_limit = max((limit or 500) * 4, 2000)
    firestore_tracks = load_firestore_catalog(limit=firestore_limit)

    merged = merge_catalog_tracks(local_tracks, firestore_tracks, limit=limit)
    if merged:
        return merged

    return []


def get_cached_spotify_identity(track: dict[str, Any]) -> dict[str, Any] | None:
    spotify_track_id = _pick_first(track.get("spotify_track_id"), track.get("id"))
    spotify_uri = _pick_first(track.get("spotify_uri"), track.get("uri"))

    if not spotify_track_id and not spotify_uri:
        return None

    return {
        "id": spotify_track_id,
        "uri": spotify_uri or f"spotify:track:{spotify_track_id}",
        "spotify_url": track.get("spotify_url"),
        "album_name": track.get("album_name"),
        "duration_ms": track.get("duration_ms"),
        "popularity": track.get("popularity", 0),
    }


def persist_spotify_match(
    catalog_track: dict[str, Any],
    spotify_track: dict[str, Any],
    *,
    match_score: float,
) -> None:
    catalog_track_id = catalog_track.get("catalog_track_id")
    if not catalog_track_id:
        return

    payload = {
        "catalog_track_id": catalog_track_id,
        "msd_track_id": catalog_track.get("msd_track_id"),
        "title": catalog_track.get("name"),
        "artist_name": catalog_track.get("artist_name"),
        "spotify_track_id": spotify_track.get("id"),
        "spotify_uri": spotify_track.get("uri"),
        "spotify_url": spotify_track.get("spotify_url"),
        "spotify_match": {
            "score": round(match_score, 3),
            "matched_at": datetime.now(UTC).isoformat(),
            "title": spotify_track.get("name"),
            "artists": spotify_track.get("artists", []),
        },
        "updated_at": datetime.now(UTC),
    }

    try:
        db = get_firestore_client()
        db.collection(_match_cache_collection_name()).document(str(catalog_track_id)).set(
            payload,
            merge=True,
        )

        if catalog_track.get("_catalog_source") == "firestore":
            document_id = catalog_track.get("_catalog_document_id") or catalog_track_id
            db.collection(_tracks_collection_name()).document(str(document_id)).set(
                payload,
                merge=True,
            )
    except Exception:
        return
