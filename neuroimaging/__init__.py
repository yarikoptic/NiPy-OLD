# -*- coding: utf-8 -*-
"""
Neuroimaging tools for Python (NIPY).

The aim of NIPY is to produce a platform-independent Python environment for
the analysis of brain imaging data using an open development model.

While
the project is still in its initial stages, packages for file I/O, script
support as well as single subject fMRI and random effects group comparisons
model are currently available.

Specifically, we aim to:

   1. Provide an open source, mixed language scientific programming
      environment suitable for rapid development.

   2. Create sofware components in this environment to make it easy
      to develop tools for MRI, EEG, PET and other modalities.

   3. Create and maintain a wide base of developers to contribute to
      this platform.

   4. To maintain and develop this framework as a single, easily
      installable bundle.

Package Organization 
==================== 
The neuroimaging package contains the following subpackages and modules: 

.. packagetree:: 
   :style: UML  
"""
__docformat__ = 'restructuredtext en'



from version import version as __version__
# FIXME
#__revision__ = int("$Rev$".split()[-2])
__status__   = 'alpha'
__date__    = "$LastChangedDate$"
__url__     = 'http://neuroimaging.scipy.org'

packages = (
  'neuroimaging',
  'neuroimaging.algorithms',
  'neuroimaging.algorithms.tests',
  'neuroimaging.algorithms.statistics',
  'neuroimaging.algorithms.statistics.tests',
  'neuroimaging.core',
  'neuroimaging.core.image',
  'neuroimaging.core.image.tests',
  'neuroimaging.core.reference',
  'neuroimaging.core.reference.tests',
  'neuroimaging.io',
  'neuroimaging.io.tests',
  'neuroimaging.modalities',
  'neuroimaging.modalities.fmri',
  'neuroimaging.modalities.fmri.tests',
  'neuroimaging.modalities.fmri.fmristat',
  'neuroimaging.modalities.fmri.fmristat.tests',
  'neuroimaging.utils',
  'neuroimaging.utils.tests',
  'neuroimaging.utils.tests.data',
  'neuroimaging.testing')

def import_from(modulename, objectname):
    """Import and return objectname from modulename."""
    module = __import__(modulename, {}, {}, (objectname,))
    try:
        return getattr(module, objectname)
    except AttributeError:
        return None

from neuroimaging.testing import Tester
test = Tester().test
bench = Tester().bench
