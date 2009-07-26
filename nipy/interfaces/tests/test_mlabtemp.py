"""Tests for the temporary matlab file module."""

# Stdlib imports
import os
import tempfile

# Our own imports
from nipy.interfaces.matlab import mlab_tempfile

# Functions, classes and other top-level code
def check_mlab_tempfile(dir):
    """Helper function for testing the mlab temp file creation."""

    try:
        f = mlab_tempfile(dir)
    except OSError,msg:
        if not os.path.isdir(dir) and 'No such file or directory' in msg:
            # This is OK, it's the expected error
            return True
        else:
            raise
    else:
        f.close()


def test_mlab_tempfile():
    for dir in [None,tempfile.tempdir,tempfile.mkdtemp()]:
        yield check_mlab_tempfile,dir
