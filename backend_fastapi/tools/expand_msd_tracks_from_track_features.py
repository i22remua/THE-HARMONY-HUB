from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import MSD_CATALOG_PATH, MSD_TRACKS_COLLECTION
from app.services.catalog_bootstrap_service import build_bootstrap_catalog_track
from app.services.firestore_service import get_firestore_client
from app.services.msd_catalog_service import (
    load_catalog_tracks,
    normalize_text,
)


TRACK_FEATURES_COLLECTION = "track_features"
def _identity_key(track: dict[str, Any]) -> str:
    title = normalize_text(track.get("name") or track.get("title"))
    artists = track.get("artists", []) or []
    artist = normalize_text(track.get("artist_name") or (artists[0] if artists else ""))
    return f"{title}::{artist}"


def _load_existing_catalog_sets() -> tuple[set[str], set[str]]:
    merged = load_catalog_tracks(limit=None)
    ids = {
        str(track.get("catalog_track_id")).strip()
        for track in merged
        if str(track.get("catalog_track_id") or "").strip()
    }
    identities = {_identity_key(track) for track in merged}
    return ids, identities


def _iter_track_features(limit: int = 0):
    db = get_firestore_client()
    stream = db.collection(TRACK_FEATURES_COLLECTION).stream()
    for index, doc in enumerate(stream, start=1):
        if limit and index > limit:
            break
        yield doc.to_dict() or {}


def _append_jsonl(path: Path, tracks: list[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        for track in tracks:
            fh.write(json.dumps(track, ensure_ascii=False) + "\n")


def _write_firestore(collection_name: str, tracks: list[dict[str, Any]]) -> int:
    if not tracks:
        return 0

    db = get_firestore_client()
    batch = db.batch()
    written = 0
    for track in tracks:
        doc_id = str(track.get("catalog_track_id"))
        batch.set(
            db.collection(collection_name).document(doc_id),
            track,
            merge=True,
        )
        written += 1
        if written % 400 == 0:
            batch.commit()
            batch = db.batch()

    if written % 400 != 0:
        batch.commit()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Amplia msd_tracks a partir de track_features observadas.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Máximo de docs de track_features a revisar")
    parser.add_argument("--write-local", action="store_true", help="Añade las nuevas entradas al JSONL local")
    parser.add_argument("--write-firestore", action="store_true", help="Escribe las nuevas entradas en la colección msd_tracks")
    parser.add_argument("--jsonl-path", default=MSD_CATALOG_PATH, help="Ruta del JSONL local a ampliar")
    parser.add_argument("--collection", default=MSD_TRACKS_COLLECTION, help="Colección Firestore destino")
    args = parser.parse_args()

    existing_ids, existing_identities = _load_existing_catalog_sets()
    generated: list[dict[str, Any]] = []
    skipped_existing = 0
    skipped_invalid = 0

    for raw_track in _iter_track_features(limit=args.limit):
        candidate = build_bootstrap_catalog_track(
            raw_track,
            source="track_features_bootstrap",
        )
        if candidate is None:
            skipped_invalid += 1
            continue

        catalog_id = str(candidate.get("catalog_track_id") or "").strip()
        identity = _identity_key(candidate)
        if catalog_id in existing_ids or identity in existing_identities:
            skipped_existing += 1
            continue

        existing_ids.add(catalog_id)
        existing_identities.add(identity)
        generated.append(candidate)

    print(
        "Bootstrap candidates generated:",
        len(generated),
        "| skipped_existing:",
        skipped_existing,
        "| skipped_invalid:",
        skipped_invalid,
    )

    if args.write_local:
        jsonl_path = Path(args.jsonl_path)
        _append_jsonl(jsonl_path, generated)
        print(f"Appended to local catalog: {jsonl_path} | tracks={len(generated)}")

    if args.write_firestore:
        written = _write_firestore(args.collection, generated)
        print(f"Written to Firestore collection '{args.collection}': {written}")


if __name__ == "__main__":
    main()
