from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys

from google.cloud.firestore_v1.base_query import FieldFilter

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.firestore_service import get_firestore_client


FIREBASE_USER_COLLECTION = "users"
LEARNING_PROFILE_COLLECTION = "user_generation_preferences"

FIREBASE_UID_COLLECTIONS = [
    "checkins",
    "checkins_private",
    "feedback",
    "feedback_private",
    "recommendations",
    "generated_playlists",
    "saved_preset_modes",
]

SPOTIFY_USER_COLLECTIONS = [
    "generated_playlists",
    "training_session_examples",
]

BATCH_SIZE = 200


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _resolve_uid_by_email(email: str) -> str | None:
    db = get_firestore_client()
    normalized = _normalize_email(email)
    query = (
        db.collection(FIREBASE_USER_COLLECTION)
        .where(filter=FieldFilter("email_normalized", "==", normalized))
        .limit(1)
    )
    docs = list(query.stream())
    if not docs:
        fallback = (
            db.collection(FIREBASE_USER_COLLECTION)
            .where(filter=FieldFilter("email", "==", email.strip()))
            .limit(1)
        )
        docs = list(fallback.stream())
    if not docs:
        return None
    return docs[0].id


def _delete_query_docs(
    *,
    collection_name: str,
    field_name: str,
    field_value: str,
    dry_run: bool,
    batch_size: int = BATCH_SIZE,
) -> int:
    db = get_firestore_client()
    deleted = 0

    while True:
        docs = list(
            db.collection(collection_name)
            .where(filter=FieldFilter(field_name, "==", field_value))
            .limit(batch_size)
            .stream()
        )
        if not docs:
            break

        if dry_run:
            deleted += len(docs)
            break

        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()
        deleted += len(docs)

    return deleted


def _delete_doc_if_exists(collection_name: str, document_id: str, dry_run: bool) -> int:
    db = get_firestore_client()
    doc_ref = db.collection(collection_name).document(document_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        return 0
    if dry_run:
        return 1
    doc_ref.delete()
    return 1


def reset_profile(
    *,
    firebase_uid: str | None,
    spotify_user_id: str | None,
    dry_run: bool,
) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)

    if firebase_uid:
        for collection_name in FIREBASE_UID_COLLECTIONS:
            counts[collection_name] += _delete_query_docs(
                collection_name=collection_name,
                field_name="user_id",
                field_value=firebase_uid,
                dry_run=dry_run,
            )

    if spotify_user_id:
        counts[LEARNING_PROFILE_COLLECTION] += _delete_doc_if_exists(
            LEARNING_PROFILE_COLLECTION,
            spotify_user_id,
            dry_run,
        )
        for collection_name in SPOTIFY_USER_COLLECTIONS:
            counts[collection_name] += _delete_query_docs(
                collection_name=collection_name,
                field_name="spotify_user_id",
                field_value=spotify_user_id,
                dry_run=dry_run,
            )

    return dict(counts)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resetea el historial y el aprendizaje de perfiles concretos sin "
            "borrar todo Firestore."
        )
    )
    parser.add_argument(
        "--email",
        action="append",
        default=[],
        help="Email de la cuenta Firebase del perfil. Puede repetirse.",
    )
    parser.add_argument(
        "--firebase-uid",
        action="append",
        default=[],
        help="UID Firebase si ya lo conoces. Puede repetirse.",
    )
    parser.add_argument(
        "--spotify-user",
        action="append",
        default=[],
        help="spotify_user_id exacto del perfil. Puede repetirse.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ejecuta el borrado real. Sin esto solo hace dry-run.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dry_run = not args.apply

    resolved_uids = list(args.firebase_uid)
    for email in args.email:
        uid = _resolve_uid_by_email(email)
        print(f"[resolve] {email} -> {uid or 'NOT_FOUND'}")
        if uid:
            resolved_uids.append(uid)

    firebase_uids = list(dict.fromkeys(uid for uid in resolved_uids if uid))
    spotify_user_ids = list(
        dict.fromkeys(user_id.strip() for user_id in args.spotify_user if user_id.strip())
    )

    if not firebase_uids and not spotify_user_ids:
        raise SystemExit(
            "Debes indicar al menos un --email, --firebase-uid o --spotify-user."
        )

    print("=== RESET TARGET PROFILES ===")
    print(f"mode: {'DRY_RUN' if dry_run else 'APPLY'}")
    print(f"firebase_uids: {firebase_uids}")
    print(f"spotify_user_ids: {spotify_user_ids}")

    total_counts: dict[str, int] = defaultdict(int)

    for firebase_uid in firebase_uids:
        counts = reset_profile(
            firebase_uid=firebase_uid,
            spotify_user_id=None,
            dry_run=dry_run,
        )
        print(f"\n[firebase_uid={firebase_uid}]")
        for key, value in sorted(counts.items()):
            print(f"  - {key}: {value}")
            total_counts[key] += value

    for spotify_user_id in spotify_user_ids:
        counts = reset_profile(
            firebase_uid=None,
            spotify_user_id=spotify_user_id,
            dry_run=dry_run,
        )
        print(f"\n[spotify_user_id={spotify_user_id}]")
        for key, value in sorted(counts.items()):
            print(f"  - {key}: {value}")
            total_counts[key] += value

    print("\n=== TOTAL ===")
    for key, value in sorted(total_counts.items()):
        print(f"  - {key}: {value}")

    if dry_run:
        print("\nNo se ha borrado nada. Vuelve a ejecutar con --apply para confirmar.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
