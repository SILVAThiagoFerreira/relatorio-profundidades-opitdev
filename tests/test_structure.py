from __future__ import annotations

import unittest
from pathlib import Path


class StructureTest(unittest.TestCase):
    def test_required_files_and_dirs_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        required_files = [
            "README.md",
            "AGENTS.md",
            "TASK.md",
            "SPEC.md",
            "CHECKLIST.md",
            "PROMPT.md",
            "PIPELINE.md",
            "DATA_SCHEMA.md",
            "config.json",
            "main.py",
            "generate_relatorio_profundidades_reg260526.py",
        ]
        required_dirs = ["src", "tests", "imput", "output", "logs", "web"]
        for rel_path in required_files:
            self.assertTrue((root / rel_path).exists(), rel_path)
        for rel_path in required_dirs:
            self.assertTrue((root / rel_path).exists(), rel_path)
