''' Test results of OLS against R '''


import numpy as np
import numpy.testing as nptest
import nose.tools


import nipy.fixes.scipy.stats.models as SSM
#from nipy.fixes.scipy.stats.models.formula import Term, I


from exampledata import y, x

def assert_model_similar(res1, res2):
    ''' Test if models have similar parameters '''
    nptest.assert_almost_equal(res1.beta, res2.beta, 4)
    nptest.assert_almost_equal(res1.resid, res2.resid, 4)
    nptest.assert_almost_equal(res1.predict, res2.predict, 4)
    nptest.assert_almost_equal(res1.df_resid, res2.df_resid, 4)

def check_model_class(model_class, r_model_type):
    results = model_class(x).fit(y)
    r_results = WrappedRModel(y, x, r_model_type)
    r_results.assert_similar(results)

def test_using_rpy():
    """
    this test fails because the glm results don't agree with the ols and rlm
    results
    """
    try:
        from rpy import r
        from rmodelwrap import RModel

        # Test OLS
        ols_res = SSM.regression.OLSModel(x).fit(y)
        rlm_res = RModel(y, x, r.lm)
        yield assert_model_similar, ols_res, rlm_res
#       this is failing with an error right now
#       segfaults on my other machine (don't know if it's here exactly though)
#        glm_res = SSM.glm(x).fit(y)
#        yield assert_model_similar, glm_res, rlm_res
    except ImportError:
        yield nose.tools.assert_true, True

def test_longley():
    '''
    Test OLS accuracy with Longley (1967) data
    '''

    from exampledata import longley
    y,x = longley()
    nist_long = (-3482258.63459582,15.0618722713733,-0.358191792925910E-01, 
                 -2.02022980381683, -1.03322686717359, -0.511041056535807E-01, 
                 1829.15146461355)
    nist_long_bse=(890420.383607373,84.9149257747669,0.334910077722432E-01, 
                   0.488399681651699,0.214274163161675,0.226073200069370, 
                   455.478499142212)
#   From STATA
    conf_int=[(-5496529,-1467987),(-177.0291,207.1524),
                   (-.111581,.0399428),(-3.125065,-.9153928),
                   (-1.517948,-.5485049),(-.5625173,.4603083),
                   (798.7873,2859.515)]
#    x = np.hstack((np.ones((len(x), 1)), x))  # A constant is not added by default
# new flag should take care of that now.
    res = SSM.regression.OLSModel(x, hascons=False).fit(y)
    nptest.assert_almost_equal(res.beta, nist_long, 4)
    nptest.assert_almost_equal(res.bse,nist_long_bse, 4)
    nptest.assert_almost_equal(res.scale, 92936.0061673238, 6)
    nptest.assert_almost_equal(res.Rsq, 0.995479004577296, 12)
    nptest.assert_equal(res.df_resid,9)
    nptest.assert_equal(res.df_model,6)
    nptest.assert_almost_equal(res.ESS, 184172401.944494, 3)
    nptest.assert_almost_equal(res.SSR, 836424.055505915, 5)
    nptest.assert_almost_equal(res.MSE_model, 30695400.3240823, 4) 
    nptest.assert_almost_equal(res.MSE_resid, 92936.0061673238, 6)
    nptest.assert_almost_equal(res.F, 330.285339234588, 8)
# This fails, but it's just a precision issue in Stata, try STATA
# how to compare arrays with floats and ints?
    nptest.assert_almost_equal(res.conf_int(),conf_int)
# Need to get test values for the llf,aic,bic from a stats package
# Need to test adjRsq
# Need to test robust errors, write a SAS routine to compare values


def test_wampler():
    nist_wamp1=(1.00000000000000,1.00000000000000,1.00000000000000,
                1.00000000000000,1.00000000000000,1.00000000000000)
    x=np.arange(21,dtype=float)[:,np.newaxis]
    p=np.poly1d([1,1,1,1,1,1])
    y=np.polyval(p,x).reshape(len(x))
    x=np.hstack((np.ones((len(x), 1)), x, x**2, x**3, x**4, x**5))
    res = SSM.regression.OLSModel(x).fit(y)
    nptest.assert_almost_equal(res.beta,nist_wamp1)
##  include next three wampler sets

##  the precision appears to be machine specific, 
##      so default to 4 decimal places
##  check scipy test suite

    

if __name__=="__main__":
    nptest.run_module_suite()

    



