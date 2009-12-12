"""
These are several functions for computing reproducibility measures.
A use script should be appended soon on the repository.

In general thuis proceeds as follows:
The dataset is subject to jacknife subampling ('splitting'),
each subsample being analysed independently.
A reproducibility measure is then derived;

All is used to produce the work described in
Analysis of a large fMRI cohort: Statistical and methodological issues for group analyses.
Thirion B, Pinel P, Meriaux S, Roche A, Dehaene S, Poline JB.
Neuroimage. 2007 Mar;35(1):105-20. 

Bertrand Thirion, 2009.
"""

import numpy as np
import nipy.neurospin.graph as fg


# ---------------------------------------------------------
# ----- cluster handling functions ------------------------
# ---------------------------------------------------------


def histo_repro(h):
    """
    Given the histogram h, compute a standardized reproducibility measure    
    
    Parameters
    ----------
    h array of shape(xmax+1), the histogram values
    
    Returns
    -------
    hr, float: the measure
    """
    k = np.size(h)-1
    if k==1:
       return 0.
    nf = np.dot(h,np.arange(k+1))/(k)
    if nf==0:
       return 0.
    n1k = np.arange(1,k+1)
    res = 1.0*np.dot(h[1:],n1k*(n1k-1))/(k*(k-1))
    return res/nf


def cluster_threshold(map, ijk, th, csize):
    """
    perform a thresholding of a map at the cluster-level

    Parameters
    ----------
    map: array of shape(nbvox)
    ijk: array of shape(nbvox,3):
        the set of associated grid coordinates
    th (float): cluster-forming threshold
    cisze (int>0): cluster size threshold
        
    Returns
    -------
    binary array of shape (nvox): the binarized thresholded map

    Note
    ----
    Should be replaced by a more standard function in teh future in the future
    """
    if map.shape[0]!=ijk.shape[0]:
        raise ValueError, 'incompatible dimensions'
    ithr = np.nonzero(map>th)[0]
    binary = np.zeros(np.size(map)).astype(np.int)
    
    if np.size(ithr)>0:
        G = fg.WeightedGraph(np.size(ithr))
        G.from_3d_grid(ijk[ithr,:],18)
        
        # get the connected components
        label = G.cc()+1 
        binary[ithr] = label
        
        #remove the small clusters
        for i in range(label.max()+1):
            ji = np.nonzero(label==i)[0]
            if np.size(ji)<csize: binary[ji]=0

        binary = (binary>0)
    return binary


def get_cluster_position_from_thresholded_map(smap, ijk, coord, thr=3.0,
                                              csize=10):
    """
    the clusters above thr of size greater than csize in
    18-connectivity are computed

    Parameters
    ----------
    smap : array of shape (nbvox): map to threshold
    ijk array of shape(nbvox,anat_dim) grid coordinates
    coord: array of shape (nbvox,anatdim) physical ccordinates
    thr=3.0 (float) cluster-forming threshold
    cisze=10 (int>0): cluster size threshold

    Returns
    -------
    positions array of shape(k,anat_dim):
              the cluster positions in physical coordinates
              where k= number of clusters
              if no such cluster exists, None is returned
    """
    
    # if no supra-threshold voxel, return
    ithr = np.nonzero(smap>thr)[0]
    if np.size(ithr)==0:
        return None

    # first build a graph
    g = fg.WeightedGraph(np.size(ithr))
    g.from_3d_grid(ijk[ithr,:],18)
    
    # get the connected components
    label = g.cc()
    baryc = []
    for i in range(label.max()+1):
        ji = np.nonzero(label==i)[0]
        if np.size(ji)>=csize:
            idx = ithr[ji]
            baryc.append(np.mean(coord[idx],0))

    if len(baryc)==0:
        return None

    baryc = np.vstack(baryc)
    return baryc



# ---------------------------------------------------------
# ----- data splitting functions ------------------------
# ---------------------------------------------------------

def bootstrap_group(nsubj, ngroups):
    """
    Split the proposed group into redundant subgroups by bootstrap

    Parameters
    ----------
    nsubj (int) the number of subjects in the population
    ngroups(int) Number of subbgroups to be drawn

    Returns
    -------
    samples: a list of ngroups arrays containing
             the indexes of the subjects in each subgroup
    """
    groupsize = nsubj
    samples= [(groupsize*np.random.rand(groupsize)).astype(np.int)
             for i in range(ngroups)]
    return samples

def split_group(nsubj, ngroups):
    """
    Split the proposed group into random disjoint subgroups

    Parameters
    ----------
    nsubj (int) the number of subjects to be split
    ngroups(int) Number of subbgroups to be drawn

    Returns
    -------
    samples: a list of ngroups arrays containing
             the indexes of the subjects in each subgroup
    """
    groupsize = int(np.floor(nsubj/ngroups))
    rperm = np.argsort(np.random.rand(nsubj))
    samples= [rperm[i*groupsize:(i+1)*groupsize] for i in range(ngroups)]
    return samples


# ---------------------------------------------------------
# ----- statistic computation -----------------------------
# ---------------------------------------------------------

def ttest(x):
    """
    returns the t-test for each row of the data x
    """
    import nipy.neurospin.group.onesample as fos
    t = fos.stat(x.T,id='student',axis=0)
    return np.squeeze(t)
    #t = x.mean(1)/x.std(1)*np.sqrt(x.shape[1]-1)
    #return t

def fttest(x,vx):
    """
    Assuming that x and vx represent a effect and variance estimates,    
    returns a cumulated ('fixed effects') t-test of the data over each row

    Parameters
    ----------
    x: array of shape(nrows, ncols): effect matrix
    vx: array of shape(nrows, ncols): variance matrix

    Returns
    -------
    t array of shape(nrows): fixed effect statistics array
    """
    if np.shape(x)!=np.shape(vx):
       raise ValueError, "incompatible dimensions for x and vx"
    n = x.shape[1]
    t = x/np.sqrt(vx)
    t = t.mean(1)*np.sqrt(n)
    return t
    
def mfx_ttest(x, vx):
    """
    Idem fttest, but returns a mixed-effects statistic 
    
    Parameters
    ----------
    x: array of shape(nrows, ncols): effect matrix
    vx: array of shape(nrows, ncols): variance matrix

    Returns
    -------
    t array of shape(nrows): mixed effect statistics array
    """
    import nipy.neurospin.group.onesample as fos
    t = fos.stat_mfx(x.T,vx.T,id='student_mfx',axis=0)
    return np.squeeze(t)

def voxel_thresholded_ttest(x,threshold):
    """returns a binary map of the ttest>threshold
    """
    t = ttest(x)
    return t>threshold

def statistics_from_position(target, data, sigma=1.0):
    """
    return a number characterizing how close data is from
    target using a kernel-based statistic
    
    Parameters
    ----------
    target: array of shape(nt,anat_dim) or None
            the target positions
    data: array of shape(nd,anat_dim) or None
          the data position
    sigma=1.0 (float), kernel parameter
              or  a distance that say how good good is 

    Returns
    -------
    sensitivity (float): how well the targets are fitted
                by the data  in [0,1] interval
                1 is good
                0 is bad
    """
    from nipy.neurospin.eda.dimension_reduction import Euclidian_distance as ed
    if data==None:
        if target==None:
            return 0.# or 1.0, can be debated
        else:
            return 0.
    if target==None:
        return 0.
    
    dmatrix = ed(data,target)/sigma
    sensitivity = dmatrix.min(0)
    sensitivity = np.exp(-0.5*sensitivity**2)
    sensitivity = np.mean(sensitivity)
    return sensitivity


# -------------------------------------------------------
# ---------- The main functions -----------------------------
# -------------------------------------------------------


def voxel_reproducibility(data, vardata, xyz, ngroups, method='crfx',
                          swap=False, verbose=0, **kwargs):
    """
    return a measure of voxel-level reproducibility
    of activation patterns

    Parameters
    ----------
    data: array of shape (nvox,nsubj)
          the input data from which everything is computed
    vardata: array of shape (nvox,nsubj)
             the corresponding variance information
    xyz array of shape (nvox,3) 
        the grid ccordinates of the imput voxels
    ngroups (int): 
             Number of subbgroups to be drawn  
    threshold (float): 
              binarization threshold (makes sense only if method==rfx)
    method='crfx', string, to be chosen among 'crfx', 'cmfx', 'cffx'
           inference method under study
    verbose=0 : verbosity mode

    Returns
    -------
    kappa (float): the desired  reproducibility index
    """
    nsubj = data.shape[1]
    rmap = map_reproducibility(data, vardata, xyz, ngroups, method, 
                                     swap, verbose, **kwargs)

    h = np.array([np.sum(rmap==i) for i in range(ngroups+1)])
    hr = histo_repro(h)  
    return hr

def voxel_reproducibility_old(data, vardata, xyz, ngroups, method='crfx',
                          swap=False, verbose=0, **kwargs):
    """
    see voxel_reproducibility API    
    
    Note
    ----
    This uses  the mixture of binomial heuristic, which has been abandoned now  
    """
    nsubj = data.shape[1]
    rmap = map_reproducibility(data, vardata, xyz, ngroups, method, 
                                     swap, verbose, **kwargs)

    import two_binomial_mixture as mtb
    MB = mtb.TwoBinomialMixture()
    MB.estimate_parameters(rmap, ngroups+1)
    if verbose:
        h = np.array([np.sum(rmap==i) for i in range(ngroups+1)])
        MB.show(h)
    return MB.kappa()


def draw_samples(nsubj, ngroups, split_method='default'):
    """
    Draw randomly ngroups sets of samples from [0..nsubj-1]
    
    Parameters
    ----------
    nsubj, int, the total number of items
    ngroups, int, the number of desired groups
    split_method= 'default', string to be chosen among 'default', 'bootstrap', 'jacknife'
                  if 'bootstrap', then each group will be nsubj 
                     drawn with repetitions among nsubj
                  if 'jacknife' the population is divided into ngroups disjoint equally-sized 
                     subgroups
                  if 'default', 'bootstrap' is used when nsubj<10*ngroups
                     otherwise jacknife is used
                  
    Returns
    -------
    samples, a list of ngroups array that represent the subsets.

    fixme : this should allow variable bootstrap, i.e. draw ngroups of groupsize among nsubj
    """
    if split_method=='default':
        if nsubj>10*ngroups:
            samples = split_group(nsubj, ngroups)
        else:
            samples = bootstrap_group(nsubj, ngroups)
    elif split_method=='bootstrap':
        samples = bootstrap_group(nsubj, ngroups)      
    elif split_method=='':
        samples = plit_group(nsubj, ngroups)
    else: raise ValueError, 'unknown splitting method'
 
    return samples

def map_reproducibility(data, vardata, xyz, ngroups, method='crfx',
                        swap=False, verbose=0, **kwargs):
    """
    return a reproducibility map for the given method

    Parameters
    ----------
    data: array of shape (nvox,nsubj)
          the input data from which everything is computed
    vardata: array of the same size
             the corresponding variance information
    xyz array of shape (nvox,3) 
        the grid ccordinates of the imput voxels
    ngroups (int): the size of each subrgoup to be studied
    threshold (float): binarization threshold
              (makes sense only if method==rfx)
    method='crfx', string to be chosen among 'crfx', 'cmfx', 'cffx' 
           inference method under study
    verbose=0 : verbosity mode

    Returns
    -------
    rmap: array of shape(nvox)
          the reproducibility map
    """
    nsubj = data.shape[1]
    nvox = data.shape[0]
    samples = draw_samples(nsubj, ngroups)
    rmap = np.zeros(nvox)
    
    for i in range(ngroups):
        x = data[:,samples[i]]

        if swap:
           # randomly swap the sign of x
           x *= (2*(np.random.rand(len(samples[i]))>0.5)-1)
        
        vx = vardata[:,samples[i]]
        csize = kwargs['csize']
        threshold = kwargs['threshold']

        # compute the statistical maps according to the method you like
        if method=='crfx':
            smap = ttest(x)
        elif method=='cffx':
            smap = fttest(x,vx)
        elif method=='cmfx':
            smap = mfx_ttest(x,vx)
        else: raise ValueError, 'unknown method'

        # add the binarized map to a reproducibility map
        rmap += cluster_threshold(smap, xyz, threshold, csize)>0

    return rmap


def cluster_reproducibility(data, vardata, xyz, ngroups, coord, sigma,
                            method='crfx', swap=False, verbose=0, 
                            **kwargs):
    """
    return a measure of cluster-level reproducibility
    of activation patterns
    (i.e. how far clusters are from each other)

    Parameters
    ----------
    data: array of shape (nvox,nsubj)
          the input data from which everything is computed
    vardata: array of shape (nvox,nsubj)
             the variance of the data that is also available
    xyz array of shape (nvox,3) 
        the grid ccordinates of the imput voxels
    ngroups (int),
             Number of subbgroups to be drawn
    coord: array of shape (nvox,3) 
           the corresponding physical coordinates
    sigma (float): parameter that encodes how far far is
    threshold (float): 
              binarization threshold
    method='crfx', string to be chosen among 'crfx', 'cmfx' or 'cffx' 
           inference method under study
    swap = False: if True, a random sign swap of the data is performed
         This is used to simulate a null hypothesis on the data.
    verbose=0 : verbosity mode
    
    Returns
    -------
    score (float): the desired  cluster-level reproducibility index
    """
    tiny = 1.e-15
    nsubj = data.shape[1]
    samples = draw_samples(nsubj, ngroups)
    all_pos = []

    # compute the positions in the different subgroups
    for i in range(ngroups):           
        x = data[:,samples[i]]

        if swap:
           # apply a random sign swap to x
           x *= (2*(np.random.rand(len(samples[i]))>0.5)-1)

        vx = vardata[:,samples[i]]
        if method!='bsa':
            csize = kwargs['csize']
            threshold = kwargs['threshold']
           
            if method =='crfx':
                smap = ttest(x)
            elif method == 'cmfx':
                smap = mfx_ttest(x,vx)
            elif method == 'cffx':
                smap = fttest(x,vx)
            pos = get_cluster_position_from_thresholded_map(smap, xyz, coord,
                                                            threshold, csize)
            all_pos.append(pos)
        else: 
            # method='bsa' is a special case
            tx = x/(tiny+np.sqrt(vx))
            afname = kwargs['afname']
            shape = kwargs['shape']
            affine = kwargs['affine']
            theta = kwargs['theta']
            dmax = kwargs['dmax']
            ths = kwargs['ths']
            thq = kwargs['thq']
            smin = kwargs['smin']
            niter = kwargs['niter']
            afname = afname+'_%02d_%04d.pic'%(niter,i)
            pos = coord_bsa(xyz, coord, tx, affine, shape, theta, dmax,
                            ths, thq, smin, afname)
        all_pos.append(pos)

    # derive a kernel-based goodness measure from the pairwise comparison
    # of sets of positions
    score = 0
    for i in range(ngroups):
        for j in range(i):
            score += statistics_from_position(all_pos[i], all_pos[j], sigma)
            score += statistics_from_position(all_pos[j], all_pos[i], sigma)
            
    score /= (ngroups*(ngroups-1))
    return score



# -------------------------------------------------------
# ---------- BSA stuff ----------------------------------
# -------------------------------------------------------

def coord_bsa(xyz, coord, betas, affine=np.eye(4), shape=None, theta=3.,
              dmax=5., ths=0, thq=0.5, smin=0, afname='/tmp/af.pic'):
    """
    main function for  performing bsa on a dataset
    where bsa =  nipy.neurospin.spatial_models.bayesian_structural_analysis

    Parameters
    ----------
    xyz array of shape (nnodes,3):
        the grid coordinates of the field
    coord array of shape (nnodes,3):
          spatial coordinates of the nodes
    betas: an array of shape (nbnodes, subjects):
           the multi-subject statistical maps       
    affine: array of shape (4,4) affine transformation
            to map grid coordinates to positions
    shape=None : shape of the implicit grid on which everything is defined
    theta = 3.0 (float): first level threshold
    dmax = 5. float>0:
         expected cluster std in the common space in units of coord
    ths = 0 (int, >=0) : representatitivity threshold
    thq = 0.5 (float): posterior significance threshold should be in [0,1]
    smin = 0 (int): minimal size of the regions to validate them
    afname = '/tmp/af.pic': place where intermediate resullts wam be written
    
    Returns
    -------
    afcoord array of shape(number_of_regions,3):
            coordinate of the found landmark regions
    
    """
    import nipy.neurospin.spatial_models.bayesian_structural_analysis as bsa
    import nipy.neurospin.graph.field as ff
    import  pickle
    
    nbvox = np.shape(xyz)[0]

    # create the field strcture that encodes image topology
    Fbeta = ff.Field(nbvox)
    Fbeta.from_3d_grid(xyz.astype(np.int),18)

    # volume density
    voxvol = np.absolute(np.linalg.det(affine))
    g0 = 1.0/(voxvol*nbvox)

    crmap,AF,BF,p = bsa.compute_BSA_simple_quick(Fbeta, betas, coord, dmax, xyz,
                                            affine, shape, thq, smin,ths, theta,
                                            g0, verbose=0)
    if AF==None:
        return None
    pickle.dump(AF, open(afname, 'w'), 2)
    afcoord = AF.discrete_to_roi_features('position')
    return afcoord


