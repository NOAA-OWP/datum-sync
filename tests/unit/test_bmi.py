from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal, assert_array_equal

from datum_sync.bmi import BmiDatumSync
from datum_sync.bmi.config import DatumSyncConfig

dir = Path(__file__).parent


@pytest.fixture
def base_model_xy() -> BmiDatumSync:
    """Use an XY only when possible to speed up initializing because 3D requires downloading CRS grid"""
    model = BmiDatumSync()
    model.initialize(dir / "config/config_base_xy.yaml")
    return model


@pytest.fixture
def base_model_xyz() -> BmiDatumSync:
    """Use a XYZ model to test XYZ capabilities"""
    model = BmiDatumSync()
    model.initialize(dir / "config/config_base_xyz.yaml")
    return model


def test_init() -> None:
    model = BmiDatumSync()
    assert model.input_names == (
        "longitude",
        "latitude",
        "elevation",
        "crs_in",
        "crs_out",
        "z_warn",
    )
    assert model.output_names == ("coordinates__output",)
    assert model.input == {
        "longitude": 0,
        "latitude": 0,
        "elevation": 0,
        "crs_in": 0,
        "crs_out": 0,
        "z_warn": 0,
    }

    assert model.output == {"coordinates__output": 0}


def test_initialize(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    assert model.config == DatumSyncConfig(crs_input=4269, crs_output=4326, z_warn=False)
    assert model.input["crs_in"] == 4269
    assert model.input["crs_out"] == 4326
    assert not model.input["z_warn"]


def test_update_coordinates__xy(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    model.set_value("longitude", [-80, -81])
    model.set_value("latitude", [40, 41])
    model.update()
    assert_array_almost_equal(
        model.output["coordinates__output"], np.array([[-79.999998, -80.999999], [39.999998, 40.999999]])
    )


def test_update_coordinates__xyz(base_model_xyz: BmiDatumSync) -> None:
    """Use the XYZ base model to check elevation conversions"""
    model = base_model_xyz
    model.set_value("longitude", [-79.4, -79])
    model.set_value("latitude", [43.7, 43])
    model.set_value("elevation", [100, 110])
    model.update()
    assert_array_almost_equal(
        model.output["coordinates__output"],
        np.array([[-79.3999985, -78.9999969], [43.6999915, 42.9999918], [137.6331231, 146.6187439]]),
    )


def test_finalize(base_model_xy: BmiDatumSync) -> None:
    """Confirm finalize deleted attributes"""
    model = base_model_xy
    model.finalize()
    for param in ["longitude", "latitude", "elevation"]:
        with pytest.raises(KeyError):
            model.input[param]
    with pytest.raises(AttributeError):
        _ = model.syncer


def test_get_component_name(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    assert model.get_component_name() == "Datum Sync"


def test_set_value(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    model.set_value("longitude", [1])
    assert model.input["longitude"] == [1]


def test_set_value__error(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    with pytest.raises(
        ValueError,
        match="Variable fake does not exist input or output variables.  User getters to view options.",
    ):
        model.set_value("fake", [1])


def test_get_value(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    model.set_value("longitude", [1])
    dest_array = np.zeros(1)
    model.get_value("longitude", dest_array)
    assert_array_equal(dest_array, np.array([1.0]))


get_value_ptr_data = [
    pytest.param("longitude", [1], id="get value ptr input var"),
    pytest.param(
        "coordinates__output",
        np.array(
            [
                [1],
                [
                    1,
                ],
            ]
        ),
        id="get value output var",
    ),
]


@pytest.mark.parametrize("name,expected", get_value_ptr_data)
def test_get_value_ptr(base_model_xy: BmiDatumSync, name: str, expected: Any) -> None:
    model = base_model_xy
    model.set_value(name, expected)
    value = model.get_value_ptr(name)
    assert_array_equal(value, expected)


def test_get_value_ptr__error(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    with pytest.raises(KeyError):
        model.get_value_ptr("fake")


def test_get_var_nbytes(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    model.set_value("latitude", np.array([1]))
    val = model.get_var_nbytes("latitude")
    assert val == 8


def test_get_var_itemsize(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    model.set_value("latitude", np.array([1]))
    val = model.get_var_itemsize("latitude")
    assert val == 8


def test_get_var_type(base_model_xy: BmiDatumSync) -> None:
    model = base_model_xy
    model.set_value("latitude", np.array([1.0]))
    val = model.get_var_type("latitude")
    assert val == "float64"
