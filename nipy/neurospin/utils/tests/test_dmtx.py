"""
Test the design_matrix utilities.

Note that the tests just looks whether the data produces has correct dimension,
not whether it is exact
"""

import numpy as np
from nipy.neurospin.utils.design_matrix import *
from numpy.testing import assert_almost_equal

def basic_paradigm():
    conditions = [0, 0, 0, 1, 1, 1, 2, 2, 2]
    onsets=[30, 70, 100, 10, 30, 90, 30, 40, 60]
    paradigm = np.vstack(([conditions, onsets])).T
    return paradigm

def block_paradigm():
    conditions = [0, 0, 0, 1, 1, 1, 2, 2, 2]
    onsets=[30, 70, 100, 10, 30, 90, 30, 40, 60]
    duration=5*np.ones(9)
    paradigm = np.vstack(([conditions, onsets, duration])).T
    return paradigm

def test_dmtx0():
    """ test design matrix creation when no paradigm is provided
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    X, names= dmtx_light(frametimes, drift_model='Polynomial', drift_order=3)
    print names
    assert(len(names)==4)

def test_dmtx0b():
    """ test design matrix creation when no paradigm is provided
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    X, names= dmtx_light(frametimes, drift_model='Polynomial', drift_order=3)
    assert_almost_equal(X[:,0],np.linspace(0, 1.,128))

def test_dmtx0c():
    """ test design matrix creation when regressors are provided manually
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    ax = np.random.randn(128,4)
    X, names= dmtx_light(frametimes, drift_model='Polynomial', drift_order=3,
                         add_regs=ax)
    assert_almost_equal(X[:,0],ax[:,0])

def test_dmtx0d():
    """ test design matrix creation when regressors are provided manually
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    ax = np.random.randn(128,4)
    X, names= dmtx_light(frametimes, drift_model='Polynomial', drift_order=3,
                         add_regs=ax)
    assert((len(names)==8)&(X.shape[1]==8))

    
    
def test_dmtx1():
    """ basic test based on basic_paradigm and canonical hrf
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3)
    print names
    assert(len(names)==7)

def test_dmtx1b():
    """ idem test_dmtx1, but different test
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    X,names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                        drift_model='Polynomial', drift_order=3)
    print np.shape(X)
    assert(X.shape==(128,7))

def test_dmtx1c():
    """ idem test_dmtx1, but different test
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    X,names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                        drift_model='Polynomial', drift_order=3)
    assert((X[:,-1]==1).all())


def test_dmtx1d():
    """ idem test_dmtx1, but different test
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    X,names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                        drift_model='Polynomial', drift_order=3)
    assert((np.isnan(X)==0).all())
       
def test_dmtx2():
    """ idem test_dmtx1 with a different drift term
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    X,names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                        drift_model='Cosine', hfcut=63)
    print names
    assert(len(names)==8)

def test_dmtx3():
    """ idem test_dmtx1 with a different drift term
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    X,names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                        drift_model='Blank')
    print names
    assert(len(names)==4)  

def test_dmtx4():
    """ idem test_dmtx1 with a different hrf model
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical With Derivative'
    X, names= dmtx_light(frametimes, paradigm, hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3)
    print names
    assert(len(names)==10)

def test_dmtx5():
    """ idem test_dmtx1 with a block paradigm
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = block_paradigm()
    hrf_model='Canonical'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3)
    print names
    assert(len(names)==7)

def test_dmtx6():
    """ idem test_dmtx1 with a block paradigm and the hrf derivative
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    paradigm = block_paradigm()
    hrf_model='Canonical With Derivative'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3)
    assert(len(names)==10)

def test_dmtx7():
    """ idem test_dmtx1, but odd paradigm
    """
    tr = 1.0
    frametimes = np.linspace(0,127*tr,128)
    conditions = [0,0,0,1,1,1,3,3,3]
    # no condition '2'
    onsets=[30,70,100,10,30,90,30,40,60]
    paradigm = np.vstack(([conditions,onsets])).T
    return paradigm
    hrf_model='Canonical'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3)
    assert(len(names)==7)

def test_dmtx8():
    """ basic test based on basic_paradigm and FIR
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='FIR'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3)
    print names
    assert(len(names)==7)

def test_dmtx9():
    """ basic test based on basic_paradigm and FIR
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='FIR'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3, fir_delays=range(1,5))
    print names
    assert(len(names)==16)

def test_dmtx10():
    """
    Check that the first column o FIR design matrix is OK
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='FIR'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3,
                         fir_delays=range(1,5))
    assert(X[paradigm[paradigm[:,0]==0,1]+2,0]==1).all()

def test_dmtx11():
    """
    check that the second column of the FIR design matrix is OK indeed
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='FIR'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3,
                         fir_delays=range(1,5))
    assert(X[paradigm[paradigm[:,0]==0,1]+5,3]==1).all()

def test_dmtx12():
    """
    check that the 11th column of a FIR design matrix is indeed OK
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='FIR'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3,
                         fir_delays=range(1,5))
    assert(X[paradigm[paradigm[:,0]==2,1]+5,11]==1).all()

def test_dmtx13():
    """
    Check that the fir_duration is well taken into account
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='FIR'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3,
                         fir_delays=range(1,5), fir_duration=2*tr)
    assert(X[paradigm[paradigm[:,0]==0,1]+3,0]==1).all()

def test_dmtx14():
    """
    Check that the first column o FIR design matrix is OK after a 1/2 time shift
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)+tr/2
    paradigm = basic_paradigm()
    hrf_model='FIR'
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3,
                         fir_delays=range(1,5))
    assert(X[paradigm[paradigm[:,0]==0,1]+1,0]==1).all()

def test_dmtx15():
    """ basic test based on basic_paradigm, plus user supplied regressors 
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    ax = np.random.randn(128,4)
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3, add_regs=ax)
    assert((len(names)==11)&(X.shape[1]==11))

def test_dmtx16():
    """ check that additional regressors are put at the reight place
    """
    tr = 1.0
    frametimes = np.linspace(0, 127*tr,128)
    paradigm = basic_paradigm()
    hrf_model='Canonical'
    ax = np.random.randn(128,4)
    X, names= dmtx_light(frametimes, paradigm,  hrf_model=hrf_model,
                         drift_model='Polynomial', drift_order=3, add_regs=ax)
    assert_almost_equal(X[:,3:7],ax)



    
if __name__ == "__main__":
    import nose
    nose.run(argv=['', __file__])


