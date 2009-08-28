"""
This module is the interface to the bayesian_structural_analysis (bsa) module
It handles the images provided as input and produces result images.

"""

import numpy as np
import os.path as op
from nipy.io.imageformats import load, save, Nifti1Image

import nipy.neurospin.spatial_models.bayesian_structural_analysis as bsa
import nipy.neurospin.graph.field as ff


def make_bsa_nifti(mask_images, betas, theta=3., dmax= 5., ths=0, thq=0.5,
                   smin=0, swd="/tmp/",method='simple',subj_id=None,nbeta=0):
    """
    main function for  performing bsa on a set of images.
    It creates the some output images in the given directory

    Parameters
    ------------
    mask_images: A list of image paths that yield binary images,
                 one for each subject
                 the number os subjects, nsubj, is taken as len(mask_images)
    betas: A list of image paths that yields the activation images,
           one for each subject
    theta=3., threshold used to ignore all the image data that si below
    dmax=5., prior width of the spatial model;
             corresponds to multi-subject uncertainty 
    ths=0: threshold on the representativity measure of the obtained
           regions
    thq=0.5: p-value of the representativity test:
             test = p(representativity>ths)>thq
    smin=0: minimal size (in voxels) of the extracted blobs
            smaller blobs are merged into larger ones
    swd='/tmp': writedir
    method='simple': applied region detection method; to be chose among
                     'simple', 'dev','ipmi'
    subj_id=None: list of int identifiers (<10000) of the subjects.
                  by default it is range(nsubj)
    nbeta=0 (int): numerical identifier of the contrast
 
    Returns
    -------
    AF: an nipy.neurospin.spatial_models.structural_bfls.landmark_regions
        instance that describes the structures found at the group level
         None is returned if nothing has been found significant 
         at the group level
    BF : a list of nipy.neurospin.spatial_models.hroi.Nroi instances
       (one per subject) that describe the individual coounterpart of AF

    """
    # Sanity check
    if len(mask_images)!=len(betas):
        raise ValueError,"the number of masks and activation images\
        should be the same"
    nsubj = len(mask_images)
    if subj_id==None:
        bru = range(nsubj)
    
    # Read the referential information
    nim = load(mask_images[0])
    header = nim.get_header()
    ref_dim = nim.get_shape()
    affine = nim.get_affine()
    
    # Read the masks and compute the "intersection"
    mask = np.zeros(ref_dim)
    for s in range(nsubj):
        nim = load(mask_images[s])
        temp = nim.get_data()
        mask = mask+temp;

    xyz = np.array(np.where(mask>nsubj/2)).T
    nvox = xyz.shape[0]

    # create the field strcture that encodes image topology
    Fbeta = ff.Field(nvox)
    Fbeta.from_3d_grid(xyz.astype(np.int),18)

    # Get  coordinates in mm
    xyz = np.hstack((xyz,np.ones((nvox,1))))
    coord = np.dot(xyz,affine.T)[:,:3]
    xyz = xyz.astype(np.int)
    
    # read the functional images
    lbeta = []
    for s in range(nsubj):
        rbeta = load(betas[s])
        beta = rbeta.get_data()
        beta = beta[mask>nsubj/2]
        lbeta.append(beta)
    lbeta = np.array(lbeta).T

    # launch the method
    g0 = 1.0/(np.absolute(np.linalg.det(affine))*nvox)
    bdensity = 1
    crmap = np.zeros(nvox)
    p = np.zeros(nvox)
    AF = None
    BF = [None for s in range(nsubj)]
    if method=='ipmi':
        crmap,AF,BF,p = bsa.compute_BSA_ipmi(Fbeta,lbeta,coord,dmax,xyz[:,:3],
                                             header,thq, smin,ths, theta,g0,
                                             bdensity)
    if method=='dev':
        crmap,AF,BF,p = bsa.compute_BSA_dev (Fbeta,lbeta,coord,dmax,xyz[:,:3],
                                             header,thq, smin,ths, theta,g0,
                                             bdensity,verbose=1)
    if method=='simple':
        crmap,AF,BF,p = bsa.compute_BSA_simple (Fbeta,lbeta,coord,dmax,xyz[:,:3],
                                                header,thq, smin,ths, theta,g0,
                                                verbose=0)

    # Write the results
    LabelImage = op.join(swd,"CR_%04d.nii"%nbeta)
    Label = -2*np.ones(ref_dim,'int16')
    Label[mask>nsubj/2] = crmap.astype('i')
    wim = Nifti1Image (Label, affine)
    wim.get_header()['descrip'] = 'group Level labels from bsa procedure'
    save(wim, LabelImage)

    if AF==None:
        default_idx = 0
    else:
        default_idx = AF.k+2
        
    if bdensity:
        DensImage = op.join(swd,"density_%04d.nii"%nbeta)
        density = np.zeros(ref_dim)
        density[mask>nsubj/2]=p
        wim = Nifti1Image (density, affine)
        wim.get_header()['descrip'] = 'group-level spatial density of active regions'
        save(wim, DensImage)
        
    for s in range(nsubj):
        LabelImage = op.join(swd,"AR_s%04d_%04d.nii"%(subj_id[s],nbeta))
        Label = -2*np.ones(ref_dim,'int16')
        Label[mask>nsubj/2]=-1
        if BF[s]!=None:
            nls = BF[s].get_roi_feature('label')
            nls[nls==-1] = default_idx
            for k in range(BF[s].k):
                xyzk = BF[s].xyz[k].T 
                Label[xyzk[0],xyzk[1],xyzk[2]] =  nls[k]
        
        wim = Nifti1Image (Label, affine)
        wim.get_header()['descrip'] = 'Individual label image from bsa procedure'
        save(wim, LabelImage)
        
    return AF,BF
