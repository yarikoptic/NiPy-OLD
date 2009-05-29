import numpy as np

from nipy.modalities.fmri.api import fromimage
from nipy.modalities.fmri.pca import PCA
from nipy.core.api import Image
from nipy.io.api import  load_image
from nipy.testing import funcfile, TestCase, dec

class test_PCA(TestCase):

    def setUp(self):
        self.img = load_image(funcfile)
        self.fmridata = fromimage(self.img)

        frame = self.fmridata[0]
        self.mask = Image(np.greater(np.asarray(frame), 500).astype(np.float64),
                          frame.coordmap)

class test_PCAMask(test_PCA):
    # FIXME: Fix slice_iterator errors in pca module.
    @dec.knownfailure
    def test_PCAmask(self):
        p = PCA(self.fmridata, self.mask)
        p.fit()
        output = p.images(which=range(4))

class test_PCANoMask(test_PCA):
    # FIXME: Fix slice_iterator errors in pca modules.
    @dec.knownfailure
    @dec.slow
    @dec.data
    def test_PCA(self):
        p = PCA(self.fmridata)
        p.fit()
        output = p.images(which=range(4))

# FIXME: Figure out good automated test to replace these graphical tests.
"""
class test_PCAMontageNoMask(test_PCA):
    @dec.slow
    @dec.data
    def test_PCAmontage(self):
        from nipy.modalities.fmri.pca import PCAmontage
        from pylab import savefig
        p = PCAmontage(self.fmridata)
        p.fit()
        output = p.images(which=range(4))
        p.time_series()
        p.montage()
        savefig('image.png')
        os.remove('image.png')

class test_PCAMontageMask(test_PCA):
    @dec.slow
    @dec.data
    def test_PCAmontage_nomask(self):
        from nipy.modalities.fmri.pca import PCAmontage
        from pylab import savefig
        p = PCAmontage(self.fmridata, mask=self.mask)
        p.fit()
        output = p.images(which=range(4))
        p.time_series()
        p.montage()
        savefig('image.png')
        os.remove('image.png')
"""



        


