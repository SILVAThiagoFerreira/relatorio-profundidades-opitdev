"""CSV and compact ENAEX-styled PDF output generation."""

from __future__ import annotations

import csv
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle

from .exceptions import OutputError
from .models import AppConfig, ReportResult

ENAEX_RED = colors.HexColor("#E31B23")
ENAEX_NAVY = colors.HexColor("#273747")
TEXT = colors.HexColor("#263746")
MUTED = colors.HexColor("#68727B")
RULE = colors.HexColor("#D5D9DC")
HEADER_FILL = colors.HexColor("#F1F3F5")
WHITE = colors.white


def _fmt_num(value: float | int | None, digits: int = 2, signed: bool = False) -> str:
    if value is None:
        return ""
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return text.replace(".", ",")


def _make_list_table(
    records: list[tuple[int, float | None, float | None, float | None]],
    config: AppConfig,
) -> Table:
    plan_style = ParagraphStyle(
        "plan_id",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=ENAEX_NAVY,
        alignment=0,
    )
    column_style = ParagraphStyle(
        "column_header",
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=10,
        textColor=ENAEX_NAVY,
        alignment=1,
    )
    id_style = ParagraphStyle(
        "hole_id",
        fontName="Helvetica",
        fontSize=8.1,
        leading=9.4,
        textColor=TEXT,
        alignment=1,
    )
    value_style = ParagraphStyle(
        "depth_value",
        fontName="Helvetica",
        fontSize=8.1,
        leading=9.4,
        textColor=TEXT,
        alignment=2,
    )

    plan_text = (
        f'<font color="{ENAEX_RED.hexval()}">{escape(config.report_plan_label)}</font>'
        f'&nbsp;&nbsp;<b>{escape(config.report_plan_id)}</b>'
    )
    data: list[list[object]] = [
        [Paragraph(plan_text, plan_style), "", "", ""],
        [Paragraph(escape(label), column_style) for label in config.report_table_headers],
    ]
    for hole_id, planned_depth, realized_depth, variation in records:
        data.append([
            Paragraph(str(hole_id), id_style),
            Paragraph(_fmt_num(planned_depth), value_style),
            Paragraph(_fmt_num(realized_depth), value_style),
            Paragraph(_fmt_num(variation, signed=variation is not None), value_style),
        ])

    table = Table(
        data,
        colWidths=[2.3 * cm, 5.2 * cm, 5.4 * cm, 5.4 * cm],
        repeatRows=2,
        hAlign="LEFT",
    )
    commands = [
        ("SPAN", (0, 0), (-1, 0)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 1), (-1, 1), HEADER_FILL),
        ("LINEBELOW", (0, 1), (-1, 1), 0.8, ENAEX_NAVY),
        ("LINEBELOW", (0, 2), (-1, -1), 0.35, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 5),
        ("TOPPADDING", (0, 2), (-1, -1), 1.3),
        ("BOTTOMPADDING", (0, 2), (-1, -1), 1.3),
    ]
    for row_index in range(2, len(data)):
        if (row_index - 2) % 2 == 1:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#FAFBFC")))
    table.setStyle(TableStyle(commands))
    return table


def _draw_page_chrome(c: canvas.Canvas, doc: SimpleDocTemplate, config: AppConfig) -> None:
    c.saveState()
    if config.brand_logo_path is not None:
        logo = ImageReader(str(config.brand_logo_path))
        image_width, image_height = logo.getSize()
        max_width = 5.0 * cm
        max_height = 1.25 * cm
        scale = min(max_width / image_width, max_height / image_height)
        draw_width = image_width * scale
        draw_height = image_height * scale
        c.drawImage(
            logo,
            A4[0] - doc.rightMargin - draw_width,
            A4[1] - 1.65 * cm,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )

    c.setStrokeColor(ENAEX_RED)
    c.setLineWidth(0.7)
    c.line(doc.leftMargin, A4[1] - 1.95 * cm, A4[0] - doc.rightMargin, A4[1] - 1.95 * cm)

    c.setStrokeColor(RULE)
    c.setLineWidth(0.45)
    c.line(doc.leftMargin, 1.05 * cm, A4[0] - doc.rightMargin, 1.05 * cm)
    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED)
    c.drawRightString(A4[0] - doc.rightMargin, 0.68 * cm, str(c.getPageNumber()))
    c.restoreState()


def _write_csv(result: ReportResult) -> None:
    result.execution.output_csv.parent.mkdir(parents=True, exist_ok=True)
    try:
        with result.execution.output_csv.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["ID", "Prevista_m", "Realizada_m", "Desvio_m", "Status", "Outlier", "Motivo_outlier", "Prevista_linha", "Realizada_linha"])
            for record in result.comparison_records:
                writer.writerow([
                    record.hole_id,
                    _fmt_num(record.planned_depth),
                    _fmt_num(record.realized_depth),
                    _fmt_num(record.diff, signed=True),
                    record.status,
                    "Sim" if record.is_outlier else "Nao",
                    record.outlier_reason,
                    record.planned_row_number,
                    record.realized_row_number,
                ])
    except Exception as exc:  # pragma: no cover - filesystem specific
        raise OutputError(f"Unable to write CSV output: {result.execution.output_csv}") from exc


def _build_pdf_story(config: AppConfig, result: ReportResult) -> list[object]:
    planned = {record.hole_id: record.depth for record in result.planned.records}
    realized = {record.hole_id: record.depth for record in result.realized.records}
    records = []
    for hole_id in sorted(set(planned) | set(realized)):
        planned_depth = planned.get(hole_id)
        realized_depth = realized.get(hole_id)
        variation = realized_depth - planned_depth if planned_depth is not None and realized_depth is not None else None
        records.append((hole_id, planned_depth, realized_depth, variation))
    story: list[object] = []
    for start in range(0, len(records), config.detail_rows_per_page):
        if start:
            story.append(PageBreak())
        story.append(_make_list_table(records[start:start + config.detail_rows_per_page], config))
    return story


def write_outputs(config: AppConfig, result: ReportResult) -> None:
    """Write the analytical CSV and the compact ENAEX-styled list PDF."""
    try:
        _write_csv(result)

        result.execution.output_pdf.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(result.execution.output_pdf),
            pagesize=A4,
            rightMargin=1.35 * cm,
            leftMargin=1.35 * cm,
            topMargin=2.25 * cm,
            bottomMargin=1.45 * cm,
            title=f"{config.report_plan_label} {config.report_plan_id}",
            author="ENAEX Brasil",
        )
        doc.build(
            _build_pdf_story(config, result),
            onFirstPage=lambda page_canvas, page_doc: _draw_page_chrome(page_canvas, page_doc, config),
            onLaterPages=lambda page_canvas, page_doc: _draw_page_chrome(page_canvas, page_doc, config),
        )
    except OutputError:
        raise
    except Exception as exc:  # pragma: no cover - ReportLab/filesystem failures are environment specific
        raise OutputError("Unable to write report outputs") from exc
