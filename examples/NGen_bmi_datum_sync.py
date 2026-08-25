import os
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------
# Set up paths and environment
# ------------------------------------------------------
# Import the BMI interface
from datum_sync.bmi.bmi_datum_sync import BmiDatumSync

# Define data and config paths
# Must run in directory of file
data_path = Path.cwd() / "data" / "NextGen"

# Define your output directory
output_dir = "/path/to/output_directory"
bmi_cfg_file = Path.cwd() / "data" / "NextGen" / "bmi_config.yaml"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------------------
# Initialize the model
# ------------------------------------------------------

print("Starting BMI")
model = BmiDatumSync()
model.initialize(bmi_cfg_file)

# ------------------------------------------------------
# Gather input/output CSV file paths
# ------------------------------------------------------

input_files = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.endswith(".csv")]

output_files = [os.path.join(output_dir, "out_" + os.path.basename(f)) for f in input_files]

# ------------------------------------------------------
# Define column name matching rules
# ------------------------------------------------------

lat_keys = ["lat", "latitude"]
lon_keys = ["lon", "long", "longitude"]
elev_keys = ["z", "elev", "elevation"]


def find_column(columns: list[str], keys: list[str]) -> str | None:
    """Return the first column name that matches any of the specified keys."""
    for key in keys:
        for col in columns:
            if key in col.lower():
                return col
    return None


# ------------------------------------------------------
# Process each file
# ------------------------------------------------------

for input_path, output_path in zip(input_files, output_files, strict=False):
    df = pd.read_csv(input_path)

    # Identify coordinate columns
    lat_col = find_column(df.columns, lat_keys)
    lon_col = find_column(df.columns, lon_keys)
    elev_col = find_column(df.columns, elev_keys)

    if not (lat_col and lon_col):
        raise ValueError(f"{input_path}: CSV must contain at least latitude and longitude columns.")

    # Build list of coordinate columns
    use_cols = [lon_col, lat_col] + ([elev_col] if elev_col else [])

    # Create a filtered and standardized DataFrame with consistent column names
    df_filtered = df[use_cols].rename(
        columns={lat_col: "latitude", lon_col: "longitude", **({elev_col: "elevation"} if elev_col else {})}
    )

    # Set model input values
    for col in df_filtered.columns:
        model.set_value(col, df_filtered[col].tolist())
    model.update()

    # Retrieve model output
    n_rows, n_cols = df_filtered.shape
    dest_array = np.zeros(n_rows * n_cols)
    model.get_value("coordinates__output", dest_array)

    df_model_out = pd.DataFrame(dest_array.reshape((n_rows, n_cols), order="F"), columns=df_filtered.columns)

    # Append all original non-coordinate metadata columns
    metadata_cols = df.drop(columns=use_cols, errors="ignore")
    df_final_out = pd.concat([df_model_out, metadata_cols], axis=1)

    # Save the result to output CSV
    df_final_out.to_csv(output_path, index=False)

    # Optionally retrieve CRS value (not used further here)
    crs_array = np.zeros(1)
    model.get_value("crs_in", crs_array)

    print(f"Finished processing: {input_path}")

# ------------------------------------------------------
# Finalize the model
# ------------------------------------------------------

print("Finalize")
model.finalize()
