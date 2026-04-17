"""Automatic manifest-driven strategy registry."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from shared.base_strategy import BaseStrategy
from shared.manifest_schema import ManifestValidationError, validate_manifest
from shared.params import get_default_params, validate_params_against_manifest


class RegistryError(RuntimeError):
    """Raised when strategy discovery or instantiation fails."""


class StrategyRegistry:
    """Discover and instantiate strategies declared under ``strategies/**``."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parent.parent)
        self.strategies_root = self.root / "strategies"
        self._manifests: dict[str, dict[str, Any]] = {}
        self._classes: dict[str, type[BaseStrategy]] = {}

    def discover(self) -> None:
        """Load and validate all strategy manifests and strategy classes."""

        self._manifests.clear()
        self._classes.clear()

        if not self.strategies_root.exists():
            return

        for manifest_path in sorted(self.strategies_root.rglob("manifest.json")):
            manifest = self._load_manifest(manifest_path)
            slug = manifest["slug"]
            if slug in self._manifests:
                raise RegistryError(f"Duplicate strategy slug detected: '{slug}'.")
            self._manifests[slug] = manifest
            self._classes[slug] = self._load_strategy_class(manifest_path, manifest)

    def list_strategies(self) -> list[dict[str, Any]]:
        """Return lightweight metadata for all discovered strategies."""

        self._ensure_discovered()
        return [
            {
                "slug": manifest["slug"],
                "name": manifest["name"],
                "category": manifest["category"],
                "version": manifest["version"],
                "direction": manifest["direction"],
            }
            for manifest in self._manifests.values()
        ]

    def get_strategy_class(self, slug: str) -> type[BaseStrategy]:
        """Return the strategy class registered for the given slug."""

        self._ensure_discovered()
        try:
            return self._classes[slug]
        except KeyError as exc:
            raise RegistryError(f"Strategy '{slug}' is not registered.") from exc

    def get_manifest(self, slug: str) -> dict[str, Any]:
        """Return the validated manifest for the given slug."""

        self._ensure_discovered()
        try:
            return self._manifests[slug]
        except KeyError as exc:
            raise RegistryError(f"Strategy manifest '{slug}' was not found.") from exc

    def create(self, slug: str, params: dict[str, Any] | None = None) -> BaseStrategy:
        """Instantiate a strategy using manifest defaults plus explicit params."""

        manifest = self.get_manifest(slug)
        strategy_class = self.get_strategy_class(slug)
        merged_params = get_default_params(manifest)
        if params:
            merged_params.update(params)
        validate_params_against_manifest(merged_params, manifest)
        return strategy_class(params=merged_params)

    def smoke_test_imports(self) -> None:
        """Ensure all discovered strategy modules are importable."""

        self._ensure_discovered()
        for slug in self._classes:
            self.get_strategy_class(slug)

    def _ensure_discovered(self) -> None:
        if not self._manifests:
            self.discover()

    def _load_manifest(self, manifest_path: Path) -> dict[str, Any]:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RegistryError(f"Invalid JSON in manifest '{manifest_path}'.") from exc

        try:
            return validate_manifest(manifest)
        except ManifestValidationError as exc:
            raise RegistryError(f"Invalid manifest '{manifest_path}': {exc}") from exc

    def _load_strategy_class(
        self, manifest_path: Path, manifest: dict[str, Any]
    ) -> type[BaseStrategy]:
        strategy_path = manifest_path.with_name("strategy.py")
        if not strategy_path.exists():
            raise RegistryError(
                f"Strategy module '{strategy_path}' referenced by slug "
                f"'{manifest['slug']}' does not exist."
            )

        module_name = ".".join(strategy_path.relative_to(self.root).with_suffix("").parts)
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            spec = importlib.util.spec_from_file_location(module_name, strategy_path)
            if spec is None or spec.loader is None:
                raise RegistryError(f"Could not create import spec for '{strategy_path}'.")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        class_name = manifest["class_name"]
        strategy_class = getattr(module, class_name, None)
        if strategy_class is None:
            raise RegistryError(
                f"Strategy class '{class_name}' was not found in '{strategy_path}'."
            )
        if not issubclass(strategy_class, BaseStrategy):
            raise RegistryError(
                f"Strategy class '{class_name}' in '{strategy_path}' must inherit BaseStrategy."
            )
        return strategy_class
