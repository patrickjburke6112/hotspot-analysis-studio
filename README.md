# Hotspot Analysis Studio

This repository now provides **two ways** to run the analysis:

1. Python CLI (`hotspot_analysis.py`)
2. Installable **R package** (`hotspotstudio`) for RStudio workflows

---

## Where your software is

Your software is the source code in this GitHub repository.
After cloning/downloading the repo, you can either:

- run Python commands directly, or
- install the R package from GitHub and run functions inside RStudio.

---

## RStudio package install and usage (recommended for you)

### 1) Install package from GitHub

In RStudio Console:

```r
install.packages(c("remotes", "sf"))
remotes::install_github("patrickjburke6112/hotspot-analysis-studio", ref = "main", build_vignettes = FALSE)
```

If `install_github()` returns HTTP 404 in RStudio, use this exact fallback sequence:

```r
# 1) Authenticate GitHub API requests in R (fixes private-repo/permission 404s)
install.packages(c("gitcreds", "gh"))
gitcreds::gitcreds_set()
gh::gh_whoami()

# 2) Retry install from GitHub
remotes::install_github("patrickjburke6112/hotspot-analysis-studio", ref = "main", build_vignettes = FALSE)
```

If you still get 404, install from a local clone (bypasses GitHub API entirely):

```r
# In terminal (or Git Bash), clone then open RStudio in that folder
# git clone https://github.com/patrickjburke6112/hotspot-analysis-studio.git

# In RStudio, run from the cloned repo root:
remotes::install_local(".", build_vignettes = FALSE, upgrade = "never")
```

If `install_url(main.zip)` says "no DESCRIPTION", that usually means GitHub returned a non-package page (auth/permissions/proxy) instead of the zip archive.

After install, verify package load:

```r
library(hotspotstudio)
packageVersion("hotspotstudio")
```

### 2) Prepare your point data in R

Your table needs at least these columns:

- `id`
- `latitude`
- `longitude`
- `value`

Example:

```r
library(hotspotstudio)

points <- read.csv("data/input/points.csv")
hotspots <- compute_gi_star(
  points_df = points,
  id_col = "id",
  lat_col = "latitude",
  lon_col = "longitude",
  value_col = "value",
  k_neighbors = 8
)

write.csv(hotspots, "data/output/hotspot_results.csv", row.names = FALSE)
```

### 3) Join hotspot results to block groups in R

```r
joined <- join_hotspots_to_polygons(
  hotspot_df = hotspots,
  polygons_path = "data/input/blockgroups.geojson",
  polygon_id_col = "GEOID",
  lat_col = "latitude",
  lon_col = "longitude"
)

write.csv(joined$points_joined, "data/output/hotspots_with_blockgroup.csv", row.names = FALSE)
write.csv(joined$polygon_summary, "data/output/blockgroup_hotspot_summary.csv", row.names = FALSE)
```

You can then load `blockgroup_hotspot_summary.csv` into ArcGIS Pro and join on `GEOID`.

---

## Folder locations

- `data/input/` → where you place your raw CSV/GeoJSON files
- `data/output/` → generated outputs

Suggested file names:

- `data/input/points.csv`
- `data/input/blockgroups.geojson`

---

## Python CLI usage (still available)

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

Join to polygons:

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

---

## Example files in repo

- `examples/sample_points.csv`
- `examples/sample_blockgroups.geojson`

