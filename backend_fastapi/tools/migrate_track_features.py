from datetime import datetime, UTC
from pathlib import Path
import re
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.firestore_service import get_firestore_client

SOURCE_COLLECTIONS = [
    "Tracks",
    "audio_analysis",
    "audio_metadata",
    "music_library",
]

TARGET_COLLECTION = "track_features"


def _normalize_text(value):
    if not value:
        return ""
    value = str(value).strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []
    return [str(value).strip()]


def _merge_labels(*candidates):
    result = []
    seen = set()

    for candidate in candidates:
        if candidate is None:
            continue

        if isinstance(candidate, list):
            values = candidate
        else:
            values = [candidate]

        for item in values:
            item = str(item).strip().lower()
            if item and item not in seen:
                seen.add(item)
                result.append(item)

    return result


def _safe_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _pick_first(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _drop_none_fields(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None}


def _is_meaningful_record(data: dict) -> bool:
    return any([
        data.get("name"),
        data.get("artist"),
        data.get("artists"),
        data.get("bpm") is not None,
        data.get("energy") is not None,
        data.get("valence") is not None,
        data.get("danceability") is not None,
        data.get("acousticness") is not None,
        data.get("instrumentalness") is not None,
        data.get("speechiness") is not None,
        data.get("labels"),
    ])


def _extract_acoustic(data: dict) -> dict:
    acoustic = data.get("acoustic_features", {}) or {}

    return {
        "bpm": _pick_first(
            acoustic.get("bpm"),
            acoustic.get("tempo"),
            data.get("bpm"),
            data.get("tempo"),
        ),
        "energy": _pick_first(
            acoustic.get("energy"),
            data.get("energy"),
        ),
        "valence": _pick_first(
            acoustic.get("valence"),
            data.get("valence"),
        ),
        "danceability": _pick_first(
            acoustic.get("danceability"),
            data.get("danceability"),
        ),
        "acousticness": _pick_first(
            acoustic.get("acousticness"),
            data.get("acousticness"),
        ),
        "instrumentalness": _pick_first(
            acoustic.get("instrumentalness"),
            data.get("instrumentalness"),
        ),
        "speechiness": _pick_first(
            acoustic.get("speechiness"),
            data.get("speechiness"),
        ),
    }


def _extract_track_record(doc_id: str, collection_name: str, data: dict) -> dict | None:
    acoustic = _extract_acoustic(data)

    track_id = _pick_first(
        data.get("track_id"),
        data.get("id"),
        data.get("spotify_track_id"),
    )

    if not track_id:
        return None

    artist = _pick_first(
        data.get("artist"),
        data.get("main_artist"),
    )

    artists = _pick_first(
        data.get("artists"),
        [artist] if artist else [],
    )

    labels = _merge_labels(
        data.get("labels"),
        data.get("tags"),
        data.get("tag"),
    )

    record = {
        "track_id": str(track_id),
        "name": _pick_first(
            data.get("name"),
            data.get("track_name"),
            data.get("title"),
        ),
        "artist": artist,
        "artists": _as_list(artists),
        "bpm": _safe_float(acoustic["bpm"]),
        "energy": _safe_float(acoustic["energy"]),
        "valence": _safe_float(acoustic["valence"]),
        "danceability": _safe_float(acoustic["danceability"]),
        "acousticness": _safe_float(acoustic["acousticness"]),
        "instrumentalness": _safe_float(acoustic["instrumentalness"]),
        "speechiness": _safe_float(acoustic["speechiness"]),
        "labels": labels,
        "source_collections": [collection_name],
        "updated_at": datetime.now(UTC),
    }

    return _drop_none_fields(record)


def _merge_records(existing: dict | None, incoming: dict) -> dict:
    if not existing:
        return incoming

    merged = dict(existing)

    for field in [
        "name",
        "artist",
        "bpm",
        "energy",
        "valence",
        "danceability",
        "acousticness",
        "instrumentalness",
        "speechiness",
    ]:
        merged[field] = _pick_first(existing.get(field), incoming.get(field))

    existing_artists = existing.get("artists", []) or []
    incoming_artists = incoming.get("artists", []) or []
    merged["artists"] = _merge_labels(existing_artists, incoming_artists)

    existing_labels = existing.get("labels", []) or []
    incoming_labels = incoming.get("labels", []) or []
    merged["labels"] = _merge_labels(existing_labels, incoming_labels)

    existing_sources = existing.get("source_collections", []) or []
    incoming_sources = incoming.get("source_collections", []) or []
    merged["source_collections"] = _merge_labels(existing_sources, incoming_sources)

    merged["track_id"] = _pick_first(existing.get("track_id"), incoming.get("track_id"))
    merged["updated_at"] = datetime.now(UTC)

    return _drop_none_fields(merged)


def migrate():
    db = get_firestore_client()
    migrated = 0
    skipped_without_track_id = 0
    skipped_empty = 0

    print("=== DEBUG MIGRATION START ===")

    for collection_name in SOURCE_COLLECTIONS:
        print(f"\nProcesando colección: {collection_name}")
        sample_docs = list(db.collection_group(collection_name).limit(5).stream())
        print(f"Docs encontrados en {collection_name}: {len(sample_docs)}")

        for doc in sample_docs:
            data = doc.to_dict() or {}
            print(f" - path={doc.reference.path}")
            print(f"   doc.id={doc.id}")
            print(f"   keys={list(data.keys())[:10]}")

        docs = db.collection_group(collection_name).stream()

        for doc in docs:
            data = doc.to_dict() or {}
            incoming = _extract_track_record(doc.id, collection_name, data)

            if incoming is None:
                skipped_without_track_id += 1
                continue

            if not _is_meaningful_record(incoming):
                skipped_empty += 1
                continue

            track_id = incoming["track_id"]
            target_ref = db.collection(TARGET_COLLECTION).document(track_id)
            target_doc = target_ref.get()

            existing = target_doc.to_dict() if target_doc.exists else None
            merged = _merge_records(existing, incoming)

            if not _is_meaningful_record(merged):
                skipped_empty += 1
                continue

            target_ref.set(merged)
            migrated += 1

    print(f"\nMigración completada. Registros procesados: {migrated}")
    print(f"Saltados sin track_id real: {skipped_without_track_id}")
    print(f"Saltados por vacíos/inútiles: {skipped_empty}")


if __name__ == "__main__":
    migrate()
