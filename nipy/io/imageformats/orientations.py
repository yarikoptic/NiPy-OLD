''' Utilities for calculating and applying affine orientations '''

import numpy as np
import numpy.linalg as npl


def io_orientation(affine):
    ''' Return orientation of input axes in terms of output axes
    for an affine transformation from m dimensions to n dimensions.

    The calculated orientations can be used to transform associated
    arrays to best match the output orientations. If n > m,
    then some of the output axes should be considered dropped
    in this orientation.

    Parameters
    ----------
    affine : (n+1,m+1) ndarray-like

    Returns
    -------
    orientations : (n,2) ndarray
       one row per input axis, where the first value in each row is the
       closest corresponding output axis, and the second value is 1 if
       the input axis is in the same direction as the corresponding
       output axis, , and -1 if it is in the opposite direction, to the
       corresponding output axis.
       if a row is [np.nan, np.nan], which can happen when n > m,
       then this row should be considered dropped.

    '''
    affine = np.asarray(affine)
    n, m = affine.shape[0]-1, affine.shape[1]-1
    # extract the underlying rotation matrix
    RZS = affine[:n,:m]
    zooms = np.sqrt(np.sum(RZS * RZS, axis=0))
    RS = np.dot(RZS, np.diag(zooms))

    # Transform below is polar decomposition, returning the closest
    # shearless matrix R to RS (XXX is "shearless" the right term here?)

    P, S, Qs = npl.svd(RS)

    # Threshold the singular values to 
    # determine the rank. 
    # XXX is this tolerance sufficient?
    keep = (S/S.max() > 1.0e-12)
    R = np.dot(P[:,keep], Qs[keep])

    # the matrix R is such that np.dot(R,R.T) is projection onto
    # the columns of P[:,keep] and np.dot(R.T,R) is projection onto
    # the rows of Qs[keep].

    # R (== np.dot(R, np.eye(3))) gives rotation of the unit input
    # vectors to output coordinates.  Therefore, the row index of abs max
    # R[:,N], is the output axis changing most as input
    # axis N changes.  In case there are ties, we choose the axes
    # iteratively, removing used axes from consideration as we go

    ornt = np.ones((n,2), dtype=np.int8)*np.nan

    for in_ax in range(m):
        col = R[:,in_ax]
        if not np.alltrue(np.equal(col, 0)):
            out_ax = np.argmax(np.abs(col))
            ornt[in_ax,0] = out_ax
            assert col[out_ax] != 0
            if col[out_ax] < 0:
                ornt[in_ax,1] = -1
            else:
                ornt[in_ax,1] = 1
            # remove the identified axis from further consideration, by
            # zeroing out the corresponding row in R
            R[out_ax,:] = 0
    return ornt

def _ornt_to_affine(orientations):
    ''' Create affine transformation matrix determined by orientations.
    This transformation will simply flip and possibly drop some
    coordinates.

    Parameters
    ----------
    orientations : (n,2) ndarray
       one row per input axis, where the first value in each row is the
       closest corresponding output axis, and the second value is 1 if
       the input axis is in the same direction as the corresponding
       output axis, , and -1 if it is in the opposite direction, to the
       corresponding output axis.
       if a row has first entry np.nan,
       then this axis is dropped from the output.

    Returns
    -------
    affine : (m+1,n+1) ndarray
       matrix representing flipping / dropping axes. m is equal to the 
       number of rows of orientations[:,0] that are not np.nan

    '''
    ornt = np.asarray(orientations)
    n = ornt.shape[0]
    keep = ~np.isnan(ornt[:,1])

    # these are the coordinate axes that do have a matching
    # output column in the orientation

    # that is, if the 2nd row is [np.nan, np.nan]
    # then the orientation indicates that no output axes
    # of an affine with this orientation matches the 2nd
    # coordinate axis. this would happen if the 2nd
    # row of the affine that generated ornt was [0,0,0,*]

    axes_kept = np.arange(n)[keep] 
    
    m = keep.sum(0)

    # the matrix P represents the affine transform
    # impled by ornt. if all entries of ornt
    # are not np.nan, then P is square 
    # otherwise it has more columns than rows
    # indicating some coordinates were dropped

    P = np.zeros((m+1,n+1))
    P[-1,-1] = 1
    for idx in range(m):
        axs, flip = ornt[axes_kept[idx]]
        P[idx, axs] = flip
    return P


def apply_orientation(arr, ornt):
    ''' Apply transformations implied by `ornt` to the first
    n axes of the array `arr`

    Parameters
    ----------
    arr : array-like of data with ndim >= n
    ornt : (n,2) orientation array
       orientation transform. ``ornt[N,1]` is flip of axis N of the
       array implied by `shape`, where 1 means no flip and -1 means
       flip.  For example, if ``N==0`` and ``ornt[0,1] == -1``, and
       there's an array ``arr`` of shape `shape`, the flip would
       correspond to the effect of ``np.flipud(arr)``.  ``ornt[:,0]`` is
       the transpose that needs to be done to the implied array, as in
       ``arr.transpose(ornt[:,0])``

    Returns
    -------
    t_arr : ndarray of data 
       array `arr` transformed according to ornt

    '''

    t_arr = np.asarray(arr)
    ornt = np.asarray(ornt)
    n = ornt.shape[0]
    assert t_arr.ndim >= n
    # no coordinates can be dropped for applying the orientations
    assert not np.any(np.isnan(ornt[:,0]))

    shape = t_arr.shape
    # apply ornt transformations
    for ax, flip in enumerate(ornt[:,1]):
        if flip == -1:
            t_arr = flip_axis(t_arr, axis=ax)
    full_transpose = np.arange(t_arr.ndim)
    full_transpose[:n] = ornt[:,0]
    t_arr = t_arr.transpose(full_transpose)
    return t_arr

def orientation_affine(ornt, shape):
    ''' Affine transform resulting from transforms implied in `ornt`

    Imagine you have an array ``arr`` of shape `shape`, and you apply the
    transforms implied by `ornt` (more below), to get ``tarr``.
    ``tarr`` may have a different shape ``shape_prime``.  This routine
    returns the affine that will take a array coordinate for ``tarr``
    and give you the corresponding array coordinate in ``arr``.  

    Parameters
    ----------
    ornt : (n,2) ndarray
       orientation transform. ``ornt[N,1]` is flip of axis N of the
       array implied by `shape`, where 1 means no flip and -1 means
       flip.  For example, if ``N==0`` and ``ornt[0,1] == -1``, and
       there's an array ``arr`` of shape `shape`, the flip would
       correspond to the effect of ``np.flipud(arr)``.  ``ornt[:,0]`` is
       the transpose that needs to be done to the implied array, as in
       ``arr.transpose(ornt[:,0])``

    shape : length n sequence
       shape of array you may transform with `ornt`

    Returns
    -------
    transformed_affine : (n+1,n+1) ndarray
       An array ``arr`` (shape `shape`) might be transformed according
       to `ornt`, resulting in a transformed array ``tarr``.
       `transformed_affine` is the transform that takes you from array
       coordinates in ``tarr`` to array coordinates in ``arr``.
    '''
    ornt = np.asarray(ornt)
    n = ornt.shape[0]
    shape = np.array(shape)[:n]
    # ornt implies a flip, followed by a transpose.   We need the affine
    # that inverts these.  Thus we need the affine that first undoes the
    # effect of the transpose, then undoes the effects of the flip.
    reversed_ordering = np.argsort(ornt[:,0])
    undo_reorder = np.eye(n+1)[list(reversed_ordering) + [n],:]
    undo_flip = np.diag(list(ornt[:,1]) + [1.0])
    center_trans = -(shape-1) / 2.0
    undo_flip[:n,n] = (ornt[:,1] * center_trans) - center_trans
    return np.dot(undo_flip, undo_reorder)

def flip_axis(arr, axis=0):
    ''' Flip contents of `axis` in array `arr`

    ``flip_axis`` is the same transform as ``np.flipud``, but for any
    axis.  For example ``flip_axis(arr, axis=0)`` is the same transform
    as ``np.flipud(arr)``, and ``flip_axis(arr, axis=1)`` is the same
    transform as ``np.fliplr(arr)``

    Parameters
    ----------
    arr : array-like
    axis : int, optional
       axis to flip.  Default `axis` == 0

    Returns
    -------
    farr : array
       Array with axis `axis` flipped

    Examples
    --------
    >>> a = np.arange(6).reshape((2,3))
    >>> a
    array([[0, 1, 2],
           [3, 4, 5]])
    >>> flip_axis(a, axis=0)
    array([[3, 4, 5],
           [0, 1, 2]])
    >>> flip_axis(a, axis=1)
    array([[2, 1, 0],
           [5, 4, 3]])
    '''
    arr = np.asanyarray(arr)
    arr = arr.swapaxes(0, axis)
    arr = np.flipud(arr)
    return arr.swapaxes(axis, 0)


