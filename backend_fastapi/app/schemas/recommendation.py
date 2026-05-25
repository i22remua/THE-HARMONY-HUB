from typing import Literal

from pydantic import BaseModel, Field


MoodLabel = Literal["feliz", "neutral", "triste", "estresado", "cansado"]
GoalLabel = Literal["foco", "relajacion", "energia"]
NoiseCategory = Literal["quiet", "moderate", "active", "loud"]


class RecommendationRequest(BaseModel):
    mood: MoodLabel
    goal: GoalLabel
    spotify_user_id: str | None = None
    stress_level: int = Field(ge=1, le=5)
    energy_level: int = Field(ge=1, le=5)
    noise_category: NoiseCategory
    use_environment: bool = True
    vocal_preference: str = "indistinto"
    intensity_preference: str = "media"
    exploration_preference: str = "equilibrado"
    popularity_preference: str = "mixta"
    session_duration_min: int = Field(default=20, ge=5, le=240)
    desired_outcome: str | None = None
    environment_context: str | None = None
    environment_variability: float | None = None
    environment_peak_delta: float | None = None
    environment_confidence: float | None = None
    transient_ratio: float | None = None
    burst_count: int | None = None


class RecommendationResponse(BaseModel):
    recommendation_id: str | None = None
    title: str
    description: str
    recommended_mode: str
    target_bpm_range: str
    target_energy: str
    target_valence: str
    spotify_playlist: str | None = None
    catalog_item_id: str | None = None
    catalog_noise_category: str | None = None
    ml_enabled: bool = False
    mode_ml_probability: float | None = None
    selection_source: str = "heuristic"
    feedback_count: int = 0
    session_taste_weight: float = 0.0
    stable_taste_weight: float = 0.0
    taste_profile_mode: str = "session_weighted"
    ml_explanation: dict | None = None
    model_card_summary: dict | None = None
