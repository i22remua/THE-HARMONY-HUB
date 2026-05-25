from __future__ import annotations

from pathlib import Path
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.session_mode_ml_audit_service import build_audit_payload


def main() -> None:
    payload = build_audit_payload()

    print("=== Session Mode Model Audit ===")
    print(f"collection: {payload.get('collection')}")
    print(f"examples_total_in_firestore: {payload.get('examples_total_in_firestore')}")
    print(f"examples_with_label: {payload.get('examples_with_label')}")
    print(f"class_counts: {payload.get('class_counts')}")
    print(
        "minimum_total_examples_required: "
        f"{payload.get('minimum_total_examples_required')}"
    )
    print(
        "minimum_examples_per_class_required: "
        f"{payload.get('minimum_examples_per_class_required')}"
    )
    print(f"model_available_now: {payload.get('model_available_now')}")
    print()

    print("top_goals:")
    for key, value in payload.get("top_goals", {}).items():
        print(f"  - {key}: {value}")

    print()
    print("top_modes:")
    for key, value in payload.get("top_modes", {}).items():
        print(f"  - {key}: {value}")

    print()
    metadata = payload.get("metadata_summary")
    if metadata is None:
        print("metadata: missing")
        return

    print("metadata_summary:")
    print(f"  - trained_at: {metadata.get('trained_at')}")
    print(f"  - total_examples: {metadata.get('total_examples')}")
    print(f"  - class_counts: {metadata.get('class_counts')}")
    print(f"  - data_gate_passed: {metadata.get('data_gate_passed')}")
    print(f"  - model_gate_passed: {metadata.get('model_gate_passed')}")
    print(f"  - model_readiness_reason: {metadata.get('model_readiness_reason')}")
    print(f"  - quality_gate_passed: {metadata.get('quality_gate_passed')}")
    print(f"  - readiness_reason: {metadata.get('readiness_reason')}")
    print(f"  - quality_score: {metadata.get('quality_score')}")
    print(f"  - metrics: {metadata.get('metrics')}")
    print(f"  - mood_observability: {metadata.get('mood_coverage')}")


if __name__ == "__main__":
    main()
