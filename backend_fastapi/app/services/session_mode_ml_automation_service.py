from __future__ import annotations

import json
from pathlib import Path
import threading
from datetime import datetime, timezone

from app.ml.train_ranking_model import train_session_mode_model
from app.services.session_mode_ml_audit_service import build_audit_payload
from app.services.ml_training_data_service import COLLECTION_NAME
from app.services.firestore_service import get_firestore_client
from app.services.session_mode_ml_service import get_model_quality_metadata


AUDIT_SNAPSHOT_PATH = Path("app/ml/models/session_mode_model_audit.json")
_MAINTENANCE_LOCK = threading.Lock()


def _log(message: str) -> None:
    print(f"[ML MAINTENANCE] {message}")


def _count_labeled_examples() -> int:
    # Solo cuentan sesiones ya útiles para supervisión: las que tienen
    # feedback convertido a etiqueta binaria `helpful`.
    db = get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()
    total = 0
    for doc in docs:
        data = doc.to_dict() or {}
        if data.get("helpful") is not None:
            total += 1
    return total


def _save_audit_snapshot(payload: dict) -> None:
    AUDIT_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_SNAPSHOT_PATH.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _build_maintenance_summary(
    *,
    current_examples: int,
    metadata_before: dict | None,
    trained: bool,
    train_result: dict | None,
    audit_payload: dict,
    skipped_reason: str | None = None,
) -> dict:
    return {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "current_labeled_examples": current_examples,
        "previous_metadata_examples": None
        if metadata_before is None
        else metadata_before.get("total_examples"),
        "trained": trained,
        "skipped_reason": skipped_reason,
        "train_result": train_result,
        "audit": audit_payload,
    }


def run_session_mode_ml_maintenance() -> dict:
    """
    Audita y reentrena el modelo automáticamente cuando aparecen ejemplos nuevos.

    Política:
    - siempre genera un snapshot de auditoría actual
    - se salta solo si el total etiquetado coincide con el último metadata
    - si el dataset ha crecido, reentrena
    - si el dataset se ha reducido o reiniciado, también reentrena para dejar
      el modelo y sus metadatos alineados con la realidad actual
    - nunca ejecuta dos mantenimientos en paralelo
    """
    if not _MAINTENANCE_LOCK.acquire(blocking=False):
        # Si llegan varios feedbacks casi a la vez, dejamos que uno solo haga
        # el trabajo y evitamos reentrenados concurrentes.
        _log("skip | reason=maintenance_already_running")
        return {
            "trained": False,
            "skipped_reason": "maintenance_already_running",
        }

    try:
        metadata_before = get_model_quality_metadata()
        current_examples = _count_labeled_examples()
        previous_examples = (
            int(metadata_before.get("total_examples", 0) or 0)
            if metadata_before
            else 0
        )

        _log(
            "start | "
            f"labeled_examples={current_examples} | "
            f"previous_metadata_examples={previous_examples}"
        )

        if current_examples == previous_examples:
            # Si el número de ejemplos etiquetados no ha cambiado, el modelo y
            # sus artefactos ya están alineados con el dataset actual.
            audit_payload = build_audit_payload()
            summary = _build_maintenance_summary(
                current_examples=current_examples,
                metadata_before=metadata_before,
                trained=False,
                train_result=None,
                audit_payload=audit_payload,
                skipped_reason="no_new_labeled_examples",
            )
            _save_audit_snapshot(summary)
            _log("skip | reason=no_new_labeled_examples")
            return summary

        train_reason = (
            "new_labeled_examples_detected"
            if current_examples > previous_examples
            else "dataset_shrunk_or_reset_detected"
        )
        # También reentrenamos tras un reset o reducción del dataset para no
        # dejar un modelo describiendo una realidad histórica ya inválida.
        _log(f"train | reason={train_reason}")
        train_result = train_session_mode_model()
        audit_payload = build_audit_payload()
        summary = _build_maintenance_summary(
            current_examples=current_examples,
            metadata_before=metadata_before,
            trained=bool(train_result.get("trained") is True),
            train_result=train_result,
            audit_payload=audit_payload,
            skipped_reason=None
            if train_result.get("trained") is True
            else str(train_result.get("reason")),
        )
        _save_audit_snapshot(summary)
        _log(
            "done | "
            f"trained={summary.get('trained')} | "
            f"reason={summary.get('skipped_reason') or summary.get('train_result', {}).get('reason')}"
        )
        return summary
    finally:
        _MAINTENANCE_LOCK.release()
