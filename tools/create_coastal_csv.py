"""
A file to create the coastal CSV intersection file based on the hydrofabric and coastal polygons

Example cmd:
python tools/create_coastal_csv.py --gpkg conus_nextgen.gpkg --coastal-cw AtlGulf_InflowsOutflows_CCBuff.shp --file-name AtlGulf_hf_cross_walk
"""

import argparse
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


def create_coastal_csv(gpkg: Path, coastal_cw: Path, file_name: str) -> None:
    """A script that converts the CW shape file points to contain latest HF IDs and attrs

    Parameters
    ----------
    gpkg : Path
        The path to the conus_nextgen gpkg
    coastal_cw : Path
        The path to the coastal polygons shp file
    file_name : str
        The file name for the output csv and gpkg files
    """
    divide_attr = gpd.read_file(gpkg, layer="divide-attributes")
    divides = gpd.read_file(gpkg, layer="divides")
    coastal_gdf = gpd.read_file(coastal_cw)

    if divides.crs != coastal_gdf.crs:
        print("Reprojecting coastal bounds to match divides CRS")
        coastal_gdf = coastal_gdf.to_crs(divides.crs)

    print("Generating points from coastal polygon boundaries")
    coastal_points = []

    for idx, row in coastal_gdf.iterrows():
        coastal_points.append(
            {
                "point_idx": idx,
                "longitude": row["long"],
                "latitude": row["lat"],
                "geometry": Point(row["long"], row["lat"]),
            }
        )

    coastal_points_gdf = gpd.GeoDataFrame(coastal_points, crs="EPSG:4326").to_crs(divides.crs)
    points_with_divides = gpd.sjoin(coastal_points_gdf, divides, how="left", predicate="within")
    points_with_divides = points_with_divides.drop_duplicates("point_idx")
    points_with_divides = points_with_divides.dropna(subset=["divide_id"])

    merged_points = points_with_divides.merge(
        divide_attr,
        on="divide_id",
        how="left",
    )
    results_df = merged_points.drop_duplicates().copy()

    results_df.to_csv(Path.cwd() / f"{file_name}.csv", index=False)
    results_df.to_file(Path.cwd() / f"{file_name}.gpkg", driver="GPKG")
    print(f"Coastal summary saved to {file_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates a CSV file that has the lat/lon of a flowpath source point for the coastal models + additional info"
    )

    parser.add_argument(
        "--gpkg",
        type=Path,
        required=True,
        help="The path to the hydrofabric gpkg",
    )
    parser.add_argument(
        "--coastal-cw",
        type=Path,
        required=True,
        help="The path to the coastal polygons shp file",
    )
    parser.add_argument(
        "--file-name",
        type=Path,
        required=True,
        help="The file name for the output csv and gpkg files",
    )

    args = parser.parse_args()
    create_coastal_csv(gpkg=args.gpkg, coastal_cw=args.coastal_cw, file_name=args.file_name)
