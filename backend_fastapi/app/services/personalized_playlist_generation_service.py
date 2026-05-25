from __future__ import annotations

from typing import Any

from app.services.spotify_service import get_user_top_items, search_tracks_by_artist


# -----------------------------------------------------------------------------
# UTILIDADES BÁSICAS
# -----------------------------------------------------------------------------
def _normalize(value: Any) -> str:
    """
    Normaliza texto para comparar nombres de artistas o valores de forma robusta.

    Convierte a string, limpia espacios y pasa a minúsculas.

    Ejemplo:
    " Myke Towers " -> "myke towers"
    """
    if value is None:
        return ""
    return str(value).strip().lower()


def _safe_float(value: Any) -> float | None:
    """
    Convierte un valor a float de forma segura.

    Devuelve None si el valor:
    - no existe
    - está vacío
    - no se puede convertir

    Se usa para features como:
    - energy
    - valence
    - danceability
    - instrumentalness
    """
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _track_text(track: dict) -> str:
    """
    Construye una versión textual simplificada del track.

    Une:
    - nombre de canción
    - artistas
    - labels
    - nombre de álbum

    Esta representación textual se usa para:
    - detectar patrones genéricos/artificiales
    - inferir si parece instrumental
    - detectar incompatibilidades por palabras
    """
    artists = " ".join(track.get("artists", []) or [])
    labels = " ".join(track.get("labels", []) or [])
    name = str(track.get("name", "") or "")
    album = str(track.get("album_name", "") or "")
    return f"{name} {artists} {labels} {album}".lower().strip()


def _instrumental_like(track: dict) -> bool:
    """
    Heurística para detectar si una canción parece instrumental.

    La canción se considera instrumental si:
    - tiene instrumentalness >= 0.58
    - o el texto contiene pistas como:
      instrumental, piano, ambient, classical, study, acoustic

    Esto es útil especialmente cuando el usuario busca:
    - foco
    - relajación
    - música instrumental explícitamente
    """
    instrumentalness = (
        _safe_float(track.get("audio_instrumentalness"))
        or _safe_float(track.get("instrumentalness"))
    )
    text = _track_text(track)

    if instrumentalness is not None and instrumentalness >= 0.58:
        return True

    hints = ["instrumental", "piano", "ambient", "classical", "soundscape"]
    return any(hint in text for hint in hints)


# -----------------------------------------------------------------------------
# CONSTRUCCIÓN DE CANDIDATOS PERSONALIZADOS
# -----------------------------------------------------------------------------
async def build_personalized_candidates(
    *,
    access_token: str,
    market: str = "ES",
    per_artist_limit: int = 10,
) -> tuple[list[dict], dict]:
    """
    Construye una bolsa de canciones personalizadas a partir del historial real
    del usuario en Spotify.

    Estrategia:
    1. Obtiene top tracks de corto plazo
    2. Obtiene top tracks de medio plazo
    3. Obtiene top artists de corto plazo
    4. Obtiene top artists de medio plazo
    5. Usa esas canciones y artistas para generar candidatos personalizados

    Devuelve:
    - candidates: canciones candidatas personalizadas
    - affinity_context: contexto de afinidad, que luego se usará para aplicar bonus

    Importante:
    esta función NO decide aún si las canciones son adecuadas para la sesión.
    Solo construye el conjunto de favoritos / afines del usuario.
    """
    top_tracks_short = await get_user_top_items(
        access_token=access_token,
        item_type="tracks",
        time_range="short_term",
        limit=12,
    )
    top_tracks_medium = await get_user_top_items(
        access_token=access_token,
        item_type="tracks",
        time_range="medium_term",
        limit=12,
    )
    top_artists_short = await get_user_top_items(
        access_token=access_token,
        item_type="artists",
        time_range="short_term",
        limit=10,
    )
    top_artists_medium = await get_user_top_items(
        access_token=access_token,
        item_type="artists",
        time_range="medium_term",
        limit=10,
    )

    # Unimos información reciente y algo más estable
    top_tracks = top_tracks_short + top_tracks_medium
    top_artists = top_artists_short + top_artists_medium

    # Guardamos IDs de top tracks para poder dar bonus luego
    top_track_ids = {
        track.get("id")
        for track in top_tracks
        if track.get("id")
    }

    # Construimos una lista única de artistas preferidos
    preferred_artist_names: list[str] = []
    seen_artist_names: set[str] = set()

    for artist in top_artists:
        name = artist.get("name")
        key = _normalize(name)
        if name and key and key not in seen_artist_names:
            seen_artist_names.add(key)
            preferred_artist_names.append(name)

    # También extraemos artistas desde los top tracks, por si no salieron en top_artists
    for track in top_tracks:
        for artist in track.get("artists_full", []):
            name = artist.get("name")
            key = _normalize(name)
            if name and key and key not in seen_artist_names:
                seen_artist_names.add(key)
                preferred_artist_names.append(name)

    candidates: list[dict] = []
    seen_track_ids: set[str] = set()

    def add_candidate(track: dict, affinity_source: str):
        """
        Añade un track a la lista de candidatos si no está repetido.

        Además deja marcada la fuente de afinidad:
        - user_top_track
        - artist_search:NombreArtista

        Esa fuente luego servirá para explicar por qué el sistema ha dado bonus.
        """
        track_id = track.get("id")
        if not track_id or track_id in seen_track_ids:
            return

        seen_track_ids.add(track_id)
        track["_affinity_source"] = affinity_source
        candidates.append(track)

    # Primero añadimos top tracks del propio usuario
    for track in top_tracks:
        add_candidate(track, "user_top_track")

    # Luego buscamos más canciones de artistas preferidos
    for artist_name in preferred_artist_names[:12]:
        try:
            tracks = await search_tracks_by_artist(
                access_token=access_token,
                artist_name=artist_name,
                limit=per_artist_limit,
                market=market,
            )
            for track in tracks:
                add_candidate(track, f"artist_search:{artist_name}")
        except Exception:
            # Si falla la búsqueda de un artista concreto, seguimos con los demás
            continue

    affinity_context = {
        "preferred_artist_names": preferred_artist_names,
        "top_track_ids": list(top_track_ids),
    }

    return candidates, affinity_context


# -----------------------------------------------------------------------------
# PESOS DE AFINIDAD PERSONAL
# -----------------------------------------------------------------------------
def _goal_affinity_weight(goal: str) -> float:
    """
    Ajusta cuánto debe pesar la afinidad personal según el objetivo de la sesión.

    Idea:
    - En relajación y foco, la afinidad personal debe pesar menos,
      porque importa más la funcionalidad emocional de la música.
    - En energía, puede pesar más, porque escuchar favoritos puede ayudar.
    """
    if goal == "relajacion":
        return 0.25
    if goal == "foco":
        return 0.35
    if goal == "energia":
        return 0.75
    return 0.50


def _desired_outcome_affinity_weight(desired_outcome: str | None) -> float:
    """
    Ajusta el peso de la afinidad según el resultado deseado.

    Ejemplo:
    - si el usuario quiere 'mas_centrado' o 'mas_calmado',
      la afinidad pesa algo menos que la funcionalidad
    - si quiere 'mas_animado' o 'mas_despierto',
      puede pesar algo más
    """
    if desired_outcome in {"mas_calmado", "mas_centrado"}:
        return 0.70
    if desired_outcome in {"mas_despierto", "mas_animado"}:
        return 0.85
    if desired_outcome in {"mas_ligero", "mas_acompanado"}:
        return 0.80
    return 1.0


def _mood_affinity_weight(mood: str) -> float:
    """
    Ajusta cuánto debe pesar la afinidad en función del mood.

    Si el usuario está:
    - triste o estresado -> reducimos un poco el peso de sus favoritos
    - feliz o neutral -> puede pesar más
    """
    if mood in {"estresado", "triste"}:
        return 0.75
    if mood == "cansado":
        return 0.85
    if mood in {"feliz", "neutral"}:
        return 1.0
    return 0.90


# -----------------------------------------------------------------------------
# BONUS DE AFINIDAD PERSONAL
# -----------------------------------------------------------------------------
def apply_personal_affinity_bonus(
    ranked_tracks: list[dict],
    affinity_context: dict,
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    exploration_preference: str,
) -> list[dict]:
    """
    Aplica bonus a canciones que:
    - ya están entre los top tracks del usuario
    - pertenecen a artistas preferidos
    - vienen directamente de la fuente user_top_track

    Importante:
    este bonus no es fijo.
    Se modula por:
    - goal
    - mood
    - desired_outcome
    - y por lo bien alineado que ya estaba el track con la sesión

    Así evitamos que "mis favoritos" destruyan la lógica emocional de la playlist.
    """
    preferred_artist_names = {
        _normalize(name)
        for name in affinity_context.get("preferred_artist_names", [])
        if name
    }
    top_track_ids = {
        track_id
        for track_id in affinity_context.get("top_track_ids", [])
        if track_id
    }

    goal_weight = _goal_affinity_weight(goal)
    outcome_weight = _desired_outcome_affinity_weight(desired_outcome)
    mood_weight = _mood_affinity_weight(mood)

    # Peso global de afinidad personal
    global_weight = goal_weight * outcome_weight * mood_weight

    if exploration_preference == "descubrir":
        global_weight *= 0.15
    elif exploration_preference == "equilibrado":
        global_weight *= 0.75

    for track in ranked_tracks:
        base_delta = 0.0
        reasons = list(track.get("reasons", track.get("_reasons", [])))

        track_id = track.get("id")
        artist_names = {
            _normalize(name)
            for name in track.get("artists", [])
            if name
        }

        # Bonus si esta canción está entre las más escuchadas del usuario
        if track_id in top_track_ids:
            base_delta += 4.0
            reasons.append("personal_affinity:top_track:+4")

        # Bonus si el track es de artistas preferidos
        if preferred_artist_names.intersection(artist_names):
            base_delta += 3.0
            reasons.append("personal_affinity:preferred_artist:+3")

        # Bonus extra si la fuente era directamente un top track del usuario
        affinity_source = track.get("_affinity_source")
        if affinity_source == "user_top_track":
            base_delta += 2.0
            reasons.append("personal_affinity:user_top_track_source:+2")

        heuristic_score = float(track.get("heuristic_score", track.get("_score", 0.0)))

        # El bonus de afinidad pesa más si la canción ya estaba bien alineada
        # con la sesión desde el ranking heurístico.
        if heuristic_score >= 28:
            alignment_weight = 1.00
        elif heuristic_score >= 22:
            alignment_weight = 0.80
        elif heuristic_score >= 16:
            alignment_weight = 0.60
        else:
            alignment_weight = 0.35

        final_delta = round(base_delta * global_weight * alignment_weight, 2)

        track["personal_affinity_delta"] = final_delta

        if final_delta > 0:
            reasons.append(f"personal_affinity:weighted:+{final_delta}")

        # Actualizamos score
        if "heuristic_score" in track:
            track["heuristic_score"] = (
                float(track.get("heuristic_score", 0.0)) + final_delta
            )

        current_score = float(track.get("_score", track.get("heuristic_score", 0.0)))
        track["_score"] = round(current_score + final_delta, 2)

        track["reasons"] = reasons
        track["_reasons"] = reasons

    ranked_tracks.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return ranked_tracks


# -----------------------------------------------------------------------------
# FILTRO DURO DE INCOMPATIBILIDAD PERSONALIZADA
# -----------------------------------------------------------------------------
def _is_clearly_incompatible(
    track: dict,
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    vocal_preference: str,
) -> tuple[bool, list[str]]:
    """
    Decide si un track personalizado es claramente incompatible con la sesión.

    Esta función es muy importante:
    evita que canciones favoritas del usuario entren solo por ser favoritas.

    Ejemplos de incompatibilidad:
    - demasiado baile para foco
    - demasiado tensa para relajación
    - demasiado oscura para energía cuando el usuario está triste
    - sin features fiables para una sesión donde necesitamos precisión
    """
    reasons: list[str] = []

    heuristic_score = float(track.get("heuristic_score", track.get("_score", 0.0)))
    energy = _safe_float(track.get("energy_feature")) or _safe_float(track.get("audio_energy"))
    valence = _safe_float(track.get("valence_feature")) or _safe_float(track.get("audio_valence"))
    danceability = _safe_float(track.get("danceability")) or _safe_float(track.get("audio_danceability"))
    instrumentalness = (
        _safe_float(track.get("instrumentalness"))
        or _safe_float(track.get("audio_instrumentalness"))
    )
    explicit = bool(track.get("explicit", False))
    text = _track_text(track)

    # Información semántica procedente del análisis textual
    text_profile = track.get("text_profile", {}) or {}
    tension = _safe_float(text_profile.get("tension")) or 0.0
    sadness = _safe_float(text_profile.get("sadness")) or 0.0
    uplift = _safe_float(text_profile.get("uplift")) or 0.0
    calm = _safe_float(text_profile.get("calm")) or 0.0
    focus = _safe_float(text_profile.get("focus")) or 0.0
    warmth = _safe_float(text_profile.get("warmth")) or 0.0

    affinity_source = track.get("_affinity_source")
    has_feature_source = bool(track.get("_feature_source"))

    # Si es personalizado pero parte de un score muy bajo, ya es una mala señal.
    if affinity_source and heuristic_score < 8:
        reasons.append("very_low_heuristic_for_personalized_track")

    # -------------------------------------------------------------------------
    # REGLAS DE RELAJACIÓN
    # -------------------------------------------------------------------------
    if goal == "relajacion":
        if heuristic_score < 12:
            reasons.append("low_heuristic_for_relax")
        if energy is not None and energy > 0.78:
            reasons.append("too_energetic_for_relax")
        if explicit:
            reasons.append("explicit_for_relax")
        if tension > 0.60:
            reasons.append("too_tense_for_relax")
        if any(x in text for x in ["gym", "workout", "party", "club", "hard", "trap", "drop"]):
            reasons.append("aggressive_text_for_relax")
        if desired_outcome == "mas_calmado" and energy is not None and energy > 0.65:
            reasons.append("too_intense_for_more_calm")
        if mood == "estresado" and tension > 0.45:
            reasons.append("stress_incompatible_text")

        # Si es personalizado y no tiene buen soporte de features,
        # la relajación pierde precisión -> lo penalizamos.
        if affinity_source and not has_feature_source:
            reasons.append("no_feature_source_for_relax_personalized_track")

    # -------------------------------------------------------------------------
    # REGLAS DE FOCO
    # -------------------------------------------------------------------------
    elif goal == "foco":
        if heuristic_score < 12:
            reasons.append("low_heuristic_for_focus")
        if energy is not None and energy > 0.82:
            reasons.append("too_energetic_for_focus")
        if explicit and heuristic_score < 18:
            reasons.append("explicit_for_focus")
        if danceability is not None and danceability > 0.72:
            reasons.append("too_danceable_for_focus")
        if tension > 0.55:
            reasons.append("too_tense_for_focus")
        if any(x in text for x in ["party", "club", "remix", "karaoke", "live", "gym", "workout"]):
            reasons.append("distracting_text_for_focus")
        if desired_outcome == "mas_centrado" and focus < 0.15 and calm < 0.15:
            reasons.append("low_focus_semantics")

        # Para foco exigimos más precisión acústica en candidatos personalizados.
        if affinity_source and (
            energy is None
            or valence is None
            or danceability is None
        ):
            reasons.append("missing_audio_features_for_focus_personalized_track")

        if affinity_source and not has_feature_source:
            reasons.append("no_feature_source_for_focus_personalized_track")

        if vocal_preference == "instrumental":
            if instrumentalness is not None and instrumentalness < 0.35:
                reasons.append("not_instrumental_enough_for_focus")
            elif instrumentalness is None and not _instrumental_like(track):
                reasons.append("not_instrumental_enough_for_focus")

    # -------------------------------------------------------------------------
    # REGLAS DE ENERGÍA
    # -------------------------------------------------------------------------
    elif goal == "energia":
        if heuristic_score < 14:
            reasons.append("low_heuristic_for_energy")

        if energy is not None and energy < 0.40:
            reasons.append("too_flat_for_energy")

        if desired_outcome in {"mas_despierto", "mas_animado"}:
            if energy is not None and energy < 0.50:
                reasons.append("not_enough_activation")
            if uplift < 0.30:
                reasons.append("low_uplift_for_activation")
            if valence is not None and valence < 0.38:
                reasons.append("low_valence_for_activation")

        if mood == "triste":
            if sadness > 0.55 and uplift < 0.35:
                reasons.append("too_heavy_for_sad_user_energy_goal")
            if valence is not None and valence < 0.42:
                reasons.append("too_dark_for_sad_user")

        if mood == "cansado":
            if energy is not None and energy < 0.45:
                reasons.append("too_low_energy_for_tired_user")
            if uplift < 0.25:
                reasons.append("not_gently_uplifting_for_tired_user")
            if energy is not None and energy > 0.90:
                reasons.append("too_abrupt_for_tired_user")
            if tension > 0.58 and uplift < 0.35:
                reasons.append("too_tense_for_tired_user")

        if any(x in text for x in ["sleep", "meditation", "whisper", "lullaby"]):
            reasons.append("too_sleepy_for_energy")

        if mood == "triste" and desired_outcome == "mas_acompanado":
            if sadness > 0.55 and uplift < 0.25 and warmth < 0.18:
                reasons.append("too_heavy_for_supported_energy")
            if tension > 0.58 and warmth < 0.18:
                reasons.append("too_harsh_for_supported_energy")
            if affinity_source and not has_feature_source and heuristic_score < 12:
                reasons.append("weak_supported_energy_evidence")

    # Si el usuario pidió instrumental para foco/relajación, reforzamos ese filtro.
    if vocal_preference == "instrumental" and goal in {"relajacion", "foco"}:
        if not _instrumental_like(track) and heuristic_score < 18:
            reasons.append("not_instrumental_enough")

    # Regla final:
    # si el track es personalizado y acumula al menos 2 razones graves,
    # lo consideramos incompatible y se elimina.
    if affinity_source and len(reasons) >= 2:
        return True, reasons

    return len(reasons) > 0, reasons


def _can_keep_soft_personalized_track(
    track: dict,
    *,
    goal: str,
    reasons: list[str],
) -> bool:
    """
    Permite conservar algunos favoritos conocidos cuando la evidencia es débil.

    Esto protege sesiones donde Spotify no devuelve bien features o
    recomendaciones y, aun así, el usuario ha pedido algo más cercano/familiar.
    """
    affinity_source = track.get("_affinity_source")
    if not affinity_source or goal != "energia" or not reasons:
        return False

    soft_reason_tokens = {
        "very_low_heuristic_for_personalized_track",
        "low_heuristic_for_energy",
        "low_uplift_for_activation",
        "low_valence_for_activation",
        "not_enough_activation",
    }
    blocking_reason_tokens = {
        "too_sleepy_for_energy",
        "too_dark_for_sad_user",
        "too_heavy_for_sad_user_energy_goal",
        "too_low_energy_for_tired_user",
        "too_abrupt_for_tired_user",
        "too_tense_for_tired_user",
    }

    reason_set = set(reasons)
    if reason_set.intersection(blocking_reason_tokens):
        return False

    if not reason_set.issubset(soft_reason_tokens):
        return False

    popularity = int(track.get("popularity", 0) or 0)
    return affinity_source == "user_top_track" or popularity >= 65


def filter_incompatible_personalized_tracks(
    ranked_tracks: list[dict],
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    vocal_preference: str,
    min_remaining: int = 20,
    allow_recovery: bool = True,
) -> tuple[list[dict], list[dict]]:
    """
    Elimina temporalmente canciones personalizadas incompatibles con la sesión.

    Solo filtra tracks con _affinity_source, es decir, los introducidos por afinidad.

    Devuelve dos listas:
    - kept: tracks conservados
    - removed: tracks personalizados eliminados temporalmente

    También incluye una lógica de recuperación parcial:
    si filtrar demasiado deja la bolsa muy pequeña, recupera algunos.
    """
    kept: list[dict] = []
    removed: list[dict] = []

    for track in ranked_tracks:
        affinity_source = track.get("_affinity_source")

        # Los tracks no personalizados no pasan por este filtro duro
        if not affinity_source:
            kept.append(track)
            continue

        incompatible, reasons = _is_clearly_incompatible(
            track,
            goal=goal,
            mood=mood,
            desired_outcome=desired_outcome,
            vocal_preference=vocal_preference,
        )

        if incompatible and _can_keep_soft_personalized_track(
            track,
            goal=goal,
            reasons=reasons,
        ):
            kept.append(track)
            continue

        if incompatible:
            track["_personal_filter_removed"] = True
            track["_personal_filter_reasons"] = reasons
            track["_personal_filter_penalty"] = len(reasons)
            removed.append(track)
        else:
            kept.append(track)

    # En contextos estrictos podemos preferir no reintroducir favoritos
    # incompatibles aunque la bolsa quede pequeña.
    if not allow_recovery:
        kept.sort(key=lambda x: x.get("_score", 0), reverse=True)
        removed.sort(key=lambda x: x.get("_personal_filter_penalty", 999))
        return kept, removed

    # Si aún quedan suficientes candidatos, devolvemos el filtro duro tal cual
    if len(kept) >= min_remaining:
        kept.sort(key=lambda x: x.get("_score", 0), reverse=True)
        removed.sort(key=lambda x: x.get("_personal_filter_penalty", 999))
        return kept, removed

    # Si nos hemos quedado demasiado cortos, recuperamos algunos de los menos graves
    removed_sorted = sorted(
        removed,
        key=lambda x: (
            x.get("_personal_filter_penalty", 999),
            -float(x.get("_score", 0)),
        ),
    )

    recovered: list[dict] = []
    current = list(kept)

    for track in removed_sorted:
        if len(current) >= min_remaining:
            break
        track["_personal_filter_recovered"] = True
        recovered.append(track)
        current.append(track)

    final_removed = [t for t in removed if t not in recovered]

    current.sort(key=lambda x: x.get("_score", 0), reverse=True)
    final_removed.sort(key=lambda x: x.get("_personal_filter_penalty", 999))

    return current, final_removed


# -----------------------------------------------------------------------------
# PENALIZACIÓN DE TÍTULOS GENÉRICOS / STOCK
# -----------------------------------------------------------------------------
def _generic_stock_penalty(track: dict) -> tuple[float, list[str]]:
    """
    Penaliza canciones con nombres que parecen demasiado funcionales, genéricos
    o propios de librerías de stock/producción.

    Ejemplos:
    - "background music"
    - "focus music"
    - "study music"
    - "brain waves"
    - "ambient session"

    Esto evita que la playlist se llene de contenido artificial o demasiado
    genérico cuando el fallback textual encuentra resultados poco musicales.
    """
    text = _track_text(track)
    penalty = 0.0
    reasons: list[str] = []

    strong_patterns = [
        "corporate",
        "corporate music",
        "corporate instrumental",
        "corporate motivational",
        "background music",
        "stock music",
        "production music",
        "motivational background",
        "uplifting motivational",
        "emotion pop",
        "zen music",
        "focus music",
        "focus playlist",
        "study music",
        "study playlist",
        "concentration music",
        "meditation music",
        "sleep music",
        "healing music",
        "relaxing music",
        "brain waves",
        "ambient session",
        "focus session",
        "bgm",
        "working bgm",
        "for studying",
        "study sounds",
        "focus sounds",
        "office work",
        "office beat",
        "office playlist",
        "music for work",
        "music to focus while working",
        "work music",
        "for work",
        "for working",
        "working music",
        "work concentration music",
        "work focus playlist",
        "music for office work",
        "motivational music for work",
        "office instrumentals",
        "work instrumentals",
        "musica para concentrarse",
        "para estudiar",
        "wellness",
        "wellness world",
        "neural activation",
        "chakra",
        "healing frequencies",
        "therapy music",
        "sound festival",
        "relax world",
        "temple of light",
        "temple",
        "zen k",
        "zen",
        "meditation",
        "spiritual",
        "background opener",
        "rock background opener",
    ]

    medium_patterns = [
        "gentle energy boost",
        "energy boost",
        "boost up",
        "uplifting",
        "motivational",
        "background",
        "ambient music",
        "soft instrumental",
        "calm music",
        "concentration",
        "focused melody",
        "minimal techno",
        "lofi",
        "lofi music",
        "motivational corporate",
        "office",
        "feel good",
        "good feeling",
        "light",
        "energy",
        "fresh",
        "vibes",
        "positive energy",
        "energy flow",
        "feelgood",
    ]

    for pattern in strong_patterns:
        if pattern in text:
            penalty += 7.0
            reasons.append(f"generic_stock:{pattern}:-7")

    for pattern in medium_patterns:
        if pattern in text:
            penalty += 3.0
            reasons.append(f"generic_stock:{pattern}:-3")

    if "music for" in text or "playlist for" in text:
        penalty += 5.0
        reasons.append("generic_stock:functional_phrase:-5")

    return penalty, reasons


def apply_generic_title_penalty(
    ranked_tracks: list[dict],
    *,
    goal: str | None = None,
    session_mode: str | None = None,
    desired_outcome: str | None = None,
) -> list[dict]:
    """
    Aplica la penalización por títulos genéricos.

    Si el track viene de afinidad personal, la penalización se suaviza,
    porque aunque el título sea raro, puede seguir siendo relevante para el usuario.
    """
    strict_functional_mode = goal == "energia" and (
        session_mode in {"steady_energy", "boost_energy"}
        or desired_outcome in {"mas_animado", "mas_despierto", "mas_ligero"}
    )

    for track in ranked_tracks:
        affinity_source = track.get("_affinity_source")
        reasons = list(track.get("reasons", track.get("_reasons", [])))
        title = _normalize(track.get("name", ""))

        penalty, penalty_reasons = _generic_stock_penalty(track)

        title_tokens = [token for token in title.replace("-", " ").split() if token]
        single_word_generic_titles = {
            "light",
            "energy",
            "fresh",
            "positive",
            "vibes",
            "presence",
        }
        airy_energy_titles = {
            "temple",
            "zen",
            "spirit",
            "spiritual",
            "meditation",
        }

        if len(title_tokens) == 1 and title_tokens[0] in single_word_generic_titles:
            penalty += 4.0
            penalty_reasons.append("generic_stock:single_word_title:-4")

        if (
            strict_functional_mode
            and any(token in airy_energy_titles for token in title_tokens)
        ):
            penalty += 5.0
            penalty_reasons.append("generic_stock:airy_energy_title:-5")

        if (
            strict_functional_mode
            and len(title_tokens) <= 2
            and any(token in {"light", "energy", "fresh", "positive"} for token in title_tokens)
        ):
            penalty += 3.0
            penalty_reasons.append("generic_stock:too_generic_energy_title:-3")

        if (
            strict_functional_mode
            and len(title_tokens) <= 4
            and any(
                token in {"background", "opener", "motivation", "boost", "flow"}
                for token in title_tokens
            )
        ):
            penalty += 4.0
            penalty_reasons.append("generic_stock:functional_energy_title:-4")

        if penalty <= 0:
            track["generic_title_penalty"] = 0.0
            track["reasons"] = reasons
            track["_reasons"] = reasons
            continue

        # Si el track viene por afinidad personal, reducimos la dureza
        if affinity_source:
            penalty *= 0.45
        else:
            penalty *= 1.00
            if strict_functional_mode and track.get("_fallback_query"):
                penalty *= 1.45
                penalty_reasons.append(
                    "generic_stock:strict_functional_mode_multiplier"
                )
            if strict_functional_mode and not track.get("_feature_source"):
                penalty += 5.0
                penalty_reasons.append("generic_stock:no_audio_features_strict_mode:-5")

        penalty = round(penalty, 2)
        track["generic_title_penalty"] = penalty

        reasons.extend(penalty_reasons)
        reasons.append(f"generic_title_penalty:-{penalty}")

        if "heuristic_score" in track:
            track["heuristic_score"] = float(track.get("heuristic_score", 0.0)) - penalty

        current_score = float(track.get("_score", track.get("heuristic_score", 0.0)))
        track["_score"] = round(current_score - penalty, 2)

        track["reasons"] = reasons
        track["_reasons"] = reasons

    ranked_tracks.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return ranked_tracks


def apply_semantic_evidence_bonus(
    ranked_tracks: list[dict],
    *,
    goal: str,
    session_mode: str | None = None,
    desired_outcome: str | None = None,
) -> list[dict]:
    """
    Prioriza tracks con buena señal semántica cuando faltan audio features.

    Esto ayuda a rescatar mejores candidatos textuales del fallback y a evitar
    que resultados muy genéricos sigan demasiado arriba solo por keywords.
    """
    strict_functional_mode = goal == "energia" and (
        session_mode in {"steady_energy", "boost_energy"}
        or desired_outcome in {"mas_animado", "mas_despierto", "mas_ligero"}
    )

    if not strict_functional_mode:
        return ranked_tracks

    for track in ranked_tracks:
        reasons = list(track.get("reasons", track.get("_reasons", [])))
        generic_penalty = _safe_float(track.get("generic_title_penalty")) or 0.0
        textual_delta = _safe_float(track.get("textual_semantic_delta")) or 0.0
        semantic_similarity = _safe_float(track.get("semantic_similarity")) or 0.0
        vector_similarity = _safe_float(track.get("vector_similarity")) or 0.0
        has_feature_source = bool(track.get("_feature_source"))
        has_personal_affinity = bool(track.get("_affinity_source"))
        fallback_query = track.get("_fallback_query")

        delta = 0.0

        if generic_penalty >= 8.0 and fallback_query and not has_feature_source:
            delta -= 1.25
            reasons.append("textual_alignment:stock_drag")
            if generic_penalty >= 12.0:
                delta -= 2.0
                reasons.append("textual_alignment:hard_stock_drag")
        else:
            if fallback_query and textual_delta >= 6.0:
                delta += 1.75
                reasons.append("textual_alignment:functional_semantic_bonus")
            elif fallback_query and semantic_similarity >= 0.12:
                delta += 1.0
                reasons.append("textual_alignment:functional_semantic_support")

            if (
                not has_feature_source
                and vector_similarity >= 0.45
                and generic_penalty <= 4.0
            ):
                delta += 0.75
                reasons.append("textual_alignment:vector_support_bonus")

            if (
                not has_feature_source
                and semantic_similarity >= 0.16
                and generic_penalty <= 6.0
            ):
                delta += 0.5
                reasons.append("textual_alignment:semantic_similarity_bonus")

        if has_personal_affinity and delta > 0:
            delta *= 0.65
            reasons.append("textual_alignment:personalized_cap")

        if delta != 0.0:
            track["textual_alignment_delta"] = round(delta, 2)
            if "heuristic_score" in track:
                track["heuristic_score"] = round(
                    float(track.get("heuristic_score", 0.0)) + delta,
                    2,
                )
            current_score = float(track.get("_score", track.get("heuristic_score", 0.0)))
            track["_score"] = round(current_score + delta, 2)
            track["reasons"] = reasons
            track["_reasons"] = reasons

    ranked_tracks.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return ranked_tracks


# -----------------------------------------------------------------------------
# PENALIZACIÓN DE TRACKS QUE VIENEN SOLO DE FALLBACK DE BÚSQUEDA
# -----------------------------------------------------------------------------
def apply_fallback_source_penalty(
    ranked_tracks: list[dict],
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    exploration_preference: str,
    popularity_preference: str,
) -> list[dict]:
    """
    Penaliza canciones que solo han entrado por búsquedas fallback genéricas
    y no por afinidad personal.

    Idea:
    si una canción aparece simplemente porque buscábamos textos como
    "deep focus instrumental" o "gentle energy boost", no queremos que compita
    de igual a igual con canciones más ricas o más personalizadas.
    """
    for track in ranked_tracks:
        fallback_query = track.get("_fallback_query")
        affinity_source = track.get("_affinity_source")

        # Solo penalizamos fallback puro; si es personal, no lo tocamos aquí
        if not fallback_query or affinity_source:
            track["fallback_source_penalty"] = 0.0
            continue

        reasons = list(track.get("reasons", track.get("_reasons", [])))
        penalty = 0.0
        query = str(fallback_query).lower()
        popularity = int(track.get("popularity", 0) or 0)
        has_feature_source = bool(track.get("_feature_source"))

        # Penalización base por ser resultado fallback
        penalty += 1.5

        # En energía para usuarios tristes/cansados, nos ponemos un poco más estrictos
        if goal == "energia" and mood in {"triste", "cansado"}:
            penalty += 1.0

        if desired_outcome in {"mas_despierto", "mas_animado"}:
            penalty += 0.5

        generic_queries = {
            "uplifting motivation",
            "gentle energy boost",
            "feel good upbeat",
            "feel good soft pop",
            "deep focus instrumental",
            "study ambient",
            "stress relief ambient",
            "calm piano relax",
            "awake focus instrumental",
            "clear head concentration",
            "steady study beats",
            "alert study music",
        }
        if query in generic_queries:
            penalty += 1.0

        if not has_feature_source:
            penalty += 1.0
            if goal == "energia":
                penalty += 0.5
            if desired_outcome in {"mas_despierto", "mas_animado", "mas_ligero"}:
                penalty += 0.5

        if exploration_preference == "familiar" and not has_feature_source:
            penalty += 1.5

        if popularity_preference == "mainstream":
            if popularity < 20:
                penalty += 4.0
            elif popularity < 35:
                penalty += 2.5

            if not has_feature_source and popularity < 50:
                penalty += 1.5

        penalty = round(penalty, 2)
        track["fallback_source_penalty"] = penalty

        if penalty > 0:
            reasons.append(f"fallback_source_penalty:-{penalty}")

            if "heuristic_score" in track:
                track["heuristic_score"] = (
                    float(track.get("heuristic_score", 0.0)) - penalty
                )

            current_score = float(
                track.get("_score", track.get("heuristic_score", 0.0))
            )
            track["_score"] = round(current_score - penalty, 2)

        track["reasons"] = reasons
        track["_reasons"] = reasons

    ranked_tracks.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return ranked_tracks


# -----------------------------------------------------------------------------
# RECUPERACIÓN SUAVE DE TRACKS PERSONALIZADOS
# -----------------------------------------------------------------------------
def recover_soft_personalized_tracks(
    ranked_tracks: list[dict],
    removed_tracks: list[dict],
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    exploration_preference: str = "equilibrado",
    top_window: int = 8,
    max_recover: int = 3,
) -> list[dict]:
    """
    Recupera de forma suave algunos tracks personalizados que fueron filtrados,
    si el top final ha quedado demasiado poco personalizado.

    Objetivo:
    - no perder del todo el sello personal del usuario
    - pero sin reintroducir tracks claramente peligrosos o incoherentes

    La recuperación es limitada y controlada:
    - como mucho max_recover tracks
    - no recupera los que tienen razones graves/fatales
    """
    if not removed_tracks:
        return ranked_tracks

    if exploration_preference == "descubrir":
        return ranked_tracks

    current_top = ranked_tracks[:top_window]
    personalized_in_top = sum(1 for t in current_top if t.get("_affinity_source"))

    # Queremos un mínimo de personalización:
    # - energía: al menos 2 tracks personalizados en top
    # - foco/relajación: al menos 1
    target_personalized = 2 if goal == "energia" else 1
    if personalized_in_top >= target_personalized:
        return ranked_tracks

    fatal_reason_tokens = {
        "too_sleepy_for_energy",
        "too_dark_for_sad_user",
        "too_tense_for_safe_energy_mode",
        "aggressive_text_for_relax",
        "distracting_text_for_focus",
        "very_low_heuristic_for_personalized_track",
        "missing_audio_features_for_focus_personalized_track",
        "no_feature_source_for_focus_personalized_track",
    }

    eligible: list[dict] = []
    for track in removed_tracks:
        reasons = set(track.get("_personal_filter_reasons", []) or [])
        penalty_count = int(track.get("_personal_filter_penalty", len(reasons)))

        # Si tiene demasiadas razones negativas, no se recupera
        if penalty_count > 2:
            continue

        # Si tiene razones fatales, no se recupera
        if reasons.intersection(fatal_reason_tokens):
            continue

        score = float(track.get("_score", track.get("heuristic_score", 0.0)))
        if goal == "energia" and score < 8:
            continue
        if goal in {"relajacion", "foco"} and score < 10:
            continue

        eligible.append(track)

    if not eligible:
        return ranked_tracks

    ranked_tracks.sort(key=lambda x: x.get("_score", 0), reverse=True)
    floor_index = min(len(ranked_tracks) - 1, max(0, top_window - 1))
    floor_score = float(ranked_tracks[floor_index].get("_score", 0.0))

    recovered_count = 0
    for track in sorted(
        eligible,
        key=lambda x: (
            x.get("_personal_filter_penalty", 999),
            -float(x.get("_score", 0.0)),
        ),
    ):
        if recovered_count >= max_recover:
            break

        current_score = float(track.get("_score", track.get("heuristic_score", 0.0)))
        needed_delta = max(0.8, min(3.0, floor_score - current_score + 1.0))

        reasons = list(track.get("reasons", track.get("_reasons", [])))
        reasons.append(f"soft_personal_recovery:+{round(needed_delta, 2)}")

        track["soft_personal_recovery_delta"] = round(needed_delta, 2)
        track["_soft_personal_recovered"] = True
        track["_score"] = round(current_score + needed_delta, 2)

        if "heuristic_score" in track:
            track["heuristic_score"] = (
                float(track.get("heuristic_score", 0.0)) + needed_delta
            )

        track["reasons"] = reasons
        track["_reasons"] = reasons

        if track not in ranked_tracks:
            ranked_tracks.append(track)

        recovered_count += 1

    ranked_tracks.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return ranked_tracks
