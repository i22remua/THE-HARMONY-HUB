from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODEL_CARD_PATH = Path("app/ml/models/session_mode_model_card.json")


def _round_float(value: Any, digits: int = 4) -> float | None:
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except Exception:
        return None


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _humanize_feature_name(name: str) -> str:
    text = str(name)
    if "__" in text:
        _, text = text.split("__", 1)

    categorical_prefixes = (
        "goal_",
        "mood_",
        "noise_category_",
        "vocal_preference_",
        "intensity_preference_",
        "exploration_preference_",
        "popularity_preference_",
        "desired_outcome_",
        "recommended_mode_",
        "target_energy_",
        "target_valence_",
        "target_bpm_range_",
        "catalog_noise_category_",
    )
    for prefix in categorical_prefixes:
        if text.startswith(prefix):
            return f"{prefix[:-1]}={text[len(prefix):]}"

    return text


def _feature_names_from_pipeline(pipeline) -> list[str]:
    preprocessor = pipeline.named_steps["preprocessor"]
    # Recuperamos los nombres después del preprocesado real, porque la
    # regresión logística opera en ese espacio expandido y no sobre campos
    # brutos del usuario.
    names = preprocessor.get_feature_names_out()
    return [str(name) for name in names]


def _coefficient_summary(feature_names: list[str], coefficients, top_n: int = 12) -> dict[str, Any]:
    # Resumimos los coeficientes más influyentes para defender qué señales
    # empujan a favor o en contra de helpful=1 en el modelo global.
    feature_rows = []
    for feature_name, coefficient in zip(feature_names, coefficients):
        feature_rows.append(
            {
                "feature": feature_name,
                "label": _humanize_feature_name(feature_name),
                "coefficient": round(float(coefficient), 4),
            }
        )

    ordered_positive = sorted(feature_rows, key=lambda item: item["coefficient"], reverse=True)
    ordered_negative = sorted(feature_rows, key=lambda item: item["coefficient"])
    recommended_mode_rows = [
        row
        for row in feature_rows
        if row["feature"].endswith("recommended_mode")
        or "recommended_mode_" in row["feature"]
    ]
    recommended_mode_rows.sort(key=lambda item: abs(item["coefficient"]), reverse=True)

    return {
        "top_positive_features": ordered_positive[:top_n],
        "top_negative_features": ordered_negative[:top_n],
        "recommended_mode_feature_weights": recommended_mode_rows[: max(10, top_n)],
    }


def save_model_card(
    *,
    pipeline,
    metadata: dict[str, Any],
    feature_columns: list[str],
) -> dict[str, Any]:
    model = pipeline.named_steps["model"]
    # La model card actúa como artefacto estable de auditoría, memoria y
    # depuración; evita depender de logs efímeros del entrenamiento.
    feature_names = _feature_names_from_pipeline(pipeline)
    coefficients = getattr(model, "coef_", [[0.0] * len(feature_names)])[0]
    intercept = float(getattr(model, "intercept_", [0.0])[0])
    coefficient_summary = _coefficient_summary(feature_names, coefficients)

    payload = {
        "model_type": model.__class__.__name__,
        "trained_at": metadata.get("trained_at"),
        "total_examples": metadata.get("total_examples"),
        "class_counts": metadata.get("class_counts"),
        "feature_groups": {
            "raw_feature_columns": feature_columns,
            "transformed_feature_count": len(feature_names),
        },
        "quality_summary": {
            "model_gate_passed": metadata.get("model_gate_passed"),
            "quality_gate_passed": metadata.get("quality_gate_passed"),
            "quality_score": metadata.get("quality_score"),
            "model_readiness_reason": metadata.get("model_readiness_reason"),
            "metrics": metadata.get("metrics"),
        },
        "decision_thresholds": metadata.get("decision_thresholds"),
        "mood_coverage": metadata.get("mood_coverage"),
        "intercept": round(intercept, 4),
        "coefficient_summary": coefficient_summary,
        "explanation_notes": [
            "La regresion logistica estima helpful=1 a partir de una combinacion lineal de features transformadas.",
            "Coeficientes positivos empujan la prediccion hacia sesiones potencialmente utiles.",
            "Coeficientes negativos empujan la prediccion hacia helpful=0 o reducen confianza.",
        ],
    }

    MODEL_CARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_CARD_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return payload


def load_model_card() -> dict[str, Any] | None:
    if not MODEL_CARD_PATH.exists():
        return None
    try:
        return json.loads(MODEL_CARD_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _dense_contribution_vector(row, coefficients) -> list[float]:
    # Calculamos contribuciones locales ya en el espacio transformado del
    # pipeline, que es donde realmente vive la decisión lineal.
    if hasattr(row, "multiply") and hasattr(row, "toarray"):
        return row.multiply(coefficients).toarray().ravel().tolist()
    if hasattr(row, "toarray"):
        dense = row.toarray().ravel()
        return (dense * coefficients).tolist()
    return (row.ravel() * coefficients).tolist()


def explain_candidate_rows(
    *,
    pipeline,
    feature_frame,
    candidates: list[dict[str, Any]],
    top_n: int = 5,
) -> list[dict[str, Any]]:
    feature_names = _feature_names_from_pipeline(pipeline)
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]
    transformed = preprocessor.transform(feature_frame)
    coefficients = getattr(model, "coef_", [[0.0] * len(feature_names)])[0]
    intercept = float(getattr(model, "intercept_", [0.0])[0])

    explanations: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates):
        row = transformed[index]
        contributions = _dense_contribution_vector(row, coefficients)
        contribution_rows = []
        for feature_name, contribution in zip(feature_names, contributions):
            contribution_rows.append(
                {
                    "feature": feature_name,
                    "label": _humanize_feature_name(feature_name),
                    "contribution": round(float(contribution), 4),
                }
            )

        positive_rows = [
            item for item in contribution_rows if float(item["contribution"]) > 0.0
        ]
        negative_rows = [
            item for item in contribution_rows if float(item["contribution"]) < 0.0
        ]
        positive_rows.sort(key=lambda item: item["contribution"], reverse=True)
        negative_rows.sort(key=lambda item: item["contribution"])

        raw_probability = candidate.get("_mode_ml_probability")
        explanation = {
            "recommended_mode": candidate.get("recommended_mode"),
            "selection_source": candidate.get("_selection_source"),
            "probability": _round_float(raw_probability),
            "heuristic_score": _round_float(candidate.get("_base_score"), 2),
            "ml_delta": _round_float(candidate.get("_mode_ml_delta"), 2),
            "final_score": _round_float(candidate.get("_score"), 2),
            "decision_threshold": None,
            "intercept": round(intercept, 4),
            # `linear_score` es la suma interna antes de normalizar a
            # probabilidad; resulta útil para explicar dirección e intensidad.
            "linear_score": round(intercept + sum(float(value) for value in contributions), 4),
            "top_positive_signals": positive_rows[:top_n],
            "top_negative_signals": negative_rows[:top_n],
        }
        explanations.append(explanation)

    return explanations
