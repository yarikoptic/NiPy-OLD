"""
TODO
"""
__docformat__ = 'restructuredtext'

import gc

import numpy as np
from neuroimaging.fixes.scipy.stats.models.utils import recipr

class OneSampleResults(object):
    """
    A container for results from fitting a (weighted) one sample T.
    """

    def __init__(self):
        """
        TODO
        """
        self.values = {'mean': {'mu': None,
                                'sd': None,
                                't': None,
                                'resid': None,
                                'df_resid': None,
                                'scale': None},
                       'varatio': {'varatio': None,
                                   'varfix': None}}

    def __getitem__(self, key):
        """
        :Parameters:
            key : TODO
                TODO

        :Returns: TODO
        """
        return self.values[key]

    def __setitem__(self, key, val):
        """
        :Parameters:
            key : TODO
                TODO
            val : TODO
                TODO

        :Returns: ``None``
        """
        self.values[key] = val

class OneSample(object):
    """
    TODO
    """
    
    def __init__(self, use_scale=True, niter=10, weight_type='sd'):
        """
        :Parameters:
            use_scale : ``bool``
                TODO
            niter : ``int``
                TODO
            weight_type : ``string``
                TODO                
        """
        if weight_type in ['sd', 'var', 'weight']:
            self.weight_type = weight_type
        else:
            raise ValueError, "Weight type must be one of " \
                  "['sd', 'var', 'weight']"
        self.use_scale = use_scale
        self.niter = niter
        self.value = OneSampleResults()

    def fit(self, Y, W, which='mean', df=None):
        """
        :Parameters:
            Y : TODO
                TODO
            W : TODO
                TODO
            which : ``string``
                TODO
            df : TODO
                TODO

        :Returns: TODO
        """
        if which == 'mean':
            return self.estimate_mean(Y, W)
        else:
            return self.estimate_varatio(Y, W, df=df)

    def get_weights(self, W):
        """
        :Parameters:
            W : TODO
                TODO

        :Returns: ``numpy.ndarray``
        """
        try:
            if W.ndim == 1:
                W.shape = (W.shape[0], 1)
        except:
            pass

        if self.weight_type == 'sd':
            W = 1. / np.power(W, 2)
        elif self.weight_type == 'var':
            W = 1. / W
        return np.asarray(W)

    def estimate_mean(self, Y, W):
        """
        :Parameters:
            Y : TODO
                TODO
            W : TODO
                TODO

        :Returns: TODO
        """

        if Y.ndim == 1:
            Y.shape = (Y.shape[0], 1)
        W = np.asarray(self.get_weights(W))
        if W.shape in [(), (1,)]:
            W = np.ones(Y.shape) * W

        nsubject = Y.shape[0]

        if self.value['varatio']['varfix'] is not None:
            sigma2 = np.asarray(self['varatio']['varfix'] *
                               self['varatio']['varatio'])

            if sigma2.shape != ():
                sigma2 = np.multiply.outer(np.ones((nsubject,)), sigma2)
            S = recipr(W) + sigma2
            W = recipr(S)
        
        mu = np.add.reduce(Y * W, 0) / np.add.reduce(W, 0)
        df_resid = nsubject - 1
        resid = (Y - np.multiply.outer(np.ones(Y.shape[0]), mu)) * np.sqrt(W)

        if self.use_scale:
            scale = np.add.reduce(np.power(resid, 2), 0) / df_resid
        else:
            scale = 1.
        var_total = scale * recipr(np.add.reduce(W, 0))

        self.value['mean']['df_resid'] = df_resid
        self.value['mean']['resid'] = resid        
        self.value['mean']['mu'] = mu
        self.value['mean']['sd'] = np.squeeze(np.sqrt(var_total))
        self.value['mean']['t'] = np.squeeze(self.value['mean']['mu'] *
                                            recipr(self.value['mean']['sd']))
        self.value['mean']['scale'] = np.sqrt(scale)

        return self.value

    def estimate_varatio(self, Y, W, df=None):
        """
        :Parameters:
            Y : TODO
                TODO
            W : TODO
                TODO
            df : TODO
                TODO

        :Returns; TODO
        """
        Sreduction = 0.99
        S = 1. / W

        nsubject = Y.shape[0]
        df_resid = nsubject - 1

        R = Y - np.multiply.outer(np.ones(Y.shape[0]), np.mean(Y, axis=0))
        sigma2 = np.squeeze(np.add.reduce(np.power(R, 2), axis=0) / df_resid)

        minS = np.minimum.reduce(S, 0) * Sreduction

        Sm = S - np.multiply.outer(np.ones(nsubject), minS)

        for _ in range(self.niter):
            Sms = Sm + np.multiply.outer(np.ones(nsubject), sigma2)
            W = recipr(Sms)
            Winv = 1. / np.add.reduce(W, axis=0)
            mu = Winv * np.add.reduce(W * Y, axis=0)
            R = W * (Y - np.multiply.outer(np.ones(nsubject), mu))
            ptrS = 1 + np.add.reduce(Sm * W, 0) - \
                   np.add.reduce(Sm * np.power(W, 2), axis=0) * Winv
            sigma2 = np.squeeze((sigma2 * ptrS + np.power(sigma2, 2) *
                                np.add.reduce(np.power(R,2), 0)) / nsubject)

        sigma2 = sigma2 - minS

        if df is None:
            df = np.ones(nsubject)
            
        df.shape = (1, nsubject)
        
        _Sshape = S.shape
        S.shape = (S.shape[0], np.product(S.shape[1:]))


        self.value['varatio']['varfix'] = np.dot(df, S) / df.sum()

        S.shape = _Sshape
        self.value['varatio']['varfix'].shape = _Sshape[1:]
        self.value['varatio']['varatio'] = \
                         np.nan_to_num(sigma2 / self.value['varatio']['varfix'])
        return self.value


class OneSampleIterator(object):
    """
    TODO
    """

    def __init__(self, iterator, outputs=()):
        """
        :Parameters:
            iterator : TODO
                TODO
            outputs : TODO
                TODO
        """
        self.iterator = iter(iterator)
        self.outputs = [iter(output) for output in outputs]
        
    def weights(self):
        """
        This method should get the weights from self.iterator.

        :Returns: ``float``
        """
        return 1.

    def _getinputs(self):
        pass

    def fit(self, which='mean', df=None):
        """
        Go through an iterator, instantiating model and passing data,
        going through outputs.

        :Parameters:
            which : ``string``
                TODO
            df : TODO
                TODO

        :Returns: ``None``
        """

        for data in self.iterator:

            W = self.weights()
            self._getinputs()
            shape = data.shape[1:]

            results = OneSample().fit(data, W, which, df)

            for output in self.outputs:
                out = output.extract(results)
                if output.nout > 1:
                    out.shape = (output.nout,) + shape
                else:
                    out.shape = shape

                output.next().set(out)

            del(results)
            gc.collect()

