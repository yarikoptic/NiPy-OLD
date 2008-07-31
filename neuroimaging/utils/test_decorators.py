class Needs:
    def __init__(self, flag):
        self.flag = flag

    def __call__(self, *args, **kw):
        print ("Test not run. Requires %s flag"  % self.flag)

def _flag(func, flag):
    from neuroimaging.utils.testutils import FLAGS
    if flag not in FLAGS and "all" not in FLAGS:
        return Needs(flag)
    else:
        return func

def slow(func):    
    return _flag(func, "slow")

def gui(func):    
    return _flag(func, "gui")

def data(func):    
    from neuroimaging.utils.testutils import FLAGS
    flag = "data"
    if flag not in FLAGS and "all" not in FLAGS:
        return Needs(flag)
    else:
        def _f(self):
            self.data_setUp()
            return func(self)
        return _f



if __name__ == '__main__':
    @dec.slow
    def foo(x, y, z):
        print "foo"


    foo(1, 2, 3)
