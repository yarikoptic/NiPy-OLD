#!/usr/bin/env python 
"""
This script requires the nipy-data package to run. It is an example of
inter-subject affine registration using two MR-T1 images from the
'sulcal 2000' database acquired at CEA, SHFJ, Orsay, France. The
source is 'ammon' and the target is 'anubis'.

Usage: 
  python affine_matching [criterion][interpolation][optimizer]

  Choices for criterion: 
    cc   -- correlation coefficient 
    cr   -- correlation ratio [DEFAULT]
    crl1 -- correlation ratio, L1 norm version
    mi   -- mutual information
    nmi  -- normalized mutual information
    je   -- joint entropy 
    ce   -- conditional entropy 

  Choices for interpolation method: 
    pv   -- partial volume [DEFAULT]
    tri  -- trilinear
    rand -- random 

  Choices for optimizer: 
    simplex
    powell [DEFAULT]
    conjugate_gradient

Running this script will result in two files being created in the
working directory:

ammon_TO_anubis.nii 
  the source image resampled according to the target coordinate system

ammon_TO_anubis.npz 
  a numpy data file containing the 4x4 matrix that maps the source to 
  the target coordinate system

Author: Alexis Roche, 2009. 
"""

from nipy.neurospin.image_registration import affine_register, affine_resample
from nipy.io.imageformats import load as load_image, save as save_image
from nipy.utils import example_data

from os.path import join
import sys
import time

print('Scanning data directory...')

# Input images are provided with the nipy-data package
source = 'ammon'
target = 'anubis'
source_file = example_data.get_filename('neurospin','sulcal2000','nobias_'+source+'.nii.gz')
target_file = example_data.get_filename('neurospin','sulcal2000','nobias_'+target+'.nii.gz')

# Optional arguments
similarity = 'cr' 
interp = 'pv'
optimizer = 'powell'
normalize = None
if len(sys.argv)>1: 
    similarity = sys.argv[1]
if len(sys.argv)>2: 
    interp = sys.argv[2]
if len(sys.argv)>3: 
    optimizer = sys.argv[3]
if len(sys.argv)>4: 
    normalize = sys.argv[4]

# Print messages
print ('Source brain: %s' % source)
print ('Target brain: %s' % target)
print ('Similarity measure: %s' % similarity)
print ('Optimizer: %s' % optimizer)

# Get data
print('Fetching image data...')
I = load_image(source_file)
J = load_image(target_file)

# Perform affine normalization 
print('Setting up registration...')
tic = time.time()
T = affine_register(I, J, similarity=similarity, interp=interp, normalize=normalize, optimizer=optimizer)
toc = time.time()
print('  Registration time: %f sec' % (toc-tic))


# Resample source image
print('Resampling source image...')
tic = time.time()
It = affine_resample(I, J, T) 
toc = time.time()
print('  Resampling time: %f sec' % (toc-tic))

# Save resampled source
outfile =  source+'_TO_'+target+'.nii'
print ('Saving resampled source in: %s' % outfile)
save_image(It, outfile)

# Save transformation matrix
import numpy as np
np.save(outfile, np.asarray(T))

