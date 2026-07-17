"""Command-line interface for gDMFT data bundles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .manifest import ManifestError, load_manifest, verify_artifacts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gdmft-data")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate a dataset bundle")
    validate.add_argument("manifest", type=Path)
    validate.add_argument(
        "--manifest-only",
        action="store_true",
        help="skip local artifact size and checksum verification",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        document = load_manifest(args.manifest)
        verified_files = 0
        if not args.manifest_only:
            verified_files = verify_artifacts(document, args.manifest.parent)
        remote_artifacts = sum("uri" in artifact for artifact in document["artifacts"])
    except ManifestError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "dataset_id": document["dataset_id"],
                "version": document["version"],
                "declared_data_stage": document["data_stage"],
                "release_status": document["release_status"],
                "artifacts": len(document["artifacts"]),
                "manifest_validation": "passed",
                "artifact_integrity": (
                    "skipped" if args.manifest_only else "local-passed"
                ),
                "local_artifacts_verified": verified_files,
                "remote_artifacts_unverified": remote_artifacts,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
