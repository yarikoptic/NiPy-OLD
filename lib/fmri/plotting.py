"""
Defines a class MultiPlot to plot multiple functions of time simultaneously.
"""

import pylab
import numpy as N
import enthought.traits as traits

class MultiPlot(traits.HasTraits):
    """
    Class to plot multi-valued function of time simultaneously.
    """
    
    tmin = traits.Float(0.)
    tmax = traits.Float(300.)
    dt = traits.Float(0.2)
    figure = traits.Any()
    title = traits.Str()

    def __init__(self, fn, **keywords):
        traits.HasTraits.__init__(self, **keywords)
        self.t = N.arange(self.tmin, self.tmax, self.dt)
        self.fn = fn
        self.figure = pylab.gcf()

    def draw(self, t=None, **keywords):
        pylab.figure(num=self.figure.number)
        if t is None:
            t = self.t
        self.lines = []
        v = self.fn(time=t, **keywords)
        if v.ndim == 1:
            v.shape = (1, v.shape[0])
            
        n = v.shape[0]
        dy = 0.9 / n
        for i in range(n):
            a = pylab.axes([0.05,0.05+i*dy,0.9,dy])
            a.set_xticklabels([])
            a.set_yticks([])
            a.set_yticklabels([])
            pylab.plot(t, v[i])
            m = v[i].min()
            M = v[i].max()
            r = M - m
            l = m - 0.2 * r
            u = M + 0.2 * r
            if l == u:
                u += 1.
                l -= 1.
            a.set_ylim([l, u])

        pylab.title(self.title)

