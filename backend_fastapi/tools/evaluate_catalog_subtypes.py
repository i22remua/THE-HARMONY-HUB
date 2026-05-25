from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.services.professional_playlist_model_service as profile_service
from app.services.dataset_recommendation_service import select_dataset_candidates


@dataclass(frozen=True)
class EvaluationScenario:
    name: str
    description: str
    inputs: dict[str, Any]


SCENARIOS: tuple[EvaluationScenario, ...] = (
    EvaluationScenario(
        name="deep_focus",
        description="Foco instrumental estable para concentracion profunda.",
        inputs={
            "goal": "foco",
            "mood": "neutral",
            "stress_level": 3,
            "energy_level": 3,
            "noise_category": "quiet",
            "vocal_preference": "instrumental",
            "intensity_preference": "suave",
            "exploration_preference": "equilibrado",
            "popularity_preference": "mixta",
            "session_duration_min": 25,
            "desired_outcome": "mas_centrado",
            "environment_context": "Silencio estable",
            "use_environment": True,
        },
    ),
    EvaluationScenario(
        name="alert_focus",
        description="Foco con algo mas de impulso para cansancio leve.",
        inputs={
            "goal": "foco",
            "mood": "cansado",
            "stress_level": 2,
            "energy_level": 2,
            "noise_category": "moderate",
            "vocal_preference": "instrumental",
            "intensity_preference": "media",
            "exploration_preference": "equilibrado",
            "popularity_preference": "alternativa",
            "session_duration_min": 25,
            "desired_outcome": "mas_despierto",
            "environment_context": "Oficina tranquila",
            "use_environment": True,
        },
    ),
    EvaluationScenario(
        name="stable_relaxation",
        description="Relajacion suave, segura y poco invasiva.",
        inputs={
            "goal": "relajacion",
            "mood": "estresado",
            "stress_level": 5,
            "energy_level": 2,
            "noise_category": "quiet",
            "vocal_preference": "indistinto",
            "intensity_preference": "suave",
            "exploration_preference": "equilibrado",
            "popularity_preference": "mixta",
            "session_duration_min": 25,
            "desired_outcome": "mas_calmado",
            "environment_context": "Casa en silencio",
            "use_environment": True,
        },
    ),
    EvaluationScenario(
        name="warm_relaxation",
        description="Relajacion acompanada, mas calida y humana.",
        inputs={
            "goal": "relajacion",
            "mood": "triste",
            "stress_level": 4,
            "energy_level": 2,
            "noise_category": "quiet",
            "vocal_preference": "con_voz",
            "intensity_preference": "suave",
            "exploration_preference": "familiar",
            "popularity_preference": "mixta",
            "session_duration_min": 20,
            "desired_outcome": "mas_acompanado",
            "environment_context": "Noche tranquila",
            "use_environment": True,
        },
    ),
    EvaluationScenario(
        name="soft_activation",
        description="Subida de energia progresiva sin agresividad.",
        inputs={
            "goal": "energia",
            "mood": "cansado",
            "stress_level": 2,
            "energy_level": 1,
            "noise_category": "active",
            "vocal_preference": "con_voz",
            "intensity_preference": "suave",
            "exploration_preference": "familiar",
            "popularity_preference": "mainstream",
            "session_duration_min": 20,
            "desired_outcome": "mas_despierto",
            "environment_context": "Camino al trabajo",
            "use_environment": True,
        },
    ),
    EvaluationScenario(
        name="warm_companionship",
        description="Energia emocionalmente acompanada y calida.",
        inputs={
            "goal": "energia",
            "mood": "triste",
            "stress_level": 4,
            "energy_level": 2,
            "noise_category": "quiet",
            "vocal_preference": "con_voz",
            "intensity_preference": "suave",
            "exploration_preference": "familiar",
            "popularity_preference": "mainstream",
            "session_duration_min": 20,
            "desired_outcome": "mas_acompanado",
            "environment_context": "Silencio estable",
            "use_environment": True,
        },
    ),
    EvaluationScenario(
        name="peak_energy",
        description="Energia alta con tolerancia a picos y tracks mas directos.",
        inputs={
            "goal": "energia",
            "mood": "neutral",
            "stress_level": 2,
            "energy_level": 4,
            "noise_category": "active",
            "vocal_preference": "con_voz",
            "intensity_preference": "alta",
            "exploration_preference": "familiar",
            "popularity_preference": "mainstream",
            "session_duration_min": 20,
            "desired_outcome": "mas_animado",
            "environment_context": "Gimnasio",
            "use_environment": True,
        },
    ),
)


def _scenario_map() -> dict[str, EvaluationScenario]:
    return {scenario.name: scenario for scenario in SCENARIOS}


def _build_profile(scenario: EvaluationScenario, user_id: str, use_real_preferences: bool) -> dict[str, Any]:
    if not use_real_preferences:
        profile_service.get_user_generation_preferences = lambda _user_id: {}

    return profile_service.build_generation_profile(
        user_id=user_id,
        **scenario.inputs,
    )


def _summarize_candidates(candidates: list[dict[str, Any]], top_n: int) -> dict[str, Any]:
    visible = candidates[:top_n]
    genre_counter = Counter((item.get("genre") or "unknown") for item in visible)
    cluster_counter = Counter((item.get("cluster") or "unknown") for item in visible)
    activation_counter = Counter(
        (item.get("activation_style") or "unknown") for item in visible
    )

    top_tracks = []
    for item in visible:
        top_tracks.append(
            {
                "msd_track_id": item.get("msd_track_id"),
                "title": item.get("title"),
                "artist_name": item.get("artist_name"),
                "genre": item.get("genre"),
                "cluster": item.get("cluster"),
                "activation_style": item.get("activation_style"),
                "score": item.get("_catalog_score"),
                "energy": item.get("energy_feature"),
                "valence": item.get("valence_feature"),
                "danceability": item.get("danceability"),
                "warmth_score": item.get("warmth_score"),
                "steadiness_score": item.get("steadiness_score"),
                "vocal_presence_score": item.get("vocal_presence_score"),
                "supportiveness_score": item.get("supportiveness_score"),
                "tension_score": item.get("tension_score"),
            }
        )

    return {
        "candidate_count": len(candidates),
        "top_genres": genre_counter.most_common(8),
        "top_clusters": cluster_counter.most_common(8),
        "top_activation_styles": activation_counter.most_common(6),
        "top_tracks": top_tracks,
    }


def evaluate_scenario(
    scenario_name: str,
    *,
    user_id: str = "catalog_eval_user",
    top_n: int = 10,
    limit: int = 40,
    use_real_preferences: bool = False,
) -> dict[str, Any]:
    scenario = _scenario_map().get(scenario_name)
    if not scenario:
        valid = ", ".join(item.name for item in SCENARIOS)
        raise ValueError(f"Unknown scenario '{scenario_name}'. Valid: {valid}")

    profile = _build_profile(
        scenario=scenario,
        user_id=user_id,
        use_real_preferences=use_real_preferences,
    )
    candidates = select_dataset_candidates(
        profile=profile,
        affinity_context={},
        limit=limit,
    )

    return {
        "scenario": scenario.name,
        "description": scenario.description,
        "inputs": scenario.inputs,
        "profile": {
            "recommended_mode": profile.get("recommended_mode"),
            "session_subtype": profile.get("session_subtype"),
            "activation_curve": profile.get("activation_curve"),
            "seed_genres": profile.get("seed_genres"),
            "primary_queries": profile.get("primary_queries"),
            "target_energy": profile.get("target_energy"),
            "target_valence": profile.get("target_valence"),
            "target_danceability": profile.get("target_danceability"),
            "target_warmth": profile.get("target_warmth"),
            "target_steadiness": profile.get("target_steadiness"),
            "target_vocal_presence": profile.get("target_vocal_presence"),
        },
        "summary": _summarize_candidates(candidates, top_n=top_n),
    }


def _format_report(result: dict[str, Any]) -> str:
    profile = result["profile"]
    summary = result["summary"]

    lines = [
        f"SCENARIO: {result['scenario']}",
        f"DESCRIPTION: {result['description']}",
        (
            "PROFILE: "
            f"subtype={profile.get('session_subtype')} | "
            f"curve={profile.get('activation_curve')} | "
            f"mode={profile.get('recommended_mode')}"
        ),
        (
            "TARGETS: "
            f"energy={round(float(profile.get('target_energy', 0.0)), 2)} | "
            f"valence={round(float(profile.get('target_valence', 0.0)), 2)} | "
            f"danceability={round(float(profile.get('target_danceability', 0.0)), 2)} | "
            f"warmth={round(float(profile.get('target_warmth', 0.0)), 2)} | "
            f"steadiness={round(float(profile.get('target_steadiness', 0.0)), 2)} | "
            f"vocal={round(float(profile.get('target_vocal_presence', 0.0)), 2)}"
        ),
        f"SEED_GENRES: {', '.join(profile.get('seed_genres') or [])}",
        f"PRIMARY_QUERIES: {', '.join(profile.get('primary_queries') or [])}",
        f"CANDIDATES: {summary['candidate_count']}",
        f"TOP_GENRES: {summary['top_genres']}",
        f"TOP_CLUSTERS: {summary['top_clusters']}",
        f"TOP_ACTIVATION_STYLES: {summary['top_activation_styles']}",
        "TOP_TRACKS:",
    ]

    for item in summary["top_tracks"]:
        lines.append(
            "  - "
            f"{item.get('title')} | {item.get('artist_name')} | "
            f"genre={item.get('genre')} | cluster={item.get('cluster')} | "
            f"style={item.get('activation_style')} | score={item.get('score')} | "
            f"energy={item.get('energy')} | valence={item.get('valence')} | "
            f"warmth={item.get('warmth_score')} | support={item.get('supportiveness_score')}"
        )

    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evalua el catalogo MSD por subtipo funcional y mezcla de generos."
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="Escenario a ejecutar. Puede repetirse. Por defecto ejecuta todos.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=8,
        help="Numero de tracks a mostrar en el resumen.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Numero de candidatos a pedir al selector antes de resumir.",
    )
    parser.add_argument(
        "--user-id",
        default="catalog_eval_user",
        help="User id usado al construir el generation_profile.",
    )
    parser.add_argument(
        "--use-real-preferences",
        action="store_true",
        help="Usa preferencias reales del usuario en lugar de un perfil vacio.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime la salida en JSON en vez de texto legible.",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="Lista los escenarios disponibles y sale.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.list_scenarios:
        for scenario in SCENARIOS:
            print(f"{scenario.name}: {scenario.description}")
        return 0

    scenario_names = args.scenarios or [scenario.name for scenario in SCENARIOS]
    results = [
        evaluate_scenario(
            scenario_name,
            user_id=args.user_id,
            top_n=args.top_n,
            limit=args.limit,
            use_real_preferences=args.use_real_preferences,
        )
        for scenario_name in scenario_names
    ]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    for index, result in enumerate(results):
        if index:
            print()
            print("=" * 80)
            print()
        print(_format_report(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
