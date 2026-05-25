from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.recommendation import RecommendationRequest
from app.services.recommender_service import _build_dynamic_candidates
from app.services.session_mode_ml_service import (
    DEFAULT_MIN_SELECTED_MODE_PROBABILITY,
    MIN_BALANCED_ACCURACY,
    MIN_QUALITY_SCORE,
    MIN_ROC_AUC,
    MIN_TOTAL_EXAMPLES,
    get_min_selected_mode_probability,
    get_model_quality_metadata,
    model_available,
    rank_recommendation_candidates,
)


@dataclass(frozen=True)
class MlScenario:
    name: str
    description: str
    payload: RecommendationRequest


SCENARIOS: tuple[MlScenario, ...] = (
    MlScenario(
        name="focus_deep",
        description="Foco instrumental para concentracion estable.",
        payload=RecommendationRequest(
            spotify_user_id="xabi05",
            mood="neutral",
            goal="foco",
            stress_level=3,
            energy_level=3,
            noise_category="quiet",
            vocal_preference="instrumental",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=25,
            desired_outcome="mas_centrado",
            use_environment=True,
        ),
    ),
    MlScenario(
        name="relax_calm",
        description="Relajacion suave para bajar activacion.",
        payload=RecommendationRequest(
            spotify_user_id="xabi05",
            mood="estresado",
            goal="relajacion",
            stress_level=5,
            energy_level=2,
            noise_category="quiet",
            vocal_preference="indistinto",
            intensity_preference="suave",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=25,
            desired_outcome="mas_calmado",
            use_environment=True,
        ),
    ),
    MlScenario(
        name="energy_awake",
        description="Energia para recuperar impulso sin dureza excesiva.",
        payload=RecommendationRequest(
            spotify_user_id="xabi05",
            mood="neutral",
            goal="energia",
            stress_level=2,
            energy_level=3,
            noise_category="quiet",
            vocal_preference="con_voz",
            intensity_preference="media",
            exploration_preference="equilibrado",
            popularity_preference="mixta",
            session_duration_min=20,
            desired_outcome="mas_despierto",
            use_environment=True,
        ),
    ),
    MlScenario(
        name="energy_companionship",
        description="Energia acompanada para estado emocional sensible.",
        payload=RecommendationRequest(
            spotify_user_id="xabi05",
            mood="triste",
            goal="energia",
            stress_level=4,
            energy_level=2,
            noise_category="quiet",
            vocal_preference="con_voz",
            intensity_preference="suave",
            exploration_preference="familiar",
            popularity_preference="mainstream",
            session_duration_min=20,
            desired_outcome="mas_acompanado",
            use_environment=True,
        ),
    ),
)


def _scenario_map() -> dict[str, MlScenario]:
    return {scenario.name: scenario for scenario in SCENARIOS}


def _context_from_payload(payload: RecommendationRequest) -> dict[str, Any]:
    return {
        "goal": payload.goal,
        "mood": payload.mood,
        "stress_level": payload.stress_level,
        "energy_level": payload.energy_level,
        "noise_category": payload.noise_category if payload.use_environment else None,
        "use_environment": payload.use_environment,
        "vocal_preference": payload.vocal_preference,
        "intensity_preference": payload.intensity_preference,
        "exploration_preference": payload.exploration_preference,
        "popularity_preference": payload.popularity_preference,
        "session_duration_min": payload.session_duration_min,
        "desired_outcome": payload.desired_outcome,
    }


def _candidate_snapshot(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "recommended_mode": candidate.get("recommended_mode"),
        "target_energy": candidate.get("target_energy"),
        "target_valence": candidate.get("target_valence"),
        "target_bpm_range": candidate.get("target_bpm_range"),
        "heuristic_score": round(float(candidate.get("_base_score", candidate.get("_score", 0.0)) or 0.0), 2),
        "final_score": round(float(candidate.get("_score", 0.0) or 0.0), 2),
        "mode_ml_probability": candidate.get("_mode_ml_probability"),
        "mode_ml_delta": candidate.get("_mode_ml_delta"),
        "selection_source": candidate.get("_selection_source"),
    }


def _evaluate_scenario(scenario: MlScenario) -> dict[str, Any]:
    candidates = _build_dynamic_candidates(scenario.payload)
    context = _context_from_payload(scenario.payload)

    heuristic_ranked = sorted(
        deepcopy(candidates),
        key=lambda item: float(item.get("_score", 0.0)),
        reverse=True,
    )
    ml_ranked = rank_recommendation_candidates(deepcopy(candidates), context)

    probabilities = [
        float(item.get("_mode_ml_probability"))
        for item in ml_ranked
        if item.get("_mode_ml_probability") is not None
    ]
    probability_spread = (
        round(max(probabilities) - min(probabilities), 4)
        if probabilities
        else None
    )

    heuristic_top = heuristic_ranked[0] if heuristic_ranked else {}
    ml_top = ml_ranked[0] if ml_ranked else {}
    selection_source = str(ml_top.get("_selection_source") or "")
    model_scored_candidates = bool(probabilities)
    ml_applied_to_ranking = selection_source == "session_ml"
    heuristic_fallback_due_to_low_confidence = (
        selection_source == "heuristic_low_ml_confidence"
    )

    return {
        "scenario": scenario.name,
        "description": scenario.description,
        "context": context,
        "heuristic_top": _candidate_snapshot(heuristic_top),
        "ml_top": _candidate_snapshot(ml_top),
        "top_mode_changed": heuristic_top.get("recommended_mode") != ml_top.get("recommended_mode"),
        "probability_spread": probability_spread,
        "model_scored_candidates": model_scored_candidates,
        "ml_applied_to_ranking": ml_applied_to_ranking,
        "heuristic_fallback_due_to_low_confidence": heuristic_fallback_due_to_low_confidence,
        "ml_candidates": [_candidate_snapshot(item) for item in ml_ranked],
    }


def _metadata_evidence() -> dict[str, Any]:
    metadata = get_model_quality_metadata() or {}
    metrics = metadata.get("metrics", {}) or {}

    return {
        "model_available_now": model_available(),
        "trained_at": metadata.get("trained_at"),
        "total_examples": metadata.get("total_examples"),
        "class_counts": metadata.get("class_counts"),
        "model_gate_passed": metadata.get("model_gate_passed"),
        "quality_gate_passed": metadata.get("quality_gate_passed"),
        "quality_score": metadata.get("quality_score"),
        "mood_coverage": metadata.get("mood_coverage"),
        "balanced_accuracy_mean": metrics.get("balanced_accuracy_mean"),
        "roc_auc_mean": metrics.get("roc_auc_mean"),
        "f1_mean": metrics.get("f1_mean"),
        "thresholds": {
            "min_total_examples": MIN_TOTAL_EXAMPLES,
            "min_balanced_accuracy": MIN_BALANCED_ACCURACY,
            "min_roc_auc": MIN_ROC_AUC,
            "min_quality_score": MIN_QUALITY_SCORE,
            "min_selected_mode_probability": get_min_selected_mode_probability(metadata),
            "default_min_selected_mode_probability": DEFAULT_MIN_SELECTED_MODE_PROBABILITY,
        },
    }


def _format_report(payload: dict[str, Any]) -> str:
    metadata = payload["metadata"]
    scenarios = payload["scenarios"]

    lines = [
        "=== Session ML Verification ===",
        f"model_available_now: {metadata.get('model_available_now')}",
        f"trained_at: {metadata.get('trained_at')}",
        f"total_examples: {metadata.get('total_examples')}",
        f"class_counts: {metadata.get('class_counts')}",
        f"model_gate_passed: {metadata.get('model_gate_passed')}",
        f"quality_gate_passed: {metadata.get('quality_gate_passed')}",
        f"quality_score: {metadata.get('quality_score')}",
        f"mood_observability: {metadata.get('mood_coverage')}",
        (
            "metrics: "
            f"balanced_accuracy={metadata.get('balanced_accuracy_mean')} | "
            f"roc_auc={metadata.get('roc_auc_mean')} | "
            f"f1={metadata.get('f1_mean')}"
        ),
        (
            "thresholds: "
            f"examples>={metadata['thresholds']['min_total_examples']} | "
            f"balanced_accuracy>={metadata['thresholds']['min_balanced_accuracy']} | "
            f"roc_auc>={metadata['thresholds']['min_roc_auc']} | "
            f"quality_score>={metadata['thresholds']['min_quality_score']} | "
            "selected_mode_probability>="
            f"{metadata['thresholds']['min_selected_mode_probability']}"
        ),
    ]

    for scenario in scenarios:
        lines.extend(
            [
                "",
                f"SCENARIO: {scenario['scenario']}",
                f"DESCRIPTION: {scenario['description']}",
                f"heuristic_top: {scenario['heuristic_top']}",
                f"ml_top: {scenario['ml_top']}",
                f"model_scored_candidates: {scenario['model_scored_candidates']}",
                f"ml_applied_to_ranking: {scenario['ml_applied_to_ranking']}",
                "heuristic_fallback_due_to_low_confidence: "
                f"{scenario['heuristic_fallback_due_to_low_confidence']}",
                f"top_mode_changed: {scenario['top_mode_changed']}",
                f"probability_spread: {scenario['probability_spread']}",
                "candidates:",
            ]
        )
        for item in scenario["ml_candidates"]:
            lines.append(
                "  - "
                f"{item['recommended_mode']} | heuristic={item['heuristic_score']} | "
                f"ml_prob={item['mode_ml_probability']} | ml_delta={item['mode_ml_delta']} | "
                f"final={item['final_score']} | source={item['selection_source']}"
            )

    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Comprueba y evidencia el funcionamiento del modelo de sesion ML."
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="Escenario a ejecutar. Puede repetirse. Por defecto ejecuta todos.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime el informe en JSON.",
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

    selected_names = args.scenarios or [scenario.name for scenario in SCENARIOS]
    selected: list[MlScenario] = []
    available = _scenario_map()

    for name in selected_names:
        scenario = available.get(name)
        if scenario is None:
            valid = ", ".join(available)
            raise SystemExit(f"Unknown scenario '{name}'. Valid: {valid}")
        selected.append(scenario)

    payload = {
        "metadata": _metadata_evidence(),
        "scenarios": [_evaluate_scenario(scenario) for scenario in selected],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_format_report(payload))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
