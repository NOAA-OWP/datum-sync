from pathlib import Path

import numpy as np
import pandas as pd

from datum_sync.bmi.bmi_datum_sync import BmiDatumSync

# Run from directory of this file
cwd = Path.cwd()
data_path = Path.cwd() / "data"
bmi_cfg_file = data_path / "bmi_config.yaml"

# Initializing the BMI
print("Starting BMI")
model = BmiDatumSync()

# has CRS inputs and outputs
model.initialize(bmi_cfg_file)

# Get input data that matches the LSTM test runs
print("Getting input data")
list_data = [data_path / "sample_data_1.csv", data_path / "sample_data_2.csv"]
list_output = [data_path / "sample_output_1.csv", data_path / "sample_output_2.csv"]

# Now loop through csvs, update model, save output. 'sequence' of model updates is your file list.
print("Set values & update model")
for data, output in zip(list_data, list_output, strict=False):
    # read values from csv to update model
    df = pd.read_csv(data)

    # 3D
    if df.columns.tolist() == ["longitude", "latitude", "elevation"]:
        # set new values
        for i in df.columns:
            model.set_value(i, df[i].tolist())
        model.update()

    # 2D
    elif df.columns.tolist() == ["longitude", "latitude"]:
        # set new values
        for i in df.columns:
            model.set_value(i, df[i].tolist())
        model.update()
    else:
        raise ValueError(
            "Input csv must contain columns ['longitude', 'latitude', 'elevation'] or ['longitude', 'latitude']"
        )

    # get values and save output to csv
    dest_array = np.zeros(df.shape[0] * df.shape[1])
    model.get_value("coordinates__output", dest_array)
    pd.DataFrame(columns=df.columns, data=dest_array.reshape(df.shape, order="F")).to_csv(output, index=False)

    # demonstrating retrieving a 1D input var
    des_array = np.zeros(1)
    model.get_value("crs_in", des_array)

    print(f"Finished {data}")

# Finalizing the BMI
print("Finalize")
model.finalize()
