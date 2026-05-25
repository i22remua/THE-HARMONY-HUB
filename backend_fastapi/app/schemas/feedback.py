from datetime import datetime
from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    recommendation_id: str | None = None
    recommendation_title: str
    helpful: bool
    effect: str
    post_session_state: str
    comment: str | None = None

    # Nuevo: permite decidir si esta sesión debe influir
    # en el gusto estable o solo en el aprendizaje de sesión.
    use_for_taste_profile: bool | None = None
    preference_scope: str | None = None


class FeedbackResponse(BaseModel):
    id: str
    created_at: datetime
    recommendation_id: str | None = None
    helpful: bool
    effect: str
    post_session_state: str
    comment: str | None = None
    recommendation_title: str

    use_for_taste_profile: bool | None = None
    preference_scope: str | None = None
