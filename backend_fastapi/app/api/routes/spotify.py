import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel

from app.services.firestore_service import get_firestore_client
from app.services.dataset_recommendation_service import select_dataset_candidates
from app.services.in_memory_store import recommendations_store
from app.services.personalized_playlist_generation_service import (
    apply_fallback_source_penalty,
    apply_generic_title_penalty,
    apply_personal_affinity_bonus,
    apply_semantic_evidence_bonus,
    build_personalized_candidates,
    filter_incompatible_personalized_tracks,
    recover_soft_personalized_tracks,
)
from app.services.spotify_track_matching_service import (
    materialize_ranked_tracks_for_spotify,
)
from app.services.professional_playlist_model_service import (
    assemble_playlist,
    build_generation_profile,
    rank_candidate_tracks,
)
from app.services.session_mode_ml_service import (
    model_available as session_mode_model_available,
)
from app.services.spotify_service import (
    add_items_to_playlist,
    create_authorize_url,
    create_playlist,
    exchange_code_for_token,
    refresh_access_token,
    get_recommendations,
    get_spotify_profile,
    get_user_playlists,
    search_tracks,
)
from app.services.track_feature_upsert_service import (
    upsert_track_features_from_tracks,
)

router = APIRouter()

# Versión final entregable:
# - `msd_tracks` actúa como fuente real de candidatos y features
# - Spotify solo se usa para autenticar, crear playlists y materializar URIs
USE_SPOTIFY_AFFINITY_SUPPORT = False
USE_SPOTIFY_FALLBACK_SEARCHES = False
USE_SPOTIFY_RESCUE_RECOMMENDATIONS = False


# -----------------------------------------------------------------------------
# SCHEMAS DE ENTRADA
# -----------------------------------------------------------------------------
class SpotifyExchangeRequest(BaseModel):
    code: str
    state: str


class SpotifyProfileRequest(BaseModel):
    access_token: str


class SpotifyRefreshRequest(BaseModel):
    refresh_token: str


class SpotifyPlaylistsRequest(BaseModel):
    access_token: str


class SpotifyGeneratePlaylistRequest(BaseModel):
    """
    Variables que el usuario manda al backend para generar una playlist
    personalizada.
    """
    access_token: str
    goal: str
    mood: str
    stress_level: int
    energy_level: int
    noise_category: str
    recommendation_id: str | None = None
    recommendation_title: str | None = None
    vocal_preference: str = "indistinto"
    intensity_preference: str = "media"
    exploration_preference: str = "equilibrado"
    popularity_preference: str = "mixta"
    session_duration_min: int = 20
    desired_outcome: str | None = None
    environment_context: str | None = None
    environment_variability: float | None = None
    environment_peak_delta: float | None = None
    environment_confidence: float | None = None
    transient_ratio: float | None = None
    burst_count: int | None = None
    use_environment: bool = True


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------
def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _build_materialization_error_message(match_stats: dict[str, Any]) -> str:
    if match_stats.get("rate_limited") is True:
        return (
            "Spotify está limitando temporalmente las búsquedas de canciones. "
            "Espera un poco y vuelve a intentarlo."
        )

    fresh_matches = int(match_stats.get("fresh_matches", 0) or 0)
    cached_matches = int(match_stats.get("cached_matches", 0) or 0)
    searches = int(match_stats.get("searches", 0) or 0)
    failed_matches = int(match_stats.get("failed_matches", 0) or 0)

    return (
        "No se pudieron materializar canciones del catálogo en Spotify. "
        f"búsquedas={searches}, coincidencias_nuevas={fresh_matches}, "
        f"coincidencias_cacheadas={cached_matches}, fallos={failed_matches}"
    )


def _track_text(track: dict) -> str:
    """
    Representación textual simple del track:
    nombre + artistas + labels.
    """
    name = str(track.get("name", "") or "")
    artists = " ".join(track.get("artists", []) or [])
    labels = " ".join(track.get("labels", []) or [])
    return f"{name} {artists} {labels}".lower().strip()


def _find_recommendation_entry(
    recommendation_id: str | None,
    recommendation_title: str | None,
) -> dict | None:
    """
    Recupera la recomendación original asociada a la generación de playlist.

    Es la pieza que enlaza la capa de recomendación con la capa de Spotify para
    poder reutilizar `recommended_mode`, `recommendation_id` y luego cerrar bien
    el ciclo de feedback y entrenamiento.
    """
    for item in reversed(recommendations_store):
        if recommendation_id and item.get("recommendation_id") == recommendation_id:
            return item
        if recommendation_title and item.get("title") == recommendation_title:
            return item

    try:
        db = get_firestore_client()
        recommendation_data: dict | None = None

        if recommendation_id:
            docs = (
                db.collection("recommendations")
                .where(filter=FieldFilter("recommendation_id", "==", recommendation_id))
                .limit(1)
                .stream()
            )
            for doc in docs:
                recommendation_data = doc.to_dict() or {}
                break
        elif recommendation_title:
            docs = (
                db.collection("recommendations")
                .where(filter=FieldFilter("title", "==", recommendation_title))
                .limit(1)
                .stream()
            )
            for doc in docs:
                recommendation_data = doc.to_dict() or {}
                break

        if not recommendation_data:
            return None

        if recommendation_id:
            playlist_docs = (
                db.collection("generated_playlists")
                .where(filter=FieldFilter("recommendation_id", "==", recommendation_id))
                .limit(1)
                .stream()
            )
            for doc in playlist_docs:
                playlist_data = doc.to_dict() or {}
                if playlist_data.get("selected_tracks"):
                    recommendation_data["selected_tracks"] = playlist_data.get("selected_tracks")
                recommendation_data["generation_mode"] = playlist_data.get(
                    "generation_mode",
                    recommendation_data.get("generation_mode"),
                )
                recommendation_data["spotify_user_id"] = playlist_data.get(
                    "spotify_user_id",
                    recommendation_data.get("spotify_user_id"),
                )
                break

        return recommendation_data
    except Exception:
        return None
    return None


def _track_has_functional_evidence(track: dict, goal: str) -> bool:
    """
    Comprueba si una canción tiene evidencia funcional de servir para el objetivo.
    """
    labels = {str(x).lower() for x in (track.get("labels", []) or []) if x}
    text = _track_text(track)

    bpm = _safe_float(track.get("bpm"))
    danceability = _safe_float(track.get("danceability"))
    instrumentalness = _safe_float(track.get("instrumentalness"))
    energy = _safe_float(track.get("energy_feature"))
    valence = _safe_float(track.get("valence_feature"))

    if goal == "foco":
        if labels.intersection({"focus", "study", "ambient", "instrumental", "deep", "calm"}):
            return True
        if any(
            token in text
            for token in ["focus", "study", "ambient", "instrumental", "piano"]
        ):
            return True
        if instrumentalness is not None and instrumentalness >= 0.45:
            return True
        if (
            bpm is not None
            and 55 <= bpm <= 100
            and (danceability is None or danceability <= 0.65)
        ):
            return True
        return False

    if goal == "relajacion":
        if labels.intersection({"relax", "calm", "ambient", "instrumental", "chill"}):
            return True
        if any(
            token in text
            for token in ["relax", "calm", "ambient", "chill", "piano"]
        ):
            return True
        if instrumentalness is not None and instrumentalness >= 0.45:
            return True
        if energy is not None and energy <= 0.45:
            return True
        return False

    if goal == "energia":
        if labels.intersection({"energy", "upbeat", "motivation", "dance"}):
            return True
        if any(
            token in text
            for token in ["energy", "upbeat", "motivation", "dance", "boost"]
        ):
            return True
        if energy is not None and energy >= 0.58:
            return True
        if valence is not None and valence >= 0.52:
            return True
        return False

    return False


def _session_mode_requires_functional_alignment(
    goal: str,
    session_mode: str | None,
    desired_outcome: str | None,
) -> bool:
    """
    Decide cuándo el generador debe respetar con más fuerza el modo de sesión.

    Ahora mismo se activa sobre todo en sesiones de energía, donde un modo como
    `steady_energy` o `boost_energy` no debería degradarse en una playlist que
    solo refleje afinidad histórica del usuario.
    """
    if goal != "energia":
        return False

    normalized_mode = str(session_mode or "").strip().lower()

    # Modos antiguos del catálogo.
    if normalized_mode in {"steady_energy", "boost_energy"}:
        return True

    # Modos dinámicos nuevos, por ejemplo `energia_feliz_alta`.
    if normalized_mode.startswith("energia_"):
        return True

    # Algunos resultados deseados también necesitan proteger la intención
    # funcional aunque el nombre del modo no venga de un catálogo fijo.
    return desired_outcome in {"mas_animado", "mas_despierto", "mas_ligero"}


def _apply_session_mode_alignment_guard(
    ranked_tracks: list[dict],
    *,
    goal: str,
    session_mode: str | None,
    desired_outcome: str | None,
) -> list[dict]:
    """
    Refuerza que la playlist final refleje el modo de sesión elegido.

    En energía, si el modo lo decidió el ML (`steady_energy` o `boost_energy`),
    no queremos que el top quede dominado por favoritos sin evidencia funcional.
    """
    if not _session_mode_requires_functional_alignment(
        goal,
        session_mode,
        desired_outcome,
    ):
        return ranked_tracks

    for track in ranked_tracks:
        reasons = list(track.get("reasons", track.get("_reasons", [])))
        delta = 0.0
        has_functional_evidence = _track_has_functional_evidence(track, goal)
        has_personal_affinity = bool(track.get("_affinity_source"))
        has_feature_source = bool(track.get("_feature_source"))
        fallback_query = track.get("_fallback_query")

        if has_functional_evidence:
            if fallback_query:
                delta += 4.0
                reasons.append("session_mode_alignment:functional_fallback_bonus")
            else:
                delta += 2.5
                reasons.append("session_mode_alignment:functional_bonus")
        elif has_personal_affinity:
            delta -= 4.0
            reasons.append("session_mode_alignment:weak_personalized_penalty")
            if not has_feature_source:
                delta -= 2.0
                reasons.append("session_mode_alignment:no_feature_support_penalty")
        elif not has_feature_source:
            delta -= 1.5
            reasons.append("session_mode_alignment:weak_energy_evidence_penalty")

        if delta != 0.0:
            track["session_mode_alignment_delta"] = round(delta, 2)
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


def _needs_functional_reinforcement(
    ranked_tracks: list[dict],
    *,
    goal: str,
    session_mode: str | None,
    desired_outcome: str | None,
) -> bool:
    """
    Decide si el ranking necesita una segunda ronda de refuerzo funcional.
    """
    top = ranked_tracks[:5]
    if not top:
        return False

    personalized_top = sum(1 for t in top if t.get("_affinity_source"))
    functional_top = sum(1 for t in top if _track_has_functional_evidence(t, goal))
    feature_backed_top = sum(1 for t in top if t.get("_feature_source"))

    if goal in {"foco", "relajacion"}:
        return personalized_top >= 3 or functional_top <= 1 or feature_backed_top <= 1

    if _session_mode_requires_functional_alignment(goal, session_mode, desired_outcome):
        return personalized_top >= 3 or functional_top <= 1 or feature_backed_top == 0

    return False


def _is_weak_playlist_ranking(
    ranked_tracks: list[dict],
    *,
    goal: str,
    desired_outcome: str | None,
) -> bool:
    """
    Detecta cuándo el ranking ha quedado demasiado flojo como para confiar
    en la primera bolsa de candidatos.
    """
    top = ranked_tracks[:5]
    if not top:
        return True

    top_scores = [float(t.get("_score", 0.0) or 0.0) for t in top]
    top1 = top_scores[0]
    top3_avg = sum(top_scores[:3]) / max(1, min(3, len(top_scores)))
    negative_top = sum(1 for score in top_scores if score < 0)
    functional_top = sum(1 for t in top if _track_has_functional_evidence(t, goal))
    fallback_top = sum(1 for t in top if t.get("_fallback_query"))

    if top1 < 8.0:
        return True
    if top3_avg < 6.5:
        return True
    if negative_top >= 2:
        return True

    if goal == "energia" and desired_outcome in {"mas_despierto", "mas_animado", "mas_ligero"}:
        if functional_top <= 1:
            return True
        if fallback_top >= 4 and top3_avg < 9.0:
            return True

    return False


def _build_rescue_queries(
    *,
    goal: str,
    mood: str,
    intensity_preference: str,
    desired_outcome: str | None,
    exploration_preference: str,
    popularity_preference: str,
) -> list[str]:
    """
    Queries alternativas más musicales para rescatar rankings débiles.
    """
    if goal == "energia":
        if mood == "triste" and desired_outcome == "mas_acompanado":
            return [
                "popular comforting pop",
                "warm familiar pop",
                "known uplifting latin pop",
                "soft emotional pop hits",
            ]
        if (
            popularity_preference == "mainstream"
            or exploration_preference == "familiar"
        ):
            return [
                "popular upbeat pop",
                "famous feel good pop",
                "hit positive pop",
                "known uplifting pop",
            ]
        if mood == "cansado" and intensity_preference == "suave":
            return [
                "warm uplifting pop",
                "gentle wake up indie",
                "bright feel good pop",
                "soft upbeat pop",
            ]
        if desired_outcome in {"mas_despierto", "mas_animado"}:
            return [
                "uplifting indie pop",
                "bright pop energy",
                "feel good dance pop",
                "warm upbeat motivation",
            ]
        return [
            "positive indie pop",
            "light pop energy",
            "upbeat feel good pop",
            "bright soft dance",
        ]

    if goal == "foco":
        return [
            "deep focus instrumental",
            "steady concentration instrumental",
            "minimal study piano",
            "clear mind ambient",
        ]

    if goal == "relajacion":
        return [
            "calm ambient piano",
            "gentle relaxation instrumental",
            "soft evening acoustic",
            "warm quiet ambient",
        ]

    return []


def _merge_tracks(
    *,
    candidate_tracks: list[dict],
    new_tracks: list[dict],
    seen_uris: set[str],
    fallback_query: str | None = None,
) -> int:
    """
    Une nuevas canciones a la bolsa de candidatos evitando duplicados por URI.
    """
    added = 0
    for track in new_tracks:
        uri = track.get("uri")
        if not uri or uri in seen_uris:
            continue

        seen_uris.add(uri)
        if fallback_query:
            track["_fallback_query"] = fallback_query
        candidate_tracks.append(track)
        added += 1

    return added


def _estimate_required_match_count(target_duration_ms: int) -> int:
    """
    Estima cuántos tracks conviene materializar en Spotify antes de ensamblar.

    No buscamos solo el mínimo exacto, sino una bolsa algo mayor para que
    `assemble_playlist` pueda deduplicar y limitar artistas sin quedarse corta.
    """
    rough_track_count = max(8, min(42, int(target_duration_ms / 210000) + 4))
    return max(12, rough_track_count)


def _rank_pipeline(
    *,
    candidate_tracks: list[dict],
    affinity_context: dict,
    generation_profile: dict,
    payload: SpotifyGeneratePlaylistRequest,
    session_mode: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """
    Ejecuta el pipeline heurístico completo de ranking de canciones.

    Aquí se combinan, en orden:
    - compatibilidad musical con la sesión
    - afinidad personal
    - penalizaciones por títulos genéricos o fuentes fallback
    - refuerzo semántico
    - guardas para que el resultado respete el modo elegido por el sistema
    """
    heuristic_ranked_tracks = rank_candidate_tracks(
        tracks=candidate_tracks,
        profile=generation_profile,
        goal=payload.goal,
        mood=payload.mood,
        desired_outcome=payload.desired_outcome,
    )

    removed_personal_tracks: list[dict] = [] 

    if affinity_context:
        strict_personal_filter = (
            payload.exploration_preference == "descubrir"
            or (
                payload.vocal_preference == "instrumental"
                and payload.goal in {"foco", "relajacion"}
            )
        )
        heuristic_ranked_tracks, removed_personal_tracks = ( 
            filter_incompatible_personalized_tracks(
                heuristic_ranked_tracks,
                goal=payload.goal,
                mood=payload.mood,
                desired_outcome=payload.desired_outcome,
                vocal_preference=payload.vocal_preference,
                min_remaining=20,
                allow_recovery=not strict_personal_filter,
            )
        )

        heuristic_ranked_tracks = apply_personal_affinity_bonus(
            heuristic_ranked_tracks,
            affinity_context,
            goal=payload.goal,
            mood=payload.mood,
            desired_outcome=payload.desired_outcome,
            exploration_preference=payload.exploration_preference,
        )

    heuristic_ranked_tracks = apply_generic_title_penalty(
        heuristic_ranked_tracks,
        goal=payload.goal,
        session_mode=session_mode,
        desired_outcome=payload.desired_outcome,
    )

    heuristic_ranked_tracks = apply_fallback_source_penalty(
        heuristic_ranked_tracks,
        goal=payload.goal,
        mood=payload.mood,
        desired_outcome=payload.desired_outcome,
        exploration_preference=payload.exploration_preference,
        popularity_preference=payload.popularity_preference,
    )

    heuristic_ranked_tracks = apply_semantic_evidence_bonus(
        heuristic_ranked_tracks,
        goal=payload.goal,
        session_mode=session_mode,
        desired_outcome=payload.desired_outcome,
    )

    heuristic_ranked_tracks = recover_soft_personalized_tracks(
        heuristic_ranked_tracks,
        removed_personal_tracks,
        goal=payload.goal,
        mood=payload.mood,
        desired_outcome=payload.desired_outcome,
        exploration_preference=payload.exploration_preference,
        top_window=8,
        max_recover=3,
    )

    heuristic_ranked_tracks = _apply_session_mode_alignment_guard(
        heuristic_ranked_tracks,
        goal=payload.goal,
        session_mode=session_mode,
        desired_outcome=payload.desired_outcome,
    )

    return heuristic_ranked_tracks, removed_personal_tracks


def _attach_generated_context_to_recommendation(
    recommendation_id: str | None,
    recommendation_title: str | None,
    spotify_user_id: str,
    use_environment: bool,
    goal: str,
    mood: str,
    stress_level: int,
    energy_level: int,
    noise_category: str | None,
    vocal_preference: str,
    intensity_preference: str,
    exploration_preference: str,
    popularity_preference: str,
    session_duration_min: int,
    desired_outcome: str | None,
    environment_context: str | None,
    environment_variability: float | None,
    environment_peak_delta: float | None,
    environment_confidence: float | None,
    transient_ratio: float | None,
    burst_count: int | None,
    generation_mode: str,
    session_subtype: str | None,
    activation_curve: str | None, 
    selected_tracks: list[dict],
) -> None:
    """
    Persiste el contexto completo de generación dentro de la recomendación.

    Este paso es clave porque deja un único objeto enlazado con:
    - la recomendación original
    - el resultado de Spotify
    - los tracks realmente usados
    - el contexto final que luego consumirá el feedback y el entrenamiento
    """
    recommendation_item = _find_recommendation_entry(
        recommendation_id,
        recommendation_title,
    )
    if not recommendation_item:
        return

    # Backend no recibe el UID de Firebase en este flujo, así que persistimos
    # el identificador estable disponible para que feedback y ML no queden cojos.
    recommendation_item["user_id"] = spotify_user_id
    recommendation_item["spotify_user_id"] = spotify_user_id
    recommendation_item["use_environment"] = use_environment
    recommendation_item["goal"] = goal
    recommendation_item["mood"] = mood
    recommendation_item["stress_level"] = stress_level
    recommendation_item["energy_level"] = energy_level
    recommendation_item["noise_category"] = noise_category
    recommendation_item["vocal_preference"] = vocal_preference
    recommendation_item["intensity_preference"] = intensity_preference
    recommendation_item["exploration_preference"] = exploration_preference
    recommendation_item["popularity_preference"] = popularity_preference
    recommendation_item["session_duration_min"] = session_duration_min
    recommendation_item["desired_outcome"] = desired_outcome
    recommendation_item["environment_context"] = environment_context
    recommendation_item["environment_variability"] = environment_variability
    recommendation_item["environment_peak_delta"] = environment_peak_delta
    recommendation_item["environment_confidence"] = environment_confidence
    recommendation_item["transient_ratio"] = transient_ratio
    recommendation_item["burst_count"] = burst_count
    recommendation_item["generation_mode"] = generation_mode
    recommendation_item["session_subtype"] = session_subtype
    recommendation_item["activation_curve"] = activation_curve
    recommendation_item["selected_tracks"] = [
        {
            "id": track.get("id"),
            "catalog_track_id": track.get("catalog_track_id"),
            "msd_track_id": track.get("msd_track_id"),
            "name": track.get("name"),
            "artists": track.get("artists", []),
            "popularity": track.get("popularity", 0),
            "duration_ms": track.get("duration_ms", 0),
            "explicit": track.get("explicit", False),
            "bpm": track.get("bpm"),
            "danceability": track.get("danceability"),
            "energy_feature": track.get("energy_feature"),
            "valence_feature": track.get("valence_feature"),
            "instrumentalness": track.get("instrumentalness"),
            "acousticness": track.get("acousticness"),
            "speechiness": track.get("speechiness"),
            "liveness": track.get("liveness"),
            "heuristic_score": track.get(
                "heuristic_score",
                track.get("_score", 0),
            ),
            "_score": track.get("_score", track.get("heuristic_score", 0)),
            "_reasons": track.get("_reasons", track.get("reasons", [])),
            "desired_outcome_delta": track.get("desired_outcome_delta"),
            "environment_delta": track.get("environment_delta"),
            "textual_semantic_delta": track.get("textual_semantic_delta"),
            "vector_similarity": track.get("vector_similarity"),
            "vector_similarity_delta": track.get("vector_similarity_delta"),
            "personal_affinity_delta": track.get("personal_affinity_delta"),
            "generic_title_penalty": track.get("generic_title_penalty"),
            "fallback_source_penalty": track.get("fallback_source_penalty"),
            "soft_personal_recovery_delta": track.get(
                "soft_personal_recovery_delta"
            ),
            "session_subtype_delta": track.get("session_subtype_delta"),
            "lyrics_available": track.get("lyrics_available"),
            "description_available": track.get("description_available"),
            "text_profile": track.get("text_profile"),
            "sentiment_label": track.get("sentiment_label"),
            "sentiment_score": track.get("sentiment_score"),
            "semantic_similarity": track.get("semantic_similarity"),
            "text_source_preview": track.get("text_source_preview"),
            "spotify_track_id": track.get("spotify_track_id"),
            "spotify_uri": track.get("spotify_uri"),
            "spotify_match": track.get("spotify_match"),
            "_feature_source": track.get("_feature_source"),
            "_feature_match": track.get("_feature_match"),
            "_affinity_source": track.get("_affinity_source"),
            "_fallback_query": track.get("_fallback_query"),
        }
        for track in selected_tracks
    ]


async def _run_fallback_searches(
    access_token: str,
    queries: list[str],
    market: str,
) -> list[list[dict]]:
    """
    Ejecuta varias búsquedas fallback con ritmo conservador para reducir 429.
    """
    results: list[list[dict] | Exception] = []
    for index, query in enumerate(queries):
        try:
            result = await search_tracks(access_token, query, limit=5, market=market)
            results.append(result)
        except Exception as exc:
            results.append(exc)

        if index < len(queries) - 1:
            await asyncio.sleep(0.35)

    return results


# -----------------------------------------------------------------------------
# ENDPOINTS BÁSICOS DE SPOTIFY
# -----------------------------------------------------------------------------
@router.get("/login-url")
async def spotify_login_url():
    """
    Inicia el flujo OAuth de Spotify devolviendo la URL de autorización.
    """
    try:
        result = create_authorize_url()
        print("\n[AUTH] login_url_created")
        print("authorize_url:", result.get("authorize_url"))
        print("state:", result.get("state"))
        return result
    except Exception as e:
        print("\n[AUTH ERROR] login_url:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exchange")
async def spotify_exchange(payload: SpotifyExchangeRequest):
    """
    Intercambia el código OAuth por un access token de Spotify.
    """
    try:
        print("\n[AUTH] exchange_received")
        print("code (primeros 12):", payload.code[:12] if payload.code else None)
        print("state:", payload.state)

        token_data = await exchange_code_for_token(payload.code, payload.state)

        print("[AUTH] token_obtained")
        print("access_token (primeros 20):", token_data.get("access_token", "")[:20])
        print("scope:", token_data.get("scope"))
        print("token_type:", token_data.get("token_type"))
        print("expires_in:", token_data.get("expires_in"))

        return token_data
    except Exception as e:
        print("\n[AUTH ERROR] exchange:", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me")
async def spotify_me(payload: SpotifyProfileRequest):
    """
    Recupera el perfil básico del usuario autenticado en Spotify.
    """
    try:
        print("\n[PROFILE] me_received")
        print(
            "access_token (primeros 20):",
            payload.access_token[:20] if payload.access_token else None,
        )

        profile = await get_spotify_profile(payload.access_token)

        print("[PROFILE] profile_obtained")
        print("spotify_user_id:", profile.get("id"))
        print("display_name:", profile.get("display_name"))
        print("country:", profile.get("country"))

        return profile
    except Exception as e:
        print("\n[PROFILE ERROR] /me:", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
async def spotify_refresh(payload: SpotifyRefreshRequest):
    """
    Renueva el access token de Spotify sin obligar a repetir el login OAuth.
    """
    try:
        print("\n[AUTH] refresh_received")

        token_data = await refresh_access_token(payload.refresh_token)

        print("[AUTH] token_refreshed")
        print("access_token (primeros 20):", token_data.get("access_token", "")[:20])
        print("scope:", token_data.get("scope"))
        print("expires_in:", token_data.get("expires_in"))

        return token_data
    except Exception as e:
        print("\n[AUTH ERROR] /refresh:", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/my-playlists")
async def spotify_my_playlists(payload: SpotifyPlaylistsRequest):
    """
    Devuelve las playlists del usuario autenticado.
    """
    try:
        playlists = await get_user_playlists(payload.access_token)
        return {"items": playlists}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# ENDPOINT PRINCIPAL: GENERACIÓN DE PLAYLIST
# -----------------------------------------------------------------------------
@router.post("/generate-playlist")
async def spotify_generate_playlist(payload: SpotifyGeneratePlaylistRequest):
    """
    Genera la playlist final de la sesión y la crea en Spotify.

    Es el endpoint central del producto musical:
    1. valida al usuario Spotify
    2. recupera la recomendación previa si existe
    3. construye el perfil musical de generación
    4. reúne y puntúa candidatos
    5. ensambla la playlist final
    6. la crea en Spotify
    7. deja trazado el contexto para feedback y ML
    """
    try:
        print(
            "\n[INPUT] "
            f"recommendation_id={payload.recommendation_id} | "
            f"goal={payload.goal} | mood={payload.mood} | "
            f"stress={payload.stress_level} | energy={payload.energy_level} | "
            f"outcome={payload.desired_outcome} | "
            f"env={'on' if payload.use_environment else 'off'} | "
            f"env_context={payload.environment_context if payload.use_environment else 'none'} | "
            f"prefs={payload.vocal_preference}/{payload.intensity_preference}/"
            f"{payload.exploration_preference}/{payload.popularity_preference}"
        )

        # 1) Obtener perfil del usuario Spotify
        profile = await get_spotify_profile(payload.access_token)
        spotify_user_id = profile.get("id")
        spotify_market = profile.get("country") or "ES"
        if not spotify_user_id:
            raise ValueError("No se pudo obtener el id del usuario Spotify")

        print(f"[PROFILE] spotify_user_id={spotify_user_id} | playlist_generation=ready")

        # Reusar la recomendación previa mantiene la trazabilidad de toda la
        # sesión: recomendación -> playlist -> feedback -> entrenamiento.
        recommendation_entry = _find_recommendation_entry(
            payload.recommendation_id,
            payload.recommendation_title,
        )
        session_mode = (
            recommendation_entry.get("recommended_mode")
            if recommendation_entry
            else None
        )

        # 2) Construir el perfil musical objetivo de la sesión
        generation_profile = build_generation_profile(
            user_id=spotify_user_id,
            goal=payload.goal,
            mood=payload.mood,
            stress_level=payload.stress_level,
            energy_level=payload.energy_level,
            noise_category=payload.noise_category,
            vocal_preference=payload.vocal_preference,
            intensity_preference=payload.intensity_preference,
            exploration_preference=payload.exploration_preference,
            popularity_preference=payload.popularity_preference,
            session_duration_min=payload.session_duration_min,
            desired_outcome=payload.desired_outcome,
            environment_context=payload.environment_context if payload.use_environment else None,
            environment_variability=(
                payload.environment_variability if payload.use_environment else None
            ),
            environment_peak_delta=(
                payload.environment_peak_delta if payload.use_environment else None
            ),
            environment_confidence=(
                payload.environment_confidence if payload.use_environment else None
            ),
            transient_ratio=payload.transient_ratio if payload.use_environment else None,
            burst_count=payload.burst_count if payload.use_environment else None,
            use_environment=payload.use_environment,
        )

        print(
            "[LEARNING] "
            f"mode={generation_profile.get('recommended_mode')} | "
            f"subtype={generation_profile.get('session_subtype')} | "
            f"curve={generation_profile.get('activation_curve')} | "
            f"profile_mode={generation_profile.get('taste_profile_mode')} | "
            f"session_weight={generation_profile.get('session_taste_weight')} | "
            f"stable_weight={generation_profile.get('stable_taste_weight')} | "
            f"mood_gate={generation_profile.get('mood_learning_gate_passed')} | "
            f"mood_q={generation_profile.get('mood_learning_quality_score')} | "
            f"apply_factor={generation_profile.get('mood_learning_application_factor')} | "
            f"env_strength={generation_profile.get('environment_influence_strength')} | "
            f"env_query_support="
            f"{bool(generation_profile.get('environment_noise_queries')) or bool(generation_profile.get('environment_context_queries'))}"
        )

        queries_used: list[str] = []
        candidate_tracks: list[dict] = []
        affinity_context: dict = {}
        dataset_candidate_count = 0
        removed_personal_tracks_count = 0
        # 3) En la entrega final desactivamos la afinidad viva de Spotify para
        # que el comportamiento observado dependa solo del catálogo local.
        personalized_candidates: list[dict] = []
        if USE_SPOTIFY_AFFINITY_SUPPORT:
            try:
                personalized_candidates, affinity_context = await build_personalized_candidates(
                    access_token=payload.access_token,
                    market=spotify_market,
                    per_artist_limit=10,
                )
                print(
                    "[AFFINITY] "
                    f"candidate_count={len(personalized_candidates)} | "
                    f"preferred_artist_count={len(affinity_context.get('preferred_artist_names', []))} | "
                    f"top_track_signal_count={len(affinity_context.get('top_track_ids', []))}"
                )
            except Exception as personalized_error:
                print("[AFFINITY] personalized candidates fallback:", personalized_error)
        else:
            print("[AFFINITY] source=msd_only")

        # El catálogo MSD es la fuente principal del ranking. Spotify queda como
        # apoyo de afinidad y como capa final de materialización, no como origen
        # principal de la decisión musical.
        # 4) Catálogo MSD como fuente principal de canciones y features.
        dataset_limit = max(
            60,
            _estimate_required_match_count(generation_profile["target_duration_ms"]) * 4,
        )
        try:
            dataset_candidates = select_dataset_candidates(
                profile=generation_profile,
                affinity_context=affinity_context,
                limit=dataset_limit,
            )
            dataset_candidate_count = len(dataset_candidates)
            if dataset_candidates:
                candidate_tracks.extend(dataset_candidates)
                queries_used.append("msd_catalog:feature_ranked_candidates")
        except Exception as dataset_error:
            print("[CATALOG] dataset candidates fallback:", dataset_error)

        seen_uris = {
            track.get("uri")
            for track in candidate_tracks
            if track.get("uri")
        }

        # 4B) Sin apoyo vivo de Spotify, el pool de trabajo sale solo del catálogo.
        if USE_SPOTIFY_AFFINITY_SUPPORT and len(candidate_tracks) < 20 and personalized_candidates:
            added_personalized = _merge_tracks(
                candidate_tracks=candidate_tracks,
                new_tracks=personalized_candidates,
                seen_uris=seen_uris,
            )
            if added_personalized > 0:
                queries_used.append("personal_affinity_support:top_items+artist_search")

        # 5) Fallback de búsqueda textual
        should_force_functional_fallback = (
            payload.goal in {"foco", "relajacion"}
            or (
                payload.goal == "energia"
                and payload.mood in {"triste", "cansado"}
                and payload.energy_level <= 2
            )
            or _session_mode_requires_functional_alignment(
                payload.goal,
                session_mode,
                payload.desired_outcome,
            )
        )

        if USE_SPOTIFY_FALLBACK_SEARCHES and (len(candidate_tracks) < 20 or should_force_functional_fallback):
            fallback_query_count = (
                4
                if (
                    payload.goal in {"foco", "relajacion"}
                    or _session_mode_requires_functional_alignment(
                        payload.goal,
                        session_mode,
                        payload.desired_outcome,
                    )
                )
                else 2
            )
            fallback_queries = generation_profile["primary_queries"][:fallback_query_count]
            fallback_results = await _run_fallback_searches(
                payload.access_token,
                fallback_queries,
                spotify_market,
            )

            for query, result in zip(fallback_queries, fallback_results):
                if query not in queries_used:
                    queries_used.append(query)

                if isinstance(result, Exception):
                    print(f"[CATALOG] fallback search error for '{query}':", result)
                    continue

                _merge_tracks(
                    candidate_tracks=candidate_tracks,
                    new_tracks=result,
                    seen_uris=seen_uris,
                    fallback_query=query,
                )

        if not candidate_tracks:
            raise ValueError("No se encontraron canciones para generar la playlist")

        # En este punto ya tenemos un pool mixto de candidatos. A partir de aquí
        # el backend decide cuáles encajan mejor con la sesión antes de intentar
        # convertirlos en URIs reales de Spotify.
        # 6) Ranking heurístico principal
        heuristic_ranked_tracks, removed_personal_tracks = _rank_pipeline(
            candidate_tracks=candidate_tracks,
            affinity_context=affinity_context,
            generation_profile=generation_profile,
            payload=payload,
            session_mode=session_mode,
        )
        removed_personal_tracks_count = len(removed_personal_tracks)

        # 7) Refuerzo funcional si el top ha quedado poco útil
        if USE_SPOTIFY_FALLBACK_SEARCHES and _needs_functional_reinforcement(
            heuristic_ranked_tracks,
            goal=payload.goal,
            session_mode=session_mode,
            desired_outcome=payload.desired_outcome,
        ):
            reinforcement_queries = [
                q for q in generation_profile["primary_queries"] if q not in queries_used
            ][:4]

            if reinforcement_queries:
                reinforcement_results = await _run_fallback_searches(
                    payload.access_token,
                    reinforcement_queries,
                    spotify_market,
                )

                added = 0
                for query, result in zip(reinforcement_queries, reinforcement_results):
                    if query not in queries_used:
                        queries_used.append(query)

                    if isinstance(result, Exception):
                        print(f"[CATALOG] reinforcement search error for '{query}':", result)
                        continue

                    added += _merge_tracks(
                        candidate_tracks=candidate_tracks,
                        new_tracks=result,
                        seen_uris=seen_uris,
                        fallback_query=query,
                    )
                if added > 0:
                    heuristic_ranked_tracks, removed_personal_tracks = _rank_pipeline(
                        candidate_tracks=candidate_tracks,
                        affinity_context=affinity_context,
                        generation_profile=generation_profile,
                        payload=payload,
                        session_mode=session_mode,
                    )

        # 7B) Rescate automático si el ranking sigue siendo demasiado débil
        if USE_SPOTIFY_RESCUE_RECOMMENDATIONS and _is_weak_playlist_ranking(
            heuristic_ranked_tracks,
            goal=payload.goal,
            desired_outcome=payload.desired_outcome,
        ):
            rescue_added = 0

            try:
                rescue_recommendations = await get_recommendations(
                    access_token=payload.access_token,
                    seed_genres=generation_profile["seed_genres"],
                    target_valence=generation_profile["target_valence"],
                    target_energy=generation_profile["target_energy"],
                    target_danceability=generation_profile["target_danceability"],
                    min_valence=max(0.0, generation_profile["target_valence"] - 0.32),
                    max_valence=min(1.0, generation_profile["target_valence"] + 0.32),
                    min_energy=max(0.0, generation_profile["target_energy"] - 0.32),
                    max_energy=min(1.0, generation_profile["target_energy"] + 0.32),
                    limit=28,
                    market=spotify_market,
                )
                if rescue_recommendations:
                    rescue_query_label = (
                        f"rescue_recommendations:{','.join(generation_profile['seed_genres'])}"
                    )
                    if rescue_query_label not in queries_used:
                        queries_used.append(rescue_query_label)
                    rescue_added += _merge_tracks(
                        candidate_tracks=candidate_tracks,
                        new_tracks=rescue_recommendations,
                        seen_uris=seen_uris,
                    )
            except Exception as rescue_recommendation_error:
                print("[CATALOG] weak ranking recommendations rescue fallback:", rescue_recommendation_error)

            rescue_queries = [
                q
                for q in _build_rescue_queries(
                    goal=payload.goal,
                    mood=payload.mood,
                    intensity_preference=payload.intensity_preference,
                    desired_outcome=payload.desired_outcome,
                    exploration_preference=payload.exploration_preference,
                    popularity_preference=payload.popularity_preference,
                )
                if q not in queries_used
            ]

            if rescue_queries:
                rescue_results = await _run_fallback_searches(
                    payload.access_token,
                    rescue_queries,
                    spotify_market,
                )

                for query, result in zip(rescue_queries, rescue_results):
                    if query not in queries_used:
                        queries_used.append(query)

                    if isinstance(result, Exception):
                        print(f"[CATALOG] weak ranking rescue search error for '{query}':", result)
                        continue

                    rescue_added += _merge_tracks(
                        candidate_tracks=candidate_tracks,
                        new_tracks=result,
                        seen_uris=seen_uris,
                        fallback_query=query,
                    )

            if rescue_added > 0:
                heuristic_ranked_tracks, removed_personal_tracks = _rank_pipeline(
                    candidate_tracks=candidate_tracks,
                    affinity_context=affinity_context,
                    generation_profile=generation_profile,
                    payload=payload,
                    session_mode=session_mode,
                )

        top_track = heuristic_ranked_tracks[0] if heuristic_ranked_tracks else {}
        top_artists = top_track.get("artists") or []
        top_artist = top_artists[0] if top_artists else "unknown"
        print(
            "[CATALOG] "
            f"dataset_candidates={dataset_candidate_count} | "
            f"hard_filter_removed={removed_personal_tracks_count} | "
            f"ranking=heuristic_only | "
            f"top_track={top_track.get('name', 'unknown')} - {top_artist} | "
            f"top_score={top_track.get('_score')}"
        )

        # 8) El ML se aplica ahora a nivel de sesión/modo, no por canción.
        # El ranking de tracks queda heurístico para mantenerlo explicable.
        final_ranked_tracks = heuristic_ranked_tracks
        for track in final_ranked_tracks:
            track["_ml_probability"] = None
            track["_ml_delta"] = 0.0
            track["_hybrid_score"] = track.get(
                "_score",
                track.get("heuristic_score", 0),
            )

        # 10) Materializamos los tracks elegidos del catálogo en Spotify.
        playable_track_target = _estimate_required_match_count(
            generation_profile["target_duration_ms"]
        )
        playable_ranked_tracks, match_stats = await materialize_ranked_tracks_for_spotify(
            access_token=payload.access_token,
            ranked_tracks=final_ranked_tracks,
            market=spotify_market,
            min_candidates=playable_track_target,
            max_searches=max(12, playable_track_target * 2),
        )

        print(
            "[MATERIALIZATION] "
            f"playable={len(playable_ranked_tracks)} | "
            f"cached={match_stats.get('cached_matches', 0)} | "
            f"fresh={match_stats.get('fresh_matches', 0)} | "
            f"failed={match_stats.get('failed_matches', 0)} | "
            f"searches={match_stats.get('searches', 0)} | "
            f"rate_limited={match_stats.get('rate_limited', False)}"
        )

        if match_stats.get("fresh_matches", 0) > 0:
            queries_used.append("materialization:title+artist_match")

        if not playable_ranked_tracks:
            raise HTTPException(
                status_code=429 if match_stats.get("rate_limited") is True else 400,
                detail=_build_materialization_error_message(match_stats),
            )

        # 11) Ensamblado final de la playlist ya con URIs válidas.
        selected_tracks = assemble_playlist(
            ranked_tracks=playable_ranked_tracks,
            target_duration_ms=generation_profile["target_duration_ms"],
            max_tracks_per_artist=generation_profile["max_tracks_per_artist"],
            activation_curve=generation_profile.get("activation_curve", "flat"),
            session_subtype=generation_profile.get("session_subtype"),
            vocal_preference=payload.vocal_preference,
        )

        if not selected_tracks:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudieron materializar suficientes canciones que respeten "
                    "la preferencia vocal solicitada."
                ),
            )

        # Guardamos features de los tracks seleccionados para futuras sesiones
        upsert_track_features_from_tracks(selected_tracks)

        actual_duration_ms = sum(int(t.get("duration_ms", 0) or 0) for t in selected_tracks)
        missing_duration_count = sum(
            1 for t in selected_tracks if not int(t.get("duration_ms", 0) or 0)
        )
        uris_count = len([t for t in selected_tracks if t.get("uri")])
        print(
            "[PLAYLIST] "
            f"selected_tracks={len(selected_tracks)} | "
            f"uris={uris_count} | "
            f"target_ms={generation_profile['target_duration_ms']} | "
            f"actual_ms={actual_duration_ms} | "
            f"missing_duration={missing_duration_count}"
        )

        # Guardamos contexto completo de la recomendación
        _attach_generated_context_to_recommendation(
            recommendation_id=payload.recommendation_id,
            recommendation_title=payload.recommendation_title,
            spotify_user_id=spotify_user_id,
            use_environment=payload.use_environment,
            goal=payload.goal,
            mood=payload.mood,
            stress_level=payload.stress_level,
            energy_level=payload.energy_level,
            noise_category=payload.noise_category if payload.use_environment else None,
            vocal_preference=payload.vocal_preference,
            intensity_preference=payload.intensity_preference,
            exploration_preference=payload.exploration_preference,
            popularity_preference=payload.popularity_preference,
            session_duration_min=payload.session_duration_min,
            desired_outcome=payload.desired_outcome,
            environment_context=payload.environment_context if payload.use_environment else None,
            environment_variability=payload.environment_variability if payload.use_environment else None,
            environment_peak_delta=payload.environment_peak_delta if payload.use_environment else None,
            environment_confidence=payload.environment_confidence if payload.use_environment else None,
            transient_ratio=payload.transient_ratio if payload.use_environment else None,
            burst_count=payload.burst_count if payload.use_environment else None,
            generation_mode=generation_profile["recommended_mode"],
            session_subtype=generation_profile.get("session_subtype"),
            activation_curve=generation_profile.get("activation_curve"),
            selected_tracks=selected_tracks,
        )

        recommendation_entry = _find_recommendation_entry(
            payload.recommendation_id,
            payload.recommendation_title,
        )

        uris = [track["uri"] for track in selected_tracks if track.get("uri")]
        if not uris:
            raise ValueError("No se pudo construir una playlist válida")

        # 11) Crear playlist en Spotify
        playlist_name = f"Harmony Hub · {payload.goal.title()}"
        description_parts = [
            f"goal={payload.goal}",
            f"mood={payload.mood}",
            f"estrés={payload.stress_level}",
            f"energía={payload.energy_level}",
            f"ruido={payload.noise_category if payload.use_environment else 'omitido'}",
            f"intensidad={payload.intensity_preference}",
            f"vocal={payload.vocal_preference}",
            f"desired_outcome={payload.desired_outcome}",
        ]

        if payload.use_environment and payload.environment_context:
            description_parts.append(f"entorno={payload.environment_context}")

        playlist_description = "Playlist profesional generada para " + ", ".join(
            description_parts
        )

        playlist = await create_playlist(
            access_token=payload.access_token,
            name=playlist_name,
            description=playlist_description,
            public=False,
        )

        await add_items_to_playlist(
            access_token=payload.access_token,
            playlist_id=playlist["id"],
            uris=uris,
        )

        print(
            "[PLAYLIST] "
            f"created id={playlist.get('id')} | "
            f"name={playlist.get('name')} | "
            f"query_signal_count={len(queries_used)}"
        )

        # 12) Respuesta al frontend
        return {
            "recommendation_id": payload.recommendation_id,
            "playlist_id": playlist.get("id"),
            "playlist_name": playlist.get("name"),
            "playlist_url": playlist.get("external_urls", {}).get("spotify"),
            "tracks_added": len(uris),
            "recommended_mode": recommendation_entry.get("recommended_mode")
            if recommendation_entry
            else generation_profile["recommended_mode"],
            "generation_mode": generation_profile["recommended_mode"],
            "session_subtype": generation_profile.get("session_subtype"),
            "activation_curve": generation_profile.get("activation_curve"),
            "queries_used": queries_used,
            "spotify_user_id": spotify_user_id,
            "ml_enabled": recommendation_entry.get("ml_enabled")
            if recommendation_entry
            else session_mode_model_available(),
            "selection_source": recommendation_entry.get("selection_source")
            if recommendation_entry
            else "heuristic",
            "mode_ml_probability": recommendation_entry.get("mode_ml_probability")
            if recommendation_entry
            else None,
            "spotify_matching": match_stats,
            "use_environment": payload.use_environment,
            "desired_outcome": payload.desired_outcome,
            "noise_category": payload.noise_category if payload.use_environment else None,
            "environment_context": payload.environment_context if payload.use_environment else None,
            "environment_variability": payload.environment_variability if payload.use_environment else None,
            "environment_peak_delta": payload.environment_peak_delta if payload.use_environment else None,
            "environment_confidence": payload.environment_confidence if payload.use_environment else None,
            "transient_ratio": payload.transient_ratio if payload.use_environment else None,
            "burst_count": payload.burst_count if payload.use_environment else None,
            "selected_tracks": [
                {
                    "id": track.get("id"),
                    "catalog_track_id": track.get("catalog_track_id"),
                    "msd_track_id": track.get("msd_track_id"),
                    "name": track.get("name"),
                    "artists": track.get("artists", []),
                    "popularity": track.get("popularity", 0),
                    "duration_ms": track.get("duration_ms", 0),
                    "explicit": track.get("explicit", False),
                    "bpm": track.get("bpm"),
                    "danceability": track.get("danceability"),
                    "energy_feature": track.get("energy_feature"),
                    "valence_feature": track.get("valence_feature"),
                    "instrumentalness": track.get("instrumentalness"),
                    "acousticness": track.get("acousticness"),
                    "speechiness": track.get("speechiness"),
                    "liveness": track.get("liveness"),
                    "score": track.get("_score", track.get("heuristic_score", 0)),
                    "heuristic_score": track.get(
                        "heuristic_score",
                        track.get("_score", 0),
                    ),
                    "ml_probability": round(track.get("_ml_probability"), 4)
                    if track.get("_ml_probability") is not None
                    else None,
                    "ml_delta": round(track.get("_ml_delta", 0.0), 2),
                    "hybrid_score": round(
                        track.get("_hybrid_score", track.get("_score", 0)),
                        2,
                    ),
                    "reasons": track.get("_reasons", track.get("reasons", [])),
                    "desired_outcome_delta": track.get("desired_outcome_delta"),
                    "environment_delta": track.get("environment_delta"),
                    "textual_semantic_delta": track.get("textual_semantic_delta"),
                    "vector_similarity": track.get("vector_similarity"),
                    "vector_similarity_delta": track.get("vector_similarity_delta"),
                    "personal_affinity_delta": track.get("personal_affinity_delta"),
                    "generic_title_penalty": track.get("generic_title_penalty"),
                    "fallback_source_penalty": track.get("fallback_source_penalty"),
                    "soft_personal_recovery_delta": track.get(
                        "soft_personal_recovery_delta"
                    ),
                    "session_subtype_delta": track.get("session_subtype_delta"),
                    "lyrics_available": track.get("lyrics_available"),
                    "description_available": track.get("description_available"),
                    "text_profile": track.get("text_profile"),
                    "sentiment_label": track.get("sentiment_label"),
                    "sentiment_score": track.get("sentiment_score"),
                    "semantic_similarity": track.get("semantic_similarity"),
                    "text_source_preview": track.get("text_source_preview"),
                    "spotify_track_id": track.get("spotify_track_id"),
                    "spotify_uri": track.get("spotify_uri"),
                    "spotify_match": track.get("spotify_match"),
                    "affinity_source": track.get("_affinity_source"),
                    "fallback_query": track.get("_fallback_query"),
                    "feature_source": track.get("_feature_source"),
                    "feature_match": track.get("_feature_match"),
                }
                for track in selected_tracks
            ],
            "learning_info": {
                "feedback_count": generation_profile["feedback_count"],
                "seed_genres": generation_profile["seed_genres"],
                "session_subtype": generation_profile.get("session_subtype"),
                "activation_curve": generation_profile.get("activation_curve"),
                "taste_profile_mode": generation_profile.get("taste_profile_mode"),
                "session_taste_weight": generation_profile.get("session_taste_weight"),
                "stable_taste_weight": generation_profile.get("stable_taste_weight"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        print("\n[PLAYLIST ERROR] generate-playlist:", repr(e))
        raise HTTPException(status_code=400, detail=str(e))
