"""A quick and dirty example of using Mayavi to overlay anatomy and activation.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import numpy as np

from enthought.mayavi import mlab

from fiac_util import load_image_fiac

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

MASK = load_image_fiac('group', 'mask.nii')
AVGANAT = load_image_fiac('group', 'avganat.nii')

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def view_thresholdedT(design, contrast, threshold, inequality=np.greater):
    """
    A mayavi isosurface view of thresholded t-statistics

    Parameters
    ----------

    design: one of ['block', 'event']

    contrast: str
    
    threshold: float

    inequality: one of [np.greater, np.less]

    """

    maska = np.asarray(MASK)
    tmap = np.array(load_image_fiac('group', design, contrast, 't.nii'))
    test = inequality(tmap, threshold)
    tval = np.zeros(tmap.shape)
    tval[test] = tmap[test]

    # XXX make the array axes agree with mayavi2
    avganata = np.array(AVGANAT)
    avganat_iso = mlab.contour3d(avganata * maska, opacity=0.3, contours=[3600],
                               color=(0.8,0.8,0.8))

    avganat_iso.actor.property.backface_culling = True
    avganat_iso.actor.property.ambient = 0.3

    tval_iso = mlab.contour3d(tval * MASK, color=(0.8,0.3,0.3),
                            contours=[threshold])
    return avganat_iso, tval_iso


#-----------------------------------------------------------------------------
# Script entry point
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    # A simple example use case
    design = 'block'
    contrast = 'sentence_0'
    threshold = 0.3
    print 'Starting thresholded view with:'
    print 'Design=',design,'contrast=',contrast,'threshold=',threshold
    view_thresholdedT(design, contrast, threshold)
