"""Functions working with affine transformation matrices.
"""

import numpy as np

def apply_affine(x, y, z, affine):
    """ Apply the affine matrix to the given coordinate.

        Parameters
        ----------
        x: number or ndarray
            The x coordinates
        y: number or ndarray
            The y coordinates
        z: number or ndarray
            The z coordinates
        affine: 4x4 ndarray
            The affine matrix of the transformation
    """
    shape = x.shape
    assert y.shape == shape, 'Coordinate shapes are not equal'
    assert z.shape == shape, 'Coordinate shapes are not equal'
    # Ravel, but avoiding a copy if possible
    x = np.reshape(x, (-1,))
    y = np.reshape(y, (-1,))
    z = np.reshape(z, (-1,))
    
    in_coords = np.c_[x,
                        y,
                        z,
                        np.ones(x.shape)].T
    x, y, z, _ = np.dot(affine, in_coords)
    x = np.reshape(x, shape)
    y = np.reshape(y, shape)
    z = np.reshape(z, shape)
    return x, y, z


def to_matrix_vector(transform):
    """Split a transform into it's matrix and vector components.

    The tranformation must be represented in homogeneous coordinates
    and is split into it's rotation matrix and translation vector
    components.

    Parameters
    ----------
    transform : ndarray
        Transform matrix in homogeneous coordinates.  Example, a 4x4
        transform representing rotations and translations in 3
        dimensions.

    Returns
    -------
    matrix, vector : ndarray
        The matrix and vector components of the transform matrix.  For
        an NxN transform, matrix will be N-1xN-1 and vector will be
        1xN-1.

    See Also
    --------
    from_matrix_vector

    """
    
    ndimin = transform.shape[0] - 1
    ndimout = transform.shape[1] - 1
    matrix = transform[0:ndimin, 0:ndimout]
    vector = transform[0:ndimin, ndimout]
    return matrix, vector


def from_matrix_vector(matrix, vector):
    """Combine a matrix and vector into a homogeneous transform.

    Combine a rotation matrix and translation vector into a transform
    in homogeneous coordinates.
    
    Parameters
    ----------
    matrix : ndarray
        An NxN array representing the rotation matrix.
    vector : ndarray
        A 1xN array representing the translation.

    Returns
    -------
    xform : ndarray
        An N+1xN+1 transform matrix.

    See Also
    --------
    to_matrix_vector

    """
    
    nin, nout = matrix.shape
    t = np.zeros((nin+1,nout+1), matrix.dtype)
    t[0:nin, 0:nout] = matrix
    t[nin,   nout] = 1.
    t[0:nin, nout] = vector
    return t
