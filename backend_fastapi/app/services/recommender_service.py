from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.adaptive_learning_service import get_feedback_bonus
from app.services.professional_playlist_model_service import build_generation_profile
from app.services.session_mode_ml_service import (
    get_model_card_summary,
    model_available as session_model_available,
    rank_recommendation_candidates,
)

INTENSITY_LEVELS = ["suave", "media", "alta"]


def _energy_label(value: float) -> str:
    if value < 0.30:
        return "baja"
    if value < 0.48:
        return "baja-media"
    if value < 0.65:
        return "media"
    if value < 0.82:
        return "media-alta"
    return "alta"


def _valence_label(value: float) -> str:
    if value < 0.40:
        return "baja"
    if value < 0.58:
        return "neutral"
    if value < 0.72:
        return "neutral-positiva"
    return "positiva"


def _round_optional(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _target_bpm_range(
    *,
    goal: str,
    target_energy: float,
    desired_outcome: str | None,
) -> str:
    if goal == "foco":
        if desired_outcome in {"mas_despierto", "mas_animado"}:
            return "75-110"
        if target_energy < 0.35:
            return "60-85"
        return "65-100"

    if goal == "relajacion":
        if target_energy < 0.28:
            return "55-75"
        return "60-90"

    if desired_outcome == "mas_ligero":
        return "90-118"
    if target_energy < 0.72:
        return "95-120"
    return "105-135"


def _build_dynamic_title(goal: str) -> str:
    if goal == "foco":
        return "Sesion de Foco Guiado"
    if goal == "relajacion":
        return "Sesion de Regulacion y Calma"
    return "Sesion de Activacion Musical"


def _build_dynamic_description(
    data: RecommendationRequest,
    *,
    target_energy: str,
    target_valence: str,
) -> str:
    environment_text = (
        f" teniendo en cuenta un entorno {data.noise_category}"
        if data.use_environment
        else " sin apoyarse en el entorno"
    )

    outcome_text = (
        f" para ayudarte a acabar {data.desired_outcome.replace('_', ' ')}"
        if data.desired_outcome
        else ""
    )

    if data.goal == "foco":
        return (
            "Perfil dinamico orientado a concentracion estable, "
            f"con energia {target_energy} y tono {target_valence}"
            f"{environment_text}{outcome_text}."
        )

    if data.goal == "relajacion":
        return (
            "Perfil dinamico orientado a bajar activacion y sostener calma, "
            f"con energia {target_energy} y tono {target_valence}"
            f"{environment_text}{outcome_text}."
        )

    return (
        "Perfil dinamico orientado a recuperar impulso y tono positivo"
        f", con energia {target_energy} y valencia {target_valence}"
        f"{environment_text}{outcome_text}."
    )


def _intensity_distance_score(
    requested_intensity: str,
    candidate_intensity: str,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    requested_idx = INTENSITY_LEVELS.index(requested_intensity)
    candidate_idx = INTENSITY_LEVELS.index(candidate_intensity)
    distance = abs(requested_idx - candidate_idx)

    if distance == 0:
        reasons.append("intensity_match:+10")
        return 10.0, reasons
    if distance == 1:
        reasons.append("intensity_neighbor:+5")
        return 5.0, reasons
    reasons.append("intensity_far:+0")
    return 0.0, reasons


def _goal_alignment_score(
    candidate: dict,
    data: RecommendationRequest,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    target_energy_value = float(candidate["_target_energy_value"])
    if data.goal == "foco":
        if 0.22 <= target_energy_value <= 0.58:
            score += 8.0
            reasons.append("goal_focus_energy_band:+8")
    elif data.goal == "relajacion":
        if target_energy_value <= 0.42:
            score += 8.0
            reasons.append("goal_relax_energy_band:+8")
    elif data.goal == "energia":
        if target_energy_value >= 0.62:
            score += 8.0
            reasons.append("goal_energy_band:+8")

    if data.use_environment and candidate.get("noise_category") == data.noise_category:
        score += 4.0
        reasons.append("environment_match:+4")

    return score, reasons


def _desired_outcome_score(
    candidate: dict,
    desired_outcome: str | None,
) -> tuple[float, list[str]]:
    if not desired_outcome:
        return 0.0, []

    target_energy_value = float(candidate["_target_energy_value"])
    target_valence_value = float(candidate["_target_valence_value"])
    reasons: list[str] = []
    score = 0.0

    if desired_outcome == "mas_calmado" and target_energy_value <= 0.40:
        score += 6.0
        reasons.append("desired_outcome_calm:+6")
    elif desired_outcome == "mas_centrado" and 0.25 <= target_energy_value <= 0.55:
        score += 6.0
        reasons.append("desired_outcome_focus:+6")
    elif desired_outcome in {"mas_animado", "mas_despierto"} and target_energy_value >= 0.68:
        score += 6.0
        reasons.append("desired_outcome_awake:+6")
    elif desired_outcome == "mas_ligero" and target_valence_value >= 0.58:
        score += 6.0
        reasons.append("desired_outcome_light:+6")
    elif desired_outcome == "mas_acompanado" and target_valence_value >= 0.52:
        score += 4.0
        reasons.append("desired_outcome_supported:+4")

    return score, reasons


def _build_dynamic_candidate(
    data: RecommendationRequest,
    *,
    candidate_intensity: str,
) -> dict:
    # La recomendación necesita un identificador estable incluso si la sesión no
    # parte de una cuenta Spotify enlazada todavía. Esto permite mantener el
    # mismo flujo de perfilado y trazabilidad sin romper la generación.
    recommendation_user_id = (
        str(data.spotify_user_id).strip()
        if data.spotify_user_id is not None and str(data.spotify_user_id).strip()
        else "anonymous_recommendation"
    )

    # El generation profile concentra toda la lógica musical compleja
    # posterior: pesos aprendidos, entorno, targets musicales y modo final
    # sugerido para esta variante de intensidad.
    profile = build_generation_profile(
        user_id=recommendation_user_id,
        goal=data.goal,
        mood=data.mood,
        stress_level=data.stress_level,
        energy_level=data.energy_level,
        noise_category=data.noise_category,
        vocal_preference=data.vocal_preference,
        intensity_preference=candidate_intensity,
        exploration_preference=data.exploration_preference,
        popularity_preference=data.popularity_preference,
        session_duration_min=data.session_duration_min,
        desired_outcome=data.desired_outcome,
        environment_context=data.environment_context if data.use_environment else None,
        environment_variability=(
            data.environment_variability if data.use_environment else None
        ),
        environment_peak_delta=(
            data.environment_peak_delta if data.use_environment else None
        ),
        environment_confidence=(
            data.environment_confidence if data.use_environment else None
        ),
        transient_ratio=data.transient_ratio if data.use_environment else None,
        burst_count=data.burst_count if data.use_environment else None,
        use_environment=data.use_environment,
    )

    target_energy_value = float(profile.get("target_energy", 0.5))
    target_valence_value = float(profile.get("target_valence", 0.5))

    target_energy = _energy_label(target_energy_value)
    target_valence = _valence_label(target_valence_value)
    target_bpm_range = _target_bpm_range(
        goal=data.goal,
        target_energy=target_energy_value,
        desired_outcome=data.desired_outcome,
    )

    candidate = {
        "id": None,
        "title": _build_dynamic_title(data.goal),
        "description": _build_dynamic_description(
            data,
            target_energy=target_energy,
            target_valence=target_valence,
        ),
        "spotify_playlist": None,
        "goal": data.goal,
        "noise_category": data.noise_category if data.use_environment else None,
        "recommended_mode": profile["recommended_mode"],
        "target_bpm_range": target_bpm_range,
        "target_energy": target_energy,
        "target_valence": target_valence,
        "_target_energy_value": target_energy_value,
        "_target_valence_value": target_valence_value,
        "_candidate_intensity": candidate_intensity,
        "_profile": profile,
    }
    return candidate


def _log_ranked_candidates(
    ranked: list[dict],
    *,
    ml_enabled: bool,
) -> None:
    print("[SESSION] ranked candidates")
    print("[SESSION] ml_enabled:", ml_enabled)

    probabilities = [
        float(item.get("_mode_ml_probability"))
        for item in ranked
        if item.get("_mode_ml_probability") is not None
    ]
    probability_spread = (
        max(probabilities) - min(probabilities) if probabilities else None
    )
    print("[SESSION] probability_spread:", _round_optional(probability_spread))

    for item in ranked:
        print(
            "[SESSION] CANDIDATE:",
            item.get("recommended_mode"),
            "| heuristic=",
            round(float(item.get("_base_score", 0.0) or 0.0), 2),
            "| ml_prob=",
            _round_optional(item.get("_mode_ml_probability")),
            "| ml_delta=",
            round(float(item.get("_mode_ml_delta", 0.0) or 0.0), 2),
            "| final=",
            round(float(item.get("_score", 0.0) or 0.0), 2),
            "| source=",
            item.get("_selection_source"),
        )

    if ranked:
        best = ranked[0]
        print("[SESSION] selected_mode:", best.get("recommended_mode"))
        print("[SESSION] selection_source:", best.get("_selection_source"))
        print(
            "[SESSION] selected_mode_probability:",
            _round_optional(best.get("_mode_ml_probability")),
        )
        print(
            "[SESSION] selected_mode_scores:",
            {
                "heuristic": round(float(best.get("_base_score", 0.0) or 0.0), 2),
                "ml_delta": round(float(best.get("_mode_ml_delta", 0.0) or 0.0), 2),
                "final": round(float(best.get("_score", 0.0) or 0.0), 2),
            },
        )


def _score_dynamic_candidate(
    candidate: dict,
    data: RecommendationRequest,
) -> tuple[float, list[str]]:
    """
    Asigna un score heurístico base a un candidato dinámico.

    No elige canciones ni usa un catálogo estático. Solo compara varias formas
    posibles de perfilar la sesión para que luego el ML, si existe, pueda
    reordenarlas.
    """
    score = 0.0
    reasons: list[str] = []

    intensity_score, intensity_reasons = _intensity_distance_score(
        data.intensity_preference,
        candidate["_candidate_intensity"],
    )
    score += intensity_score
    reasons.extend(intensity_reasons)

    goal_score, goal_reasons = _goal_alignment_score(candidate, data)
    score += goal_score
    reasons.extend(goal_reasons)

    desired_score, desired_reasons = _desired_outcome_score(
        candidate,
        data.desired_outcome,
    )
    score += desired_score
    reasons.extend(desired_reasons)

    feedback_bonus = get_feedback_bonus(candidate["recommended_mode"])
    score += feedback_bonus
    if feedback_bonus:
        reasons.append(f"adaptive_feedback:{feedback_bonus:+d}")

    return score, reasons


def _build_dynamic_candidates(data: RecommendationRequest) -> list[dict]:
    """
    Genera varios candidatos dinámicos variando la intensidad del perfil.

    Esto mantiene la recomendación abierta y libre de catálogo, pero conserva
    una pequeña competencia entre alternativas para que heurística y ML puedan
    decidir cuál perfila mejor la sesión.
    """
    candidates: list[dict] = []
    seen_modes: set[str] = set()

    # Primero se prueba la intensidad pedida por el usuario y después sus vecinas.
    # Así la heurística y el ML comparan alternativas plausibles sin abrir un
    # espacio de búsqueda innecesariamente grande.
    ordered_intensities = [data.intensity_preference] + [
        intensity
        for intensity in INTENSITY_LEVELS
        if intensity != data.intensity_preference
    ]

    for candidate_intensity in ordered_intensities:
        candidate = _build_dynamic_candidate(
            data,
            candidate_intensity=candidate_intensity,
        )
        if candidate["recommended_mode"] in seen_modes:
            continue
        seen_modes.add(candidate["recommended_mode"])

        base_score, reasons = _score_dynamic_candidate(candidate, data)
        candidate["_base_score"] = float(base_score)
        candidate["_score"] = float(base_score)
        candidate["_base_reasons"] = reasons
        candidates.append(candidate)

    return candidates


def generate_recommendation(data: RecommendationRequest) -> RecommendationResponse:
    """
    Genera una recomendación dinámica sin depender de `music_catalog.json`.

    Flujo:
    1. construye varios perfiles musicales posibles a partir del contexto
    2. los puntúa heurísticamente
    3. si hay modelo entrenado, deja que el ML reordene esos perfiles
    4. devuelve el mejor como recomendación de sesión
    """
    candidates = _build_dynamic_candidates(data)

    context = {
        "goal": data.goal,
        "mood": data.mood,
        "stress_level": data.stress_level,
        "energy_level": data.energy_level,
        "noise_category": data.noise_category if data.use_environment else None,
        "use_environment": data.use_environment,
        "vocal_preference": data.vocal_preference,
        "intensity_preference": data.intensity_preference,
        "exploration_preference": data.exploration_preference,
        "popularity_preference": data.popularity_preference,
        "session_duration_min": data.session_duration_min,
        "desired_outcome": data.desired_outcome,
        "environment_context": data.environment_context if data.use_environment else None,
        "environment_variability": (
            data.environment_variability if data.use_environment else None
        ),
        "environment_peak_delta": (
            data.environment_peak_delta if data.use_environment else None
        ),
        "environment_confidence": (
            data.environment_confidence if data.use_environment else None
        ),
        "transient_ratio": data.transient_ratio if data.use_environment else None,
        "burst_count": data.burst_count if data.use_environment else None,
    }

    # El clasificador global solo entra si supera sus puertas de datos y
    # calidad. La confianza local de la sesión se resuelve después con el
    # umbral operativo de probabilidad del mejor candidato.
    ml_enabled = session_model_available()

    if ml_enabled:
        ranked = rank_recommendation_candidates(candidates, context)
    else:
        ranked = sorted(
            candidates,
            key=lambda item: float(item.get("_score", 0.0)),
            reverse=True,
        )
        for item in ranked:
            item["_selection_source"] = "dynamic_profile"
            item["_mode_ml_delta"] = 0.0
            item["_mode_ml_explanation"] = None

    _log_ranked_candidates(ranked, ml_enabled=ml_enabled)

    # El primer elemento ya representa la decisión final porque la lista llega
    # ordenada por heurística o por heurística + ajuste supervisado.
    best = ranked[0]
    profile = dict(best.get("_profile", {}) or {})

    print("[ENV] use_environment:", data.use_environment)
    print("[ENV] environment_context:", profile.get("environment_context"))
    print(
        "[ENV] environment_influence_strength:",
        _round_optional(profile.get("environment_influence_strength")),
    )
    print(
        "[ENV] target_adjustment:",
        profile.get("environment_target_adjustment"),
    )
    print(
        "[ENV] noise_queries:",
        profile.get("environment_noise_queries", []),
    )
    print(
        "[ENV] context_queries:",
        profile.get("environment_context_queries", []),
    )
    print(
        "[LEARNING] mood_gate_passed:",
        profile.get("mood_learning_gate_passed"),
    )
    print(
        "[LEARNING] mood_quality_score:",
        _round_optional(profile.get("mood_learning_quality_score")),
    )
    print(
        "[LEARNING] mood_application_factor:",
        _round_optional(profile.get("mood_learning_application_factor")),
    )

    return RecommendationResponse(
        title=best["title"],
        description=best["description"],
        recommended_mode=best["recommended_mode"],
        target_bpm_range=best["target_bpm_range"],
        target_energy=best["target_energy"],
        target_valence=best["target_valence"],
        spotify_playlist=best["spotify_playlist"],
        catalog_item_id=None,
        catalog_noise_category=None,
        ml_enabled=ml_enabled,
        mode_ml_probability=best.get("_mode_ml_probability"),
        selection_source=best.get("_selection_source", "dynamic_profile"),
        feedback_count=int(profile.get("feedback_count", 0) or 0),
        session_taste_weight=float(profile.get("session_taste_weight", 0.0) or 0.0),
        stable_taste_weight=float(profile.get("stable_taste_weight", 0.0) or 0.0),
        taste_profile_mode=str(profile.get("taste_profile_mode", "session_weighted")),
        ml_explanation=best.get("_mode_ml_explanation"),
        model_card_summary=get_model_card_summary(),
    )
