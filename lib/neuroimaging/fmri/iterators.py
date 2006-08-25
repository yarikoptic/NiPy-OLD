from neuroimaging.reference.iterators import SliceIterator, SliceParcelIterator

class fMRISliceIterator(SliceIterator):
    """
    Instead of iterating over slices of a 4d file -- return slices of
    timeseries.
    """

    def __init__(self, end, **kwargs):
        kwargs["axis"]=1
        SliceIterator.__init__(self, end, **kwargs)
        self.nframe = self.end[0]


class fMRISliceParcelIterator(SliceParcelIterator):
    "Return parcels of timeseries within slices."

    def __init__(self, parcelmap, parcelseq, nframe):
        SliceParcelIterator.__init__(self, parcelmap, parcelseq)
        self.nframe = nframe

    def next(self):
        value = SliceParcelIterator.next(self)
        return SliceParcelIterator.Item(
            value.label, value.where,(slice(0,self.nframe), value.slice))

