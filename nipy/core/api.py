"""
Pseudo-package for all of the core symbols from the image object and its
reference system.  Use this module for importing core names into your
namespace.

For example:

>>> from nipy.core.api import Image
"""

# Note: The order of imports is important here.
from .reference.coordinate_system import CoordinateSystem
from .reference.coordinate_map import (CoordinateMap, Affine, compose, 
                                       drop_io_dim, append_io_dim)
from .reference.array_coords import Grid, ArrayCoordMap

from .image.image import Image, merge_images, fromarray, is_image

from .image.image_list import ImageList

from .image.generators import (parcels, data_generator, write_data,
                               slice_generator, f_generator,
                               matrix_generator)

