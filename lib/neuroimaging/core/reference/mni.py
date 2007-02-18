"""
A set of reference object which represent the MNI space.
"""

__docformat__ = 'restructuredtext'

from neuroimaging.core.reference.axis import RegularAxis
from neuroimaging.core.reference.coordinate_system import VoxelCoordinateSystem, \
    DiagonalCoordinateSystem
from neuroimaging.core.reference.mapping import Affine



MNI_axes = (
  RegularAxis(name='zspace', length=109, start=-72., step=2.0),
  RegularAxis(name='yspace', length=109, start=-126., step=2.0),
  RegularAxis(name='xspace', length=91, start=-90., step=2.0))
""" The three spatial axes in MNI space """

MNI_voxel = VoxelCoordinateSystem('MNI_voxel', MNI_axes)
""" Standard voxel space coordinate system for MNI template """

MNI_world = DiagonalCoordinateSystem('MNI_world', MNI_axes)
""" Standard real space coordinate system for MNI template """

MNI_mapping = Affine(MNI_world.transform())
""" A mapping between the MNI voxel space and the MNI real space """
