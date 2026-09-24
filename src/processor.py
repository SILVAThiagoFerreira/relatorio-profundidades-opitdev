"""Depth comparison and metrics calculation."""

from __future__ import annotations

import statistics

from .exceptions import ProcessingError
from .models import AppConfig, ComparisonRecord, ExecutionContext, ReportMetrics, ReportResult, ValidatedDataset, ValidatedRecord


def _safe_mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _safe_median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _build_map(dataset: ValidatedDataset) -> dict[int, ValidatedRecord]:
    return {record.hole_id: record for record in dataset.records}


def compare_depths(config: AppConfig, planned: ValidatedDataset, realized: ValidatedDataset, execution: ExecutionContext) -> ReportResult:
    """Compare planned and realized datasets and calculate report metrics."""

    planned_map = _build_map(planned)
    realized_map = _build_map(realized)
    shared_ids = sorted(set(planned_map) & set(realized_map))
    if not shared_ids:
        raise ProcessingError("No matching IDs found between planned and realized datasets")
    if len(shared_ids) < config.minimum_matched_rows:
        raise ProcessingError(
            f"Matched records ({len(shared_ids)}) below minimum required ({config.minimum_matched_rows})"
        )

    comparison_records: list[ComparisonRecord] = []
    for hole_id in shared_ids:
        planned_record = planned_map[hole_id]
        realized_record = realized_map[hole_id]
        diff = realized_record.depth - planned_record.depth
        is_outlier = planned_record.depth > config.outlier_threshold_m or realized_record.depth > config.outlier_threshold_m
        if is_outlier:
            status = "Outlier"
        elif abs(diff) <= config.depth_tolerance_m:
            status = "Aderente"
        elif diff > config.depth_tolerance_m:
            status = "Acima"
        else:
            status = "Abaixo"
        comparison_records.append(
            ComparisonRecord(
                hole_id=hole_id,
                planned_depth=planned_record.depth,
                realized_depth=realized_record.depth,
                diff=diff,
                abs_diff=abs(diff),
                planned_row_number=planned_record.row_number,
                realized_row_number=realized_record.row_number,
                status=status,
                is_outlier=is_outlier,
                outlier_reason="Furo acima de 20 m" if is_outlier else "",
            )
        )

    planned_only = sorted(set(planned_map) - set(realized_map))
    realized_only = sorted(set(realized_map) - set(planned_map))

    analyzed = [record for record in comparison_records if not record.is_outlier]
    outliers = [record for record in comparison_records if record.is_outlier]
    adherent = [record for record in analyzed if record.status == "Aderente"]
    above = [record for record in analyzed if record.status == "Acima"]
    below = [record for record in analyzed if record.status == "Abaixo"]

    analyzed_diffs = [record.diff for record in analyzed]
    all_diffs = [record.diff for record in comparison_records]

    metrics = ReportMetrics(
        total_planned=len(planned_map),
        total_realized=len(realized_map),
        total_matched=len(comparison_records),
        planned_only_count=len(planned_only),
        realized_only_count=len(realized_only),
        outlier_count=len(outliers),
        analyzed_count=len(analyzed),
        adherent_count=len(adherent),
        above_count=len(above),
        below_count=len(below),
        adherent_rate=(len(adherent) / len(analyzed)) if analyzed else None,
        non_adherent_rate=((len(above) + len(below)) / len(analyzed)) if analyzed else None,
        diff_mean=_safe_mean(analyzed_diffs),
        diff_median=_safe_median(analyzed_diffs),
        abs_diff_mean=_safe_mean([abs(value) for value in analyzed_diffs]),
        diff_all_mean=_safe_mean(all_diffs),
        abs_diff_all_mean=_safe_mean([abs(value) for value in all_diffs]),
        max_positive=max(analyzed, key=lambda record: record.diff) if analyzed else None,
        max_negative=min(analyzed, key=lambda record: record.diff) if analyzed else None,
        top_valid_abs=sorted(analyzed, key=lambda record: record.abs_diff, reverse=True)[: config.top_deviation_count],
        top_outliers_abs=sorted(outliers, key=lambda record: record.abs_diff, reverse=True)[: config.outlier_preview_count],
        outlier_threshold_m=config.outlier_threshold_m,
    )

    return ReportResult(
        planned=planned,
        realized=realized,
        comparison_records=comparison_records,
        planned_only=planned_only,
        realized_only=realized_only,
        metrics=metrics,
        execution=execution,
    )
