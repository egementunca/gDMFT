"""Extract per-point pole/bath parameters from the registered raw archives.

The scalar point tables carry no bath structure; the lossless raw archives
do. This module streams them once per build, joins each record to its
points.csv row by point id (asserting an exact 1:1 match), normalizes every
energy-like parameter by the raw half bandwidth, and reduces the
particle-hole-symmetric records to compact parameters:

  g-sector  (hybridization poles): v0 at eps = 0, v1 at +-eps1
  h-sector  (self-energy poles):   weight w at +-eta

Records that are not PH-symmetric (the v1 exotic families) fall back to
full normalized arrays. Lattice and gateway h-sectors are retained
separately; they are equal for most roots but can differ in legacy Mg=1
records. v1 rows without a bare h-sector use the canonical block's
bare-equivalent (eta_R, W_R) view and are flagged `h_from_R`.
"""

from __future__ import annotations

import gzip
import json
import tarfile
from pathlib import Path
from typing import Any

SYM_REL_TOL = 1e-8
SECTOR_REL_TOL = 2e-6


class PoleError(ValueError):
    """Raised when the raw archives disagree with the point table."""


def _arrays_close(left: list[float], right: list[float]) -> bool:
    if len(left) != len(right):
        return False
    return all(
        abs(a - b) <= SECTOR_REL_TOL * max(abs(a), abs(b), 1.0)
        for a, b in zip(left, right, strict=True)
    )


def _round6(value: float) -> float:
    return float(f"{value:.6g}") if value else value


def _central_and_pairs(
    energies: list[float], amplitudes: list[float]
) -> tuple[float | None, list[tuple[float, float]]] | None:
    """Split modes into (central amplitude, [(+energy, amplitude)]) when
    PH-symmetric; None when the record is asymmetric."""
    scale = max([abs(e) for e in energies] + [1.0])
    central: float | None = None
    positive: list[tuple[float, float]] = []
    negative: list[tuple[float, float]] = []
    for energy, amplitude in zip(energies, amplitudes, strict=True):
        if abs(energy) <= SYM_REL_TOL * scale:
            if central is not None:
                return None
            central = abs(amplitude)
        elif energy > 0:
            positive.append((energy, abs(amplitude)))
        else:
            negative.append((-energy, abs(amplitude)))
    if len(positive) != len(negative):
        return None
    positive.sort()
    negative.sort()
    for (ep, ap), (en, an) in zip(positive, negative, strict=True):
        if abs(ep - en) > SYM_REL_TOL * scale:
            return None
        if abs(ap - an) > SYM_REL_TOL * max(ap, an, 1.0):
            return None
    return central, positive


def _reduce_record(
    g_eps: list[float],
    g_v: list[float],
    h_eta: list[float] | None,
    h_w: list[float] | None,
    raw_d: float,
) -> dict[str, Any]:
    """Reduce one record; returns {red: {...}} or {full: {...}}."""
    g_eps_n = [e / raw_d for e in g_eps]
    g_v_n = [v / raw_d for v in g_v]
    h_eta_n = [e / raw_d for e in (h_eta or [])]
    h_w_n = [w / raw_d for w in (h_w or [])]

    g_split = _central_and_pairs(g_eps_n, g_v_n)
    h_split = (
        _central_and_pairs(h_eta_n, h_w_n) if h_eta is not None else (None, [])
    )
    symmetric = (
        g_split is not None
        and h_split is not None
        and len(g_split[1]) <= 1
        and len(h_split[1]) <= 1
        and (h_split[0] is None or h_split[0] == 0.0)
    )
    if symmetric:
        g_central, g_pairs = g_split
        _h_central, h_pairs = h_split
        return {
            "red": {
                "v0": _round6(g_central) if g_central is not None else None,
                "v1": _round6(g_pairs[0][1]) if g_pairs else None,
                "eps1": _round6(g_pairs[0][0]) if g_pairs else None,
                "w": _round6(h_pairs[0][1]) if h_pairs else None,
                "eta": _round6(h_pairs[0][0]) if h_pairs else None,
            }
        }
    return {
        "full": {
            "ge": [_round6(e) for e in g_eps_n],
            "gv": [_round6(v) for v in g_v_n],
            "he": [_round6(e) for e in h_eta_n] or None,
            "hw": [_round6(w) for w in h_w_n] or None,
        }
    }


def _record_poles(record: dict[str, Any], raw_d: float) -> dict[str, Any]:
    g_sector = record.get("g_sector") or {}
    g_eps = g_sector.get("eps_g")
    g_v = g_sector.get("V_g")
    if g_eps is None or g_v is None:
        raise PoleError("record without g_sector eps_g/V_g")
    bare = record.get("bare_h_sectors") or {}
    canonical = record.get("canonical_h_sectors") or {}
    h_eta = bare.get("eta_lattice")
    h_w = bare.get("W_lattice")
    gateway_eta = bare.get("eta_gateway")
    gateway_w = bare.get("W_gateway")
    h_from_r = False
    if h_eta is None or h_w is None:
        h_eta = canonical.get("eta_R")
        h_w = canonical.get("W_R")
        h_from_r = h_eta is not None
    if gateway_eta is None or gateway_w is None:
        gateway_eta = canonical.get("eta_R")
        gateway_w = canonical.get("W_R")
    if gateway_eta is None or gateway_w is None:
        gateway_eta = h_eta
        gateway_w = h_w
    result = _reduce_record(g_eps, g_v, h_eta, h_w, raw_d)
    gateway = _reduce_record(
        g_eps, g_v, gateway_eta, gateway_w, raw_d
    )
    if "red" in gateway:
        result["gateway_red"] = {
            "w": gateway["red"]["w"],
            "eta": gateway["red"]["eta"],
        }
    else:
        result["gateway_full"] = {
            "he": gateway["full"]["he"],
            "hw": gateway["full"]["hw"],
        }
    result["gateway_differs"] = not (
        _arrays_close(
            [float(value) for value in (gateway_eta or [])],
            [float(value) for value in (h_eta or [])],
        )
        and _arrays_close(
            [float(value) for value in (gateway_w or [])],
            [float(value) for value in (h_w or [])],
        )
    )
    result["h_from_R"] = h_from_r
    return result


def _iter_v1_records(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            yield record["identity"]["source_record_id"], record, float(
                record["model"]["D"]
            )


def _iter_v2_records(path: Path, cells: set[str]):
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if (
                not member.isfile()
                or len(parts) != 3
                or parts[0] != "raw_campaign"
                or parts[1] not in cells
                or not parts[2].endswith(".jsonl")
            ):
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                raise PoleError(f"cannot read archive member {member.name}")
            for line in extracted:
                if not line.strip():
                    continue
                record = json.loads(line)
                yield record["attempt_id"], record, float(record["D"])


def _iter_v2_jsonl_records(path: Path):
    """Fill-campaign lossless records: gzip JSONL of the v2 attempt schema
    (stage3_attempts promotion; same record shape as the tar members)."""
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("bare_h_sectors") is None and \
                    record.get("g_sector") is None:
                continue  # solver_failed record: no pole payload
            yield record["attempt_id"], record, float(record["D"])


def collect_pole_records(
    archive_path: Path,
    *,
    kind: str,
    cells: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """id -> reduced pole entry for one archive (duplicate ids rejected
    WITHIN an archive; merging across archives is the caller's job, keyed
    by campaign)."""
    if kind == "jsonl":
        iterator = _iter_v1_records(archive_path)
    elif kind == "tar":
        if not cells:
            raise PoleError("tar extraction needs the registered cell set")
        iterator = _iter_v2_records(archive_path, cells)
    elif kind == "v2-jsonl":
        iterator = _iter_v2_jsonl_records(archive_path)
    else:  # pragma: no cover - closed set
        raise PoleError(f"unknown archive kind {kind}")
    by_id: dict[str, dict[str, Any]] = {}
    for point_id, record, raw_d in iterator:
        if point_id in by_id:
            raise PoleError(f"duplicate point id {point_id} in {archive_path}")
        by_id[point_id] = _record_poles(record, raw_d)
    return by_id


def assemble_pole_table(
    point_ids: list[str],
    by_id: dict[str, dict[str, Any]],
    archive_label: str = "<merged archives>",
) -> dict[str, Any]:
    return _assemble(point_ids, by_id, archive_label)


def extract_pole_table(
    archive_path: Path,
    point_ids: list[str],
    *,
    kind: str,
    cells: set[str] | None = None,
) -> dict[str, Any]:
    """Build the payload pole table aligned to the point-id row order.

    kind: "jsonl" (v1 roots.jsonl.gz), "tar" (v2 raw_campaign.tar.gz, which
    needs the manifest's registered cell whitelist), or "v2-jsonl" (the
    fill-campaign lossless gzip JSONL).
    """
    by_id = collect_pole_records(archive_path, kind=kind, cells=cells)
    return _assemble(point_ids, by_id, str(archive_path))


def _assemble(
    point_ids: list[str],
    by_id: dict[str, dict[str, Any]],
    archive_path: str,
) -> dict[str, Any]:
    missing = [pid for pid in point_ids if pid not in by_id]
    if missing:
        raise PoleError(
            f"{archive_path}: {len(missing)} point ids have no raw record "
            f"(first: {missing[:3]})"
        )
    if len(by_id) != len(point_ids):
        raise PoleError(
            f"{archive_path}: {len(by_id)} raw records vs "
            f"{len(point_ids)} point rows"
        )

    red = {"v0": [], "v1": [], "eps1": [], "w": [], "eta": []}
    full: dict[str, dict[str, Any]] = {}
    gateway_red = {"w": [], "eta": []}
    gateway_full: dict[str, dict[str, Any]] = {}
    gateway_differs: list[int] = []
    h_from_r: list[int] = []
    full_rows = 0
    for row_index, point_id in enumerate(point_ids):
        entry = by_id[point_id]
        if entry["h_from_R"]:
            h_from_r.append(row_index)
        if entry["gateway_differs"]:
            gateway_differs.append(row_index)
        if "red" in entry:
            for key in red:
                red[key].append(entry["red"][key])
        else:
            for key in red:
                red[key].append(None)
            full[str(row_index)] = entry["full"]
            full_rows += 1
        if "gateway_red" in entry:
            for key in gateway_red:
                gateway_red[key].append(entry["gateway_red"][key])
        else:
            for key in gateway_red:
                gateway_red[key].append(None)
            gateway_full[str(row_index)] = entry["gateway_full"]
    return {
        "red": red,
        "full": full,
        "gateway_red": gateway_red,
        "gateway_full": gateway_full,
        "gateway_differs": gateway_differs,
        "h_from_R": h_from_r,
        "counts": {
            "rows": len(point_ids),
            "reduced": len(point_ids) - full_rows,
            "full": full_rows,
            "h_from_R": len(h_from_r),
            "gateway_differs": len(gateway_differs),
        },
    }
