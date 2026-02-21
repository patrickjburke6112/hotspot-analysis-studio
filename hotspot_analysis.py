#!/usr/bin/env python3
"""Hotspot analysis workflow inspired by ArcGIS Pro optimized hotspot analysis.

This implementation intentionally avoids third-party dependencies so it can run in
minimal environments. It supports:
1) CSV point hotspot analysis via Getis-Ord Gi*.
2) Joining hotspot points to GeoJSON polygons (e.g., block groups).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _validate_columns(rows: list[dict[str, str]], required: list[str]) -> None:
    if not rows:
        raise ValueError("Input CSV is empty")
    cols = set(rows[0].keys())
    missing = [c for c in required if c not in cols]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals)


def _sample_std(vals: list[float]) -> float:
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _normal_sf(abs_z: float) -> float:
    # survival function for standard normal
    return 0.5 * math.erfc(abs_z / math.sqrt(2))


def classify_significance(z_score: float, p_value: float) -> str:
    if p_value <= 0.01:
        return "Hot Spot 99%" if z_score > 0 else "Cold Spot 99%"
    if p_value <= 0.05:
        return "Hot Spot 95%" if z_score > 0 else "Cold Spot 95%"
    if p_value <= 0.10:
        return "Hot Spot 90%" if z_score > 0 else "Cold Spot 90%"
    return "Not Significant"


def compute_gi_star_rows(
    rows: list[dict[str, str]],
    *,
    id_col: str,
    lat_col: str,
    lon_col: str,
    value_col: str,
    k_neighbors: int,
) -> list[dict[str, Any]]:
    _validate_columns(rows, [id_col, lat_col, lon_col, value_col])
    if k_neighbors < 1:
        raise ValueError("k_neighbors must be >= 1")
    if len(rows) < 3:
        raise ValueError("At least 3 points are required")

    points: list[tuple[float, float, float]] = []
    for r in rows:
        points.append((float(r[lat_col]), float(r[lon_col]), float(r[value_col])))

    n = len(points)
    values = [v for _, _, v in points]
    xbar = _mean(values)
    s = _sample_std(values)
    if s == 0:
        raise ValueError("Input value column has no variance")

    out: list[dict[str, Any]] = []
    for i, (lat_i, lon_i, _) in enumerate(points):
        dists = []
        for j, (lat_j, lon_j, _) in enumerate(points):
            dists.append((j, _haversine_km(lat_i, lon_i, lat_j, lon_j)))
        dists.sort(key=lambda x: x[1])

        k = min(k_neighbors + 1, n)
        neighbor_ids = {idx for idx, _ in dists[:k]}

        wij_sum = float(len(neighbor_ids))
        wij_sq_sum = wij_sum
        weighted_x_sum = sum(values[j] for j in neighbor_ids)

        denom_term = ((n * wij_sq_sum) - (wij_sum ** 2)) / (n - 1)
        denominator = s * math.sqrt(denom_term)
        if denominator == 0:
            raise ValueError("Encountered zero denominator in Gi* computation")

        z = (weighted_x_sum - (xbar * wij_sum)) / denominator
        p = 2 * _normal_sf(abs(z))

        row = dict(rows[i])
        row["gi_star_zscore"] = f"{z:.6f}"
        row["gi_star_pvalue"] = f"{p:.6f}"
        row["gi_bin"] = classify_significance(z, p)
        out.append(row)
    return out


def _point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1):
            inside = not inside
    return inside


def _point_in_polygon(point: tuple[float, float], polygon_coords: list[list[list[float]]]) -> bool:
    # GeoJSON polygon: [outer_ring, hole1, ...]
    if not _point_in_ring(point, polygon_coords[0]):
        return False
    for hole in polygon_coords[1:]:
        if _point_in_ring(point, hole):
            return False
    return True


def _point_in_geometry(point: tuple[float, float], geometry: dict[str, Any]) -> bool:
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    if gtype == "Polygon":
        return _point_in_polygon(point, coords)
    if gtype == "MultiPolygon":
        return any(_point_in_polygon(point, poly) for poly in coords)
    return False


def join_points_to_geojson(
    point_rows: list[dict[str, Any]],
    geojson_path: Path,
    polygon_id_col: str,
    lat_col: str,
    lon_col: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with geojson_path.open("r", encoding="utf-8") as f:
        gj = json.load(f)

    features = gj.get("features", [])
    joined_rows: list[dict[str, Any]] = []

    for row in point_rows:
        point = (float(row[lon_col]), float(row[lat_col]))
        matched_id = ""
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            if polygon_id_col not in props:
                continue
            if _point_in_geometry(point, geom):
                matched_id = str(props[polygon_id_col])
                break
        enriched = dict(row)
        enriched[polygon_id_col] = matched_id
        joined_rows.append(enriched)

    summary_map: dict[str, dict[str, Any]] = {}
    for row in joined_rows:
        pid = row[polygon_id_col]
        if pid not in summary_map:
            summary_map[pid] = {
                polygon_id_col: pid,
                "point_count": 0,
                "hotspot_99": 0,
                "hotspot_95": 0,
                "hotspot_90": 0,
                "coldspot_99": 0,
                "coldspot_95": 0,
                "coldspot_90": 0,
                "zscore_sum": 0.0,
                "min_pvalue": 1.0,
            }
        s = summary_map[pid]
        s["point_count"] += 1
        z = float(row["gi_star_zscore"])
        p = float(row["gi_star_pvalue"])
        s["zscore_sum"] += z
        s["min_pvalue"] = min(s["min_pvalue"], p)

        label = row["gi_bin"]
        if label == "Hot Spot 99%":
            s["hotspot_99"] += 1
        elif label == "Hot Spot 95%":
            s["hotspot_95"] += 1
        elif label == "Hot Spot 90%":
            s["hotspot_90"] += 1
        elif label == "Cold Spot 99%":
            s["coldspot_99"] += 1
        elif label == "Cold Spot 95%":
            s["coldspot_95"] += 1
        elif label == "Cold Spot 90%":
            s["coldspot_90"] += 1

    summary_rows = []
    for pid, s in summary_map.items():
        count = s["point_count"]
        summary_rows.append(
            {
                polygon_id_col: pid,
                "point_count": count,
                "hotspot_99": s["hotspot_99"],
                "hotspot_95": s["hotspot_95"],
                "hotspot_90": s["hotspot_90"],
                "coldspot_99": s["coldspot_99"],
                "coldspot_95": s["coldspot_95"],
                "coldspot_90": s["coldspot_90"],
                "mean_zscore": f"{(s['zscore_sum'] / count):.6f}" if count else "",
                "min_pvalue": f"{s['min_pvalue']:.6f}" if count else "",
            }
        )

    return joined_rows, summary_rows


def run_hotspot_command(args: argparse.Namespace) -> None:
    rows = _read_csv(Path(args.input_csv))
    output = compute_gi_star_rows(
        rows,
        id_col=args.id_col,
        lat_col=args.lat_col,
        lon_col=args.lon_col,
        value_col=args.value_col,
        k_neighbors=args.k_neighbors,
    )
    fieldnames = list(output[0].keys())
    _write_csv(Path(args.output_csv), output, fieldnames)
    print(f"Wrote hotspot output: {args.output_csv}")


def run_join_command(args: argparse.Namespace) -> None:
    point_rows = _read_csv(Path(args.points_csv))
    joined, summary = join_points_to_geojson(
        point_rows,
        geojson_path=Path(args.polygons_geojson),
        polygon_id_col=args.polygon_id_col,
        lat_col=args.lat_col,
        lon_col=args.lon_col,
    )

    _write_csv(Path(args.output_points_csv), joined, list(joined[0].keys()))
    _write_csv(Path(args.output_polygon_summary_csv), summary, list(summary[0].keys()))

    print(f"Wrote joined points output: {args.output_points_csv}")
    print(f"Wrote polygon summary output: {args.output_polygon_summary_csv}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optimized hotspot analysis workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    hotspot = subparsers.add_parser("hotspot", help="Run Gi* hotspot analysis on a point CSV")
    hotspot.add_argument("--input-csv", required=True)
    hotspot.add_argument("--output-csv", required=True)
    hotspot.add_argument("--id-col", default="id")
    hotspot.add_argument("--lat-col", default="latitude")
    hotspot.add_argument("--lon-col", default="longitude")
    hotspot.add_argument("--value-col", default="value")
    hotspot.add_argument("--k-neighbors", type=int, default=8)
    hotspot.set_defaults(func=run_hotspot_command)

    join = subparsers.add_parser("join", help="Join hotspot results to GeoJSON polygons")
    join.add_argument("--points-csv", required=True)
    join.add_argument("--polygons-geojson", required=True)
    join.add_argument("--polygon-id-col", required=True)
    join.add_argument("--lat-col", default="latitude")
    join.add_argument("--lon-col", default="longitude")
    join.add_argument("--output-points-csv", required=True)
    join.add_argument("--output-polygon-summary-csv", required=True)
    join.set_defaults(func=run_join_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
