# datum-sync
A BMI-compliant module to convert vertical datum between inland and coastal models.

This function wraps the library pyproj (a Python implementation of geospatial PROJ library) to convert between defined EPSG CRS. It includes focus on ensuring z (elevation) variables are correctly handled by producing meaningful warnings if CRS input/output did not change z values when the user may have expected this.

An example notebook `examples/example_convert.ipynb` demonstrates the function itself. Interacting with the BMI module is demonstrated in `examples/run_bmi_datum_sync.py`. `tests` individually tests both the base function and BMI wrapper.

This module currently requires network connectivity.

# Running
This repository is managed with [UV](https://docs.astral.sh/uv/getting-started/installation/). Installing with `pip` may cause import problems. To install with uv:

`uv sync`

`source .venv/bin/activate`

To run juptyer notebook examples and tests:

`uv sync --extra dev-examples`

## Testing
To run the collection of pytests, at root directory with `dev-examples` installed, run:

`pytest tests`

If you have import problems after running `uv sync`, update `uv` with `uv self update`.

# NextGen inflows & outflows dataset to coastal area
Dataset related to NextGen inflows and outflows has been added to 'examples/data/NextGen'

To verify that the dataset meets the required criteria, run the following test code:
`pytest -v tests/unit/test_NGen_datum_sync.py`

To convert the NextGen dataset into the crs for coastal model, use `examples/NGEN_bmi_datum_sync.py`.

1. Open the file and set output working directory.
2. Verify that `bmi_config.yaml` file in `examples/data/NextGen/` is properly configured to match your current coordinate reference system (CRS) and target output CRS.
3. Run:
```
cd examples
python NGen_bmi_datum_sync.py
```
