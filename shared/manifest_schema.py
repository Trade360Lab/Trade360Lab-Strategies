"""Manifest schema definitions and validation helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from shared.types import REQUIRED_OHLCV_COLUMNS, REQUIRED_SIGNAL_COLUMNS

REQUIRED_MANIFEST_FIELDS: tuple[str, ...] = (
    "slug",
    "name",
    "category",
    "version",
    "description",
    "direction",
    "class_name",
    "timeframes",
    "symbols",
    "required_columns",
    "outputs",
    "parameters",
)
ALLOWED_PARAMETER_TYPES = {"int", "float", "bool", "str", "enum"}
ALLOWED_DIRECTIONS = {"long", "short"}


class ManifestValidationError(ValueError):
    """Raised when a strategy manifest does not match the library contract."""


def validate_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize a manifest dictionary."""

    normalized = deepcopy(dict(manifest))
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in normalized]
    if missing:
        raise ManifestValidationError(
            "Manifest is missing required fields: " + ", ".join(missing)
        )

    if not isinstance(normalized["slug"], str) or not normalized["slug"].strip():
        raise ManifestValidationError("Manifest field 'slug' must be a non-empty string.")
    if not isinstance(normalized["name"], str) or not normalized["name"].strip():
        raise ManifestValidationError("Manifest field 'name' must be a non-empty string.")
    if not isinstance(normalized["category"], str) or not normalized["category"].strip():
        raise ManifestValidationError(
            "Manifest field 'category' must be a non-empty string."
        )
    if not isinstance(normalized["class_name"], str) or not normalized["class_name"].strip():
        raise ManifestValidationError(
            "Manifest field 'class_name' must be a non-empty string."
        )

    direction = normalized["direction"]
    if not isinstance(direction, list) or not direction:
        raise ManifestValidationError("Manifest field 'direction' must be a non-empty list.")
    if not set(direction).issubset(ALLOWED_DIRECTIONS):
        raise ManifestValidationError(
            "Manifest field 'direction' may only contain 'long' and 'short'."
        )

    for field in ("timeframes", "symbols", "required_columns", "outputs"):
        value = normalized[field]
        if not isinstance(value, list) or not value:
            raise ManifestValidationError(f"Manifest field '{field}' must be a non-empty list.")

    missing_required_columns = [
        column for column in REQUIRED_OHLCV_COLUMNS if column not in normalized["required_columns"]
    ]
    if missing_required_columns:
        raise ManifestValidationError(
            "Manifest field 'required_columns' must include OHLCV columns: "
            + ", ".join(missing_required_columns)
        )

    missing_signal_columns = [
        column for column in REQUIRED_SIGNAL_COLUMNS if column not in normalized["outputs"]
    ]
    if missing_signal_columns:
        raise ManifestValidationError(
            "Manifest field 'outputs' must include standard signal columns: "
            + ", ".join(missing_signal_columns)
        )

    parameters = normalized["parameters"]
    if not isinstance(parameters, dict):
        raise ManifestValidationError("Manifest field 'parameters' must be an object.")

    for name, definition in parameters.items():
        _validate_parameter_definition(name, definition)

    return normalized


def _validate_parameter_definition(name: str, definition: Any) -> None:
    if not isinstance(definition, dict):
        raise ManifestValidationError(
            f"Manifest parameter '{name}' must be described by an object."
        )
    parameter_type = definition.get("type")
    if parameter_type not in ALLOWED_PARAMETER_TYPES:
        raise ManifestValidationError(
            f"Manifest parameter '{name}' has unsupported type '{parameter_type}'."
        )
    if "default" not in definition:
        raise ManifestValidationError(
            f"Manifest parameter '{name}' must declare a default value."
        )
    if parameter_type == "enum" and not definition.get("options"):
        raise ManifestValidationError(
            f"Manifest parameter '{name}' of type 'enum' must define 'options'."
        )

