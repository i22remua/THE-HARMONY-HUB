from app.services.firestore_service import get_firestore_client

# -----------------------------------------------------------------------------
# COLECCIÓN PRINCIPAL DE PREFERENCIAS DE GENERACIÓN
# -----------------------------------------------------------------------------
# Aquí se guarda el perfil aprendido del usuario:
# - géneros preferidos
# - géneros evitados
# - promedios de valence / energy / danceability
# - contadores de feedback
# - exclusiones de canciones o recomendaciones
# -----------------------------------------------------------------------------
COLLECTION_NAME = "user_generation_preferences"


# -----------------------------------------------------------------------------
# UTILIDADES BÁSICAS
# -----------------------------------------------------------------------------
def _safe_num(value, default: float = 0.0) -> float:
    """
    Convierte un valor a número de forma segura.

    Se usa para evitar errores cuando un campo viene como:
    - None
    - string vacío
    - texto no convertible

    Si falla, devuelve un valor por defecto.
    """
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _update_running_average(
    old_value: float | None,
    new_value: float,
    count: int,
    weight: float = 1.0,
) -> float:
    """
    Actualiza una media acumulada (running average).

    Ejemplo:
    si el usuario suele responder bien a música con energy = 0.65
    y ahora vuelve a dar feedback positivo a una sesión con energy = 0.70,
    esta función recalcula la media aprendida.

    Parámetros:
    - old_value: media previa
    - new_value: nuevo valor observado
    - count: cuántas observaciones previas había
    - weight: peso del nuevo dato (se usa para que algunos feedbacks cuenten más)

    Idea:
    - feedback "mejoró" puede pesar más
    - feedback "igual" puede pesar menos
    """
    if old_value is None or count <= 0:
        return new_value
    return ((old_value * count) + (new_value * weight)) / (count + weight)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Limita un valor a un rango.

    En este fichero se usa mucho para mantener
    valence / energy / danceability entre 0 y 1.
    """
    return max(min_value, min(max_value, value))


def _effect_weight(effect: str | None) -> float:
    """
    Asigna un peso al feedback según el efecto percibido por el usuario.

    Interpretación:
    - "mejoro"  -> el sistema considera este feedback más valioso
    - "igual"   -> aporta información, pero menos fuerte
    - "empeoro" -> también es importante, porque indica qué evitar

    Esto permite que no todos los feedbacks tengan exactamente la misma fuerza.
    """
    if effect == "mejoro":
        return 1.5
    if effect == "igual":
        return 0.6
    if effect == "empeoro":
        return 1.2
    return 1.0


def _unique_strings(values: list[str] | None) -> list[str]:
    """
    Limpia una lista de strings:
    - elimina None
    - elimina vacíos
    - elimina duplicados
    - conserva el orden de aparición

    Se usa por ejemplo para:
    - track_ids excluidos
    - títulos de recomendaciones excluidas
    """
    result: list[str] = []
    seen: set[str] = set()

    for value in values or []:
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        result.append(text)

    return result


def _merge_unique_lists(old_values: list[str] | None, new_values: list[str] | None) -> list[str]:
    """
    Une dos listas de strings sin duplicados.

    Se usa para acumular exclusiones sin repetir elementos.
    """
    return _unique_strings((old_values or []) + (new_values or []))


def _normalize_mood_label(value: str | None) -> str | None:
    """
    Normaliza la etiqueta de mood para usarla como clave estable.
    """
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def _default_mood_learning_block() -> dict:
    """
    Estado inicial de aprendizaje específico por mood.

    Se usa para guardar evidencia musical de un estado emocional concreto,
    por ejemplo `triste` o `estresado`, sin mezclarla con otros moods.
    """
    return {
        "feedback_count": 0,
        "positive_feedback_count": 0,
        "negative_feedback_count": 0,
        "preferred_genres": {},
        "avoided_genres": {},
        "genre_scores": {},
        "preferred_valence": None,
        "preferred_energy": None,
        "preferred_danceability": None,
    }


def _normalize_mood_learning_stats(value: dict | None) -> dict:
    """
    Normaliza la estructura `mood_learning_stats` para compatibilidad.
    """
    normalized: dict[str, dict] = {}

    for raw_mood, raw_stats in (value or {}).items():
        mood = _normalize_mood_label(raw_mood)
        if not mood:
            continue

        stats = raw_stats or {}
        defaults = _default_mood_learning_block()
        normalized[mood] = {
            **defaults,
            **stats,
            "feedback_count": int(stats.get("feedback_count", 0) or 0),
            "positive_feedback_count": int(stats.get("positive_feedback_count", 0) or 0),
            "negative_feedback_count": int(stats.get("negative_feedback_count", 0) or 0),
            "preferred_genres": dict(stats.get("preferred_genres", {})),
            "avoided_genres": dict(stats.get("avoided_genres", {})),
            "genre_scores": dict(stats.get("genre_scores", {})),
        }

    return normalized


# -----------------------------------------------------------------------------
# ESTADO INICIAL DEL PERFIL DE PREFERENCIAS
# -----------------------------------------------------------------------------
def _default_preferences(user_id: str) -> dict:
    """
    Construye el perfil por defecto para un usuario que todavía no tiene historial.

    El diseño distingue dos niveles de aprendizaje:
    1. session_* : gustos de corto plazo o contexto reciente
    2. stable_*  : gustos más estables / históricos

    Esto permite que el sistema combine:
    - lo que suele gustar en general
    - lo que está funcionando en sesiones recientes
    """
    return {
        "user_id": user_id,

        # Perfil estable "clásico"
        "preferred_genres": {},
        "avoided_genres": {},
        "genre_scores": {},
        "preferred_valence": None,
        "preferred_energy": None,
        "preferred_danceability": None,

        # Contadores globales
        "feedback_count": 0,
        "positive_feedback_count": 0,
        "negative_feedback_count": 0,

        # Perfil de sesión / corto plazo
        "session_preferred_genres": {},
        "session_genre_scores": {},
        "session_preferred_valence": None,
        "session_preferred_energy": None,
        "session_preferred_danceability": None,
        "session_feedback_count": 0,
        "session_positive_feedback_count": 0,
        "session_negative_feedback_count": 0,

        # Perfil estable / largo plazo
        "stable_preferred_genres": {},
        "stable_genre_scores": {},
        "stable_preferred_valence": None,
        "stable_preferred_energy": None,
        "stable_preferred_danceability": None,
        "stable_feedback_count": 0,
        "stable_positive_feedback_count": 0,
        "stable_negative_feedback_count": 0,

        # Exclusiones: sirven para evitar reusar ciertos contenidos
        "excluded_track_ids": [],
        "excluded_recommendation_titles": [],

        # Evidencia aprendida por mood para decidir si el sistema ya conoce
        # suficiente información musical de ese estado emocional.
        "mood_learning_stats": {},

        # Versión del esquema
        "taste_profile_version": 3,
    }


# -----------------------------------------------------------------------------
# LECTURA DEL PERFIL DE PREFERENCIAS DEL USUARIO
# -----------------------------------------------------------------------------
def get_user_generation_preferences(user_id: str) -> dict:
    """
    Recupera el perfil de preferencias del usuario desde Firestore.

    Si no existe, devuelve el perfil por defecto.

    Además hace normalización y compatibilidad:
    - si faltan campos nuevos, los rellena
    - si hay campos antiguos, los adapta al formato actual
    """
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(user_id)
    snapshot = doc_ref.get()

    if not snapshot.exists:
        return _default_preferences(user_id)

    data = snapshot.to_dict() or {}
    defaults = _default_preferences(user_id)

    # Cargamos preferencias de sesión
    session_preferred_genres = data.get("session_preferred_genres", {})

    # Si aún no existe stable_preferred_genres, usamos preferred_genres antiguo
    stable_preferred_genres = data.get(
        "stable_preferred_genres",
        data.get("preferred_genres", {}),
    )

    session_genre_scores = data.get("session_genre_scores", {})
    stable_genre_scores = data.get(
        "stable_genre_scores",
        data.get("genre_scores", {}),
    )
    mood_learning_stats = _normalize_mood_learning_stats(
        data.get("mood_learning_stats", {})
    )

    # Resultado final normalizado
    result = {
        **defaults,
        **data,
        "user_id": user_id,
        "session_preferred_genres": session_preferred_genres,
        "session_genre_scores": session_genre_scores,
        "stable_preferred_genres": stable_preferred_genres,
        "stable_genre_scores": stable_genre_scores,

        # Para mantener compatibilidad con partes del sistema que aún miran
        # preferred_genres / genre_scores como perfil principal
        "preferred_genres": stable_preferred_genres,
        "genre_scores": stable_genre_scores,

        "preferred_valence": data.get(
            "stable_preferred_valence",
            data.get("preferred_valence"),
        ),
        "preferred_energy": data.get(
            "stable_preferred_energy",
            data.get("preferred_energy"),
        ),
        "preferred_danceability": data.get(
            "stable_preferred_danceability",
            data.get("preferred_danceability"),
        ),

        # feedback_count total = suma de sesión + estable, si no existe directamente
        "feedback_count": data.get(
            "feedback_count",
            data.get("stable_feedback_count", 0) + data.get("session_feedback_count", 0),
        ),

        # Normalizamos exclusiones
        "excluded_track_ids": _unique_strings(data.get("excluded_track_ids", [])),
        "excluded_recommendation_titles": _unique_strings(
            data.get("excluded_recommendation_titles", [])
        ),
        "mood_learning_stats": mood_learning_stats,
    }

    return result


# -----------------------------------------------------------------------------
# ACTUALIZACIÓN INTERNA DE PREFERENCIAS
# -----------------------------------------------------------------------------
def _apply_preference_update(
    *,
    helpful: bool,
    genres: list[str],
    valence: float,
    energy: float,
    danceability: float,
    effect: str | None,
    preferred_genres: dict,
    avoided_genres: dict,
    genre_scores: dict,
    preferred_valence: float | None,
    preferred_energy: float | None,
    preferred_danceability: float | None,
    positive_feedback_count: int,
    negative_feedback_count: int,
    weight_multiplier: float,
) -> tuple[dict, dict, dict, float | None, float | None, float | None, int, int]:
    """
    Aplica una actualización de preferencias a un bloque de perfil
    (por ejemplo al perfil de sesión o al perfil estable).

    Esta función es el núcleo del aprendizaje.

    Si el feedback es positivo:
    - sube preferred_genres
    - sube genre_scores
    - actualiza promedios de valence/energy/danceability

    Si el feedback es negativo:
    - sube avoided_genres
    - baja genre_scores
    - desplaza los promedios alejándolos del valor observado

    Parámetro importante:
    - weight_multiplier:
      permite que el perfil estable aprenda más lento que el de sesión.
    """
    weight = _effect_weight(effect) * weight_multiplier

    if helpful:
        positive_feedback_count += 1

        # Reforzamos géneros asociados a sesiones útiles
        for genre in genres:
            preferred_genres[genre] = preferred_genres.get(genre, 0) + weight
            genre_scores[genre] = genre_scores.get(genre, 0.0) + weight

        # Actualizamos medias de rasgos musicales preferidos
        preferred_valence = _update_running_average(
            preferred_valence,
            valence,
            positive_feedback_count - 1,
            weight=weight,
        )
        preferred_energy = _update_running_average(
            preferred_energy,
            energy,
            positive_feedback_count - 1,
            weight=weight,
        )
        preferred_danceability = _update_running_average(
            preferred_danceability,
            danceability,
            positive_feedback_count - 1,
            weight=weight,
        )
    else:
        negative_feedback_count += 1

        # Penalizamos géneros asociados a sesiones poco útiles
        for genre in genres:
            avoided_genres[genre] = avoided_genres.get(genre, 0) + weight
            genre_scores[genre] = genre_scores.get(genre, 0.0) - weight

        # En feedback negativo, alejamos ligeramente los promedios del valor observado
        if preferred_valence is not None:
            preferred_valence = _clamp(
                preferred_valence + 0.15 * (preferred_valence - valence)
            )
        if preferred_energy is not None:
            preferred_energy = _clamp(
                preferred_energy + 0.15 * (preferred_energy - energy)
            )
        if preferred_danceability is not None:
            preferred_danceability = _clamp(
                preferred_danceability
                + 0.15 * (preferred_danceability - danceability)
            )

    return (
        preferred_genres,
        avoided_genres,
        genre_scores,
        preferred_valence,
        preferred_energy,
        preferred_danceability,
        positive_feedback_count,
        negative_feedback_count,
    )


# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE APRENDIZAJE DEL USUARIO
# -----------------------------------------------------------------------------
def update_user_generation_preferences(
    user_id: str,
    helpful: bool,
    genres: list[str],
    valence: float,
    energy: float,
    danceability: float,
    effect: str | None = None,
    use_for_taste_profile: bool = True,
    preference_scope: str = "both",
    recommendation_title: str | None = None,
    track_ids: list[str] | None = None,
    mood: str | None = None,
) -> None:
    """
    Actualiza el perfil aprendido del usuario tras recibir feedback.

    Entradas:
    - helpful: si la sesión ayudó o no
    - genres: géneros asociados a la sesión
    - valence / energy / danceability: rasgos musicales de la sesión
    - effect: mejoró / igual / empeoró
    - use_for_taste_profile:
        indica si este feedback debe usarse para aprender gustos
        o solo para excluir contenido
    - preference_scope:
        controla si se actualiza:
        * session_only
        * stable_only
        * both

    Esta función:
    1. carga el perfil actual
    2. decide qué partes actualizar
    3. aplica aprendizaje de sesión y/o estable
    4. actualiza contadores globales
    5. guarda el resultado en Firestore
    """
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(user_id)

    prefs = get_user_generation_preferences(user_id)

    # Géneros evitados se comparten como señal negativa global
    avoided_genres = dict(prefs.get("avoided_genres", {}))

    # ---------------------------
    # PERFIL DE SESIÓN
    # ---------------------------
    session_preferred_genres = dict(prefs.get("session_preferred_genres", {}))
    session_genre_scores = dict(prefs.get("session_genre_scores", {}))
    session_preferred_valence = prefs.get("session_preferred_valence")
    session_preferred_energy = prefs.get("session_preferred_energy")
    session_preferred_danceability = prefs.get("session_preferred_danceability")
    session_feedback_count = int(prefs.get("session_feedback_count", 0))
    session_positive_feedback_count = int(prefs.get("session_positive_feedback_count", 0))
    session_negative_feedback_count = int(prefs.get("session_negative_feedback_count", 0))

    # ---------------------------
    # PERFIL ESTABLE
    # ---------------------------
    stable_preferred_genres = dict(
        prefs.get("stable_preferred_genres", prefs.get("preferred_genres", {}))
    )
    stable_genre_scores = dict(
        prefs.get("stable_genre_scores", prefs.get("genre_scores", {}))
    )
    stable_preferred_valence = prefs.get(
        "stable_preferred_valence",
        prefs.get("preferred_valence"),
    )
    stable_preferred_energy = prefs.get(
        "stable_preferred_energy",
        prefs.get("preferred_energy"),
    )
    stable_preferred_danceability = prefs.get(
        "stable_preferred_danceability",
        prefs.get("preferred_danceability"),
    )
    stable_feedback_count = int(prefs.get("stable_feedback_count", 0))
    stable_positive_feedback_count = int(prefs.get("stable_positive_feedback_count", 0))
    stable_negative_feedback_count = int(prefs.get("stable_negative_feedback_count", 0))

    # Contadores globales
    total_positive_feedback_count = int(prefs.get("positive_feedback_count", 0))
    total_negative_feedback_count = int(prefs.get("negative_feedback_count", 0))
    total_feedback_count = int(prefs.get("feedback_count", 0))
    mood_learning_stats = _normalize_mood_learning_stats(
        prefs.get("mood_learning_stats", {})
    )

    # Determinamos qué bloque actualizar
    normalized_scope = (preference_scope or "both").lower()
    update_session = normalized_scope in {"both", "session_only", "session"}
    update_stable = (
        use_for_taste_profile
        and normalized_scope in {"both", "stable_only", "stable"}
    )

    # Normalizamos géneros
    genres = [str(genre).strip() for genre in genres if str(genre).strip()]
    mood_key = _normalize_mood_label(mood)

    # -------------------------------------------------------------------------
    # ACTUALIZACIÓN DEL PERFIL DE SESIÓN
    # -------------------------------------------------------------------------
    if update_session:
        (
            session_preferred_genres,
            avoided_genres,
            session_genre_scores,
            session_preferred_valence,
            session_preferred_energy,
            session_preferred_danceability,
            session_positive_feedback_count,
            session_negative_feedback_count,
        ) = _apply_preference_update(
            helpful=helpful,
            genres=genres,
            valence=valence,
            energy=energy,
            danceability=danceability,
            effect=effect,
            preferred_genres=session_preferred_genres,
            avoided_genres=avoided_genres,
            genre_scores=session_genre_scores,
            preferred_valence=session_preferred_valence,
            preferred_energy=session_preferred_energy,
            preferred_danceability=session_preferred_danceability,
            positive_feedback_count=session_positive_feedback_count,
            negative_feedback_count=session_negative_feedback_count,
            weight_multiplier=1.0,  # la sesión aprende rápido
        )
        session_feedback_count += 1

    # -------------------------------------------------------------------------
    # ACTUALIZACIÓN DEL PERFIL ESTABLE
    # -------------------------------------------------------------------------
    if update_stable:
        (
            stable_preferred_genres,
            avoided_genres,
            stable_genre_scores,
            stable_preferred_valence,
            stable_preferred_energy,
            stable_preferred_danceability,
            stable_positive_feedback_count,
            stable_negative_feedback_count,
        ) = _apply_preference_update(
            helpful=helpful,
            genres=genres,
            valence=valence,
            energy=energy,
            danceability=danceability,
            effect=effect,
            preferred_genres=stable_preferred_genres,
            avoided_genres=avoided_genres,
            genre_scores=stable_genre_scores,
            preferred_valence=stable_preferred_valence,
            preferred_energy=stable_preferred_energy,
            preferred_danceability=stable_preferred_danceability,
            positive_feedback_count=stable_positive_feedback_count,
            negative_feedback_count=stable_negative_feedback_count,
            weight_multiplier=0.75,  # el perfil estable aprende más despacio
        )
        stable_feedback_count += 1

    # -------------------------------------------------------------------------
    # APRENDIZAJE ESPECÍFICO POR MOOD
    # -------------------------------------------------------------------------
    if use_for_taste_profile and mood_key:
        current_mood_stats = {
            **_default_mood_learning_block(),
            **mood_learning_stats.get(mood_key, {}),
        }
        mood_preferred_genres = dict(current_mood_stats.get("preferred_genres", {}))
        mood_avoided_genres = dict(current_mood_stats.get("avoided_genres", {}))
        mood_genre_scores = dict(current_mood_stats.get("genre_scores", {}))
        mood_preferred_valence = current_mood_stats.get("preferred_valence")
        mood_preferred_energy = current_mood_stats.get("preferred_energy")
        mood_preferred_danceability = current_mood_stats.get("preferred_danceability")
        mood_positive_feedback_count = int(
            current_mood_stats.get("positive_feedback_count", 0) or 0
        )
        mood_negative_feedback_count = int(
            current_mood_stats.get("negative_feedback_count", 0) or 0
        )
        mood_feedback_count = int(current_mood_stats.get("feedback_count", 0) or 0)

        (
            mood_preferred_genres,
            mood_avoided_genres,
            mood_genre_scores,
            mood_preferred_valence,
            mood_preferred_energy,
            mood_preferred_danceability,
            mood_positive_feedback_count,
            mood_negative_feedback_count,
        ) = _apply_preference_update(
            helpful=helpful,
            genres=genres,
            valence=valence,
            energy=energy,
            danceability=danceability,
            effect=effect,
            preferred_genres=mood_preferred_genres,
            avoided_genres=mood_avoided_genres,
            genre_scores=mood_genre_scores,
            preferred_valence=mood_preferred_valence,
            preferred_energy=mood_preferred_energy,
            preferred_danceability=mood_preferred_danceability,
            positive_feedback_count=mood_positive_feedback_count,
            negative_feedback_count=mood_negative_feedback_count,
            weight_multiplier=1.0,
        )
        mood_feedback_count += 1

        mood_learning_stats[mood_key] = {
            "feedback_count": mood_feedback_count,
            "positive_feedback_count": mood_positive_feedback_count,
            "negative_feedback_count": mood_negative_feedback_count,
            "preferred_genres": mood_preferred_genres,
            "avoided_genres": mood_avoided_genres,
            "genre_scores": mood_genre_scores,
            "preferred_valence": mood_preferred_valence,
            "preferred_energy": mood_preferred_energy,
            "preferred_danceability": mood_preferred_danceability,
        }

    # Recalculamos contadores globales como suma de sesión + estable
    total_positive_feedback_count = (
        session_positive_feedback_count + stable_positive_feedback_count
    )
    total_negative_feedback_count = (
        session_negative_feedback_count + stable_negative_feedback_count
    )
    total_feedback_count = session_feedback_count + stable_feedback_count

    # Listas de exclusión
    excluded_recommendation_titles = list(prefs.get("excluded_recommendation_titles", []))
    excluded_track_ids = list(prefs.get("excluded_track_ids", []))

    # Si este feedback no debe entrar en taste profile, lo usamos para excluir
    # canciones o recomendaciones futuras sin alterar el perfil aprendido
    if not use_for_taste_profile:
        if recommendation_title:
            excluded_recommendation_titles = _merge_unique_lists(
                excluded_recommendation_titles,
                [recommendation_title],
            )
        if track_ids:
            excluded_track_ids = _merge_unique_lists(excluded_track_ids, track_ids)

    # -------------------------------------------------------------------------
    # ESCRITURA FINAL EN FIRESTORE
    # -------------------------------------------------------------------------
    # Guardamos tanto:
    # - perfiles de sesión
    # - perfiles estables
    # - campos legacy/compatibles
    # - exclusiones
    doc_ref.set(
        {
            "user_id": user_id,

            # Perfil principal compatible: usamos el estable como referencia base
            "preferred_genres": stable_preferred_genres,
            "avoided_genres": avoided_genres,
            "genre_scores": stable_genre_scores,
            "preferred_valence": stable_preferred_valence,
            "preferred_energy": stable_preferred_energy,
            "preferred_danceability": stable_preferred_danceability,

            # Contadores globales
            "feedback_count": total_feedback_count,
            "positive_feedback_count": total_positive_feedback_count,
            "negative_feedback_count": total_negative_feedback_count,

            # Perfil de sesión
            "session_preferred_genres": session_preferred_genres,
            "session_genre_scores": session_genre_scores,
            "session_preferred_valence": session_preferred_valence,
            "session_preferred_energy": session_preferred_energy,
            "session_preferred_danceability": session_preferred_danceability,
            "session_feedback_count": session_feedback_count,
            "session_positive_feedback_count": session_positive_feedback_count,
            "session_negative_feedback_count": session_negative_feedback_count,

            # Perfil estable
            "stable_preferred_genres": stable_preferred_genres,
            "stable_genre_scores": stable_genre_scores,
            "stable_preferred_valence": stable_preferred_valence,
            "stable_preferred_energy": stable_preferred_energy,
            "stable_preferred_danceability": stable_preferred_danceability,
            "stable_feedback_count": stable_feedback_count,
            "stable_positive_feedback_count": stable_positive_feedback_count,
            "stable_negative_feedback_count": stable_negative_feedback_count,

            # Exclusiones
            "excluded_track_ids": _unique_strings(excluded_track_ids),
            "excluded_recommendation_titles": _unique_strings(
                excluded_recommendation_titles
            ),
            "mood_learning_stats": mood_learning_stats,

            # Versión del esquema
            "taste_profile_version": 3,
        },
        merge=True,
    )
