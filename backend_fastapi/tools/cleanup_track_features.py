from pathlib import Path
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.firestore_service import get_firestore_client

TARGET_COLLECTION = "track_features"


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return len(value) == 0
    return False


def should_delete(doc_id: str, data: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    track_id = data.get("track_id")
    name = data.get("name")
    artist = data.get("artist")
    artists = data.get("artists") or []

    bpm = data.get("bpm")
    energy = data.get("energy")
    valence = data.get("valence")
    danceability = data.get("danceability")
    acousticness = data.get("acousticness")
    instrumentalness = data.get("instrumentalness")
    speechiness = data.get("speechiness")

    has_identity = not _is_empty(track_id) and (
        not _is_empty(name) or not _is_empty(artist) or len(artists) > 0
    )

    has_features = any(
        value is not None
        for value in [
            bpm,
            energy,
            valence,
            danceability,
            acousticness,
            instrumentalness,
            speechiness,
        ]
    )

    if _is_empty(name):
        reasons.append("missing_name")
    if _is_empty(artist) and len(artists) == 0:
        reasons.append("missing_artist")
    if not has_identity:
        reasons.append("weak_identity")
    if not has_features:
        reasons.append("no_features")

    delete_it = (not has_identity) or (not has_features)
    return delete_it, reasons


def cleanup(dry_run: bool = True):
    db = get_firestore_client()
    docs = db.collection(TARGET_COLLECTION).stream()

    total = 0
    to_delete = 0

    for doc in docs:
        total += 1
        data = doc.to_dict() or {}
        delete_it, reasons = should_delete(doc.id, data)

        if not delete_it:
            continue

        to_delete += 1
        print(f"DELETE {doc.id} | reasons={reasons}")

        if not dry_run:
            db.collection(TARGET_COLLECTION).document(doc.id).delete()

    print(f"Total revisados: {total}")
    print(f"Total a borrar: {to_delete}")
    print(f"Dry run: {dry_run}")


if __name__ == "__main__":
    cleanup(dry_run=False)
