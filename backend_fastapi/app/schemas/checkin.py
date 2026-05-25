from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MoodLabel = Literal["feliz", "neutral", "triste", "estresado", "cansado"]
GoalLabel = Literal["foco", "relajacion", "energia"]
NoiseCategory = Literal["quiet", "moderate", "active", "loud"]


class CheckinRequest(BaseModel):
    mood: MoodLabel
    goal: GoalLabel
    stress_level: int = Field(ge=1, le=5)
    energy_level: int = Field(ge=1, le=5)
    noise_category: NoiseCategory
    noise_db: float | None = None


class CheckinResponse(BaseModel):
    id: str
    created_at: datetime
    mood: MoodLabel
    goal: GoalLabel
    stress_level: int
    energy_level: int
    noise_category: NoiseCategory
    noise_db: float | None = None