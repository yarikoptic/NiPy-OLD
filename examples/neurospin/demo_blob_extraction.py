"""
This scipt generates a noisy activation image image
and extracts the blob from it.

Author : Bertrand Thirion, 2009
"""
#autoindent

import numpy as np
import pylab as pl
import matplotlib

import nipy.neurospin.graph.field as ff
import nipy.neurospin.utils.simul_2d_multisubject_fmri_dataset as simul
import nipy.neurospin.spatial_models.hroi as hroi

# simulatean activation image
dimx = 60
dimy = 60
pos = 2*np.array([[6,7],[10,10],[15,10]])
ampli = np.array([3,4,4])

nbvox = dimx*dimy
dataset = simul.make_surrogate_array(nbsubj=1, dimx=dimx, dimy=dimy,
                                     pos=pos, ampli=ampli, width=10.0)
x = np.reshape(dataset, (dimx, dimy, 1))
beta = np.reshape(x, (nbvox, 1))

xyz = np.array(np.where(x)).T
nbvox = np.size(xyz, 0)

# build the field instance
F = ff.Field(nbvox)
F.from_3d_grid(xyz, 18)
F.set_field(beta)

# compute the blobs
th = 2.36
smin = 5
affine = np.eye(4)
shape = (dimx, dimy, 1)
nroi = hroi.NROI_from_field(F, affine, shape, xyz, refdim=0, th=th, smin = smin)

bmap = np.zeros(nbvox)
label = -np.ones(nbvox)

if nroi!=None:
    # compute the average signal within each blob
    nroi.set_discrete_feature_from_index('activation',beta)
    bfm = nroi.discrete_to_roi_features('activation')

    # plot the input image 
    idx = nroi.discrete_features['index']
    for k in range(nroi.k):
        bmap[idx[k]] = bfm[k]
        label[idx[k]] = k
        
label = np.reshape(label,(dimx,dimy))
bmap = np.reshape(bmap,(dimx,dimy))

aux1 = (0-x.min())/(x.max()-x.min())
aux2 = (bmap.max()-x.min())/(x.max()-x.min())
cdict = {'red': ((0.0, 0.0, 0.7), 
                 (aux1, 0.7, 0.7),
                 (aux2, 1.0, 1.0),
                 (1.0, 1.0, 1.0)),
         'green': ((0.0, 0.0, 0.7),
                   (aux1, 0.7, 0.0),
                   (aux2, 1.0, 1.0),
                   (1.0, 1.0, 1.0)),
         'blue': ((0.0, 0.0, 0.7),
                  (aux1, 0.7, 0.0),
                  (aux2, 0.5, 0.5),
                  (1.0, 1.0, 1.0))}
my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)

pl.figure(figsize=(12, 3))
pl.subplot(1, 3, 1)
pl.imshow(np.squeeze(x), interpolation='nearest', cmap=my_cmap)
cb = pl.colorbar()
for t in cb.ax.get_yticklabels():
    t.set_fontsize(16)
    
pl.axis('off')
pl.title('Thresholded data')

# plot the blob label image
pl.subplot(1, 3, 2)
pl.imshow(label, interpolation='nearest')
pl.colorbar()
pl.title('Blob labels')

# plot the blob-averaged signal image
aux = 0.01#(th-bmap.min())/(bmap.max()-bmap.min())
cdict = {'red': ((0.0, 0.0, 0.7), (aux, 0.7, 0.7), (1.0, 1.0, 1.0)),
         'green': ((0.0, 0.0, 0.7), (aux, 0.7, 0.0), (1.0, 1.0, 1.0)),
         'blue': ((0.0, 0.0, 0.7), (aux, 0.7, 0.0), (1.0, 0.5, 1.0))}
my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict, 256)

pl.subplot(1, 3, 3)
pl.imshow(bmap, interpolation='nearest', cmap=my_cmap)
cb = pl.colorbar()
for t in cb.ax.get_yticklabels():
    t.set_fontsize(16)
pl.axis('off')
pl.title('Blob average')
pl.show()
