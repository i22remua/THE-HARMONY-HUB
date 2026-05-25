from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter

from app.schemas.checkin import CheckinRequest, CheckinResponse
from app.services.in_memory_store import checkins_store

router = APIRouter()


@router.post("/", response_model=CheckinResponse)
async def create_checkin(payload: CheckinRequest):
    """
    Registra el check-in operativo mínimo de la sesión actual.

    Este endpoint guarda el contexto base que el usuario declara antes de pedir
    una recomendación: estado emocional, objetivo, energía, estrés y ruido.
    """
    item = {
        "id": str(uuid4()),
        "created_at": datetime.now(UTC),
        "mood": payload.mood,
        "goal": payload.goal,
        "stress_level": payload.stress_level,
        "energy_level": payload.energy_level,
        "noise_category": payload.noise_category,
        "noise_db": payload.noise_db,
    }
    checkins_store.append(item)
    return item
