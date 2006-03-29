import unittest, os, scipy, glob, sets
import numpy as N
from neuroimaging.image import Image

class AnalyzeImageTest(unittest.TestCase):

    def setUp(self):
        imgname = '/usr/share/BrainSTAT/repository/kff.stanford.edu/~jtaylo/BrainSTAT/avg152T1.img'
        self.img = Image(imgname)

    def tearDown(self):
        tmpf = glob.glob('tmp.*')
        for f in tmpf:
            os.remove(f)

    def test_analyze(self):
        y = self.img.readall()
        self.assertEquals(y.shape, tuple(self.img.grid.shape))
        y.shape = N.product(y.shape)
        self.assertEquals(N.maximum.reduce(y), 437336.375)
        self.assertEquals(N.minimum.reduce(y), 0.)

    def test_slice1(self):
        x = self.img.getslice(3)
        self.assertEquals(x.shape, tuple(self.img.grid.shape[1:]))
        
    def test_slice2(self):
        x = self.img.getslice(slice(3,5))
        self.assertEquals(x.shape, (2,) + tuple(self.img.grid.shape[1:]))

    def test_slice3(self):
        s = slice(0,20,2)
        x = self.img.getslice(s)
        self.assertEquals(x.shape, (10,) + tuple(self.img.grid.shape[1:]))

    def test_slice4(self):
        s = slice(0,self.img.grid.shape[0])
        x = self.img.getslice(s)
        self.assertEquals(x.shape, tuple((self.img.grid.shape)))

    def test_slice5(self):
        s1 = slice(0,20,2)
        s2 = slice(0,50,5)
        x = self.img.getslice([s1,s2])
        self.assertEquals(x.shape, (10,10,self.img.grid.shape[2]))

    def test_array(self):
        x = self.img.toarray()
        
    def test_file(self):
        x = self.img.tofile('tmp.img')

    def test_nondiag(self):
        self.img.grid.mapping.transform[0,1] = 3.0
        x = self.img.tofile('tmp.img')
        scipy.testing.assert_almost_equal(x.grid.mapping.transform, self.img.grid.mapping.transform)

    def test_clobber(self):
        x = self.img.tofile('tmp.img', clobber=True)
        a = Image('tmp.img')
        A = a.readall()
        I = self.img.readall()
        z = N.add.reduce(((A-I)**2).flat)
        self.assertEquals(z, 0.)
        t = a.grid.mapping.transform
        b = self.img.grid.mapping.transform
        scipy.testing.assert_almost_equal(b, t)

    def test_iter(self):
        I = iter(self.img)
        for i in I:
            self.assertEquals(i.shape, (109,91))

    def test_labels1(self):
        rho = Image('http://kff.stanford.edu/~jtaylo/BrainSTAT/rho.img')
        labels = (rho.readall() * 100).astype(N.Int)
        test = Image(N.zeros(labels.shape), grid=rho.grid)
        test.grid.itertype = 'parcel'
        test.grid.labels = labels
        labels.shape = N.product(labels.shape)
        test.grid.labelset = sets.Set(N.unique(labels))

        v = 0
        for t in test:
            v += t.shape[0]
        self.assertEquals(v, N.product(test.grid.shape))

    def test_labels2(self):
        rho = Image('http://kff.stanford.edu/~jtaylo/BrainSTAT/rho.img')
        labels = (rho.readall() * 100).astype(N.Int)
        test = Image(N.zeros(labels.shape), grid=rho.grid)

        test.grid.itertype = 'parcel'
        test.grid.labels = labels
        labels.shape = N.product(labels.shape)
        test.grid.labelset = sets.Set(N.unique(labels))

        v = 0
        iter(test)
        while True:
            try:
                test.next(data=v)
                v += 1
            except StopIteration:
                break

    def test_labels3(self):
        rho = Image('http://kff.stanford.edu/~jtaylo/BrainSTAT/rho.img')
        labels = (rho.readall() * 100).astype(N.Int)
        shape = labels.shape
        labels.shape = N.product(labels.shape)
        labelset = sets.Set(N.unique(labels))

        test = Image(N.zeros(shape), grid=rho.grid)
        test.grid.itertype = 'parcel'
        test.grid.labels = labels
        test.grid.labelset = labelset

        v = 0

        for t in test:
            v += t.shape[0]
        self.assertEquals(v, N.product(test.grid.shape))
        

def suite():
    suite = unittest.makeSuite(AnalyzeImageTest)
    return suite

if __name__ == '__main__':
    unittest.main()