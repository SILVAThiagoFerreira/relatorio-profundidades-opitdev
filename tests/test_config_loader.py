from __future__ import annotations

import unittest
from pathlib import Path

from src.config_loader import load_config


class ConfigLoaderTest(unittest.TestCase):
    def test_load_repo_config(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = load_config(root / "config.json")
        self.assertEqual(config.input_format, "dxf")
        self.assertEqual(config.dxf_source.file_name, "opit.dxf")
        self.assertEqual(config.dxf_source.planned.layer_name, "Theoretical Hole")
        self.assertEqual(config.dxf_source.realized.layer_name, "Real Hole")
        self.assertEqual(config.depth_tolerance_m, 0.3)
        self.assertEqual(config.outlier_threshold_m, 20.0)
        self.assertIn("{run_id}", config.output_pdf_template)
