from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.config_loader import load_config
from src.data_reader import read_workbook
from src.exceptions import ValidationError
from src.validator import validate_workbook

from tests.helpers import build_sample_project


class ValidatorTest(unittest.TestCase):
    def test_valid_workbook_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = build_sample_project(Path(tmp))
            config = load_config(project["config"])
            raw_planned = read_workbook(config, config.planned)
            dataset = validate_workbook(config, raw_planned, config.planned)
            self.assertEqual(len(dataset.records), 5)
            self.assertEqual(dataset.records[0].hole_id, 1)
            self.assertEqual(dataset.records[0].depth, 10.0)

    def test_duplicate_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = build_sample_project(
                root,
                planned_rows=[[1, 10.0], [1, 11.0]],
                realized_rows=[[1, 10.0]],
            )
            config = load_config(project["config"])
            raw_planned = read_workbook(config, config.planned)
            with self.assertRaises(ValidationError):
                validate_workbook(config, raw_planned, config.planned)
