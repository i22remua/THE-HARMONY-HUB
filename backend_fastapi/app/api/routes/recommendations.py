from uuid import uuid4

from fastapi import APIRouter

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.in_memory_store import recommendations_store
from app.services.recommender_service import generate_recommendation

router = APIRouter()


@router.post("/generate", response_model=RecommendationResponse)
async def create_recommendation(payload: RecommendationRequest):
    """
    Genera una recomendación de sesión y la deja trazada en memoria.

    Además de devolver la recomendación al cliente, aquí se crea el
    `recommendation_id` que luego conecta:
    - la pantalla de recomendación
    - la generación real de playlist en Spotify
    - el feedback
    - el dataset de entrenamiento del modelo de sesión
    """
    recommendation_id = str(uuid4())
    result = generate_recommendation(payload).model_copy(
        update={"recommendation_id": recommendation_id}
    )

    recommendations_store.append(
        {
            **result.model_dump(),
            "goal": payload.goal,
            "mood": payload.mood,
            "noise_category": payload.noise_category if payload.use_environment else None,
            "stress_level": payload.stress_level,
            "energy_level": payload.energy_level,
            "use_environment": payload.use_environment,
            "vocal_preference": payload.vocal_preference,
            "intensity_preference": payload.intensity_preference,
            "exploration_preference": payload.exploration_preference,
            "popularity_preference": payload.popularity_preference,
            "session_duration_min": payload.session_duration_min,
            "desired_outcome": payload.desired_outcome,
            "environment_context": (
                payload.environment_context if payload.use_environment else None
            ),
            "environment_variability": (
                payload.environment_variability if payload.use_environment else None
            ),
            "environment_peak_delta": (
                payload.environment_peak_delta if payload.use_environment else None
            ),
            "environment_confidence": (
                payload.environment_confidence if payload.use_environment else None
            ),
            "transient_ratio": (
                payload.transient_ratio if payload.use_environment else None
            ),
            "burst_count": payload.burst_count if payload.use_environment else None,
            "user_id": None,
            "spotify_user_id": payload.spotify_user_id,
            "selected_tracks": [],
            "inferred_keywords": [
                payload.goal,
                payload.noise_category,
                payload.mood,
            ],
        }
    )

    return result
