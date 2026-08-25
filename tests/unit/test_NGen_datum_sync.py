
from pathlib import Path
import sys
import pandas as pd
import pytest
# getting the root project
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(Path(project_root / "src")))
from datum_sync.bmi.bmi_datum_sync import BmiDatumSync

# Column matching helper
def find_column(columns, keys):
    for key in keys:
        for col in columns:
            if key in col.lower():
                return col
    return None

# Parametrize test using actual CSV files
project_root = Path(__file__).resolve().parents[2]
NGen_dir = project_root / "examples" / "data" / "NextGen"
csv_files = list(NGen_dir.glob("*.csv"))

@pytest.mark.parametrize("input_path", csv_files)
def test_nextgen_csv_files(input_path: Path) -> None:
    output_path = input_path.parent / "out" / f"out_{input_path.name}"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # check config file path is available
    config_file = project_root / "examples" / "data" / "NextGen"/ "bmi_config.yaml"
    assert config_file.exists(), "Missing config file for BMI model"

    # checking the required columns are in the csv files
    df = pd.read_csv(input_path)

    lat_col = find_column(df.columns, ["lat", "latitude"])
    lon_col = find_column(df.columns, ["lon", "long", "longitude"])
    elev_col = find_column(df.columns, ["z", "elev", "elevation"])

    assert lat_col and lon_col, f"{input_path.name} missing required columns"

    use_cols = [lon_col, lat_col] + ([elev_col] if elev_col else [])

    df_filtered = df[use_cols].rename(columns={
        lat_col: "latitude",
        lon_col: "longitude",
        **({elev_col: "elevation"} if elev_col else {})
    })

    assert df_filtered[["latitude", "longitude"]].notnull().all().all(), f"Missing coordinates in {input_path.name}"
