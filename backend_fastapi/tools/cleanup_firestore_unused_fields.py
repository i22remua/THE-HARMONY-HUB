from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys

from firebase_admin import firestore

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.firestore_service import get_firestore_client


BATCH_SIZE = 200

COLLECTION_UNUSED_FIELDS: dict[str, tuple[str, ...]] = {
    "recommendations": (
        "spotify_playlist",
        "catalog_item_id",
        "catalog_noise_category",
    ),
    "generated_playlists": (
        "queries_used",
        "selected_tracks",
        "stress_band",
        "energy_band",
    ),
}


def _iter_docs(collection_name: str, batch_size: int = BATCH_SIZE):
    db = get_firestore_client()
    last_doc = None

    while True:
        query = db.collection(collection_name).order_by("__name__").limit(batch_size)
        if last_doc is not None:
            query = query.start_after(last_doc)

        docs = list(query.stream())
        if not docs:
            break

        for doc in docs:
            yield doc

        last_doc = docs[-1]


def _cleanup_unused_fields(collection_name: str, dry_run: bool) -> int:
    fields = COLLECTION_UNUSED_FIELDS.get(collection_name, ())
    if not fields:
        return 0

    db = get_firestore_client()
    batch = db.batch()
    pending = 0
    touched = 0

    for doc in _iter_docs(collection_name):
        data = doc.to_dict() or {}
        updates = {
            field_name: firestore.DELETE_FIELD
            for field_name in fields
            if field_name in data
        }

        if not updates:
            continue

        touched += 1
        if dry_run:
            continue

        batch.update(doc.reference, updates)
        pending += 1

        if pending >= BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            pending = 0

    if not dry_run and pending > 0:
        batch.commit()

    return touched


def _migrate_feedback_flags(dry_run: bool) -> int:
    db = get_firestore_client()
    batch = db.batch()
    pending = 0
    touched = 0

    for doc in _iter_docs("feedback"):
        data = doc.to_dict() or {}
        old_present = "has_encrypted_emotion_data" in data
        new_present = "has_encrypted_feedback_data" in data

        if not old_present and new_present:
            continue

        if not old_present and not new_present:
            continue

        updates = {}
        if old_present:
            updates["has_encrypted_feedback_data"] = bool(
                data.get("has_encrypted_emotion_data")
            )
            updates["has_encrypted_emotion_data"] = firestore.DELETE_FIELD

        touched += 1
        if dry_run:
            continue

        batch.update(doc.reference, updates)
        pending += 1

        if pending >= BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            pending = 0

    if not dry_run and pending > 0:
        batch.commit()

    return touched


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Elimina de Firestore campos ya no utilizados por el proyecto y "
            "migra nombres heredados de colecciones públicas."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica los cambios reales. Sin esta bandera, ejecuta un dry-run.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dry_run = not args.apply

    print("=== CLEANUP FIRESTORE UNUSED FIELDS ===")
    print(f"mode: {'DRY_RUN' if dry_run else 'APPLY'}")

    results: dict[str, int] = defaultdict(int)

    for collection_name in COLLECTION_UNUSED_FIELDS:
        touched = _cleanup_unused_fields(collection_name, dry_run=dry_run)
        results[collection_name] = touched
        print(f"[{collection_name}] docs tocados: {touched}")

    feedback_touched = _migrate_feedback_flags(dry_run=dry_run)
    results["feedback_flag_migration"] = feedback_touched
    print(f"[feedback_flag_migration] docs tocados: {feedback_touched}")

    total = sum(results.values())
    print(f"Total documentos afectados: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
