from _clustering import *
from _clustering import __doc__

import numpy as np


def kmeans(X, nbclusters=2, Labels=None, maxiter=300, delta=0.0001, verbose=0,
              ninit=1):
    """
    kmeans clustering algorithm 

    Parameters
    ----------
    X: array of shape (n,p): n = number of items, p = dimension
       data array
    nbclusters (int), the number of desired clusters
    Labels = None array of shape (n) prior Labels.   
           if None or inadequate a random initilization is performed.
    maxiter=300 (int), the maximum number of iterations  before convergence
    delta=0.0001 (float), 
                 the relative increment in the results 
                 before declaring convergence.
    verbose=0: verbosity mode
    ninit=1: number of random initalizations
 
    Returns
    -------
    Centers: array of size nbclusters*p, 
             the centroids of  the resulting clusters
    Labels : array of size n, the discrete labels of the input items
    J (float):  the final value of the inertia criterion
    """
    nbitems = X.shape[0]
    if nbitems<1:
        if verbose:
            raise ValueError, " I need at least one item to cluster"
        
    if np.size(X.shape)>2:
        if verbose:
            raise ValueError, " please enter a two-diemnsional array \
                              for clustering"
            
    if np.size(X.shape)==1:
        X = np.reshape(X,(nbitems,1))
    X = X.astype('d')
    
    nbclusters = int(nbclusters)
    if nbclusters<1:
        if verbose:
            print " cannot compute less than 1 cluster"
        nbclusters = 1
        
    if nbclusters>nbitems:
        if verbose:
            print " cannot find more clusters than items"
        nbclusters = nbitems
    
    nolabel = 1

    if ninit<1:
       if verbose: "need at least one iteration"
       ninit = np.maximum(int(ninit),1)

    if Labels != None:
        if np.size(Labels) == nbitems:
            Labels = Labels.astype(np.int)
            OK = (Labels.min()>-1)&(Labels.max()<nbclusters+1)
            if OK:
                nolabel = 0
                maxiter = int(maxiter)
                if maxiter>0:
                    delta = float(delta)
                    if delta<0:
                        if verbose:
                            print "incorrect stopping criterion - ignored"
                        delta = 0.0001
                    else:
                        pass
                else:
                    if verbose:
                        print "incorrect number of iterations - ignored"
                    maxiter = 300
            else:
                if verbose:
                    print "incorrect labelling - ignored"
        else:
            if verbose:
                print "incompatible number of labels provided - ignored"
    
    #if nolabel:
    #    Labels = (rand(nbitems)*nbclusters).astype(np.int)
    #
    #Centers,labels,J = cmeans(X, nbclusters, Labels, maxiter, delta)
    Centers,labels,J = _kmeans(X, nbclusters, Labels, maxiter, delta, ninit)
    
    return Centers,labels,J


def _MStep(x, z ,k):
    """
    computation of cluster centers/means    

    Parameters
    ----------
    x array of shape (n,p)
      n = number of items, p = data dimension 
    z, array of shape (x.shape[0]) current assignment  
    k, int, number of desired clusters       
    
    Returns
    -------
    centers, array of shape (k,p)
             the resulting centers
    """
    dim = x.shape[1]
    centers = np.repeat(np.reshape(x.mean(0),(1,dim)),k,0)
    for q in range(k):
        centers[q] = np.mean(x[z==q],0)
    return centers

def _EStep(x, centers):
    """
    Computation of the input-to-cluster assignment
    
    Parameters
    ----------
    x array of shape (n,p)
      n = number of items, p = data dimension 
    centers, array of shape (k,p) the cluster centers
    
    Returns
    -------
    z vector of shape(n), the resulting assignment
    """
    nbitem = x.shape[0]
    z = -np.ones(nbitem).astype(np.int)
    mindist = np.infty * np.ones(nbitem)
    k = centers.shape[0]
    for q in range(k):
        dist = np.sum((x-centers[q])**2,1)
        z[dist<mindist] = q
        mindist = np.minimum(dist, mindist)
    J = mindist.sum()    
    return z, J

def voronoi(x, centers):
    """
    Assignment of data items to nearest cluster center
    
    Parameters
    ----------
    x array of shape (n,p)
      n = number of items, p = data dimension 
    centers, array of shape (k,p) the cluster centers
    
    Returns
    -------
    z vector of shape(n), the resulting assignment
    """
    if np.size(x)==x.shape[0]:
       x = np.reshape(x,(np.size(x),1))
    if np.size(centers)==centers.shape[0]:
       centers = np.reshape(centers,(np.size(centers),1))
    if x.shape[1]!=centers.shape[1]:
       raise ValueError, "Inconsistent dimensions for x and centers"

    return _EStep(x, centers)[0]

def _kmeans(X, nbclusters=2, Labels=None, maxiter=300, delta=1.e-4,
            ninit=1, verbose=0):
    """
    kmeans clustering algorithm 

    Parameters
    ----------
    X: array of shape (n,p): n = number of items, p = dimension
       data array
    nbclusters (int), the number of desired clusters
    Labels = None array of shape (n) prior Labels.   
           if None or inadequate a random initilization is performed.
    maxiter=300 (int), the maximum number of iterations  before convergence
    delta=0.0001 (float), 
                 the relative increment in the results 
                 before declaring convergence.
    verbose=0: verboseity mode
 
    Returns
    -------
    Centers: array of size nbclusters*p, 
             the centroids of  the resulting clusters
    Labels : array of size n, the discrete labels of the input items
    J (float):  the final value of the inertia criterion
    """
    # fixme: do the checks
    nbitem = X.shape[0]

    vdata = np.mean(np.var(X,0))
    bJ = np.infty
    for it in range(ninit):
        # init
        if Labels==None:
            seeds = np.argsort(np.random.rand(nbitem))[:nbclusters]
            centers = X[seeds]
        else:
            centers = _MStep(X, Labels, nbclusters)
        centers_old = centers.copy()
    
        # iterations
        for i in range(maxiter):
            z, J = _EStep(X, centers, )
            centers = _MStep(X, z, nbclusters)
            if verbose: print i,J
            if np.sum((centers_old-centers)**2)<delta*vdata:
                if verbose: print i
                break
            centers_old = centers.copy()

        if J<bJ:
            bJ = J
            centers_output = centers.copy()
            z_output = z.copy()

    return centers_output, z_output, J

def tempTest():
    X1 = np.array([1,0,0,0]) + np.random.randn(1000, 4)
    X2 = np.array([0,0,0,0]) + np.random.randn(10000, 4)
    X3 = np.array([0,-1,0,0]) + np.random.randn(1000, 4)
    X4 = np.array([2,2,0,0]) + np.random.randn(1000, 4)
    X = np.vstack((X1, X2, X3, X4))
    import time
    t1 = time.time()
    c,z,j = _kmeans(X, 3, ninit=2,  verbose=0 )
    t2 = time.time()
    print j/X.shape[0]
    t3 = time.time()
    c,z,j = kmeans(X, 3, verbose=0 )
    t4 = time.time()
    print j/X.shape[0]
    print t4-t3, t2-t1
