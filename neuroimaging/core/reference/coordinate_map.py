"""
Coordinate maps store all the details about how an image translates to
space.  They also provide mechanisms for iterating over that space.
"""

import copy
import warnings

import numpy as np

from neuroimaging.core.reference.coordinate_system import \
    CoordinateSystem, safe_dtype 
from neuroimaging.core.reference.coordinate_system import product as coordsys_product

__docformat__ = 'restructuredtext'

class CoordinateMap(object):
    """A set of input and output CoordinateSystems and a mapping between them.

    For example, the mapping may represent the mapping of an image
    from voxel space (the input coordinates) to real space (the output
    coordinates).  The mapping may be an affine or non-affine
    transformation.

    Attributes
    ----------
    input_coords : ``CoordinateSystem``
        The input coordinate system.
    output_coords : ``CoordinateSystem``
        The output coordinate system.
    mapping : callable
        A callable that maps the input_coords to the output_coords.
    inverse_mapping : callable
        A callable that maps the output_coords to the input_coords.
        Not all mappings have an inverse, in which case
        inverse_mapping is None.
        
    Examples
    --------
    >>> input_coords = CoordinateSystem('ijk')
    >>> output_coords = CoordinateSystem('xyz')
    >>> mni_orig = np.array([-90.0, -126.0, -72.0])
    >>> mapping = lambda x: np.array(x) + mni_orig
    >>> inverse_mapping = lambda x: np.array(x) - mni_orig
    >>> cm = CoordinateMap(mapping, input_coords, output_coords, inverse_mapping)

    Map the first 3 voxel coordinates, along the x-axis, to mni space:

    >>> x = np.array([[0,0,0], [1,0,0], [2,0,0]])
    >>> cm.mapping(x)
    array([[ -90., -126.,  -72.],
           [ -89., -126.,  -72.],
           [ -88., -126.,  -72.]])


    """
    
    def __init__(self, mapping, 
                 input_coords, 
                 output_coords, 
                 inverse_mapping=None):
        """Create a CoordinateMap given the input/output coords and mappings.

        Parameters
        ----------
        mapping : callable
            The mapping between input and output coordinates
        input_coords : ``CoordinateSystem``
            The input coordinate system
        output_coords : ``CoordinateSystem``
            The output coordinate system
        inverse_mapping : callable, optional
            The optional inverse of mapping, with the intention
            being ``x = inverse_mapping(mapping(x))``.  If the
            mapping is affine and invertible, then this is true
            for all x.

        Returns
        -------
        coordmap : CoordinateMap

        """

        # These attrs define the structure of the coordmap.
        self._mapping = mapping
        self.input_coords = input_coords
        self.output_coords = output_coords
        self._inverse_mapping = inverse_mapping

        if not callable(mapping):
            raise ValueError('The mapping must be callable.')

        if inverse_mapping is not None:
            if not callable(inverse_mapping):
                raise ValueError('The inverse_mapping must be callable.')
        self._checkmapping()

    def _getmapping(self):
        return self._mapping
    mapping = property(_getmapping,
                       doc='The mapping from input_coords to output_coords.')

    def _getinverse_mapping(self):
        return self._inverse_mapping
    inverse_mapping = property(_getinverse_mapping,
                               doc='The mapping from output_coords to input_coords')

    def _getinverse(self):
        """
        Return the inverse coordinate map.
        """
        if self._inverse_mapping is not None:
            return CoordinateMap(self._inverse_mapping, 
                                 self.output_coords, 
                                 self.input_coords, 
                                 inverse_mapping=self.mapping)
    inverse = property(_getinverse,
                       doc='Return a new CoordinateMap with the mappings reversed.')

    def _getndim(self):
        return (self.input_coords.ndim, self.output_coords.ndim)
    ndim = property(_getndim,
                    doc='Number of dimensions of input and output coordinates.')

    def _checkshape(self, x):
        """Verify that x has the proper shape for evaluating the mapping

        """

        ndim = self.ndim
        if x.dtype.isbuiltin:
            if x.ndim > 2 or x.shape[-1] != ndim[0]:
                raise ValueError('if dtype is builtin, expecting a 2-d '
                                 'array of shape (*,%d) or '
                                 'a 1-d array of shape (%d,)' % 
                                 (ndim[0], ndim[0]))
        elif x.ndim > 1:
            raise ValueError('if dtype is not builtin, '
                             'expecting 1-d array, or a 0-d array')

    def _checkmapping(self, check_outdtype=True):
        """Verify that the input and output dimensions of self.mapping work.

        """

        input = np.zeros((10, self.ndim[0]),
                         dtype=self.input_coords.coord_dtype)
        output = self.mapping(input)
        if output.dtype != self.output_coords.coord_dtype and check_outdtype:
            warnings.warn('output.dtype != self.output_coords.coord_dtype')
        output = output.astype(self.output_coords.coord_dtype)
        if output.shape != (10, self.ndim[1]):
            raise ValueError('input and output dimensions of mapping do not agree with specified CoordinateSystems')

    def __call__(self, x):
        """Return mapping evaluated at x

        Examples
        --------
        >>> input_cs = CoordinateSystem('ijk')
        >>> output_cs = CoordinateSystem('xyz')
        >>> mapping = lambda x:np.array(x)+1
        >>> inverse = lambda x:np.array(x)-1
        >>> cm = CoordinateMap(mapping, input_cs, output_cs, inverse)
        >>> cm([2,3,4])
        array([3, 4, 5])
        >>> cmi = cm.inverse
        >>> cmi([2,6,12])
        array([ 1,  5, 11])
        >>>                                    
        """
        return self.mapping(x)

    def copy(self):
        """Create a copy of the coordmap.

        Returns
        -------
        coordmap : CoordinateMap

        """

        return CoordinateMap(self.mapping, 
                             self.input_coords,
                             self.output_coords, 
                             inverse_mapping=self.inverse_mapping)

class Affine(CoordinateMap):
    """
    A class representing an affine transformation from an input coordinate system
    to an output coordinate system.
    
    This class has an affine property, which is a matrix representing
    the affine transformation in homogeneous coordinates. 
    This matrix is used to perform mappings,
    rather than having an explicit mapping function. 

    """

    def __init__(self, affine, input_coords, output_coords, dtype=None):
        """
        Return an CoordinateMap specified by an affine transformation in
        homogeneous coordinates.
        

        :Notes:

        The dtype of the resulting matrix is determined
        by finding a safe typecast for the input_coords, output_coords
        and affine.

        """

        dtype = safe_dtype(affine.dtype,
                           input_coords.coord_dtype,
                           output_coords.coord_dtype)

        inaxes = input_coords.coord_names
        outaxes = output_coords.coord_names

        self.input_coords = CoordinateSystem(inaxes,
                                             input_coords.name,
                                             dtype)
        self.output_coords = CoordinateSystem(outaxes,
                                              output_coords.name,
                                              dtype)
        self.affine = affine.astype(dtype)

        if self.affine.shape != (self.ndim[1]+1, self.ndim[0]+1):
            raise ValueError('coordinate lengths do not match affine matrix shape')

    def _getinverse_mapping(self):
        A, b = self.inverse.params
        def _mapping(x):
            value = np.dot(x, A.T)
            value += b
            return value
        return _mapping
    inverse_mapping = property(_getinverse_mapping)

    def copy(self):
        """
        Create a copy of the coordmap.

        :Returns: `CoordinateMap`
        """
        return Affine(self.affine, self.input_coords,
                      self.output_coords)


    def _getmapping(self):
        A, b = self.params
        def _mapping(x):
            value = np.dot(x, A.T)
            value += b
            return value
        return _mapping
    mapping = property(_getmapping)

    def _getinverse(self):
        """
        Return the inverse coordinate map.
        """
        try:
            return Affine(np.linalg.inv(self.affine), self.output_coords, self.input_coords)
        except np.linalg.linalg.LinAlgError:
            pass
    inverse = property(_getinverse)

    def _getparams(self):
        return matvec_from_transform(self.affine)
    params = property(_getparams, doc='Get (matrix, vector) representation of affine.')

    def __call__(self, x):
        A, b = self.params
        value = np.dot(x, A.T)
        value += b
        return value

    @staticmethod
    def from_params(innames, outnames, params):
        """
        Create an `Affine` instance from sequences of innames and outnames.

        :Parameters:
            innames : ``tuple`` of ``string``
                The names of the axes of the input coordinate systems

            outnames : ``tuple`` of ``string``
                The names of the axes of the output coordinate systems

            params : `Affine`, `ndarray` or `(ndarray, ndarray)`
                An affine mapping between the input and output coordinate systems.
                This can be represented either by a single
                ndarray (which is interpreted as the representation of the
                mapping in homogeneous coordinates) or an (A,b) tuple.

        :Returns: `Affine`
        
        :Precondition: ``len(shape) == len(names)``
        
        :Raises ValueError: ``if len(shape) != len(names)``
        """
        if type(params) == type(()):
            A, b = params
            params = transform_from_matvec(A, b)

        ndim = (len(innames) + 1, len(outnames) + 1)
        if params.shape != ndim[::-1]:
            raise ValueError('shape and number of axis names do not agree')
        dtype = params.dtype

        input_coords = CoordinateSystem(innames, "input")
        output_coords = CoordinateSystem(outnames, 'output')
        return Affine(params, input_coords, output_coords)

    @staticmethod
    def from_start_step(innames, outnames, start, step):
        """
        Create an `Affine` instance from sequences of names, start
        and step.

        :Parameters:
            innames : ``tuple`` of ``string``
                The names of the axes of the input coordinate systems

            outnames : ``tuple`` of ``string``
                The names of the axes of the output coordinate systems

            start : ``tuple`` of ``float``
                Start vector used in constructing affine transformation
            step : ``tuple`` of ``float``
                Step vector used in constructing affine transformation

        :Returns: `CoordinateMap`
        
        :Predcondition: ``len(names) == len(start) == len(step)``
        """
        ndim = len(innames)
        if len(outnames) != ndim:
            raise ValueError, 'len(innames) != len(outnames)'

        cmaps = []
        for i in range(ndim):
            A = np.array([[step[i], start[i]],
                          [0, 1]])
            cmaps.append(Affine.from_params([innames[i]], [outnames[i]], A))
        return product(*cmaps)

    @staticmethod
    def identity(names):
        """
        Return an identity coordmap of the given shape.
        
        :Parameters:
            names : ``tuple`` of ``string`` 
                  Names of Axes in output CoordinateSystem

        :Returns: `CoordinateMap` with `CoordinateSystem` input
                  and an identity transform, with identical input and output coords. 
        
        """
        return Affine.from_start_step(names, names, [0]*len(names),
                                      [1]*len(names))

def _rename_coords(coord_names, **kwargs):
    coords = list(coord_names)
    for name, newname in kwargs.items():
        if name in coords:
            coords[coords.index(name)] = newname
        else:
            raise ValueError('coordinate name %s not found.'%name)
    return tuple(coords)


def rename_input(coordmap, **kwargs):
    """
    Rename the input_coords, returning a new CoordinateMap

    >>> input_cs = CoordinateSystem('ijk')
    >>> output_cs = CoordinateSystem('xyz')
    >>> cm = Affine(np.identity(4), input_cs, output_cs)
    >>> print cm.input_coords
    name: '', coord_names: ('i', 'j', 'k'), coord_dtype: float64
    >>> cm2 = rename_input(cm, i='x')
    >>> print cm2.input_coords
    name: '', coord_names: ('x', 'j', 'k'), coord_dtype: float64
    """
    coord_names = _rename_coords(coordmap.input_coords.coord_names, **kwargs)
    input_coords = CoordinateSystem(coord_names, coordmap.input_coords.name,
                                    coordmap.input_coords.coord_dtype)
    return CoordinateMap(coordmap.mapping, input_coords, coordmap.output_coords)

def rename_output(coordmap, **kwargs):
    """
    Rename the output_coords, returning a new CoordinateMap.
    
    >>> input_cs = CoordinateSystem('ijk')
    >>> output_cs = CoordinateSystem('xyz')
    >>> cm = Affine(np.identity(4), input_cs, output_cs)
    >>> print cm.output_coords
    name: '', coord_names: ('x', 'y', 'z'), coord_dtype: float64
    >>> cm2 = rename_output(cm, y='a')
    >>> print cm2.output_coords
    name: '', coord_names: ('x', 'a', 'z'), coord_dtype: float64
    >>>                             
    """
    coord_names = _rename_coords(coordmap.output_coords.coord_names, **kwargs)
    output_coords = CoordinateSystem(coord_names, coordmap.output_coords.name,
                                    coordmap.output_coords.coord_dtype)
    return CoordinateMap(coordmap.mapping, coordmap.input_coords, output_coords)
        
def reorder_input(coordmap, order=None):
    """
    Create a new coordmap with reversed input_coords.
    Default behaviour is to reverse the order of the input_coords.
    If the coordmap has a shape, the resulting one will as well.

    Inputs:
    -------
    order: sequence
         Order to use, defaults to reverse. The elements
         can be integers, strings or 2-tuples of strings.
         If they are strings, they should be in coordmap.input_coords.coord_names.

    Returns:
    --------

    newcoordmap: `CoordinateMap`
         A new CoordinateMap with reversed input_coords.

    >>> input_cs = CoordinateSystem('ijk')
    >>> output_cs = CoordinateSystem('xyz')
    >>> cm = Affine(np.identity(4), input_cs, output_cs)
    >>> print reorder_input(cm, 'ikj').input_coords
    name: '-reordered', coord_names: ('i', 'k', 'j'), coord_dtype: float64
    """
    ndim = coordmap.ndim[0]
    if order is None:
        order = range(ndim)[::-1]
    elif type(order[0]) == type(''):
        order = [coordmap.input_coords.index(s) for s in order]

    newaxes = [coordmap.input_coords.coord_names[i] for i in order]
    newincoords = CoordinateSystem(newaxes, 
                                   coordmap.input_coords.name + '-reordered', 
                                   coord_dtype=coordmap.input_coords.coord_dtype)
    perm = np.zeros((ndim+1,)*2)
    perm[-1,-1] = 1.

    for i, j in enumerate(order):
        perm[j,i] = 1.

    perm = perm.astype(coordmap.input_coords.coord_dtype)
    A = Affine(perm, newincoords, coordmap.input_coords)
    return compose(coordmap, A)

def reorder_output(coordmap, order=None):
    """
    Create a new coordmap with reversed output_coords.
    Default behaviour is to reverse the order of the input_coords.
    
    Inputs:
    -------

    order: sequence
         Order to use, defaults to reverse. The elements
         can be integers, strings or 2-tuples of strings.
         If they are strings, they should be in coordmap.output_coords.coord_names.

    Returns:
    --------
        
    newcoordmap: `CoordinateMap`
         A new CoordinateMap with reversed output_coords.

    >>> input_cs = CoordinateSystem('ijk')
    >>> output_cs = CoordinateSystem('xyz')
    >>> cm = Affine(np.identity(4), input_cs, output_cs)
    >>> print reorder_output(cm, 'xzy').output_coords
    name: '-reordered', coord_names: ('x', 'z', 'y'), coord_dtype: float64
    >>> print reorder_output(cm, [0,2,1]).output_coords.coord_names
    ('x', 'z', 'y')

    >>> newcm = reorder_output(cm, 'yzx')
    >>> newcm.output_coords.coord_names
    ('y', 'z', 'x')

    """

    ndim = coordmap.ndim[1]
    if order is None:
        order = range(ndim)[::-1]
    elif type(order[0]) == type(''):
        order = [coordmap.output_coords.index(s) for s in order]

    newaxes = [coordmap.output_coords.coord_names[i] for i in order]
    newoutcoords = CoordinateSystem(newaxes, coordmap.output_coords.name + '-reordered', coordmap.output_coords.coord_dtype)
    
    perm = np.zeros((ndim+1,)*2)
    perm[-1,-1] = 1.

    for i, j in enumerate(order):
        perm[j,i] = 1.

    perm = perm.astype(coordmap.output_coords.coord_dtype)
    A = Affine(perm, coordmap.output_coords, newoutcoords)
    return compose(A, coordmap)

def product(*cmaps):
    """
    Return the "topological" product of two or more CoordinateMaps.

    Inputs:
    -------
    cmaps : sequence of CoordinateMaps

    Returns:
    --------
    cmap : ``CoordinateMap``

    >>> inc1 = Affine.from_params('i', 'x', np.diag([2,1]))
    >>> inc2 = Affine.from_params('j', 'y', np.diag([3,1]))
    >>> inc3 = Affine.from_params('k', 'z', np.diag([4,1]))

    >>> cmap = product(inc1, inc3, inc2)
    >>> cmap.input_coords.coord_names
    ('i', 'k', 'j')
    >>> cmap.output_coords.coord_names
    ('x', 'z', 'y')
    >>> cmap.affine
    array([[ 2.,  0.,  0.,  0.],
           [ 0.,  4.,  0.,  0.],
           [ 0.,  0.,  3.,  0.],
           [ 0.,  0.,  0.,  1.]])

    """
    ndimin = [cmap.ndim[0] for cmap in cmaps]
    ndimin.insert(0,0)
    ndimin = tuple(np.cumsum(ndimin))

    def mapping(x):
        x = np.asarray(x)
        y = []
        for i in range(len(ndimin)-1):
            cmap = cmaps[i]
            if x.ndim == 2:
                yy = cmaps[i](x[:,ndimin[i]:ndimin[i+1]])
            else:
                yy = cmaps[i](x[ndimin[i]:ndimin[i+1]])
            y.append(yy)
        yy = np.hstack(y)
        return yy

    notaffine = filter(lambda x: not isinstance(x, Affine), cmaps)

    incoords = coordsys_product(*[cmap.input_coords for cmap in cmaps])
    outcoords = coordsys_product(*[cmap.output_coords for cmap in cmaps])

    if not notaffine:

        affine = linearize(mapping, ndimin[-1], step=np.array(1, incoords.coord_dtype))
        return Affine(affine, incoords, outcoords)
    return CoordinateMap(mapping, incoords, outcoords)

def compose(*cmaps):
    """
    Return the composition of two or more CoordinateMaps.

    Inputs:
    -------
    cmaps : sequence of CoordinateMaps

    Returns:
    --------
    cmap : ``CoordinateMap``
         The resulting CoordinateMap has input_coords == cmaps[-1].input_coords
         and output_coords == cmaps[0].output_coords

    >>> cmap = Affine.from_params('i', 'x', np.diag([2.,1.]))
    >>> cmapi = cmap.inverse
    >>> id1 = compose(cmap,cmapi)
    >>> print id1.affine
    [[ 1.  0.]
     [ 0.  1.]]

    >>> id2 = compose(cmapi,cmap)
    >>> id1.input_coords.coord_names
    ('x',)
    >>> id2.input_coords.coord_names
    ('i',)
    >>> 

    """

    def _compose2(cmap1, cmap2):
        forward = lambda input: cmap1.mapping(cmap2.mapping(input))
        if cmap1.inverse is not None and cmap2.inverse is not None:
            backward = lambda output: cmap2.inverse.mapping(cmap1.inverse.mapping(output))
        else:
            backward = None
        return forward, backward

    cmap = cmaps[-1]
    for i in range(len(cmaps)-2,-1,-1):
        m = cmaps[i]
        if m.input_coords == cmap.output_coords:
            forward, backward = _compose2(m, cmap)
            cmap = CoordinateMap(forward, 
                                 cmap.input_coords, 
                                 m.output_coords, 
                                 inverse_mapping=backward)
        else:
            raise ValueError, 'input and output coordinates do not match: input=%s, output=%s' % (`m.input_coords.dtype`, `cmap.output_coords.dtype`)

    notaffine = filter(lambda cmap: not isinstance(cmap, Affine), cmaps)

    if not notaffine:
        affine = linearize(cmap, cmap.ndim[0], step=np.array(1, cmaps[0].output_coords.coord_dtype))
        return Affine(affine, cmap.input_coords,
                      cmap.output_coords)
    return cmap
    
def replicate(coordmap, n, concataxis='concat'):
    """
    Create a CoordinateMap by taking the product
    of coordmap with a 1-dimensional 'concat' CoordinateSystem

    :Parameters:
         coordmap : `CoordinateMap`
                The coordmap to be used
         n : ``int``
                The number of tiems to concatenate the coordmap
         concataxis : ``string``
                The name of the new dimension formed by concatenation
    """
    concat = CoordinateMap.from_affine([concataxis], [concataxis], Affine(np.identity(2)), (n,))
    return product(concat, coordmap)

#TODO: renames this interpolate? And implement interpolation?
def hstack(*cmaps):
    """
    Return a "hstacked" CoordinateMap. That is,
    take the result of a number of cmaps, and return np.hstack(results)
    with an additional first row being the 'concat' axis values.

    If the cmaps are identical
    the resulting map is essentially
    replicate(cmaps[0], len(cmaps)) but the mapping is not Affine.

    Some simple modifications of this function would allow 'interpolation'
    along the 'concataxis'. 

    Inputs:
    -------
    cmaps : sequence of CoordinateMaps
          Each cmap should have the same input_coords and output_coords.

    Returns:
    --------
    cmap : ``CoordinateMap``

    >>> inc1 = Affine.from_params('ab', 'cd', np.diag([2,3,1]))
    >>> inc2 = Affine.from_params('ab', 'cd', np.diag([3,2,1]))
    >>> inc3 = Affine.from_params('ab', 'cd', np.diag([1,1,1]))
    >>> stacked = hstack(inc1, inc2, inc3)

    >>> stacked(np.array([[0,1,2],[1,1,2],[2,1,2], [1,1,2]]).T)
    array([[ 0.,  2.,  6.],
           [ 1.,  3.,  4.],
           [ 2. , 1.,  2.],
           [ 1.,  3.,  4.]])
    >>> 

    """

    # Ensure that they all have the same coordinate systems

    notinput = filter(lambda i: cmaps[i].input_coords != cmaps[0].input_coords, 
                      range(len(cmaps)))
    notoutput = filter(lambda i: cmaps[i].output_coords != cmaps[0].output_coords,
                       range(len(cmaps)))
    if notinput or notoutput:
        raise ValueError("input and output coordinates of each CoordinateMap "
                         "should be the same in order to stack them")

    def mapping(x, return_index=False):
        r = []
        for i in range(x.shape[1]):
            ii = int(x[0,i])
            y = cmaps[ii](x[1:,i])
            r.append(np.hstack([x[0,i], y]))
        return np.vstack(r)

    inaxes = ('stack-input',) + cmaps[0].input_coords.coord_names
    incoords = CoordinateSystem(inaxes, 'stackin-%s' % cmaps[0].input_coords.name)
    outaxes = ('stack-output',) + cmaps[0].output_coords.coord_names
    outcoords = CoordinateSystem(outaxes, 'stackout-%s' % cmaps[0].output_coords.name)
    return CoordinateMap(mapping, incoords, outcoords)

def matvec_from_transform(transform):
    """ Split a tranformation represented in homogeneous
    coordinates into it's matrix and vector components. """
    ndimin = transform.shape[0] - 1
    ndimout = transform.shape[1] - 1
    matrix = transform[0:ndimin, 0:ndimout]
    vector = transform[0:ndimin, ndimout]
    return matrix, vector

def transform_from_matvec(matrix, vector):
    """ Combine a matrix and vector into its representation in homogeneous coordinates. """
    nin, nout = matrix.shape
    t = np.zeros((nin+1,nout+1), matrix.dtype)
    t[0:nin, 0:nout] = matrix
    t[nin,   nout] = 1.
    t[0:nin, nout] = vector
    return t


def linearize(mapping, ndimin, step=np.array(1.), origin=None):
    """
    Given a Mapping of ndimin variables, 
    with an input builtin dtype, return the linearization
    of mapping at origin based on a given step size
    in each coordinate axis.

    If not specified, origin defaults to np.zeros(ndimin, dtype=dtype).
    
    :Inputs: 
        mapping: ``Mapping``
              A function to linearize
        ndimin: ``int``
              Number of input dimensions to mapping
        origin: ``ndarray``
              Origin at which to linearize mapping
        step: ``ndarray``
              Step size, an ndarray with step.shape == ().

    :Returns:
        C: ``ndarray``
            Linearization of mapping in homogeneous coordinates, i.e. 
            an array of size (ndimout+1, ndimin+1) where
            ndimout = mapping(origin).shape[0].

    :Notes: The dtype of the resulting Affine mapping
            will be the dtype of mapping(origin)/step, regardless
            of the input dtype.

    """
    step = np.asarray(step)
    dtype = step.dtype
    if step.shape != ():
        raise ValueError('step should be a scalar value')
    if origin is None:
        origin = np.zeros(ndimin, dtype)
    else:
        if origin.dtype != step.dtype:
            warnings.warn('origin.dtype != step.dtype in function linearize, using step.dtype')
        origin = np.asarray(origin, dtype=step.dtype)
        if origin.shape != (ndimin,):
            raise ValueError('origin.shape != (%d,)' % ndimin)
    b = mapping(origin)

    origin = np.multiply.outer(np.ones(ndimin, dtype), origin)
    y1 = mapping(step*np.identity(ndimin) + origin)
    y0 = mapping(origin)

    ndimout = y1.shape[1]
    C = np.zeros((ndimout+1, ndimin+1), (y0/step).dtype)
    C[-1,-1] = 1
    C[:ndimout,-1] = b
    C[:ndimout,:ndimin] = (y1 - y0).T / step
    return C

