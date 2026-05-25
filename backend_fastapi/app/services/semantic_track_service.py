from __future__ import annotations

from typing import Any

from app.services.lyrics_nlp_service import analyze_song_text, cosine_similarity, embed_text
from app.services.lyrics_provider_service import build_track_text_bundle


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def build_user_semantic_text(
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    noise_category: str,
    vocal_preference: str,
    intensity_preference: str,
    environment_context: str | None = None,
) -> str:
    fragments: list[str] = [
        f"goal {goal}",
        f"mood {mood}",
        f"noise {noise_category}",
        f"vocal_preference {vocal_preference}",
        f"intensity_preference {intensity_preference}",
    ]

    if desired_outcome:
        fragments.append(f"desired_outcome {desired_outcome}")

    if environment_context:
        fragments.append(f"environment_context {environment_context}")

    if goal == "relajacion":
        fragments.append(
            "looking for calm relief comfort breathing soft stable emotional release"
        )
    elif goal == "foco":
        fragments.append(
            "looking for concentration clarity stable attention minimal distraction steady focus"
        )
    elif goal == "energia":
        fragments.append(
            "looking for uplift activation movement brighter emotional energy motivation"
        )

    if mood == "estresado":
        fragments.append("avoid harsh tension overload chaotic verbal aggression")
    elif mood == "triste":
        fragments.append("prefer support warmth lightness hope companionship")
    elif mood == "cansado":
        fragments.append("prefer gentle activation not abrupt intensity")
    elif mood == "feliz":
        fragments.append("keep bright uplifting positive emotional tone")

    if desired_outcome == "mas_calmado":
        fragments.append("prefer calm stable warm soothing reassuring songs")
    elif desired_outcome == "mas_centrado":
        fragments.append("prefer focused clear minimal steady mentally clean songs")
    elif desired_outcome == "mas_ligero":
        fragments.append("prefer lighter hopeful easy warm songs")
    elif desired_outcome == "mas_acompanado":
        fragments.append("prefer warm supportive human emotionally close songs")
    elif desired_outcome in {"mas_despierto", "mas_animado"}:
        fragments.append("prefer energizing uplifting moving brighter songs")

    if vocal_preference == "instrumental":
        fragments.append("prefer low verbal load instrumental atmosphere")
    elif vocal_preference == "con_voz":
        fragments.append("vocal presence can help emotional accompaniment")

    if intensity_preference == "suave":
        fragments.append("avoid aggressive explosive textual tone")
    elif intensity_preference == "alta":
        fragments.append("can tolerate stronger activation and expressive tone")

    return " ".join(fragment for fragment in fragments if fragment).strip()


def compute_textual_adjustment(
    track: dict,
    *,
    goal: str,
    mood: str,
    desired_outcome: str | None,
    noise_category: str,
    vocal_preference: str,
    intensity_preference: str,
    environment_context: str | None = None,
) -> tuple[float, list[str], dict]:
    text_bundle = build_track_text_bundle(track)
    combined_text = text_bundle["combined_text"]

    if not combined_text:
        metadata = {
            "lyrics_available": False,
            "description_available": False,
            "text_profile": {},
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "semantic_similarity": 0.0,
        }
        return 0.0, [], metadata

    user_text = build_user_semantic_text(
        goal=goal,
        mood=mood,
        desired_outcome=desired_outcome,
        noise_category=noise_category,
        vocal_preference=vocal_preference,
        intensity_preference=intensity_preference,
        environment_context=environment_context,
    )

    analysis = analyze_song_text(combined_text)
    query_embedding = embed_text(user_text)
    similarity = cosine_similarity(query_embedding, analysis["embedding"])

    text_profile = analysis["text_profile"]
    sentiment_label = analysis["sentiment_label"]
    sentiment_score = analysis["sentiment_score"]

    calm = _safe_float(text_profile.get("calm")) or 0.0
    focus = _safe_float(text_profile.get("focus")) or 0.0
    uplift = _safe_float(text_profile.get("uplift")) or 0.0
    warmth = _safe_float(text_profile.get("warmth")) or 0.0
    tension = _safe_float(text_profile.get("tension")) or 0.0
    sadness = _safe_float(text_profile.get("sadness")) or 0.0

    delta = 0.0
    reasons: list[str] = []

    semantic_bonus = round(similarity * 12.0, 2)
    delta += semantic_bonus
    reasons.append(f"text_semantic_similarity:+{semantic_bonus}")

    if goal == "relajacion":
        bonus = calm * 8.0 + warmth * 4.0
        penalty = tension * 9.0
        delta += bonus - penalty
        reasons.append(f"text_relax_profile:{round(bonus - penalty, 2):+}")

    elif goal == "foco":
        bonus = focus * 9.0 + calm * 3.0
        penalty = tension * 6.0 + sadness * 2.0
        delta += bonus - penalty
        reasons.append(f"text_focus_profile:{round(bonus - penalty, 2):+}")

    elif goal == "energia":
        bonus = uplift * 9.0 + warmth * 2.0
        penalty = sadness * 6.0
        delta += bonus - penalty
        reasons.append(f"text_energy_profile:{round(bonus - penalty, 2):+}")

    if desired_outcome == "mas_calmado":
        value = calm * 6.0 + warmth * 2.5 - tension * 7.0
        delta += value
        reasons.append(f"text_outcome_calm:{round(value, 2):+}")

    elif desired_outcome == "mas_centrado":
        value = focus * 7.0 + calm * 2.0 - tension * 4.0
        delta += value
        reasons.append(f"text_outcome_focus:{round(value, 2):+}")

    elif desired_outcome == "mas_ligero":
        value = uplift * 5.5 + warmth * 2.0 - sadness * 5.0
        delta += value
        reasons.append(f"text_outcome_light:{round(value, 2):+}")

    elif desired_outcome == "mas_acompanado":
        value = warmth * 6.0 + calm * 1.5
        delta += value
        reasons.append(f"text_outcome_supported:{round(value, 2):+}")

    elif desired_outcome in {"mas_despierto", "mas_animado"}:
        value = uplift * 7.0 - sadness * 3.5
        delta += value
        reasons.append(f"text_outcome_awake:{round(value, 2):+}")

    if mood == "triste":
        if sadness > 0.75 and uplift < 0.20 and warmth < 0.20:
            delta -= 5.0
            reasons.append("text_mood_too_heavy:-5.0")

    if mood == "estresado":
        if tension > 0.65:
            delta -= 6.5
            reasons.append("text_mood_too_tense:-6.5")

    metadata = {
        "lyrics_available": text_bundle["lyrics_available"],
        "description_available": text_bundle["description_available"],
        "text_profile": text_profile,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "semantic_similarity": round(similarity, 4),
        "text_source_preview": combined_text[:220],
    }

    return round(delta, 2), reasons, metadata
