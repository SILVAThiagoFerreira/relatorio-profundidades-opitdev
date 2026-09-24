"""Test helpers for workbook and config fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook


def write_workbook(path: Path, sheet_name: str, headers: list[str], rows: list[list[object]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    workbook.close()


def build_sample_project(
    root: Path,
    planned_rows: list[list[object]] | None = None,
    realized_rows: list[list[object]] | None = None,
) -> dict[str, Path]:
    input_dir = root / "input"
    output_dir = root / "output"
    logs_dir = root / "logs"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    planned_file = input_dir / "PP.xlsx"
    realized_file = input_dir / "opit.xlsx"

    write_workbook(
        planned_file,
        "PROJETO PERFURAÇÃO",
        ["ID", "Depth"],
        planned_rows if planned_rows is not None else [
            [1, 10.0],
            [2, 10.0],
            [3, 5.0],
            [4, 8.0],
            [5, 7.0],
        ],
    )
    write_workbook(
        realized_file,
        "Data",
        ["Number", "Length_Real (m)"],
        realized_rows if realized_rows is not None else [
            [1, 10.2],
            [2, 10.6],
            [3, 4.8],
            [4, 21.1],
            [6, 12.0],
        ],
    )

    config = {
        "project_root": ".",
        "directories": {"input": "input", "output": "output", "logs": "logs"},
        "execution": {"run_id_strategy": "timestamp", "timestamp_format": "%Y%m%d_%H%M%S"},
        "inputs": {
            "format": "workbook",
            "planned": {
                "role": "planned",
                "label": "Prevista",
                "file_name": "PP.xlsx",
                "sheet_name": "PROJETO PERFURAÇÃO",
                "header_row": 1,
                "id_column": "ID",
                "depth_column": "Depth",
            },
            "realized": {
                "role": "realized",
                "label": "Realizada",
                "file_name": "opit.xlsx",
                "sheet_name": "Data",
                "header_row": 1,
                "id_column": "Number",
                "depth_column": "Length_Real (m)",
            },
        },
        "rules": {
            "depth_tolerance_m": 0.3,
            "outlier_threshold_m": 20.0,
            "duplicate_id_policy": "error",
            "incomplete_row_policy": "ignore_with_warning",
            "outlier_rule": "planned_or_realized_gt_threshold",
            "minimum_matched_rows": 1,
            "detail_rows_per_page": 44,
            "top_deviation_count": 10,
            "outlier_preview_count": 20,
        },
        "outputs": {
            "pdf_template": "RELATORIO_PROFUNDIDADES_{run_id}.pdf",
            "csv_template": "RELATORIO_PROFUNDIDADES_{run_id}_BASE_ANALITICA.csv",
            "log_template": "RELATORIO_PROFUNDIDADES_{run_id}.log",
            "report_plan_id": "TEST-PLAN",
            "report_plan_label": "ID DO PLANO",
            "report_table_headers": {
                "id": "ID",
                "planned": "Prof. prevista (m)",
                "realized": "Prof. realizada (m)",
                "variation": "Variação (m)",
            },
            "brand_logo_file": None,
        },
        "logging": {"level": "INFO", "console": False, "file": True},
    }
    config_path = root / "config.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "root": root,
        "config": config_path,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "logs_dir": logs_dir,
        "planned_file": planned_file,
        "realized_file": realized_file,
    }
