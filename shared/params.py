"""Helpers for strategy parameter defaults and optimizer metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from shared.manifest_schema import ManifestValidationError


def get_default_params(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the default parameter set from a validated manifest."""

    return {
        name: definition["default"]
        for name, definition in manifest.get("parameters", {}).items()
    }


def build_search_space(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Prepare optimizer-friendly parameter descriptors from the manifest."""

    search_space: dict[str, dict[str, Any]] = {}
    for name, definition in manifest.get("parameters", {}).items():
        if not definition.get("optimize", False):
            continue
        search_space[name] = {
            key: value
            for key, value in definition.items()
            if key in {"type", "min", "max", "step", "options", "default"}
        }
    return search_space


def validate_params_against_manifest(
    params: Mapping[str, Any], manifest: Mapping[str, Any]
) -> None:
    """Validate user-provided params against manifest metadata."""

    definitions = manifest.get("parameters", {})
    unknown = sorted(set(params) - set(definitions))
    if unknown:
        raise ManifestValidationError(
            "Unknown strategy parameters: " + ", ".join(unknown)
        )

    for name, value in params.items():
        validate_param_value(name, value, definitions[name])


def validate_param_value(name: str, value: Any, definition: Mapping[str, Any]) -> None:
    """Validate a single value against a manifest parameter definition."""

    parameter_type = definition["type"]
    if parameter_type == "int" and not isinstance(value, int):
        raise ManifestValidationError(f"Parameter '{name}' must be an integer.")
    if parameter_type == "float" and not isinstance(value, (int, float)):
        raise ManifestValidationError(f"Parameter '{name}' must be numeric.")
    if parameter_type == "bool" and not isinstance(value, bool):
        raise ManifestValidationError(f"Parameter '{name}' must be a boolean.")
    if parameter_type == "str" and not isinstance(value, str):
        raise ManifestValidationError(f"Parameter '{name}' must be a string.")
    if parameter_type == "enum" and value not in definition.get("options", []):
        raise ManifestValidationError(
            f"Parameter '{name}' must be one of: {definition.get('options', [])}."
        )

    minimum = definition.get("min")
    maximum = definition.get("max")
    if minimum is not None and value < minimum:
        raise ManifestValidationError(
            f"Parameter '{name}' must be greater than or equal to {minimum}."
        )
    if maximum is not None and value > maximum:
        raise ManifestValidationError(
            f"Parameter '{name}' must be less than or equal to {maximum}."
        )
