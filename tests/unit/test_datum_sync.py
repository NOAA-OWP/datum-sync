from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal
from numpy.typing import NDArray
from pyproj import CRS, Transformer

from datum_sync import DatumSync
from datum_sync.exceptions import TransformError, ZConversionWarning

convert_datum_data = [
    pytest.param(
        [-79.4, -79],
        [43.7, 43],
        [100, 110],
        (4979, 5498),
        np.array([[-79.3999985, -78.9999969], [43.6999915, 42.9999918], [137.6331231, 146.6187439]]),
        id="XYZ input lists",
    ),
    pytest.param(
        np.array([-79.4, -79]),
        np.array([43.7, 43]),
        np.array([100, 110]),
        (4979, 5498),
        np.array([[-79.3999985, -78.9999969], [43.6999915, 42.9999918], [137.6331231, 146.6187439]]),
        id="XYZ input np arrays",
    ),
    pytest.param(
        np.array([-79.4, -79]),
        np.array([43.7, 43]),
        None,
        (4979, 5498),
        np.array([[-79.3999985, -78.9999969], [43.6999915, 42.9999918]]),
        id="XY input np arrays",
    ),
    pytest.param(
        [-79.4, -79],
        [43.7, 43],
        None,
        (4979, 5498),
        np.array([[-79.3999985, -78.9999969], [43.6999915, 42.9999918]]),
        id="XY input lists",
    ),
    pytest.param(
        [-79.4, -79],
        [43.7, 43],
        None,
        (4326, 4269),
        np.array([[-79.399999, -78.999999], [43.700001, 43.000002]]),
        id="XY input lists - no network connectivity download",
    ),
]


@pytest.mark.parametrize("xx,yy,zz,crs,expected", convert_datum_data)
def test_convert_datum(xx: Any, yy: Any, zz: Any, crs: tuple[int, int], expected: NDArray) -> None:
    """Convert datum between XY or XYZ. Use approx equals to handle floating point difference by OS"""
    syncer = DatumSync(crs_input=crs[0], crs_output=crs[1])
    output = syncer.convert_datum(xx=xx, yy=yy, zz=zz)

    # assert at 6 decimals
    assert_array_almost_equal(np.array(output), expected)


def test_convert_datum__z_warning() -> None:
    """Warning for z values not changed. Uses values from input 5498 to output 5070"""
    xx = [-79.39999849691358, -78.99999685400357]
    yy = [
        43.69999146739919,
        42.99999183172088,
    ]
    zz = [137.6331231, 146.6187439]
    expected = np.array(
        [
            [1325676.0689027791, 1371188.7036548508],
            [2416931.24897092, 2345672.0544312494],
            [137.6331231, 146.6187439],
        ]
    )
    syncer = DatumSync(crs_input=5498, crs_output=5070)
    with pytest.warns(
        ZConversionWarning,
        match="Z values were not altered. This could be expected. This may be because input and output CRS do not have vertical element.",
    ):
        output = syncer.convert_datum(xx=xx, yy=yy, zz=zz)
        assert_array_almost_equal(np.array(output), expected)


def test_epsg_to_transform() -> None:
    """epsg_to_transform should be same as from CRS"""
    transform = DatumSync.epsg_to_transform(4326, 4269)
    expected = Transformer.from_crs(4326, 4269, always_xy=True)
    assert transform == expected


def test_epsg_to_transform__exception() -> None:
    """Transform error if bad transformation happens, e.g. bad CRS values"""
    with pytest.raises(TransformError, match="Issue creating CRS and transformer. Check if CRS are valid."):
        DatumSync.epsg_to_transform(432, 0)


def test_check_z_conversion() -> None:
    """Warning for z values not changed"""
    syncer = DatumSync(crs_input=5070, crs_output=5498)
    syncer.zz = 1
    syncer.output = (1, 1, 1)

    with pytest.warns(
        ZConversionWarning,
        match="Z values were not altered. This could be expected. This may be because input and output CRS do not have vertical element.",
    ):
        syncer._check_z_conversion()


def test_check_z_units() -> None:
    """Warning for z units converted but values not changed"""
    syncer = DatumSync(crs_input=5070, crs_output=5498)
    syncer.zz = 1
    syncer.output = (1, 1, 0.3048)

    with pytest.warns(
        ZConversionWarning,
        match="Z values were converted between meters and feet but were not altered."
        " This may be because input and output CRS do not have vertical element.",
    ):
        syncer._check_z_units()


init_error_data = [
    pytest.param(4326, None, None, id="CRS input only"),
    pytest.param(4326, 4269, 1, id="CRS (in and out) and transform input"),
    pytest.param(4326, None, 1, id="CRS (in) and transform input"),
]


@pytest.mark.parametrize("crs_input,crs_output,transform_flag", init_error_data)
def test_datum_sync_init__error(crs_input: int, crs_output: int, transform_flag: bool) -> None:
    """Warn if inputs are incorrect (CRS in and out OR transform)

    Use a flag to generate a transformer for test input"""
    transform = (
        Transformer.from_crs(crs_from=CRS.from_epsg(4326), crs_to=CRS.from_epsg(4269), always_xy=True)
        if transform_flag
        else None
    )

    with pytest.raises(
        ValueError,
        match="CRS/transform input incorretly specified. "
        "Either input crs_in and crs_out OR transform; but not both",
    ):
        DatumSync(crs_input=crs_input, crs_output=crs_output, transform=transform)


def test_datum_sync_init__crs() -> None:
    """Initialize with a CRS input and output"""
    syncer = DatumSync(crs_input=4326, crs_output=4269)
    assert syncer.transform == Transformer.from_crs(
        crs_from=CRS.from_epsg(4326), crs_to=CRS.from_epsg(4269), always_xy=True
    )


def test_datum_sync_init__transform() -> None:
    """Initialize with a transformer object"""
    transform = Transformer.from_crs(crs_from=CRS.from_epsg(4326), crs_to=CRS.from_epsg(4269), always_xy=True)
    syncer = DatumSync(transform=transform)
    assert syncer.transform == transform


# TODO
def test_transformer_group() -> None:
    """"""
