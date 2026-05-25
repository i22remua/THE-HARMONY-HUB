from collections import defaultdict
import math
import re
import unicodedata

from app.services.semantic_track_service import compute_textual_adjustment
from app.services.track_feature_service import enrich_track_with_features
from app.services.user_preference_learning_service import (
    get_user_generation_preferences,
)
from app.services.vector_recommendation_service import (
    build_session_target_vector,
    build_stable_target_vector,
    compute_vector_similarity_delta,
)

# -----------------------------------------------------------------------------
# UTILIDADES BÁSICAS
# -----------------------------------------------------------------------------
def _safe_float(value):
    """
    Convierte un valor a float de forma segura.

    Se usa porque muchos datos pueden llegar como string, vacíos o nulos.
    Si no se puede convertir, devuelve None en lugar de romper la ejecución.
    """
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _track_text(track: dict) -> str:
    """
    Construye una representación textual simple de una canción.

    Une:
    - nombre del track
    - artistas

    Esto se usa para:
    - detectar keywords
    - penalizar términos incompatibles
    - inferir si el track parece instrumental, relajante, etc.
    """
    artists = " ".join(track.get("artists", []))
    return f"{track.get('name', '')} {artists}".lower()


def _normalize_text_for_dedupe(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _semantic_duplicate_key(track: dict) -> str:
    """
    Genera una clave de deduplicado semántico para evitar clones por título.

    Para títulos claramente funcionales o de fallback, deduplicamos por nombre.
    Para el resto, usamos nombre + artistas para no ser demasiado agresivos.
    """
    title = _normalize_text_for_dedupe(track.get("name"))
    if not title:
        return ""

    artists = [
        _normalize_text_for_dedupe(artist)
        for artist in (track.get("artists", []) or [])
        if artist
    ]
    artists = [artist for artist in artists if artist]
    artists_key = "|".join(sorted(dict.fromkeys(artists[:2])))

    generic_penalty = _safe_float(track.get("generic_title_penalty")) or 0.0
    fallback_query = bool(track.get("_fallback_query"))
    generic_title = any(
        token in title
        for token in [
            "corporate",
            "office",
            "work",
            "motivational",
            "background",
            "study",
            "focus",
            "playlist",
            "music",
        ]
    )

    if fallback_query or generic_penalty >= 8.0 or generic_title:
        return f"title::{title}"

    if artists_key:
        return f"title_artist::{title}::{artists_key}"

    return f"title::{title}"


def _track_labels(track: dict) -> set[str]:
    """
    Devuelve un conjunto de etiquetas normalizadas asociadas a la canción.

    Las etiquetas salen de dos fuentes:
    1. labels ya existentes en el track
    2. tokens inferidos a partir del nombre del track

    Ejemplo:
    si el nombre contiene 'focus' o 'ambient', esas etiquetas se añaden.
    """
    labels = track.get("labels", []) or []
    normalized = set()

    for item in labels:
        if item is None:
            continue
        normalized.add(str(item).strip().lower())

    name = str(track.get("name", "")).lower()
    if name:
        for token in [
            "focus",
            "study",
            "deep",
            "calm",
            "ambient",
            "chill",
            "relax",
            "energy",
            "party",
            "rage",
            "hard",
            "sleep",
            "soft",
            "instrumental",
            "acoustic",
            "workout",
            "club",
            "remix",
        ]:
            if token in name:
                normalized.add(token)

    return normalized


def _is_instrumental_like(track: dict) -> bool:
    """
    Heurística para decidir si una canción parece instrumental.

    Se considera instrumental si:
    - tiene label 'instrumental'
    - su instrumentalness >= 0.58
    - o el texto contiene pistas como 'piano', 'ambient', 'classical', etc.

    Esto es útil cuando el usuario pide:
    - música instrumental
    - foco
    - relajación
    """
    labels = _track_labels(track)
    instrumentalness = _safe_float(track.get("instrumentalness"))

    if "instrumental" in labels:
        return True

    if instrumentalness is not None and instrumentalness >= 0.58:
        return True

    text = _track_text(track)
    instrumental_hints = ["instrumental", "piano", "ambient", "classical", "soundscape"]
    if any(hint in text for hint in instrumental_hints):
        return True

    return False


def _observed_vocal_presence(track: dict) -> float | None:
    """
    Estima la presencia vocal observable de un track.

    Prioridad:
    1. `vocal_presence_score` explícito del catálogo
    2. inversión aproximada de `instrumentalness`

    Devuelve un valor 0-1 o `None` si no hay evidencia suficiente.
    """
    explicit_score = _safe_float(track.get("vocal_presence_score"))
    if explicit_score is not None:
        return _clamp(explicit_score, 0.0, 1.0)

    instrumentalness = _safe_float(track.get("instrumentalness"))
    if instrumentalness is None:
        return None

    return _clamp(1.0 - instrumentalness, 0.0, 1.0)


def _matches_vocal_preference_hard_constraint(
    track: dict,
    vocal_preference: str,
) -> bool:
    """
    Aplica una restricción dura de presencia vocal.

    - `instrumental`: exige evidencia clara de instrumentalidad.
    - `con_voz`: exige evidencia positiva de voz o letra disponible.

    Esto endurece el comportamiento final para que la preferencia vocal no sea
    solo una señal de ranking, sino una condición de aceptación del track.
    """
    preference = (vocal_preference or "indistinto").lower()
    if preference not in {"instrumental", "con_voz"}:
        return True

    instrumental_like = _is_instrumental_like(track)
    instrumentalness = _safe_float(track.get("instrumentalness"))
    vocal_presence = _observed_vocal_presence(track)
    lyrics_available = bool(track.get("lyrics_available"))

    if preference == "instrumental":
        if instrumental_like:
            return True
        if instrumentalness is not None and instrumentalness >= 0.55:
            return True
        if vocal_presence is not None and vocal_presence <= 0.20:
            return True
        return False

    # con_voz
    if instrumental_like:
        return False
    if instrumentalness is not None and instrumentalness >= 0.40:
        return False
    if lyrics_available:
        return True
    if vocal_presence is not None and vocal_presence >= 0.55:
        return True
    return False


# -----------------------------------------------------------------------------
# PREFERENCIAS APRENDIDAS DEL USUARIO
# -----------------------------------------------------------------------------
def _sorted_positive_genres(map_data: dict | None, limit: int = 3) -> list[str]:
    """
    Selecciona los géneros con puntuación positiva más alta.

    Ejemplo:
    si el usuario ha dado feedback positivo repetido sobre 'ambient' o 'chill',
    estos géneros subirán y se usarán antes como semillas de recomendación.
    """
    items = []
    for genre, value in (map_data or {}).items():
        score = _safe_float(value)
        if score is None or score <= 0:
            continue
        items.append((genre, score))

    items.sort(key=lambda x: x[1], reverse=True)
    return [genre for genre, _ in items[:limit]]


def _merge_seed_genres(
    *,
    session_genres: list[str],
    stable_genres: list[str],
    goal_genres: list[str],
    avoided_genres_map: dict | None,
    max_items: int = 5,
) -> list[str]:
    """
    Construye la lista final de géneros semilla para Spotify.

    Orden de prioridad:
    1. géneros preferidos en la sesión/contexto
    2. géneros preferidos estables del usuario
    3. géneros base del objetivo (foco, relajación, energía)

    Además evita géneros demasiado penalizados por el usuario.
    """
    avoided = avoided_genres_map or {}
    merged: list[str] = []

    for genre in session_genres + stable_genres + goal_genres:
        if not genre or genre in merged:
            continue

        avoided_score = _safe_float(avoided.get(genre)) or 0.0
        if avoided_score >= 3.0 and genre not in goal_genres:
            continue

        merged.append(genre)
        if len(merged) >= max_items:
            break

    return merged or goal_genres[:max_items] or ["pop"]


def _compute_taste_weights(
    *,
    session_positive_feedback_count: int,
    session_negative_feedback_count: int,
    stable_positive_feedback_count: int,
    stable_negative_feedback_count: int,
    exploration_preference: str,
) -> tuple[float, float, float, float]:
    """
    Calcula cuánto peso damos a las preferencias aprendidas del usuario a partir
    de evidencia estadística, no de saltos fijos por número de sesiones.

    Devuelve dos pesos:
    - session_weight: peso del gusto reciente / contextual 
    - stable_weight: peso del gusto estable / histórico 
    - session_confidence: confianza estadística del perfil de sesión
    - stable_confidence: confianza estadística del perfil estable

    La confianza se estima con el límite inferior de Wilson al 95% sobre la
    tasa de feedback positivo. Así penalizamos automáticamente:
    - pocas observaciones
    - señales inconsistentes
    - usuarios con muchos negativos o feedback muy volátil
    """
    def _wilson_lower_bound(positive_count: int, total_count: int, z: float = 1.96) -> float:
        if total_count <= 0:
            return 0.0

        proportion = positive_count / total_count
        denominator = 1.0 + (z * z) / total_count
        center = proportion + (z * z) / (2.0 * total_count)
        margin = z * math.sqrt(
            (proportion * (1.0 - proportion) + (z * z) / (4.0 * total_count))
            / total_count
        )
        return max(0.0, min(1.0, (center - margin) / denominator))

    session_total = max(
        0,
        int(session_positive_feedback_count or 0) + int(session_negative_feedback_count or 0),
    )
    stable_total = max(
        0,
        int(stable_positive_feedback_count or 0) + int(stable_negative_feedback_count or 0),
    )

    session_confidence = _wilson_lower_bound(
        int(session_positive_feedback_count or 0),
        session_total,
    )
    stable_confidence = _wilson_lower_bound(
        int(stable_positive_feedback_count or 0),
        stable_total,
    )

    exploration_factor_map = {
        "familiar": 1.0,
        "equilibrado": 0.75,
        "descubrir": 0.4,
    }
    exploration_factor = exploration_factor_map.get(
        exploration_preference,
        exploration_factor_map["equilibrado"],
    )

    raw_session_weight = session_confidence * exploration_factor
    raw_stable_weight = stable_confidence * exploration_factor

    # Reservamos siempre una masa base de contexto actual = 1.0 y repartimos el
    # resto entre el perfil de sesión y el estable según la evidencia observada.
    denominator = 1.0 + raw_session_weight + raw_stable_weight
    session_weight = raw_session_weight / denominator
    stable_weight = raw_stable_weight / denominator

    return (
        round(session_weight, 3),
        round(stable_weight, 3),
        round(session_confidence, 3),
        round(stable_confidence, 3),
    )


def _compute_mood_learning_quality(mood_stats: dict | None) -> tuple[bool, float, float, float, float]:
    """
    Calcula si el sistema ya tiene evidencia musical suficiente para un mood.

    La gate no depende de "haber llegado a N sesiones" como salto duro, sino de
    una combinación continua de:
    - consistencia del feedback positivo
    - fuerza observacional acumulada
    - cobertura de géneros positivos en ese mood
    - las curvas exponenciales permiten que la calidad mejore progresivamente a medida que se acumula más evidencia, sin saltos abruptos, pero aún manteniendo un criterio riguroso para la activación completa del aprendizaje.
    """
    stats = mood_stats or {}
    positive_count = max(0, int(stats.get("positive_feedback_count", 0) or 0))
    negative_count = max(0, int(stats.get("negative_feedback_count", 0) or 0))
    feedback_count = max(
        max(0, int(stats.get("feedback_count", 0) or 0)),
        positive_count + negative_count,
    )

    if feedback_count <= 0:
        return (False, 0.0, 0.0, 0.0, 0.0)

    proportion = positive_count / feedback_count
    z = 1.96
    denominator = 1.0 + (z * z) / feedback_count
    center = proportion + (z * z) / (2.0 * feedback_count)
    margin = z * math.sqrt(
        (proportion * (1.0 - proportion) + (z * z) / (4.0 * feedback_count))
        / feedback_count
    )
    consistency = max(0.0, min(1.0, (center - margin) / denominator))

    observation_strength = 1.0 - math.exp(-feedback_count / 4.0) # crece rápido al principio y luego se estabiliza alrededor de 1.0
    positive_genres = stats.get("preferred_genres", {}) or {}
    positive_genre_count = sum(
        1 for score in positive_genres.values() if (_safe_float(score) or 0.0) > 0.0
    )
    genre_coverage = 1.0 - math.exp(-positive_genre_count / 2.5)

    quality_score = round(
        (
            consistency * 0.45
            + observation_strength * 0.35
            + genre_coverage * 0.20
        )
        * 100.0,
        2,
    )
    gate_passed = (
        quality_score >= 60.0
        and consistency >= 0.22
        and observation_strength >= 0.50
        and positive_genre_count >= 2
    )

    return (
        gate_passed,
        quality_score,
        round(consistency, 3),
        round(observation_strength, 3),
        round(genre_coverage, 3),
    )


def _compute_mood_application_factor(
    *,
    gate_passed: bool,
    quality_score: float,
    consistency: float,
    observation_strength: float,
    genre_coverage: float,
) -> float:
    """
    Traduce la evidencia de un mood a un factor progresivo 0-1.

    La gate sigue existiendo y cuando se supera el factor pasa a 1.0. Si no se
    supera, se evita el salto binario a cero total y se permite una aplicación
    parcial del aprendizaje cuando ya hay señales razonables, aunque todavía no
    suficientes para una activación completa.
    """
    if gate_passed:
        return 1.0

    if quality_score < 35.0:
        return 0.0

    if quality_score < 50.0:
        factor = 0.15
    elif quality_score < 60.0:
        factor = 0.35
    elif quality_score < 70.0:
        factor = 0.60
    else:
        factor = 0.80

    if observation_strength >= 0.50:
        factor += 0.10
    if consistency >= 0.22:
        factor += 0.05
    if genre_coverage >= 0.75:
        factor += 0.05

    return round(min(0.60, max(0.0, factor)), 3)


def _compute_stable_application_floor(
    *,
    feedback_count: int,
    stable_confidence: float,
) -> float:
    """
    Mantiene una pequeña parte del gusto estable cuando ya existe evidencia
    global suficiente, incluso si el mood actual todavía no ha madurado.
    """
    if feedback_count >= 12 and stable_confidence >= 0.70:
        return 0.25
    if feedback_count >= 8 and stable_confidence >= 0.55:
        return 0.18
    if feedback_count >= 4 and stable_confidence >= 0.45:
        return 0.10
    return 0.0


def _blend_with_taste_profiles(
    *,
    base_value: float,
    session_value: float | None,
    stable_value: float | None,
    session_weight: float,
    stable_weight: float,
) -> float:
    """
    Mezcla un valor base con las preferencias aprendidas.

    Ejemplo:
    - base_value = energía esperada por el estado actual
    - session_value = energía que suele funcionar en sesiones parecidas
    - stable_value = energía que históricamente gusta al usuario

    Resultado: un valor final más personalizado.
    """
    result = base_value

    if session_value is not None:
        result = (result * (1 - session_weight)) + (session_value * session_weight)

    if stable_value is not None:
        result = (result * (1 - stable_weight)) + (stable_value * stable_weight)

    return result

# -----------------------------------------------------------------------------
# AJUSTES DEL PERFIL MUSICAL OBJETIVO
# -----------------------------------------------------------------------------
def _apply_desired_outcome_to_targets(
    *,
    desired_outcome: str | None,
    base_valence: float,
    base_energy: float,
    base_danceability: float,
) -> tuple[float, float, float]:
    """
    Ajusta los targets musicales según cómo quiere acabar el usuario.

    Ejemplos:
    - mas_calmado -> menos energía, menos danceability
    - mas_centrado -> energía media y poca danceability
    - mas_despierto -> más energía, más valence, más danceability
    """
    if desired_outcome == "mas_calmado":
        base_energy = max(0.12, base_energy - 0.18)
        base_danceability = max(0.10, base_danceability - 0.10)
        base_valence = min(0.72, max(0.42, base_valence))

    elif desired_outcome == "mas_centrado":
        base_energy = min(max(base_energy, 0.32), 0.58)
        base_danceability = min(base_danceability, 0.28)
        base_valence = min(0.68, max(0.42, base_valence))

    elif desired_outcome in {"mas_animado", "mas_despierto"}:
        base_energy = min(0.85, base_energy + 0.12)
        base_danceability = min(0.88, base_danceability + 0.08)
        base_valence = min(0.88, base_valence + 0.10)

    elif desired_outcome == "mas_acompanado":
        base_valence = min(0.76, max(0.45, base_valence))
        base_energy = min(max(base_energy, 0.30), 0.62)

    elif desired_outcome == "mas_ligero":
        base_valence = min(0.84, max(0.55, base_valence))
        base_energy = min(max(base_energy, 0.32), 0.68)

    return base_valence, base_energy, base_danceability


def _apply_noise_context_to_targets(
    *,
    noise_category: str,
    goal: str,
    base_valence: float,
    base_energy: float,
    base_danceability: float,
) -> tuple[float, float, float]:
    """
    Ajusta el perfil musical objetivo según el ruido del entorno.

    Idea:
    - en entornos quiet, para foco o relajación preferimos música más sutil
    - en entornos loud o active, para foco necesitamos algo con más presencia
    """
    category = (noise_category or "").lower()

    if category == "quiet":
        if goal == "foco":
            base_energy = min(base_energy, 0.48)
            base_danceability = min(base_danceability, 0.22)
        elif goal == "relajacion":
            base_energy = min(base_energy, 0.32)
            base_danceability = min(base_danceability, 0.18)

    elif category == "moderate":
        if goal == "foco":
            base_energy = min(max(base_energy, 0.32), 0.56)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.62), 0.82)

    elif category == "active":
        if goal in {"foco", "relajacion"}:
            base_energy = min(max(base_energy, 0.40), 0.64)
            base_danceability = min(max(base_danceability, 0.20), 0.42)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.70), 0.88)

    elif category == "loud":
        if goal == "foco":
            base_energy = min(max(base_energy, 0.48), 0.68)
            base_danceability = min(max(base_danceability, 0.24), 0.45)
        elif goal == "relajacion":
            base_energy = min(max(base_energy, 0.36), 0.58)
            base_valence = min(max(base_valence, 0.45), 0.72)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.74), 0.90)

    return base_valence, base_energy, base_danceability


def _queries_for_noise_context(noise_category: str, goal: str) -> list[str]:
    """
    Genera queries de búsqueda en función del entorno acústico.

    Estas queries sirven para buscar canciones candidatas más coherentes con el
    contexto real del usuario. Por ejemplo, si el ruido es "active" y el objetivo es "foco", buscamos canciones con presencia pero no demasiado bailables, como "steady concentration beats" o "study rhythm". 
    """
    category = (noise_category or "").lower()

    if category == "quiet":
        if goal == "foco":
            return ["deep focus instrumental", "minimal piano", "soft ambient study"]
        if goal == "relajacion":
            return ["calm ambient", "soft piano relax", "gentle chill instrumental"]
        return ["gentle energy boost", "feel good soft pop", "upbeat but smooth"]

    if category == "moderate":
        if goal == "foco":
            return ["focus instrumental", "study ambient", "clear concentration music"]
        if goal == "relajacion":
            return ["relaxing ambient", "soft chill", "calm acoustic"]
        return ["motivation pop", "energy boost", "feel good dance"]

    if category == "active":
        if goal == "foco":
            return [
                "clear focus instrumental",
                "steady concentration beats",
                "study rhythm",
            ]
        if goal == "relajacion":
            return ["stable calm", "soft steady chill", "comfort ambient"]
        return ["upbeat motivation", "steady energy", "feel good workout lite"]

    if category == "loud":
        if goal == "foco":
            return [
                "strong focus instrumental",
                "steady study beats",
                "clear rhythm concentration",
            ]
        if goal == "relajacion":
            return ["stable calm focus", "warm ambient", "soft but present chill"]
        return ["high energy pop", "strong motivation", "driving upbeat"]

    return []


def _environment_influence_strength(
    *,
    use_environment: bool,
    environment_confidence: float | None,
    environment_variability: float | None,
    environment_peak_delta: float | None,
    transient_ratio: float | None,
    burst_count: int | None,
) -> float:
    if not use_environment:
        return 0.0

    confidence = _safe_float(environment_confidence)
    variability = _safe_float(environment_variability) or 0.0
    peak_delta = _safe_float(environment_peak_delta) or 0.0
    transient = _safe_float(transient_ratio) or 0.0
    bursts = max(0, int(burst_count or 0))

    base = confidence if confidence is not None else 0.45
    signal_bonus = min(variability / 12.0, 0.10)
    signal_bonus += min(peak_delta / 28.0, 0.08)
    signal_bonus += min(transient / 2.5, 0.05)
    signal_bonus += min(bursts / 10.0, 0.04)

    return _clamp((base * 0.72) + signal_bonus, 0.0, 0.95)


def _blend_environment_adjustment(
    base_value: float,
    adjusted_value: float,
    influence_strength: float,
) -> float:
    if influence_strength <= 0:
        return base_value

    weight = _clamp(influence_strength, 0.0, 1.0)
    return base_value + ((adjusted_value - base_value) * weight)


def _apply_environment_context_to_targets(
    *,
    goal: str,
    environment_context: str | None,
    base_valence: float,
    base_energy: float,
    base_danceability: float,
) -> tuple[float, float, float]:
    context = (environment_context or "").strip().lower()

    if context == "silencio estable":
        if goal == "foco":
            base_energy = min(base_energy, 0.42)
            base_danceability = min(base_danceability, 0.18)
        elif goal == "relajacion":
            base_energy = min(base_energy, 0.28)
            base_danceability = min(base_danceability, 0.15)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.52), 0.74)

    elif context == "ruido de fondo suave":
        if goal == "foco":
            base_energy = min(max(base_energy, 0.28), 0.50)
        elif goal == "relajacion":
            base_energy = min(base_energy, 0.34)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.58), 0.78)

    elif context == "entorno conversacional":
        if goal == "foco":
            base_energy = min(max(base_energy, 0.38), 0.60)
            base_danceability = min(max(base_danceability, 0.18), 0.32)
        elif goal == "relajacion":
            base_energy = min(max(base_energy, 0.30), 0.46)
            base_valence = min(max(base_valence, 0.46), 0.70)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.68), 0.86)

    elif context == "picos intermitentes":
        if goal in {"foco", "relajacion"}:
            base_energy = min(max(base_energy, 0.34), 0.56)
            base_danceability = min(max(base_danceability, 0.16), 0.30)
        else:
            base_energy = min(max(base_energy, 0.66), 0.84)

    elif context == "espacio público activo":
        if goal == "foco":
            base_energy = min(max(base_energy, 0.42), 0.64)
            base_danceability = min(max(base_danceability, 0.20), 0.36)
        elif goal == "relajacion":
            base_energy = min(max(base_energy, 0.34), 0.52)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.72), 0.90)

    elif context == "ruido continuo intenso":
        if goal == "foco":
            base_energy = min(max(base_energy, 0.46), 0.68)
            base_danceability = min(max(base_danceability, 0.22), 0.40)
        elif goal == "relajacion":
            base_energy = min(max(base_energy, 0.36), 0.56)
            base_valence = min(max(base_valence, 0.48), 0.72)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.74), 0.90)

    elif context == "actividad sonora moderada":
        if goal == "foco":
            base_energy = min(max(base_energy, 0.34), 0.56)
        elif goal == "relajacion":
            base_energy = min(max(base_energy, 0.28), 0.44)
        elif goal == "energia":
            base_energy = min(max(base_energy, 0.64), 0.82)

    return base_valence, base_energy, base_danceability


def _queries_for_environment_context(
    environment_context: str | None,
    goal: str,
) -> list[str]:
    context = (environment_context or "").strip().lower()

    if context == "silencio estable":
        if goal == "foco":
            return ["ultra minimal focus", "silent room piano", "detail rich ambient"]
        if goal == "relajacion":
            return ["quiet room ambient", "soft still piano", "weightless calm"]
        return ["gentle awake pop", "soft motivational indie", "light bright groove"]

    if context == "ruido de fondo suave":
        if goal == "foco":
            return ["steady study instrumental", "soft clear focus", "warm concentration music"]
        if goal == "relajacion":
            return ["soft warm calm", "gentle acoustic relax", "stable comforting chill"]
        return ["easy energy pop", "bright but smooth indie", "light movement music"]

    if context == "entorno conversacional":
        if goal == "foco":
            return ["clear focus beats", "present instrumental study", "structured concentration music"]
        if goal == "relajacion":
            return ["steady warm relax", "comforting chill vocals", "calm but present music"]
        return ["social energy pop", "confident groove pop", "warm upbeat tracks"]

    if context == "picos intermitentes":
        if goal == "foco":
            return ["steady rhythm focus", "anchoring instrumental", "consistent study pulse"]
        if goal == "relajacion":
            return ["stable ambient comfort", "soft grounding chill", "settling instrumental"]
        return ["steady lift pop", "focused upbeat indie", "controlled energy boost"]

    if context == "espacio público activo":
        if goal == "foco":
            return ["present focus instrumental", "clear rhythm concentration", "public space study music"]
        if goal == "relajacion":
            return ["warm shielding ambient", "stable calm textures", "soft but present comfort"]
        return ["crowd safe energy pop", "public space motivation", "strong upbeat lift"]

    if context == "ruido continuo intenso":
        if goal == "foco":
            return ["strong focus instrumental", "dense study beats", "masking concentration music"]
        if goal == "relajacion":
            return ["protective ambient", "warm calming layers", "stable low distraction chill"]
        return ["high presence pop", "driving motivation music", "bold upbeat energy"]

    return []


def _resolve_session_subtype(
    *,
    goal: str,
    desired_outcome: str | None,
    vocal_preference: str,
    intensity_preference: str,
    mood: str,
) -> str:
    if goal == "foco":
        if vocal_preference == "instrumental" and desired_outcome == "mas_centrado":
            return "deep_focus"
        if vocal_preference == "con_voz" and desired_outcome in {"mas_centrado", "mas_acompanado"}:
            return "guided_focus"
        if desired_outcome in {"mas_despierto", "mas_animado"}:
            return "alert_focus"
        return "steady_focus"

    if goal == "relajacion":
        if vocal_preference == "con_voz" and desired_outcome in {"mas_calmado", "mas_acompanado"}:
            return "comfort_relaxation"
        if desired_outcome == "mas_calmado":
            return "stable_relaxation"
        if desired_outcome == "mas_acompanado":
            return "warm_relaxation"
        return "gentle_relaxation"

    if goal == "energia":
        if desired_outcome == "mas_acompanado" and mood == "triste":
            return "warm_companionship"
        if desired_outcome in {"mas_despierto", "mas_animado"} and intensity_preference == "suave":
            return "soft_activation"
        if intensity_preference == "alta":
            return "peak_energy"
        return "balanced_energy"

    return "balanced_session"


def _resolve_activation_curve(
    *,
    session_subtype: str,
    goal: str,
    intensity_preference: str,
) -> str:
    if session_subtype in {"deep_focus", "guided_focus", "steady_focus", "warm_relaxation"}:
        return "flat"
    if session_subtype in {"stable_relaxation", "comfort_relaxation", "peak_energy"}:
        return "peak_then_settle"
    if goal == "energia" or session_subtype in {"alert_focus", "soft_activation"}:
        return "progressive"
    if intensity_preference == "suave":
        return "flat"
    return "progressive"


def _subtype_targets(session_subtype: str, vocal_preference: str) -> tuple[float, float, float]:
    defaults = {
        "deep_focus": (0.34, 0.90, 0.05), 
        "guided_focus": (0.48, 0.86, 0.76),
        "alert_focus": (0.30, 0.74, 0.12),
        "steady_focus": (0.38, 0.82, 0.10),
        "stable_relaxation": (0.82, 0.92, 0.28),
        "comfort_relaxation": (0.88, 0.88, 0.78),
        "warm_relaxation": (0.86, 0.84, 0.46),
        "gentle_relaxation": (0.76, 0.80, 0.34),
        "soft_activation": (0.64, 0.68, 0.60),
        "warm_companionship": (0.88, 0.72, 0.82), # los numeros significan (valence, energy, vocal_presence)
        "peak_energy": (0.48, 0.50, 0.62),
        "balanced_energy": (0.58, 0.58, 0.56),
        "balanced_session": (0.55, 0.60, 0.45),
    }
    warmth, steadiness, vocal_presence = defaults.get(
        session_subtype,
        defaults["balanced_session"],
    )

    if vocal_preference == "instrumental":
        vocal_presence = min(vocal_presence, 0.08)
    elif vocal_preference == "con_voz":
        vocal_presence = max(vocal_presence, 0.62)

    return warmth, steadiness, vocal_presence


def build_generation_profile(
    user_id: str,
    goal: str,
    mood: str,
    stress_level: int,
    energy_level: int,
    noise_category: str,
    vocal_preference: str,
    intensity_preference: str,
    exploration_preference: str,
    popularity_preference: str,
    session_duration_min: int,
    desired_outcome: str | None = None,
    environment_context: str | None = None,
    environment_variability: float | None = None,
    environment_peak_delta: float | None = None,
    environment_confidence: float | None = None,
    transient_ratio: float | None = None,
    burst_count: int | None = None,
    use_environment: bool = True,
) -> dict:
    """
    FUNCIÓN CENTRAL DEL MODELO.

    Convierte el estado emocional/contextual del usuario en un perfil musical
    objetivo que luego se usará para buscar y puntuar canciones.

    Salidas principales:
    - seed_genres 
    - target_valence
    - target_energy
    - target_danceability
    - primary_queries
    - avoid_keywords
    """
    # Aquí se concentra la traducción entre "cómo está el usuario" y "qué tipo
    # de música conviene buscar". Todo el ranking posterior depende de este
    # perfil, por eso mezcla contexto actual, entorno y aprendizaje acumulado.
    prefs = get_user_generation_preferences(user_id)
    session_feedback_count = int(prefs.get("session_feedback_count", 0) or 0)
    stable_feedback_count = int(prefs.get("stable_feedback_count", 0) or 0)
    feedback_count = (
        session_feedback_count
        or stable_feedback_count
        or int(prefs.get("feedback_count", 0) or 0)
    )
    session_positive_feedback_count = int(prefs.get("session_positive_feedback_count", 0) or 0)
    session_negative_feedback_count = int(prefs.get("session_negative_feedback_count", 0) or 0)
    stable_positive_feedback_count = int(prefs.get("stable_positive_feedback_count", 0) or 0)
    stable_negative_feedback_count = int(prefs.get("stable_negative_feedback_count", 0) or 0)
    mood_learning_stats = prefs.get("mood_learning_stats", {}) or {}
    current_mood_learning = mood_learning_stats.get(mood, {}) if mood else {}

    # Géneros base por objetivo.
    genre_map = {
        "foco": ["ambient", "classical", "acoustic"],
        "relajacion": ["ambient", "chill", "classical"],
        "energia": ["pop", "dance", "edm"],
    }

    # Mapeo inicial de mood -> valence musical esperada.
    mood_valence = {
        "feliz": 0.85,
        "neutral": 0.55,
        "triste": 0.32,
        "estresado": 0.40,
        "cansado": 0.52,
    }

    base_valence = mood_valence.get(mood, 0.55)

    # La energía base sale del self-report del usuario.
    base_energy = min(max((energy_level / 5), 0.2), 0.95)

    # Ajuste grueso por objetivo.
    if goal == "relajacion": #si pides relajacion y marcas energía 5 pasas de 0.95 a 0.35

        base_energy = min(base_energy, 0.35) #esta linea significa que para el objetivo de relajación, la energía base se limita a un máximo de 0.35, lo que refleja la preferencia por música más suave y tranquila en este contexto.
    elif goal == "foco":
        base_energy = min(max(base_energy, 0.25), 0.50)    #0.25-0.50
    elif goal == "energia":
        base_energy = max(base_energy, 0.70)

    # Ajuste por preferencia de intensidad.
    if intensity_preference == "suave":
        base_energy = max(0.15, base_energy - 0.18)
    elif intensity_preference == "alta":
        base_energy = min(1.0, base_energy + 0.15)

    # Danceability base por objetivo.
    base_danceability = 0.58
    if goal == "foco":
        base_danceability = 0.22
    elif goal == "relajacion":
        base_danceability = 0.18
    elif goal == "energia":
        base_danceability = 0.78

    # La intensidad también debe reflejarse en el movimiento percibido:
    # `suave` busca sesiones menos invasivas y `alta` tolera más impulso.
    if intensity_preference == "suave":
        base_danceability = max(0.10, base_danceability - 0.10)
    elif intensity_preference == "alta":
        base_danceability = min(0.92, base_danceability + 0.08)

    # Refinamos según el estado final deseado.
    base_valence, base_energy, base_danceability = _apply_desired_outcome_to_targets(
        desired_outcome=desired_outcome,
        base_valence=base_valence,
        base_energy=base_energy,
        base_danceability=base_danceability,
    )

    pre_environment_targets = {
        "valence": round(base_valence, 4),
        "energy": round(base_energy, 4),
        "danceability": round(base_danceability, 4),
    }

    environment_influence_strength = _environment_influence_strength(
        use_environment=use_environment,
        environment_confidence=environment_confidence,
        environment_variability=environment_variability,
        environment_peak_delta=environment_peak_delta,
        transient_ratio=transient_ratio,
        burst_count=burst_count,
    )
    noise_queries_applied: list[str] = []
    context_queries_applied: list[str] = []

    # Refinamos según el ruido del entorno solo cuando el usuario decide usarlo.
    if use_environment:
        (
            noise_valence,
            noise_energy,
            noise_danceability,
        ) = _apply_noise_context_to_targets(
            noise_category=noise_category,
            goal=goal,
            base_valence=base_valence,
            base_energy=base_energy,
            base_danceability=base_danceability,
        )
        base_valence = _blend_environment_adjustment(
            base_valence,
            noise_valence,
            environment_influence_strength,
        )
        base_energy = _blend_environment_adjustment(
            base_energy,
            noise_energy,
            environment_influence_strength,
        )
        base_danceability = _blend_environment_adjustment(
            base_danceability,
            noise_danceability,
            environment_influence_strength,
        )

        (
            context_valence,
            context_energy,
            context_danceability,
        ) = _apply_environment_context_to_targets(
            goal=goal,
            environment_context=environment_context,
            base_valence=base_valence,
            base_energy=base_energy,
            base_danceability=base_danceability,
        )
        context_weight = min(0.85, environment_influence_strength + 0.08)
        base_valence = _blend_environment_adjustment(
            base_valence,
            context_valence,
            context_weight,
        )
        base_energy = _blend_environment_adjustment(
            base_energy,
            context_energy,
            context_weight,
        )
        base_danceability = _blend_environment_adjustment(
            base_danceability,
            context_danceability,
            context_weight,
        )

    post_environment_targets = {
        "valence": round(base_valence, 4),
        "energy": round(base_energy, 4),
        "danceability": round(base_danceability, 4),
    }

    (
        mood_learning_gate_passed,
        mood_learning_quality_score,
        mood_learning_consistency,
        mood_learning_observation_strength,
        mood_learning_genre_coverage,
    ) = _compute_mood_learning_quality(current_mood_learning)
    mood_learning_application_factor = _compute_mood_application_factor(
        gate_passed=mood_learning_gate_passed,
        quality_score=mood_learning_quality_score,
        consistency=mood_learning_consistency,
        observation_strength=mood_learning_observation_strength,
        genre_coverage=mood_learning_genre_coverage,
    )

    # Preferencias aprendidas del usuario.
    session_preferred_genres_map = prefs.get("session_preferred_genres", {})
    stable_preferred_genres_map = prefs.get(
        "stable_preferred_genres",
        prefs.get("preferred_genres", {}),
    )
    avoided_genres_map = prefs.get("avoided_genres", {})
    mood_preferred_genres_map = current_mood_learning.get("preferred_genres", {})

    mood_preferred_genres = _sorted_positive_genres(mood_preferred_genres_map, limit=2)
    global_session_preferred_genres = _sorted_positive_genres(
        session_preferred_genres_map,
        limit=2,
    )
    global_stable_preferred_genres = _sorted_positive_genres(
        stable_preferred_genres_map,
        limit=2,
    )

    # Cuánto peso damos a gustos de sesión e históricos.
    (
        session_weight,
        stable_weight,
        session_learning_confidence,
        stable_learning_confidence,
    ) = _compute_taste_weights(
        session_positive_feedback_count=session_positive_feedback_count,
        session_negative_feedback_count=session_negative_feedback_count,
        stable_positive_feedback_count=stable_positive_feedback_count,
        stable_negative_feedback_count=stable_negative_feedback_count,
        exploration_preference=exploration_preference,
    )

    # Preferencias aprendidas de valence/energy/danceability.
    session_preferred_valence = prefs.get(
        "session_preferred_valence",
        prefs.get("preferred_valence"),
    )
    session_preferred_energy = prefs.get(
        "session_preferred_energy",
        prefs.get("preferred_energy"),
    )
    session_preferred_danceability = prefs.get(
        "session_preferred_danceability",
        prefs.get("preferred_danceability"),
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

    mood_preferred_valence = current_mood_learning.get("preferred_valence")
    mood_preferred_energy = current_mood_learning.get("preferred_energy")
    mood_preferred_danceability = current_mood_learning.get("preferred_danceability")

    if mood_learning_gate_passed:
        session_preferred_genres = list(
            dict.fromkeys(mood_preferred_genres + global_session_preferred_genres)
        )[:2]
        stable_preferred_genres = global_stable_preferred_genres
        if mood_preferred_valence is not None:
            session_preferred_valence = mood_preferred_valence
        if mood_preferred_energy is not None:
            session_preferred_energy = mood_preferred_energy
        if mood_preferred_danceability is not None:
            session_preferred_danceability = mood_preferred_danceability
    else:
        session_preferred_genres = global_session_preferred_genres
        stable_preferred_genres = global_stable_preferred_genres

        session_weight = round(
            session_weight * mood_learning_application_factor,
            3,
        )
        stable_weight = round(
            stable_weight
            * max(
                mood_learning_application_factor,
                _compute_stable_application_floor(
                    feedback_count=feedback_count,
                    stable_confidence=stable_learning_confidence,
                ),
            ),
            3,
        )

    # Seed genres finales = mezcla entre objetivo y gusto aprendido.
    seed_genres = _merge_seed_genres(
        session_genres=session_preferred_genres,
        stable_genres=stable_preferred_genres,
        goal_genres=genre_map.get(goal, ["pop"]),
        avoided_genres_map=avoided_genres_map,
        max_items=5,
    )

    # Mezcla final entre el contexto actual y el gusto aprendido.
    target_valence = _blend_with_taste_profiles(
        base_value=base_valence,
        session_value=session_preferred_valence,
        stable_value=stable_preferred_valence,
        session_weight=session_weight,
        stable_weight=stable_weight,
    )
    target_energy = _blend_with_taste_profiles(
        base_value=base_energy,
        session_value=session_preferred_energy,
        stable_value=stable_preferred_energy,
        session_weight=session_weight,
        stable_weight=stable_weight,
    )
    target_danceability = _blend_with_taste_profiles(
        base_value=base_danceability,
        session_value=session_preferred_danceability,
        stable_value=stable_preferred_danceability,
        session_weight=session_weight,
        stable_weight=stable_weight,
    )

    # Las queries son un puente entre el modo abstracto de sesión y un espacio
    # musical recuperable. Se construyen por capas: objetivo, entorno,
    # resultado deseado e intensidad pedida.
    # Queries base por objetivo.
    if goal == "foco":
        primary_queries = [
            "deep focus instrumental",
            "study ambient",
            "minimal piano",
        ]
    elif goal == "relajacion":
        primary_queries = [
            "stress relief ambient",
            "calm piano relax",
            "soft chill instrumental",
        ]
    else:
        primary_queries = [
            "upbeat motivation",
            "energy boost",
            "feel good dance",
        ]

    if goal == "energia" and popularity_preference == "mainstream":
        primary_queries = [
            "popular upbeat pop",
            "known feel good pop",
            "famous positive hits",
        ] + primary_queries

    # Queries extra por contexto acústico.
    if use_environment:
        noise_queries = _queries_for_noise_context(noise_category, goal)
        if noise_queries:
            noise_queries_applied = list(noise_queries)
            primary_queries = noise_queries + primary_queries

        if environment_influence_strength >= 0.30:
            context_queries = _queries_for_environment_context(
                environment_context,
                goal,
            )
            if context_queries:
                max_context_queries = 2 if environment_influence_strength < 0.60 else 3
                context_queries_applied = context_queries[:max_context_queries]
                primary_queries = context_queries_applied + primary_queries

    # Queries extra por resultado deseado.
    if desired_outcome == "mas_calmado":
        primary_queries = [
            "calm ambient",
            "soft piano relax",
            "gentle chill instrumental",
        ] + primary_queries
    elif desired_outcome == "mas_centrado":
        primary_queries = [
            "deep focus study",
            "instrumental concentration",
            "minimal ambient focus",
        ] + primary_queries
    elif desired_outcome in {"mas_animado", "mas_despierto"}:
        if goal == "foco":
            primary_queries = [
                "awake focus instrumental",
                "clear head concentration",
                "steady study beats",
                "alert study music",
            ] + primary_queries
        else:
            primary_queries = [
                "uplifting motivation",
                "gentle energy boost",
                "feel good upbeat",
            ] + primary_queries
    elif desired_outcome == "mas_acompanado":
        primary_queries = [
            "warm acoustic comfort",
            "soft vocal comfort",
            "gentle indie comfort",
        ] + primary_queries
    elif desired_outcome == "mas_ligero":
        primary_queries = [
            "light uplifting chill",
            "soft positive indie",
            "easy feel good",
        ] + primary_queries

    if goal == "energia" and mood == "triste" and desired_outcome == "mas_acompanado":
        primary_queries = [
            "warm familiar pop",
            "popular comforting pop",
            "known uplifting latin pop",
            "soft emotional pop hits",
        ] + primary_queries

    # Refuerzo directo de la preferencia de intensidad para que, al quitar
    # safe_mode, siga habiendo una traducción clara del input del usuario.
    if intensity_preference == "suave":
        if goal == "foco":
            primary_queries = [
                "soft ambient study",
                "gentle piano focus",
                "minimal focus instrumental",
            ] + primary_queries
        elif goal == "relajacion":
            primary_queries = [
                "soft ambient calm",
                "gentle chill instrumental",
                "quiet piano relax",
            ] + primary_queries
        else:
            primary_queries = [
                "soft uplifting indie",
                "gentle positive pop",
                "light chill energy",
            ] + primary_queries
    elif intensity_preference == "alta":
        if goal == "foco":
            primary_queries = [
                "clear focus instrumental",
                "steady concentration beats",
                "alert study music",
            ] + primary_queries
        elif goal == "relajacion":
            primary_queries = [
                "warm present ambient",
                "steady calm textures",
                "soft but present chill",
            ] + primary_queries
        else:
            primary_queries = [
                "uplifting indie pop",
                "energetic feel good",
                "bright pop energy",
            ] + primary_queries

    # Palabras a evitar según objetivo y contexto.
    avoid_keywords = []
    if goal == "foco":
        avoid_keywords.extend(["party", "workout", "remix", "karaoke", "live"])
    if goal == "relajacion":
        avoid_keywords.extend(["hard", "trap", "party", "gym", "boost"])
    if goal == "energia":
        avoid_keywords.extend(["sleep", "ambient", "meditation", "sad piano"])

    if noise_category == "loud":
        avoid_keywords.extend(["whisper", "sleep music"])
    if noise_category == "active" and goal == "foco":
        avoid_keywords.extend(["very slow", "drone"])

    if vocal_preference == "instrumental":
        avoid_keywords.extend(["vocal", "lyrics", "singer"])
    elif vocal_preference == "con_voz":
        avoid_keywords.extend(["instrumental"])

    if intensity_preference == "suave":
        avoid_keywords.extend(
            ["hard", "rage", "club", "drop", "aggressive", "work bgm", "focus forest"]
        )
    elif intensity_preference == "alta":
        avoid_keywords.extend(
            ["sleep", "whisper", "lullaby", "chakra", "neural activation", "healing"]
        )

    if desired_outcome == "mas_calmado":
        avoid_keywords.extend(["rage", "hard", "club", "drop"])
    if desired_outcome == "mas_centrado":
        avoid_keywords.extend(["party", "club", "remix"])
    if desired_outcome == "mas_acompanado":
        avoid_keywords.extend(["drill", "diss", "violence", "beef", "rage"])
    if desired_outcome == "mas_ligero":
        avoid_keywords.extend(["cry", "lonely", "sad"])
    if desired_outcome in {"mas_animado", "mas_despierto"}:
        avoid_keywords.extend(["sleep", "meditation"])
        if goal == "foco":
            avoid_keywords.extend(["party", "club", "remix", "workout"])

    target_duration_ms = max(10, session_duration_min) * 60 * 1000

    exclude_from_taste_profile_default = goal in {"foco", "relajacion"}
    session_subtype = _resolve_session_subtype(
        goal=goal,
        desired_outcome=desired_outcome,
        vocal_preference=vocal_preference,
        intensity_preference=intensity_preference,
        mood=mood,
    )
    activation_curve = _resolve_activation_curve(
        session_subtype=session_subtype,
        goal=goal,
        intensity_preference=intensity_preference,
    )
    target_warmth, target_steadiness, target_vocal_presence = _subtype_targets(
        session_subtype,
        vocal_preference,
    )

    # El resultado final no es todavía una playlist, sino un contrato interno
    # que resume intención funcional, peso aprendido y señales de búsqueda para
    # el catálogo MSD y la materialización posterior.
    return {
        "goal": goal,
        "mood": mood,
        "seed_genres": seed_genres[:5],
        "target_valence": min(max(target_valence, 0.0), 1.0),
        "target_energy": min(max(target_energy, 0.0), 1.0),
        "target_danceability": min(max(target_danceability, 0.0), 1.0),
        "primary_queries": list(dict.fromkeys(primary_queries))[:4],
        "avoid_keywords": avoid_keywords,
        "target_duration_ms": target_duration_ms,
        "max_tracks_per_artist": 2 if exploration_preference != "familiar" else 3,
        "popularity_preference": popularity_preference,
        "exploration_preference": exploration_preference,
        "intensity_preference": intensity_preference,
        "vocal_preference": vocal_preference,
        "recommended_mode": f"{goal}_{mood}_{intensity_preference}",
        "session_subtype": session_subtype,
        "activation_curve": activation_curve,
        "target_warmth": target_warmth,
        "target_steadiness": target_steadiness,
        "target_vocal_presence": target_vocal_presence,
        "feedback_count": feedback_count,
        "session_learning_confidence": session_learning_confidence,
        "stable_learning_confidence": stable_learning_confidence,
        "mood_learning_gate_passed": mood_learning_gate_passed,
        "mood_learning_quality_score": mood_learning_quality_score,
        "mood_learning_consistency": mood_learning_consistency,
        "mood_learning_observation_strength": mood_learning_observation_strength,
        "mood_learning_genre_coverage": mood_learning_genre_coverage,
        "mood_learning_application_factor": mood_learning_application_factor,
        "desired_outcome": desired_outcome,
        "environment_context": environment_context,
        "environment_variability": environment_variability,
        "environment_peak_delta": environment_peak_delta,
        "environment_confidence": environment_confidence,
        "transient_ratio": transient_ratio,
        "burst_count": burst_count,
        "environment_influence_strength": environment_influence_strength,
        "environment_noise_queries": noise_queries_applied,
        "environment_context_queries": context_queries_applied,
        "environment_target_adjustment": {
            "before": pre_environment_targets,
            "after": post_environment_targets,
        },
        "use_environment": use_environment,
        "stress_level": stress_level,
        "energy_level": energy_level,
        "noise_category": noise_category,
        "session_taste_weight": session_weight,
        "stable_taste_weight": stable_weight,
        "session_preferred_genres": session_preferred_genres,
        "stable_preferred_genres": stable_preferred_genres,
        "session_preferred_valence": session_preferred_valence,
        "session_preferred_energy": session_preferred_energy,
        "session_preferred_danceability": session_preferred_danceability,
        "stable_preferred_valence": stable_preferred_valence,
        "stable_preferred_energy": stable_preferred_energy,
        "stable_preferred_danceability": stable_preferred_danceability,
        "taste_profile_mode": (
            "context_only"
            if (session_weight + stable_weight) <= 0.01
            else (
                "progressive_contextual"
                if not mood_learning_gate_passed
                else (
                    "session_weighted"
                    if session_weight >= stable_weight
                    else "stable_weighted"
                )
            )
        ),
        "exclude_from_taste_profile_default": exclude_from_taste_profile_default,
    }


# -----------------------------------------------------------------------------
# SCORING DE CANCIONES
# -----------------------------------------------------------------------------
def _popularity_score(popularity: int, preference: str) -> int:
    """
    Convierte la popularidad de Spotify en una puntuación.

    - mainstream -> favorece canciones muy populares
    - alternativa -> favorece canciones menos populares
    - mixta -> busca un término medio
    """
    if preference == "mainstream":
        return popularity // 5
    if preference == "alternativa":
        return (100 - popularity) // 6
    return 10 - abs(popularity - 50) // 6


def _familiarity_alignment_adjustment(track: dict, profile: dict) -> tuple[float, list[str]]:
    """
    Ajusta el score según cercanía/conocimiento esperado por el usuario.

    Aquí metemos una capa explícita para que:
    - `familiar` favorezca señales de afinidad y perfil aprendido
    - `mainstream` penalice resultados desconocidos/raros cuando además vienen
      solo de fallback y sin features reales
    """
    delta = 0.0
    reasons: list[str] = []

    exploration_preference = profile.get("exploration_preference", "equilibrado")
    popularity_preference = profile.get("popularity_preference", "mixta")

    popularity = int(track.get("popularity", 0) or 0)
    affinity_source = track.get("_affinity_source")
    fallback_query = track.get("_fallback_query")
    has_feature_source = bool(track.get("_feature_source"))

    if exploration_preference == "familiar":
        if affinity_source == "user_top_track":
            delta += 8.0
            reasons.append("familiarity:user_top_track_bonus")
        elif affinity_source:
            delta += 5.0
            reasons.append("familiarity:affinity_artist_bonus")

        if fallback_query and not affinity_source:
            delta -= 3.5
            reasons.append("familiarity:fallback_without_affinity_penalty")

        if not has_feature_source and not affinity_source:
            delta -= 3.5
            reasons.append("familiarity:no_features_without_affinity_penalty")

    elif exploration_preference == "equilibrado":
        if affinity_source == "user_top_track":
            delta += 4.0
            reasons.append("familiarity:user_top_track_support")
        elif affinity_source:
            delta += 2.5
            reasons.append("familiarity:affinity_artist_support")

    elif exploration_preference == "descubrir":
        if affinity_source == "user_top_track":
            delta -= 7.0
            reasons.append("familiarity:discover_top_track_penalty")
        elif affinity_source:
            delta -= 4.5
            reasons.append("familiarity:discover_affinity_penalty")

        if not affinity_source and has_feature_source:
            delta += 2.0
            reasons.append("familiarity:discover_profile_deviation_support")

        if fallback_query and not affinity_source and has_feature_source:
            delta += 1.0
            reasons.append("familiarity:discover_featured_fallback_support")

        if not affinity_source and not has_feature_source:
            delta -= 2.5
            reasons.append("familiarity:discover_unprofiled_penalty")
    else:
        if affinity_source:
            delta += 1.5
            reasons.append("familiarity:light_affinity_support")

    if popularity_preference == "mainstream":
        if popularity >= 80:
            delta += 4.5
            reasons.append("popularity:hit_bonus")
        elif popularity >= 65:
            delta += 2.5
            reasons.append("popularity:strong_mainstream_bonus")
        elif popularity < 20:
            delta -= 5.5
            reasons.append("popularity:too_obscure_penalty")
        elif popularity < 35 and not affinity_source:
            delta -= 3.0
            reasons.append("popularity:obscure_non_affine_penalty")

        if fallback_query and not affinity_source and popularity < 45:
            delta -= 3.5
            reasons.append("popularity:weak_fallback_penalty")

        if not has_feature_source and not affinity_source and popularity < 50:
            delta -= 2.5
            reasons.append("popularity:no_features_non_affine_penalty")

    elif popularity_preference == "alternativa" and popularity >= 85 and not affinity_source:
        delta -= 2.5
        reasons.append("popularity:too_mainstream_penalty")

    return round(delta, 2), reasons


def _companionship_support_adjustment(
    track: dict,
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    profile: dict,
) -> tuple[float, list[str]]:
    """
    Ajusta el ranking para sesiones donde el usuario busca sentirse acompañado.

    En `energia + triste + mas_acompanado` no basta con que el tema sea familiar:
    tiene que transmitir cercanía útil y no sonar frío, brusco o demasiado opaco.
    """
    if not (
        goal == "energia"
        and mood == "triste"
        and desired_outcome == "mas_acompanado"
    ):
        return 0.0, []

    text_profile = track.get("text_profile", {}) or {}
    warmth = _safe_float(text_profile.get("warmth")) or 0.0
    uplift = _safe_float(text_profile.get("uplift")) or 0.0
    calm = _safe_float(text_profile.get("calm")) or 0.0
    sadness = _safe_float(text_profile.get("sadness")) or 0.0
    tension = _safe_float(text_profile.get("tension")) or 0.0
    semantic_similarity = _safe_float(track.get("semantic_similarity")) or 0.0
    popularity = int(track.get("popularity", 0) or 0)
    energy = _safe_float(track.get("energy_feature"))
    danceability = _safe_float(track.get("danceability"))
    affinity_source = track.get("_affinity_source")
    feature_backed = bool(track.get("_feature_source"))
    labels = _track_labels(track)
    text = _track_text(track)
    intensity_preference = profile.get("intensity_preference", "media")

    delta = 0.0
    reasons: list[str] = []

    if warmth >= 0.16:
        delta += 3.0
        reasons.append("companionship:warmth_bonus")
    elif not feature_backed and warmth < 0.08:
        delta -= 2.5
        reasons.append("companionship:low_warmth_penalty")

    if 0.14 <= uplift <= 0.68:
        delta += 2.5
        reasons.append("companionship:gentle_uplift_bonus")
    elif uplift < 0.08:
        delta -= 2.5
        reasons.append("companionship:flat_energy_penalty")

    if calm >= 0.12 and tension <= 0.55:
        delta += 1.5
        reasons.append("companionship:steady_support_bonus")

    if energy is not None:
        if 0.34 <= energy <= 0.66:
            delta += 3.5
            reasons.append("companionship:gentle_energy_window_bonus")
        elif energy > 0.76:
            delta -= 7.0
            reasons.append("companionship:too_explosive_penalty")
        elif energy < 0.22:
            delta -= 2.5
            reasons.append("companionship:too_flat_penalty")

    if danceability is not None:
        if 0.28 <= danceability <= 0.62:
            delta += 2.0
            reasons.append("companionship:balanced_motion_bonus")
        elif danceability > 0.72:
            delta -= 5.0
            reasons.append("companionship:too_dancefloor_penalty")

    if sadness > 0.55 and warmth < 0.18:
        delta -= 3.5
        reasons.append("companionship:too_heavy_penalty")

    if tension > 0.58:
        delta -= 2.5
        reasons.append("companionship:too_harsh_penalty")

    if semantic_similarity >= 0.22:
        delta += 2.5
        reasons.append("companionship:semantic_fit_bonus")
    elif semantic_similarity < 0.10 and affinity_source:
        delta -= 4.0
        reasons.append("companionship:weak_affinity_fit_penalty")

    if not feature_backed and semantic_similarity < 0.12 and not affinity_source:
        delta -= 2.0
        reasons.append("companionship:weak_unknown_fit_penalty")

    if profile.get("popularity_preference") == "mainstream" and popularity >= 55:
        delta += 1.5
        reasons.append("companionship:mainstream_comfort_bonus")

    if (
        profile.get("exploration_preference") == "familiar"
        and affinity_source
        and semantic_similarity >= 0.16
    ):
        delta += 1.5
        reasons.append("companionship:familiar_supported_bonus")

    soft_support_markers = {
        "warm",
        "comfort",
        "acoustic",
        "soft",
        "indie",
        "bright",
        "feel good",
    }
    harsh_markers = {
        "anthem",
        "power",
        "edm",
        "dance",
        "party",
        "club",
        "workout",
    }

    if any(marker in text for marker in soft_support_markers) or labels.intersection(
        {"warm", "comfort", "acoustic", "indie", "soft", "bright"}
    ):
        delta += 2.5
        reasons.append("companionship:soft_support_marker_bonus")

    if any(marker in text for marker in harsh_markers) or labels.intersection(
        {"anthem", "edm", "dance", "party"}
    ):
        penalty = 6.5 if intensity_preference == "suave" else 3.5
        delta -= penalty
        reasons.append("companionship:harsh_marker_penalty")

    return round(delta, 2), reasons


def _session_subtype_adjustment(
    track: dict,
    *,
    profile: dict,
    goal: str,
) -> tuple[float, list[str]]:
    session_subtype = profile.get("session_subtype")
    if not session_subtype:
        return 0.0, []

    text_profile = track.get("text_profile", {}) or {}
    warmth = _safe_float(text_profile.get("warmth")) or 0.0
    calm = _safe_float(text_profile.get("calm")) or 0.0
    focus = _safe_float(text_profile.get("focus")) or 0.0
    tension = _safe_float(text_profile.get("tension")) or 0.0
    energy = _safe_float(track.get("energy_feature"))
    danceability = _safe_float(track.get("danceability"))
    instrumentalness = _safe_float(track.get("instrumentalness"))
    labels = _track_labels(track)

    target_warmth = float(profile.get("target_warmth", 0.55) or 0.55)
    target_steadiness = float(profile.get("target_steadiness", 0.60) or 0.60)
    target_vocal_presence = float(profile.get("target_vocal_presence", 0.45) or 0.45)
    actual_steadiness = max(0.0, min(1.0, 1.0 - tension))

    vocal_presence = 0.85 if "instrumental" not in labels and not _is_instrumental_like(track) else 0.05

    delta = 0.0
    reasons: list[str] = []

    warmth_delta = max(0.0, 1.0 - abs(warmth - target_warmth)) * 3.0
    steadiness_delta = max(0.0, 1.0 - abs(actual_steadiness - target_steadiness)) * 3.0
    vocal_delta = max(0.0, 1.0 - abs(vocal_presence - target_vocal_presence)) * 2.5

    delta += warmth_delta + steadiness_delta + vocal_delta
    if warmth_delta:
        reasons.append(f"session_subtype:warmth_fit:+{round(warmth_delta, 2)}")
    if steadiness_delta:
        reasons.append(f"session_subtype:steadiness_fit:+{round(steadiness_delta, 2)}")
    if vocal_delta:
        reasons.append(f"session_subtype:vocal_fit:+{round(vocal_delta, 2)}")

    if session_subtype == "deep_focus":
        if instrumentalness is not None and instrumentalness >= 0.75:
            delta += 4.0
            reasons.append("session_subtype:deep_focus_instrumental_bonus")
        if energy is not None and 0.24 <= energy <= 0.48:
            delta += 2.0
            reasons.append("session_subtype:deep_focus_energy_window_bonus")
        if danceability is not None and danceability > 0.34:
            delta -= 3.0
            reasons.append("session_subtype:deep_focus_too_dancy_penalty")

    elif session_subtype == "guided_focus":
        if focus >= 0.18:
            delta += 2.5
            reasons.append("session_subtype:guided_focus_focus_bonus")
        if vocal_presence >= 0.55:
            delta += 2.0
            reasons.append("session_subtype:guided_focus_vocal_bonus")
        if instrumentalness is not None and instrumentalness >= 0.80:
            delta -= 2.5
            reasons.append("session_subtype:guided_focus_too_instrumental_penalty")
        if danceability is not None and danceability > 0.46:
            delta -= 2.0
            reasons.append("session_subtype:guided_focus_too_dancy_penalty")

    elif session_subtype == "stable_relaxation":
        if calm >= 0.18:
            delta += 3.0
            reasons.append("session_subtype:stable_relaxation_calm_bonus")
        if tension > 0.42:
            delta -= 3.0
            reasons.append("session_subtype:stable_relaxation_tension_penalty")

    elif session_subtype == "comfort_relaxation":
        if calm >= 0.16:
            delta += 2.5
            reasons.append("session_subtype:comfort_relaxation_calm_bonus")
        if warmth >= 0.18:
            delta += 2.0
            reasons.append("session_subtype:comfort_relaxation_warmth_bonus")
        if vocal_presence >= 0.55:
            delta += 1.75
            reasons.append("session_subtype:comfort_relaxation_vocal_bonus")
        if tension > 0.46:
            delta -= 3.0
            reasons.append("session_subtype:comfort_relaxation_tension_penalty")

    elif session_subtype == "soft_activation":
        if energy is not None and 0.44 <= energy <= 0.70:
            delta += 3.0
            reasons.append("session_subtype:soft_activation_energy_bonus")
        if energy is not None and energy > 0.84:
            delta -= 4.0
            reasons.append("session_subtype:soft_activation_too_hard_penalty")

    elif session_subtype == "warm_companionship":
        if warmth >= 0.16:
            delta += 2.5
            reasons.append("session_subtype:warm_companionship_warmth_bonus")
        if vocal_presence >= 0.60:
            delta += 2.5
            reasons.append("session_subtype:warm_companionship_voice_bonus")
        if "anthem" in labels or "party" in labels:
            delta -= 3.0
            reasons.append("session_subtype:warm_companionship_harsh_penalty")

    elif session_subtype in {"alert_focus", "balanced_energy", "peak_energy"}:
        if energy is not None and goal == "energia" and energy >= 0.54:
            delta += 1.5
            reasons.append("session_subtype:activation_support_bonus")

    return round(delta, 2), reasons


def _feature_alignment_bonus(track: dict, profile: dict, goal: str) -> tuple[int, list[str]]:
    """
    Compara las features acústicas del track con el perfil musical objetivo.

    Da bonus si:
    - su valence se parece a la target_valence
    - su energy se parece a la target_energy
    - su bpm cae en un rango útil para el objetivo
    - sus labels encajan con foco / relajación / energía
    """
    score = 0
    reasons = []

    bpm = track.get("bpm")
    energy = track.get("energy_feature")
    valence = track.get("valence_feature")
    labels = track.get("labels", []) or []

    target_valence = profile["target_valence"]
    target_energy = profile["target_energy"]

    if valence is not None:
        diff = abs(float(valence) - float(target_valence))
        bonus = max(0, 14 - int(diff * 20))
        score += bonus
        reasons.append(f"valence_fit:+{bonus}")

    if energy is not None:
        diff = abs(float(energy) - float(target_energy))
        bonus = max(0, 14 - int(diff * 20))
        score += bonus
        reasons.append(f"energy_fit:+{bonus}")

    if bpm is not None:
        bpm = float(bpm)
        if goal == "foco" and 55 <= bpm <= 100:
            score += 8
            reasons.append("bpm_focus:+8")
        elif goal == "relajacion" and 50 <= bpm <= 90:
            score += 8
            reasons.append("bpm_relax:+8")
        elif goal == "energia" and 95 <= bpm <= 150:
            score += 8
            reasons.append("bpm_energy:+8")

    lower_labels = [str(label).lower() for label in labels]
    if "focus" in lower_labels and goal == "foco":
        score += 8
        reasons.append("label_focus:+8")
    if "relax" in lower_labels and goal == "relajacion":
        score += 8
        reasons.append("label_relax:+8")
    if "energy" in lower_labels and goal == "energia":
        score += 8
        reasons.append("label_energy:+8")

    return score, reasons


def compute_environment_adjustment(
    track: dict,
    *,
    noise_category: str,
    goal: str,
) -> tuple[float, list[str]]:
    """
    Ajusta la puntuación según el entorno acústico real.

    Ejemplo:
    - si hay ruido fuerte y el objetivo es foco, premiamos tracks con más presencia
    - si el entorno es quiet y el objetivo es foco, premiamos tracks delicados y estables
    """
    delta = 0.0
    reasons: list[str] = []

    category = (noise_category or "").lower()
    energy = _safe_float(track.get("energy_feature"))
    valence = _safe_float(track.get("valence_feature"))
    labels = _track_labels(track)
    text = _track_text(track)

    if category == "quiet":
        if goal == "foco":
            if energy is not None and 0.20 <= energy <= 0.55:
                delta += 4.0
                reasons.append("environment:quiet_focus_bonus")
            if "ambient" in labels or "study" in labels or "instrumental" in labels:
                delta += 3.0
                reasons.append("environment:quiet_detail_bonus")
        elif goal == "relajacion":
            if energy is not None and energy < 0.42:
                delta += 4.0
                reasons.append("environment:quiet_relax_bonus")

    elif category == "moderate":
        if goal == "foco":
            if energy is not None and 0.30 <= energy <= 0.62:
                delta += 3.5
                reasons.append("environment:moderate_focus_bonus")
        elif goal == "energia":
            if energy is not None and 0.55 <= energy <= 0.80:
                delta += 3.0
                reasons.append("environment:moderate_energy_bonus")

    elif category == "active":
        if goal in {"foco", "relajacion"}:
            if energy is not None and energy < 0.18:
                delta -= 4.0
                reasons.append("environment:too_subtle_for_active_space")
            elif 0.38 <= energy <= 0.68:
                delta += 4.5
                reasons.append("environment:present_enough_bonus")
        if "whisper" in text or "sleep" in text:
            delta -= 3.0
            reasons.append("environment:fragile_track_penalty")

    elif category == "loud":
        if energy is not None:
            if goal == "foco":
                if 0.45 <= energy <= 0.72:
                    delta += 5.0
                    reasons.append("environment:loud_focus_presence_bonus")
                elif energy < 0.18:
                    delta -= 5.0
                    reasons.append("environment:too_flat_for_loud_space")
            elif goal == "relajacion":
                if 0.34 <= energy <= 0.58:
                    delta += 4.0
                    reasons.append("environment:loud_relax_stability_bonus")
                elif energy > 0.86:
                    delta -= 5.0
                    reasons.append("environment:loud_relax_overload_penalty")
            elif goal == "energia":
                if 0.68 <= energy <= 0.88:
                    delta += 4.0
                    reasons.append("environment:loud_energy_bonus")

        if valence is not None and goal == "relajacion" and 0.45 <= valence <= 0.75:
            delta += 2.0
            reasons.append("environment:loud_relax_valence_bonus")

        if "ambient" in labels and goal == "foco":
            delta -= 1.5
            reasons.append("environment:loud_focus_ambient_soft_penalty")

    return delta, reasons


def compute_desired_outcome_adjustment(
    track: dict,
    *,
    desired_outcome: str | None,
    goal: str,
    mood: str,
    energy_level: int,
    stress_level: int,
) -> tuple[float, list[str]]:
    """
    Ajusta la puntuación según el estado final deseado.

    Ejemplo:
    - si quiere salir más calmado, premiamos tracks calmados y no intensos
    - si quiere salir más centrado, premiamos focus/study/instrumental
    - si quiere salir más despierto, premiamos activación y tono positivo
    """
    if not desired_outcome:
        return 0.0, []

    delta = 0.0
    reasons: list[str] = []

    energy = _safe_float(track.get("energy_feature"))
    valence = _safe_float(track.get("valence_feature"))
    popularity = _safe_float(track.get("popularity"))
    labels = _track_labels(track)

    if desired_outcome == "mas_calmado":
        if energy is not None:
            if energy > 0.80:
                delta -= 10.0
                reasons.append("desired_outcome:too_intense_for_calm")
            elif 0.25 <= energy <= 0.58:
                delta += 8.0
                reasons.append("desired_outcome:calm_energy_bonus")
        if (
            "calm" in labels
            or "ambient" in labels
            or "chill" in labels
            or "relax" in labels
        ):
            delta += 4.0
            reasons.append("desired_outcome:calm_label_bonus")

    elif desired_outcome == "mas_centrado":
        if energy is not None:
            if 0.35 <= energy <= 0.62:
                delta += 8.0
                reasons.append("desired_outcome:focus_energy_bonus")
            elif energy > 0.82:
                delta -= 8.0
                reasons.append("desired_outcome:too_intense_for_focus")
        if (
            "focus" in labels
            or "study" in labels
            or "deep" in labels
            or "instrumental" in labels
        ):
            delta += 5.0
            reasons.append("desired_outcome:focus_label_bonus")

    elif desired_outcome in {"mas_animado", "mas_despierto"}:
        if energy is not None:
            if energy_level <= 2:
                if 0.48 <= energy <= 0.72:
                    delta += 9.0
                    reasons.append("desired_outcome:gentle_activation_bonus")
                elif energy > 0.88:
                    delta -= 7.0
                    reasons.append("desired_outcome:too_abrupt_for_activation")
            else:
                if 0.58 <= energy <= 0.82:
                    delta += 7.0
                    reasons.append("desired_outcome:energizing_bonus")
        if valence is not None and 0.50 <= valence <= 0.85:
            delta += 4.0
            reasons.append("desired_outcome:positive_tone_bonus")

    elif desired_outcome == "mas_acompanado":
        if "instrumental" not in labels and not _is_instrumental_like(track):
            delta += 3.5
            reasons.append("desired_outcome:voice_presence_bonus")
        if valence is not None and 0.35 <= valence <= 0.75:
            delta += 4.0
            reasons.append("desired_outcome:warm_valence_bonus")
        if popularity is not None and popularity >= 35:
            delta += 2.0
            reasons.append("desired_outcome:familiarity_bonus")
        if energy is not None:
            if 0.34 <= energy <= 0.66:
                delta += 5.0
                reasons.append("desired_outcome:companionship_energy_window_bonus")
            elif energy > 0.76:
                delta -= 8.5
                reasons.append("desired_outcome:too_intense_for_companionship")
            elif energy < 0.22 and goal == "energia":
                delta -= 2.5
                reasons.append("desired_outcome:too_flat_for_companionship")
        if goal == "energia" and mood == "triste":
            if "dance" in labels or "party" in labels:
                delta -= 4.5
                reasons.append("desired_outcome:too_party_for_companionship")
            if "acoustic" in labels or "warm" in labels or "indie" in labels:
                delta += 2.5
                reasons.append("desired_outcome:comfort_label_bonus")

    elif desired_outcome == "mas_ligero":
        if valence is not None:
            if valence < 0.22:
                delta -= 8.0
                reasons.append("desired_outcome:too_heavy_penalty")
            elif 0.48 <= valence <= 0.88:
                delta += 7.0
                reasons.append("desired_outcome:lighter_tone_bonus")
        if energy is not None and energy > 0.88 and stress_level >= 4:
            delta -= 4.0
            reasons.append("desired_outcome:too_sharp_for_lightness")

    return delta, reasons


def rank_candidate_tracks(
    tracks: list[dict],
    profile: dict,
    goal: str,
    mood: str,
    desired_outcome: str | None = None,
) -> list[dict]:
    """
    FUNCIÓN DE RANKING PRINCIPAL.

    Para cada canción:
    1. la enriquece con features
    2. calcula una puntuación heurística inicial
    3. ajusta por entorno
    4. ajusta por desired_outcome
    5. ajusta por semántica textual
    6. ajusta por similitud vectorial
    7. guarda score final y razones

    Luego devuelve la lista ordenada de mayor a menor score.
    """
    ranked = []

    # Vectores objetivo:
    # - session_vector representa la necesidad actual
    # - stable_vector representa el gusto más estable del usuario
    session_vector = build_session_target_vector(profile, goal, mood)
    stable_vector = build_stable_target_vector(profile)

    for raw_track in tracks:
        track = enrich_track_with_features(raw_track)

        # Filtrado temprano de incompatibilidades obvias para no seguir
        # puntuando candidatos que contradicen la preferencia vocal.
        if profile.get("vocal_preference") == "instrumental":
            if not _matches_vocal_preference_hard_constraint(track, "instrumental"):
                continue
        elif profile.get("vocal_preference") == "con_voz":
            instrumentalness = _safe_float(track.get("instrumentalness"))
            if _is_instrumental_like(track):
                continue
            if instrumentalness is not None and instrumentalness >= 0.40:
                continue

        score = 0
        reasons = []

        text = _track_text(track)
        popularity = int(track.get("popularity", 0))
        duration_ms = int(track.get("duration_ms", 0))
        explicit = bool(track.get("explicit", False))

        # ---------------------------------------------------------
        # 1) Coincidencia textual con las queries objetivo
        # ---------------------------------------------------------
        keyword_bonus = 0
        for query in profile["primary_queries"]:
            for token in query.lower().split():
                if token and token in text:
                    keyword_bonus += 2

        if keyword_bonus:
            score += keyword_bonus
            reasons.append(f"keyword_match:+{keyword_bonus}")

        # ---------------------------------------------------------
        # 2) Penalización por términos a evitar
        # ---------------------------------------------------------
        avoid_penalty = 0
        for word in profile["avoid_keywords"]:
            if word.lower() in text:
                avoid_penalty += 12

        if avoid_penalty:
            score -= avoid_penalty
            reasons.append(f"avoid_penalty:-{avoid_penalty}")

        # ---------------------------------------------------------
        # 3) Popularidad según preferencia del usuario
        # ---------------------------------------------------------
        pop_score = _popularity_score(popularity, profile["popularity_preference"])
        score += pop_score
        reasons.append(f"popularity:{pop_score:+d}")

        familiarity_delta, familiarity_reasons = _familiarity_alignment_adjustment(
            track,
            profile,
        )
        score += familiarity_delta
        reasons.extend(familiarity_reasons)

        # ---------------------------------------------------------
        # 4) Bonus/penalización por instrumentalidad
        # ---------------------------------------------------------
        if profile["vocal_preference"] == "instrumental":
            if _is_instrumental_like(track):
                score += 12
                reasons.append("instrumental_hint:+12")
            else:
                score -= 18
                reasons.append("instrumental_missing:-18")

                if goal in {"foco", "relajacion"}:
                    score -= 8
                    reasons.append("instrumental_required_for_goal:-8")

        # ---------------------------------------------------------
        # 5) Reglas incompatibles por objetivo
        # ---------------------------------------------------------
        if goal == "foco" and any(x in text for x in ["remix", "party", "club"]):
            score -= 15
            reasons.append("focus_penalty:-15")

        if goal == "relajacion" and any(
            x in text for x in ["gym", "power", "workout"]
        ):
            score -= 18
            reasons.append("relax_penalty:-18")

        if goal == "energia" and any(
            x in text for x in ["sleep", "calm piano", "meditation"]
        ):
            score -= 18
            reasons.append("energy_penalty:-18")

        if mood == "feliz" and any(x in text for x in ["sad", "cry", "lonely"]):
            score -= 12
            reasons.append("happy_mood_penalty:-12")

        # ---------------------------------------------------------
        # 6) Duración adecuada
        # ---------------------------------------------------------
        if duration_ms > 0 and 120000 <= duration_ms <= 330000:
            score += 4
            reasons.append("duration_fit:+4")

        # ---------------------------------------------------------
        # 7) Penalización adicional por explicit en foco
        # ---------------------------------------------------------
        if explicit and goal == "foco":
            score -= 3
            reasons.append("explicit_focus_penalty:-3")

        # ---------------------------------------------------------
        # 8) Ajuste por features acústicas
        # ---------------------------------------------------------
        feature_bonus, feature_reasons = _feature_alignment_bonus(track, profile, goal)
        score += feature_bonus
        reasons.extend(feature_reasons)

        track["heuristic_score"] = score
        track["reasons"] = list(reasons)
        track["taste_profile_mode"] = profile.get("taste_profile_mode")
        track["session_taste_weight"] = profile.get("session_taste_weight", 0.0)
        track["stable_taste_weight"] = profile.get("stable_taste_weight", 0.0)

        # ---------------------------------------------------------
        # 9) Ajuste por entorno acústico
        # ---------------------------------------------------------
        if profile.get("use_environment", True):
            env_delta, env_reasons = compute_environment_adjustment(
                track,
                noise_category=profile.get("noise_category", "moderate"),
                goal=goal,
            )
        else:
            env_delta, env_reasons = 0.0, []
        track["environment_delta"] = round(env_delta, 2)
        track["heuristic_score"] = float(track.get("heuristic_score", 0.0)) + env_delta
        track["reasons"].extend(env_reasons)

        # ---------------------------------------------------------
        # 10) Ajuste por resultado deseado
        # ---------------------------------------------------------
        desired_delta, desired_reasons = compute_desired_outcome_adjustment(
            track,
            desired_outcome=desired_outcome,
            goal=goal,
            mood=mood,
            energy_level=profile.get("energy_level", 3),
            stress_level=profile.get("stress_level", 3),
        )
        track["desired_outcome"] = desired_outcome
        track["desired_outcome_delta"] = round(desired_delta, 2)
        track["heuristic_score"] = (
            float(track.get("heuristic_score", 0.0)) + desired_delta
        )
        track["reasons"].extend(desired_reasons)

        # ---------------------------------------------------------
        # 11) Ajuste semántico-textual avanzado
        # ---------------------------------------------------------
        try:
            text_delta, text_reasons, text_metadata = compute_textual_adjustment(
                track,
                goal=goal,
                mood=mood,
                desired_outcome=desired_outcome,
                noise_category=profile.get("noise_category", "moderate"),
                vocal_preference=profile.get("vocal_preference", "indistinto"),
                intensity_preference=profile.get("intensity_preference", "media"),
                environment_context=profile.get("environment_context"),
            )
        except Exception:
            # Fallback defensivo si el servicio semántico falla.
            text_delta, text_reasons, text_metadata = 0.0, [], {
                "lyrics_available": False,
                "description_available": False,
                "text_profile": {},
                "sentiment_label": "neutral",
                "sentiment_score": 0.0,
                "semantic_similarity": 0.0,
                "text_source_preview": "",
            }

        track["textual_semantic_delta"] = round(text_delta, 2)
        track["lyrics_available"] = text_metadata.get("lyrics_available", False)
        track["description_available"] = text_metadata.get(
            "description_available", False
        )
        track["text_profile"] = text_metadata.get("text_profile", {})
        track["sentiment_label"] = text_metadata.get("sentiment_label", "neutral")
        track["sentiment_score"] = text_metadata.get("sentiment_score", 0.0)
        track["semantic_similarity"] = text_metadata.get("semantic_similarity", 0.0)
        track["text_source_preview"] = text_metadata.get("text_source_preview", "")

        track["heuristic_score"] = float(track.get("heuristic_score", 0.0)) + text_delta
        track["reasons"].extend(text_reasons)

        # Validación final de la preferencia vocal ya con toda la evidencia
        # disponible (features + semántica + lyrics).
        if not _matches_vocal_preference_hard_constraint(
            track,
            profile.get("vocal_preference", "indistinto"),
        ):
            continue

        # ---------------------------------------------------------
        # 12) Refuerzo de contexto cuando faltan audio features
        # ---------------------------------------------------------
        feature_backed = bool(track.get("_feature_source"))
        context_delta = 0.0
        context_reasons: list[str] = []

        if not feature_backed:
            text_profile = track.get("text_profile", {}) or {}
            semantic_similarity = float(track.get("semantic_similarity", 0.0) or 0.0)
            uplift = float(text_profile.get("uplift", 0.0) or 0.0)
            calm = float(text_profile.get("calm", 0.0) or 0.0)
            focus = float(text_profile.get("focus", 0.0) or 0.0)
            warmth = float(text_profile.get("warmth", 0.0) or 0.0)
            tension = float(text_profile.get("tension", 0.0) or 0.0)
            sadness = float(text_profile.get("sadness", 0.0) or 0.0)

            if semantic_similarity >= 0.30:
                context_delta += 2.5
                context_reasons.append("missing_features:semantic_match_bonus")
            elif semantic_similarity < 0.08:
                context_delta -= 2.5
                context_reasons.append("missing_features:weak_semantic_match")

            if goal == "energia":
                if uplift >= 0.30:
                    context_delta += 2.5
                    context_reasons.append("missing_features:uplift_bonus")
                elif uplift < 0.15:
                    context_delta -= 2.5
                    context_reasons.append("missing_features:low_uplift_penalty")

                if desired_outcome in {"mas_despierto", "mas_animado"} and warmth >= 0.12:
                    context_delta += 1.5
                    context_reasons.append("missing_features:warm_activation_bonus")

                if mood == "cansado":
                    if 0.18 <= uplift <= 0.70 and tension <= 0.55:
                        context_delta += 2.0
                        context_reasons.append("missing_features:gentle_activation_bonus")
                    if tension > 0.62:
                        context_delta -= 3.0
                        context_reasons.append("missing_features:too_tense_for_tired_user")
                    if calm > 0.78:
                        context_delta -= 2.0
                        context_reasons.append("missing_features:too_sleepy_for_energy")

                if mood == "triste" and sadness > 0.55 and uplift < 0.30:
                    context_delta -= 2.5
                    context_reasons.append("missing_features:too_heavy_for_sad_user")

            elif goal == "foco":
                if focus >= 0.22 or calm >= 0.28:
                    context_delta += 2.5
                    context_reasons.append("missing_features:focus_text_bonus")
                if tension > 0.52:
                    context_delta -= 2.5
                    context_reasons.append("missing_features:focus_tension_penalty")

            elif goal == "relajacion":
                if calm >= 0.26 or warmth >= 0.18:
                    context_delta += 2.5
                    context_reasons.append("missing_features:calm_text_bonus")
                if tension > 0.48:
                    context_delta -= 2.5
                    context_reasons.append("missing_features:relax_tension_penalty")

        track["missing_feature_context_delta"] = round(context_delta, 2)
        track["heuristic_score"] = float(track.get("heuristic_score", 0.0)) + context_delta
        track["reasons"].extend(context_reasons)

        companionship_delta, companionship_reasons = _companionship_support_adjustment(
            track,
            goal=goal,
            mood=mood,
            desired_outcome=desired_outcome,
            profile=profile,
        )
        track["companionship_delta"] = round(companionship_delta, 2)
        track["heuristic_score"] = (
            float(track.get("heuristic_score", 0.0)) + companionship_delta
        )
        track["reasons"].extend(companionship_reasons)

        session_subtype_delta, session_subtype_reasons = _session_subtype_adjustment(
            track,
            profile=profile,
            goal=goal,
        )
        track["session_subtype_delta"] = round(session_subtype_delta, 2)
        track["heuristic_score"] = (
            float(track.get("heuristic_score", 0.0)) + session_subtype_delta
        )
        track["reasons"].extend(session_subtype_reasons)

        # ---------------------------------------------------------
        # 13) Ajuste por similitud vectorial EN PRUEBAS
        # ---------------------------------------------------------
        # Si no hay features fiables del track, limitamos el bonus vectorial
        # para evitar que domine el score con información pobre.
        vector_max_bonus = 18.0 if feature_backed else 4.0

        vector_delta, vector_meta = compute_vector_similarity_delta(
            track,
            session_vector=session_vector,
            stable_vector=stable_vector,
            session_weight=0.72,
            stable_weight=0.28,
            max_bonus=vector_max_bonus,
        )
        track["vector_similarity_delta"] = round(vector_delta, 2)
        track["vector_similarity"] = vector_meta.get("cosine_similarity", 0.0)
        track["track_vector"] = vector_meta.get("track_vector", {})
        track["user_vector"] = vector_meta.get("user_vector", {})
        track["heuristic_score"] = float(track.get("heuristic_score", 0.0)) + vector_delta
        track["reasons"].append(f"vector_similarity:+{round(vector_delta, 2)}")

        # ---------------------------------------------------------
        # 14) Score final
        # ---------------------------------------------------------
        final_score = float(track.get("heuristic_score", 0.0))
        track["_score"] = final_score
        track["_reasons"] = list(track.get("reasons", []))

        ranked.append(track)

    ranked.sort(key=lambda x: x["_score"], reverse=True)
    return ranked


def _playlist_energy_value(track: dict, default_value: float = 0.5) -> float:
    energy = _safe_float(track.get("energy_feature"))
    if energy is None:
        energy = _safe_float(track.get("audio_energy"))
    if energy is None:
        return default_value
    return min(max(float(energy), 0.0), 1.0)


def _curve_sort_key(track: dict, target_energy: float, fallback_rank: int) -> tuple[float, float]:
    energy = _playlist_energy_value(track, target_energy)
    rank_score = float(track.get("_score", 0.0) or 0.0)
    return (abs(energy - target_energy), -(rank_score - (fallback_rank * 0.01)))


def _reorder_playlist_by_curve(
    tracks: list[dict],
    *,
    activation_curve: str,
    session_subtype: str | None,
) -> list[dict]:
    if len(tracks) <= 2:
        return tracks

    subtype_centers = {
        "deep_focus": 0.34,
        "guided_focus": 0.42,
        "alert_focus": 0.46,
        "steady_focus": 0.40,
        "stable_relaxation": 0.26,
        "comfort_relaxation": 0.30,
        "warm_relaxation": 0.34,
        "gentle_relaxation": 0.30,
        "soft_activation": 0.58,
        "warm_companionship": 0.54,
        "peak_energy": 0.78,
        "balanced_energy": 0.66,
    }
    center = subtype_centers.get(session_subtype or "", 0.50)

    indexed_tracks = list(enumerate(tracks))
    if activation_curve == "progressive":
        ordered = sorted(
            indexed_tracks,
            key=lambda item: (
                _playlist_energy_value(item[1], center),
                -float(item[1].get("_score", 0.0) or 0.0),
                item[0],
            ),
        )
        return [track for _, track in ordered]

    if activation_curve == "peak_then_settle":
        sorted_tracks = [
            track
            for _, track in sorted(
                indexed_tracks,
                key=lambda item: (
                    _playlist_energy_value(item[1], center),
                    -float(item[1].get("_score", 0.0) or 0.0),
                    item[0],
                ),
            )
        ]
        first_cut = max(1, len(sorted_tracks) // 3)
        second_cut = max(first_cut + 1, (len(sorted_tracks) * 2) // 3)
        low = sorted_tracks[:first_cut]
        mid = sorted_tracks[first_cut:second_cut]
        high = sorted_tracks[second_cut:]
        return low + high + mid

    # flat
    ordered = sorted(
        indexed_tracks,
        key=lambda item: _curve_sort_key(item[1], center, item[0]),
    )
    return [track for _, track in ordered]


def assemble_playlist(
    ranked_tracks: list[dict],
    target_duration_ms: int,
    max_tracks_per_artist: int,
    activation_curve: str = "flat",
    session_subtype: str | None = None,
    vocal_preference: str = "indistinto",
) -> list[dict]:
    """
    Construye la playlist final a partir del ranking.

    Reglas principales:
    - no repetir la misma canción
    - no abusar del mismo artista
    - aproximarse a la duración objetivo
    - asegurar un mínimo de canciones
    """
    selected = []
    seen_uris = set()
    seen_semantic_keys = set()
    artist_counts = defaultdict(int)
    accumulated_duration = 0
    estimated_track_duration_ms = 210000
    target_track_count_floor = max(
        4,
        min(10, int(target_duration_ms / estimated_track_duration_ms)),
    )

    def _effective_track_duration_ms(track: dict) -> int:
        duration_ms = int(track.get("duration_ms", 0) or 0)
        if duration_ms > 0:
            return duration_ms

        fallback_duration = track.get("duration")
        if fallback_duration is not None:
            try:
                numeric = float(fallback_duration)
                if numeric > 0:
                    return int(numeric * 1000 if numeric < 10000 else numeric)
            except Exception:
                pass

        return estimated_track_duration_ms

    for track in ranked_tracks:
        if not _matches_vocal_preference_hard_constraint(track, vocal_preference):
            continue

        uri = track.get("uri")
        semantic_key = _semantic_duplicate_key(track)
        if not uri or uri in seen_uris:
            continue
        if semantic_key and semantic_key in seen_semantic_keys:
            continue

        artists = track.get("artists", [])
        if not artists:
            continue

        main_artist = artists[0]
        if artist_counts[main_artist] >= max_tracks_per_artist:
            continue

        track_duration_ms = _effective_track_duration_ms(track)
        projected_duration = accumulated_duration + track_duration_ms
        can_stop_near_target = (
            len(selected) >= target_track_count_floor
            and accumulated_duration >= int(target_duration_ms * 0.82)
        )
        overshoots_too_much = projected_duration > (target_duration_ms + 90000)
        if can_stop_near_target and overshoots_too_much:
            break

        selected.append(track)
        seen_uris.add(uri)
        if semantic_key:
            seen_semantic_keys.add(semantic_key)
        artist_counts[main_artist] += 1
        accumulated_duration = projected_duration

        if accumulated_duration >= target_duration_ms:
            break

        if len(selected) >= 18:
            break

    # Si la playlist ha quedado demasiado corta, rellena con siguientes buenas opciones,
    # pero sin ignorar la duración objetivo.
    if (
        len(selected) < target_track_count_floor
        and accumulated_duration < int(target_duration_ms * 0.9)
    ):
        for track in ranked_tracks:
            if not _matches_vocal_preference_hard_constraint(track, vocal_preference):
                continue

            uri = track.get("uri")
            semantic_key = _semantic_duplicate_key(track)
            if not uri or uri in seen_uris:
                continue
            if semantic_key and semantic_key in seen_semantic_keys:
                continue

            track_duration_ms = _effective_track_duration_ms(track)
            if (
                len(selected) >= max(4, target_track_count_floor - 1)
                and accumulated_duration + track_duration_ms > (target_duration_ms + 90000)
            ):
                continue

            selected.append(track)
            seen_uris.add(uri)
            if semantic_key:
                seen_semantic_keys.add(semantic_key)
            accumulated_duration += track_duration_ms
            if (
                len(selected) >= target_track_count_floor
                or accumulated_duration >= target_duration_ms
            ):
                break

    return _reorder_playlist_by_curve(
        selected,
        activation_curve=activation_curve,
        session_subtype=session_subtype,
    )
