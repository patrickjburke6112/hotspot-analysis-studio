\name{classify_significance}
\alias{classify_significance}
\title{Classify Gi* significance labels}
\usage{
classify_significance(z_score, p_value)
}
\arguments{
  \item{z_score}{Numeric Gi* z-score.}
  \item{p_value}{Two-sided p-value.}
}
\value{A character significance class label.}
\description{Maps Gi* z-score and p-value to hotspot/coldspot confidence bins.}
