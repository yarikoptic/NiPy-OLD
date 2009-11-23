''' Test example images '''

from nipy import load_image
from nipy.testing import funcfile, anatfile

from nose.tools import assert_true, assert_false, assert_equal


def test_dims():
    fimg = load_image(funcfile)
    # make sure time dimension is correctly set in affine
    yield assert_equal, fimg.coordmap.affine[3,3], 2.0
    # should follow, but also make sure affine is invertible
    ainv = fimg.coordmap.inverse
    yield assert_false, ainv is None
    
