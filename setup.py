#!/usr/bin/env python
import sys
import os
import zipfile

from nipy import  __doc__

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

# extra_setuptools_args is injected by the setupegg.py script, for
# running the setup with setuptools.
if not 'extra_setuptools_args' in globals():
    extra_setuptools_args = dict()


################################################################################
# Extra command class, for building and shipping documentation
################################################################################
try:
    from sphinx.setup_command import BuildDoc
    from distutils.cmd import Command

    ##############################################################################
    # Code to force the API generation 
    class APIDocs(Command):
        description = \
        """ Generate API docs """

        user_options = [
            ('None', None, 'this command has no options'),
            ]
    
        def run(self):
            os.chdir('doc')
            try:
                os.system('%s ../tools/build_modref_templates.py' 
                                                    % sys.executable)
            finally:
                os.chdir('..')
    
        def initialize_options(self):
            pass
        
        def finalize_options(self):
            pass


    ##############################################################################
    # Code to build the docs 

    class MyBuildDoc(BuildDoc):
        
        def run(self):
            # We need to be in the doc directory for to plot_directive
            # and API generation to work
            os.chdir('doc')
            try:
                if not os.path.exists(os.path.join('api', 'generated')):
                    os.system('%s ../tools/build_modref_templates.py' 
                                                        % sys.executable)
                BuildDoc.run(self)
            finally:
                os.chdir('..')
    

    ##############################################################################
    # Code to copy the sphinx-generated html docs in the distribution.
    DOC_BUILD_DIR = os.path.join('build', 'sphinx', 'html')

    def relative_path(filename):
        """ Return the relative path to the file, assuming the file is
            in the DOC_BUILD_DIR directory.
        """
        length = len(os.path.abspath(DOC_BUILD_DIR)) + 1
        return os.path.abspath(filename)[length:]


    class ZipHelp(Command):
        description = \
        """ Zip the help created by the build_sphinx, and put it in the 
            source distribution. """

        user_options = [
            ('None', None, 'this command has no options'),
            ]
    
        def run(self):
            if not os.path.exists(DOC_BUILD_DIR):
                raise OSError, 'Doc directory does not exist.'
            target_file = os.path.join('doc', 'documentation.zip')
            # ZIP_DEFLATED actually compresses the archive. However, there
            # will be a RuntimeError if zlib is not installed, so we check
            # for it. ZIP_STORED produces an uncompressed zip, but does not
            # require zlib.
            try:
                zf = zipfile.ZipFile(target_file, 'w', 
                                                compression=zipfile.ZIP_DEFLATED)
            except RuntimeError:
                zf = zipfile.ZipFile(target_file, 'w', 
                                                compression=zipfile.ZIP_STORED)    

            for root, dirs, files in os.walk(DOC_BUILD_DIR):
                relative = relative_path(root)
                if not relative.startswith('.doctrees'):
                    for f in files:
                        zf.write(os.path.join(root, f), 
                                os.path.join(relative, 'html_docs', f))
            zf.close()

        def initialize_options(self):
            pass
        
        def finalize_options(self):
            pass


    cmdclass = {'zip_help': ZipHelp,
                'build_sphinx': MyBuildDoc,
                'api_docs': APIDocs,
                }

except ImportError:
    """ Fail gracefully if sphinx is not installed """
    print "Sphinx is not installed, docs cannot be built"
    cmdclass = {}


################################################################################

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
           **extra_args)


if __name__ == "__main__":
    main(**extra_setuptools_args)
