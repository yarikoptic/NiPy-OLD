"""
The base image interface.

This defines the nipy image interface.
"""

import numpy as np
from scipy import ndimage

# Local imports
from ..transforms.transform import CompositionError

################################################################################
# class `BaseImage`
################################################################################

class BaseImage(object):
    """ The base image for neuroimaging.

        This object is an ndarray representing a volume, with the first 3 
        dimensions being spatial, that knows how it is mapped to a
        "real-world space", and how it can change real-world coordinate
        system.

        **Attributes**

        :world_space: string 
            World space the data is embedded in. For instance `mni152`.

        :metadata: dictionnary
            Optional, user-defined, dictionnary used to carry around
            extra information about the data as it goes through
            transformations. The Image class does not garanty consistency
            of this information as the data is modified.

        :_data: 
            Private pointer to the data.

        **Notes**

        The data is stored in an undefined way: prescalings might need to
        be applied to it before using it, or the data might be loaded on
        demand. The best practice to access the data is not to access the
        _data attribute, but to use the `get_data` method.
    """
    # XXX: We need to make sure the transform attached has an inverse,
    # elsewhere, we cannot implement a values_in_world.

    #---------------------------------------------------------------------------
    # Public attributes -- BaseImage interface
    #---------------------------------------------------------------------------

    # The name of the reference coordinate system
    world_space = ''

    # User defined meta data
    metadata = dict()

    # XXX: interpolation_order is not a good not: we want
    # 'interpolation_ordertion=None',it could take 'nearest'. The class has 
    # an attribute, that can be used to specify the default behavior, in 
    # case 'None' is passed. This is used for eg label images, or mask.

    #---------------------------------------------------------------------------
    # Private attributes -- BaseImage interface
    #---------------------------------------------------------------------------

    # The data (ndarray)
    _data = None

    #---------------------------------------------------------------------------
    # Public methods -- BaseImage interface
    #---------------------------------------------------------------------------

    def get_data(self):
        """ Return data as a numpy array.
        """
        return np.asarray(self._data)


    def get_lookalike(data):
        """ Returns an image with the same transformation and metadata,
            but different data.

            Parameters
            -----------
            data: ndarray
        """
        # XXX: Horrible name
        raise NotImplementedError


    def get_transform(self):
        """ Returns the transform object associated with the image which is a 
            general description of the mapping from the voxel space to the 
            world space.
            
            Returns
            -------
            transform : nipy.core.Transform object
        """
        raise NotImplementedError


    def resampled_to_img(self, target_image, interpolation_order=3):
        """ Resample the image to be on the same voxel grid than the target 
            image.

            Parameters
            ----------
            target_image : nipy image
                Nipy image onto the voxel grid of which the data will be
                resampled.
            interpolation_order : int, optional
                Order of the spline interplation. If 0, nearest neighboor 
                interpolation is performed.

            Returns
            -------
            resampled_image : nipy_image
                New nipy image with the data resampled.

            Notes
            -----
            Both the target image and the original image should be
            embedded in the same world space.
        """
        my_v2w_transform = self.get_transform()
        # XXX: Transform do not have a 'get_inverse' method yet
        transform_map = \
                target_image.get_transform().get_inverse().composed_with(
                                                    my_v2w_transform)
        target_shape = target_image.get_data().shape[:3]
        target_grid = np.indices(target_shape)
        target_grid = target_grid.reshape((3, -1))
        input_space_grid = transform_map(target_grid)
        interpolated_data = \
                    ndimage.map_coordinates(self.get_data(), 
                                            input_space_grid)
        # XXX: we need a dispatcher pattern or to encode the
        # information in the transform: how do we know that we need to 
        # instantiate a `WarpImage`
        from image import Image as WarpImage
        return WarpImage(interpolated_data, 
                                target_image.coord_map,
                                metadata=self.metadata)


    def resampled_to_affine(self, target_affine=None, interpolation_order=3):
        """ Resample the image to be an affine image.

            Parameters
            ----------
            affine : 4x4 ndarray or 3x3 ndarray
                Affine of the new voxel grid or transform object pointing
                to the new voxel coordinate grid. If a 3x3 ndarray is given, 
                it is considered to be the rotation part of the affine, 
                and the best possible bounding box is calculated.
            interpolation_order : int, optional
                Order of the spline interplation. If 0, nearest-neighboor 
                interpolation is performed.

            Returns
            -------
            resampled_image : nipy AffineImage
                New nipy image with the data resampled in the given
                affine.

            Notes
            -----
            The coordinate system of the image is not changed: the
            returned image points to the same world space.
        """
        # XXX: Docstring to be reworked.
        raise NotImplementedError


    def values_in_world(self, x, y, z, interpolation_order=3):
        """ Return the values of the data at the world-space positions given by 
            x, y, z

            Parameters
            ----------
            x : number or ndarray
                x positions in world space, in other words milimeters
            y : number or ndarray
                y positions in world space, in other words milimeters.
                The shape of y should match the shape of x
            z : number or ndarray
                z positions in world space, in other words milimeters.
                The shape of z should match the shape of x
            interpolation_order : int, optional
                Order of the spline interplation. If 0, nearest neighboor 
                interpolation is performed.

            Returns
            -------
            values : number or ndarray
                Data values interpolated at the given world position.
                This is a number or an ndarray, depending on the shape of
                the input coordinate.
        """
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)
        z = np.atleast_1d(z)
        shape = x.shape
        if not ((x.shape == y.shape) and (x.shape == z.shape)):
            raise ValueError('x, y and z shapes should be equal')
        x = x.ravel()
        y = y.ravel()
        z = z.ravel()
        transform = self.get_transform()
        if hasattr(transform, 'get_inverse'):
            i, j, k = transform.get_inverse().mapping(x, y, z)
        values = ndimage.map_coordinates(self.get_data(), np.c_[i, j, k].T,
                                    order=interpolation_order)
        values = np.reshape(values, shape)
        return values


    def transformed_with(self, w2w_transform):
        """ Change the word space the image is embedded into,
            using the given world to world transform.

            Parameters
            ----------
            w2w_transform : transform object
                The transform object giving the mapping between
                the current world space of the image, and the new
                word space.

            Returns
            --------
            remapped_image : nipy image
                An image containing the same data, expressed
                in the new world space.

            Notes
            -----
            No resampling is done by this function.
        """
        if not w2w_transform.input_world_space == self.world_space:
            raise CompositionError(
                "The transform given does not apply to"
                "the image's world space")
        # XXX: We can see an ugly 'if-then' statement maybe we should be
        # encoding some of that logic in the transform.
        new_v2w_transform = \
                        self.get_transform().composed_with(w2w_transform)
        if hasattr(new_v2w_transform, 'affine'):
            # We need to delay the import until now, to avoid circular
            # imports
            from affine_image import AffineImage
            return AffineImage(self._data, new_v2w_transform.affine, 
                                w2w_transform.output_world_space,
                                metadata=self.metadata)
        else:
            from image import Image as WarpImage
            return WarpImage(self._data, 
                                 new_v2w_transform,
                                 metadata=self.metadata)
 

    #---------------------------------------------------------------------------
    # Private methods
    #---------------------------------------------------------------------------

    # TODO: We need to implement (or check if implemented) hashing,
    # weakref, copy, pickling, and __eq__? 

    def __repr__(self):
        options = np.get_printoptions()
        np.set_printoptions(precision=6, threshold=64, edgeitems=2)
        representation = \
                '%s(\n  data=%s,\n  world_space=%s)' % (
                self.__class__.__name__,
                '\n       '.join(repr(self._data).split('\n')),
                self.world_space)
        np.set_printoptions(**options)
        return representation


