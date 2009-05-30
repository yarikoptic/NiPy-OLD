import numpy as np

from nipy.testing import *

from nipy.utils.tests.data import datapjoin

from nipy.core.image.image_list import ImageList
from nipy.io.api import load_image



# FIXME: Write valid tests for fmri image list objects.
@dec.knownfailure
def test_image_list():
    img_path = datapjoin("test_fmri.nii.gz")
    ff = load_image(img_path)
    f = ImageList.from_image(ff)

    fl = ImageList([f.frame(i) for i in range(f.shape[0])])
    print type(np.asarray(fl))

    print fl[2:5].__class__
    print fl[2].__class__

## from numpy import asarray
## from nipy.testing funcfile
## from nipy.core.image.image_list import ImageList
## from nipy.modalities.fmri.api import load_image

## funcim = load_image(funcfile)
## ilist = ImageList(funcim)
## print ilist[2:5]

## print ilist[2]

## print asarray(ilist).shape
## print asarray(ilist[4]).shape
