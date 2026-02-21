#' Classify Gi* significance labels
#'
#' @param z_score Numeric Gi* z-score.
#' @param p_value Two-sided p-value.
#'
#' @return Character class label.
classify_significance <- function(z_score, p_value) {
  if (p_value <= 0.01) {
    return(ifelse(z_score > 0, "Hot Spot 99%", "Cold Spot 99%"))
  }
  if (p_value <= 0.05) {
    return(ifelse(z_score > 0, "Hot Spot 95%", "Cold Spot 95%"))
  }
  if (p_value <= 0.10) {
    return(ifelse(z_score > 0, "Hot Spot 90%", "Cold Spot 90%"))
  }
  "Not Significant"
}

.haversine_km <- function(lat1, lon1, lat2, lon2) {
  r <- 6371.0088
  phi1 <- lat1 * pi / 180
  phi2 <- lat2 * pi / 180
  dphi <- (lat2 - lat1) * pi / 180
  dlambda <- (lon2 - lon1) * pi / 180
  a <- sin(dphi / 2)^2 + cos(phi1) * cos(phi2) * sin(dlambda / 2)^2
  2 * r * asin(sqrt(a))
}

#' Compute Getis-Ord Gi* on a point data frame
#'
#' @param points_df data.frame containing ID, latitude, longitude, and value fields.
#' @param id_col ID column name.
#' @param lat_col Latitude column name.
#' @param lon_col Longitude column name.
#' @param value_col Analysis variable column name.
#' @param k_neighbors Number of nearest neighbors (excluding self).
#'
#' @return data.frame with Gi* z-score, p-value, and class labels.
#' @export
compute_gi_star <- function(points_df,
                            id_col = "id",
                            lat_col = "latitude",
                            lon_col = "longitude",
                            value_col = "value",
                            k_neighbors = 8) {
  required <- c(id_col, lat_col, lon_col, value_col)
  missing <- setdiff(required, names(points_df))
  if (length(missing) > 0) {
    stop("Missing required columns: ", paste(missing, collapse = ", "))
  }
  if (k_neighbors < 1) {
    stop("k_neighbors must be >= 1")
  }

  n <- nrow(points_df)
  if (n < 3) {
    stop("At least 3 points are required")
  }

  lat <- as.numeric(points_df[[lat_col]])
  lon <- as.numeric(points_df[[lon_col]])
  values <- as.numeric(points_df[[value_col]])

  if (any(is.na(lat)) || any(is.na(lon)) || any(is.na(values))) {
    stop("Input columns contain NA or non-numeric values")
  }

  xbar <- mean(values)
  s <- stats::sd(values)
  if (s == 0) {
    stop("Input value column has no variance")
  }

  zscores <- numeric(n)
  pvals <- numeric(n)

  for (i in seq_len(n)) {
    dists <- vapply(seq_len(n), function(j) .haversine_km(lat[i], lon[i], lat[j], lon[j]), numeric(1))
    ord <- order(dists)
    k <- min(k_neighbors + 1, n)
    neighbors <- ord[seq_len(k)]

    wij_sum <- length(neighbors)
    wij_sq_sum <- wij_sum
    weighted_x_sum <- sum(values[neighbors])

    denom_term <- ((n * wij_sq_sum) - (wij_sum^2)) / (n - 1)
    denom <- s * sqrt(denom_term)
    if (denom == 0) {
      stop("Encountered zero denominator in Gi* computation")
    }

    z <- (weighted_x_sum - (xbar * wij_sum)) / denom
    p <- 2 * stats::pnorm(abs(z), lower.tail = FALSE)

    zscores[i] <- z
    pvals[i] <- p
  }

  points_df$gi_star_zscore <- zscores
  points_df$gi_star_pvalue <- pvals
  points_df$gi_bin <- mapply(classify_significance, points_df$gi_star_zscore, points_df$gi_star_pvalue)
  points_df
}

#' Join hotspot points to polygons and summarize by polygon ID
#'
#' @param hotspot_df Output from [compute_gi_star()].
#' @param polygons_path Path to polygon file readable by sf (GeoJSON, GPKG, shapefile).
#' @param polygon_id_col Polygon identifier field (for example GEOID).
#' @param lat_col Latitude column in hotspot_df.
#' @param lon_col Longitude column in hotspot_df.
#'
#' @return A list with `points_joined` and `polygon_summary` data frames.
#' @export
join_hotspots_to_polygons <- function(hotspot_df,
                                      polygons_path,
                                      polygon_id_col,
                                      lat_col = "latitude",
                                      lon_col = "longitude") {
  if (!requireNamespace("sf", quietly = TRUE)) {
    stop("Package 'sf' is required for polygon joins. Install with install.packages('sf').")
  }

  needed <- c(lat_col, lon_col, "gi_star_zscore", "gi_star_pvalue", "gi_bin")
  missing <- setdiff(needed, names(hotspot_df))
  if (length(missing) > 0) {
    stop("hotspot_df missing required columns: ", paste(missing, collapse = ", "))
  }

  points_sf <- sf::st_as_sf(hotspot_df, coords = c(lon_col, lat_col), crs = 4326, remove = FALSE)
  polygons_sf <- sf::st_read(polygons_path, quiet = TRUE)

  if (!(polygon_id_col %in% names(polygons_sf))) {
    stop("polygon_id_col not found in polygon data: ", polygon_id_col)
  }

  if (!sf::st_is_longlat(polygons_sf)) {
    polygons_sf <- sf::st_transform(polygons_sf, 4326)
  }

  join_cols <- unique(c(polygon_id_col, attr(polygons_sf, "sf_column")))
  joined <- sf::st_join(points_sf, polygons_sf[, join_cols], join = sf::st_within, left = TRUE)
  joined_df <- as.data.frame(joined)

  geoid <- joined_df[[polygon_id_col]]
  split_idx <- split(seq_len(nrow(joined_df)), geoid, drop = FALSE)

  summary_rows <- lapply(names(split_idx), function(pid) {
    idx <- split_idx[[pid]]
    sub <- joined_df[idx, , drop = FALSE]
    labels <- sub$gi_bin

    data.frame(
      polygon_id = ifelse(is.na(pid) || pid == "", "", pid),
      point_count = nrow(sub),
      hotspot_99 = sum(labels == "Hot Spot 99%", na.rm = TRUE),
      hotspot_95 = sum(labels == "Hot Spot 95%", na.rm = TRUE),
      hotspot_90 = sum(labels == "Hot Spot 90%", na.rm = TRUE),
      coldspot_99 = sum(labels == "Cold Spot 99%", na.rm = TRUE),
      coldspot_95 = sum(labels == "Cold Spot 95%", na.rm = TRUE),
      coldspot_90 = sum(labels == "Cold Spot 90%", na.rm = TRUE),
      mean_zscore = mean(sub$gi_star_zscore, na.rm = TRUE),
      min_pvalue = min(sub$gi_star_pvalue, na.rm = TRUE)
    )
  })

  summary_df <- do.call(rbind, summary_rows)
  names(summary_df)[names(summary_df) == "polygon_id"] <- polygon_id_col

  list(points_joined = joined_df, polygon_summary = summary_df)
}
