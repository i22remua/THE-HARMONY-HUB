from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.msd_catalog_service import load_catalog_tracks


REPORT_PATH = BACKEND_ROOT / "CATALOG_SUMMARY_REPORT.md"
JSON_PATH = BACKEND_ROOT / "catalog_summary_report.json"


def _safe_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100.0, 2)


def _top_counter(items: Counter[str], total: int, limit: int = 15) -> list[dict[str, Any]]:
    return [
        {"label": label, "count": count, "percent": _percent(count, total)}
        for label, count in items.most_common(limit)
    ]


def _goal_archetype(track: dict[str, Any]) -> str:
    scores = {
        "foco": _safe_float(track.get("focus_score")),
        "relajacion": _safe_float(track.get("calm_score")),
        "energia": _safe_float(track.get("uplift_score")),
    }
    return max(scores, key=scores.get)


def _bucket_avg(tracks: list[dict[str, Any]], field: str) -> float:
    values = [_safe_float(track.get(field)) for track in tracks if track.get(field) is not None]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def build_catalog_summary() -> dict[str, Any]:
    tracks = load_catalog_tracks(limit=None)
    total = len(tracks)

    genre_counts = Counter(str(track.get("genre") or "unknown") for track in tracks)
    cluster_counts = Counter(str(track.get("cluster") or "unknown") for track in tracks)
    activation_counts = Counter(
        str(track.get("activation_style") or "unknown") for track in tracks
    )
    source_counts = Counter(str(track.get("_catalog_source") or "unknown") for track in tracks)
    goal_counts = Counter(_goal_archetype(track) for track in tracks)

    summary = {
        "total_tracks": total,
        "top_genres": _top_counter(genre_counts, total),
        "top_clusters": _top_counter(cluster_counts, total),
        "top_activation_styles": _top_counter(activation_counts, total),
        "goal_archetypes": _top_counter(goal_counts, total, limit=10),
        "catalog_sources": _top_counter(source_counts, total, limit=10),
        "feature_averages": {
            "bpm": _bucket_avg(tracks, "bpm"),
            "energy_feature": _bucket_avg(tracks, "energy_feature"),
            "valence_feature": _bucket_avg(tracks, "valence_feature"),
            "danceability": _bucket_avg(tracks, "danceability"),
            "instrumentalness": _bucket_avg(tracks, "instrumentalness"),
            "acousticness": _bucket_avg(tracks, "acousticness"),
        },
    }
    return summary


def _markdown_table(rows: list[dict[str, Any]], label_name: str = "Etiqueta") -> str:
    lines = [f"| {label_name} | Conteo | % |", "|---|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['label']} | {row['count']} | {row['percent']} |")
    return "\n".join(lines)


def _build_markdown(summary: dict[str, Any]) -> str:
    total = summary["total_tracks"]
    feature_averages = summary["feature_averages"]

    return f"""# Catalog Summary Report

Resumen cuantitativo del catálogo musical actualmente disponible para Harmony Hub.

## Resumen general

- Total de tracks disponibles: `{total}`
- BPM medio: `{feature_averages['bpm']}`
- Energy media: `{feature_averages['energy_feature']}`
- Valence media: `{feature_averages['valence_feature']}`
- Danceability media: `{feature_averages['danceability']}`
- Instrumentalness media: `{feature_averages['instrumentalness']}`
- Acousticness media: `{feature_averages['acousticness']}`

## Top géneros

{_markdown_table(summary["top_genres"], label_name="Género")}

## Top clusters

{_markdown_table(summary["top_clusters"], label_name="Cluster")}

## Top activation styles

{_markdown_table(summary["top_activation_styles"], label_name="Activation style")}

## Arquetipo funcional dominante

Asignación aproximada según el mayor score entre `focus_score`, `calm_score` y `uplift_score`.

{_markdown_table(summary["goal_archetypes"], label_name="Arquetipo")}

## Fuentes del catálogo

{_markdown_table(summary["catalog_sources"], label_name="Fuente")}
"""


def main() -> None:
    summary = build_catalog_summary()
    JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(_build_markdown(summary), encoding="utf-8")
    print(f"Catalog summary generated: {REPORT_PATH}")
    print(f"Catalog summary JSON: {JSON_PATH}")


if __name__ == "__main__":
    main()
