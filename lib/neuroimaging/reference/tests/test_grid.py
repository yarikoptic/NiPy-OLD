import unittest

import numpy as N

from neuroimaging.reference.axis import space
from neuroimaging.reference.grid import SamplingGrid, ConcatenatedGrids, \
     ConcatenatedIdenticalGrids

from neuroimaging.image.formats.analyze import ANALYZE
from neuroimaging.tests.data import repository

class GridTest(unittest.TestCase):

    def setUp(self):
        self.img = ANALYZE("avg152T1", repository)

    def test_concat(self):
        grids = ConcatenatedGrids([self.img.grid]*5)
        self.assertEquals(tuple(grids.shape), (5,) + tuple(self.img.grid.shape))
        z = grids.mapping(N.transpose([4,5,6,7]))
        a = grids.subgrid(0)
        x = a.mapping(N.transpose([5,6,7]))

    def test_replicate(self):
        grids = self.img.grid.replicate(4)
        self.assertEquals(tuple(grids.shape), (4,) + tuple(self.img.grid.shape))
        z = grids.mapping(N.transpose([2,5,6,7]))
        a = grids.subgrid(0)
        x = a.mapping(N.transpose([5,6,7]))

    def test_replicate2(self):
        """
        Test passing
        """
        grids = self.img.grid.replicate(4)
        grids.python2matlab()

    def test_concat2(self):
        """
        Test passing
        """
        grids = ConcatenatedIdenticalGrids(self.img.grid, 4)
        grids.python2matlab()

    def test_concat3(self):
        """
        Test failing
        """
        grids = ConcatenatedGrids([self.img.grid]*4)
        grids.python2matlab()

    def test_identity(self):
        shape = (30,40,50)
        i = SamplingGrid.identity(shape=shape, names=space)
        self.assertEquals(tuple(i.shape), shape)
        y = i.mapping.map([3,4,5])
        N.testing.assert_almost_equal(y, N.array([3,4,5]))

    def test_identity2(self):
        shape = (30, 40)
        self.assertRaises(ValueError, SamplingGrid.identity, shape, space)

    def test_allslice(self):
        shape = (30,40,50)
        i = SamplingGrid.identity(shape=shape, names=space)
        print i.allslice()
        
    def test_iterslices(self):
        for i in range(3):
            self.img.grid.set_iter("slice", axis=i)
            self.assertEqual(len(list(iter(self.img.grid))), self.img.grid.shape[i])
        
        parcelmap = N.zeros(self.img.grid.shape)
        parcelmap[:3,:5,:4] = 1
        parcelmap[3:10,5:10,4:10] = 2
        parcelseq = (1, (0,2))
        self.img.grid.set_iter("parcel", parcelmap=parcelmap, parcelseq=parcelseq)
        for i in iter(self.img.grid):
            print i
            print self.img[i.where]

        print len(parcelmap)
        parcelseq = (1, (1,2), 0) + (0,)*(len(parcelmap)-3)
        self.img.grid.set_iter("slice/parcel", parcelseq=parcelseq)                
        for i, it in enumerate(iter(self.img.grid)):
            print it.where, self.img.grid.shape
            print self.img[i,it.where]

if __name__ == '__main__':
    unittest.main()
