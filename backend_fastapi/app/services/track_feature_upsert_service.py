from datetime import datetime, UTC
from typing import Any

from app.services.firestore_service import get_firestore_client

TARGET_COLLECTION = "track_features"


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


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []
    return [str(value).strip()]


def _merge_unique(existing: list[str] | None, incoming: list[str] | None) -> list[str]:
    result: list[str] = []
    seen = set()

    for item in (existing or []) + (incoming or []):
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)

    return result


def _drop_none_fields(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None}


def _prefer_existing(existing_value: Any, incoming_value: Any) -> Any:
    return existing_value if existing_value is not None else incoming_value


def _extract_numeric_features(track: dict) -> dict:
    return {
        "bpm": _safe_float(
            _pick_first(
                track.get("bpm"),
                track.get("tempo"),
                track.get("audio_tempo"),
            )
        ),
        "danceability": _safe_float(
            _pick_first(
                track.get("danceability"),
                track.get("danceability_feature"),
                track.get("audio_danceability"),
            )
        ),
        "energy": _safe_float(
            _pick_first(
                track.get("energy_feature"),
                track.get("energy"),
                track.get("audio_energy"),
            )
        ),
        "valence": _safe_float(
            _pick_first(
                track.get("valence_feature"),
                track.get("valence"),
                track.get("audio_valence"),
            )
        ),
        "instrumentalness": _safe_float(
            _pick_first(
                track.get("instrumentalness"),
                track.get("audio_instrumentalness"),
            )
        ),
        "acousticness": _safe_float(
            _pick_first(
                track.get("acousticness"),
                track.get("audio_acousticness"),
            )
        ),
        "speechiness": _safe_float(
            _pick_first(
                track.get("speechiness"),
                track.get("audio_speechiness"),
            )
        ),
        "liveness": _safe_float(
            _pick_first(
                track.get("liveness"),
                track.get("audio_liveness"),
            )
        ),
    }


def upsert_track_feature_from_track(track: dict) -> None:
    track_id = _pick_first(track.get("id"), track.get("track_id"))
    if not track_id:
        return

    db = get_firestore_client()
    ref = db.collection(TARGET_COLLECTION).document(str(track_id))
    snap = ref.get()
    existing = snap.to_dict() if snap.exists else {}

    artists = _as_list(track.get("artists"))
    artist = _pick_first(
        track.get("artist"),
        track.get("artist_label"),
        artists[0] if artists else None,
    )

    features = _extract_numeric_features(track)

    incoming = {
        "track_id": str(track_id),
        "catalog_track_id": _pick_first(track.get("catalog_track_id")),
        "msd_track_id": _pick_first(track.get("msd_track_id")),
        "name": _pick_first(track.get("name"), track.get("track_name")),
        "artist": artist,
        "artists": artists,
        "bpm": features["bpm"],
        "danceability": features["danceability"],
        "energy": features["energy"],
        "valence": features["valence"],
        "instrumentalness": features["instrumentalness"],
        "acousticness": features["acousticness"],
        "speechiness": features["speechiness"],
        "liveness": features["liveness"],
        "labels": _as_list(track.get("labels")),
        "duration_ms": track.get("duration_ms"),
        "popularity": track.get("popularity"),
        "explicit": _safe_bool(track.get("explicit")),
        "feature_source": _pick_first(track.get("_feature_source"), track.get("feature_source")),
        "feature_match": _pick_first(track.get("_feature_match"), track.get("feature_match")),
        "selection_source": track.get("selection_source"),
        "spotify_uri": _pick_first(track.get("spotify_uri"), track.get("uri")),
        "spotify_match": track.get("spotify_match"),
        "created_at": existing.get("created_at") or datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    merged = {
        "track_id": _prefer_existing(existing.get("track_id"), incoming.get("track_id")),
        "catalog_track_id": _prefer_existing(
            existing.get("catalog_track_id"),
            incoming.get("catalog_track_id"),
        ),
        "msd_track_id": _prefer_existing(
            existing.get("msd_track_id"),
            incoming.get("msd_track_id"),
        ),
        "name": _prefer_existing(existing.get("name"), incoming.get("name")),
        "artist": _prefer_existing(existing.get("artist"), incoming.get("artist")),
        "artists": _merge_unique(existing.get("artists"), incoming.get("artists")),
        "bpm": _prefer_existing(existing.get("bpm"), incoming.get("bpm")),
        "danceability": _prefer_existing(
            existing.get("danceability"),
            incoming.get("danceability"),
        ),
        "energy": _prefer_existing(existing.get("energy"), incoming.get("energy")),
        "valence": _prefer_existing(existing.get("valence"), incoming.get("valence")),
        "instrumentalness": _prefer_existing(
            existing.get("instrumentalness"),
            incoming.get("instrumentalness"),
        ),
        "acousticness": _prefer_existing(
            existing.get("acousticness"),
            incoming.get("acousticness"),
        ),
        "speechiness": _prefer_existing(
            existing.get("speechiness"),
            incoming.get("speechiness"),
        ),
        "liveness": _prefer_existing(existing.get("liveness"), incoming.get("liveness")),
        "duration_ms": _prefer_existing(
            existing.get("duration_ms"),
            incoming.get("duration_ms"),
        ),
        "popularity": _prefer_existing(
            existing.get("popularity"),
            incoming.get("popularity"),
        ),
        "explicit": _prefer_existing(existing.get("explicit"), incoming.get("explicit")),
        "feature_source": _prefer_existing(
            existing.get("feature_source"),
            incoming.get("feature_source"),
        ),
        "feature_match": _prefer_existing(
            existing.get("feature_match"),
            incoming.get("feature_match"),
        ),
        "selection_source": _prefer_existing(
            existing.get("selection_source"),
            incoming.get("selection_source"),
        ),
        "spotify_uri": _prefer_existing(
            existing.get("spotify_uri"),
            incoming.get("spotify_uri"),
        ),
        "spotify_match": _prefer_existing(
            existing.get("spotify_match"),
            incoming.get("spotify_match"),
        ),
        "labels": _merge_unique(existing.get("labels"), incoming.get("labels")),
        "created_at": existing.get("created_at") or incoming.get("created_at"),
        "updated_at": datetime.now(UTC),
    }

    ref.set(_drop_none_fields(merged), merge=True)


def upsert_track_features_from_tracks(tracks: list[dict]) -> None:
    for track in tracks:
        upsert_track_feature_from_track(track)
