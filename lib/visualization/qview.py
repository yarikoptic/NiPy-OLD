import sys, pylab
import neuroimaging.image as image
import neuroimaging.visualization.viewer as viewer

x = image.Image(sys.argv[1])
v = viewer.BoxViewer(x)

if len(sys.argv) == 3:
    m, M = map(float, sys.argv[1:])
    v.m = m
    v.M = M

v.draw()
pylab.show()
