#!/usr/bin/env python
import sys
from glob import glob
from distutils import log
from distutils.cmd import Command
from distutils.version import LooseVersion

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration(None, parent_package, top_path)
    config.set_options(ignore_setup_xxx_py=True,
                       assume_default_configuration=True,
                       delegate_options_to_subpackages=True,
                       quiet=True)
    # The quiet=True option will silence all of the name setting warnings:
    # Ignoring attempt to set 'name' (from 'nipy.core' to 
    #    'nipy.core.image')
    # Robert Kern recommends setting quiet=True on the numpy list, stating
    # these messages are probably only used in debugging numpy distutils.
    config.get_version('nipy/version.py') # sets config.version
    config.add_subpackage('nipy', 'nipy')
    return config

################################################################################
# For some commands, use setuptools

if len(set(('develop', 'bdist_egg', 'bdist_rpm', 'bdist', 'bdist_dumb', 
            'bdist_wininst', 'install_egg_info', 'egg_info', 'easy_install',
            )).intersection(sys.argv)) > 0:
    from setup_egg import extra_setuptools_args

# extra_setuptools_args can be defined from the line above, but it can
# also be defined here because setup.py has been exec'ed from
# setup_egg.py.
if not 'extra_setuptools_args' in globals():
    extra_setuptools_args = dict()


# Dependency checks
def package_check(pkg_name, version=None,
                  optional=False,
                  checker=LooseVersion,
                  version_getter=None,
                  ):
    ''' Check if package `pkg_name` is present, and correct version

    Parameters
    ----------
    pkg_name : str
       name of package as imported into python
    version : {None, str}, optional
       minimum version of the package that we require. If None, we don't
       check the version.  Default is None
    optional : {False, True}, optional
       If False, raise error for absent package or wrong version;
       otherwise warn
    checker : callable, optional
       callable with which to return comparable thing from version
       string.  Default is ``distutils.version.LooseVersion``
    version_getter : {None, callable}:
       Callable that takes `pkg_name` as argument, and returns the
       package version string - as in::
       
          ``version = version_getter(pkg_name)``

       If None, equivalent to::

          mod = __import__(pkg_name); version = mod.__version__``
    '''
    if version_getter is None:
        def version_getter(pkg_name):
            mod = __import__(pkg_name)
            return mod.__version__
    try:
        mod = __import__(pkg_name)
    except ImportError:
        if not optional:
            raise RuntimeError('Cannot import package "%s" '
                               '- is it installed?' % pkg_name)
        log.warn('Missing optional package "%s"; '
                 'you may get run-time errors' % pkg_name)
        return
    if not version:
        return
    try:
        have_version = version_getter(pkg_name)
    except AttributeError:
        raise RuntimeError('Cannot find version for %s' % pkg_name)
    if checker(have_version) < checker(version):
        v_msg = 'You have version %s of package "%s"' \
            ' but we need version >= %s' % (
            have_version,
            pkg_name,
            version,
            )
        if optional:
            log.warn(v_msg + '; you may get run-time errors')
        else:
            raise RuntimeError(v_msg)


# Hard and soft dependency checking
package_check('scipy', '0.5')
package_check('sympy', '0.6.6')
def _mayavi_version(pkg_name):
    from enthought.mayavi import version
    return version.version
package_check('mayavi', '3.0', optional=True,
              version_getter=_mayavi_version)
    
################################################################################
# Import the documentation building classes. 

try:
    from build_docs import cmdclass
except ImportError:
    """ Pass by the doc build gracefully if sphinx is not installed """
    print "Sphinx is not installed, docs cannot be built"
    cmdclass = {}


################################################################################
# commands for installing the data
from numpy.distutils.command.install_data import install_data
from numpy.distutils.command.build_ext import build_ext

def data_install_msgs():
    from nipy.utils import make_datasource, DataError
    for name in ('templates', 'data'):
        try:
            make_datasource('nipy', name)
        except DataError, exception:
            log.warn('%s\n%s' % ('_'*80, exception))
        

class MyInstallData(install_data):
    """ Subclass the install_data to generate data install warnings if necessary
    """
    def run(self):
        install_data.run(self)
        data_install_msgs()


class MyBuildExt(build_ext):
    """ Subclass the build_ext to generate data install warnings if
        necessary: warn at build == warn early
        This is also important to get a warning when run a 'develop'.
    """
    def run(self):
        build_ext.run(self)
        data_install_msgs()


cmdclass['install_data'] = MyInstallData
cmdclass['build_ext'] = MyBuildExt

################################################################################

# We need to import nipy as late as possible, 
from nipy import  __doc__

def main(**extra_args):
    from numpy.distutils.core import setup
    
    setup( name = 'nipy',
           description = 'This is a neuroimaging python package',
           author = 'Various',
           author_email = 'nipy-devel@neuroimaging.scipy.org',
           url = 'http://neuroimaging.scipy.org',
           long_description = __doc__,
           configuration = configuration,
           cmdclass = cmdclass,
           scripts = glob('scripts/*.py'),
           **extra_args)


if __name__ == "__main__":
    main(**extra_setuptools_args)
