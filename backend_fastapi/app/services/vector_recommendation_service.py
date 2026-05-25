from __future__ import annotations

from math import sqrt

# La similitud vectorial es una capa adicional de personalización que compara un vector de características
# del track con un vector objetivo del usuario, y asigna un bonus al ranking basado en esa similitud,
# lo que permite que el sistema tenga en cuenta no solo características individuales, sino también la coherencia global
# entre el perfil del track y las necesidades y gustos del usuario, afectando así la relevancia de las recomendaciones generadas.
# -----------------------------------------------------------------------------
# UTILIDADES BÁSICAS
# -----------------------------------------------------------------------------
def _safe_float(value, default: float = 0.0) -> float:
    """
    Convierte un valor a float de forma segura.

    Si el valor:
    - es None
    - está vacío
    - o no se puede convertir

    entonces devuelve un valor por defecto.

    Se usa continuamente porque las features pueden venir incompletas
    o con formatos distintos según la fuente.
    """
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Limita un valor a un rango [0, 1].

    Esto es importante porque casi todas las dimensiones del vector
    están pensadas como intensidades o probabilidades normalizadas.
    """
    return max(min_value, min(max_value, value))


# -----------------------------------------------------------------------------
# VECTOR DE LA CANCIÓN
# -----------------------------------------------------------------------------
def build_track_vector(track: dict) -> dict[str, float]:
    """
    Convierte una canción en un vector numérico de características.

    Este vector representa la canción en un espacio común donde
    luego podremos compararla con el vector del usuario.

    Dimensiones incluidas:
    - energy
    - valence
    - danceability
    - instrumentalness
    - popularity
    - uplift
    - calm
    - focus
    - sadness
    - tension
    - warmth

    Importante:
    este vector mezcla dos tipos de señales:
    1. acústicas / musicales
    2. semánticas / emocionales extraídas del texto
    """
    text_profile = track.get("text_profile", {}) or {}

    # Features acústicas base
    energy = (
        _safe_float(track.get("energy_feature"))
        or _safe_float(track.get("audio_energy"))
    )
    valence = (
        _safe_float(track.get("valence_feature"))
        or _safe_float(track.get("audio_valence"))
    )
    danceability = (
        _safe_float(track.get("danceability_feature"))
        or _safe_float(track.get("danceability"))
        or _safe_float(track.get("audio_danceability"))
    )
    instrumentalness = (
        _safe_float(track.get("instrumentalness"))
        or _safe_float(track.get("audio_instrumentalness"))
    )

    # Popularidad de Spotify normalizada de [0..100] a [0..1]
    popularity = _safe_float(track.get("popularity")) / 100.0

    # Devolvemos el vector del track ya normalizado
    return {
        "energy": _clamp(energy),
        "valence": _clamp(valence),
        "danceability": _clamp(danceability),
        "instrumentalness": _clamp(instrumentalness),
        "popularity": _clamp(popularity),

        # Rasgos semánticos/emocionales extraídos del análisis textual
        "uplift": _clamp(_safe_float(text_profile.get("uplift"))),
        "calm": _clamp(_safe_float(text_profile.get("calm"))),
        "focus": _clamp(_safe_float(text_profile.get("focus"))),
        "sadness": _clamp(_safe_float(text_profile.get("sadness"))),
        "tension": _clamp(_safe_float(text_profile.get("tension"))),
        "warmth": _clamp(_safe_float(text_profile.get("warmth"))),
    }


# -----------------------------------------------------------------------------
# VECTOR OBJETIVO DE LA SESIÓN ACTUAL
# -----------------------------------------------------------------------------
def build_session_target_vector(profile: dict, goal: str, mood: str) -> dict[str, float]:
    """
    Construye el vector objetivo de la sesión actual.

    Este vector representa:
    "qué tipo de música necesita el usuario ahora mismo"

    Parte de los targets ya calculados en el generation_profile:
    - target_energy
    - target_valence
    - target_danceability

    Y además añade una capa semántica:
    - uplift
    - calm
    - focus
    - sadness
    - tension
    - warmth
    - instrumentalness

    La lógica depende de:
    - el objetivo (goal)
    - el estado emocional actual (mood)
    """
    target_energy = _clamp(_safe_float(profile.get("target_energy"), 0.5))
    target_valence = _clamp(_safe_float(profile.get("target_valence"), 0.5))
    target_danceability = _clamp(_safe_float(profile.get("target_danceability"), 0.5))

    # Valores base neutros
    uplift = 0.45
    calm = 0.35
    focus = 0.35
    sadness = 0.15
    tension = 0.15
    warmth = 0.45
    instrumentalness = 0.20

    # -------------------------------------------------------------------------
    # Ajustes principales según objetivo
    # -------------------------------------------------------------------------
    if goal == "foco":
        focus = 0.88
        calm = 0.60
        uplift = 0.28
        sadness = 0.08
        tension = 0.08
        warmth = 0.42
        instrumentalness = 0.72

    elif goal == "relajacion":
        calm = 0.92
        focus = 0.32
        uplift = 0.30
        sadness = 0.08
        tension = 0.05
        warmth = 0.72
        instrumentalness = 0.68

    elif goal == "energia":
        calm = 0.22
        focus = 0.28
        uplift = 0.88
        sadness = 0.05
        tension = 0.18
        warmth = 0.52
        instrumentalness = 0.12

    # -------------------------------------------------------------------------
    # Ajustes adicionales según mood actual
    # -------------------------------------------------------------------------
    if mood == "triste":
        # Cuando el usuario está triste:
        # - queremos menos tristeza en la música
        # - más calidez
        # - más uplift
        sadness = 0.04
        warmth = max(warmth, 0.68)
        uplift = max(uplift, 0.72)
        tension = min(tension, 0.12)

    elif mood == "estresado":
        # Si está estresado:
        # - reducimos tensión
        # - subimos calma
        tension = 0.04
        calm = max(calm, 0.78)

    elif mood == "cansado":
        # Si está cansado:
        # - buscamos algo algo más animador
        # - pero manteniendo cierta suavidad
        uplift = max(uplift, 0.62)
        calm = max(calm, 0.42)

    return {
        "energy": target_energy,
        "valence": target_valence,
        "danceability": target_danceability,
        "instrumentalness": instrumentalness,
        "popularity": 0.50,  # valor neutro
        "uplift": uplift,
        "calm": calm,
        "focus": focus,
        "sadness": sadness,
        "tension": tension,
        "warmth": warmth,
    }


# -----------------------------------------------------------------------------
# VECTOR ESTABLE DEL USUARIO
# -----------------------------------------------------------------------------
def build_stable_target_vector(profile: dict) -> dict[str, float]:
    """
    Construye un vector estable del usuario a partir de su perfil aprendido.

    Este vector no representa la sesión actual, sino el gusto relativamente
    duradero del usuario.

    Usa:
    - stable_preferred_energy
    - stable_preferred_valence
    - stable_preferred_danceability
    - vocal_preference
    - géneros preferidos estables

    Conceptualmente:
    - session vector = lo que necesita ahora
    - stable vector  = lo que suele gustarle en general
    """
    stable_energy = _safe_float(
        profile.get("stable_preferred_energy", profile.get("target_energy")),
        0.5,
    )
    stable_valence = _safe_float(
        profile.get("stable_preferred_valence", profile.get("target_valence")),
        0.5,
    )
    stable_danceability = _safe_float(
        profile.get("stable_preferred_danceability", profile.get("target_danceability")),
        0.5,
    )

    vocal_preference = str(profile.get("vocal_preference", "indistinto")).lower()

    # Inferimos una preferencia estable de instrumentalidad
    if vocal_preference == "instrumental":
        instrumentalness = 0.72
    elif vocal_preference == "con_voz":
        instrumentalness = 0.08
    else:
        instrumentalness = 0.28

    stable_genres = profile.get("stable_preferred_genres", []) or []

    # Valores base neutrales
    focus = 0.50
    calm = 0.50
    uplift = 0.50
    sadness = 0.10
    tension = 0.10
    warmth = 0.50

    # Inferimos un sesgo semántico a partir de géneros preferidos
    joined = " ".join(stable_genres).lower()

    if any(x in joined for x in ["ambient", "classical", "acoustic", "chill"]):
        calm = 0.70
        focus = 0.62
        uplift = 0.32
        warmth = 0.58

    if any(x in joined for x in ["dance", "edm", "pop"]):
        uplift = 0.72
        calm = 0.28
        focus = 0.34
        warmth = 0.48

    return {
        "energy": _clamp(stable_energy),
        "valence": _clamp(stable_valence),
        "danceability": _clamp(stable_danceability),
        "instrumentalness": _clamp(instrumentalness),
        "popularity": 0.50,
        "uplift": _clamp(uplift),
        "calm": _clamp(calm),
        "focus": _clamp(focus),
        "sadness": _clamp(sadness),
        "tension": _clamp(tension),
        "warmth": _clamp(warmth),
    }


# -----------------------------------------------------------------------------
# FUSIÓN DE VECTORES DE USUARIO
# -----------------------------------------------------------------------------
def merge_user_vectors(
    *,
    session_vector: dict[str, float] | None,
    stable_vector: dict[str, float] | None,
    session_weight: float = 0.65,
    stable_weight: float = 0.35,
) -> dict[str, float]:
    """
    Fusiona el vector de sesión y el vector estable del usuario.

    Esto permite construir una representación única del usuario
    que combine:
    - necesidad actual
    - gusto estable

    Por defecto:
    - 65% sesión
    - 35% gusto estable

    La idea es que el contexto actual pese más que la preferencia histórica.
    """
    keys = set((session_vector or {}).keys()) | set((stable_vector or {}).keys())
    result: dict[str, float] = {}

    for key in keys:
        sv = _safe_float((session_vector or {}).get(key), 0.0)
        tv = _safe_float((stable_vector or {}).get(key), 0.0)
        result[key] = (sv * session_weight) + (tv * stable_weight)

    return result


# -----------------------------------------------------------------------------
# SIMILITUD COSENO
# -----------------------------------------------------------------------------
def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """
    Calcula la similitud coseno entre dos vectores.
 las canciones se representan como 
    Resultado:
    - cercano a 1.0  -> vectores muy parecidos
    - cercano a 0.0  -> vectores poco parecidos

    Esta métrica no compara magnitudes absolutas, sino orientación.
    Eso es útil aquí porque queremos medir:
    "¿se parece el perfil del track al perfil deseado del usuario?"
    """
    keys = set(vec_a.keys()) | set(vec_b.keys())

    dot = sum(_safe_float(vec_a.get(k)) * _safe_float(vec_b.get(k)) for k in keys)
    norm_a = sqrt(sum(_safe_float(vec_a.get(k)) ** 2 for k in keys))
    norm_b = sqrt(sum(_safe_float(vec_b.get(k)) ** 2 for k in keys))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


# -----------------------------------------------------------------------------
# BONUS FINAL POR SIMILITUD VECTORIAL
# -----------------------------------------------------------------------------
def compute_vector_similarity_delta(
    track: dict,
    *,
    session_vector: dict[str, float],
    stable_vector: dict[str, float] | None = None,
    session_weight: float = 0.72,
    stable_weight: float = 0.28,
    max_bonus: float = 18.0,
) -> tuple[float, dict]:
    """
    Calcula cuánto bonus recibe una canción por similitud vectorial.

    Pasos:
    1. construye el vector del track
    2. construye el vector combinado del usuario
    3. calcula similitud coseno
    4. transforma esa similitud en un bonus de score

    max_bonus controla el peso máximo de esta capa vectorial.
    En otras partes del sistema, este valor se reduce si faltan features fiables,
    para evitar dar demasiado peso a una similitud pobremente fundamentada.
    """
    track_vector = build_track_vector(track)

    user_vector = merge_user_vectors(
        session_vector=session_vector,
        stable_vector=stable_vector,
        session_weight=session_weight,
        stable_weight=stable_weight,
    )

    similarity = cosine_similarity(user_vector, track_vector)

    # Convertimos la similitud [0..1] en una bonificación sobre el ranking
    delta = round(similarity * max_bonus, 2)

    return delta, {
        "track_vector": track_vector,
        "user_vector": user_vector,
        "cosine_similarity": round(similarity, 4),
    }