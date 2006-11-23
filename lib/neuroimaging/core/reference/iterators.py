#
# This is demonstration code to help thrash out ideas for the new iterator
# proposal. This will most likely change and shouldn't be used. See the
# end of the file for example usage.
#
# See http://projects.scipy.org/neuroimaging/ni/wiki/ImageIterators

import numpy as N

class Iterator(object):

    def __init__(self, img, mode='r'):
        self.img = img
        self.mode = mode

    def __iter__(self):
        return self
    

    def next(self):
        if self.mode == 'r':
            return self._next().get()
        else:
            return self._next()

    
    def _next(self):
        raise NotImplementedError


class IteratorItem(object):

    def __init__(self, img, slice):
        self.img = img
        self.slice = slice

    def get(self):
        return self.img[self.slice]

    def set(self, value):
        self.img[self.slice] = value


class SliceIterator(Iterator):

    def __init__(self, img, mode='r', axis=0):
        Iterator.__init__(self, img, mode)
        self.axis = axis
        self.shape = self.img.shape
        self.max = self.shape[axis]
        self.n = 0

    def _next(self):
        if self.n >= self.max:
            raise StopIteration
        else:
            slices = [slice(0, shape, 1) for shape in self.shape]
            slices[self.axis] = slice(self.n, self.n+1, 1)
            ret = SliceIteratorItem(self.img, slices)
        self.n += 1
        return ret


class SliceIteratorItem(IteratorItem):

    def get(self):
        return self.img[self.slice].squeeze()

    def set(self, value):
        if type(value) == N.ndarray:
            value = value.reshape(self.img[self.slice].shape)
        self.img[self.slice] = value



if __name__ == '__main__':
    from neuroimaging.core.image.image import Image
    import numpy as N
    img = Image(N.zeros((3, 4, 5)))

    # Slice along the 0th axis
    print "slicing along axis=0"
    for s in SliceIterator(img):
        print s, s.shape


    # Slice along the 1st axis
    print "slicing along axis=1"
    for s in SliceIterator(img, axis=1):
        print s, s.shape

    # Slice along the 2nd axis, writing the z index
    # to each point in the image
    print "Writing z index values"
    z = 0
    for s in SliceIterator(img, axis=2, mode='w'):
        s.set(z)
        z += 1

    print img[:]

    # Slice using the image method interface
    print "slicing with .slice() method"
    for s in img.slice():
        print s, s.shape

    print "...and along axis=1"
    for s in img.slice(axis=1):
        print s, s.shape

    print "...and writing along the y axis"
    y = 0
    for s in img.slice(mode='w', axis=1):
        s.set(y)
        y += 1

    print img[:]


    B = Image(N.zeros((3, 4, 5)))
    B.from_slice(SliceIterator(img))
    print B[:]

    B = Image(N.zeros((4, 3, 5)))
    B.from_slice(SliceIterator(img), axis=1)
    print B[:]

    B = Image(N.zeros((3, 5, 4)))
    B.from_slice(SliceIterator(img, axis=2), axis=1)
    print B[:]
    
