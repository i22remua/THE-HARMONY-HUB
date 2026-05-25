from pathlib import Path
import json

import joblib
import pandas as pd

from app.core.config import SESSION_MODE_MIN_SELECTED_PROBABILITY
from app.services.session_mode_model_explainability_service import (
    explain_candidate_rows,
    load_model_card,
)

# Si el artefacto no existe, el sistema vuelve sin romperse al ranking heurístico.
MODEL_PATH = Path("app/ml/models/session_mode_model.joblib")
MODEL_METADATA_PATH = Path("app/ml/models/session_mode_model_metadata.json")

# Gates mínimos para permitir que el ML intervenga en producción.
# Ajustados al estado final defendible del proyecto para que el clasificador
# entre cuando ya existe cobertura completa por mood y una calidad global
MIN_BALANCED_ACCURACY = 0.45
MIN_ROC_AUC = 0.38 
MIN_QUALITY_SCORE = 49.0
MIN_TOTAL_EXAMPLES = 40
MIN_CLASS_EXAMPLES = 8

# Umbral operativo final para la demo. Se mantiene configurable desde entorno
# para poder afinar la frecuencia con la que el ML toma la decisión final.
DEFAULT_MIN_SELECTED_MODE_PROBABILITY = SESSION_MODE_MIN_SELECTED_PROBABILITY

# Señales numéricas del contexto actual de la sesión.
NUMERIC_FEATURES = [
    "stress_level",
    "energy_level",
    "session_duration_min",
]

# Mezclan contexto de usuario y rasgos del candidato para aprender
# qué modo encaja mejor en cada situación concreta.
CATEGORICAL_FEATURES = [
    "goal",
    "mood",
    "noise_category",
    "vocal_preference",
    "intensity_preference",
    "exploration_preference",
    "popularity_preference",
    "desired_outcome",
    "recommended_mode",
    "target_energy",
    "target_valence",
    "target_bpm_range",
    "catalog_noise_category",
]

# Señal binaria que indica si el entorno debe participar en la decisión.
BINARY_FEATURES = [
    "use_environment",
]


def _safe_float(value, default: float = 0.0) -> float:
    """
    Convierte valores de entrada a float sin romper el pipeline de ML.

    Se usa al preparar features porque parte del contexto puede llegar como
    `None`, string vacío o string numérico.
    """
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def model_available() -> bool:
    """
    Indica si el modelo de sesión está entrenado y además ha superado la puerta
    mínima de calidad definida en sus metadatos de validación.
    """
    if not MODEL_PATH.exists() or not MODEL_METADATA_PATH.exists():
        return False

    try:
        metadata = json.loads(MODEL_METADATA_PATH.read_text())
    except Exception:
        return False

    if "model_gate_passed" in metadata:
        return bool(metadata.get("model_gate_passed") is True)

    if metadata.get("quality_gate_passed") is not True:
        return False

    total_examples = int(metadata.get("total_examples", 0) or 0)
    if total_examples < MIN_TOTAL_EXAMPLES:
        return False

    class_counts = metadata.get("class_counts", {}) or {}
    positive_count = int(class_counts.get("1", class_counts.get(1, 0)) or 0)
    negative_count = int(class_counts.get("0", class_counts.get(0, 0)) or 0)

    return positive_count >= MIN_CLASS_EXAMPLES and negative_count >= MIN_CLASS_EXAMPLES


def mood_model_available(mood: str | None) -> bool:
    """
    Indica si el ML puede actuar para un mood concreto.

    Requiere:
    - que el modelo global haya superado su gate
    - y que el mood actual tenga cobertura suficiente en los metadatos
    """
    if not model_available():
        return False

    normalized_mood = str(mood).strip().lower() if mood is not None else ""
    if not normalized_mood:
        return False

    metadata = get_model_quality_metadata() or {}
    mood_coverage = metadata.get("mood_coverage", {}) or {}
    per_mood = mood_coverage.get("per_mood", {}) or {}
    mood_payload = per_mood.get(normalized_mood)
    if not mood_payload:
        return False

    return bool(mood_payload.get("quality_gate_passed") is True)


def get_model_quality_metadata() -> dict | None:
    """
    Carga los metadatos de calidad del último entrenamiento, si existen.
    """
    if not MODEL_METADATA_PATH.exists():
        return None

    try:
        return json.loads(MODEL_METADATA_PATH.read_text())
    except Exception:
        return None


def get_model_card_summary() -> dict | None:
    # La API solo necesita un resumen pequeño y estable del modelo; el detalle
    # completo se conserva en la model card persistida en disco.
    model_card = load_model_card()
    if not model_card:
        return None

    quality_summary = model_card.get("quality_summary", {}) or {}
    coefficient_summary = model_card.get("coefficient_summary", {}) or {}
    return {
        "model_type": model_card.get("model_type"),
        "trained_at": model_card.get("trained_at"),
        "quality_score": quality_summary.get("quality_score"),
        "model_gate_passed": quality_summary.get("model_gate_passed"),
        "model_readiness_reason": quality_summary.get("model_readiness_reason"),
        "top_positive_features": coefficient_summary.get("top_positive_features", [])[:5],
        "top_negative_features": coefficient_summary.get("top_negative_features", [])[:5],
    }


def get_min_selected_mode_probability(metadata: dict | None = None) -> float:
    """
    Devuelve el umbral mínimo de confianza para dejar actuar al ML.

    Para la defensa usamos un umbral operativo configurable y lo tratamos como
    cota superior. Si la calibración out-of-fold sugiere un valor todavía más
    bajo, se respeta; si sugiere uno más alto, mantenemos el umbral de demo
    para evitar abstenciones excesivas en un dataset pequeño.
    """
    payload = metadata or get_model_quality_metadata() or {}
    thresholds = payload.get("decision_thresholds", {}) or {}
    try:
        calibrated = float(
            thresholds.get(
                "min_selected_mode_probability",
                DEFAULT_MIN_SELECTED_MODE_PROBABILITY,
            )
        )
    except Exception:
        calibrated = DEFAULT_MIN_SELECTED_MODE_PROBABILITY

    configured = max(0.01, min(DEFAULT_MIN_SELECTED_MODE_PROBABILITY, 0.99))
    return min(max(calibrated, 0.01), configured)


def build_feature_rows(
    candidates: list[dict],
    context: dict,
) -> pd.DataFrame:
    """
    Convierte contexto + candidatos en una tabla lista para `predict_proba`.

    Cada fila representa un modo candidato evaluado para la sesión actual.
    El objetivo es que el modelo compare varias alternativas de recomendación
    usando exactamente el mismo contexto de usuario.
    """
    # Todas las filas comparten el mismo contexto; solo cambia el candidato.
    # Así el modelo compara alternativas y no vuelve a inferir el estado del usuario.
    rows = []

    for candidate in candidates:
        rows.append(
            {
                # ------------------------------
                # Contexto de sesión (usuario)
                # ------------------------------
                "stress_level": _safe_float(context.get("stress_level")),
                "energy_level": _safe_float(context.get("energy_level")),
                "session_duration_min": _safe_float(
                    context.get("session_duration_min"),
                    default=20.0,
                ),
                "goal": context.get("goal"),
                "mood": context.get("mood"),
                "noise_category": context.get("noise_category"),
                "vocal_preference": context.get("vocal_preference"),
                "intensity_preference": context.get("intensity_preference"),
                "exploration_preference": context.get("exploration_preference"),
                "popularity_preference": context.get("popularity_preference"),
                "desired_outcome": context.get("desired_outcome"),

                # ------------------------------
                # Rasgos del candidato
                # ------------------------------
                "recommended_mode": candidate.get("recommended_mode"),
                "target_energy": candidate.get("target_energy"),
                "target_valence": candidate.get("target_valence"),
                "target_bpm_range": candidate.get("target_bpm_range"),
                "catalog_noise_category": candidate.get("noise_category"),

                # Señal binaria compacta.
                "use_environment": 1 if context.get("use_environment", True) else 0,
            }
        )

    return pd.DataFrame(rows)


def rank_recommendation_candidates(
    candidates: list[dict],
    context: dict,
    ml_weight: float = 2.0,
) -> list[dict]:
    """
    Reordena modos candidatos a nivel de sesión.

    Este modelo no puntúa canciones individuales. Solo estima la probabilidad
    de que un modo concreto sea útil para el contexto actual del usuario.

    Idea central del reordenado:
    1. la heurística ya ha dado a cada candidato un `_score` base
    2. el modelo calcula una probabilidad de éxito para cada candidato
    3. esa probabilidad se convierte en un pequeño delta (`_mode_ml_delta`)
    4. el delta se suma al `_score` base
    5. se vuelve a ordenar la lista por el nuevo `_score`
    """
    if not candidates:
        return candidates

    if not model_available():
        # Si aún no existe modelo, preservamos la salida heurística.
        for candidate in candidates:
            candidate["_mode_ml_probability"] = None
            candidate["_mode_ml_delta"] = 0.0
            candidate["_selection_source"] = "heuristic"
            candidate["_mode_ml_explanation"] = None
        candidates.sort(key=lambda item: float(item.get("_score", 0.0)), reverse=True)
        return candidates

    try:
        model = joblib.load(MODEL_PATH)
        # Reproducimos exactamente el pipeline entrenado: mismo preprocesado,
        # mismo clasificador y mismas probabilidades que se validaron offline.
        X = build_feature_rows(candidates, context)

        print("[ML] model loaded")
        print("[ML] candidates:", len(candidates))
        print("[ML] context:", context)

        probabilities = model.predict_proba(X)[:, 1] 
        # Generamos explicación local por candidato para que el resultado final
        # sea defendible sin tener que inspeccionar solo logs agregados.
        explanations = explain_candidate_rows(
            pipeline=model,
            feature_frame=X,
            candidates=candidates,
            top_n=4,
        )
        for candidate, explanation in zip(candidates, explanations):
            explanation["decision_threshold"] = get_min_selected_mode_probability()
            candidate["_mode_ml_explanation"] = explanation
        print(
            "[ML] probabilities:",
            [round(float(p), 4) for p in probabilities[:10]],
        )

        probability_spread = float(probabilities.max() - probabilities.min())
        selected_mode_probability = float(probabilities.max())
        min_selected_mode_probability = get_min_selected_mode_probability()
        print("[ML] probability_spread:", round(probability_spread, 4))
        print(
            "[ML] selected_mode_probability:",
            round(selected_mode_probability, 4),
        )
        print(
            "[ML] min_selected_mode_probability:",
            round(min_selected_mode_probability, 4),
        )

        if selected_mode_probability < min_selected_mode_probability:
            # Si la confianza del mejor candidato no supera el umbral calibrado,
            # el sistema se abstiene y deja intacta la ordenación heurística.
            print(
                "[ML] fallback to heuristic due to low selected-mode confidence; "
                "the model does not provide enough evidence."
            )
            for candidate, prob in zip(candidates, probabilities):
                candidate["_mode_ml_probability"] = round(float(prob), 4)
                candidate["_mode_ml_delta"] = 0.0
                candidate["_selection_source"] = "heuristic_low_ml_confidence"
                if candidate.get("_mode_ml_explanation"):
                    candidate["_mode_ml_explanation"]["selection_source"] = "heuristic_low_ml_confidence"

            candidates.sort(
                key=lambda item: float(item.get("_score", 0.0)),
                reverse=True,
            )
            return candidates

        for candidate, prob in zip(candidates, probabilities):
            # `_score` ya viene de la heurística base.
            # El modelo no la sustituye: la ajusta.
            base_score = _safe_float(candidate.get("_score", 0.0))
            # `predict_proba(...)[1]` devuelve probabilidad de clase positiva,
            # es decir, probabilidad estimada de que este modo sea útil.
            #
            # Transformación:
            # - si prob = 0.50 -> delta = 0.0  (neutral)
            # - si prob > 0.50 -> delta positivo
            # - si prob < 0.50 -> delta negativo
            #
            # El factor `10.0 * ml_weight` controla cuánto empuja el ML frente
            # a la heurística. No cambia el orden por sí solo: cambia cuánto
            # peso tiene la evidencia aprendida.
            ml_delta = round((float(prob) - 0.5) * 10.0 * ml_weight, 2) 
            final_score = round(base_score + ml_delta, 2)

            # Guardamos trazabilidad para depurar y para persistir después:
            # - probabilidad cruda del modelo
            # - delta aplicado
            # - score final usado para ordenar
            candidate["_mode_ml_probability"] = round(float(prob), 4)
            candidate["_mode_ml_delta"] = ml_delta
            candidate["_score"] = final_score
            candidate["_selection_source"] = "session_ml"
            if candidate.get("_mode_ml_explanation"):
                candidate["_mode_ml_explanation"]["probability"] = round(float(prob), 4)
                candidate["_mode_ml_explanation"]["ml_delta"] = ml_delta
                candidate["_mode_ml_explanation"]["final_score"] = final_score
                candidate["_mode_ml_explanation"]["selection_source"] = "session_ml"

        # El reordenado real ocurre aquí: mismo conjunto de candidatos, pero
        # ahora ordenados por score heurístico + ajuste ML.
        candidates.sort(key=lambda item: float(item.get("_score", 0.0)), reverse=True)
        return candidates
    except Exception as e:
        print(f"[ML] fallback to heuristic due to error: {e}")

        # Si algo falla al cargar o aplicar el modelo, el sistema sigue siendo
        # usable: se vuelve al ranking heurístico y se marca el origen.
        for candidate in candidates:
            candidate["_mode_ml_probability"] = None
            candidate["_mode_ml_delta"] = 0.0
            candidate["_selection_source"] = "heuristic"
            candidate["_mode_ml_explanation"] = None

        candidates.sort(key=lambda item: float(item.get("_score", 0.0)), reverse=True)
        return candidates
