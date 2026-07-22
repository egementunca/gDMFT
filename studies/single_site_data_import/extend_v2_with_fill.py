#!/usr/bin/env python3
"""Extend single-site.scan-matrix-v2 with the 20260721 fill campaign.

The superseding revision of the SAME dataset id (user directive: one source
of truth, no new dataset): the existing 15,240 D09 rows stay untouched and
the canonical-grid fill campaign (Stage-3 promotion, dmft worktree
deliverable 09/fill_20260721, preservation commit pinned below) is appended
as additional rows with run_id "d09-fill-20260721:<cell>".

Every evidence route is imported as rows of fact — bare, exact conversion,
R-reoptimized refit, R-native — with the source campaign, seed provenance,
and category preserved. No gauge or branch is selected; selection stays a
separate analysis layer.

Reads the two inputs as Git blobs at the pinned commit (same audit property
as the original importer). Idempotent: re-running after the SCC square rows
land regenerates the same dataset with more rows.

Usage:
  python3 studies/single_site_data_import/extend_v2_with_fill.py \
    --source-worktree /Users/egementunca/dmft/worktrees/paper-consolidation \
    --fill-commit <sha>
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import import_snapshot as base  # noqa: E402

DATASET = Path("data/datasets/single-site-scan-matrix-v2")
FILL_PREFIX = "d09-fill-20260721"
DELIVER = "results/deliverables/09_single_site_publication_validation/fill_20260721"
NEW_CELLS = ("bethe_mg3_bare",)


def git_blob(worktree: Path, revision: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(worktree), "show", f"{revision}:{path}"]
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-worktree", type=Path, required=True)
    ap.add_argument("--fill-commit", required=True)
    args = ap.parse_args()

    revision = subprocess.check_output(
        ["git", "-C", str(args.source_worktree), "rev-parse", args.fill_commit],
        text=True).strip()

    scalar_bytes = git_blob(args.source_worktree, revision,
                            f"{DELIVER}/stage3_scalar_projection.csv")
    attempts_gz = git_blob(args.source_worktree, revision,
                           f"{DELIVER}/stage3_attempts.jsonl.gz")

    # ---- raw records keyed by attempt id (v2 attempt schema) --------------
    raw_records: dict[str, dict] = {}
    with gzip.open(io.BytesIO(attempts_gz), "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record["attempt_id"] in raw_records:
                raise SystemExit(
                    f"duplicate fill attempt_id {record['attempt_id']}")
            raw_records[record["attempt_id"]] = record

    # ---- provenance copies inside the dataset -----------------------------
    prov_dir = DATASET / "provenance"
    scalar_path = prov_dir / "fill_20260721_scalar_projection.csv"
    scalar_path.write_bytes(scalar_bytes)
    raw_path = DATASET / "raw" / "fill_attempts_20260721.jsonl.gz"
    raw_path.write_bytes(attempts_gz)

    # ---- fill point rows via the SAME adapter as the original import ------
    fill_rows = []
    seen_cells = set()
    for row in base.d09_point_rows(scalar_path, dict(raw_records)):
        cell = row["source_cell"]
        seen_cells.add(cell)
        row["run_id"] = f"{FILL_PREFIX}:{cell}"
        fill_rows.append(row)

    # ---- merged points.csv ------------------------------------------------
    existing = DATASET / "points.csv"
    with existing.open(newline="", encoding="utf-8") as stream:
        old_rows = list(csv.DictReader(stream))
    n_old = len(old_rows)
    merged = old_rows + fill_rows
    n_total = base.write_points(existing, merged)
    print(f"points.csv: {n_old} existing + {len(fill_rows)} fill "
          f"= {n_total} rows; fill cells: {sorted(seen_cells)}")

    # ---- manifest: version bump, cells, artifacts -------------------------
    manifest_path = DATASET / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["version"] = "0.2.0"
    cells = set(manifest["grid"]["cells"]) | seen_cells | set(NEW_CELLS)
    manifest["grid"]["cells"] = sorted(cells)
    manifest["description"] = (
        manifest["description"].rstrip()
        + " Superseding revision 0.2.0 appends the 20260721 canonical-grid "
          "fill campaign (run_id prefix d09-fill-20260721; unified 17-row "
          "T-ladder on both lattices, 0.05 U-grid with 0.01 coexistence "
          "windows, new bethe_mg3_bare cell carrying bare + exact-R + "
          "R-reoptimized evidence per root, protected R-native chains).")
    ext = manifest.setdefault("extensions", {})
    ext["fill_20260721"] = {
        "source_repository": str(args.source_worktree),
        "source_revision": revision,
        "source_paths": [
            f"{DELIVER}/stage3_scalar_projection.csv",
            f"{DELIVER}/stage3_attempts.jsonl.gz",
        ],
        "run_id_prefix": FILL_PREFIX,
        "note": ("square_mg3 partial until the SCC job completes; "
                 "square_mg3_Rnative pending. Re-run "
                 "extend_v2_with_fill.py after each promotion pass."),
        "imported_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"),
    }

    def sha256_file(path: Path) -> tuple[str, int]:
        h = hashlib.sha256()
        n = 0
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
                n += len(chunk)
        return h.hexdigest(), n

    by_path = {a["path"]: a for a in manifest["artifacts"]}
    digest, size = sha256_file(existing)
    by_path["points.csv"].update(sha256=digest, bytes=size, rows=n_total)
    for path, role, media in (
        (scalar_path, "fill-campaign-scalar-projection", "text/csv"),
        (raw_path, "lossless-raw-archive", "application/gzip"),
    ):
        rel = str(path.relative_to(DATASET))
        digest, size = sha256_file(path)
        entry = by_path.get(rel) or {}
        entry.update(
            artifact_id=rel.replace("/", "."), path=rel, role=role,
            media_type=media, sha256=digest, bytes=size)
        if rel not in by_path:
            manifest["artifacts"].append(entry)
            by_path[rel] = entry
    manifest["artifacts"].sort(key=lambda a: a["path"])
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n")
    print(f"manifest: version 0.2.0, {len(manifest['artifacts'])} artifacts, "
          f"cells={len(manifest['grid']['cells'])}")

    # ---- README note ------------------------------------------------------
    readme = DATASET / "README.md"
    text = readme.read_text()
    marker = "## Superseding revision 0.2.0"
    if marker not in text:
        readme.write_text(text.rstrip() + f"""

{marker} (fill campaign 20260721)

Appends the canonical-grid fill campaign as rows with run_id prefix
`{FILL_PREFIX}` (source: dmft worktree deliverable 09/fill_20260721 at
commit `{revision[:12]}`): the unified 17-row T-ladder on BOTH lattices,
uniform 0.05 U-grid plus 0.01 coexistence windows, and the previously
missing `bethe_mg3_bare` cell — every bare root accompanied by its exact
canonical-R conversion and its R-reoptimized refit; R-native chains grown
from bare roots (seed provenance recorded). All evidence routes are rows
of fact; nothing is selected. Raw lossless records:
`raw/fill_attempts_20260721.jsonl.gz`. square_mg3 rows are partial until
the SCC pass completes; the import is idempotent and re-run per pass.
""")
        print("README: superseding note appended")


if __name__ == "__main__":
    main()
