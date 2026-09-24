"""Read IDs and hole depths from configured DXF layers."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .exceptions import DataReadError
from .models import DXFLayerSpec, DXFSourceSpec, RawDataset, RawRow


def _entity_position(entity: Any) -> tuple[float, float, float]:
    if entity.dxftype() == "TEXT" or entity.dxftype() == "MTEXT":
        point = entity.dxf.insert
        return float(point.x), float(point.y), float(point.z)
    if entity.dxftype() == "LINE":
        point = entity.dxf.start
        return float(point.x), float(point.y), float(point.z)
    if entity.dxftype() == "POLYLINE":
        vertices = entity.vertices
        if not vertices:
            raise DataReadError(f"Empty POLYLINE entity in DXF handle {entity.dxf.handle}")
        point = vertices[0].dxf.location
        return float(point.x), float(point.y), float(point.z)
    raise DataReadError(f"Unsupported DXF entity type '{entity.dxftype()}'")


def _entity_depth_m(entity: Any, spec: DXFLayerSpec, scale_to_meters: float) -> float:
    if spec.depth_measure == "3d_length" and entity.dxftype() == "LINE":
        start = tuple(entity.dxf.start)
        end = tuple(entity.dxf.end)
        return math.dist(start, end) * scale_to_meters

    if spec.depth_measure == "3d_path_length" and entity.dxftype() == "POLYLINE":
        if entity.is_closed:
            raise DataReadError(f"Closed POLYLINE is not a valid depth path (handle {entity.dxf.handle})")
        points = [tuple(vertex.dxf.location) for vertex in entity.vertices]
        if len(points) < 2:
            raise DataReadError(f"POLYLINE depth path has fewer than two vertices (handle {entity.dxf.handle})")
        return sum(math.dist(start, end) for start, end in zip(points, points[1:])) * scale_to_meters

    raise DataReadError(
        f"DXF entity '{entity.dxftype()}' in layer '{spec.layer_name}' does not match depth measure '{spec.depth_measure}'"
    )


def _layer_entities(doc: Any, layer_name: str, expected_type: str, path: Path) -> list[Any]:
    actual_name = next(
        (layer.dxf.name for layer in doc.layers if layer.dxf.name.casefold() == layer_name.casefold()),
        None,
    )
    if actual_name is None:
        raise DataReadError(f"DXF layer '{layer_name}' not found in '{path.name}'")

    entities = [entity for entity in doc.modelspace() if entity.dxf.layer.casefold() == actual_name.casefold()]
    unexpected = sorted({entity.dxftype() for entity in entities if entity.dxftype() != expected_type})
    if unexpected:
        raise DataReadError(
            f"DXF layer '{actual_name}' contains unexpected entity types {unexpected}; expected only {expected_type}"
        )
    if not entities:
        raise DataReadError(f"DXF layer '{actual_name}' contains no {expected_type} entities")
    return entities


def _id_text(entity: Any) -> str:
    value = entity.dxf.text if entity.dxftype() == "TEXT" else entity.plain_text()
    return str(value).strip()


def _build_dataset(
    path: Path,
    id_entities: list[Any],
    geometry_entities: list[Any],
    source: DXFSourceSpec,
    layer_spec: DXFLayerSpec,
    allow_missing_geometry: bool,
) -> RawDataset:
    tolerance_units = source.id_match_tolerance_m / source.drawing_units_to_meters
    assigned_entities: set[int] = set()
    rows: list[RawRow] = []

    for row_number, id_entity in enumerate(id_entities, start=1):
        id_position = _entity_position(id_entity)
        distances = [
            (math.dist(id_position, _entity_position(geometry)), index)
            for index, geometry in enumerate(geometry_entities)
        ]
        distances.sort()
        if not distances or distances[0][0] > tolerance_units:
            if allow_missing_geometry:
                continue
            closest = distances[0][0] if distances else math.inf
            raise DataReadError(
                f"No {layer_spec.role} geometry within {source.id_match_tolerance_m:g} m of ID label "
                f"'{_id_text(id_entity)}' in DXF layer '{layer_spec.layer_name}' (nearest={closest:g} drawing units)"
            )

        if len(distances) > 1 and abs(distances[1][0] - distances[0][0]) <= 1e-7:
            raise DataReadError(
                f"ID label '{_id_text(id_entity)}' has ambiguous nearby geometry in DXF layer '{layer_spec.layer_name}'"
            )
        entity_index = distances[0][1]
        if entity_index in assigned_entities:
            raise DataReadError(
                f"Multiple ID labels map to the same geometry in DXF layer '{layer_spec.layer_name}'"
            )
        assigned_entities.add(entity_index)

        geometry = geometry_entities[entity_index]
        rows.append(
            RawRow(
                row_number=row_number,
                values={
                    layer_spec.id_column: _id_text(id_entity),
                    layer_spec.depth_column: _entity_depth_m(geometry, layer_spec, source.drawing_units_to_meters),
                },
            )
        )

    unassigned = len(geometry_entities) - len(assigned_entities)
    if unassigned:
        raise DataReadError(
            f"{unassigned} {layer_spec.entity_type} entities in DXF layer '{layer_spec.layer_name}' "
            "could not be associated with an ID label"
        )
    return RawDataset(
        label=layer_spec.label,
        path=path,
        sheet_name=layer_spec.layer_name,
        headers=[layer_spec.id_column, layer_spec.depth_column],
        rows=rows,
    )


def read_dxf_datasets(source: DXFSourceSpec, input_dir: Path) -> tuple[RawDataset, RawDataset]:
    """Read the planned and realized geometry using configured DXF layers."""
    try:
        import ezdxf
    except ImportError as exc:  # pragma: no cover - dependency installation varies by environment
        raise DataReadError("DXF source requires ezdxf; install it with 'python -m pip install ezdxf'") from exc

    file_path = Path(source.file_name)
    path = file_path if file_path.is_absolute() else (input_dir / file_path).resolve()
    if not path.is_file():
        raise DataReadError(f"Input DXF file not found: {path}")
    try:
        doc = ezdxf.readfile(path)
    except Exception as exc:  # pragma: no cover - ezdxf exposes multiple parser errors
        raise DataReadError(f"Unable to read DXF file: {path}") from exc

    id_entities = _layer_entities(doc, source.id_layer, source.id_entity_type, path)
    planned_geometry = _layer_entities(doc, source.planned.layer_name, source.planned.entity_type, path)
    realized_geometry = _layer_entities(doc, source.realized.layer_name, source.realized.entity_type, path)
    planned = _build_dataset(
        path,
        id_entities,
        planned_geometry,
        source,
        source.planned,
        allow_missing_geometry=False,
    )
    realized = _build_dataset(
        path,
        id_entities,
        realized_geometry,
        source,
        source.realized,
        allow_missing_geometry=True,
    )
    return planned, realized
