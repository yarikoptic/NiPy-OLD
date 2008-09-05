"""
Pseudo-package for all of the core symbols from the image object and its reference
system.  Use this module for importing core names into your namespace. For example:
 from neuorimaging.core.api import Image
"""

# Note: The order of imports is important here.
from neuroimaging.core.reference.grid import SamplingGrid

from neuroimaging.core.reference.mapping import Mapping, Affine
from neuroimaging.core.reference.coordinate_system import CoordinateSystem, \
     DiagonalCoordinateSystem
from neuroimaging.core.reference.axis import VoxelAxis

from neuroimaging.core.image.image import Image, merge_images
from neuroimaging.core.image.image import load as load_image
from neuroimaging.core.image.image import save as save_image
from neuroimaging.core.image.image import fromarray

from neuroimaging.core.image.image_list import ImageList

from neuroimaging.core.image.generators import parcels, data_generator, write_data, slice_generator, f_generator, matrix_generator
