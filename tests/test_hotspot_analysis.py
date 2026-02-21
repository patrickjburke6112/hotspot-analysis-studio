from hotspot_analysis import compute_gi_star_rows


def test_compute_gi_star_outputs_expected_columns_and_classes():
    rows = [
        {"id": "1", "latitude": "40.0", "longitude": "-75.0", "value": "25"},
        {"id": "2", "latitude": "40.001", "longitude": "-75.001", "value": "24"},
        {"id": "3", "latitude": "40.002", "longitude": "-75.002", "value": "26"},
        {"id": "4", "latitude": "40.05", "longitude": "-75.05", "value": "4"},
        {"id": "5", "latitude": "40.051", "longitude": "-75.051", "value": "3"},
        {"id": "6", "latitude": "40.052", "longitude": "-75.052", "value": "5"},
    ]

    result = compute_gi_star_rows(
        rows,
        id_col="id",
        lat_col="latitude",
        lon_col="longitude",
        value_col="value",
        k_neighbors=2,
    )

    assert "gi_star_zscore" in result[0]
    assert "gi_star_pvalue" in result[0]
    assert "gi_bin" in result[0]
    assert {r["gi_bin"] for r in result}.issubset(
        {
            "Hot Spot 99%",
            "Hot Spot 95%",
            "Hot Spot 90%",
            "Cold Spot 99%",
            "Cold Spot 95%",
            "Cold Spot 90%",
            "Not Significant",
        }
    )
