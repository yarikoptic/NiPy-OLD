"""
This module defines a class to output estimates
of delays and contrasts of delays.

Liao, C.H., Worsley, K.J., Poline, J-B., Aston, J.A.D., Duncan, G.H.,
Evans, A.C. (2002). \'Estimating the delay of the response in fMRI
data.\' NeuroImage, 16:593-606.

"""

__docformat__ = 'restructuredtext'

import os, fpformat

import numpy as N
import numpy.linalg as L
from scipy.sandbox.models.utils import recipr, recipr0
from scipy.sandbox.models.contrast import Contrast, ContrastResults

from neuroimaging.modalities.fmri import hrf
from neuroimaging.modalities.fmri.protocol import ExperimentalQuantitative
from neuroimaging.modalities.fmri.regression import TContrastOutput 
from neuroimaging.modalities.fmri.utils import LinearInterpolant as interpolant
from neuroimaging.modalities.fmri.fmristat.invert import invertR

from neuroimaging.defines import pylab_def
PYLAB_DEF, pylab = pylab_def()
if PYLAB_DEF:
    from neuroimaging.ui.visualization.multiplot import MultiPlot

class DelayContrast(Contrast):

    Tmin = -100.
    Tmax = 100.

    """
    Specify a delay contrast.

    Delay contrasts are specified by a sequence of functions and weights, the
    functions should NOT already be convolved with any HRF. They will be
    convolved with self.IRF which is expected to be a filter with a canonical
    HRF and its derivative -- defaults to the Glover model.

    Weights should have the same number of columns as len(fns), with each row
    specifying a different contrast.
    """

    def _sequence_call(self, time):
        """
        :Parameters:
            `time` : TODO
                TODO

        :Returns: ``numpy.ndarray``
        """
        return N.array([fn(time) for fn in self._sequence_fn])

    def __init__(self, fns, weights, formula, IRF=None, name='', rownames=[]):
        """
        :Parameters:
            `fns` : TODO
                TODO
            `weights` : TODO
                TODO
            `formula` : TODO
                TODO
            `IRF` : TODO
                TODO
            `name` : string
                TODO
            `rownames` : [string]
                TODO
        """
        if IRF is None:
            self.IRF = canonical
        else:
            self.IRF = IRF

        self.delayflag = True

        self.name = name
        self.formula = formula
        
        self._sequence_fn = fns
        self.fn = self._sequence_call

        self.weights = N.asarray(weights)
        if self.weights.ndim == 1:
            self.weights.shape = (1, self.weights.shape[0])

        if len(self._sequence_fn) != self.weights.shape[1]:
            raise ValueError, 'length of weights does not match number of ' \
                  'terms in DelayContrast'

        term = ExperimentalQuantitative('%s_delay' % self.name, self.fn)
        term.convolve(self.IRF)
        
        Contrast.__init__(self, term, self.formula, name=self.name)

        if rownames == []:
            if name == '':
                raise ValueError, 'if rownames are not specified, name must be specified'
            if self.weights.shape[0] > 1:
                self.rownames = ['%srow%d' % (name, i) for i in
                                 range(self.weights.shape[0])]
            elif self.weights.shape[0] == 1:
                self.rownames = ['']
        else:
            self.rownames = rownames

    def getmatrix(self, time=None):
        """
        :Parameters:
            `time` : TODO
                TODO

        :Returns: ``None``
        """
        Contrast.getmatrix(self, time=time)

        cnrow = self.matrix.shape[0] / 2
        self.effectmatrix = self.matrix[0:cnrow]
        self.deltamatrix = self.matrix[cnrow:]

        self.isestimable(time)

    def isestimable(self, t):
        """
        To estimate the delay, it is assumed that the response contains

        (f ** HRF)(t + delta)

        for each delay model time series 'f'.
        More specifically, it is assumed that

        f(t + delta) = c1 * (f ** HRF)(t) + delta * c2 * (f ** dHRF)(t)

        where HRF and dHRF are the HRFs for this delay contrast.

        This function checks to ensure that the columns

        [(f ** HRF)(t), (f ** dHRF(t))]

        are in the column space of the fMRI regression model.

        :Parameters:
            `t` : TODO
                TODO

        :Returns: ``None``

        :Raises ValueError: if any of the columns are not in the column space
            of the model
        """
        
        D = self.formula(t).T
        pinvD = L.pinv(D)

        C = self.term(t)

        cnrow = C.shape[0] / 2
        effects = C[:cnrow]
        deffects = C[cnrow:]

        for i in range(self.weights.shape[0]):
            for matrix in [effects, deffects]:
                col = N.dot(self.weights[i], matrix)
                colhat = N.dot(D, N.dot(pinvD, col))
                if not N.allclose(col, colhat):
                    if self.weights.shape[0] > 1:
                        name = self.rownames[i]
                    else:
                        name = ''
                    raise ValueError, 'delay contrast %snot estimable' % name


    def _extract_effect(self, results):

        delay = self.IRF.delay

        self.gamma0 = N.dot(self.effectmatrix, results.beta)
        self.gamma1 = N.dot(self.deltamatrix, results.beta)

        nrow = self.gamma0.shape[0]
        self.T0sq = N.zeros(self.gamma0.shape)
        
        for i in range(nrow):
            self.T0sq[i] = (self.gamma0[i]**2 *
                            recipr(results.cov_beta(matrix=self.effectmatrix[i])))

        self.r = self.gamma1 * recipr0(self.gamma0)
        self.rC = self.r * self.T0sq / (1. + self.T0sq)
        self.deltahat = delay.inverse(self.rC)

        self._effect = N.dot(self.weights, self.deltahat)

    def _extract_sd(self, results):

        delay = self.IRF.delay

        self.T1 = N.zeros(self.gamma0.shape)

        nrow = self.gamma0.shape[0]
        for i in range(nrow):
            self.T1[i] = self.gamma1[i] * recipr(N.sqrt(results.cov_beta(matrix=self.deltamatrix[i])))

        a1 = 1 + 1. * recipr(self.T0sq)

        gdot = N.array(([(self.r * (a1 - 2.) *
                          recipr0(self.gamma0 * a1**2)),
                         recipr0(self.gamma0 * a1)] *
                        recipr0(delay.dforward(self.deltahat))))

        Cov = results.cov_beta
        E = self.effectmatrix
        D = self.deltamatrix

        nrow = self.effectmatrix.shape[0]
            
        cov = N.zeros((nrow,)*2 + self.T0sq.shape[1:])

        for i in range(nrow):
            for j in range(i + 1):
                cov[i,j] = (gdot[0,i] * gdot[0,j] * Cov(matrix=E[i],
                                                      other=E[j]) +  
                            gdot[0,i] * gdot[1,j] * Cov(matrix=E[i],
                                                      other=D[j]) +
                            gdot[1,i] * gdot[0,j] * Cov(matrix=D[i],
                                                      other=E[j]) +
                            gdot[1,i] * gdot[1,j] * Cov(matrix=D[i],
                                                      other=D[j]))
                cov[j,i] = cov[i,j]

        nout = self.weights.shape[0]
        self._sd = N.zeros(self._effect.shape)

        for r in range(nout):
            var = 0
            for i in range(nrow):
                var += cov[i,i] * N.power(self.weights[r,i], 2)
                for j in range(i):
                    var += 2 * cov[i,j] * self.weights[r,i] * self.weights[r,j]

            self._sd[r] = N.sqrt(var)                

    def _extract_t(self):
        t = self._effect * recipr(self._sd)        
        t = N.clip(t, self.Tmin, self.Tmax)
        return t

    def extract(self, results):
        self._extract_effect(results)
        self._extract_sd(results)
        t = self._extract_t()

        return ContrastResults(effect=self._effect,
                               sd=self._sd,
                               t=t, df_denom=results.df_resid)



class DelayContrastOutput(TContrastOutput):


    def __init__(self, grid, contrast, IRF=None, dt=0.01, delta=None, 
                 subpath='delays', clobber=False, path='.',
                 ext='.hdr', frametimes=[], **kw):
        """
        :Parameters:
            `grid` : TODO
                TODO
            `contrast` : TODO
                TODO
            `IRF` : TODO
                TODO
            `dt` : float
                TODO
            `delta` : TODO
                TODO
            `subpath` : string
                TODO
            `clobber` : bool
                TODO
            `path` : string
                TODO
            `ext` : string
                TODO
            `frametimes` : TODO
                TODO
            `kw` : dict
                Passed through to the constructor of `TContrastOutput`
            
        """
        TContrastOutput.__init__(self, grid, contrast, subpath=subpath,
                                 clobber=clobber, frametimes=frametimes, **kw)
        self.IRF = IRF
        self.dt = dt
        if delta is None:
            self.delta = N.linspace(-4.5, 4.5, 91)
        else:
            self.delta = delta
        self.path = path
        self.subpath = subpath
        self.clobber = clobber
        self._setup_output_delay(path, clobber, subpath, ext, frametimes)

    def _setup_contrast(self, time=None):
        """
        Setup the contrast for the delay.
        """

        self.contrast.getmatrix(time=time)

    def _setup_output_delay(self, path, clobber, subpath, ext, frametimes):
        """
        Setup the output for contrast, the DelayContrast. One t, sd, and
        effect img is output for each row of contrast.weights. Further,
        the \'magnitude\' (canonical HRF) contrast matrix and \'magnitude\'
        column space are also output to illustrate what contrast this
        corresponds to.

        :Parameters:
            `path` : string
                TODO
            `clobber` : bool
                TODO
            `subpath` : string
                TODO
            `ext` : TODO
                TODO
            `frametimes` : TODO
                TODO

        :Returns: ``None``
        """

        self.timgs = []
        self.sdimgs = []
        self.effectimgs = []

        self.timg_iters = []
        self.sdimg_iters = []
        self.effectimg_iters = []

        nout = self.contrast.weights.shape[0]

        for i in range(nout):
            rowname = self.contrast.rownames[i]
            outdir = os.path.join(path, subpath, rowname)
            if not os.path.exists(outdir):
                os.makedirs(outdir)

            cnrow = self.contrast.matrix.shape[0] / 2
            l = N.zeros(self.contrast.matrix.shape[0])
            l[0:cnrow] = self.contrast.weights[i]

            img, it = self._setup_img(clobber, outdir, ext, "t")
            self.timgs.append(img)
            self.timg_iters.append(it)

            img, it = self._setup_img(clobber, outdir, ext, "effect")
            self.effectimgs.append(img)
            self.effectimg_iters.append(it)

            img, it = self._setup_img(clobber, outdir, ext, "sd")
            self.sdimgs.append(img)
            self.sdimg_iters.append(it)

            matrix = N.squeeze(N.dot(l, self.contrast.matrix))

            outname = os.path.join(outdir, 'matrix%s.csv' % rowname)
            outfile = file(outname, 'w')
            outfile.write(','.join(fpformat.fix(x,4) for x in matrix) + '\n')
            outfile.close()

            outname = os.path.join(outdir, 'matrix%s.bin' % rowname)
            outfile = file(outname, 'w')
            matrix = matrix.astype('<f8')
            matrix.tofile(outfile)
            outfile.close()

            if PYLAB_DEF:
                
                ftime = frametimes
                def g(time=None, **extra):
                    return N.squeeze(N.dot(l, self.contrast.term(time=time,
                                                                 **extra)))
                f = pylab.gcf()
                f.clf()
                pl = MultiPlot(g, tmin=0, tmax=ftime.max(),
                               dt = ftime.max() / 2000.,
                               title='Magnitude column space for delay: \'%s\'' % rowname)
                pl.draw()
                pylab.savefig(os.path.join(outdir, 'matrix%s.png' % rowname))
                f.clf()
                del(f); del(g)
                
    def extract(self, results):
        """
        :Parameters:
            `results` : TODO
                TODO

        :Returns: TODO        
        """
        return self.contrast.extract(results)

    def set_next(self, data):
        """
        :Parameters:
            `data` : TODO
                TODO

        :Returns: ``None``
        """
        nout = self.contrast.weights.shape[0]
        for i in range(nout):
            self.timg_iters[i].next().set(data.t[i])
            if self.effect:
                self.effectimg_iters[i].next().set(data.effect[i])
            if self.sd:
                self.sdimg_iters[i].next().set(data.sd[i])

class DelayHRF(hrf.SpectralHRF):

    '''
    Delay filter with spectral or Taylor series decomposition
    for estimating delays.

    Liao et al. (2002).
    '''

    def __init__(self, input_hrf=hrf.canonical, spectral=True, **keywords):
        """
        :Parameters:
            `input_hrf` : TODO
                TODO
            `spectral` : bool
                TODO
            `keywords` : dict
                Passed through as keywords to the `hrf.SpectralHRF` constructor.
        """
        hrf.SpectralHRF.__init__(self, input_hrf, spectral=spectral,
                                 names=['hrf'], **keywords)

    def deltaPCA(self, tmax=50., lower=-15.0, delta=N.arange(-4.5,4.6,0.1)):
        """
        Perform an expansion of fn, shifted over the values in delta.
        Effectively, a Taylor series approximation to fn(t+delta), in delta,
        with basis given by the filter elements. If fn is None, it assumes
        fn=IRF[0], that is the first filter.

        :Parameters:
            `tmax` : float
                TODO
            `lower` : float
                TODO
            `delta` : [float]
                TODO

        :Returns: ``None``

        Example
        -------

        >>> from numpy.random import *
        >>> from pylab import *
        >>> from numpy import *
        >>>
        >>> import neuroimaging.modalities.fmri.hrf as HRF
        >>> import numpy as N
        >>>
        >>> ddelta = 0.25
        >>> delta = N.arange(-4.5,4.5+ddelta, ddelta)
        >>> time = N.arange(0,20,0.2)
        >>> hrf = HRF.SpectralHRF(deriv=True)
        >>>
        >>> canonical = HRF.canonical
        >>> taylor = hrf.deltaPCA(delta=delta)
        >>> curplot = plot(time, taylor.components[1](time))
        >>> curplot = plot(time, taylor.components[0](time))
        >>> curtitle=title('Shift using Taylor series -- components')
        >>> show()
        >>>
        >>> curplot = plot(delta, taylor.coef[1](delta))
        >>> curplot = plot(delta, taylor.coef[0](delta))
        >>> curtitle = title('Shift using Taylor series -- coefficients')
        >>> show()
        >>>
        >>> curplot = plot(delta, taylor.inverse(delta))
        >>> curplot = plot(taylor.coef[1](delta) / taylor.coef[0](delta), delta)
        >>> curtitle = title('Shift using Taylor series -- inverting w1/w0')
        >>> show()
        >>>
        """

        time = N.arange(lower, tmax, self.dt)
        irf = self.IRF

        if not self.spectral: # use Taylor series approximation
            dirf = interpolant(time, -N.gradient(irf(time), self.dt))

            H = N.array([irf(time - d) for d in delta])

            W = N.array([irf(time), dirf(time)])
            W = W.T

            WH = N.dot(L.pinv(W), H.T)

            coef = [interpolant(delta, w) for w in WH]
            
            def approx(time, delta):
                value = (coef[0](delta) * irf(time)
                         + coef[1](delta) * dirf(time))
                return value

            approx.coef = coef
            approx.components = [irf, dirf]
            self.n = len(approx.components)
            self.names = [self.names[0], 'd%s' % self.names[0]]

        else:
            hrf.SpectralHRF.deltaPCA(self)

        (self.approx.theta,
         self.approx.inverse,
         self.approx.dinverse,
         self.approx.forward,
         self.approx.dforward) = invertR(delta, self.approx.coef)
        
        self.delay = self.approx

canonical = DelayHRF()
