from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.session_mode_ml_automation_service import (
    run_session_mode_ml_maintenance,
)


class SessionModeMlAutomationServiceTest(unittest.TestCase):
    @patch("app.services.session_mode_ml_automation_service._save_audit_snapshot")
    @patch(
        "app.services.session_mode_ml_automation_service.build_audit_payload",
        return_value={"examples_with_label": 12},
    )
    @patch(
        "app.services.session_mode_ml_automation_service.get_model_quality_metadata",
        return_value={"total_examples": 12},
    )
    @patch(
        "app.services.session_mode_ml_automation_service._count_labeled_examples",
        return_value=12,
    )
    def test_skips_training_when_no_new_examples(
        self,
        _mock_count,
        _mock_metadata,
        _mock_audit,
        _mock_save,
    ) -> None:
        result = run_session_mode_ml_maintenance()

        self.assertFalse(result["trained"])
        self.assertEqual(result["skipped_reason"], "no_new_labeled_examples")

    @patch("app.services.session_mode_ml_automation_service._save_audit_snapshot")
    @patch(
        "app.services.session_mode_ml_automation_service.build_audit_payload",
        return_value={"examples_with_label": 13},
    )
    @patch(
        "app.services.session_mode_ml_automation_service.train_session_mode_model",
        return_value={"trained": True, "reason": "trained", "total_examples": 13},
    )
    @patch(
        "app.services.session_mode_ml_automation_service.get_model_quality_metadata",
        return_value={"total_examples": 12},
    )
    @patch(
        "app.services.session_mode_ml_automation_service._count_labeled_examples",
        return_value=13,
    )
    def test_retrains_when_new_examples_exist(
        self,
        _mock_count,
        _mock_metadata,
        mock_train,
        _mock_audit,
        _mock_save,
    ) -> None:
        result = run_session_mode_ml_maintenance()

        self.assertTrue(result["trained"])
        self.assertIsNone(result["skipped_reason"])
        self.assertEqual(result["train_result"]["total_examples"], 13)
        mock_train.assert_called_once()

    @patch("app.services.session_mode_ml_automation_service._save_audit_snapshot")
    @patch(
        "app.services.session_mode_ml_automation_service.build_audit_payload",
        return_value={"examples_with_label": 16},
    )
    @patch(
        "app.services.session_mode_ml_automation_service.train_session_mode_model",
        return_value={"trained": True, "reason": "trained", "total_examples": 16},
    )
    @patch(
        "app.services.session_mode_ml_automation_service.get_model_quality_metadata",
        return_value={"total_examples": 63},
    )
    @patch(
        "app.services.session_mode_ml_automation_service._count_labeled_examples",
        return_value=16,
    )
    def test_retrains_when_dataset_has_been_reduced_or_reset(
        self,
        _mock_count,
        _mock_metadata,
        mock_train,
        _mock_audit,
        _mock_save,
    ) -> None:
        result = run_session_mode_ml_maintenance()

        self.assertTrue(result["trained"])
        self.assertEqual(result["previous_metadata_examples"], 63)
        self.assertEqual(result["current_labeled_examples"], 16)
        mock_train.assert_called_once()


if __name__ == "__main__":
    unittest.main()
