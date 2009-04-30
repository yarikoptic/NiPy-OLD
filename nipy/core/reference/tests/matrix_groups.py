import numpy as np

from nipy.core.api import CoordinateSystem, Affine
from nipy.core.reference.coordinate_map import compose
from nipy.core.reference.coordinate_map import product as cmap_product

###################################################################################

class Linear(Affine):

    """
    Subclass of Affine that is Linear as opposed to Affine, i.e. the translation is 0.

    It is instantiated with an matrix of shape (ndim,ndim) instead of (ndim+1,ndim+1)
    """
    def _getmatrix(self):
        return self.affine[:-1,:-1]
    matrix = property(_getmatrix)

    def __init__(self, matrix, input_coords, output_coords):
        ndim = matrix.shape[0]
        T = np.identity(ndim+1, dtype=matrix.dtype)
        T[:-1,:-1] = matrix
        Affine.__init__(self, T, input_coords, output_coords)

###################################################################################

class MatrixGroup(Linear):

    """
    A matrix group of linear (not affine) transformations with matrices having a specific dtype.
    """
    dtype = np.float

    def __init__(self, matrix, coords, dtype=None):
        dtype = dtype or self.dtype
        if not isinstance(coords, CoordinateSystem):
            coords = CoordinateSystem(coords, 'space', coord_dtype=dtype)
        else:
            coords = CoordinateSystem(coords.coord_names, 'space', dtype)
        Linear.__init__(self, matrix.astype(dtype), coords, coords)
        if not self.validate():
            raise ValueError('this matrix is not an element of %s'
                             % `self.__class__`)
        if not self.coords.coord_dtype == self.dtype:
            raise ValueError('the input coordinates builtin '
                             'dtype should agree with self.dtype')

    def validate(self, M=None):
        """
        Abstract method:

        Ensure that a given matrix is a valid member of the group
        """
        raise NotImplementedError

    def _getcoords(self):
        return self.input_coords
    coords = property(_getcoords)

    def _getinverse(self):
        cmapi = super(MatrixGroup, self).inverse
        return self.__class__(cmapi.affine[:-1,:-1], self.coords)
    inverse = property(_getinverse)

###################################################################################

class GLC(MatrixGroup):

    dtype = np.complex

    def validate(self, M=None):
        """
        Check that the matrix is invertible.
        """
        if M is None:
            M = self.matrix
        return not np.allclose(np.linalg.det(M), 0)



###################################################################################

class GLR(GLC):
    """
    The general linear group
    """

    dtype = np.float

###################################################################################

class SLR(GLR):

    """
    Special linear group
    """

    def validate(self, M=None):
        if M is None:
            M = self.matrix
        return np.allclose(np.linalg.det(M), 1)


###################################################################################

class O(GLR):
    """
    The orthogonal group
    """

    dtype = np.float

    def validate(self, M=None):
        """
        Check that the matrix is (almost) orthogonal.
        """
        
        if M is None:
            M = self.matrix
        return np.allclose(np.identity(self.ndim[0], dtype=self.dtype), np.dot(M.T, M))

###################################################################################

class SO(O,SLR):
    """
    The special orthogonal group
    """

    dtype = np.float

    def validate(self, M=None):
        """
        Check that the matrix is (almost) orthogonal.
        """
        if M is None:
            M = self.matrix
        return O.validate(self) and np.allclose(np.linalg.det(M), 1)

###################################################################################

class GLZ(GLR):

    """
    Matrices with integer entries and determinant \pm 1
    """

    dtype = np.int

    def __init__(self, matrix, coords):
        """
        Safely round coordmap.mapping.matrix,
        creating a new coordmap first.
        """
        M = np.around(matrix).astype(self.dtype)
        GLR.__init__(self, M, coords, dtype=self.dtype)

    def validate(self):
        """
        Must have determinant  \pm 1

        """
        M = self.matrix
        return np.allclose(np.fabs(np.linalg.det(M)), 1)
###################################################################################

def product(*elements):
    """
    Compute the group product of a set of elements
    """
    notsame = filter(lambda x: type(x) != type(elements[0]), elements)
    if notsame:
        raise ValueError('all elements should be members of the same group')
    composed_mapping = compose(*elements)
    matrix = composed_mapping.affine[:-1,:-1]
    return elements[0].__class__(matrix, elements[0].coords)

###################################################################################

def change_basis(element, bchange_linear):
    """
    Matrices can be thought of as representations of linear mappings
    between two (coordinate-free) vector spaces represented in
    particular bases.

    Hence, a MatrixGroup instance with matrix.shape = (ndim, ndim)
    represents a linear transformation L on a vector space of
    dimension ndim, in a given coordinate system.

    If we change the basis in which we represent L, 
    the matrix that represents L should also change. 

    A change of basis is represented as a mapping between two
    coordinate systems and is also represented by a change of basis
    matrix.  This is expressed in this function as
    bchange_linear.output_coords == element.coords
    
    This function expresses the same transformation L in a different
    basis.

    """

    newcm = compose(bchange_linear.inverse, element, bchange_linear)
    matrix = newcm.affine[:-1,:-1]
    if bchange_linear.output_coords != element.coords:
        raise ValueError('expecting the basis change mapping to have the same output coords as element')
    return element.__class__(matrix, newcm.input_coords)

###################################################################################

def same_transformation(element1, element2, basis_change):
    """
    Matrices can be thought of as representations of linear mappings
    between two (coordinate-free) vector spaces represented in
    particular bases.

    Hence, a MatrixGroup instance with matrix.shape = (ndim, ndim)
    represents a linear transformation L on a vector space of
    dimension ndim, in a given coordinate system.

    This function asks the question:

    Do the two elements of a MatrixGroup (element1, element2)
    represent the same linear mapping if basis_change represents the
    change of basis between the two?

    element1.coords = change_basis(element2, basis_change).coords

    """
    newelement = change_basis(element1, basis_change)
    return np.allclose(newelement.matrix, element2.matrix) and newelement.coords == element2.coords
    
###################################################################################

def product_homomorphism(*elements):
    """
    Given a sequence of elements of the same subclass of MatrixGroup,
    they can be thought of as an element of the topological product,
    which has a natural group structure.

    If all of the elements are of the same subclass, then there is a
    natural group homomorphism from the product space to a larger
    MatrixGroup. The matrices of the elements of the larger group will
    be block diagonal with blocks of the size corresponding to the
    dimensions of each corresponding element.

    This function is that homomorphism.
    """
    notsame = filter(lambda x: type(x) != type(elements[0]), elements)
    if notsame:
        raise ValueError, 'all elements should be members of the same group'

    newcmap = cmap_product(*elements)
    matrix = newcmap.affine[:-1,:-1]
    return elements[0].__class__(matrix, newcmap.input_coords)

