"""Structural and semantic validation for source datasets."""

from __future__ import annotations

import logging
import math
from typing import Any

from .exceptions import ValidationError
from .models import AppConfig, DXFLayerSpec, RawDataset, ValidatedDataset, ValidatedRecord, WorkbookSpec


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip().replace(",", ".")
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _to_int(value: Any) -> int | None:
    number = _to_float(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def validate_dataset(
    config: AppConfig,
    raw: RawDataset,
    spec: WorkbookSpec | DXFLayerSpec,
    logger: logging.Logger | None = None,
) -> ValidatedDataset:
    """Validate and normalize one tabularized source dataset."""

    errors: list[str] = []
    required_columns = {spec.id_column, spec.depth_column}
    missing_columns = sorted(required_columns - set(raw.headers))
    if missing_columns:
        errors.append(f"{raw.label}: missing required columns {missing_columns}")
        raise ValidationError("\n".join(errors))

    if not raw.rows:
        raise ValidationError(f"{raw.label}: no data rows found in sheet '{raw.sheet_name}'")

    normalized: list[ValidatedRecord] = []
    seen_ids: dict[int, int] = {}
    ignored_incomplete_rows = 0
    for row in raw.rows:
        raw_id = row.values.get(spec.id_column)
        raw_depth = row.values.get(spec.depth_column)
        if raw_id in (None, "") or raw_depth in (None, ""):
            if config.incomplete_row_policy == "ignore_with_warning":
                ignored_incomplete_rows += 1
                continue
            errors.append(
                f"{raw.label} row {row.row_number}: incomplete row missing required fields '{spec.id_column}' or '{spec.depth_column}'"
            )
            continue

        hole_id = _to_int(raw_id)
        depth = _to_float(raw_depth)

        if hole_id is None:
            errors.append(f"{raw.label} row {row.row_number}: invalid ID in '{spec.id_column}' -> {raw_id!r}")
            continue
        if hole_id <= 0:
            errors.append(f"{raw.label} row {row.row_number}: ID must be positive -> {hole_id}")
            continue

        if depth is None:
            errors.append(f"{raw.label} row {row.row_number}: invalid depth in '{spec.depth_column}' -> {raw_depth!r}")
            continue
        if depth <= 0:
            errors.append(f"{raw.label} row {row.row_number}: depth must be positive -> {depth}")
            continue

        if hole_id in seen_ids:
            previous_row = seen_ids[hole_id]
            errors.append(
                f"{raw.label} row {row.row_number}: duplicate ID {hole_id} (already seen at row {previous_row})"
            )
            continue

        seen_ids[hole_id] = row.row_number
        normalized.append(ValidatedRecord(hole_id=hole_id, depth=depth, row_number=row.row_number, raw=row.values))

    if errors:
        raise ValidationError("\n".join(errors))

    if logger and ignored_incomplete_rows:
        logger.warning("%s: ignored %s incomplete rows without both key fields", raw.label, ignored_incomplete_rows)

    if not normalized:
        raise ValidationError(f"{raw.label}: no valid data rows found after filtering incomplete rows")

    return ValidatedDataset(
        label=raw.label,
        path=raw.path,
        sheet_name=raw.sheet_name,
        id_column=spec.id_column,
        depth_column=spec.depth_column,
        records=normalized,
    )


validate_workbook = validate_dataset
