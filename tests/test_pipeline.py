from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from main import run

from tests.helpers import build_sample_project


class PipelineTest(unittest.TestCase):
    def test_end_to_end_run_generates_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = build_sample_project(Path(tmp))
            exit_code = run(project["config"])
            self.assertEqual(exit_code, 0)

            output_files = list(project["output_dir"].glob("RELATORIO_PROFUNDIDADES_*.pdf"))
            csv_files = list(project["output_dir"].glob("RELATORIO_PROFUNDIDADES_*_BASE_ANALITICA.csv"))
            log_files = list(project["logs_dir"].glob("RELATORIO_PROFUNDIDADES_*.log"))

            self.assertEqual(len(output_files), 1)
            self.assertEqual(len(csv_files), 1)
            self.assertEqual(len(log_files), 1)
            self.assertGreater(output_files[0].stat().st_size, 1000)

            with csv_files[0].open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle, delimiter=";"))
            self.assertEqual(rows[0], ["ID", "Prevista_m", "Realizada_m", "Desvio_m", "Status", "Outlier", "Motivo_outlier", "Prevista_linha", "Realizada_linha"])
            self.assertEqual(len(rows) - 1, 4)
