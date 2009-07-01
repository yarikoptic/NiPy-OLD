''' Tests for loader function '''

import os
import tempfile

from StringIO import StringIO

import numpy as np

import nipy.io.imageformats as nf
import nipy.io.imageformats.analyze as ana
import nipy.io.imageformats.spm99analyze as spm99
import nipy.io.imageformats.spm2analyze as spm2
import nipy.io.imageformats.nifti1 as ni1
import nipy.io.imageformats.loadsave as nils

from nipy.io.imageformats.volumeutils import native_code, swapped_code

from numpy.testing import assert_array_equal, assert_array_almost_equal
from nose.tools import assert_true, assert_equal, assert_raises


def round_trip(img):
    sio = StringIO()
    files = {'header':sio, 'image':sio}
    img.to_files(files)
    sio.seek(0)
    img2 = nf.Nifti1Image.from_files(files)
    return img2

def test_conversion():
    shape = (2, 4, 6)
    affine = np.diag([1, 2, 3, 1])
    for npt in np.float32, np.int16:
        data = np.arange(np.prod(shape), dtype=npt).reshape(shape)
        img = ni1.Nifti1Image(data, affine)
        img.set_data_dtype(npt)
        img2 = spm2.Spm2AnalyzeImage.from_image(img)
        yield assert_array_equal, img2.get_data(), data
        img3 = spm99.Spm99AnalyzeImage.from_image(img)
        yield assert_array_equal, img3.get_data(), data
        img4 = ana.AnalyzeImage.from_image(img)
        yield assert_array_equal, img4.get_data(), data
        img5 = ni1.Nifti1Image.from_image(img4)
        yield assert_array_equal, img5.get_data(), data


def test_save_load_endian():
    shape = (2, 4, 6)
    affine = np.diag([1, 2, 3, 1])
    data = np.arange(np.prod(shape)).reshape(shape)
    # Native endian image
    img = nf.Nifti1Image(data, affine)
    yield assert_equal, img.get_header().endianness, native_code
    img2 = round_trip(img)
    yield assert_equal, img2.get_header().endianness, native_code
    yield assert_array_equal, img2.get_data(), data
    # byte swapped endian image
    bs_hdr = img.get_header().as_byteswapped()
    bs_img = nf.Nifti1Image(data, affine, bs_hdr)
    yield assert_equal, bs_img.get_header().endianness, swapped_code
    yield assert_array_equal, bs_img.get_data(), data
    # Check converting to another image maintains endian
    cbs_img = nf.AnalyzeImage.from_image(bs_img)
    cbs_hdr = cbs_img.get_header()
    yield assert_equal, cbs_hdr.endianness, swapped_code
    cbs_img2 = nf.Nifti1Image.from_image(cbs_img)
    cbs_hdr2 = cbs_img2.get_header()
    yield assert_equal, cbs_hdr2.endianness, swapped_code
    # Try byteswapped round trip
    bs_img2 = round_trip(bs_img)
    bs_data2 = bs_img2.get_data()
    yield assert_equal, bs_data2.dtype.byteorder, swapped_code
    yield assert_equal, bs_img2.get_header().endianness, swapped_code
    yield assert_array_equal, bs_data2, data
    # Now mix up byteswapped data and non-byteswapped header
    mixed_img = nf.Nifti1Image(bs_data2, affine)
    yield assert_equal, mixed_img.get_header().endianness, native_code
    m_img2 = round_trip(mixed_img)
    yield assert_equal, m_img2.get_header().endianness, native_code
    yield assert_array_equal, m_img2.get_data(), data
    

def test_save_load():
    shape = (2, 4, 6)
    npt = np.float32
    data = np.arange(np.prod(shape), dtype=npt).reshape(shape)
    affine = np.diag([1, 2, 3, 1])
    affine[:3,3] = [3,2,1]
    img = ni1.Nifti1Image(data, affine)
    img.set_data_dtype(npt)
    try:
        _, nifn = tempfile.mkstemp('.nii')
        # this somewhat unsafe, because we will make .hdr and .mat files too
        _, sifn = tempfile.mkstemp('.img')
        ni1.save(img, nifn)
        re_img = nils.load(nifn)
        yield assert_true, isinstance(re_img, ni1.Nifti1Image)
        yield assert_array_equal, re_img.get_data(), data
        yield assert_array_equal, re_img.get_affine(), affine
        spm2.save(img, sifn)
        re_img2 = nils.load(sifn)
        yield assert_true, isinstance(re_img2, spm2.Spm2AnalyzeImage)
        yield assert_array_equal, re_img2.get_data(), data
        yield assert_array_equal, re_img2.get_affine(), affine
        spm99.save(img, sifn)
        re_img3 = nils.load(sifn)
        yield assert_true, isinstance(re_img3, spm99.Spm99AnalyzeImage)
        yield assert_array_equal, re_img3.get_data(), data
        yield assert_array_equal, re_img3.get_affine(), affine
        ni1.save(re_img3, nifn)
        re_img = nils.load(nifn)
        yield assert_true, isinstance(re_img, ni1.Nifti1Image)
        yield assert_array_equal, re_img.get_data(), data
        yield assert_array_equal, re_img.get_affine(), affine
    finally:
        os.unlink(nifn)
        os.unlink(sifn)
        os.unlink(sifn[:-4] + '.hdr')
        os.unlink(sifn[:-4] + '.mat')


def test_two_to_one():
    # test going from two to one file in save
    shape = (2, 4, 6)
    npt = np.float32
    data = np.arange(np.prod(shape), dtype=npt).reshape(shape)
    affine = np.diag([1, 2, 3, 1])
    affine[:3,3] = [3,2,1]
    img = ni1.Nifti1Image(data, affine)
    yield assert_equal, img.get_header()['magic'], 'n+1'
    str_io = StringIO()
    files = {'header':str_io, 'image':str_io}
    img.to_files(files)
    yield assert_equal, img.get_header()['magic'], 'n+1'
    yield assert_equal, img.get_header()['vox_offset'], 352
    str_io2 = StringIO()
    files['image'] = str_io2
    img.to_files(files)
    yield assert_equal, img.get_header()['magic'], 'ni1'
    yield assert_equal, img.get_header()['vox_offset'], 0
    # same for from_image
    ana_img = ana.AnalyzeImage.from_image(img)
    yield assert_equal, ana_img.get_header()['vox_offset'], 0
    files = {'header':str_io, 'image':str_io}
    img.to_files(files)
    yield assert_equal, img.get_header()['vox_offset'], 352
    aimg = ana.AnalyzeImage.from_image(img)
    yield assert_equal, aimg.get_header()['vox_offset'], 0
    aimg = spm99.Spm99AnalyzeImage.from_image(img)
    yield assert_equal, aimg.get_header()['vox_offset'], 0
    aimg = spm2.Spm2AnalyzeImage.from_image(img)
    yield assert_equal, aimg.get_header()['vox_offset'], 0
    nfimg = ni1.Nifti1Image.from_image(img)
    yield assert_equal, nfimg.get_header()['vox_offset'], 352


def test_negative_load_save():
    shape = (1,2,5)
    data = np.arange(10).reshape(shape) - 10.0
    affine = np.eye(4)
    hdr = nf.Nifti1Header()
    hdr.set_data_dtype(np.int16)
    img = nf.Nifti1Image(data, affine, hdr)
    str_io = StringIO()
    files = {'header':str_io,'image':str_io}
    img.to_files(files)
    str_io.seek(0)
    re_img = nf.Nifti1Image.from_files(files)
    yield assert_array_almost_equal, re_img.get_data(), data, 4

