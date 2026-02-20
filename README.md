# Hotspot Analysis Studio

You are right to ask where the files go.

This repo is a command-line workflow for ArcGIS-Pro-style hotspot analysis (Getis-Ord Gi*) and polygon joins (e.g., block groups).

## Why you may not see code on GitHub yet

If GitHub still shows only `.gitkeep`, your local commits were not pushed to the repo's `main` branch yet.
Use the **Publish to GitHub** section below to push this code.

## Exactly where to put your CSV

Put your point CSV here:

- `data/input/points.csv`

Expected columns (or pass your own names):

- `id`
- `latitude`
- `longitude`
- `value`

A folder structure is already included:

- `data/input/` → your uploaded CSVs
- `data/output/` → generated results

## Quick start (your real data)

Run hotspot analysis:

```bash
python hotspot_analysis.py hotspot \
  --input-csv data/input/points.csv \
  --output-csv data/output/hotspot_results.csv \
  --id-col id \
  --lat-col latitude \
  --lon-col longitude \
  --value-col value \
  --k-neighbors 8
```

Join hotspot points to block groups (GeoJSON):

```bash
python hotspot_analysis.py join \
  --points-csv data/output/hotspot_results.csv \
  --polygons-geojson data/input/blockgroups.geojson \
  --polygon-id-col GEOID \
  --lat-col latitude \
  --lon-col longitude \
  --output-points-csv data/output/hotspots_with_blockgroup.csv \
  --output-polygon-summary-csv data/output/blockgroup_hotspot_summary.csv
```

## Output files you will use in GIS

- `data/output/hotspots_with_blockgroup.csv`
- `data/output/blockgroup_hotspot_summary.csv`

In ArcGIS Pro/QGIS, join `blockgroup_hotspot_summary.csv` back to your block group polygons using `GEOID`.

## Publish to GitHub (so you can actually see files in your repo)

If your screenshot still shows an empty repo, run:

```bash
git remote add origin https://github.com/<your-username>/hotspot-analysis-studio.git
# if origin already exists, skip the previous command

git checkout main
git merge --ff-only work
git push -u origin main
```

If GitHub asks for authentication, use your PAT/token or GitHub CLI.

## Example data included

- `examples/sample_points.csv`
- `examples/sample_blockgroups.geojson`

You can test the workflow immediately with those sample files.
