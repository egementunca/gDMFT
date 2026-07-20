"""Build the self-contained atlas HTML from registered datasets."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from importlib import metadata, resources
from pathlib import Path
from typing import Any

from .payload import build_payload, encode_payload
from .registry import find_registry

# Concatenation order matters: later modules may use earlier ones. Tab
# modules register themselves with app.js and may appear in any order after
# it. A public build is an all-or-nothing artifact: silently omitting a tab
# would produce a valid-looking but incomplete explorer.
WEB_MODULES = (
    "boot.js",
    "store.js",
    "plot.js",
    "semianalytics.js",
    "spectra.js",
    "app.js",
    "tabs/overview.js",
    "tabs/atlas.js",
    "tabs/series.js",
    "tabs/bench.js",
    "tabs/references.js",
    "tabs/branches.js",
    "tabs/gauge.js",
    "tabs/qa.js",
    "tabs/tables.js",
    "tabs/inspect.js",
)
REQUIRED_MODULES = set(WEB_MODULES)


def _web_root():
    return resources.files("gdmft.atlas").joinpath("web")


def _read_web(name: str) -> str | None:
    resource = _web_root().joinpath(name)
    if not resource.is_file():
        return None
    return resource.read_text(encoding="utf-8")


def _gdmft_version() -> str:
    try:
        return metadata.version("gdmft")
    except metadata.PackageNotFoundError:
        return "unknown"


def _build_time() -> str:
    """Return a reproducible UTC build time when SOURCE_DATE_EPOCH is set."""
    source_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_epoch is None:
        instant = datetime.datetime.now(datetime.timezone.utc)
    else:
        try:
            instant = datetime.datetime.fromtimestamp(
                int(source_epoch), tz=datetime.timezone.utc
            )
        except ValueError as exc:
            raise ValueError(
                "SOURCE_DATE_EPOCH must be an integer Unix timestamp"
            ) from exc
    return instant.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assemble_html(payload_blob: str, *, compressed: bool) -> str:
    """Inline style, payload, and script modules into one document."""
    index = _read_web("index.html")
    style = _read_web("style.css") or ""
    if index is None:
        raise FileNotFoundError("gdmft.atlas web/index.html is missing")

    scripts: list[str] = []
    for name in WEB_MODULES:
        content = _read_web(name)
        if content is None:
            if name in REQUIRED_MODULES:
                raise FileNotFoundError(f"gdmft.atlas web/{name} is missing")
            continue
        scripts.append(f"// ---- {name} ----\n{content}")
    script_bundle = "\n".join(scripts)

    encoding = "gzip-base64" if compressed else "base64-json"
    html = index.replace("__STYLE__", style)
    html = html.replace("__PAYLOAD_ENCODING__", encoding)
    html = html.replace("__PAYLOAD__", payload_blob)
    html = html.replace("__SCRIPTS__", script_bundle)
    return html


def build_atlas(
    *,
    registry: Path | None = None,
    output: Path | None = None,
    compress: bool = True,
    verify: bool = False,
    stamped: bool = False,
) -> tuple[Path, dict[str, Any]]:
    """Build the atlas HTML; returns (output path, size stats)."""
    registry_path = registry or find_registry(Path.cwd())
    built_at = _build_time()
    payload = build_payload(
        registry_path,
        verify=verify,
        built_at=built_at,
        gdmft_version=_gdmft_version(),
    )
    if not compress:
        import base64

        raw = json.dumps(
            payload, separators=(",", ":"), sort_keys=True, allow_nan=False
        )
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        blob = "\n".join(
            encoded[i : i + 120] for i in range(0, len(encoded), 120)
        )
        stats = {
            "raw_json_bytes": len(raw.encode("utf-8")),
            "embedded_bytes": len(blob),
        }
    else:
        blob, stats = encode_payload(payload, compress=True)

    html = assemble_html(blob, compressed=compress)

    if output is None:
        repo_root = registry_path.parent.parent
        if stamped:
            stamp = built_at.replace(":", "").replace("-", "")
            output = repo_root / "runs/atlas" / f"gdmft_atlas_{stamp}.html"
        else:
            # stable path, overwritten in place — reload the browser tab;
            # the build time is in the page masthead
            output = repo_root / "runs/atlas/gdmft_atlas.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    stats["html_bytes"] = len(html.encode("utf-8"))
    stats["datasets"] = {
        dataset_id: dataset["n"]
        for dataset_id, dataset in payload["datasets"].items()
    }
    if "gem" in payload["references"]:
        stats["gem_rows"] = payload["references"]["gem"]["n"]
    return output, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gdmft-atlas")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser(
        "build", help="build the self-contained atlas HTML"
    )
    build.add_argument("--registry", type=Path, default=None)
    build.add_argument("--output", type=Path, default=None)
    build.add_argument(
        "--verify",
        action="store_true",
        help="verify every artifact checksum before building",
    )
    build.add_argument(
        "--no-compress",
        action="store_true",
        help="embed plain base64 JSON (no DecompressionStream needed)",
    )
    build.add_argument(
        "--stats", action="store_true", help="print size statistics"
    )
    build.add_argument(
        "--stamped",
        action="store_true",
        help="write a timestamped copy instead of overwriting the stable "
        "runs/atlas/gdmft_atlas.html",
    )
    args = parser.parse_args(argv)

    try:
        output, stats = build_atlas(
            registry=args.registry,
            output=args.output,
            compress=not args.no_compress,
            verify=args.verify,
            stamped=args.stamped,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result: dict[str, Any] = {"output": str(output)}
    if args.stats:
        result["stats"] = stats
    else:
        result["html_bytes"] = stats["html_bytes"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
