from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.config_loader import build_execution_context, load_config
from src.models import ValidatedDataset, ValidatedRecord
from src.processor import compare_depths

from tests.helpers import build_sample_project


class ProcessorTest(unittest.TestCase):
    def test_classification_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = build_sample_project(Path(tmp))
            config = load_config(project["config"])
            execution = build_execution_context(config, started_at=datetime(2026, 5, 19, 12, 0, 0), run_id="20260519_120000")
            planned = ValidatedDataset(
                label="Prevista",
                path=project["planned_file"],
                sheet_name="PROJETO PERFURAÇÃO",
                id_column="ID",
                depth_column="Depth",
                records=[
                    ValidatedRecord(1, 10.0, 2, {}),
                    ValidatedRecord(2, 10.0, 3, {}),
                    ValidatedRecord(3, 5.0, 4, {}),
                    ValidatedRecord(4, 8.0, 5, {}),
                    ValidatedRecord(5, 7.0, 6, {}),
                ],
            )
            realized = ValidatedDataset(
                label="Realizada",
                path=project["realized_file"],
                sheet_name="Data",
                id_column="Number",
                depth_column="Length_Real (m)",
                records=[
                    ValidatedRecord(1, 10.2, 2, {}),
                    ValidatedRecord(2, 10.6, 3, {}),
                    ValidatedRecord(3, 4.8, 4, {}),
                    ValidatedRecord(4, 21.1, 5, {}),
                    ValidatedRecord(6, 12.0, 6, {}),
                ],
            )
            result = compare_depths(config, planned, realized, execution)
            self.assertEqual(result.metrics.total_matched, 4)
            self.assertEqual(result.metrics.adherent_count, 2)
            self.assertEqual(result.metrics.above_count, 1)
            self.assertEqual(result.metrics.outlier_count, 1)
            self.assertEqual(result.metrics.planned_only_count, 1)
            self.assertEqual(result.metrics.realized_only_count, 1)
