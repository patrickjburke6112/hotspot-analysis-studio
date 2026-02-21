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

### Before running install in RStudio (important GitHub step)

If I just pushed a fix in a PR branch, you must get that code into `main` first:

1. Open the PR on GitHub.
2. Click **Update branch** only if GitHub asks (this just syncs PR with main; it does **not** publish the fix).
3. Click **Merge pull request**.
4. Wait until the merge commit appears on the repo **Code** page for branch `main`.

Then run install commands from RStudio.

Quick verification in browser before install:
- Open `https://github.com/patrickjburke6112/hotspot-analysis-studio/blob/main/DESCRIPTION`
- If this page 404s or does not show package metadata, `main` does not yet contain the package commit.


In RStudio Console:

```r
install.packages(c("remotes", "sf"))
remotes::install_github("patrickjburke6112/hotspot-analysis-studio", ref = "main", build_vignettes = FALSE)
```

If `install_github()` returns HTTP 404 in RStudio, use one of these **no-Git-required** options:

```r
# Option A (pure R, no system git): download zip, detect DESCRIPTION path, then install
install.packages("remotes")
zip_file <- tempfile(fileext = ".zip")
unzip_dir <- tempfile("hotspotstudio_")
dir.create(unzip_dir)

utils::download.file(
  "https://github.com/patrickjburke6112/hotspot-analysis-studio/archive/refs/heads/main.zip",
  destfile = zip_file,
  mode = "wb"
)

utils::unzip(zip_file, exdir = unzip_dir)

# Optional debug: inspect extracted files
print(list.files(unzip_dir, recursive = TRUE))

# Find the extracted package root by locating DESCRIPTION
candidates <- list.files(unzip_dir, pattern = "^DESCRIPTION$", recursive = TRUE, full.names = TRUE)
if (length(candidates) == 0) {
  stop("Could not find DESCRIPTION after unzip. Usually this means main branch is not updated or the download returned an error/login page.")
}

pkg_dir <- dirname(candidates[[1]])
remotes::install_local(pkg_dir, build_vignettes = FALSE, upgrade = "never")
```

```r
# Option B (manual download in browser, then local install)
# 1) Open in browser:
#    https://github.com/patrickjburke6112/hotspot-analysis-studio/archive/refs/heads/main.zip
# 2) Unzip it
# 3) Install from that unzipped folder path
# Tip: make sure this folder contains DESCRIPTION
remotes::install_local("C:/path/to/hotspot-analysis-studio-main", build_vignettes = FALSE)
```

If you want to retry authenticated API install (optional):


```r
install.packages("gh")
Sys.setenv(GITHUB_PAT = "<your_github_pat>")
gh::gh_whoami()
remotes::install_github("patrickjburke6112/hotspot-analysis-studio", ref = "main", build_vignettes = FALSE)
```

Notes:
- `gitcreds::gitcreds_set()` requires **system git**; skip it if git is not installed.
- `git clone ...` is a shell command, not R code (run it in Git Bash/Terminal, not in R Console).

After install, verify package load:

```r
library(hotspotstudio)
packageVersion("hotspotstudio")
```

### 2) Prepare your point data in R

Your table needs at least these columns:
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

Join to polygons:
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

---

## Example files in repo
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

