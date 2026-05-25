import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _resolve_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((BACKEND_ROOT / path).resolve())


def _get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except Exception:
        return default

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "harmonyhub://spotify-auth/callback")
SPOTIFY_SCOPES = os.getenv(
    "SPOTIFY_SCOPES",
    "user-read-private user-read-email playlist-read-private playlist-read-collaborative user-top-read playlist-modify-public playlist-modify-private",
)

FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    _resolve_path("firebase-service-account.json"),
)
FIREBASE_SERVICE_ACCOUNT_PATH = _resolve_path(FIREBASE_SERVICE_ACCOUNT_PATH)

MSD_CATALOG_PATH = os.getenv(
    "MSD_CATALOG_PATH",
    _resolve_path("app/data/msd_tracks.jsonl"),
)
MSD_CATALOG_PATH = _resolve_path(MSD_CATALOG_PATH)

MSD_TRACKS_COLLECTION = os.getenv(
    "MSD_TRACKS_COLLECTION",
    "msd_tracks",
)

MSD_MATCH_CACHE_COLLECTION = os.getenv(
    "MSD_MATCH_CACHE_COLLECTION",
    "msd_spotify_matches",
)

SESSION_MODE_MIN_SELECTED_PROBABILITY = _get_float_env(
    "SESSION_MODE_MIN_SELECTED_PROBABILITY",
    0.14,
)
