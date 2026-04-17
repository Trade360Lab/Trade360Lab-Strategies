from __future__ import annotations

import pytest

from shared.manifest_schema import ManifestValidationError, validate_manifest


def test_validate_manifest_accepts_valid_payload():
    manifest = {
        "slug": "sample",
        "name": "Sample Strategy",
        "category": "trend",
        "version": "1.0.0",
        "description": "Sample description",
        "direction": ["long"],
        "class_name": "SampleStrategy",
        "timeframes": ["1h"],
        "symbols": ["BTCUSDT"],
        "required_columns": ["open", "high", "low", "close", "volume"],
        "outputs": ["entry_long", "entry_short", "exit_long", "exit_short"],
        "parameters": {
            "length": {
                "type": "int",
                "default": 20,
                "min": 1,
                "max": 200,
                "step": 1,
                "optimize": True,
                "description": "Window length",
            }
        },
    }

    validated = validate_manifest(manifest)

    assert validated["slug"] == "sample"


def test_validate_manifest_rejects_missing_required_fields():
    with pytest.raises(ManifestValidationError, match="missing required fields"):
        validate_manifest({"slug": "broken"})

