from __future__ import annotations

from typing import Any

from app.services.msd_catalog_service import load_catalog_tracks, normalize_text


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _normalized_set(items: list[str] | None) -> set[str]:
    return {
        normalize_text(item)
        for item in (items or [])
        if normalize_text(item)
    }


def _closeness_score(value: float | None, target: float | None, weight: float) -> float:
    if value is None or target is None:
        return 0.0
    diff = abs(float(value) - float(target))
    if diff >= 1.0:
        return 0.0
    return max(0.0, weight * (1.0 - diff))


def _tempo_alignment_score(bpm: float | None, goal: str) -> tuple[float, list[str]]:
    if bpm is None:
        return 0.0, []

    if goal == "foco" and 55 <= bpm <= 100:
        return 8.0, ["catalog:bpm_focus_bonus"]
    if goal == "relajacion" and 50 <= bpm <= 90:
        return 8.0, ["catalog:bpm_relax_bonus"]
    if goal == "energia" and 95 <= bpm <= 150:
        return 8.0, ["catalog:bpm_energy_bonus"]
    return 0.0, []


def _goal_field_score(track: dict[str, Any], goal: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    if goal == "foco":
        focus_score = _safe_float(track.get("focus_score"))
        if focus_score is not None:
            delta = focus_score * 14.0
            score += delta
            reasons.append(f"catalog:focus_score:+{round(delta, 2)}")
    elif goal == "relajacion":
        calm_score = _safe_float(track.get("calm_score"))
        if calm_score is not None:
            delta = calm_score * 14.0
            score += delta
            reasons.append(f"catalog:calm_score:+{round(delta, 2)}")
    elif goal == "energia":
        uplift_score = _safe_float(track.get("uplift_score"))
        if uplift_score is not None:
            delta = uplift_score * 14.0
            score += delta
            reasons.append(f"catalog:uplift_score:+{round(delta, 2)}")

    return round(score, 2), reasons


def _seed_term_score(track: dict[str, Any], profile: dict[str, Any]) -> tuple[float, list[str]]:
    seed_genres = _normalized_set(profile.get("seed_genres", []))
    search_text = str(track.get("_catalog_search_text", "") or "")
    reasons: list[str] = []
    score = 0.0

    if seed_genres:
        genre_matches = {
            genre for genre in seed_genres if genre and genre in search_text
        }
        if genre_matches:
            delta = min(12.0, len(genre_matches) * 4.0)
            score += delta
            reasons.append(f"catalog:seed_genres:+{round(delta, 2)}")

    token_hits = 0
    for query in profile.get("primary_queries", []):
        for token in normalize_text(query).split():
            if len(token) < 4:
                continue
            if token in search_text:
                token_hits += 1

    if token_hits:
        delta = min(14.0, token_hits * 1.8)
        score += delta
        reasons.append(f"catalog:query_tokens:+{round(delta, 2)}")

    return round(score, 2), reasons


def _popularity_alignment(track: dict[str, Any], profile: dict[str, Any]) -> tuple[float, list[str]]:
    popularity = _safe_float(track.get("popularity_proxy"))
    if popularity is None:
        popularity = _safe_float(track.get("popularity"))
    if popularity is None:
        return 0.0, []

    preference = profile.get("popularity_preference", "mixta")
    reasons: list[str] = []
    score = 0.0

    if preference == "mainstream":
        if popularity >= 75:
            score += 6.0
            reasons.append("catalog:mainstream_bonus")
        elif popularity < 25:
            score -= 5.0
            reasons.append("catalog:too_obscure_penalty")
    elif preference == "alternativa":
        if 18 <= popularity <= 60:
            score += 4.0
            reasons.append("catalog:alternative_bonus")
        elif popularity >= 85:
            score -= 2.0
            reasons.append("catalog:too_popular_penalty")
    else:
        if 30 <= popularity <= 80:
            score += 2.5
            reasons.append("catalog:balanced_popularity_bonus")

    return round(score, 2), reasons


def _affinity_alignment(track: dict[str, Any], affinity_context: dict[str, Any] | None) -> tuple[float, list[str]]:
    if not affinity_context:
        return 0.0, []

    preferred_artists = _normalized_set(affinity_context.get("preferred_artist_names", []))
    track_artists = _normalized_set(track.get("artists", []))
    if not preferred_artists or not track_artists:
        return 0.0, []

    if preferred_artists.intersection(track_artists):
        return 6.0, ["catalog:preferred_artist_bonus"]
    return 0.0, []


def _observed_vocal_presence(track: dict[str, Any]) -> float | None:
    explicit_score = _safe_float(track.get("vocal_presence_score"))
    if explicit_score is not None:
        return explicit_score

    instrumentalness = _safe_float(track.get("instrumentalness"))
    if instrumentalness is None:
        return None
    return max(0.0, min(1.0, 1.0 - instrumentalness))


def _functional_profile_alignment(
    track: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[float, list[str]]:
    target_warmth = _safe_float(profile.get("target_warmth"))
    target_steadiness = _safe_float(profile.get("target_steadiness"))
    target_vocal_presence = _safe_float(profile.get("target_vocal_presence"))

    warmth = _safe_float(track.get("warmth_score"))
    steadiness = _safe_float(track.get("steadiness_score"))
    vocal_presence = _observed_vocal_presence(track)
    supportiveness = _safe_float(track.get("supportiveness_score"))
    tension = _safe_float(track.get("tension_score"))
    emotional_weight = _safe_float(track.get("emotional_weight_score"))

    session_subtype = profile.get("session_subtype", "")
    goal = profile.get("goal")
    desired_outcome = profile.get("desired_outcome")

    delta = 0.0
    reasons: list[str] = []

    warmth_delta = _closeness_score(warmth, target_warmth, 8.0)
    steadiness_delta = _closeness_score(steadiness, target_steadiness, 8.0)
    vocal_delta = _closeness_score(vocal_presence, target_vocal_presence, 6.0)
    delta += warmth_delta + steadiness_delta + vocal_delta

    if warmth_delta:
        reasons.append(f"catalog:functional_warmth:+{round(warmth_delta, 2)}")
    if steadiness_delta:
        reasons.append(f"catalog:functional_steadiness:+{round(steadiness_delta, 2)}")
    if vocal_delta:
        reasons.append(f"catalog:functional_vocal:+{round(vocal_delta, 2)}")

    if session_subtype == "deep_focus":
        if steadiness is not None and steadiness >= 0.84:
            delta += 4.0
            reasons.append("catalog:deep_focus_steady_bonus")
        if tension is not None and tension > 0.34:
            delta -= 5.0
            reasons.append("catalog:deep_focus_tension_penalty")

    elif session_subtype == "stable_relaxation":
        if steadiness is not None and steadiness >= 0.84:
            delta += 4.0
            reasons.append("catalog:stable_relaxation_steady_bonus")
        if warmth is not None and warmth >= 0.68:
            delta += 3.0
            reasons.append("catalog:stable_relaxation_warm_bonus")
        if tension is not None and tension > 0.26:
            delta -= 4.5
            reasons.append("catalog:stable_relaxation_tension_penalty")

    elif session_subtype == "warm_relaxation":
        if warmth is not None and warmth >= 0.76:
            delta += 4.0
            reasons.append("catalog:warm_relaxation_warm_bonus")
        if supportiveness is not None and supportiveness >= 0.82:
            delta += 3.0
            reasons.append("catalog:warm_relaxation_support_bonus")

    elif session_subtype == "soft_activation":
        if tension is not None and tension <= 0.24:
            delta += 3.0
            reasons.append("catalog:soft_activation_low_tension_bonus")
        if supportiveness is not None and supportiveness >= 0.72:
            delta += 2.0
            reasons.append("catalog:soft_activation_support_bonus")
        if emotional_weight is not None and emotional_weight > 0.72:
            delta -= 3.0
            reasons.append("catalog:soft_activation_too_heavy_penalty")

    elif session_subtype == "warm_companionship":
        if warmth is not None and warmth >= 0.78:
            delta += 5.0
            reasons.append("catalog:warm_companionship_warm_bonus")
        if supportiveness is not None and supportiveness >= 0.82:
            delta += 4.0
            reasons.append("catalog:warm_companionship_support_bonus")
        if vocal_presence is not None and vocal_presence >= 0.72:
            delta += 3.0
            reasons.append("catalog:warm_companionship_voice_bonus")
        if tension is not None and tension > 0.26:
            delta -= 5.0
            reasons.append("catalog:warm_companionship_tension_penalty")
        if emotional_weight is not None and emotional_weight > 0.78:
            delta -= 3.5
            reasons.append("catalog:warm_companionship_too_heavy_penalty")

    elif goal == "energia" and desired_outcome in {"mas_despierto", "mas_animado"}:
        if supportiveness is not None and supportiveness >= 0.68:
            delta += 1.5
            reasons.append("catalog:energizing_support_bonus")
        if tension is not None and tension > 0.46:
            delta -= 2.5
            reasons.append("catalog:energizing_tension_penalty")

    return round(delta, 2), reasons


def _activation_style_alignment(
    track: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[float, list[str]]:
    activation_style = normalize_text(track.get("activation_style"))
    activation_curve = profile.get("activation_curve", "flat")
    session_subtype = profile.get("session_subtype", "")

    if not activation_style:
        return 0.0, []

    preferred_styles: dict[str, set[str]] = {
        "flat": {"flat"},
        "progressive": {"progressive"},
        "peak_then_settle": {"progressive", "peak"},
    }
    subtype_overrides: dict[str, set[str]] = {
        "deep_focus": {"flat"},
        "stable_relaxation": {"flat"},
        "warm_relaxation": {"flat"},
        "soft_activation": {"progressive"},
        "warm_companionship": {"progressive"},
        "peak_energy": {"peak", "progressive"},
    }

    preferred = subtype_overrides.get(session_subtype, preferred_styles.get(activation_curve, {"flat"}))
    if activation_style in preferred:
        return 4.0, [f"catalog:activation_style_match:{activation_style}"]

    if activation_curve == "flat" and activation_style == "peak":
        return -4.5, ["catalog:activation_style_too_peak_penalty"]
    if activation_curve == "progressive" and activation_style == "flat":
        return -1.5, ["catalog:activation_style_too_static_penalty"]
    return 0.0, []


def _companionship_catalog_adjustment(
    track: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[float, list[str]]:
    if not (
        profile.get("goal") == "energia"
        and profile.get("mood") == "triste"
        and profile.get("desired_outcome") == "mas_acompanado"
    ):
        return 0.0, []

    energy = _safe_float(track.get("energy_feature"))
    valence = _safe_float(track.get("valence_feature"))
    danceability = _safe_float(track.get("danceability"))
    search_text = str(track.get("_catalog_search_text", "") or "")
    intensity_preference = profile.get("intensity_preference", "media")

    delta = 0.0
    reasons: list[str] = []

    if energy is not None:
        if 0.34 <= energy <= 0.66:
            delta += 6.5
            reasons.append("catalog:companionship_energy_bonus")
        elif energy > 0.76:
            delta -= 10.0
            reasons.append("catalog:companionship_too_intense_penalty")
        elif energy < 0.24:
            delta -= 2.5
            reasons.append("catalog:companionship_too_flat_penalty")

    if valence is not None and 0.42 <= valence <= 0.76:
        delta += 4.5
        reasons.append("catalog:companionship_valence_bonus")

    if danceability is not None:
        if 0.26 <= danceability <= 0.62:
            delta += 3.0
            reasons.append("catalog:companionship_danceability_bonus")
        elif danceability > 0.72:
            delta -= 6.5
            reasons.append("catalog:companionship_too_dancy_penalty")

    warm_tokens = [
        "warm",
        "comfort",
        "acoustic",
        "soft vocal",
        "indie",
        "familiar",
        "gentle",
        "bright",
        "feel good",
    ]
    hard_tokens = [
        "edm",
        "dance",
        "party",
        "club",
        "workout",
        "power",
        "anthem",
        "firework",
        "titanium",
    ]

    warm_hits = sum(1 for token in warm_tokens if token in search_text)
    hard_hits = sum(1 for token in hard_tokens if token in search_text)

    if warm_hits:
        bonus = min(5.0, warm_hits * 1.5)
        delta += bonus
        reasons.append(f"catalog:companionship_warmth_bonus:+{round(bonus, 2)}")

    if hard_hits:
        penalty = min(10.0, hard_hits * (2.6 if intensity_preference == "suave" else 1.4))
        delta -= penalty
        reasons.append(f"catalog:companionship_hardness_penalty:-{round(penalty, 2)}")

    return round(delta, 2), reasons


def _passes_hard_filters(track: dict[str, Any], profile: dict[str, Any]) -> bool:
    goal = profile.get("goal")
    vocal_preference = profile.get("vocal_preference", "indistinto")
    intensity_preference = profile.get("intensity_preference", "media")
    energy = _safe_float(track.get("energy_feature"))
    danceability = _safe_float(track.get("danceability"))
    instrumentalness = _safe_float(track.get("instrumentalness"))
    search_text = str(track.get("_catalog_search_text", "") or "")
    duration_ms = int(track.get("duration_ms", 0) or 0)

    if duration_ms and duration_ms < 90000:
        return False

    if vocal_preference == "instrumental":
        has_instrumental_evidence = (
            (instrumentalness is not None and instrumentalness >= 0.45)
            or "instrumental" in search_text
            or "ambient" in search_text
            or "piano" in search_text
        )
        if not has_instrumental_evidence:
            return False
    elif vocal_preference == "con_voz":
        vocal_presence = _observed_vocal_presence(track)
        if "instrumental" in search_text:
            return False
        if instrumentalness is not None and instrumentalness >= 0.40:
            return False
        if vocal_presence is None or vocal_presence < 0.55:
            return False

    if goal == "foco":
        if energy is not None and energy > 0.88:
            return False
        if danceability is not None and danceability > 0.82:
            return False
    elif goal == "relajacion":
        if energy is not None and energy > 0.82:
            return False
    elif goal == "energia":
        if energy is not None and energy < 0.18:
            return False
        if "sleep" in search_text or "meditation" in search_text:
            return False

        if (
            profile.get("mood") == "triste"
            and profile.get("desired_outcome") == "mas_acompanado"
            and profile.get("intensity_preference") == "suave"
        ):
            if energy is not None and energy > 0.90:
                return False
            if danceability is not None and danceability > 0.82:
                return False

    if intensity_preference == "suave" and energy is not None and energy > 0.92:
        return False

    return True


def _diversify_candidates(tracks: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    artist_counts: dict[str, int] = {}
    cluster_counts: dict[str, int] = {}

    for track in tracks:
        artists = track.get("artists", []) or []
        artist_key = normalize_text(artists[0]) if artists else ""
        cluster_key = normalize_text(track.get("cluster"))

        if artist_key and artist_counts.get(artist_key, 0) >= 2:
            continue
        if cluster_key and cluster_counts.get(cluster_key, 0) >= 8:
            continue

        if artist_key:
            artist_counts[artist_key] = artist_counts.get(artist_key, 0) + 1
        if cluster_key:
            cluster_counts[cluster_key] = cluster_counts.get(cluster_key, 0) + 1

        selected.append(track)
        if len(selected) >= limit:
            break

    return selected


def select_dataset_candidates(
    *,
    profile: dict[str, Any],
    affinity_context: dict[str, Any] | None = None,
    limit: int = 80,
) -> list[dict[str, Any]]:
    raw_tracks = load_catalog_tracks(limit=max(limit * 12, 1000))
    if not raw_tracks:
        return []

    goal = profile.get("goal", "energia")
    target_energy = _safe_float(profile.get("target_energy"))
    target_valence = _safe_float(profile.get("target_valence"))
    target_danceability = _safe_float(profile.get("target_danceability"))

    scored: list[dict[str, Any]] = []

    for track in raw_tracks:
        if not _passes_hard_filters(track, profile):
            continue

        energy = _safe_float(track.get("energy_feature"))
        valence = _safe_float(track.get("valence_feature"))
        danceability = _safe_float(track.get("danceability"))
        bpm = _safe_float(track.get("bpm")) or _safe_float(track.get("tempo"))

        reasons: list[str] = []
        score = 0.0

        energy_delta = _closeness_score(energy, target_energy, 18.0)
        valence_delta = _closeness_score(valence, target_valence, 18.0)
        dance_delta = _closeness_score(danceability, target_danceability, 14.0)
        score += energy_delta + valence_delta + dance_delta

        if energy_delta:
            reasons.append(f"catalog:energy_fit:+{round(energy_delta, 2)}")
        if valence_delta:
            reasons.append(f"catalog:valence_fit:+{round(valence_delta, 2)}")
        if dance_delta:
            reasons.append(f"catalog:danceability_fit:+{round(dance_delta, 2)}")

        tempo_delta, tempo_reasons = _tempo_alignment_score(bpm, goal)
        goal_delta, goal_reasons = _goal_field_score(track, goal)
        seed_delta, seed_reasons = _seed_term_score(track, profile)
        popularity_delta, popularity_reasons = _popularity_alignment(track, profile)
        affinity_delta, affinity_reasons = _affinity_alignment(track, affinity_context)
        functional_delta, functional_reasons = _functional_profile_alignment(
            track,
            profile,
        )
        activation_delta, activation_reasons = _activation_style_alignment(
            track,
            profile,
        )
        companionship_delta, companionship_reasons = _companionship_catalog_adjustment(
            track,
            profile,
        )

        score += (
            tempo_delta
            + goal_delta
            + seed_delta
            + popularity_delta
            + affinity_delta
            + functional_delta
            + activation_delta
            + companionship_delta
        )
        reasons.extend(tempo_reasons)
        reasons.extend(goal_reasons)
        reasons.extend(seed_reasons)
        reasons.extend(popularity_reasons)
        reasons.extend(affinity_reasons)
        reasons.extend(functional_reasons)
        reasons.extend(activation_reasons)
        reasons.extend(companionship_reasons)

        enriched_track = dict(track)
        enriched_track["_catalog_score"] = round(score, 2)
        enriched_track["_catalog_reasons"] = reasons
        enriched_track["selection_source"] = "msd_catalog"
        enriched_track["_feature_source"] = enriched_track.get("_feature_source") or "msd_catalog"
        enriched_track["_feature_match"] = enriched_track.get("_feature_match") or "catalog_track_id"

        scored.append(enriched_track)

    scored.sort(key=lambda item: item.get("_catalog_score", 0.0), reverse=True)
    return _diversify_candidates(scored, limit=limit)
