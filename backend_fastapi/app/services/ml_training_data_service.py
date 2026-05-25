from datetime import UTC, datetime
from uuid import uuid4

from app.services.firestore_service import get_firestore_client

# Dataset supervisado a nivel de sesión: contexto + modo + resumen de playlist + feedback.
COLLECTION_NAME = "training_session_examples"


def _safe_float(value) -> float | None:
    """
    Convierte valores numéricos opcionales a float sin interrumpir el guardado.
    """
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _average_track_value(tracks: list[dict], field: str) -> float | None:
    """
    Resume una playlist calculando la media de un campo numérico por track.

    Esto permite guardar señales agregadas de la sesión sin depender de
    entrenar a nivel de canción.
    """
    values = [
        value
        for value in (_safe_float(track.get(field)) for track in tracks or [])
        if value is not None
    ]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _explicit_ratio(tracks: list[dict]) -> float | None:
    """
    Calcula el porcentaje de canciones explícitas dentro de la sesión final.
    """
    if not tracks:
        return None
    explicit_count = sum(1 for track in tracks if bool(track.get("explicit", False)))
    return round(explicit_count / len(tracks), 4)


def save_session_training_event(
    *,
    user_id: str | None,
    spotify_user_id: str | None,
    recommendation_id: str | None,
    recommendation_title: str,
    recommended_mode: str,
    helpful: bool | None,
    effect: str | None,
    post_session_state: str | None,
    context: dict,
    recommendation: dict,
    selected_tracks: list[dict],
) -> None:
    """
    Guarda un ejemplo de entrenamiento a nivel de sesión.

    El modelo aprende qué modo funciona mejor para un contexto concreto, no qué
    canción concreta fue buena o mala cuando solo existe feedback global.
    """
    db = get_firestore_client()

    # El documento mezcla tres capas:
    # - contexto declarado por el usuario
    # - modo/decisión producida por el recomendador
    # - resumen agregado de la playlist realmente entregada
    #
    # Así el entrenamiento puede aprender "qué tipo de sesión funcionó" sin
    # depender de que exista feedback explícito por canción individual.
    item = {
        "id": str(uuid4()),
        "created_at": datetime.now(UTC),
        "user_id": user_id,
        "spotify_user_id": spotify_user_id,
        "recommendation_id": recommendation_id,
        "recommendation_title": recommendation_title,
        "recommended_mode": recommended_mode,
        "generation_mode": recommendation.get("generation_mode"),
        "helpful": helpful,
        "effect": effect,
        "post_session_state": post_session_state,
        "goal": context.get("goal"),
        "mood": context.get("mood"),
        "stress_level": context.get("stress_level"),
        "energy_level": context.get("energy_level"),
        "noise_category": context.get("noise_category"),
        "use_environment": context.get("use_environment"),
        "vocal_preference": context.get("vocal_preference"),
        "intensity_preference": context.get("intensity_preference"),
        "exploration_preference": context.get("exploration_preference"),
        "popularity_preference": context.get("popularity_preference"),
        "session_duration_min": context.get("session_duration_min"),
        "desired_outcome": context.get("desired_outcome"),
        "catalog_item_id": recommendation.get("catalog_item_id"),
        "catalog_noise_category": recommendation.get("catalog_noise_category"),
        "target_bpm_range": recommendation.get("target_bpm_range"),
        "target_energy": recommendation.get("target_energy"),
        "target_valence": recommendation.get("target_valence"),
        "selection_source": recommendation.get("selection_source"),
        "mode_ml_probability": recommendation.get("mode_ml_probability"),
        # A nivel supervisado no guardamos toda la playlist cruda: nos basta
        # con señales resumidas que describen el resultado final de la sesión.
        "selected_tracks_count": len(selected_tracks or []),
        "avg_track_popularity": _average_track_value(selected_tracks, "popularity"),
        "avg_track_bpm": _average_track_value(selected_tracks, "bpm"),
        "avg_track_energy": _average_track_value(selected_tracks, "energy_feature"),
        "avg_track_valence": _average_track_value(selected_tracks, "valence_feature"),
        "avg_track_danceability": _average_track_value(selected_tracks, "danceability"),
        "avg_track_instrumentalness": _average_track_value(
            selected_tracks,
            "instrumentalness",
        ),
        "explicit_ratio": _explicit_ratio(selected_tracks),
    }

    db.collection(COLLECTION_NAME).document(item["id"]).set(item)
