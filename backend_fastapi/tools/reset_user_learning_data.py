from pathlib import Path
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.firestore_service import get_firestore_client

# Colecciones que sí quieres limpiar para ver el aprendizaje desde cero
COLLECTIONS_TO_CLEAR = [
    "feedback",
    "feedback_private",
    "training_examples",
    "training_session_examples",
    "user_generation_preferences",
    "checkins",
    "checkins_private",
    "recommendations",
    "generated_playlists",
    # "track_features",  # descomenta esto si también quieres borrarla
]

BATCH_SIZE = 200


def delete_collection(collection_name: str, batch_size: int = BATCH_SIZE) -> int:
    db = get_firestore_client()
    total_deleted = 0

    while True:
        docs = list(db.collection(collection_name).limit(batch_size).stream())
        if not docs:
            break

        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)

        batch.commit()
        total_deleted += len(docs)
        print(f"[{collection_name}] borrados {len(docs)} docs en este lote...")

    return total_deleted


def main():
    print("=== RESET FIRESTORE DATA START ===")
    grand_total = 0

    for collection_name in COLLECTIONS_TO_CLEAR:
        print(f"\nLimpiando colección: {collection_name}")
        deleted = delete_collection(collection_name)
        grand_total += deleted
        print(f"Total borrados en {collection_name}: {deleted}")

    print("\n=== RESET FIRESTORE DATA END ===")
    print(f"Total global borrado: {grand_total}")


if __name__ == "__main__":
    main()
