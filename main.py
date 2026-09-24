"""Single entry point for the depth report system."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.config_loader import build_execution_context, load_config
from src.data_reader import read_workbook
from src.dxf_reader import read_dxf_datasets
from src.exceptions import ConfigError, ProjectError
from src.logger_setup import setup_logging
from src.output_writer import write_outputs
from src.processor import compare_depths
from src.validator import validate_dataset


def run(config_path: str | Path, run_id: str | None = None) -> int:
    config = load_config(config_path)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)

    context = build_execution_context(config, started_at=datetime.now(), run_id=run_id)
    logger = setup_logging(config, context)

    try:
        logger.info("Loading input sources using format=%s", config.input_format)
        if config.input_format == "dxf":
            if config.dxf_source is None:
                raise ConfigError("DXF input format requires inputs.dxf configuration")
            planned_spec = config.dxf_source.planned
            realized_spec = config.dxf_source.realized
            logger.info(
                "Reading DXF %s: planned layer=%s, realized layer=%s, ID layer=%s",
                config.dxf_source.file_name,
                planned_spec.layer_name,
                realized_spec.layer_name,
                config.dxf_source.id_layer,
            )
            planned_raw, realized_raw = read_dxf_datasets(config.dxf_source, config.input_dir)
        else:
            if config.planned is None or config.realized is None:
                raise ConfigError("Workbook input format requires planned and realized workbook configuration")
            planned_spec = config.planned
            realized_spec = config.realized
            planned_raw = read_workbook(config, planned_spec)
            realized_raw = read_workbook(config, realized_spec)

        logger.info("Validating planned source")
        planned = validate_dataset(config, planned_raw, planned_spec, logger=logger)
        logger.info("Validating realized source")
        realized = validate_dataset(config, realized_raw, realized_spec, logger=logger)

        logger.info("Processing comparison")
        result = compare_depths(config, planned, realized, context)
        if result.planned_only:
            logger.warning("Planned IDs without a realized record: %s", result.planned_only)
        if result.realized_only:
            logger.warning("Realized IDs without a planned record: %s", result.realized_only)

        logger.info("Writing outputs")
        write_outputs(config, result)

        logger.info(
            "Completed run: matched=%s analyzed=%s adherent_rate=%s outliers=%s",
            result.metrics.total_matched,
            result.metrics.analyzed_count,
            result.metrics.adherent_rate,
            result.metrics.outlier_count,
        )
        return 0
    except ProjectError:
        logger.exception("Run failed")
        raise
    finally:
        for handler in list(logger.handlers):
            handler.flush()
            handler.close()
            logger.removeHandler(handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the drilling depth adherence report")
    parser.add_argument("--config", default="config.json", help="Path to the JSON configuration file")
    parser.add_argument("--run-id", default=None, help="Optional run identifier override")
    args = parser.parse_args(argv)

    try:
        return run(args.config, run_id=args.run_id)
    except ProjectError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - unexpected runtime failures
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
