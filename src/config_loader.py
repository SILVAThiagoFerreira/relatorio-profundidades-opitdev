"""Configuration loading and runtime context assembly."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .exceptions import ConfigError
from .models import AppConfig, DXFLayerSpec, DXFSourceSpec, ExecutionContext, WorkbookSpec


def _require(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing required key '{section}.{key}' in config")
    return mapping[key]


def _resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _to_bool(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"Config key '{key}' must be boolean")


def _to_int(value: Any, key: str) -> int:
    if isinstance(value, bool):
        raise ConfigError(f"Config key '{key}' must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Config key '{key}' must be an integer") from exc
    return number


def _to_float(value: Any, key: str) -> float:
    if isinstance(value, bool):
        raise ConfigError(f"Config key '{key}' must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Config key '{key}' must be numeric") from exc
    return number


def _build_spec(data: dict[str, Any], section: str) -> WorkbookSpec:
    role = str(_require(data, "role", section)).strip()
    label = str(_require(data, "label", section)).strip()
    file_name = str(_require(data, "file_name", section)).strip()
    id_column = str(_require(data, "id_column", section)).strip()
    depth_column = str(_require(data, "depth_column", section)).strip()
    header_row = _to_int(data.get("header_row", 1), f"{section}.header_row")
    sheet_name = data.get("sheet_name")
    if not role or not label or not file_name or not id_column or not depth_column:
        raise ConfigError(f"Config section '{section}' contains empty required values")
    if header_row < 1:
        raise ConfigError(f"Config key '{section}.header_row' must be >= 1")
    return WorkbookSpec(
        role=role,
        label=label,
        file_name=file_name,
        sheet_name=None if sheet_name in (None, "") else str(sheet_name),
        header_row=header_row,
        id_column=id_column,
        depth_column=depth_column,
    )


def _build_dxf_layer_spec(data: dict[str, Any], section: str, expected_role: str) -> DXFLayerSpec:
    if not isinstance(data, dict):
        raise ConfigError(f"Config section '{section}' must be an object")
    role = str(_require(data, "role", section)).strip().lower()
    label = str(_require(data, "label", section)).strip()
    layer_name = str(_require(data, "layer_name", section)).strip()
    entity_type = str(_require(data, "entity_type", section)).strip().upper()
    depth_measure = str(_require(data, "depth_measure", section)).strip().lower()
    id_column = str(_require(data, "id_column", section)).strip()
    depth_column = str(_require(data, "depth_column", section)).strip()
    supported_measures = {"LINE": "3d_length", "POLYLINE": "3d_path_length"}
    if role != expected_role:
        raise ConfigError(f"Config section '{section}.role' must be '{expected_role}'")
    if not all((label, layer_name, entity_type, id_column, depth_column)):
        raise ConfigError(f"Config section '{section}' contains empty required values")
    if supported_measures.get(entity_type) != depth_measure:
        raise ConfigError(
            f"Config section '{section}' must pair LINE with 3d_length or POLYLINE with 3d_path_length"
        )
    return DXFLayerSpec(
        role=role,
        label=label,
        layer_name=layer_name,
        entity_type=entity_type,
        depth_measure=depth_measure,
        id_column=id_column,
        depth_column=depth_column,
    )


def _build_dxf_source(data: dict[str, Any]) -> DXFSourceSpec:
    section = "inputs.dxf"
    if not isinstance(data, dict):
        raise ConfigError(f"Config section '{section}' must be an object")
    file_name = str(_require(data, "file_name", section)).strip()
    id_layer = str(_require(data, "id_layer", section)).strip()
    id_entity_type = str(_require(data, "id_entity_type", section)).strip().upper()
    id_match_tolerance_m = _to_float(
        _require(data, "id_match_tolerance_m", section), f"{section}.id_match_tolerance_m"
    )
    drawing_units_to_meters = _to_float(
        _require(data, "drawing_units_to_meters", section), f"{section}.drawing_units_to_meters"
    )
    if not file_name or not id_layer:
        raise ConfigError(f"Config section '{section}' requires a file name and ID layer")
    if id_entity_type not in {"TEXT", "MTEXT"}:
        raise ConfigError(f"Config key '{section}.id_entity_type' must be TEXT or MTEXT")
    if id_match_tolerance_m <= 0 or drawing_units_to_meters <= 0:
        raise ConfigError(f"DXF matching tolerance and drawing unit scale in '{section}' must be > 0")

    planned = _build_dxf_layer_spec(_require(data, "planned", section), f"{section}.planned", "planned")
    realized = _build_dxf_layer_spec(_require(data, "realized", section), f"{section}.realized", "realized")
    if planned.layer_name.casefold() == realized.layer_name.casefold():
        raise ConfigError("Planned and realized DXF layers must be different")
    return DXFSourceSpec(
        file_name=file_name,
        id_layer=id_layer,
        id_entity_type=id_entity_type,
        id_match_tolerance_m=id_match_tolerance_m,
        drawing_units_to_meters=drawing_units_to_meters,
        planned=planned,
        realized=realized,
    )


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path).resolve()
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file: {path}") from exc

    project_root = _resolve_path(path.parent, str(data.get("project_root", ".")))

    directories = _require(data, "directories", "root")
    inputs = _require(data, "inputs", "root")
    rules = _require(data, "rules", "root")
    outputs = _require(data, "outputs", "root")
    logging = _require(data, "logging", "root")
    execution = _require(data, "execution", "root")

    input_dir = _resolve_path(project_root, str(_require(directories, "input", "directories")))
    output_dir = _resolve_path(project_root, str(_require(directories, "output", "directories")))
    logs_dir = _resolve_path(project_root, str(_require(directories, "logs", "directories")))

    input_format = str(_require(inputs, "format", "inputs")).strip().lower()
    planned: WorkbookSpec | None = None
    realized: WorkbookSpec | None = None
    dxf_source: DXFSourceSpec | None = None
    if input_format == "workbook":
        planned = _build_spec(_require(inputs, "planned", "inputs"), "inputs.planned")
        realized = _build_spec(_require(inputs, "realized", "inputs"), "inputs.realized")
    elif input_format == "dxf":
        dxf_source = _build_dxf_source(_require(inputs, "dxf", "inputs"))
    else:
        raise ConfigError("Config key 'inputs.format' must be 'workbook' or 'dxf'")

    run_id_strategy = str(_require(execution, "run_id_strategy", "execution")).strip().lower()
    timestamp_format = str(_require(execution, "timestamp_format", "execution")).strip()
    if run_id_strategy != "timestamp":
        raise ConfigError("Only 'timestamp' run_id strategy is supported")

    depth_tolerance_m = _to_float(_require(rules, "depth_tolerance_m", "rules"), "rules.depth_tolerance_m")
    outlier_threshold_m = _to_float(_require(rules, "outlier_threshold_m", "rules"), "rules.outlier_threshold_m")
    duplicate_id_policy = str(_require(rules, "duplicate_id_policy", "rules")).strip().lower()
    if duplicate_id_policy != "error":
        raise ConfigError("Only 'error' duplicate_id_policy is supported")
    incomplete_row_policy = str(_require(rules, "incomplete_row_policy", "rules")).strip().lower()
    if incomplete_row_policy != "ignore_with_warning":
        raise ConfigError("Only 'ignore_with_warning' incomplete_row_policy is supported")
    if depth_tolerance_m <= 0:
        raise ConfigError("rules.depth_tolerance_m must be > 0")
    if outlier_threshold_m <= 0:
        raise ConfigError("rules.outlier_threshold_m must be > 0")

    output_pdf_template = str(_require(outputs, "pdf_template", "outputs")).strip()
    output_csv_template = str(_require(outputs, "csv_template", "outputs")).strip()
    log_template = str(_require(outputs, "log_template", "outputs")).strip()
    report_plan_id = str(_require(outputs, "report_plan_id", "outputs")).strip()
    report_plan_label = str(_require(outputs, "report_plan_label", "outputs")).strip()
    header_data = _require(outputs, "report_table_headers", "outputs")
    if not isinstance(header_data, dict):
        raise ConfigError("Config key 'outputs.report_table_headers' must be an object")
    header_keys = ("id", "planned", "realized", "variation")
    report_table_headers = tuple(
        str(_require(header_data, key, "outputs.report_table_headers")).strip()
        for key in header_keys
    )
    if not report_plan_id or not report_plan_label or any(not label for label in report_table_headers):
        raise ConfigError("Plan ID, plan label and all report table headers must be non-empty")

    brand_logo_value = outputs.get("brand_logo_file")
    brand_logo_path = _resolve_path(project_root, str(brand_logo_value)) if brand_logo_value else None
    if brand_logo_path is not None and not brand_logo_path.is_file():
        raise ConfigError(f"ENAEX logo file not found: {brand_logo_path}")

    for template_key, template in {
        "outputs.pdf_template": output_pdf_template,
        "outputs.csv_template": output_csv_template,
        "outputs.log_template": log_template,
    }.items():
        if "{run_id}" not in template:
            raise ConfigError(f"{template_key} must contain 'run_id' placeholder")

    logging_level = str(_require(logging, "level", "logging")).strip().upper()
    console_logging = _to_bool(logging.get("console", True), "logging.console")
    file_logging = _to_bool(logging.get("file", True), "logging.file")
    if not console_logging and not file_logging:
        raise ConfigError("At least one logging target must be enabled")

    detail_rows_per_page = _to_int(_require(rules, "detail_rows_per_page", "rules"), "rules.detail_rows_per_page")
    top_deviation_count = _to_int(_require(rules, "top_deviation_count", "rules"), "rules.top_deviation_count")
    outlier_preview_count = _to_int(_require(rules, "outlier_preview_count", "rules"), "rules.outlier_preview_count")
    minimum_matched_rows = _to_int(_require(rules, "minimum_matched_rows", "rules"), "rules.minimum_matched_rows")
    for key, value in {
        "rules.detail_rows_per_page": detail_rows_per_page,
        "rules.top_deviation_count": top_deviation_count,
        "rules.outlier_preview_count": outlier_preview_count,
        "rules.minimum_matched_rows": minimum_matched_rows,
    }.items():
        if value < 1:
            raise ConfigError(f"{key} must be >= 1")

    return AppConfig(
        project_root=project_root,
        input_dir=input_dir,
        output_dir=output_dir,
        logs_dir=logs_dir,
        input_format=input_format,
        run_id_strategy=run_id_strategy,
        timestamp_format=timestamp_format,
        planned=planned,
        realized=realized,
        dxf_source=dxf_source,
        depth_tolerance_m=depth_tolerance_m,
        outlier_threshold_m=outlier_threshold_m,
        duplicate_id_policy=duplicate_id_policy,
        incomplete_row_policy=incomplete_row_policy,
        minimum_matched_rows=minimum_matched_rows,
        output_pdf_template=output_pdf_template,
        output_csv_template=output_csv_template,
        log_template=log_template,
        report_plan_id=report_plan_id,
        report_plan_label=report_plan_label,
        report_table_headers=report_table_headers,
        brand_logo_path=brand_logo_path,
        logging_level=logging_level,
        console_logging=console_logging,
        file_logging=file_logging,
        detail_rows_per_page=detail_rows_per_page,
        top_deviation_count=top_deviation_count,
        outlier_preview_count=outlier_preview_count,
    )


def build_execution_context(config: AppConfig, started_at: datetime | None = None, run_id: str | None = None) -> ExecutionContext:
    started_at = started_at or datetime.now()
    if run_id is None:
        if config.run_id_strategy != "timestamp":
            raise ConfigError(f"Unsupported run_id strategy: {config.run_id_strategy}")
        run_id = started_at.strftime(config.timestamp_format)
    elif not re.fullmatch(r"[A-Za-z0-9._-]+", run_id):
        raise ConfigError("Manual run_id must contain only letters, numbers, dot, underscore or dash")

    output_pdf = config.output_dir / config.output_pdf_template.format(run_id=run_id)
    output_csv = config.output_dir / config.output_csv_template.format(run_id=run_id)
    log_file = config.logs_dir / config.log_template.format(run_id=run_id)
    return ExecutionContext(run_id=run_id, started_at=started_at, output_pdf=output_pdf, output_csv=output_csv, log_file=log_file)
