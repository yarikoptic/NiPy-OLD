# module imports
from nipy.io.imageformats import volumeutils as vu
from nipy.io.imageformats import spm2analyze as spm2
from nipy.io.imageformats import nifti1
from nipy.io.imageformats import minc


def load(filespec, *args, **kwargs):
    ''' Load file given filespec, guessing at file type

    Parameters
    ----------
    filespec : string or file-like
       specification of filename or file to load
    *args
    **kwargs
       arguments to pass to image load function

    Returns
    -------
    img : ``SpatialImage``
       Image of guessed type

    '''
    # Try and guess file type from filename
    if isinstance(filespec, basestring):
        fname = filespec
        for ending in ('.gz', '.bz2'):
            if filespec.endswith(ending):
                fname = fname[:-len(ending)]
                break
        if fname.endswith('.nii'):
            return nifti1.load(filespec, *args, **kwargs)
        if fname.endswith('.mnc'):
            return minc.load(filespec, *args, **kwargs)
    # Not a string, or not recognized as nii or mnc
    try:
        files = nifti1.Nifti1Image.filespec_to_files(filespec)
    except ValueError:
        raise RuntimeError('Cannot work out file type of "%s"' %
                           filespec)
    hdr = nifti1.Nifti1Header.from_fileobj(
        vu.allopen(files['header']),
        check=False)
    magic = hdr['magic']
    if magic in ('ni1', 'n+1'):
        return nifti1.load(filespec, *args, **kwargs)
    return spm2.load(filespec, *args, **kwargs)


def save(img, filespec):
    ''' Save an image to file without changing format'''
    img.to_filespec(filespec)
