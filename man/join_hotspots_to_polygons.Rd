\name{join_hotspots_to_polygons}
\alias{join_hotspots_to_polygons}
\title{Join hotspot points to polygons and summarize}
\usage{
join_hotspots_to_polygons(
  hotspot_df,
  polygons_path,
  polygon_id_col,
  lat_col = "latitude",
  lon_col = "longitude"
)
}
\arguments{
  \item{hotspot_df}{Output data frame from \code{compute_gi_star}.}
  \item{polygons_path}{Path to polygon file readable by \code{sf::st_read}.}
  \item{polygon_id_col}{ID field in polygon layer for joins.}
  \item{lat_col}{Latitude column name in hotspot_df.}
  \item{lon_col}{Longitude column name in hotspot_df.}
}
\value{A list with \code{points_joined} and \code{polygon_summary} data frames.}
\description{Assigns points to polygons and builds polygon-level hotspot/coldspot counts and summary metrics.}
