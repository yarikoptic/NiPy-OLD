"""
Package containing core nipy classes.
"""
__docformat__ = 'restructuredtext'

from .volumes.volume_field import VolumeField
from .volumes.volume_img import VolumeImg
from .volumes.volume_grid  import VolumeGrid
from .transforms.transform import Transform, CompositionError
from .transforms.affine_transform import AffineTransform

from nipy.testing import Tester
test = Tester().test
bench = Tester().bench
