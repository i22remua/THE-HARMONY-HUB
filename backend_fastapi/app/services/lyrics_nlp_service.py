from __future__ import annotations

"""
Capas ligeras de NLP para letras y texto musical.

El servicio combina dos estrategias:

- si el entorno dispone de modelos externos, intenta usarlos
- si no, cae a heurísticas deterministas y embeddings hash

El objetivo no es hacer análisis lingüístico profundo, sino aportar señales
semánticas robustas para el ranking musical sin romper el backend cuando faltan
dependencias pesadas.
"""

import math
import os
import re
from functools import lru_cache
from typing import Any

from sklearn.feature_extraction.text import HashingVectorizer

_HASHING_DIM = int(os.getenv("TEXT_EMBEDDING_DIM", "256"))

_hashing_vectorizer = HashingVectorizer( #esto es un vectorizador de texto que convierte texto en vectores numéricos utilizando una función de hash. Es útil para manejar grandes vocabularios sin necesidad de almacenar un diccionario explícito. por ejemplo en la app de recomendación de música, se puede usar para convertir las letras de las canciones en vectores numéricos que luego se pueden comparar para encontrar similitudes entre canciones.
    n_features=_HASHING_DIM,
    alternate_sign=False,
    norm=None,
    lowercase=True,
)

_SENTENCE_MODEL = None
_SENTENCE_MODEL_READY = None
_EMOTION_PIPELINE = None
_EMOTION_PIPELINE_READY = None


DOMAIN_LEXICONS: dict[str, set[str]] = {
    "calm": {
        "calm",
        "peace",
        "peaceful",
        "soft",
        "breathe",
        "breathing",
        "still",
        "quiet",
        "gentle",
        "slow",
        "rest",
        "restful",
        "relax",
        "relaxing",
        "serene",
        "ambient",
        "dream",
        "safe",
        "soothe",
    },
    "focus": {
        "focus",
        "clarity",
        "clear",
        "steady",
        "deep",
        "study",
        "concentrate",
        "attention",
        "minimal",
        "instrumental",
        "precision",
        "flow",
    },
    "uplift": {
        "rise",
        "light",
        "bright",
        "up",
        "move",
        "alive",
        "hope",
        "free",
        "better",
        "smile",
        "dance",
        "energy",
        "strong",
        "sun",
        "upbeat",
        "motivation",
        "joy",
    },
    "warmth": {
        "warm",
        "hold",
        "home",
        "comfort",
        "close",
        "together",
        "care",
        "heart",
        "gentle",
        "support",
        "tender",
        "acoustic",
    },
    "tension": {
        "burn",
        "fight",
        "fear",
        "panic",
        "rage",
        "hard",
        "dark",
        "pressure",
        "storm",
        "broken",
        "restless",
        "angry",
        "chaos",
        "trap",
        "club",
    },
    "sadness": {
        "sad",
        "alone",
        "lonely",
        "cry",
        "tears",
        "lost",
        "empty",
        "falling",
        "gone",
        "hurt",
        "pain",
        "cold",
        "goodbye",
        "miss",
    },
}


def _tokenize(text: str) -> list[str]:
    """Tokenización mínima y estable para español/inglés sin dependencias extra."""
    return re.findall(r"[a-záéíóúñü']+", text.lower())


def _normalize_embedding(vector: list[float]) -> list[float]:
    """Normaliza un embedding a norma L2 para poder compararlo con coseno."""
    norm = math.sqrt(sum(v * v for v in vector))
    if norm <= 1e-12:
        return vector
    return [v / norm for v in vector]


def _try_load_sentence_transformer():
    """Carga perezosa del modelo de embeddings para no penalizar el arranque."""
    global _SENTENCE_MODEL, _SENTENCE_MODEL_READY

    if _SENTENCE_MODEL_READY is not None:
        return

    model_name = os.getenv(
        "TEXT_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    )

    try:
        from sentence_transformers import SentenceTransformer

        _SENTENCE_MODEL = SentenceTransformer(model_name)
        _SENTENCE_MODEL_READY = True
    except Exception:
        _SENTENCE_MODEL = None
        _SENTENCE_MODEL_READY = False


def _try_load_emotion_pipeline():
    """Carga perezosa del clasificador emocional si está disponible."""
    global _EMOTION_PIPELINE, _EMOTION_PIPELINE_READY

    if _EMOTION_PIPELINE_READY is not None:
        return

    model_name = os.getenv(
        "TEXT_EMOTION_MODEL",
        "j-hartmann/emotion-english-distilroberta-base",
    )

    try:
        from transformers import pipeline

        _EMOTION_PIPELINE = pipeline(
            "text-classification",
            model=model_name,
            top_k=None,
        )
        _EMOTION_PIPELINE_READY = True
    except Exception:
        _EMOTION_PIPELINE = None
        _EMOTION_PIPELINE_READY = False


def embed_text(text: str) -> list[float]:
    """
    Devuelve un embedding del texto.

    Prioriza `sentence-transformers` si puede cargarse; en caso contrario usa un
    `HashingVectorizer` normalizado, lo que mantiene una representación
    reproducible incluso en entornos ligeros.
    """
    text = (text or "").strip()
    if not text:
        return [0.0] * _HASHING_DIM

    _try_load_sentence_transformer()

    if _SENTENCE_MODEL_READY and _SENTENCE_MODEL is not None:
        try:
            vector = _SENTENCE_MODEL.encode(text, normalize_embeddings=True)
            return [float(x) for x in vector.tolist()]
        except Exception:
            pass

    hashed = _hashing_vectorizer.transform([text]).toarray()[0].tolist()
    return _normalize_embedding([float(x) for x in hashed])


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Similitud coseno segura para embeddings de igual dimensión."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 <= 1e-12 or norm2 <= 1e-12:
        return 0.0

    return dot / (norm1 * norm2)


def _heuristic_domain_profile(text: str) -> dict[str, float]:
    """
    Estima un perfil semántico de dominio a partir de lexicones manuales.

    Esta capa sirve como fallback explicable cuando no hay pipeline emocional
    disponible.
    """
    tokens = _tokenize(text)

    if not tokens:
        return {
            "calm": 0.0,
            "focus": 0.0,
            "uplift": 0.0,
            "warmth": 0.0,
            "tension": 0.0,
            "sadness": 0.0,
        }

    total = max(len(tokens), 1)
    profile: dict[str, float] = {}

    for domain, lexicon in DOMAIN_LEXICONS.items():
        hits = sum(1 for token in tokens if token in lexicon)
        profile[domain] = round(min(hits / max(total / 4, 1), 1.0), 4)

    return profile


def _heuristic_emotion_scores(text: str) -> dict[str, float]:
    """Proyecta el perfil heurístico a emociones básicas comparables."""
    domain = _heuristic_domain_profile(text)

    joy = min(1.0, domain["uplift"] * 0.75 + domain["warmth"] * 0.25)
    sadness = min(1.0, domain["sadness"])
    fear = min(1.0, domain["tension"] * 0.55)
    anger = min(1.0, domain["tension"] * 0.80)
    neutral = max(
        0.0,
        1.0 - min(1.0, joy * 0.40 + sadness * 0.45 + anger * 0.35 + fear * 0.25),
    )

    return {
        "joy": round(joy, 4),
        "sadness": round(sadness, 4),
        "fear": round(fear, 4),
        "anger": round(anger, 4),
        "neutral": round(neutral, 4),
    }


def _map_pipeline_emotions_to_domain(model_scores: dict[str, float]) -> dict[str, float]:
    """
    Reexpresa emociones básicas del modelo en dimensiones útiles para Harmony Hub.

    El ranking musical trabaja mejor con señales como `calm`, `warmth` o
    `tension` que con etiquetas emocionales puras.
    """
    joy = model_scores.get("joy", 0.0)
    sadness = model_scores.get("sadness", 0.0)
    anger = model_scores.get("anger", 0.0)
    fear = model_scores.get("fear", 0.0)
    neutral = model_scores.get("neutral", 0.0)
    surprise = model_scores.get("surprise", 0.0)

    return {
        "calm": round(max(0.0, neutral * 0.60 + (1 - anger) * 0.10 + (1 - fear) * 0.10), 4),
        "focus": round(max(0.0, neutral * 0.50 + (1 - surprise) * 0.20), 4),
        "uplift": round(max(0.0, joy * 0.85 + surprise * 0.10), 4),
        "warmth": round(max(0.0, joy * 0.45 + neutral * 0.15), 4),
        "tension": round(max(0.0, anger * 0.70 + fear * 0.70), 4),
        "sadness": round(max(0.0, sadness), 4),
    }


def _run_emotion_pipeline(text: str) -> dict[str, float] | None:
    """Ejecuta el clasificador emocional externo y normaliza su salida."""
    _try_load_emotion_pipeline()

    if not (_EMOTION_PIPELINE_READY and _EMOTION_PIPELINE is not None):
        return None

    try:
        outputs = _EMOTION_PIPELINE(text[:512])
        if not outputs:
            return None

        if isinstance(outputs, list) and outputs and isinstance(outputs[0], list):
            outputs = outputs[0]

        mapped: dict[str, float] = {}
        for item in outputs:
            label = str(item.get("label", "")).lower().strip()
            score = float(item.get("score", 0.0))
            mapped[label] = score

        return mapped
    except Exception:
        return None


def _sentiment_from_domain(profile: dict[str, float]) -> tuple[str, float]:
    """Deriva una polaridad simple a partir del perfil de dominio."""
    positive = profile.get("uplift", 0.0) * 0.75 + profile.get("warmth", 0.0) * 0.45
    negative = profile.get("tension", 0.0) * 0.70 + profile.get("sadness", 0.0) * 0.80
    raw = positive - negative
    score = max(-1.0, min(1.0, raw))

    if score >= 0.20:
        return "positive", round(score, 4)
    if score <= -0.20:
        return "negative", round(score, 4)
    return "neutral", round(score, 4)


@lru_cache(maxsize=2048)
def analyze_song_text(text: str) -> dict[str, Any]:
    """
    Punto de entrada principal para analizar letras o texto descriptivo.

    Devuelve:
    - `emotion_scores`: emociones básicas
    - `text_profile`: dimensiones funcionales del proyecto
    - `sentiment_label` y `sentiment_score`
    - `embedding`: vector reusable en comparaciones semánticas
    """
    clean_text = (text or "").strip()

    if not clean_text:
        empty_embedding = [0.0] * _HASHING_DIM
        return {
            "emotion_scores": {
                "joy": 0.0,
                "sadness": 0.0,
                "fear": 0.0,
                "anger": 0.0,
                "neutral": 1.0,
            },
            "text_profile": {
                "calm": 0.0,
                "focus": 0.0,
                "uplift": 0.0,
                "warmth": 0.0,
                "tension": 0.0,
                "sadness": 0.0,
            },
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "embedding": empty_embedding,
        }

    model_emotions = _run_emotion_pipeline(clean_text)

    if model_emotions:
        emotion_scores = {
            "joy": round(model_emotions.get("joy", 0.0), 4),
            "sadness": round(model_emotions.get("sadness", 0.0), 4),
            "fear": round(model_emotions.get("fear", 0.0), 4),
            "anger": round(model_emotions.get("anger", 0.0), 4),
            "neutral": round(model_emotions.get("neutral", 0.0), 4),
        }
        text_profile = _map_pipeline_emotions_to_domain(model_emotions)
    else:
        emotion_scores = _heuristic_emotion_scores(clean_text)
        text_profile = _heuristic_domain_profile(clean_text)

    sentiment_label, sentiment_score = _sentiment_from_domain(text_profile)
    embedding = embed_text(clean_text)

    return {
        "emotion_scores": emotion_scores,
        "text_profile": text_profile,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "embedding": embedding,
    }
