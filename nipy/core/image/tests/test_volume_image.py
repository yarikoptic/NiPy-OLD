"""
The base image interface.
"""

import copy

import nose
import numpy as np

from ...transforms.affine_utils import from_matrix_vector
from ...transforms.affine_transform import AffineTransform
from ...transforms.transform import Transform
from ..volume_image import VolumeImage, CompositionError

################################################################################
# Helper function
def rotation(theta, phi):
    """ Returns a rotation 3x3 matrix.
    """
    cos = np.cos
    sin = np.sin
    a1 = np.array([[cos(theta), -sin(theta), 0],
                [sin(theta),  cos(theta), 0],
                [         0,           0, 1]])
    a2 = np.array([[ 1,        0,         0],
                [ 0, cos(phi), -sin(phi)],
                [ 0, sin(phi),  cos(phi)]])
    return np.dot(a1, a2)

def id(x, y, z):
    return x, y, z
    

################################################################################
# Tests
def test_constructor():
    yield np.testing.assert_raises, AttributeError, VolumeImage, None, \
        None, 'foo'
    yield np.testing.assert_raises, ValueError, VolumeImage, None, \
        np.eye(4), 'foo', {}, 'e'


def test_identity_resample():
    """ Test resampling of the VolumeImage with an identity affine.
    """
    shape = (3., 2., 5., 2.)
    data = np.random.randint(0, 10, shape)
    affine = np.eye(4)
    affine[:3, -1] = 0.5*np.array(shape[:3])
    ref_im = VolumeImage(data, affine, 'mine')
    rot_im = ref_im.as_volume_img(affine, interpolation='nearest')
    yield np.testing.assert_almost_equal, data, rot_im.get_data()
    reordered_im = rot_im.xyz_ordered()
    yield np.testing.assert_almost_equal, data, reordered_im.get_data()


def test_downsample():
    """ Test resampling of the VolumeImage with a 1/2 down-sampling affine.
    """
    shape = (6., 3., 6, 2.)
    data = np.random.randint(0, 10, shape)
    affine = np.eye(4)
    ref_im = VolumeImage(data, affine, 'mine')
    rot_im = ref_im.as_volume_img(2*affine, interpolation='nearest')
    downsampled = data[::2, ::2, ::2, ...]
    x, y, z = downsampled.shape[:3]
    np.testing.assert_almost_equal(downsampled, 
                                   rot_im.get_data()[:x, :y, :z, ...])


def test_reordering():
    """ Test the xyz_ordered method of the VolumeImage.
    """
    # We need to test on a square array, as rotation does not change
    # shape, whereas reordering does.
    shape = (5., 5., 5., 2., 2.)
    data = np.random.random(shape)
    affine = np.eye(4)
    affine[:3, -1] = 0.5*np.array(shape[:3])
    ref_im = VolumeImage(data, affine, 'mine')
    # Test with purely positive matrices and compare to a rotation
    for theta, phi in np.random.randint(4, size=(5, 2)):
        rot = rotation(theta*np.pi/2, phi*np.pi/2)
        rot[np.abs(rot)<0.001] = 0
        rot[rot>0.9] = 1
        rot[rot<-0.9] = 1
        b = 0.5*np.array(shape[:3])
        new_affine = from_matrix_vector(rot, b)
        rot_im = ref_im.as_volume_img(affine=new_affine)
        yield np.testing.assert_array_equal, rot_im.affine, \
                                    new_affine
        yield np.testing.assert_array_equal, rot_im.get_data().shape, \
                                    shape
        reordered_im = rot_im.xyz_ordered()
        yield np.testing.assert_array_equal, reordered_im.affine[:3, :3], \
                                    np.eye(3)
        yield np.testing.assert_almost_equal, reordered_im.get_data(), \
                                    data
    
    # Create a non-diagonal affine, and check that we raise a sensible
    # exception
    affine[1, 0] = 0.1
    ref_im = VolumeImage(data, affine, 'mine')
    yield nose.tools.assert_raises, CompositionError, ref_im.xyz_ordered

    # Test flipping an axis
    data = np.random.random(shape)
    for i in (0, 1, 2):
        # Make a diagonal affine with a negative axis, and check that
        # can be reordered, also vary the shape
        shape = (i+1, i+2, 3-i)
        affine = np.eye(4)
        affine[i, i] *= -1
        img = VolumeImage(data, affine, 'mine')
        orig_img = copy.copy(img)
        x, y, z = img.get_world_coords() 
        sample = img.values_in_world(x, y, z)
        img2 = img.xyz_ordered()
        # Check that img has not been changed
        yield nose.tools.assert_true, img == orig_img
        x_, y_, z_ = img.get_world_coords() 
        yield np.testing.assert_array_equal, np.unique(x), np.unique(x_)
        yield np.testing.assert_array_equal, np.unique(y), np.unique(y_)
        yield np.testing.assert_array_equal, np.unique(z), np.unique(z_)
        sample2 = img.values_in_world(x, y, z)
        yield np.testing.assert_array_equal, sample, sample2


def test_eq():
    """ Test copy and equality for VolumeImages.
    """
    import copy
    shape = (4., 3., 5., 2.)
    data = np.random.random(shape)
    affine = np.random.random((4, 4))
    ref_im = VolumeImage(data, affine, 'mine')
    yield nose.tools.assert_equal, ref_im, ref_im
    yield nose.tools.assert_equal, ref_im, copy.copy(ref_im)
    yield nose.tools.assert_equal, ref_im, copy.deepcopy(ref_im)
    # Check that as_volume_img with no arguments returns the same image
    yield nose.tools.assert_equal, ref_im, ref_im.as_volume_img()
    copy_im = copy.copy(ref_im)
    copy_im.get_data()[0, 0, 0] *= -1
    yield nose.tools.assert_not_equal, ref_im, copy_im
    copy_im = copy.copy(ref_im)
    copy_im.affine[0, 0] *= -1
    yield nose.tools.assert_not_equal, ref_im, copy_im
    copy_im = copy.copy(ref_im)
    copy_im.world_space = 'other'
    yield nose.tools.assert_not_equal, ref_im, copy_im
    # Test repr
    yield np.testing.assert_, isinstance(repr(ref_im), str)
    # Test init: should raise exception is not passing in right affine
    yield nose.tools.assert_raises, Exception, VolumeImage, data, \
                np.eye(3, 3), 'mine'


def test_values_in_world():
    """ Test the evaluation of the data in world coordinate.
    """
    shape = (3., 5., 4., 2.)
    data = np.random.random(shape)
    affine = np.eye(4)
    ref_im = VolumeImage(data, affine, 'mine')
    x, y, z = np.indices(ref_im.get_data().shape[:3])
    values = ref_im.values_in_world(x, y, z)
    np.testing.assert_almost_equal(values, data)


def test_resampled_to_img():
    """ Trivial test of resampled_to_img.
    """
    shape = (5., 4., 3., 2.)
    data = np.random.random(shape)
    affine = np.random.random((4, 4))
    ref_im = VolumeImage(data, affine, 'mine')
    yield np.testing.assert_almost_equal, data, \
                ref_im.as_volume_img(affine=ref_im.affine).get_data()
    yield np.testing.assert_almost_equal, data, \
                        ref_im.resampled_to_img(ref_im).get_data()
    other_im = VolumeImage(data, affine, 'other')
    yield nose.tools.assert_raises, CompositionError, \
            other_im.resampled_to_img, ref_im


def test_transformation():
    """ Test transforming images.
    """
    N = 10
    identity1  = Transform('world1', 'world2', id, id) 
    identity2  = AffineTransform('world1', 'world2', np.eye(4)) 
    for identity in (identity1, identity2):
        data = np.random.random((N, N, N))
        img1 = VolumeImage(data=data,
                           affine=np.eye(4),
                           world_space='world1',
                           )
        img2 = img1.composed_with_transform(identity)
        
        yield nose.tools.assert_equal, img2.world_space, 'world2'

        x, y, z = N*np.random.random(size=(3, 10))
        yield np.testing.assert_almost_equal, img1.values_in_world(x, y, z), \
            img2.values_in_world(x, y, z)

        yield nose.tools.assert_raises, CompositionError, \
                img1.composed_with_transform, identity.get_inverse()

        yield nose.tools.assert_raises, CompositionError, \
                img1.resampled_to_img, img2
        
        # Resample an image on itself: it shouldn't change much:
        img  = img1.resampled_to_img(img1)
        yield np.testing.assert_almost_equal, data, img.get_data()


