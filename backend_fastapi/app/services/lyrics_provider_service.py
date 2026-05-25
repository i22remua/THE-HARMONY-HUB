from __future__ import annotations

from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _stringify_labels(track: dict) -> list[str]:
    labels = track.get("labels", []) or []
    output: list[str] = []

    for label in labels:
        text = _normalize_text(label).lower()
        if text:
            output.append(text)

    return list(dict.fromkeys(output))


def _build_feature_description(track: dict) -> str:
    parts: list[str] = []

    bpm = _safe_float(track.get("bpm"))
    energy = _safe_float(track.get("energy_feature"))
    valence = _safe_float(track.get("valence_feature"))
    danceability = _safe_float(track.get("danceability"))
    instrumentalness = _safe_float(track.get("instrumentalness"))
    acousticness = _safe_float(track.get("acousticness"))
    speechiness = _safe_float(track.get("speechiness"))

    if bpm is not None:
        if bpm < 75:
            parts.append("slow tempo")
        elif bpm < 110:
            parts.append("steady tempo")
        else:
            parts.append("fast tempo")

    if energy is not None:
        if energy < 0.30:
            parts.append("low energy")
        elif energy < 0.65:
            parts.append("moderate energy")
        else:
            parts.append("high energy")

    if valence is not None:
        if valence < 0.35:
            parts.append("melancholic tone")
        elif valence < 0.65:
            parts.append("balanced emotional tone")
        else:
            parts.append("bright emotional tone")

    if danceability is not None:
        if danceability >= 0.70:
            parts.append("danceable rhythm")
        elif danceability <= 0.25:
            parts.append("non dance focused")

    if instrumentalness is not None and instrumentalness >= 0.45:
        parts.append("instrumental")

    if acousticness is not None and acousticness >= 0.55:
        parts.append("acoustic texture")

    if speechiness is not None and speechiness >= 0.45:
        parts.append("spoken or speech-like delivery")

    return ", ".join(parts)


def _derive_semantic_description(track: dict) -> str:
    labels = _stringify_labels(track)
    label_text = " ".join(labels)

    title = _normalize_text(track.get("name"))
    artists = ", ".join(track.get("artists", []) or [])
    feature_description = _build_feature_description(track)

    fragments: list[str] = []

    if title:
        fragments.append(f"title {title}")
    if artists:
        fragments.append(f"artist {artists}")
    if label_text:
        fragments.append(f"labels {label_text}")
    if feature_description:
        fragments.append(feature_description)

    # Reglas semánticas simples a partir de labels
    label_set = set(labels)

    if {"focus", "study", "deep"} & label_set:
        fragments.append("supports concentration and mental clarity")

    if {"ambient", "calm", "relax", "chill", "soft"} & label_set:
        fragments.append("soft relaxing calming atmosphere")

    if {"energy", "workout", "party", "club"} & label_set:
        fragments.append("activating energetic uplifting atmosphere")

    if {"instrumental", "acoustic", "piano"} & label_set:
        fragments.append("less vocal presence and more instrumental texture")

    if {"sad", "lonely", "cry"} & label_set:
        fragments.append("emotionally heavy introspective atmosphere")

    if {"warm", "comfort", "gentle"} & label_set:
        fragments.append("warm comforting supportive emotional tone")

    return ". ".join(fragment for fragment in fragments if fragment).strip()


def build_track_text_bundle(track: dict) -> dict:
    """
    Construye un bundle textual listo para NLP.
    Si en el futuro integras un proveedor externo de lyrics,
    solo tendrás que rellenar lyrics_text dentro del track o aquí.
    """
    title = _normalize_text(track.get("name"))
    artists = ", ".join(track.get("artists", []) or [])
    labels = _stringify_labels(track)

    lyrics_text = _normalize_text(
        track.get("lyrics_text")
        or track.get("lyrics")
        or track.get("full_lyrics")
    )

    description_text = _normalize_text(
        track.get("description_text")
        or track.get("description")
        or track.get("semantic_description")
    )

    derived_description = _derive_semantic_description(track)

    combined_parts = [
        f"title: {title}" if title else "",
        f"artists: {artists}" if artists else "",
        f"labels: {' '.join(labels)}" if labels else "",
        f"description: {description_text}" if description_text else "",
        f"derived_description: {derived_description}" if derived_description else "",
        f"lyrics: {lyrics_text}" if lyrics_text else "",
    ]

    combined_text = " ".join(part for part in combined_parts if part).strip()

    return {
        "title": title,
        "artists": artists,
        "labels": labels,
        "lyrics_text": lyrics_text,
        "description_text": description_text,
        "derived_description": derived_description,
        "combined_text": combined_text,
        "lyrics_available": bool(lyrics_text),
        "description_available": bool(description_text or derived_description),
    }