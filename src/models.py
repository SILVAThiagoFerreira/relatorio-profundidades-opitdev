"""Data structures used by the report pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkbookSpec:
    """Configuration for a single workbook source."""

    role: str
    label: str
    file_name: str
    sheet_name: str | None
    header_row: int
    id_column: str
    depth_column: str


@dataclass(frozen=True)
class DXFLayerSpec:
    """A depth dataset represented by a configured DXF layer."""

    role: str
    label: str
    layer_name: str
    entity_type: str
    depth_measure: str
    id_column: str
    depth_column: str


@dataclass(frozen=True)
class DXFSourceSpec:
    """DXF file and geometry-to-ID mapping settings."""

    file_name: str
    id_layer: str
    id_entity_type: str
    id_match_tolerance_m: float
    drawing_units_to_meters: float
    planned: DXFLayerSpec
    realized: DXFLayerSpec


@dataclass(frozen=True)
class AppConfig:
    """Normalized application configuration."""

    project_root: Path
    input_dir: Path
    output_dir: Path
    logs_dir: Path
    input_format: str
    run_id_strategy: str
    timestamp_format: str
    planned: WorkbookSpec | None
    realized: WorkbookSpec | None
    dxf_source: DXFSourceSpec | None
    depth_tolerance_m: float
    outlier_threshold_m: float
    duplicate_id_policy: str
    incomplete_row_policy: str
    minimum_matched_rows: int
    output_pdf_template: str
    output_csv_template: str
    log_template: str
    report_plan_id: str
    report_plan_label: str
    report_table_headers: tuple[str, str, str, str]
    brand_logo_path: Path | None
    logging_level: str
    console_logging: bool
    file_logging: bool
    detail_rows_per_page: int
    top_deviation_count: int
    outlier_preview_count: int


@dataclass(frozen=True)
class RawRow:
    """Single normalized source record before validation."""

    row_number: int
    values: dict[str, Any]


@dataclass(frozen=True)
class RawDataset:
    """Raw source snapshot before validation (workbook or DXF layer)."""

    label: str
    path: Path
    sheet_name: str
    headers: list[str]
    rows: list[RawRow]


RawWorkbook = RawDataset


@dataclass(frozen=True)
class ValidatedRecord:
    """Validated and normalized single source record."""

    hole_id: int
    depth: float
    row_number: int
    raw: dict[str, Any]


@dataclass(frozen=True)
class ValidatedDataset:
    """Validated source dataset ready for processing."""

    label: str
    path: Path
    sheet_name: str
    id_column: str
    depth_column: str
    records: list[ValidatedRecord]


@dataclass(frozen=True)
class ComparisonRecord:
    """Single planned vs realized comparison."""

    hole_id: int
    planned_depth: float
    realized_depth: float
    diff: float
    abs_diff: float
    planned_row_number: int
    realized_row_number: int
    status: str
    is_outlier: bool
    outlier_reason: str = ""


@dataclass(frozen=True)
class ReportMetrics:
    """Aggregate statistics for the report."""

    total_planned: int
    total_realized: int
    total_matched: int
    planned_only_count: int
    realized_only_count: int
    outlier_count: int
    analyzed_count: int
    adherent_count: int
    above_count: int
    below_count: int
    adherent_rate: float | None
    non_adherent_rate: float | None
    diff_mean: float | None
    diff_median: float | None
    abs_diff_mean: float | None
    diff_all_mean: float | None
    abs_diff_all_mean: float | None
    max_positive: ComparisonRecord | None
    max_negative: ComparisonRecord | None
    top_valid_abs: list[ComparisonRecord]
    top_outliers_abs: list[ComparisonRecord]
    outlier_threshold_m: float


@dataclass(frozen=True)
class ExecutionContext:
    """Run-specific paths and identifiers."""

    run_id: str
    started_at: datetime
    output_pdf: Path
    output_csv: Path
    log_file: Path


@dataclass(frozen=True)
class ReportResult:
    """Final processed result delivered to the writer."""

    planned: ValidatedDataset
    realized: ValidatedDataset
    comparison_records: list[ComparisonRecord]
    planned_only: list[int]
    realized_only: list[int]
    metrics: ReportMetrics
    execution: ExecutionContext
