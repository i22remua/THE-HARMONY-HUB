from pathlib import Path
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tools.reset_user_learning_data import delete_collection

# Colecciones necesarias para reiniciar el ciclo del modelo de sesión desde cero.
ML_COLLECTIONS_TO_CLEAR = [
    "feedback",
    "feedback_private",
    "training_session_examples",
    "user_generation_preferences",
    "adaptive_mode_stats",
    "checkins",
    "checkins_private",
    "recommendations",
    "generated_playlists",
]

MODEL_ARTIFACTS = [
    Path("app/ml/models/session_mode_model.joblib"),
    Path("app/ml/models/session_mode_model_metadata.json"),
]


def main() -> None:
    print("=== RESET SESSION MODE ML PIPELINE START ===")
    total_deleted = 0

    for collection_name in ML_COLLECTIONS_TO_CLEAR:
        print(f"\nLimpiando colección: {collection_name}")
        deleted = delete_collection(collection_name)
        total_deleted += deleted
        print(f"Total borrados en {collection_name}: {deleted}")

    print("\nEliminando artefactos locales del modelo:")
    for artifact_path in MODEL_ARTIFACTS:
        if artifact_path.exists():
            artifact_path.unlink()
            print(f"[deleted] {artifact_path}")
        else:
            print(f"[missing] {artifact_path}")

    print("\n=== RESET SESSION MODE ML PIPELINE END ===")
    print(f"Total global borrado en Firestore: {total_deleted}")
    print(
        "Recuerda reiniciar el backend si quieres limpiar también el estado en "
        "memoria (recommendations_store, feedback_store, checkins_store)."
    )


if __name__ == "__main__":
    main()
