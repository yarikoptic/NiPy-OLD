import numpy as np

from nipy.neurospin.register.iconic_matcher import IconicMatcher
from nipy.neurospin.register.routines import cspline_resample
from nipy.neurospin.register.realign4d import Image4d, realign4d, _resample4d

# Use the brifti image object
from nipy.io.imageformats import Nifti1Image as Image 

def affine_register(source, 
                    target, 
                    similarity='cr',
                    interp='pv',
                    subsampling=None,
                    normalize=None, 
                    search='affine',
                    graduate_search=False,
                    optimizer='powell'):
    
    """
    Three-dimensional affine image registration. 
    
    Parameters
    ----------
    source : image object 
       Source image array 
    target : image object
       Target image array
    similarity : str
       Cost-function for assessing image similarity.  One of 'cc', 'cr',
       'crl1', 'mi', je', 'ce', 'nmi', 'smi', 'custom'.  'cr'
       (correlation ratio) is the default.  See ``routines.pyx``
    interp : str
       Interpolation method.  One of 'pv': Partial volume, 'tri':
       Trilinear, 'rand': Random interpolation.  See
       ``register.iconic_matcher.py`
    subsampling : None or sequence of integers length 3
       subsampling of image in voxels, where None (default) results 
       in [1,1,1], See ``register.iconic_matcher.py``
    normalize : None or ?
       Passed to ``matcher.set_similarity`` in
       ``register.iconic_matcher.py`` - used where?
    search : str
       One of 'affine', 'rigid', 'similarity'; default 'affine'
    graduate_search : {False, True}
       Run registration by doing first 'rigid', then 'similarity', then
       'affine' - if True
    optimizer : str
       One of 'powell', 'simplex', 'conjugate_gradient'
       
    Returns
    -------
    T : source-to-target affine transformation 
        Object that can be casted to a numpy array. 

    """
    matcher = IconicMatcher(source.get_data(), 
                            target.get_data(), 
                            source.get_affine(),
                            target.get_affine())
    if subsampling == None: 
        matcher.set_field_of_view(fixed_npoints=64**3)
    else:
        matcher.set_field_of_view(subsampling=subsampling)
    matcher.set_interpolation(method=interp)
    matcher.set_similarity(similarity=similarity, normalize=normalize)

    # Register
    print('Starting registration...')
    print('Similarity: %s' % matcher.similarity)
    print('Normalize: %s' % matcher.normalize) 
    print('Interpolation: %s' % matcher.interp)

    T = None
    if graduate_search or search=='rigid':
        T = matcher.optimize(method=optimizer, search='rigid')
    if graduate_search or search=='similarity':
        T = matcher.optimize(method=optimizer, search='similarity', start=T)
    if graduate_search or search=='affine':
        T = matcher.optimize(method=optimizer, search='affine', start=T)
    return T


def affine_resample(source, 
                    target, 
                    T, 
                    toresample='source', 
                    dtype=None, 
                    order=3, 
                    use_scipy=False): 
    """
    Image resampling using spline interpolation. 

    Parameters
    ----------
    source : image
    
    target : image

    T : source-to-target affine transform
    """
    Tv = np.dot(np.linalg.inv(target.get_affine()), np.dot(T, source.get_affine()))
    if use_scipy or not order==3: 
        use_scipy = True
        from scipy.ndimage import affine_transform 
    if toresample == 'target': 
        if not use_scipy:
            data = cspline_resample(target.get_data(), 
                                    source.get_shape(), 
                                    Tv, 
                                    dtype=dtype)
        else: 
            data = affine_transform(target.get_data(), 
                                    Tv[0:3,0:3], offset=Tv[0:3,3], 
                                    output_shape=source.get_shape(), 
                                    order=order)
        return Image(data, source.get_affine())
    else:
        if not use_scipy:
            data = cspline_resample(source.get_data(), 
                                    target.get_shape(), 
                                    np.linalg.inv(Tv), 
                                    dtype=dtype)
        else: 
            Tv = np.linalg.inv(Tv)
            data = affine_transform(source.get_data(), 
                                    Tv[0:3,0:3], offset=Tv[0:3,3], 
                                    output_shape=target.get_shape(), 
                                    order=order)
        return Image(data, target.get_affine())



def image4d(im, tr, tr_slices=None, start=0.0, 
            slice_order='ascending', interleaved=False):

    """
    Wrapper function. 
    Returns an Image4d instance. 

    Assumes that the input image referential is 'scanner' and that the
    third array index stands for 'z', i.e. the slice index. 
    """
    return Image4d(im.get_data(), im.get_affine(),
                   tr=tr, tr_slices=tr_slices, start=start,
                   slice_order=slice_order, interleaved=interleaved)


def resample4d(im4d, transforms=None): 
    """
    corr_img = resample4d(im4d, transforms=None)
    """
    return Image(_resample4d(im4d, transforms),
                 im4d.get_affine())
