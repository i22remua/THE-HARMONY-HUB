import re
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.firestore_service import get_firestore_client

# -----------------------------------------------------------------------------
# CACHE EN MEMORIA EN PRUEBA, NO SE GUARDA EN FIRESTORE
# -----------------------------------------------------------------------------
# Guardamos resultados ya consultados para no ir a Firestore cada vez que
# aparezca la misma canción durante el ranking.
#
# Clave:
#   track_id + nombre normalizado + artistas normalizados
#
# Valor:
#   diccionario con bpm, energy, valence, danceability, etc.
# -----------------------------------------------------------------------------
_FEATURE_CACHE: dict[str, dict] = {}

# Colección de Firestore donde se guardan las features musicales enriquecidas.
TARGET_COLLECTION = "track_features"


def _normalize_text(value: str | None) -> str:
    """
    Normaliza texto para hacer matching más robusto.

    Limpia:
    - mayúsculas/minúsculas
    - paréntesis y corchetes
    - 'feat.'
    - caracteres extraños
    - espacios duplicados

    Ejemplo:
    "Song Name (Remix) feat. Artist" -> "song name"
    """
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"\(.*?\)", "", value)
    value = re.sub(r"\[.*?\]", "", value)
    value = re.sub(r"feat\.?.*", "", value)
    value = re.sub(r"[^a-z0-9áéíóúüñ\s-]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _safe_float(value: Any) -> float | None:
    """
    Convierte un valor a float de forma segura.

    Devuelve None si:
    - el valor es nulo
    - está vacío
    - o no se puede convertir

    Se usa para campos como:
    - bpm
    - danceability
    - energy
    - valence
    - instrumentalness
    """
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _pick_first_non_null(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        return value
    return None


def _merge_unique_labels(existing: list[str] | None, incoming: list[str] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for item in (existing or []) + (incoming or []):
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)

    return result


def _has_real_acoustic_features(data: dict[str, Any] | None) -> bool:
    if not data:
        return False

    for key in (
        "bpm",
        "danceability",
        "energy_feature",
        "valence_feature",
        "instrumentalness",
        "acousticness",
        "speechiness",
        "liveness",
        "audio_tempo",
        "audio_danceability",
        "audio_energy",
        "audio_valence",
        "audio_instrumentalness",
        "audio_acousticness",
        "audio_speechiness",
        "audio_liveness",
    ):
        if _safe_float(data.get(key)) is not None:
            return True

    return False


def _cache_key(track_id: str | None, track_name: str | None, artists: list[str] | None) -> str:
    """
    Construye la clave única de cache para una canción.

    Esto permite que si la misma canción aparece varias veces durante el ranking,
    no tengamos que volver a consultar Firestore.
    """
    normalized_artists = ",".join(_normalize_text(a) for a in (artists or []))
    return f"{track_id or ''}::{_normalize_text(track_name)}::{normalized_artists}"


def _extract_from_doc(data: dict[str, Any]) -> dict:
    """
    Extrae del documento de Firestore únicamente las features que necesita
    el sistema de recomendación.

    También unifica nombres:
    - si no hay bpm, intenta usar tempo
    """
    bpm = data.get("bpm")
    if bpm is None:
        bpm = data.get("tempo")

    stored_feature_source = data.get("feature_source") or "track_features"
    stored_feature_match = data.get("feature_match")
    inferred_match = stored_feature_match
    if inferred_match is None and stored_feature_source == "msd_catalog":
        if data.get("catalog_track_id"):
            inferred_match = "catalog_track_id"
        elif data.get("msd_track_id"):
            inferred_match = "msd_track_id"
    if inferred_match is None:
        inferred_match = data.get("_matched_by", "document_id")

    return {
        "bpm": bpm,
        "danceability": _safe_float(data.get("danceability")),
        "energy_feature": _safe_float(data.get("energy")),
        "valence_feature": _safe_float(data.get("valence")),
        "instrumentalness": _safe_float(data.get("instrumentalness")),
        "acousticness": _safe_float(data.get("acousticness")),
        "speechiness": _safe_float(data.get("speechiness")),
        "liveness": _safe_float(data.get("liveness")),
        "artist_label": data.get("artist"),
        "labels": data.get("labels", []),
        "matched_source": stored_feature_source,
        "matched_by": inferred_match,
    }


def _should_preserve_existing_features(track: dict[str, Any]) -> bool:
    if not _has_real_acoustic_features(track):
        return False

    feature_source = str(track.get("_feature_source") or "").strip().lower()
    if feature_source in {"msd_catalog", "spotify_audio_features"}:
        return True

    if track.get("catalog_track_id") or track.get("msd_track_id"):
        return True

    return False


def _score_candidate(
    spotify_name: str,
    spotify_artists: list[str],
    doc_name: str | None,
    doc_artist: str | None,
) -> int:
    """
    Puntúa qué parecido es un documento de Firestore a la canción de Spotify
    que estamos intentando enriquecer.

    Se compara:
    - nombre de la canción
    - artista principal

    Reglas:
    - nombre exacto -> mucho score
    - nombre parcialmente contenido -> score medio
    - artista exacto -> mucho score
    - artista parecido -> score medio

    Esto se usa cuando no encontramos el track por ID y necesitamos buscar
    por nombre + artista.
    """
    score = 0
    n_spotify = _normalize_text(spotify_name)
    n_doc = _normalize_text(doc_name)
    if not n_spotify or not n_doc:
        return -1

    if n_spotify == n_doc:
        score += 100
    elif n_spotify in n_doc or n_doc in n_spotify:
        score += 70

    normalized_spotify_artists = [_normalize_text(a) for a in spotify_artists if a]
    n_doc_artist = _normalize_text(doc_artist)

    if n_doc_artist and n_doc_artist in normalized_spotify_artists:
        score += 80
    elif n_doc_artist and any(
        n_doc_artist in artist or artist in n_doc_artist
        for artist in normalized_spotify_artists
    ):
        score += 45

    return score


def get_track_features(
    track_id: str | None,
    track_name: str | None = None,
    artists: list[str] | None = None,
) -> dict:
    """
    Recupera las features musicales de una canción.

    Estrategia:
    1. mirar en cache
    2. buscar por track_id en Firestore
    3. si no existe, buscar por nombre y puntuar candidatos por similitud

    Devuelve:
    - bpm
    - danceability
    - energy_feature
    - valence_feature
    - instrumentalness
    - acousticness
    - speechiness
    - liveness
    - labels
    - matched_source / matched_by

    Si no encuentra nada, devuelve {}.
    """
    key = _cache_key(track_id, track_name, artists)
    if key in _FEATURE_CACHE:
        return _FEATURE_CACHE[key]

    db = get_firestore_client()
    artists = artists or []

    # -------------------------------------------------------------------------
    # 1) Búsqueda directa por document_id = track_id
    # -------------------------------------------------------------------------
    if track_id:
        doc = db.collection(TARGET_COLLECTION).document(track_id).get()
        if doc.exists:
            result = _extract_from_doc(doc.to_dict() or {})
            _FEATURE_CACHE[key] = result
            return result

    # -------------------------------------------------------------------------
    # 2) Fallback por nombre + artista
    # -------------------------------------------------------------------------
    candidates = []

    if track_name:
        docs = (
            db.collection(TARGET_COLLECTION)
            .where(filter=FieldFilter("name", "==", track_name))
            .limit(5)
            .stream()
        )
        for d in docs:
            data = d.to_dict() or {}
            score = _score_candidate(
                spotify_name=track_name,
                spotify_artists=artists,
                doc_name=data.get("name"),
                doc_artist=data.get("artist"),
            )
            if score >= 60:
                data["_matched_by"] = "name_field"
                candidates.append((score, data))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        result = _extract_from_doc(candidates[0][1])
        _FEATURE_CACHE[key] = result
        return result

    # Si no encuentra nada, cachea vacío para no repetir búsquedas inútiles
    _FEATURE_CACHE[key] = {}
    return {}


def enrich_track_with_features(track: dict) -> dict:
    """
    Enriquecer una canción significa añadirle features musicales estructuradas
    procedentes de Firestore.

    Entrada:
    - track básico (por ejemplo, desde Spotify search o recommendations)

    Salida:
    - track con campos añadidos:
      bpm, danceability, energy_feature, valence_feature, instrumentalness,
      acousticness, speechiness, liveness, labels, source, etc.

    Si no hay features en Firestore:
    - mantiene los valores que ya tuviera el track
    - o deja esos campos tal como estén
    """
    result = dict(track)
    preserve_existing = _should_preserve_existing_features(result)
    features = get_track_features(
        track_id=track.get("id"),
        track_name=track.get("name"),
        artists=track.get("artists", []),
    )

    if features:
        result["bpm"] = _pick_first_non_null(
            result.get("bpm"),
            result.get("audio_tempo"),
            features.get("bpm"),
        )
        result["danceability"] = _pick_first_non_null(
            result.get("danceability"),
            result.get("audio_danceability"),
            features.get("danceability"),
        )
        result["energy_feature"] = _pick_first_non_null(
            result.get("energy_feature"),
            result.get("audio_energy"),
            features.get("energy_feature"),
        )
        result["valence_feature"] = _pick_first_non_null(
            result.get("valence_feature"),
            result.get("audio_valence"),
            features.get("valence_feature"),
        )
        result["instrumentalness"] = _pick_first_non_null(
            result.get("instrumentalness"),
            result.get("audio_instrumentalness"),
            features.get("instrumentalness"),
        )
        result["acousticness"] = _pick_first_non_null(
            result.get("acousticness"),
            result.get("audio_acousticness"),
            features.get("acousticness"),
        )
        result["speechiness"] = _pick_first_non_null(
            result.get("speechiness"),
            result.get("audio_speechiness"),
            features.get("speechiness"),
        )
        result["liveness"] = _pick_first_non_null(
            result.get("liveness"),
            result.get("audio_liveness"),
            features.get("liveness"),
        )
        result["artist_label"] = _pick_first_non_null(
            result.get("artist_label"),
            features.get("artist_label"),
        )
        result["labels"] = _merge_unique_labels(
            result.get("labels", []),
            features.get("labels", []),
        )
        if preserve_existing and _has_real_acoustic_features(result):
            result["_feature_source"] = result.get("_feature_source")
            result["_feature_match"] = result.get("_feature_match")
        elif _has_real_acoustic_features(features):
            result["_feature_source"] = features.get("matched_source")
            result["_feature_match"] = features.get("matched_by")
        elif _has_real_acoustic_features(result):
            audio_feature_source = result.get("_audio_feature_source")
            if audio_feature_source:
                result["_feature_source"] = audio_feature_source
                result["_feature_match"] = None
            else:
                result["_feature_source"] = result.get("_feature_source")
                result["_feature_match"] = result.get("_feature_match")
        else:
            result["_feature_source"] = None
            result["_feature_match"] = None
    else:
        # Si no hay documento en Firestore, conservamos o promovemos los
        # audio_* ya presentes en el track para no perder esa señal.
        result["bpm"] = _pick_first_non_null(
            result.get("bpm"),
            result.get("audio_tempo"),
        )
        result["danceability"] = _pick_first_non_null(
            result.get("danceability"),
            result.get("audio_danceability"),
        )
        result["energy_feature"] = _pick_first_non_null(
            result.get("energy_feature"),
            result.get("audio_energy"),
        )
        result["valence_feature"] = _pick_first_non_null(
            result.get("valence_feature"),
            result.get("audio_valence"),
        )
        result["instrumentalness"] = _pick_first_non_null(
            result.get("instrumentalness"),
            result.get("audio_instrumentalness"),
        )
        result["acousticness"] = _pick_first_non_null(
            result.get("acousticness"),
            result.get("audio_acousticness"),
        )
        result["speechiness"] = _pick_first_non_null(
            result.get("speechiness"),
            result.get("audio_speechiness"),
        )
        result["liveness"] = _pick_first_non_null(
            result.get("liveness"),
            result.get("audio_liveness"),
        )
        result["artist_label"] = result.get("artist_label")
        result["labels"] = result.get("labels", [])

        if _has_real_acoustic_features(result):
            audio_feature_source = result.get("_audio_feature_source")
            if audio_feature_source:
                result["_feature_source"] = audio_feature_source
                result["_feature_match"] = None
            else:
                result["_feature_source"] = result.get("_feature_source")
                result["_feature_match"] = result.get("_feature_match")
        else:
            result["_feature_source"] = None
            result["_feature_match"] = None

    return result
