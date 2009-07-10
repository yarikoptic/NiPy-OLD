''' Test analyze headers

See test_binary.py for general binary header tests

This - basic - analyze header cannot encode full affines (only
diagonal affines), and cannot do integer scaling.

The inability to do affines raises the problem of whether the image is
neurological (left is left), or radiological (left is right).  In
general this is the problem of whether the affine should consider
proceeding within the data down an X line as being from left to right,
or right to left.

To solve this, we have a ``default_x_flip`` flag that can be True or False.
True means assume radiological.

If the image is 3D, and the X, Y and Z zooms are x, y, and z, then::

    If default_x_flip is True::
        affine = np.diag((-x,y,z,1))
    else:
        affine = np.diag((x,y,z,1))

In our implementation, there is no way of saving this assumed flip
into the header.  One way of doing this, that we have not used, is to
allow negative zooms, in particular, negative X zooms.  We did not do
this because the image can be loaded with and without a default flip,
so the saved zoom will not constrain the affine.
'''

import os
from StringIO import StringIO

import numpy as np

from nipy.io.imageformats.testing import assert_equal, assert_true, assert_false, \
     assert_raises

from numpy.testing import assert_array_equal

from nipy.io.imageformats.volumeutils import HeaderDataError, HeaderTypeError

from nipy.io.imageformats.analyze import AnalyzeHeader, AnalyzeImage
from nipy.io.imageformats.header_ufuncs import read_data, write_data, write_scaled_data

from test_binary import _TestBinaryHeader

data_path, _ = os.path.split(__file__)
data_path = os.path.join(data_path, 'data')
header_file = os.path.join(data_path, 'analyze.hdr')


class TestAnalyzeHeader(_TestBinaryHeader):
    header_class = AnalyzeHeader
    example_file = header_file

    def test_header_size(self):
        yield assert_equal, self.header_class._dtype.itemsize, 348
    
    def test_empty(self):
        hdr = self.header_class()
        yield assert_true, len(hdr.binaryblock) == 348
        yield assert_true, hdr['sizeof_hdr'] == 348
        yield assert_true, np.all(hdr['dim'][1:] == 1)
        yield assert_true, hdr['dim'][0] == 0        
        yield assert_true, np.all(hdr['pixdim'] == 1)
        yield assert_true, hdr['datatype'] == 16 # float32
        yield assert_true, hdr['bitpix'] == 32

    def test_checks(self):
        # Test header checks
        hdr_t = self.header_class()
        def dxer(hdr):
            binblock = hdr.binaryblock
            return self.header_class.diagnose_binaryblock(binblock)
        yield assert_equal, dxer(hdr_t), ''
        hdr = hdr_t.copy()
        hdr['sizeof_hdr'] = 1
        yield assert_equal, dxer(hdr), 'sizeof_hdr should be 348'
        hdr = hdr_t.copy()
        hdr['datatype'] = 0
        yield assert_equal, dxer(hdr), 'data code 0 not supported\nbitpix does not match datatype'
        hdr = hdr_t.copy()
        hdr['bitpix'] = 0
        yield assert_equal, dxer(hdr), 'bitpix does not match datatype'
        for i in (1,2,3):
            hdr = hdr_t.copy()
            hdr['pixdim'][i] = -1
            yield assert_equal, dxer(hdr), 'pixdim[1,2,3] should be positive'

    def test_datatype(self):
        ehdr = self.header_class()
        codes = self.header_class._data_type_codes
        for code in codes.value_set():
            npt = codes.type[code]
            if npt is np.void:
                yield (assert_raises,
                       HeaderDataError,
                       ehdr.set_data_dtype,
                       code)
                continue
            dt = codes.dtype[code]
            ehdr.set_data_dtype(npt)
            yield assert_true, ehdr['datatype'] == code
            yield assert_true, ehdr['bitpix'] == dt.itemsize*8
            ehdr.set_data_dtype(code)
            yield assert_true, ehdr['datatype'] == code
            ehdr.set_data_dtype(dt)
            yield assert_true, ehdr['datatype'] == code

    def test_from_eg_file(self):
        fileobj = open(self.example_file, 'rb')
        hdr = self.header_class.from_fileobj(fileobj, check=False)
        yield assert_equal, hdr.endianness, '>'
        yield assert_equal, hdr['sizeof_hdr'], 348

    def test_orientation(self):
        # Test flips
        hdr = self.header_class()
        yield assert_true, hdr.default_x_flip
        hdr.set_data_shape((3,5,7))
        hdr.set_zooms((4,5,6))
        aff = np.diag((-4,5,6,1))
        aff[:3,3] = np.array([1,2,3]) * np.array([-4,5,6]) * -1
        yield assert_array_equal, hdr.get_base_affine(), aff
        hdr.default_x_flip = False
        yield assert_false, hdr.default_x_flip
        aff[0]*=-1
        yield assert_array_equal, hdr.get_base_affine(), aff


def test_best_affine():
    hdr = AnalyzeHeader()
    hdr.set_data_shape((3,5,7))
    hdr.set_zooms((4,5,6))
    yield assert_array_equal, hdr.get_base_affine(), hdr.get_best_affine()


def test_scaling():
    # Test integer scaling from float
    # Analyze headers cannot do float-integer scaling '''
    hdr = AnalyzeHeader()
    yield assert_true, hdr.default_x_flip
    shape = (1,2,3)
    hdr.set_data_shape(shape)
    hdr.set_data_dtype(np.float32)
    data = np.ones(shape, dtype=np.float64)
    S = StringIO()
    # Writing to float datatype doesn't need scaling
    write_scaled_data(hdr, data, S)
    rdata = read_data(hdr, S)
    yield assert_true, np.allclose(data, rdata)
    # Writing to integer datatype does, and raises an error
    hdr.set_data_dtype(np.int32)
    yield (assert_raises, HeaderTypeError, write_scaled_data,
           hdr, data, StringIO())
    # unless we aren't scaling, in which case we convert the floats to
    # integers and write
    write_data(hdr, data, S)
    rdata = read_data(hdr, S)
    yield assert_true, np.allclose(data, rdata)
    # This won't work for floats that aren't close to integers
    data_p5 = data + 0.5
    write_data(hdr, data_p5, S)
    rdata = read_data(hdr, S)
    yield assert_false, np.allclose(data_p5, rdata)

    
def test_images():
    img = AnalyzeImage(None, None)
    yield assert_equal, img.get_data(), None
    yield assert_equal, img.get_affine(), None
    yield assert_equal, img.get_header(), AnalyzeHeader()
