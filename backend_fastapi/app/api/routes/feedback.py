from datetime import datetime, UTC
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks
from google.cloud.firestore_v1.base_query import FieldFilter

from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.firestore_service import get_firestore_client
from app.services.adaptive_learning_service import update_mode_stats
from app.services.in_memory_store import feedback_store, recommendations_store
from app.services.ml_training_data_service import save_session_training_event
from app.services.session_mode_ml_automation_service import (
    run_session_mode_ml_maintenance,
)
from app.services.user_preference_learning_service import (
    update_user_generation_preferences,
)

router = APIRouter()


# -----------------------------------------------------------------------------
# INFERENCIA DINÁMICA DE GÉNEROS Y TARGETS
# -----------------------------------------------------------------------------
def _infer_genres_from_recommendation(recommendation_info: dict) -> list[str]:
    """
    Estima géneros base a partir del contexto recomendado, no de un catálogo fijo.
    """
    goal = recommendation_info.get("goal")
    vocal_preference = recommendation_info.get("vocal_preference")
    desired_outcome = recommendation_info.get("desired_outcome")

    if goal == "foco":
        genres = ["ambient", "classical", "acoustic"]
    elif goal == "relajacion":
        genres = ["ambient", "chill", "classical"]
    else:
        genres = ["pop", "dance", "edm"]
        if desired_outcome == "mas_ligero":
            genres = ["indie-pop", "pop", "acoustic"]

    if vocal_preference == "instrumental":
        genres = ["instrumental"] + [genre for genre in genres if genre != "instrumental"]

    return genres[:3]


def _label_to_numeric_targets(recommendation_info: dict) -> dict:
    """
    Convierte labels de recomendación en rasgos numéricos aproximados.

    Esto permite seguir aprendiendo gustos aunque la recomendación ya no venga
    de un modo predefinido del catálogo.
    """
    energy_map = {
        "baja": 0.28,
        "baja-media": 0.42,
        "media": 0.56,
        "media-alta": 0.72,
        "alta": 0.86,
    }
    valence_map = {
        "baja": 0.32,
        "neutral": 0.50,
        "neutral-positiva": 0.64,
        "positiva": 0.78,
    }

    goal = recommendation_info.get("goal")
    desired_outcome = recommendation_info.get("desired_outcome")
    target_energy_label = recommendation_info.get("target_energy")
    target_valence_label = recommendation_info.get("target_valence")

    energy = energy_map.get(str(target_energy_label), 0.60)
    valence = valence_map.get(str(target_valence_label), 0.60)

    if desired_outcome == "mas_calmado":
        danceability = 0.22
    elif desired_outcome == "mas_centrado":
        danceability = 0.25
    elif desired_outcome in {"mas_animado", "mas_despierto"}:
        danceability = 0.76
    elif desired_outcome == "mas_ligero":
        danceability = 0.46
    elif desired_outcome == "mas_acompanado":
        danceability = 0.40
    elif goal == "foco":
        danceability = 0.22
    elif goal == "relajacion":
        danceability = 0.20
    else:
        danceability = 0.70

    return {
        "valence": valence,
        "energy": energy,
        "danceability": danceability,
    }


def _find_recommendation_info(
    recommendation_id: str | None,
    recommendation_title: str,
) -> dict | None:
    """
    Busca en memoria la recomendación original asociada al feedback.

    Esto es esencial porque el feedback por sí solo no contiene todo el contexto.
    Necesitamos recuperar:
    - modo recomendado
    - tracks seleccionados
    - objetivo, mood, stress_level, etc.

    Así podemos cerrar el ciclo de aprendizaje.
    """
    for item in reversed(recommendations_store):
        if recommendation_id and item.get("recommendation_id") == recommendation_id:
            return item
        if item.get("title") == recommendation_title:
            return item

    try:
        db = get_firestore_client()
        recommendation_data: dict | None = None

        if recommendation_id:
            docs = (
                db.collection("recommendations")
                .where(filter=FieldFilter("recommendation_id", "==", recommendation_id))
                .limit(1)
                .stream()
            )
            for doc in docs:
                recommendation_data = doc.to_dict() or {}
                break
        else:
            docs = (
                db.collection("recommendations")
                .where(filter=FieldFilter("title", "==", recommendation_title))
                .limit(1)
                .stream()
            )
            for doc in docs:
                recommendation_data = doc.to_dict() or {}
                break

        if not recommendation_data:
            return None

        if recommendation_id:
            playlist_docs = (
                db.collection("generated_playlists")
                .where(filter=FieldFilter("recommendation_id", "==", recommendation_id))
                .limit(1)
                .stream()
            )
            for doc in playlist_docs:
                playlist_data = doc.to_dict() or {}
                if playlist_data.get("selected_tracks"):
                    recommendation_data["selected_tracks"] = playlist_data.get("selected_tracks")
                recommendation_data["generation_mode"] = playlist_data.get(
                    "generation_mode",
                    recommendation_data.get("generation_mode"),
                )
                recommendation_data["spotify_user_id"] = playlist_data.get(
                    "spotify_user_id",
                    recommendation_data.get("spotify_user_id"),
                )
                break

        return recommendation_data
    except Exception:
        return None
    return None


def _extract_track_ids(tracks: list[dict]) -> list[str]:
    """
    Extrae IDs únicos de canciones desde una lista de tracks.

    Se usa sobre todo para:
    - registrar exclusiones
    - asociar feedback a tracks concretos
    """
    ids: list[str] = []
    seen: set[str] = set()

    for track in tracks or []:
        track_id = track.get("id")
        if not track_id:
            continue
        track_id = str(track_id)
        if track_id in seen:
            continue
        seen.add(track_id)
        ids.append(track_id)

    return ids


def _infer_learning_mode(
    recommendation_info: dict | None,
    payload: FeedbackRequest,
) -> tuple[bool, str]:
    """
    Decide si este feedback debe usarse para actualizar el taste profile
    y con qué alcance.

    Devuelve:
    - use_for_taste_profile: bool
    - preference_scope: str

    Posibles scopes:
    - "session_only"
    - "stable_only"
    - "both"

    Lógica general:
    - si el usuario lo indica explícitamente, respetamos su decisión
    - en foco, relajación o estados vulnerables, preferimos aprender solo a
      nivel de sesión
    - en contextos más generales, permitimos aprendizaje estable
    """
    explicit_use = getattr(payload, "use_for_taste_profile", None)
    explicit_scope = getattr(payload, "preference_scope", None)

    if explicit_use is False:
        return False, "session_only"

    if explicit_use is True:
        if explicit_scope in {"both", "session_only", "stable_only"}:
            return True, explicit_scope
        return True, "both"

    if not recommendation_info:
        return True, "both"

    goal = recommendation_info.get("goal")
    mood = recommendation_info.get("mood")
    desired_outcome = recommendation_info.get("desired_outcome")

    if goal in {"foco", "relajacion"}:
        return False, "session_only"

    if mood in {"triste", "estresado", "cansado"} and desired_outcome:
        return False, "session_only"

    return True, "both"


@router.post("/", response_model=FeedbackResponse)
async def create_feedback(payload: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    ENDPOINT PRINCIPAL DE FEEDBACK.

    Este endpoint cierra el ciclo de aprendizaje del sistema.

    Flujo:
    1. recibe el feedback del usuario
    2. recupera la recomendación asociada
    3. decide cómo usar ese feedback para aprendizaje
    4. guarda el feedback
    5. actualiza estadísticas del modo recomendado
    6. actualiza preferencias del usuario
    7. genera ejemplos de entrenamiento por canción

    Este fichero es el puente entre:
    - uso real de la app
    - aprendizaje adaptativo
    - construcción del dataset para ML
    """
    recommendation_info = _find_recommendation_info(
        payload.recommendation_id,
        payload.recommendation_title,
    )
    use_for_taste_profile, preference_scope = _infer_learning_mode(
        recommendation_info,
        payload,
    )

    # -------------------------------------------------------------------------
    # 1) Guardar feedback mínimo en memoria
    # -------------------------------------------------------------------------
    item = {
        "id": str(uuid4()),
        "created_at": datetime.now(UTC),
        "recommendation_id": payload.recommendation_id,
        "helpful": payload.helpful,
        "effect": payload.effect,
        "post_session_state": payload.post_session_state,
        "comment": payload.comment,
        "recommendation_title": payload.recommendation_title,

        # Decisiones de aprendizaje asociadas a este feedback
        "use_for_taste_profile": use_for_taste_profile,
        "preference_scope": preference_scope,
    }
    feedback_store.append(item)

    # -------------------------------------------------------------------------
    # 2) Si encontramos la recomendación original, activamos el aprendizaje
    # -------------------------------------------------------------------------
    if recommendation_info:
        recommended_mode = recommendation_info.get("recommended_mode")
        user_id = (
            recommendation_info.get("user_id")
            or recommendation_info.get("spotify_user_id")
        )
        spotify_user_id = recommendation_info.get("spotify_user_id") or user_id
        selected_tracks = recommendation_info.get("selected_tracks", [])
        track_ids = _extract_track_ids(selected_tracks)

        # ---------------------------------------------------------------------
        # 3) Actualizar estadísticas del modo
        # ---------------------------------------------------------------------
        # Esto permite medir rendimiento agregado por modo:
        # ejemplo: cuántas veces "deep_focus" funciona bien.
        if recommended_mode:
            update_mode_stats(recommended_mode, payload.helpful)

        # ---------------------------------------------------------------------
        # 4) Actualizar el taste profile del usuario
        # ---------------------------------------------------------------------
        if spotify_user_id and recommended_mode:
            genres = _infer_genres_from_recommendation(recommendation_info)
            audio_targets = _label_to_numeric_targets(recommendation_info)

            update_user_generation_preferences(
                user_id=spotify_user_id,
                helpful=payload.helpful,
                genres=genres,
                valence=audio_targets["valence"],
                energy=audio_targets["energy"],
                danceability=audio_targets["danceability"],
                effect=payload.effect,
                use_for_taste_profile=use_for_taste_profile,
                preference_scope=preference_scope,
                recommendation_title=payload.recommendation_title,
                track_ids=track_ids,
                mood=recommendation_info.get("mood"),
            )

            # -----------------------------------------------------------------
            # 5) Construir contexto completo para entrenamiento
            # -----------------------------------------------------------------
            context = {
                "goal": recommendation_info.get("goal"),
                "mood": recommendation_info.get("mood"),
                "stress_level": recommendation_info.get("stress_level"),
                "energy_level": recommendation_info.get("energy_level"),
                "noise_category": recommendation_info.get("noise_category"),
                "use_environment": recommendation_info.get("use_environment", True),
                "vocal_preference": recommendation_info.get(
                    "vocal_preference",
                    "indistinto",
                ),
                "intensity_preference": recommendation_info.get(
                    "intensity_preference",
                    "media",
                ),
                "exploration_preference": recommendation_info.get(
                    "exploration_preference",
                    "equilibrado",
                ),
                "popularity_preference": recommendation_info.get(
                    "popularity_preference",
                    "mixta",
                ),
                "session_duration_min": recommendation_info.get(
                    "session_duration_min",
                    20,
                ),
                "desired_outcome": recommendation_info.get("desired_outcome"),
                "post_session_state": payload.post_session_state,
                "taste_profile_mode": recommendation_info.get("taste_profile_mode"),
                "use_for_taste_profile": use_for_taste_profile,
                "preference_scope": preference_scope,
            }

            # -----------------------------------------------------------------
            # 6) Guardar un training example por sesión
            # -----------------------------------------------------------------
            save_session_training_event(
                user_id=user_id,
                spotify_user_id=spotify_user_id,
                recommendation_id=payload.recommendation_id
                or recommendation_info.get("recommendation_id"),
                recommendation_title=payload.recommendation_title,
                recommended_mode=recommended_mode,
                helpful=payload.helpful,
                effect=payload.effect,
                post_session_state=payload.post_session_state,
                context=context,
                recommendation=recommendation_info,
                selected_tracks=selected_tracks,
            )
            background_tasks.add_task(run_session_mode_ml_maintenance)

    return item
