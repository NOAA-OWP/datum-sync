import warnings
from typing import Any

import numpy as np
import pyproj
from pyproj import CRS, Transformer
from pyproj.transformer import TransformerGroup

from datum_sync.exceptions import TransformError, ZConversionWarning

__all__ = ["DatumSync"]


FT_TO_M = 0.3048
M_TO_FT = 3.28084


class DatumSync:
    """A class to convert coordinates between input and output CRS and datum

    Requires network connectivity for some conversions.
    """

    def __init__(
        self,
        crs_input: int | None = None,
        crs_output: int | None = None,
        transform: Transformer = None,
    ) -> None:
        """Instantiates a DatumSync class.

        Turns on network enabled setting to download external grid.
        Must instantiate with either crs_input and crs_output _OR_ transform; but not both.
        Error raised if incorrectly instantiated.

        Args:
            crs_input (int): The input EPSG CRS defined as int (e.g. 4326).
                    Must be specified with crs_output.
            crs_output (int): The input EPSG CRS defined as int (e.g. 5070).
                    Must be specified with crs_input.
            transform (pyproj.Transformer): A pre-defined pyproj transformer.
                    Specified instead of using crs_input and crs_output

        """
        # This will allow transformation grids to be downloaded if they are not included in base package
        # Needed for vertical transform
        # TODO: Download grids a priori with package building; remove network connectivity
        pyproj.network.set_network_enabled(active=True)

        # determine if correct units passed in
        if (
            (transform and crs_input)
            or (transform and crs_output)
            or (not (crs_input and crs_output) and not transform)
        ):
            raise ValueError(
                "CRS/transform input incorretly specified. "
                "Either input crs_in and crs_out OR transform; but not both"
            )

        # define a pyproj transformer if none given
        self.transform = (
            transform
            if transform
            else DatumSync.epsg_to_transform(crs_input=crs_input, crs_output=crs_output)  # type: ignore[arg-type]
        )

    def convert_datum(self, xx: Any, yy: Any, zz: Any = None, z_warn: bool = True) -> tuple:
        """Convert coordinates between input and output EPSG CRS.

        Wraps pyproj transformer. It is designed to be attentive to Z conversions and will warn when
        Z conversions do not happen or if the only difference is between meters <-> feet. Inputs values
        can be of any pyproj transformer accepted class. CRS must be input as EPSG integers.



        Either define crs_input and crs_output OR define transform. Will raise error if incorrectly specified.

        Args:
            xx (Any): Scalar or array. Input x coordinate(s).
            yy (Any): Scalar or array. Input y coordinate(s).
            zz (Any): Scalar or array. Input z coordinate(s).
            z_warn (bool): Flag to check to see if z values were convereted and warn if not. Defaults to True.


        Returns
        -------
            tuple: Transformed coordinates in tuple matching input type

        From pyproj:
        Accepted numeric scalar or array:

            - :class:`int`
            - :class:`float`
            - :class:`numpy.floating`
            - :class:`numpy.integer`
            - :class:`list`
            - :class:`tuple`
            - :class:`array.array`
            - :class:`numpy.ndarray`
            - :class:`xarray.DataArray`
            - :class:`pandas.Series`
        """
        # for transforming 3D coordinates
        if zz is not None:
            # saving to class for checks
            output = self.transform.transform(xx, yy, zz)

            if z_warn:
                self.output = output
                self.zz = zz
                # check if Z was converted; warn if not
                self._check_z_conversion()

                # check if z was only changed between M and FT; warn if so
                self._check_z_units()

                # remove from instance
                self.zz = None
                self.output = None

            return output

        # 2D transformation
        else:
            return self.transform.transform(xx, yy)

    @staticmethod
    def epsg_to_transform(crs_input: int, crs_output: int) -> Transformer:
        """Convert an EPSG CRS defined as an int to a pyproj transformer.

        Args:
            crs_input (int): The input EPSG CRS defined as int (e.g. 4326)
            crs_output (int): The output EPSG CRS defined as int (e.g. 4326)

        Returns
        -------
            Transformer: pyproj transformer
        """
        # This will allow transformation grids to be downloaded if they are not included in base package
        # Needed for vertical transform
        # TODO: Download grids a priori with package building; remove network connectivity
        pyproj.network.set_network_enabled(active=True)

        try:
            crs_in = CRS.from_epsg(crs_input)
            crs_out = CRS.from_epsg(crs_output)
            transform = Transformer.from_crs(crs_from=crs_in, crs_to=crs_out, always_xy=True)

        except Exception as e:
            raise TransformError("Issue creating CRS and transformer. Check if CRS are valid.") from e

        # check that there's actual transformers
        # TODO: re-find the test case that undercovered this issue
        transformer_group = TransformerGroup(crs_from=crs_in, crs_to=crs_out, always_xy=True)
        if len(transformer_group.transformers) == 0:
            raise TransformError("No methods to transform between CRS found. Try another CRS.")

        return transform

    def _check_z_conversion(self) -> None:
        """Checks that an output was converted. This may or may not be intentional"""
        if (np.array(self.output[2], dtype=float) == np.array(self.zz, dtype=float)).all():
            warnings.warn(
                "Z values were not altered. This could be expected. This may be because input and output CRS do not have vertical element.",
                ZConversionWarning,
                stacklevel=2,
            )

    def _check_z_units(self) -> None:
        """Check to see if z units were changed, but no value change happened"""
        if (np.round(np.array(self.output[2]), 2) == np.round(np.array(self.zz) * FT_TO_M, 2)).all() or (
            np.round(np.array(self.output[2]), 2) == np.round(np.array(self.zz) * M_TO_FT, 2)
        ).all():
            warnings.warn(
                "Z values were converted between meters and feet but were not altered."
                " This may be because input and output CRS do not have vertical element.",
                ZConversionWarning,
                stacklevel=2,
            )
