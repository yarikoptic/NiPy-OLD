"""
Demo ward clustering on a graph.
"""
print __doc__

import numpy as np
from numpy.random import randn, rand
import matplotlib.pylab as mp

from nipy.neurospin import graph
from nipy.neurospin.clustering.hierarchical_clustering import ward

# n = number of points, k = number of nearest neighbours
n = 100
k = 5
verbose = 0

X = randn(n,2)
X[:np.ceil(n/3)] += 3		
G = graph.WeightedGraph(n)
#G.mst(X)
G.knn(X, 5)
tree = ward(G, X, verbose)


u = tree.partition(1.0)

mp.figure()
mp.subplot(1,2,1)
for i in range(u.max()+1):
    mp.plot(X[u==i,0], X[u==i,1],'o', color=(rand(), rand(), rand()))

mp.axis('tight')
mp.axis('off')
mp.title('clustering into clusters of inertia<1')

u = tree.split(k)
mp.subplot(1,2,2)
for e in range(G.E):
    mp.plot([X[G.edges[e,0],0], X[G.edges[e,1],0]],
            [X[G.edges[e,0],1], X[G.edges[e,1],1]], 'k')
for i in range(u.max()+1):
    mp.plot(X[u==i,0], X[u==i,1], 'o', color=(rand(), rand(), rand()))
mp.axis('tight')
mp.axis('off')
mp.title('clustering into 5 clusters')



nl = np.sum(tree.isleaf())
validleaves = np.zeros(n)
validleaves[:np.ceil(n/4)]=1
valid = np.zeros(tree.V, 'bool')
valid[tree.isleaf()] = validleaves.astype('bool')
nv =  np.sum(validleaves)
nv0 = 0
while nv>nv0:
    nv0= nv
    for v in range(tree.V):
        if valid[v]:
            valid[tree.parents[v]]=1
    nv = np.sum(valid)
    
ax = tree.fancy_plot_(valid)
ax.axis('off')

mp.show()

if verbose:
    print 'List of sub trees'
    print tree.list_of_subtrees()
