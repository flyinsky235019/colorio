from typing import Tuple

import numpy as np
from numpy.typing import ArrayLike

from ._helpers import SpectralData
from ._tools import spectrum_to_xyz100
from .cs import ColorSpace


def _get_surface_gamut_mesh(
    colorspace: ColorSpace, observer: SpectralData, illuminant: SpectralData
) -> Tuple[ArrayLike, ArrayLike]:
    from scipy.spatial import ConvexHull

    # lmbda, illu = illuminant
    values = []

    # Iterate over every possible illuminant input and store it in values
    n = len(illuminant.lmbda_nm)
    data = np.zeros(n)
    # frequency blocks
    values = []
    for width in range(n):
        data[:] = 0.0
        data[:width] = 1.0
        for _ in range(n):
            values.append(
                spectrum_to_xyz100(
                    SpectralData(illuminant.lmbda_nm, data * illuminant.data), observer
                )
            )
            data = np.roll(data, shift=1)
    # Full illuminant
    values.append(spectrum_to_xyz100(illuminant, observer))
    values = np.array(values)

    # scale the values such that the Y-coordinate of the white point (last entry)
    # has value 100.
    values *= 100 / values[-1][1]

    cells = ConvexHull(values).simplices

    if not colorspace.is_origin_well_defined:
        values = values[1:]
        cells = cells[~np.any(cells == 0, axis=1)]
        cells -= 1

    pts = colorspace.from_xyz100(values.T).T
    return pts, cells


def plot_surface_gamut(colorspace, observer, illuminant, show_grid=True):
    import pyvista as pv
    import vtk

    points, cells = _get_surface_gamut_mesh(colorspace, observer, illuminant)
    cells = np.column_stack(
        [np.full(cells.shape[0], cells.shape[1], dtype=cells.dtype), cells]
    )

    # each cell is a VTK_HEXAHEDRON
    celltypes = np.full(len(cells), vtk.VTK_TRIANGLE)

    grid = pv.UnstructuredGrid(cells.ravel(), celltypes, points)
    # grid.plot()

    p = pv.Plotter()
    p.add_mesh(grid)
    if show_grid:
        p.show_grid(
            xlabel=colorspace.labels[0],
            ylabel=colorspace.labels[1],
            zlabel=colorspace.labels[2],
        )
