"""Dataset registry access for the atlas build."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REGISTRY_SCHEMA = "gdmft.registry.v1"


@dataclass(frozen=True)
class RegistryEntry:
    """One registered dataset: identity plus its manifest location."""

    id: str
    version: str
    manifest: Path
    data_stage: str
    release_status: str


def _parse_registry_text(text: str) -> tuple[str, list[dict[str, str]]]:
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10
        return _parse_registry_fallback(text)
    document = tomllib.loads(text)
    return document.get("schema_version", ""), document.get("dataset", [])


def _parse_registry_fallback(text: str) -> tuple[str, list[dict[str, str]]]:
    """Minimal parser for the registry's flat string-only TOML subset."""
    schema_version = ""
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[dataset]]":
            current = {}
            entries.append(current)
            continue
        match = re.fullmatch(r'([A-Za-z0-9_]+)\s*=\s*"([^"]*)"', line)
        if match is None:
            raise ValueError(f"unsupported registry line: {raw_line!r}")
        key, value = match.groups()
        if current is None:
            if key == "schema_version":
                schema_version = value
            continue
        current[key] = value
    return schema_version, entries


def load_registry(path: str | Path) -> list[RegistryEntry]:
    """Load and sanity-check data/registry.toml."""
    registry_path = Path(path)
    schema_version, raw_entries = _parse_registry_text(
        registry_path.read_text(encoding="utf-8")
    )
    if schema_version != REGISTRY_SCHEMA:
        raise ValueError(
            f"unsupported registry schema {schema_version!r} in {registry_path}"
        )
    root = registry_path.parent.parent
    entries: list[RegistryEntry] = []
    seen: set[str] = set()
    for raw in raw_entries:
        missing = {
            "id",
            "version",
            "manifest",
            "data_stage",
            "release_status",
        } - set(raw)
        if missing:
            raise ValueError(
                f"registry entry {raw.get('id', '?')!r} is missing "
                f"{sorted(missing)}"
            )
        if raw["id"] in seen:
            raise ValueError(f"duplicate registry id {raw['id']!r}")
        seen.add(raw["id"])
        entries.append(
            RegistryEntry(
                id=raw["id"],
                version=raw["version"],
                manifest=root / raw["manifest"],
                data_stage=raw["data_stage"],
                release_status=raw["release_status"],
            )
        )
    return entries


def find_registry(start: str | Path) -> Path:
    """Walk up from `start` to the repository's data/registry.toml."""
    current = Path(start).resolve()
    for candidate in (current, *current.parents):
        registry = candidate / "data/registry.toml"
        if registry.is_file():
            return registry
    raise FileNotFoundError(
        f"no data/registry.toml found above {current}; pass --registry"
    )
