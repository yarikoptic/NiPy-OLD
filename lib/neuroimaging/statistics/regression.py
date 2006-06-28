"""
This module provides various regression analysis techniques to model the
relationship between the dependent and independent variables.
"""

import gc, utils

import numpy as N
import numpy.linalg as L
from enthought import traits
from scipy.sandbox.models.regression import OLSModel, WLSModel, ARModel, Results


class LinearModelIterator(traits.HasTraits):

    iterator = traits.Any()
    outputs = traits.List()

    def __init__(self, iterator, outputs=[], **keywords):
        self.iterator = iter(iterator)
        self.outputs = [iter(output) for output in outputs]

    def model(self, **keywords):
        """
        This method should take the iterator at its current state and
        return a LinearModel object.
        """
        return None

    def fit(self, **keywords):
        """
        Go through an iterator, instantiating model and passing data,
        going through outputs.
        """

        for data in self.iterator:
            shape = data.shape[1:]
            data = data.reshape(data.shape[0], N.product(shape))
            model = self.model()

            results = model.fit(data, **keywords)

            for output in self.outputs:
                out = output.extract(results)
                if output.nout > 1:
                    out.shape = (output.nout,) + shape
                else:
                    out.shape = shape
                output.next(data=out)
            
            del(results); gc.collect()


class RegressionOutput(traits.HasTraits):

    """
    A generic output for regression. Key feature is that it has
    an \'extract\' method which is called on an instance of
    Results.
    """

    Tmax = traits.Float(100.)
    Tmin = traits.Float(-100.)
    Fmax = traits.Float(100.)

    def __init__(self, iterator, **keywords):
        self.iterator = iter(iterator)
        traits.HasTraits.__init__(**keywords)

    def __iter__(self):
        return self

    def extract(self, results):
        return 0.
    
