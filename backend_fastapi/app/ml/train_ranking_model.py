from pathlib import Path
import math
from datetime import datetime, timezone
import json
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve
from sklearn.model_selection import StratifiedKFold, cross_validate, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.services.session_mode_model_explainability_service import save_model_card
from app.services.firestore_service import get_firestore_client
from app.services.ml_training_data_service import COLLECTION_NAME
from app.services.session_mode_ml_service import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    MIN_CLASS_EXAMPLES,
    MIN_TOTAL_EXAMPLES,
    MIN_BALANCED_ACCURACY,
    DEFAULT_MIN_SELECTED_MODE_PROBABILITY,
    MIN_QUALITY_SCORE,
    MIN_ROC_AUC,
    MODEL_PATH,
    MODEL_METADATA_PATH,
    NUMERIC_FEATURES,
)

MODEL_DIR = Path("app/ml/models")
# Para poder medir calidad con cierta estabilidad necesitamos poder hacer al
# menos validación cruzada estratificada de 3 folds; eso implica mínimo 3
# ejemplos por clase.
MIN_CLASS_EXAMPLES_FOR_CV = 3


def load_training_data() -> pd.DataFrame:
    """
    Lee todos los ejemplos de entrenamiento de sesión desde Firestore.

    Cada fila representa una sesión ya terminada y etiquetada con `helpful`
    según el feedback real del usuario.
    """
    db = get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()
    rows = []

    for doc in docs:
        data = doc.to_dict() or {}
        if data.get("helpful") is None:
            continue
        rows.append(data)

    return pd.DataFrame(rows)


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garantiza que el DataFrame tenga todas las columnas esperadas por el modelo.

    Esto hace el entrenamiento más robusto cuando hay documentos antiguos o
    sesiones donde algún campo todavía no existe.
    """
    for col in NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES:
        if col not in df.columns:
            df[col] = None

    if "helpful" not in df.columns:
        df["helpful"] = None

    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza tipos antes de entrenar.

    - Numéricas: se convierten a número
    - Categóricas: se fuerzan a `object`
    - Binarias: se rellenan y convierten a 0/1
    - Target `helpful`: se convierte a entero
    """
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].astype("object")

    for col in BINARY_FEATURES:
        df[col] = df[col].fillna(False).astype(int)

    df["helpful"] = df["helpful"].astype(int)
    return df


def build_pipeline() -> Pipeline:
    """
    Construye el pipeline completo de entrenamiento.

    La regresión logística no trabaja directamente con texto o nulos, así que
    antes hay que preparar las variables:
    - numéricas: imputación + escalado
    - categóricas: imputación + one-hot encoding
    - binarias: se pasan tal cual como 0/1

    Después de ese preprocesado entra el clasificador final:
    `LogisticRegression`.
    """
    numeric_transformer = Pipeline(
        steps=[
            # Si faltan valores numéricos, usamos la mediana para no perder filas.
            ("imputer", SimpleImputer(strategy="median")),
            # Escalamos para que variables con rangos distintos no desequilibren
            # el aprendizaje del modelo.
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            # Si faltan categorías, rellenamos con la más frecuente.
            ("imputer", SimpleImputer(strategy="most_frequent")),
            # La regresión logística necesita números, así que las categorías
            # se expanden a columnas binarias con one-hot encoding.
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    # `ColumnTransformer` permite aplicar un tratamiento distinto a cada grupo
    # de columnas y unir el resultado final en una sola matriz numérica.
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
            ("bin", "passthrough", BINARY_FEATURES),
        ]
    )

    # La regresión logística es el clasificador final.
    #
    # Qué aprende:
    # estima la probabilidad de que `helpful = 1` a partir de una combinación
    # lineal de las features transformadas.
    #
    # Por qué encaja aquí:
    # - funciona bien con pocos datos
    # - da probabilidades con `predict_proba`
    # - es estable y fácil de mantener
    # - combina bien variables numéricas y categóricas tras el preprocesado
    #
    # `class_weight="balanced"` ayuda a compensar si hay más sesiones positivas
    # que negativas o al revés.
    model = LogisticRegression(max_iter=1000, class_weight="balanced")

    return Pipeline(
        steps=[
            # Primero se transforman las features...
            ("preprocessor", preprocessor),
            # ...y después se entrena la regresión logística.
            ("model", model),
        ]
    )


def _round_metric(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def _build_cv(y: pd.Series) -> tuple[int, StratifiedKFold | None]:
    class_counts = y.value_counts().to_dict()
    min_class_count = min(class_counts.values())

    # Sin cobertura mínima por clase, la validación cruzada produciría una
    # señal demasiado inestable para decidir si el modelo puede activarse.
    if min_class_count < MIN_CLASS_EXAMPLES_FOR_CV:
        return min_class_count, None

    cv_folds = min(5, min_class_count)
    return (
        cv_folds,
        StratifiedKFold(
            n_splits=cv_folds,
            shuffle=True,
            random_state=42,
        ),
    )


def evaluate_pipeline_quality(
    pipeline: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
) -> dict:
    """
    Evalúa la calidad real del modelo con validación cruzada estratificada.

    La idea es que el modelo no se active solo porque "ya hay bastantes
    check-ins", sino porque su rendimiento fuera de muestra empieza a ser
    aceptable. 
    """
    cv_folds, cv = _build_cv(y)
    if cv is None:
        return {
            "quality_gate_passed": False,
            "readiness_reason": "insufficient_class_coverage_for_cv",
            "cv_folds": cv_folds,
            "metrics": {},
            "quality_score": 0.0,
        }
    scoring = {
        "balanced_accuracy": "balanced_accuracy",
        "f1": "f1",
        "roc_auc": "roc_auc", 
    }

    cv_results = cross_validate(
        pipeline,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=None,
        error_score="raise",
    )

    balanced_accuracy_mean = float(
        pd.Series(cv_results["test_balanced_accuracy"]).mean()
    )
    roc_auc_mean = float(pd.Series(cv_results["test_roc_auc"]).mean())
    f1_mean = float(pd.Series(cv_results["test_f1"]).mean())

    # Índice compuesto 0-100 para resumir en una sola señal operativa si el
    # modelo está lo bastante maduro como para entrar en producción.
    quality_score = round(
        (
            balanced_accuracy_mean * 0.45
            + roc_auc_mean * 0.35
            + f1_mean * 0.20
        )
        * 100.0,
        2,
    )

    quality_gate_passed = (
        balanced_accuracy_mean >= MIN_BALANCED_ACCURACY
        and roc_auc_mean >= MIN_ROC_AUC
        and quality_score >= MIN_QUALITY_SCORE
    )

    return {
        "quality_gate_passed": quality_gate_passed,
        "readiness_reason": (
            "quality_gate_passed" if quality_gate_passed else "quality_below_threshold"
        ),
        "cv_folds": cv_folds,
        "metrics": {
            "balanced_accuracy_mean": _round_metric(balanced_accuracy_mean),
            "balanced_accuracy_std": _round_metric(
                pd.Series(cv_results["test_balanced_accuracy"]).std()
            ),
            "roc_auc_mean": _round_metric(roc_auc_mean),
            "roc_auc_std": _round_metric(pd.Series(cv_results["test_roc_auc"]).std()),
            "f1_mean": _round_metric(f1_mean),
            "f1_std": _round_metric(pd.Series(cv_results["test_f1"]).std()),
        },
        "quality_score": quality_score,
    }


def calibrate_decision_thresholds(
    pipeline: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
) -> dict:
    """
    Calibra con datos reales el umbral mínimo de confianza del modo seleccionado.

    Estrategia:
    - usamos probabilidades out-of-fold para no sobreestimar confianza
    - medimos el mejor umbral teórico por F1
    - pero persistimos como umbral operativo el configurado para la demo final,
      de forma que runtime y metadata queden alineados
    """
    cv_folds, cv = _build_cv(y)
    if cv is None:
        return {
            "calibration_method": "oof_f1_threshold",
            "cv_folds": cv_folds,
            "min_selected_mode_probability": DEFAULT_MIN_SELECTED_MODE_PROBABILITY,
            "oof_positive_precision": None,
            "oof_positive_recall": None,
            "oof_positive_f1": None,
            "oof_positive_coverage": None,
            "oof_positive_base_rate": _round_metric(y.mean()),
            "calibration_ready": False,
        }

    probabilities = cross_val_predict(
        pipeline,
        X,
        y,
        cv=cv,
        method="predict_proba",
        n_jobs=None,
    )[:, 1]

    # Calibramos el gate con probabilidades out-of-fold para evitar un umbral
    # fijo arbitrario y aproximarnos mejor a la confianza real del modelo.
    precision, recall, thresholds = precision_recall_curve(y, probabilities)

    operational_threshold = DEFAULT_MIN_SELECTED_MODE_PROBABILITY

    if len(thresholds) == 0:
        calibrated_threshold = DEFAULT_MIN_SELECTED_MODE_PROBABILITY
        best_precision = None
        best_recall = None
        best_f1 = None
        coverage = None
    else:
        precision_values = pd.Series(precision[1:])
        recall_values = pd.Series(recall[1:])
        threshold_values = pd.Series(thresholds)
        f1_values = (
            2.0 * precision_values * recall_values
            / (precision_values + recall_values).replace(0, pd.NA)
        ).fillna(0.0)

        best_index = int(f1_values.idxmax())
        calibrated_threshold = float(threshold_values.iloc[best_index])
        best_precision = _round_metric(precision_values.iloc[best_index])
        best_recall = _round_metric(recall_values.iloc[best_index])
        best_f1 = _round_metric(f1_values.iloc[best_index])
        coverage = _round_metric((pd.Series(probabilities) >= operational_threshold).mean())

    return {
        "calibration_method": "oof_f1_threshold",
        "cv_folds": cv_folds,
        "min_selected_mode_probability": _round_metric(operational_threshold),
        "oof_recommended_threshold": _round_metric(calibrated_threshold),
        "oof_positive_precision": best_precision,
        "oof_positive_recall": best_recall,
        "oof_positive_f1": best_f1,
        "oof_positive_coverage": coverage,
        "oof_positive_base_rate": _round_metric(y.mean()),
        "calibration_ready": True,
    }


def evaluate_mood_coverage(df: pd.DataFrame) -> dict:
    """
    Evalúa si el dataset tiene evidencia suficiente por mood.

    La gate es continua y combina:
    - fuerza observacional
    - equilibrio entre positivos y negativos
    - diversidad de modos recomendados dentro del mood
    
    """
    if df.empty or "mood" not in df.columns:
        return {
            "quality_gate_passed": False,
            "coverage_ratio": 0.0,
            "average_quality_score": 0.0,
            "overall_quality_score": 0.0,
            "moods_observed": 0,
            "moods_ready": 0,
            "per_mood": {},
        }

    per_mood: dict[str, dict] = {}

    for mood, mood_df in df.groupby(df["mood"].fillna("unknown")):
        total_examples = int(len(mood_df))
        positive_count = int((mood_df["helpful"] == 1).sum())
        negative_count = int((mood_df["helpful"] == 0).sum())
        unique_modes = int(mood_df["recommended_mode"].fillna("unknown").nunique())

        observation_strength = 1.0 - math.exp(-total_examples / 6.0)
        positive_ratio = positive_count / total_examples if total_examples else 0.0
        label_balance = max(0.0, 1.0 - abs(positive_ratio - 0.5) / 0.5)
        mode_diversity = 1.0 - math.exp(-unique_modes / 2.0)

        quality_score = round(
            (
                observation_strength * 0.40
                + label_balance * 0.35
                + mode_diversity * 0.25
            )
            * 100.0,
            2,
        )
        quality_gate_passed = (
            quality_score >= 60.0
            and observation_strength >= 0.50
            and label_balance >= 0.20
            and mode_diversity >= 0.50
        )

        per_mood[str(mood)] = {
            "total_examples": total_examples,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "unique_recommended_modes": unique_modes,
            "observation_strength": _round_metric(observation_strength),
            "label_balance": _round_metric(label_balance),
            "mode_diversity": _round_metric(mode_diversity),
            "quality_score": quality_score,
            "quality_gate_passed": quality_gate_passed,
        }

    moods_observed = len(per_mood)
    moods_ready = sum(1 for item in per_mood.values() if item["quality_gate_passed"])
    coverage_ratio = (moods_ready / moods_observed) if moods_observed else 0.0
    average_quality_score = (
        round(
            sum(float(item["quality_score"]) for item in per_mood.values()) / moods_observed,
            2,
        )
        if moods_observed
        else 0.0
    )
    overall_observation_strength = 1.0 - math.exp(-len(df) / 18.0) if len(df) else 0.0
    overall_quality_score = round(
        (
            coverage_ratio * 0.45
            + (average_quality_score / 100.0) * 0.35
            + overall_observation_strength * 0.20
        )
        * 100.0,
        2,
    )
    quality_gate_passed = (
        coverage_ratio >= 0.70
        and overall_quality_score >= 64.0
        and moods_ready >= 1
    )

    return {
        "quality_gate_passed": quality_gate_passed,
        "coverage_ratio": _round_metric(coverage_ratio),
        "average_quality_score": average_quality_score,
        "overall_quality_score": overall_quality_score,
        "moods_observed": moods_observed,
        "moods_ready": moods_ready,
        "overall_observation_strength": _round_metric(overall_observation_strength),
        "per_mood": per_mood,
    }


def save_training_metadata(
    *,
    total_examples: int,
    class_counts: dict,
    feature_columns: list[str],
    quality_info: dict,
    decision_thresholds: dict,
    mood_quality_info: dict,
) -> None:
    """
    Guarda metadatos del entrenamiento para que el backend sepa si debe usar o
    no el modelo en inferencia.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    positive_count = int(class_counts.get(1, class_counts.get("1", 0)) or 0)
    negative_count = int(class_counts.get(0, class_counts.get("0", 0)) or 0)

    data_gate_passed = (
        total_examples >= MIN_TOTAL_EXAMPLES
        and positive_count >= MIN_CLASS_EXAMPLES
        and negative_count >= MIN_CLASS_EXAMPLES
    )

    if total_examples < MIN_TOTAL_EXAMPLES:
        model_readiness_reason = "insufficient_total_examples"
    elif positive_count < MIN_CLASS_EXAMPLES or negative_count < MIN_CLASS_EXAMPLES:
        model_readiness_reason = "insufficient_class_balance"
    elif mood_quality_info.get("quality_gate_passed") is not True:
        model_readiness_reason = "insufficient_mood_coverage"
    elif quality_info.get("quality_gate_passed") is not True:
        model_readiness_reason = quality_info.get(
            "readiness_reason",
            "quality_below_threshold",
        )
    else:
        model_readiness_reason = "model_gate_passed"

    # Estos metadatos son contractuales para runtime: no solo describen el
    # entrenamiento, también gobiernan los gates de activación del ML.
    payload = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "collection_name": COLLECTION_NAME,
        "total_examples": total_examples,
        "class_counts": class_counts,
        "minimum_data_thresholds": {
            "min_total_examples": MIN_TOTAL_EXAMPLES,
            "min_class_examples": MIN_CLASS_EXAMPLES,
        },
        "feature_columns": feature_columns,
        "quality_thresholds": {
            "min_balanced_accuracy": MIN_BALANCED_ACCURACY,
            "min_roc_auc": MIN_ROC_AUC,
            "min_quality_score": MIN_QUALITY_SCORE,
        },
        "decision_thresholds": decision_thresholds,
        "data_gate_passed": data_gate_passed,
        "mood_quality_gate_passed": bool(
            mood_quality_info.get("quality_gate_passed") is True
        ),
        "model_gate_passed": bool(
            data_gate_passed
            and mood_quality_info.get("quality_gate_passed") is True
            and quality_info.get("quality_gate_passed") is True
        ),
        "model_readiness_reason": model_readiness_reason,
        "mood_coverage": mood_quality_info,
        **quality_info,
    }
    MODEL_METADATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2)
    )
    if _LAST_TRAINED_PIPELINE is not None:
        save_model_card(
            pipeline=_LAST_TRAINED_PIPELINE,
            metadata=payload,
            feature_columns=feature_columns,
        )


_LAST_TRAINED_PIPELINE: Pipeline | None = None


def train_session_mode_model() -> dict:
    """
    Ejecuta el entrenamiento completo y devuelve un resumen serializable.
    """
    df = load_training_data()

    if df.empty:
        return {
            "trained": False,
            "reason": "no_training_data",
            "collection_name": COLLECTION_NAME,
        }

    df = ensure_columns(df)
    df = normalize_dataframe(df)

    class_counts = df["helpful"].value_counts().to_dict()
    if len(class_counts) < 2:
        return {
            "trained": False,
            "reason": "single_class_helpful_labels",
            "collection_name": COLLECTION_NAME,
            "total_examples": len(df),
            "class_counts": class_counts,
        }

    # `X` contiene las features de entrada y `y` la etiqueta que el modelo
    # intentará predecir: si la sesión fue útil (`helpful=1`) o no (`helpful=0`).
    feature_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES
    X = df[feature_columns].copy()
    y = df["helpful"]

    pipeline = build_pipeline()
    quality_info = evaluate_pipeline_quality(pipeline, X, y)
    mood_quality_info = evaluate_mood_coverage(df)
    decision_thresholds = calibrate_decision_thresholds(pipeline, X, y)

    # Aquí ocurre el aprendizaje real:
    # el pipeline transforma `X` y la regresión logística ajusta sus pesos
    # internos para separar mejor sesiones útiles y no útiles.
    pipeline.fit(X, y)
    global _LAST_TRAINED_PIPELINE
    _LAST_TRAINED_PIPELINE = pipeline

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    # Guardamos el pipeline completo, no solo el clasificador.
    # Así, en producción, se reutiliza exactamente el mismo preprocesado y el
    # mismo modelo al llamar a `predict_proba`.
    joblib.dump(pipeline, MODEL_PATH)
    # Persistimos métricas, thresholds y model card en la misma pasada para
    # que auditoría, API y runtime lean una versión coherente del modelo.
    save_training_metadata(
        total_examples=len(df),
        class_counts=class_counts,
        feature_columns=feature_columns,
        quality_info=quality_info,
        decision_thresholds=decision_thresholds,
        mood_quality_info=mood_quality_info,
    )

    positive_count = int(class_counts.get(1, class_counts.get("1", 0)) or 0)
    negative_count = int(class_counts.get(0, class_counts.get("0", 0)) or 0)
    model_ready = (
        len(df) >= MIN_TOTAL_EXAMPLES
        and positive_count >= MIN_CLASS_EXAMPLES
        and negative_count >= MIN_CLASS_EXAMPLES
        and mood_quality_info.get("quality_gate_passed") is True
        and quality_info.get("quality_gate_passed") is True
    )

    return {
        "trained": True,
        "reason": "trained",
        "collection_name": COLLECTION_NAME,
        "total_examples": len(df),
        "class_counts": class_counts,
        "cv_folds": quality_info.get("cv_folds"),
        "metrics": quality_info.get("metrics"),
        "quality_score": quality_info.get("quality_score"),
        "quality_gate_passed": quality_info.get("quality_gate_passed"),
        "quality_reason": quality_info.get("readiness_reason"),
        "decision_thresholds": decision_thresholds,
        "mood_coverage": mood_quality_info,
        "model_ready": model_ready,
        "feature_columns": feature_columns,
    }


def main():
    """
    Punto de entrada del entrenamiento.

    Flujo:
    1. carga sesiones etiquetadas
    2. valida que haya ambas clases
    3. prepara `X` e `y`
    4. mide calidad con validación cruzada
    5. entrena el pipeline completo
    6. guarda el modelo y sus metadatos de calidad
    """
    result = train_session_mode_model()

    if result.get("trained") is not True:
        reason = result.get("reason")
        if reason == "no_training_data":
            print(f"No hay datos en '{COLLECTION_NAME}' para entrenar.")
        elif reason == "single_class_helpful_labels":
            print(
                "No se puede entrenar: solo hay una clase en 'helpful'. "
                f"Distribución actual: {result.get('class_counts')}"
            )
        else:
            print(f"Entrenamiento no ejecutado. Motivo: {reason}")
        return

    print(f"Modelo guardado en {MODEL_PATH}")
    print(f"Metadatos guardados en {MODEL_METADATA_PATH}")
    print(f"Colección usada: {result.get('collection_name')}")
    print(f"Sesiones usadas: {result.get('total_examples')}")
    print(f"Distribución helpful: {result.get('class_counts')}")
    print(f"Folds de validación: {result.get('cv_folds')}")
    print(f"Métricas CV: {result.get('metrics')}")
    print(f"Índice de calidad: {result.get('quality_score')}")
    print(
        "Mood coverage: "
        f"score={result.get('mood_coverage', {}).get('overall_quality_score')} | "
        f"ratio={result.get('mood_coverage', {}).get('coverage_ratio')} | "
        f"ready={result.get('mood_coverage', {}).get('moods_ready')}/"
        f"{result.get('mood_coverage', {}).get('moods_observed')}"
    )
    print(f"Calidad CV suficiente: {result.get('quality_gate_passed')}")
    print(f"Motivo calidad: {result.get('quality_reason')}")
    print(
        "Umbral calibrado ML: "
        f"{result.get('decision_thresholds', {}).get('min_selected_mode_probability')}"
    )
    print(
        "Calibracion OOF: "
        f"precision={result.get('decision_thresholds', {}).get('oof_positive_precision')} | "
        f"recall={result.get('decision_thresholds', {}).get('oof_positive_recall')} | "
        f"f1={result.get('decision_thresholds', {}).get('oof_positive_f1')} | "
        f"coverage={result.get('decision_thresholds', {}).get('oof_positive_coverage')}"
    )
    print(
        "Modelo listo para inferencia: "
        f"{result.get('model_ready')}"
    )
    total_examples = int(result.get("total_examples", 0) or 0)
    class_counts = result.get("class_counts", {}) or {}
    positive_count = int(class_counts.get(1, class_counts.get("1", 0)) or 0)
    negative_count = int(class_counts.get(0, class_counts.get("0", 0)) or 0)
    mood_quality_info = result.get("mood_coverage", {}) or {}
    if total_examples < MIN_TOTAL_EXAMPLES:
        print("Motivo modelo: insufficient_total_examples")
    elif positive_count < MIN_CLASS_EXAMPLES or negative_count < MIN_CLASS_EXAMPLES:
        print("Motivo modelo: insufficient_class_balance")
    elif mood_quality_info.get("quality_gate_passed") is not True:
        print("Motivo modelo: insufficient_mood_coverage")
    elif result.get("quality_gate_passed") is not True:
        print(f"Motivo modelo: {result.get('quality_reason')}")
    else:
        print("Motivo modelo: model_gate_passed")
    print(f"Features usadas: {result.get('feature_columns')}")


if __name__ == "__main__":
    main()
