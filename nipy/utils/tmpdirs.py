''' Contexts for *with* statement providing temporary directories
'''
from __future__ import with_statement
import os
import shutil
from tempfile import template, mkdtemp


class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.
    
    Upon exiting the context, the directory and everthing contained
    in it are removed.
    
    Example
    -------
    >>> import os
    >>> with TemporaryDirectory() as tmpdir:
    ...     fname = os.path.join(tmpdir, 'example_file.txt')
    ...     with open(fname, 'wt') as fobj:
    ...         fobj.write('a string\\n')
    >>> os.path.exists(tmpdir)
    False
    """
    def __init__(self, suffix="", prefix=template, dir=None, chdir=False):
        self.name = mkdtemp(suffix, prefix, dir)
        self._closed = False

    def __enter__(self):
        return self.name

    def cleanup(self):
        if not self._closed:
            shutil.rmtree(self.name)
            self._closed = True

    def __exit__(self, exc, value, tb):
        self.cleanup()
        return False


class InTemporaryDirectory(TemporaryDirectory):
    ''' Create, return, and change directory to a temporary directory

    Example
    -------
    >>> import os
    >>> my_cwd = os.getcwd()
    >>> with InTemporaryDirectory() as tmpdir:
    ...     assert os.getcwd() != my_cwd
    ...     assert os.getcwd() == tmpdir
    >>> os.path.exists(tmpdir)
    False
    >>> os.getcwd() == my_cwd
    True
    '''
    def __enter__(self):
        self._pwd = os.getcwd()
        os.chdir(self.name)
        return super(InTemporaryDirectory, self).__enter__()

    def __exit__(self, exc, value, tb):
        os.chdir(self._pwd)
        return super(InTemporaryDirectory, self).__exit__(exc, value, tb)


