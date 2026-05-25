from app.services.firestore_service import get_firestore_client

COLLECTION_NAME = "adaptive_mode_stats"


def get_mode_stats(recommended_mode: str) -> dict:
    # Esta capa mantiene un historial ligero por modo para ajustes rápidos de
    # preferencia, independiente del dataset supervisado más rico del ML.
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(recommended_mode)
    snapshot = doc_ref.get()

    if not snapshot.exists:
        return {
            "helpful_count": 0,
            "not_helpful_count": 0,
        }

    data = snapshot.to_dict() or {}
    return {
        "helpful_count": data.get("helpful_count", 0),
        "not_helpful_count": data.get("not_helpful_count", 0),
    }


def update_mode_stats(recommended_mode: str, helpful: bool) -> None:
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(recommended_mode)

    stats = get_mode_stats(recommended_mode)

    # Acumulamos evidencia binaria simple: útil / no útil para este modo.
    # Sirve como memoria operativa rápida incluso cuando el clasificador global
    # todavía no tiene masa crítica suficiente para activarse.
    if helpful:
        stats["helpful_count"] += 1
    else:
        stats["not_helpful_count"] += 1

    doc_ref.set(
        {
            "recommended_mode": recommended_mode,
            "helpful_count": stats["helpful_count"],
            "not_helpful_count": stats["not_helpful_count"],
        },
        merge=True,
    )


def get_feedback_bonus(recommended_mode: str) -> int:
    stats = get_mode_stats(recommended_mode) 
    helpful = stats.get("helpful_count", 0)
    not_helpful = stats.get("not_helpful_count", 0)

    # Convertimos la memoria binaria acumulada a un bonus lineal pequeño que
    # puede inclinar heurísticas sin reemplazar la decisión principal.
    return (helpful * 3) - (not_helpful * 3) 
