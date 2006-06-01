import types, os

from enthought import traits
import numpy as N
from attributes import readonly, deferto

from neuroimaging import flatten
from neuroimaging.data import DataSource
from neuroimaging.image.formats import getreader
from neuroimaging.reference.grid import SamplingGrid
from neuroimaging.reference.iterators import ParcelIterator, SliceParcelIterator

zipexts = (".gz",".bz2")

##############################################################################
class Image(traits.HasTraits):
    isfile = False
    shape = traits.ListInt()
    fill = traits.Float(0.0)

    #-------------------------------------------------------------------------
    class ArrayImage (object):
        "A simple class to mimic an image file from an array."
        class data (readonly): "internal data array"; implements=N.ndarray
        deferto(data, ("__getitem__","__setitem__"))
        
        def __init__(self, data, grid=None, **extra):
            """
            Create an ArrayImage instance from an array,
            by default assumed to be 3d.

            >>> from numpy import *
            >>> from neuroimaging.image import Image
            >>> z = Image.ArrayImage(zeros((10,20,20)))
            >>> print z.ndim
            3
            """
            self.data = data
            self.shape = self.data.shape
            self.grid = grid and grid or SamplingGrid.identity(self.shape)

        def getslice(self, _slice): return self[_slice]
        def writeslice(self, _slice, data): self[_slice] = data

    #-------------------------------------------------------------------------
    @staticmethod
    def fromurl(url, datasource=DataSource(), mode="r", grid=None,
                clobber=False, **keywords):
        base, ext = os.path.splitext(url.strip())
        if ext in zipexts: url = base
        return getreader(url)(filename=url,
          datasource=datasource, mode=mode, clobber=clobber, grid=grid, **keywords)

    #-------------------------------------------------------------------------
    def __init__(self, image, datasource=DataSource(), **keywords):
        '''
        Create a Image (volumetric image) object from either a file, an
        existing Image object, or an array.
        '''
        traits.HasTraits.__init__(self, **keywords)
        
        # from existing Image
        if isinstance(image, Image):
            self.image = image.image
            self.isfile = image.isfile

        # from array
        elif isinstance(image, N.ndarray) or isinstance(image, N.core.memmap):
            self.isfile = False
            self.image = self.ArrayImage(image, **keywords)

        # from filename or url
        elif type(image) == types.StringType:
            self.isfile = True
            self.image = self.fromurl(image, datasource, **keywords)

        else: raise ValueError("Image input must be a string, array, or another image.")
            
        self.type = type(self.image)

        # Find spatial grid -- this is the one that will be used generally
        self.grid = self.image.grid
        self.shape = list(self.grid.shape)
        self.ndim = len(self.shape)

        # When possible, attach memory-mapped array or array as buffer attr
        if hasattr(self.image, 'memmap'):
            self.buffer = self.image.memmap
        elif isinstance(self.image.data, N.ndarray):
            self.buffer = self.image.data          

    #-------------------------------------------------------------------------
    def __getitem__(self, slice): return self.image[slice]
    def getslice(self, slice): return self[slice]
    def __setitem__(self, slice, data): self.image[slice] = data
    def writeslice(self, slice, data): self[slice] = data

    #-------------------------------------------------------------------------
    def __del__(self):
        if self.isfile:
            try: self.image.close()
            except: pass
        else: del(self.image)

    #-------------------------------------------------------------------------
    def open(self, mode='r'):
        if self.isfile: self.image.open(mode=mode)

    #-------------------------------------------------------------------------
    def close(self):
        if self.isfile:
            try: self.image.close()
            except: pass
        
    #-------------------------------------------------------------------------
    def __iter__(self):
        "Create an iterator over an image based on its grid's iterator."
        iter(self.grid)
        if isinstance(self.grid.iterator, ParcelIterator) or \
           isinstance(self.grid.iterator, SliceParcelIterator):
            self.buffer.shape = N.product(self.buffer.shape)
        return self

    #-------------------------------------------------------------------------
    def compress(self, where, axis=0):
        if hasattr(self, 'buffer'):
            return self.buffer.compress(where, axis=axis)
        else: raise ValueError, 'no buffer: compress not supported'

    #-------------------------------------------------------------------------
    def put(self, data, indices):
        if hasattr(self, 'buffer'):
            return self.buffer.put(data, indices)
        else: raise ValueError, 'no buffer: put not supported'

    #-------------------------------------------------------------------------
    def next(self, value=None, data=None):
        """
        The value argument here is used when, for instance one wants to
        iterate over one image with a ParcelIterator and write out data
        to this image without explicitly setting this image's grid to
        the original image's grid, i.e. to just take the value the
        original image's iterator returns and use it here.
        """
        if value is None: self.itervalue = value = self.grid.next()
        itertype = value.type
        postread = getattr(self, 'postread', None) or (lambda x:x)

        if data is None:
            if itertype is 'slice':
                return postread(N.squeeze(self[value.slice]))
            elif itertype is 'parcel':
                flatten(value.where)
                self.label = value.label
                return postread(self.compress(value.where, axis=0))
            elif itertype == 'slice/parcel':
                return postread(self[value.slice].compress(value.where))
        else:
            if itertype is 'slice':
                self[value.slice] = data
            elif itertype in ('parcel', "slice/parcel"):
                self.put(data, N.nonzero(value.where))

    #-------------------------------------------------------------------------
    def getvoxel(self, voxel):
        if len(voxel) != self.ndim:
            raise ValueError, 'expecting a voxel coordinate'
        return self[voxel]

    #-------------------------------------------------------------------------
    def toarray(self, clean=True, **keywords):
        """
        Return a Image instance that has an ArrayPipe as its image attribute.

        >>> from numpy import *
        >>> from BrainSTAT import *
        >>> test = Image(testfile('anat+orig.HEAD'))
        >>> _test = test.toarray()
        >>> print _test.image.data.shape
        (124, 256, 256)
        >>> test = Image(testfile('test_fmri.img'))
        >>> _test = test.toarray(slice=(2,), grid=test.grid)
        >>> print _test.shape
        (13, 128, 128)
        """
        if self.isfile: self.close()
        if clean:
            _clean = N.nan_to_num
            _data = _clean(self.readall(**keywords))
        else: _data = self.readall(**keywords)
        if hasattr(self, 'postread'): _data = self.postread(_data)
        return Image(_data, grid=self.grid, **keywords)

    #-------------------------------------------------------------------------
    def tofile(self, filename, array=True, clobber=False, **keywords):
        outimage = Image(filename, mode='w', grid=self.grid,
                         clobber=clobber, **keywords)
        if array:
            tmp = self.toarray(**keywords)
            #outimage.image[slice(0,self.grid.shape[0])] = tmp.image.data
            outimage.image[:] = tmp.image.data
        else:
            tmp = iter(self)
            outimage = iter(outimage)
            for dataslice in tmp: outimage.next(data=dataslice)
        outimage.close()
        return outimage

    #-------------------------------------------------------------------------
    def readall(self, clean=False, **keywords): 
        """
        Read an entire Image object, returning a numpy, not another instance of
        Image. By default, it does not read 4d images. Missing values are
        filled in with the value of fill (default=self.fill=0.0).
        """
        try:
            _slice = self.grid.iterator.allslice
        except:
            _slice = slice(0, self.shape[0], 1)
        value = self.image[_slice]
        if clean: value = Image(_clean(value, fill=self.fill))
        return value

    #-------------------------------------------------------------------------
    def check_grid(self, test): return self.grid == test.grid


##############################################################################
class ImageSequenceIterator(traits.HasTraits):
    """
    Take a sequence of images, and an optional grid (which defaults to
    imgs[0].grid) and create an iterator whose next method returns array with
    shapes (len(imgs),) + self.imgs[0].next().shape Very useful for voxel-based
    methods, i.e. regression, one-sample t.
    """
    def __init__(self, imgs, grid=None, **keywords):
        self.imgs = imgs
        if grid is None: self.grid = iter(self.imgs[0].grid)
        else: self.grid = iter(grid)

    def __iter__(self): return self

    def next(self, value=None):
        if value is None: value = self.grid.next()
        v = []
        for i in range(len(self.imgs)):
            v.append(self.imgs[i].next(value=value))
        return N.array(v, N.Float)
