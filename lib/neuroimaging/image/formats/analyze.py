import struct, os, sys, numpy, string, types
import numpy as N
from path import path
from neuroimaging.data import DataSource
from neuroimaging.reference.axis import VoxelAxis, RegularAxis, space, spacetime
from neuroimaging.reference.coordinate_system import VoxelCoordinateSystem, DiagonalCoordinateSystem
from neuroimaging.reference.mapping import Affine, IdentityMapping
import neuroimaging.reference.mapping as mapping
from neuroimaging.reference.grid import SamplingGrid, fromStartStepLength, python2matlab, matlab2python
from neuroimaging.image.formats import BinaryHeaderAtt, BinaryHeaderValidator
import enthought.traits as traits

_byteorder_dict = {'big':'>', 'little':'<'}

ANALYZE_Byte = 2
ANALYZE_Short = 4
ANALYZE_Int = 8
ANALYZE_Float = 16
ANALYZE_Double = 64

datatypes = {
  ANALYZE_Byte:(numpy.UInt8, 1),
  ANALYZE_Short:(numpy.Int16, 2),
  ANALYZE_Int:(numpy.Int32, 4),
  ANALYZE_Float:(numpy.Float32, 4),
  ANALYZE_Double:(numpy.Float64, 8)}

##############################################################################
class ANALYZE(traits.HasTraits):
    """
    A class to read and write ANALYZE format images. 

    >>> from BrainSTAT import *
    >>> from numpy import *
    >>> test = VImage(testfile('test.img'))
    >>> check = VImage(test)
    >>> print int(add.reduce(check.readall().flat))
    -11996
    >>> print check.shape, test.shape
    (68, 95, 79) (68, 95, 79)

    >>> test = VImage('http://nifti.nimh.nih.gov/nifti-1/data/zstat1.nii.gz')
    >>> new = test.tofile('test.img')
    >>> print new.shape
    (21, 64, 64)
    >>> print new.ndim
    3
    >>> new.view()
    """
    # header fields
    sizeof_hdr = BinaryHeaderAtt('i', seek=0, value=348)
    data_type = BinaryHeaderAtt('10s', seek=4, value=' '*10)
    db_name = BinaryHeaderAtt('18s', seek=14, value=' '*18)
    extents = BinaryHeaderAtt('i', seek=32, value=0)
    session_error = BinaryHeaderAtt('h', seek=36, value=0)
    regular = BinaryHeaderAtt('s', seek=38, value='r')
    hkey_un0 = BinaryHeaderAtt('s', seek=39, value='0')
    dim = BinaryHeaderAtt('8h', seek=40, value=(4,91,109,91,1,0,0,0))
    vox_units = BinaryHeaderAtt('4s', seek=56, value='mm  ')
    calib_units = BinaryHeaderAtt('8s', seek=60, value=' '*8)
    unused1 = BinaryHeaderAtt('h', seek=68, value=0)
    datatype = BinaryHeaderAtt('h', seek=70, value=16)
    bitpix = BinaryHeaderAtt('h', seek=72, value=8)
    dim_un0 = BinaryHeaderAtt('h', seek=74, value=0)
    pixdim = BinaryHeaderAtt('8f', seek=76, value=(0.,2.,2.,2.,)+(0.,)*4)
    vox_offset = BinaryHeaderAtt('f', seek=108, value=0.)
    funused1 = BinaryHeaderAtt('f', seek=112, value=1.)
    funused2 = BinaryHeaderAtt('f', seek=116, value=0.)
    funused3 = BinaryHeaderAtt('f', seek=120, value=0.)
    calmax = BinaryHeaderAtt('f', seek=124, value=0.)
    calmin = BinaryHeaderAtt('f', seek=128, value=0.)
    compressed = BinaryHeaderAtt('i', seek=132, value=0)
    verified = BinaryHeaderAtt('i', seek=136, value=0)
    glmax = BinaryHeaderAtt('i', seek=140, value=0)
    glmin = BinaryHeaderAtt('i', seek=144, value=0)
    descrip = BinaryHeaderAtt('80s', seek=148, value=' '*80)
    auxfile = BinaryHeaderAtt('24s', seek=228, value='none' + ' '*20)
    orient = BinaryHeaderAtt('B', seek=252, value=0)
    origin = BinaryHeaderAtt('5H', seek=253, value=(46,64,37,0,0))
    generated = BinaryHeaderAtt('10s', seek=263, value=' '*10)
    scannum = BinaryHeaderAtt('10s', seek=273, value=' '*10)
    patient_id = BinaryHeaderAtt('10s', seek=283, value=' '*10)
    exp_date = BinaryHeaderAtt('10s', seek=293, value=' '*10)
    exp_time = BinaryHeaderAtt('10s', seek=303, value=' '*10)
    hist_un0 = BinaryHeaderAtt('3s', seek=313, value=' '*3)
    views = BinaryHeaderAtt('i', seek=316, value=0)
    vols_added = BinaryHeaderAtt('i', seek=320, value=0)
    start_field = BinaryHeaderAtt('i', seek=324, value=0)
    field_skip = BinaryHeaderAtt('i', seek=328, value=0)
    omax = BinaryHeaderAtt('i', seek=332, value=0)
    omin = BinaryHeaderAtt('i', seek=336, value=0)
    smax = BinaryHeaderAtt('i', seek=340, value=0)
    smin = BinaryHeaderAtt('i', seek=344, value=0)

    # file extensions recognized by this format
    extensions = ('.img', '.hdr', '.mat')

    # file, mode, datatype
    memmapped = traits.true
    filename = traits.Str()
    filebase = traits.Str()
    mode = traits.Trait('r', 'w', 'r+')
    _mode = traits.Trait(['rb', 'wb', 'rb+'])
    byteorder = traits.Trait(['big', 'little'])
    bytesign = traits.Trait(['>', '<'])

    # Use mat file if it's there?
    # This will cause a problem for 4d files occasionally
    usematfile = traits.true

    # Ignore the origin as FSL does
    # This is __EQUIVALENT_TO__ setting origin=(1,)*5
    ignore_origin = traits.false

    # Use abs(pixdim)?
    abs_pixdim = traits.false

    # Try to squeeze 3d files?
    squeeze = traits.true

    # Vector axis?
    nvector = traits.Int(-1)

    # grid
    grid = traits.Any()

    clobber = traits.false

    #-------------------------------------------------------------------------
    def __init__(self, filename=None, datasource=DataSource(), **keywords):
        self.datasource = datasource
        self.filebase = filename and os.path.splitext(filename)[0] or None
        self.hdrattnames = [name for name in self.trait_names() \
          if isinstance(self.trait(name).handler, BinaryHeaderValidator)]
        if filename: self.readheader(self.hdrfilename())
        traits.HasTraits.__init__(self, **keywords)

        if self.mode is 'w':
            self._dimfromgrid(keywords['grid'])
            self.writeheader()
            self.getdtype()

            # create empty file

            from neuroimaging.image.utils import writebrick
            utils.writebrick(file(self.imgfilename(), 'w'),
                             (0,)*self.ndim,
                             N.zeros(self.grid.shape, N.Float),
                             self.grid.shape,
                             byteorder=self.byteorder,
                             outtype = self.typecode)

        self.ndim = self.dim[0]
        
        if self.ignore_origin:
            self.origin = [1]*5

        if self.abs_pixdim:
            self.pixdim = [N.fabs(pixd) for pixd in self.pixdim]

        if self.ndim == 3:
            axisnames = space[::-1]
            origin = self.origin[0:3]
            step = self.pixdim[1:4]
            shape = self.dim[1:4]
        elif self.ndim == 4 and self.nvector <= 1:
            axisnames = space[::-1] + ['time']
            origin = tuple(self.origin[0:3]) + (1,)
            step = tuple(self.pixdim[1:5]) 
            shape = self.dim[1:5]
            if self.squeeze:
                if self.dim[4] == 1:
                    origin = origin[0:3]
                    step = step[0:3]
                    axisnames = axisnames[0:3]
                    shape = self.dim[1:4]
        elif self.ndim == 4 and self.nvector > 1:
            axisnames = ['vector_dimension'] + space[::-1]
            origin = (1,) + self.origin[0:3]
            step = (1,) + tuple(self.pixdim[1:4])  
            shape = self.dim[1:5]
            if self.squeeze:
                if self.dim[1] == 1:
                    origin = origin[1:4]
                    step = step[1:4]
                    axisnames = axisnames[1:4]
                    shape = self.dim[2:5]

        ## Setup affine transformation
        self.grid = fromStartStepLength(names=axisnames,
                                        shape=shape,
                                        step=step,
                                        start=-N.array(origin)*step)

        if self.usematfile: self.grid.transform(self.readmat())

        # assume .mat matrix uses FORTRAN indexing
        self.grid = matlab2python(self.grid)

        if self.memmapped:
            self.datasource.open(self.imgfilename())
            imgfilename = self.datasource.filename(self.imgfilename())
            mode = self.mode in ('r+', 'w') and "r+" or self.mode
            self.memmap = N.memmap(imgfilename, dtype=self.dtype,
                shape=tuple(self.grid.shape), mode=mode)

    #-------------------------------------------------------------------------
    def __str__(self):
        value = ''
        for trait in self.hdrattnames:
            value = value + '%s:%s=%s\n' % (self.filebase, trait, str(getattr(self, trait)))
        return value

    #-------------------------------------------------------------------------
    def readheader(self, hdrfilename):
        hdrfile = self.datasource.open(hdrfilename)

        for traitname in self.hdrattnames:
            trait = self.trait(traitname)
            if hasattr(trait.handler, 'bytesign') and hasattr(self, 'bytesign'):
                trait.handler.bytesign = self.bytesign
            value = trait.handler.read(hdrfile)
            setattr(self, traitname, value)

        self.typecode, self.byte = datatypes[self.datatype]
        hdrfile.close()

    #-------------------------------------------------------------------------
    def _datatype_changed(self):
        ## TODO / WARNING, datatype is not checked very carefully...

        if self.datatype == ANALYZE_Byte:
            self.bitpix = 8
            self.glmin = 0
            self.glmax = 255
            self.funused1 = abs(self.calmin) / 255
        elif self.datatype == ANALYZE_Short: 
            self.bitpix = 16
            self.funused1 = max(abs(self.calmin), abs(self.calmax)) / (2.0**15-1)
            self.glmin = round(self.funused1 * self.calmin)
            self.glmax = round(self.funused1 * self.calmax)
        elif self.datatype == ANALYZE_Int: 
            self.bitpix = 32
            self.funused1 = max(abs(self.calmin), abs(self.calmax)) / (2.0**31-1)
            self.glmin = round(self.funused1 * self.calmin)
            self.glmax = round(self.funused1 * self.calmax)
        elif self.datatype == ANALYZE_Float:
            self.bitpix = 32
            self.funused1 = 1
            self.glmin = 0
            self.glmax = 0
        elif self.datatype == ANALYZE_Double:
            self.bitpix = 64
            self.funused1 = 1
            self.glmin = 0
            self.glmax = 0
        else:
            raise ValueError, 'invalid datatype'

    #-------------------------------------------------------------------------
    def writeheader(self, hdrfile=None):

        if hdrfile is None:
            hdrfilename = self.hdrfilename()
            if self.clobber or not os.path.exists(self.hdrfilename()):
                hdrfile = file(hdrfilename, 'wb')
            else:
                raise ValueError, 'error writing %s: clobber is False and hdrfile exists' % hdrfilename

        for traitname in self.hdrattnames:
            trait = self.trait(traitname)
            trait.handler.bytesign = self.bytesign

            if hasattr(trait.handler, 'seek'):
                trait.handler.write(getattr(self, traitname), outfile=hdrfile)

        hdrfile.close()

    #-------------------------------------------------------------------------
    def _byteorder_changed(self):
        self.bytesign = {'big':'>', 'little':'<'}[self.byteorder]

    #-------------------------------------------------------------------------
    def _bytesign_changed(self):
        self.byteorder = {'>':'big', '<':'little'}[self.bytesign]

    #-------------------------------------------------------------------------
    def _filebase_changed(self):
        try:
            hdrfile = self.datasource.open(self.hdrfilename())
            if self.mode in ['r', 'r+']:
                self.byteorder, self.bytesign = guess_endianness(hdrfile)
            else:
                self.byteorder = sys.byteorder 
            hdrfile.close()
        except:
            pass

    #-------------------------------------------------------------------------
    def hdrfilename(self):
        return '%s.hdr' % self.filebase

    #-------------------------------------------------------------------------
    def imgfilename(self):
        return '%s.img' % self.filebase

    #-------------------------------------------------------------------------
    def matfilename(self):
        return '%s.mat' % self.filebase

    #-------------------------------------------------------------------------
    def _grid_changed(self):
        try:
            self.ndim = len(self.grid.shape)
        except:
            pass

    #-------------------------------------------------------------------------
    def _datatype_changed(self):
        self.getdtype()
        
    #-------------------------------------------------------------------------
    def getdtype(self):
        self.typecode, self.byte = datatypes[self.datatype]
        self.dtype = N.dtype(self.typecode)
        self.dtype = self.dtype.newbyteorder(self.byteorder)

    #-------------------------------------------------------------------------
    def _mode_changed(self):
        _modemap = {'r':'rb', 'w':'wb', 'r+': 'rb+'}
        self._mode = _modemap[self.mode]
        
    #-------------------------------------------------------------------------
    def _dimfromgrid(self, grid):
        self.grid = python2matlab(grid)
            
        if not isinstance(self.grid.mapping, Affine):
            raise ValueError, 'error: non-Affine grid in writing out ANALYZE file'

        if mapping.isdiagonal(self.grid.mapping.transform[0:self.ndim,0:self.ndim]):
            _diag = True
        else:
            _diag = False
            self.writemat()

        _dim = [0]*8
        _pixdim = [0.] * 8
        _dim[0] = self.ndim

        for i in range(self.ndim):
            _dim[i+1] = self.grid.shape[i]
            if _diag:
                _pixdim[i+1] = self.grid.mapping.transform[i,i]
            else:
                _pixdim[i+1] = 1.
        self.dim = _dim
        self.pixdim = _pixdim
        if _diag:
            origin = self.grid.mapping.map([0]*self.ndim, inverse=True)
            self.origin = list(origin) + [0]*(5-origin.shape[0])
        if not _diag:
            self.origin = [0]*5
        

    #-------------------------------------------------------------------------
    def __del__(self):
        if self.memmapped and hasattr(self, "memmap"):
            self.memmap.sync()
            del(self.memmap)
        
    #-------------------------------------------------------------------------
    def getslice(self, slice):
        v = self.memmap[slice]
        if self.funused1:
            return v * self.funused1
        else:
            return v

    #-------------------------------------------------------------------------
    def writeslice(self, slice, data):
        if self.funused1:
            _data = data / self.funused1
        else:
            _data = data
        self.memmap[slice] = _data.astype(self.dtype)
        _data.shape = N.product(_data.shape)
        
    #-------------------------------------------------------------------------
    def readmat(self):
        """
        Return affine transformation matrix, if it exists.
        For now, the format is assumed to be a tab-delimited 4 line file.
        Other formats should be added.
        """
        if self.datasource.exists(self.matfilename()):
            return mapping.fromfile(self.datasource.open(self.matfilename()),
                                 input='world',
                                 output='world',
                                 delimiter='\t')
        else:
            if self.ndim == 4:
                names = spacetime[::-1]
            else:
                names = space[::-1]
            return IdentityMapping(self.ndim, input='world', output='world', names=names)

    #-------------------------------------------------------------------------
    def writemat(self, matfile=None):
        """
        Write out the affine transformation matrix.
        """

        if matfile is None:
            matfile = self.matfilename()

        if self.clobber or not path(matfile).exists():
            mapping.tofile(self.grid.mapping, matfile)


#-----------------------------------------------------------------------------
def guess_endianness(hdrfile):
    """
    Try to guess big/little endianness of an ANALYZE file based on dim[0].
    """
    for order, sign in {'big':'>', 'little':'<', 'net':'!'}.items():
        hdrfile.seek(40)
        x = hdrfile.read(2)
        try:
            test = struct.unpack(sign + 'h', x)[0]
            if test in range(1,8):
                return order, sign
        except:
            raise ValueError 
    raise ValueError, 'file format not recognized: endianness test failed'


# plug in as a format creator (see formats.getreader)
reader = ANALYZE
