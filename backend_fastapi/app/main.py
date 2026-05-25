from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.checkins import router as checkins_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.history import router as history_router
from app.api.routes.spotify import router as spotify_router

app = FastAPI(
    title="Harmony Hub API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
app.include_router(checkins_router, prefix="/checkins", tags=["checkins"])
app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
app.include_router(history_router, prefix="/history", tags=["history"])
app.include_router(spotify_router, prefix="/spotify", tags=["spotify"])


@app.get("/")
async def root():
    return {
        "message": "Harmony Hub API running",
        "docs": "/docs",
    }