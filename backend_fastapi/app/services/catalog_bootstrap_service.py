from __future__ import annotations

"""
Utilidades para convertir pistas parciales o externas en entradas compatibles
con el catálogo local del proyecto.

Este servicio se usa sobre todo cuando queremos "sembrar" el catálogo con
tracks que no llegan ya en el formato enriquecido del bloque MSD-like. A partir
de metadatos mínimos intenta:

- inferir features musicales si faltan
- asignar género, etiquetas semánticas y cluster funcional
- construir una fila homogénea para `msd_tracks.jsonl`
"""

from typing import Any

from app.services.msd_catalog_service import normalize_catalog_track, normalize_text


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "," in text:
            return [part.strip() for part in text.split(",") if part.strip()]
        return [text]
    text = str(value).strip()
    return [text] if text else []


def _pick_first(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(_clamp(value), 3)


def _has_minimum_features(track: dict[str, Any]) -> bool:
    """Comprueba si la pista ya trae rasgos suficientes para evitar inferencia."""
    return any(
        _safe_float(track.get(field)) is not None
        for field in (
            "bpm",
            "tempo",
            "energy",
            "energy_feature",
            "valence",
            "valence_feature",
            "danceability",
            "instrumentalness",
            "acousticness",
        )
    )


def infer_missing_features_from_text(track: dict[str, Any]) -> dict[str, float] | None:
    """
    Estima un conjunto básico de audio-features a partir de texto.

    Es una heurística de rescate: no pretende competir con audio-features
    reales, pero permite bootstrapear pistas con muy poca estructura a partir
    de palabras clave presentes en título, artista, etiquetas o género.
    """
    text = normalize_text(
        " ".join(
            _as_list(track.get("name"))
            + _as_list(track.get("title"))
            + _as_list(track.get("artist"))
            + _as_list(track.get("artist_name"))
            + _as_list(track.get("labels"))
            + _as_list(track.get("semantic_tags"))
            + _as_list(track.get("genre"))
        )
    )
    if not text:
        return None

    token_groups = {
        "focus": {
            "focus",
            "study",
            "concentration",
            "concentracion",
            "deep",
            "work",
            "piano",
            "instrumental",
            "binaural",
        },
        "relax": {
            "calm",
            "ambient",
            "sleep",
            "meditation",
            "quiet",
            "soft",
            "relax",
            "acoustic",
            "still",
        },
        "energy": {
            "energy",
            "boost",
            "dance",
            "upbeat",
            "party",
            "club",
            "workout",
            "motivation",
            "good",
            "remix",
            "bright",
        },
    }
    counts = {
        archetype: sum(1 for token in tokens if token in text)
        for archetype, tokens in token_groups.items()
    }
    winning = max(counts, key=counts.get)
    if counts[winning] == 0:
        return None

    profiles: dict[str, dict[str, float]] = {
        "focus": {
            "bpm": 72.0,
            "energy": 0.30,
            "valence": 0.48,
            "danceability": 0.14,
            "instrumentalness": 0.90,
            "acousticness": 0.62,
            "speechiness": 0.02,
            "liveness": 0.10,
        },
        "relax": {
            "bpm": 66.0,
            "energy": 0.18,
            "valence": 0.52,
            "danceability": 0.10,
            "instrumentalness": 0.78,
            "acousticness": 0.60,
            "speechiness": 0.02,
            "liveness": 0.09,
        },
        "energy": {
            "bpm": 118.0,
            "energy": 0.78,
            "valence": 0.76,
            "danceability": 0.70,
            "instrumentalness": 0.03,
            "acousticness": 0.12,
            "speechiness": 0.05,
            "liveness": 0.16,
        },
    }
    inferred = dict(profiles[winning])

    if "acoustic" in text:
        inferred["acousticness"] = max(inferred["acousticness"], 0.78)
    if any(token in text for token in ("instrumental", "piano", "binaural", "ambient")):
        inferred["instrumentalness"] = max(inferred["instrumentalness"], 0.88)
        inferred["danceability"] = min(inferred["danceability"], 0.18)
    if any(token in text for token in ("dance", "club", "party", "remix", "workout")):
        inferred["danceability"] = max(inferred["danceability"], 0.76)
        inferred["energy"] = max(inferred["energy"], 0.82)
    if any(token in text for token in ("quiet", "sleep", "meditation", "still")):
        inferred["energy"] = min(inferred["energy"], 0.16)
        inferred["bpm"] = min(inferred["bpm"], 62.0)

    return inferred


def _infer_activation_style(energy: float | None, bpm: float | None) -> str:
    """Resume la evolución esperada de activación en `flat`, `progressive` o `peak`."""
    if (energy or 0.0) >= 0.78 or (bpm or 0.0) >= 128:
        return "peak"
    if (energy or 0.0) >= 0.50 or (bpm or 0.0) >= 96:
        return "progressive"
    return "flat"


def _infer_genre(track: dict[str, Any], labels: list[str]) -> str:
    """
    Asigna un género primario usable por el ranking del catálogo.

    Primero intenta apoyarse en keywords semánticas y, si no encuentra una
    pista clara, cae a reglas basadas en features.
    """
    text = normalize_text(
        " ".join(
            labels
            + _as_list(track.get("artist"))
            + _as_list(track.get("artist_name"))
            + _as_list(track.get("name"))
            + _as_list(track.get("title"))
            + _as_list(track.get("genre"))
        )
    )
    genre_keywords: list[tuple[str, tuple[str, ...]]] = [
        ("ambient", ("ambient", "meditation", "weightless", "drone")),
        ("classical", ("classical", "orchestral", "strings", "piano", "neoclassical")),
        ("jazz", ("jazz", "sax", "trio", "quartet", "coltrane", "evans")),
        ("lofi", ("lofi", "lo-fi", "beat tape", "chillhop")),
        ("acoustic", ("acoustic", "folk", "singer songwriter")),
        ("indie pop", ("indie", "dream pop", "bedroom pop")),
        ("latin pop", ("latin", "reggaeton", "urbano", "bachata", "salsa")),
        ("rnb", ("rnb", "r&b", "neo soul", "soul")),
        ("dance", ("dance", "house", "edm", "disco", "club")),
        ("pop", ("pop", "mainstream", "hits")),
    ]
    for genre, keywords in genre_keywords:
        if any(keyword in text for keyword in keywords):
            return genre

    danceability = _safe_float(track.get("danceability")) or 0.0
    energy = _safe_float(track.get("energy")) or _safe_float(track.get("energy_feature")) or 0.0
    instrumentalness = _safe_float(track.get("instrumentalness")) or 0.0
    acousticness = _safe_float(track.get("acousticness")) or 0.0

    if instrumentalness >= 0.75 and acousticness >= 0.40:
        return "ambient"
    if acousticness >= 0.65:
        return "acoustic"
    if danceability >= 0.68 and energy >= 0.64:
        return "dance"
    if energy >= 0.58:
        return "pop"
    return "indie pop"


def _infer_semantic_scores(track: dict[str, Any]) -> dict[str, float]:
    """
    Deriva scores funcionales intermedios a partir de las features base.

    Estos scores no son etiquetas finales para el usuario, sino señales internas
    que luego aprovecha el ranking del catálogo para medir foco, calma, calidez,
    tensión o soporte emocional.
    """
    energy = _safe_float(_pick_first(track.get("energy"), track.get("energy_feature"))) or 0.5
    valence = _safe_float(_pick_first(track.get("valence"), track.get("valence_feature"))) or 0.5
    danceability = _safe_float(track.get("danceability")) or 0.5
    instrumentalness = _safe_float(track.get("instrumentalness")) or 0.0
    acousticness = _safe_float(track.get("acousticness")) or 0.0
    speechiness = _safe_float(track.get("speechiness")) or 0.0
    liveness = _safe_float(track.get("liveness")) or 0.0
    bpm = _safe_float(_pick_first(track.get("bpm"), track.get("tempo"))) or 95.0

    bpm_soft = 1.0 - min(abs(bpm - 92.0) / 70.0, 1.0)
    steady_pulse = 1.0 - min(abs(bpm - 88.0) / 80.0, 1.0)

    vocal_presence = _clamp(1.0 - instrumentalness)
    tension = _clamp(
        energy * 0.35
        + (1.0 - valence) * 0.30
        + speechiness * 0.20
        + (1.0 - bpm_soft) * 0.15
    )
    steadiness = _clamp(
        steady_pulse * 0.45
        + (1.0 - speechiness) * 0.25
        + (1.0 - liveness) * 0.15
        + (1.0 - min(abs(energy - 0.52) / 0.52, 1.0)) * 0.15
    )
    focus = _clamp(
        (1.0 - energy) * 0.28
        + (1.0 - danceability) * 0.18
        + instrumentalness * 0.34
        + steadiness * 0.20
    )
    calm = _clamp(
        (1.0 - energy) * 0.30
        + acousticness * 0.24
        + (1.0 - tension) * 0.24
        + steadiness * 0.22
    )
    uplift = _clamp(
        valence * 0.42
        + energy * 0.30
        + danceability * 0.20
        + vocal_presence * 0.08
    )
    warmth = _clamp(
        acousticness * 0.24
        + valence * 0.24
        + (1.0 - speechiness) * 0.12
        + vocal_presence * 0.16
        + (1.0 - tension) * 0.24
    )
    emotional_weight = _clamp(
        (1.0 - valence) * 0.40
        + acousticness * 0.20
        + vocal_presence * 0.15
        + (1.0 - uplift) * 0.25
    )
    supportiveness = _clamp(
        warmth * 0.35
        + steadiness * 0.30
        + (1.0 - tension) * 0.20
        + max(vocal_presence, instrumentalness) * 0.15
    )

    return {
        "focus_score": _round_metric(focus) or 0.0,
        "calm_score": _round_metric(calm) or 0.0,
        "uplift_score": _round_metric(uplift) or 0.0,
        "warmth_score": _round_metric(warmth) or 0.0,
        "tension_score": _round_metric(tension) or 0.0,
        "steadiness_score": _round_metric(steadiness) or 0.0,
        "vocal_presence_score": _round_metric(vocal_presence) or 0.0,
        "emotional_weight_score": _round_metric(emotional_weight) or 0.0,
        "supportiveness_score": _round_metric(supportiveness) or 0.0,
    }


def _infer_semantic_tags(track: dict[str, Any], scores: dict[str, float], genre: str) -> list[str]:
    """
    Construye un pequeño vocabulario semántico normalizado para la pista.

    Sirve para enriquecer `_catalog_search_text` y para hacer más explicable el
    comportamiento del ranking cuando no disponemos de descriptores externos
    ricos.
    """
    tags: list[str] = []
    energy = _safe_float(_pick_first(track.get("energy"), track.get("energy_feature"))) or 0.0
    danceability = _safe_float(track.get("danceability")) or 0.0
    instrumentalness = _safe_float(track.get("instrumentalness")) or 0.0
    acousticness = _safe_float(track.get("acousticness")) or 0.0
    valence = _safe_float(_pick_first(track.get("valence"), track.get("valence_feature"))) or 0.0

    if scores["focus_score"] >= 0.68:
        tags.append("focus")
    if scores["calm_score"] >= 0.68:
        tags.append("calm")
    if scores["uplift_score"] >= 0.70:
        tags.append("energy")
    if scores["warmth_score"] >= 0.70:
        tags.append("warm")
    if instrumentalness >= 0.70:
        tags.append("instrumental")
    if acousticness >= 0.60:
        tags.append("acoustic")
    if danceability >= 0.68:
        tags.append("dance")
    if valence >= 0.70:
        tags.append("feel_good")
    if energy >= 0.72:
        tags.append("upbeat")
    if scores["supportiveness_score"] >= 0.72:
        tags.append("supportive")
    tags.append(genre)

    existing = [
        normalize_text(tag)
        for tag in (
            _as_list(track.get("labels"))
            + _as_list(track.get("semantic_tags"))
            + _as_list(track.get("genre"))
        )
    ]
    ordered = []
    seen: set[str] = set()
    for tag in tags + existing:
        cleaned = normalize_text(tag)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return ordered[:8]


def _infer_cluster(
    scores: dict[str, float],
    genre: str,
    activation_style: str,
    track: dict[str, Any],
) -> str:
    """Agrupa la pista en un cluster funcional compacto usado por el catálogo."""
    instrumentalness = _safe_float(track.get("instrumentalness")) or 0.0
    if scores["focus_score"] >= max(scores["calm_score"], scores["uplift_score"]):
        return "focus_instrumental" if instrumentalness >= 0.65 else "focus_soft"
    if scores["calm_score"] >= max(scores["focus_score"], scores["uplift_score"]):
        return "relax_acoustic" if genre in {"ambient", "acoustic", "classical"} else "relax_soft"
    if genre in {"dance", "latin pop"}:
        return "energy_dance"
    if activation_style == "peak":
        return "energy_peak"
    return "energy_pop"


def build_bootstrap_catalog_track(
    track: dict[str, Any],
    *,
    source: str,
    prefer_catalog_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Convierte una pista cruda en una fila normalizada del catálogo local.

    Flujo:
    1. valida que exista identidad mínima (título + artista)
    2. intenta completar features ausentes
    3. infiere género, etiquetas y cluster funcional
    4. construye un registro homogéneo
    5. delega la normalización final en `normalize_catalog_track`
    """
    name = _pick_first(track.get("name"), track.get("title"), track.get("track_name"))
    artist = _pick_first(track.get("artist"), track.get("artist_name"))
    artists = _as_list(_pick_first(track.get("artists"), track.get("artist_names")))
    if not artists and artist:
        artists = [str(artist)]

    if not name or not artists:
        return None

    inferred_features = None
    if not _has_minimum_features(track):
        inferred_features = infer_missing_features_from_text(track)
        if inferred_features is None:
            return None

    labels = (
        _as_list(track.get("labels"))
        + _as_list(track.get("semantic_tags"))
        + _as_list(track.get("track_genre"))
    )
    genre = _infer_genre(track, labels)

    base_track = {
        **track,
        "bpm": _pick_first(
            _safe_float(track.get("bpm")),
            _safe_float(track.get("tempo")),
            inferred_features and inferred_features.get("bpm"),
        ),
        "danceability": _pick_first(
            _safe_float(track.get("danceability")),
            inferred_features and inferred_features.get("danceability"),
        ),
        "energy": _pick_first(
            _safe_float(track.get("energy")),
            _safe_float(track.get("energy_feature")),
            inferred_features and inferred_features.get("energy"),
        ),
        "valence": _pick_first(
            _safe_float(track.get("valence")),
            _safe_float(track.get("valence_feature")),
            inferred_features and inferred_features.get("valence"),
        ),
        "instrumentalness": _pick_first(
            _safe_float(track.get("instrumentalness")),
            inferred_features and inferred_features.get("instrumentalness"),
        ),
        "acousticness": _pick_first(
            _safe_float(track.get("acousticness")),
            inferred_features and inferred_features.get("acousticness"),
        ),
        "speechiness": _pick_first(
            _safe_float(track.get("speechiness")),
            inferred_features and inferred_features.get("speechiness"),
        ),
        "liveness": _pick_first(
            _safe_float(track.get("liveness")),
            inferred_features and inferred_features.get("liveness"),
        ),
    }

    scores = _infer_semantic_scores(base_track)
    activation_style = _infer_activation_style(
        _safe_float(base_track.get("energy")),
        _safe_float(base_track.get("bpm")),
    )
    semantic_tags = _infer_semantic_tags(base_track, scores, genre)
    cluster = _infer_cluster(scores, genre, activation_style, base_track)

    spotify_track_id = _pick_first(
        track.get("spotify_track_id"),
        track.get("track_id"),
        track.get("id"),
    )
    # A partir de aquí ya preparamos un registro "casi catálogo". La
    # normalización final unifica nombres de campos, ids y search text.
    raw = {
        "catalog_track_id": _pick_first(
            prefer_catalog_id,
            track.get("catalog_track_id"),
            f"bootstrap_{spotify_track_id}" if spotify_track_id else None,
        ),
        "msd_track_id": track.get("msd_track_id"),
        "title": str(name).strip(),
        "artist_name": str(artist or artists[0]).strip(),
        "artists": artists,
        "duration_ms": _pick_first(track.get("duration_ms"), track.get("duration_ms "), track.get("duration")),
        "bpm": base_track.get("bpm"),
        "tempo": base_track.get("bpm"),
        "danceability": base_track.get("danceability"),
        "energy": base_track.get("energy"),
        "valence": base_track.get("valence"),
        "instrumentalness": base_track.get("instrumentalness"),
        "acousticness": base_track.get("acousticness"),
        "speechiness": base_track.get("speechiness"),
        "liveness": base_track.get("liveness"),
        "semantic_tags": semantic_tags,
        "genre": genre,
        "genres": [genre],
        "cluster": cluster,
        "labels": labels + semantic_tags,
        "activation_style": activation_style,
        "popularity_proxy": int(round(_safe_float(_pick_first(track.get("popularity"), track.get("popularity_proxy"))) or 0.0)),
        "explicit": bool(track.get("explicit") or False),
        "spotify_track_id": spotify_track_id,
        "spotify_uri": _pick_first(track.get("spotify_uri"), track.get("uri")),
        "source_dataset": source,
        **scores,
    }
    return normalize_catalog_track(raw, source=source)
