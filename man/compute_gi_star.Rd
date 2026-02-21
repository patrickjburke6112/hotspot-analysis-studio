\name{compute_gi_star}
\alias{compute_gi_star}
\title{Compute Getis-Ord Gi* on a point data frame}
\usage{
compute_gi_star(
  points_df,
  id_col = "id",
  lat_col = "latitude",
  lon_col = "longitude",
  value_col = "value",
  k_neighbors = 8
)
}
\arguments{
  \item{points_df}{data.frame containing point coordinates and analysis values.}
  \item{id_col}{ID column name.}
  \item{lat_col}{Latitude column name.}
  \item{lon_col}{Longitude column name.}
  \item{value_col}{Analysis value column name.}
  \item{k_neighbors}{Number of nearest neighbors (excluding self).}
}
\value{data.frame with added \code{gi_star_zscore}, \code{gi_star_pvalue}, and \code{gi_bin}.}
\description{Runs local Getis-Ord Gi* hotspot analysis using k-nearest-neighbor weights.}
