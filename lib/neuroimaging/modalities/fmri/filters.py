import types

import numpy as N
from neuroimaging import traits

from neuroimaging.modalities.fmri.utils import ConvolveFunctions, WaveFunction

class Filter(traits.HasTraits):
    '''
    Takes a list of impulse response functions (IRFs): main purpose is to
    convolve a functions with each IRF for Design. The class assumes the range
    of the filter is effectively 50 seconds, can be changed by setting tmax --
    this is just for the __mul__ method for convolution.
    '''

    dt = traits.Float(0.02)
    tmax = traits.Float(500.0)
    tmin = traits.Float(-10.)

    def __getitem__(self, i):
        if type(i) is not types.IntType:
            raise ValueError, 'integer needed'
        if self.n == 1:
            if i != 0:
                raise IndexError, 'invalid index'
            try:
                IRF = self.IRF[0]
            except:
                IRF = self.IRF
            return Filter(IRF, names=[self.names[0]])
        else:
            return Filter(self.IRF[i], names=[self.names[i]])

    def __init__(self, IRF, **keywords):
        traits.HasTraits.__init__(self, **keywords)
        self.IRF = IRF
        try:
            self.n = len(self.IRF)
        except:
            self.n = 1

    def __add__(self, other):
        """
        Take two Filters with the same number of outputs and create a new one
        whose IRFs are the sum of the two.
        """
        if self.n != other.n:
            raise ValueError, 'number of dimensions in Filters must agree'
        newIRF = []
        for i in range(self.n):
            def curfn(time):
                return self.IRF[i](time) + other.IRF[i](time)
            newIRF.append(curfn)
        return Filter(newIRF)

    def __mul__(self, other):
        """
        Take two Filters with the same number of outputs and create a new one
        whose IRFs are the convolution of the two.
        """
        if self.n != other.n:
            raise ValueError, 'number of dimensions in Filters must agree'
        newIRF = []
        interval = (self.tmin, self.tmax + other.tmax)
        for i in range(self.n):
            curfn = ConvolveFunctions(self.IRF[i], other.IRF[i], interval, self.dt)
            newIRF.append(curfn)
        return Filter(newIRF)

    def convolve(self, fn, interval=None, dt=None):
        """
        Take a (possibly vector-valued) function fn of time and return
        a linearly interpolated function after convolving with the filter.
        """
        if dt is None:
            dt = self.dt
        if interval is None:
            interval = [self.tmin, self.tmax]
        if self.n > 1:
            value = []
            for _IRF in self.IRF:
                value.append(ConvolveFunctions(fn, _IRF, interval, dt))
            return value
        else:
            return ConvolveFunctions(fn, self.IRF, interval, dt)

    def __call__(self, time):
        """
        Return the values of the IRFs of the filter.
        """
        if self.n > 1:
            value = N.zeros((self.n,) + time.shape, N.float64)
            for i in range(self.n):
                value[i] = self.IRF[i](time)
        else:
            value = self.IRF(time)
        return value

class GammaDENS:
    """
    A class for a Gamma density which knows how to differentiate itself.

    By default, normalized to integrate to 1.
    """
    def __init__(self, alpha, nu, coef=1.0):
        self.alpha = alpha
        self.nu = nu
##        self.coef = nu**alpha / scipy.special.gamma(alpha)
        self.coef = coef

    def __str__(self):
        return '<GammaDENS:alpha:%03f, nu:%03f, coef:%03f>' % (self.alpha, self.nu, self.coef)

    def __repr__(self):
        return self.__str__()

##     def __mul__(self, const):
##         self.coef = self.coef * const
##         return self
    
    def __call__(self, x):
        '''Evaluate the Gamma density.'''
        _x = x * N.greater_equal(x, 0)
        return self.coef * N.power(_x, self.alpha-1.) * N.exp(-self.nu*_x)

    def deriv(self, const=1.):
        '''
        Differentiate a Gamma density. Returns a GammaCOMB that can evaluate
        the derivative.
        '''
        return GammaCOMB([[const*self.coef*(self.alpha-1),
                           GammaDENS(self.alpha-1., self.nu)],
                          [-const*self.coef*self.nu,
                           GammaDENS(self.alpha, self.nu)]])

class GammaCOMB:
    def __init__(self, fns):
        self.fns = fns

    def __mul__(self, const):
        fns = []
        for fn in self.fns:
            fns.append([fn[0] * const, fn[1]])
        return GammaCOMB(fns)

    def __add__(self, other):
        fns = self.fns + other.fns
        return GammaCOMB(fns)

    def __call__(self, x):
        value = 0
        for coef, fn in self.fns:
            value = value + coef * fn(x)
        return value

    def deriv(self, const=1.):
        fns = []
        for coef, fn in self.fns:
            comb = fn.deriv(const=const)
            comb.fns[0][0] = comb.fns[0][0] * coef
            comb.fns[1][0] = comb.fns[1][0] * coef
            fns = fns + comb.fns
        return GammaCOMB(fns)
    
class GammaHRF(Filter):
    """
    A class that represents the Gamma basis in SPM: i.e. the filter is a
    collection of a certain number of Gamma densities. Parameters are
    specified as a kx2 matrix for k Gamma functions.
    """

    def __init__(self, parameters):
        fns = [GammaDENS(alpha, nu) for alpha, nu in parameters]
        Filter.__init__(self, fns)

    def deriv(self, const=1.):
        return [fn.deriv(const=const) for fn in self.IRF]
    
class FIR(Filter):
    """
    A class for FIR filters: i.e. the filter is a collection of square waves.
    Parameters (start and duration) are specified as a kx2 matrix for k square
    waves.
    
    >>> from neuroimaging.modalities.fmri import filters
    >>> from pylab import *
    >>> from numpy import *
    >>> parameters = array([[1., 2.], [2., 5.], [4., 8.]])
    >>> IRF = filters.FIR(parameters)
    >>> IRF.plot(linestyle='steps')
    >>> ylab = ylabel('Filters')
    >>> xlab = xlabel('Time (s)')
    >>> show()

    """

    def __init__(self, parameters):
        fns = [WaveFunction(start, duration, 1.0) for (start, duration) in parameters]
        Filter.__init__(self, fns)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
