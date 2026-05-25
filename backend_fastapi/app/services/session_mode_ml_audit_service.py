from __future__ import annotations

import json
from collections import Counter

from app.services.firestore_service import get_firestore_client
from app.services.ml_training_data_service import COLLECTION_NAME
from app.services.session_mode_ml_service import (
    MIN_CLASS_EXAMPLES,
    MIN_TOTAL_EXAMPLES,
    MODEL_METADATA_PATH,
    model_available,
)


def _load_metadata() -> dict | None:
    if not MODEL_METADATA_PATH.exists():
        return None

    try:
        return json.loads(MODEL_METADATA_PATH.read_text())
    except Exception:
        return None


def build_audit_payload() -> dict:
    db = get_firestore_client()
    docs = list(db.collection(COLLECTION_NAME).stream())
    rows = [doc.to_dict() or {} for doc in docs]

    helpful_rows = [row for row in rows if row.get("helpful") is not None]
    class_counts = Counter(int(bool(row.get("helpful"))) for row in helpful_rows)
    goal_counts = Counter(str(row.get("goal") or "unknown") for row in helpful_rows)
    mode_counts = Counter(
        str(row.get("recommended_mode") or "unknown") for row in helpful_rows
    )

    metadata = _load_metadata()

    return {
        "collection": COLLECTION_NAME,
        "examples_total_in_firestore": len(rows),
        "examples_with_label": len(helpful_rows),
        "class_counts": dict(class_counts),
        "minimum_total_examples_required": MIN_TOTAL_EXAMPLES,
        "minimum_examples_per_class_required": MIN_CLASS_EXAMPLES,
        "model_available_now": model_available(),
        "top_goals": dict(goal_counts.most_common(10)),
        "top_modes": dict(mode_counts.most_common(10)),
        "metadata_summary": None
        if metadata is None
        else {
            "trained_at": metadata.get("trained_at"),
            "total_examples": metadata.get("total_examples"),
            "class_counts": metadata.get("class_counts"),
            "data_gate_passed": metadata.get("data_gate_passed"),
            "model_gate_passed": metadata.get("model_gate_passed"),
            "model_readiness_reason": metadata.get("model_readiness_reason"),
            "quality_gate_passed": metadata.get("quality_gate_passed"),
            "readiness_reason": metadata.get("readiness_reason"),
            "quality_score": metadata.get("quality_score"),
            "metrics": metadata.get("metrics"),
            "mood_coverage": metadata.get("mood_coverage"),
        },
    }
