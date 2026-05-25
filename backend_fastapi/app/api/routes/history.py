from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.firestore_service import get_firestore_client

router = APIRouter()

PUBLIC_COLLECTIONS = (
    "checkins",
    "recommendations",
    "feedback",
    "generated_playlists",
)


def _serialize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value


def _fetch_history_slice(collection_name: str, user_id: str, limit: int) -> list[dict]:
    db = get_firestore_client()
    docs = (
        db.collection(collection_name)
        .where(filter=FieldFilter("user_id", "==", user_id))
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    items: list[dict] = []
    for doc in docs:
        data = doc.to_dict() or {}
        items.append(
            {
                "id": doc.id,
                **_serialize_value(data),
            }
        )
    return items


def _count_collection(collection_name: str, user_id: str) -> int:
    db = get_firestore_client()
    return sum(
        1
        for _ in db.collection(collection_name)
        .where(filter=FieldFilter("user_id", "==", user_id))
        .stream()
    )


@router.get("/me")
async def get_history(
    user_id: str = Query(..., description="Firebase uid del usuario"),
    limit: int = Query(10, ge=1, le=50, description="Máximo por colección"),
):
    """
    Devuelve el historial persistido real del usuario desde Firestore.

    Notas:
    - usa `user_id` de Firebase porque es el único identificador compartido por
      check-ins, recomendaciones, feedback y playlists generadas
    - expone solo las colecciones públicas; los bloques privados cifrados se
      siguen resolviendo del lado cliente
    """
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise HTTPException(status_code=400, detail="user_id no puede estar vacío")

    try:
        totals = {
            "checkins": _count_collection("checkins", normalized_user_id),
            "recommendations": _count_collection("recommendations", normalized_user_id),
            "feedback": _count_collection("feedback", normalized_user_id),
            "generated_playlists": _count_collection(
                "generated_playlists",
                normalized_user_id,
            ),
        }

        history = {
            collection: _fetch_history_slice(collection, normalized_user_id, limit)
            for collection in PUBLIC_COLLECTIONS
        }

        return {
            "user_id": normalized_user_id,
            "limit_per_collection": limit,
            "collections_are_public_only": True,
            "totals": totals,
            "checkins": history["checkins"],
            "recommendations": history["recommendations"],
            "feedback": history["feedback"],
            "generated_playlists": history["generated_playlists"],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo recuperar el historial persistido: {exc}",
        ) from exc
