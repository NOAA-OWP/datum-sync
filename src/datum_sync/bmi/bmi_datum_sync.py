from pathlib import Path
from typing import Any

import numpy as np
import yaml
from numpy.typing import NDArray

from datum_sync.datum_sync import DatumSync
from datum_sync.bmi.bmi_base import BmiBase
from datum_sync.bmi.config import DatumSyncConfig

__all__ = ["BmiDatumSync"]


class BmiDatumSync(BmiBase):
    """BMI composition wrapper for datum sync"""

    def __init__(self) -> None:
        super()

        self.input_names = (
            "longitude",
            "latitude",
            "elevation",
            "crs_in",
            "crs_out",
            "z_warn",
        )
        self.output_names = ("coordinates__output",)

        self.input: dict[Any, Any] = dict(
            zip(self.input_names, [0 for i in range(len(self.input_names))], strict=False)
        )
        self.output: dict[Any, Any] = dict(
            zip(self.output_names, [0 for i in range(len(self.output_names))], strict=False)
        )

    def initialize(self, config_file: str | Path) -> None:
        """Intialize the BMI model with config, datum transformer, and datum sync class.

        Args:
            config (str): _description_
        """
        # read yaml
        with open(config_file) as f:
            config_read = yaml.safe_load(f)

        # load into pydantic model and save in class for querying
        self.config = DatumSyncConfig.model_validate(config_read)
        self.input["crs_in"] = np.array(self.config.crs_input)
        self.input["crs_out"] = np.array(self.config.crs_output)
        self.input["z_warn"] = (
            np.array(self.config.z_warn) if self.config.z_warn is not None else np.array(True)
        )

        transformer = DatumSync.epsg_to_transform(
            crs_input=self.config.crs_input, crs_output=self.config.crs_output
        )

        self.syncer = DatumSync(transform=transformer)

    def update(self) -> None:
        """Update the model based on inputs"""
        if self.input["longitude"] and self.input["latitude"] and self.input["elevation"]:
            output = self.syncer.convert_datum(
                np.array(self.input["longitude"]),
                np.array(self.input["latitude"]),
                self.input["elevation"],
                z_warn=self.input["z_warn"],
            )
            self.output["coordinates__output"] = np.array([output[0], output[1], output[2]])
        elif self.input["longitude"] and self.input["latitude"] and not self.input["elevation"]:
            output = self.syncer.convert_datum(
                np.array(self.input["longitude"]),
                np.array(self.input["latitude"]),
                z_warn=self.input["z_warn"],
            )
            self.output["coordinates__output"] = np.array([output[0], output[1]])
        else:
            raise UserWarning(
                "No longitude, latitude, elevation input. Use set_value to set longitude, latitude, and optionally elevation"
            )

    def finalize(self) -> None:
        """Clean up any internal resources of the model"""
        del self.syncer, self.input["longitude"], self.input["latitude"], self.input["elevation"]

    def get_component_name(self) -> str:
        """Name of this BMI module component.

        Returns
        -------
            str: Model Name
        """
        return "Datum Sync"

    def get_input_item_count(self) -> int:
        """Number of model input variables

        Returns
        -------
            int: number of input variables
        """
        return len(self.input_names)

    def get_input_var_names(self) -> tuple[str, ...]:  # type: ignore[override]
        """The names of each input variables

        Returns
        -------
            tuple[str, ...]: iterable tuple of input variable names
        """
        return self.input_names

    def get_output_item_count(self) -> int:
        """Number of model output variables

        Returns
        -------
            int: number of output variables
        """
        return len(self.output_names)

    def get_output_var_names(self) -> tuple[str, ...]:  # type: ignore[override]
        """The names of each output variable

        Returns
        -------
            tuple[str, ...]: iterable tuple of output variable names
        """
        return self.output_names

    # BMI Variable Query
    def set_value(self, name: str, src: Any) -> None:
        """Sets and input or output value

        Args:
            name (str): name of value
            src (Any): value to set

        Raises
        ------
            ValueError: If name does not exist
        """
        if name in self.output_names:
            self.output[name] = src
        elif name in self.input_names:
            self.input[name] = src
        else:
            raise ValueError(
                f"Variable {name} does not exist input or output variables.  User getters to view options."
            )

    def get_value(self, name: str, dest: NDArray) -> NDArray:
        """_Copies_ a variable's np.np.ndarray into `dest` and returns `dest`."""
        value = self.get_value_ptr(name)
        try:
            if not isinstance(value, np.ndarray):
                dest[:] = np.array(value).flatten()
            else:
                dest[:] = self.get_value_ptr(name).flatten()
        except Exception as e:
            raise RuntimeError(f"Could not return value {name} as flattened array") from e

        return dest

    def get_value_ptr(self, name: str) -> NDArray:
        """Gets value in native form if exists in inputs or outputs"""
        try:
            return self.output[name]
        except KeyError:
            return self.input[name]
        except KeyError as e:  # NOQA: B025
            raise KeyError(f"{name} is not a known variable") from e

    def get_var_itemsize(self, name: str) -> int:
        """Size, in bytes, of a single element of the variable name

        Args:
            name (str): variable name

        Returns
        -------
            int: number of bytes representing a single variable of @p name
        """
        return self.get_value_ptr(name).itemsize

    def get_var_nbytes(self, name: str) -> int:
        """Size, in nbytes, of a single element of the variable name

        Args:
            name (str): Name of variable.

        Returns
        -------
            int: Size of data array in bytes.
        """
        return self.get_value_ptr(name).nbytes

    def get_var_type(self, name: str) -> str:
        """Data type of variable.

        Args:
            name (str): Name of variable.

        Returns
        -------
            str: Data type.
        """
        return str(self.get_value_ptr(name).dtype)
