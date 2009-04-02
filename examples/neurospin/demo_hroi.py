"""
Example of a script that crates a 'hierarchical roi' structure
from the blob model of an image

Used mainly for debugging at the moment

This example is based on a (simplistic) simulated image.

"""
# Author : Bertrand Thirion, 2008-2009

import numpy as np
import scipy.stats as st
import os.path as op
import neuroimaging.neurospin.spatial_models.hroi as hroi
import fff2.utils.simul_2d_multisubject_fmri_dataset as simul
import fff2.graph.field as ff

################################################################################
# simulate the data
dimx = 60
dimy = 60
pos = 2*np.array([[6,7],[10,10],[15,10]])
ampli = np.array([3,4,4])

dataset = simul.make_surrogate_array(nbsubj=1, dimx=dimx, dimy=dimy, pos=pos, ampli=ampli, width=10.0).squeeze()

dataset = np.reshape(dataset, (dimx, dimy,1))
ref_dim = (dimx,dimy,1)
xyz = np.array(np.where(dataset)).T
nbvox = np.size(xyz, 0)
    
# create the field strcture that encodes image topology
Fbeta = ff.Field(nbvox)
Fbeta.from_3d_grid(xyz.astype(np.int), 18)
beta = np.reshape(dataset,(nbvox,1))
Fbeta.set_field(beta)
nroi = hroi.NROI_from_field(Fbeta,None,xyz,th=2.0,smin = 5)
