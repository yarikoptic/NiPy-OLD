"""
Example of a script that crates a 'hierarchical roi' structure
from the blob model of an image

fixme : redo it
Used mainly for debugging at the moment (before unittests are created)

This example is based on a (simplistic) simulated image.
# Author : Bertrand Thirion, 2008-2009
"""

import numpy as np


import nipy.neurospin.spatial_models.hroi as hroi
import nipy.neurospin.utils.simul_2d_multisubject_fmri_dataset as simul
import nipy.neurospin.graph.field as ff

##############################################################################
# simulate the data
dimx = 60
dimy = 60
pos = 2*np.array([[6,7],[10,10],[15,10]])
ampli = np.array([3,4,4])

dataset = simul.make_surrogate_array(nbsubj=1, dimx=dimx, dimy=dimy, pos=pos,
                                     ampli=ampli, width=10.0).squeeze()

dataset = np.reshape(dataset, (dimx, dimy,1))
ref_dim = (dimx,dimy,1)
xyz = np.array(np.where(dataset)).T
nbvox = np.size(xyz, 0)
affine = np.eye(4)
shape = (dimx,dimy,1)

# create the field strcture that encodes image topology
Fbeta = ff.Field(nbvox)
Fbeta.from_3d_grid(xyz.astype(np.int), 18)
beta = np.reshape(dataset,(nbvox,1))
Fbeta.set_field(beta)
nroi = hroi.NROI_from_field(Fbeta, affine, shape, xyz, th=2.0, smin = 10)
if nroi != None:
    n1 = nroi.copy()
    n2 = nroi.reduce_to_leaves()

td = n1.depth_from_leaves()
a = np.argmax(td)
lv = n1.rooted_subtree(a)
u = nroi.cc()
u = np.nonzero(u == u[0])[0]

nroi.set_discrete_feature_from_index('activation',beta)
nroi.discrete_to_roi_features('activation')


label = -np.ones((dimx,dimy))
for k in range(nroi.k):
    label[nroi.xyz[k][:,0],nroi.xyz[k][:,1]]=k
import matplotlib.pylab as mp
mp.figure()
mp.imshow(label,interpolation='Nearest')
mp.show()
