import numpy as np
import numpy.random as nprand
from neuroimaging.testing import *

from neuroimaging.algorithms.kernel_smooth import LinearFilter
from neuroimaging.core.api import Image
from neuroimaging.core.reference.coordinate_map import CoordinateMap

from neuroimaging.algorithms.kernel_smooth import sigma2fwhm, fwhm2sigma

"""
# FIXME: Need to make an automated test for this!
class test_Kernel(TestCase):
    @dec.gui
    import pylab
    from neuroimaging.ui.visualization.viewer import BoxViewer
    def test_smooth(self):
        rho = Image("rho.hdr", repository)
        smoother = LinearFilter(rho.grid)

        srho = smoother.smooth(rho)
        view = BoxViewer(rho)
        view.draw()

        sview = BoxViewer(srho)
        sview.m = view.m
        sview.M = view.M
        sview.draw()
        pylab.show()
"""

class test_SigmaFWHM(TestCase):
    def test_sigma_fwhm(self):
        """
        ensure that fwhm2sigma and sigma2fwhm are inverses of each other        
        """
        fwhm = np.arange(1.0, 5.0, 0.1)
        sigma = np.arange(1.0, 5.0, 0.1)
        assert_almost_equal(sigma2fwhm(fwhm2sigma(fwhm)), fwhm)
        assert_almost_equal(fwhm2sigma(sigma2fwhm(sigma)), sigma)

    @dec.slow
    def test_kernel(self):
        """
        Verify the the convolution with a delta function
        gives the correct answer.

        """

        tol = 0.9999
        sdtol = 1.0e-8
        for i in range(6):
            shape = nprand.random_integers(30,60,(3,))
            ii, jj, kk = nprand.random_integers(11,17, (3,))

            space = ('zspace', 'yspace', 'xspace')
            comap = CoordinateMap.from_start_step(names=space, shape=shape,
                                                step=nprand.random_integers(5,10,(3,))*0.5,
                                                start=nprand.random_integers(5,20,(3,))*0.25)

            signal = np.zeros(shape)
            signal[ii,jj,kk] = 1.
            signal = Image(signal, comap=comap)
    
            kernel = LinearFilter(comap,
                                  fwhm=nprand.random_integers(50,100)/10.)
            ssignal = kernel.smooth(signal)
            ssignal = np.asarray(ssignal)
            ssignal[:] *= kernel.norms[kernel.normalization]

            I = np.indices(ssignal.shape)
            I.shape = (3, np.product(shape))
            i, j, k = I[:,np.argmax(ssignal[:].flat)]

            self.assertTrue((i,j,k) == (ii,jj,kk))

            Z = kernel.comap.mapping(I) - kernel.comap.mapping([[i],[j],[k]])

            _k = kernel(Z)
            _k.shape = ssignal.shape
            self.assertTrue(np.corrcoef(_k[:].flat, ssignal[:].flat)[0,1] > tol)
            self.assertTrue((_k[:] - ssignal[:]).std() < sdtol)
            
            def _indices(i,j,k,axis):
                I = np.zeros((3,20))
                I[0] += i
                I[1] += j
                I[2] += k
                I[axis] += np.arange(-10,10)
                return I

            vx = ssignal[i,j,(k-10):(k+10)]
            vvx = comap.mapping(_indices(i,j,k,2)) - comap.mapping([[i],[j],[k]])
            self.assertTrue(np.corrcoef(vx, kernel(vvx))[0,1] > tol)

            vy = ssignal[i,(j-10):(j+10),k]
            vvy = comap.mapping(_indices(i,j,k,1)) - comap.mapping([[i],[j],[k]])
            self.assertTrue(np.corrcoef(vy, kernel(vvy))[0,1] > tol)

            vz = ssignal[(i-10):(i+10),j,k]
            vvz = comap.mapping(_indices(i,j,k,0)) - comap.mapping([[i],[j],[k]])
            self.assertTrue(np.corrcoef(vz, kernel(vvz))[0,1] > tol)





        


