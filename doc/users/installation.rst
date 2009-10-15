.. _installation:

====================
Download and Install
====================

This page covers the necessary steps to install and run NIPY.  Below
is a list of required dependencies, along with additional software
recommendations.

NIPY is currently *ALPHA* quality, but is rapidly improving. If you are
trying to get some work done wait until we have a stable release. For now,
the code will primarily be of interest to developers.

Dependencies
------------

Must Have
^^^^^^^^^

  Python_ 2.4 or later
  
  NumPy_ 1.2 or later

  SciPy_ 0.7 or later
    Numpy and Scipy are high-level, optimized scientific computing libraries.

  PyNifti_
    We are using pynifti for the underlying file IO for nifti files.

  gcc_
    NIPY does contain a few C extensions for optimized
    routines. Therefore, you must have a compiler to build from
    source.  XCode_ (OSX) and MinGW_ (Windows) both include gcc.  (*Once
    we have binary packages, this requirement will not be necessary.*)

Strong Recommendations
^^^^^^^^^^^^^^^^^^^^^^

  iPython_
    Interactive python environment.

  Matplotlib_
    2D python plotting library.

Installing from binary packages
-------------------------------

Currently we do not have binary packages.  Until we do, the easiest
installation method is to download the source tarball and follow the
:ref:`building_source` instructions below.

.. _building_source:

Building from source code
-------------------------

Developers should look through the 
:ref:`development quickstart <development-quickstart>` 
documentation.  There you will find information on building NIPY, the
required software packages and our developer guidelines.

If you are primarily interested in using NIPY, download the source
tarball and follow these instructions for building.  The installation
process is similar to other Python packages so it will be familiar if
you have Python experience.

Unpack the source tarball and change into the source directory.  Once in the
source directory, you can build the neuroimaging package using::

    python setup.py build

To install, simply do::
   
    sudo python setup.py install

.. note::

    As with any Python_ installation, this will install the modules
    in your system Python_ *site-packages* directory (which is why you
    need *sudo*).  Many of us prefer to install development packages in a
    local directory so as to leave the system python alone.  This is
    mearly a preference, nothing will go wrong if you install using the
    *sudo* method.  To install in a local directory, use the **--prefix**
    option.  For example, if you created a ``local`` directory in your
    home directory, you would install nipy like this::

	python setup.py install --prefix=$HOME/local

.. note::

    If you have downloaded the source from the development tree, you
    also should get and install the ``nipy-data`` and ``nipy-templates``
    packages (not required, but strongly suggested). Please see
    http://nipy.sourceforge.net/data-packages and :ref:`data-files`.

Building for 64-bit Snow Leopard
--------------------------------

How you install nipy for Snow Leopard depends on which version of
Python you have installed.  There are two versions we know work, using
the Python that shipped with Snow Leopard, and using a 64-bit
MacPorts_ version.

If you are using the Python that shipped with Snow Leopard, there are
detailed instructions on `this blog
<http://blog.hyperjeff.net/?p=160>`_ for installing numpy_ and scipy_.
The critical step is to set the appropriate flags for the C and
Fortran compilers so they match the architecture of your version of
Python.  You can discover the architecture of your Python by doing the
following::

    file `which python`

For example, on my 32-bit Leopard (10.5) it's a Universal binary,
built for both ppc and i386 architectures::

    /usr/local/bin/python: Mach-O universal binary with 2 architectures
    /usr/local/bin/python (for architecture i386):	Mach-O executable i386
    /usr/local/bin/python (for architecture ppc):	Mach-O executable ppc

On a 64-bit MacPorts_ install on Snow Leopard (10.6), it's built for
64-bit only::

    /opt/local/bin/python: Mach-P 64-bit executable x86_64

For the 64-bit MacPorts_ install, set the flags and build using this::

    export MACOSX_DEPLOYMENT_TARGET=10.6
    export LDFLAGS="-arch x86_64 -Wall -undefined dynamic_lookup -bundle -fPIC"
    export FFLAGS="-arch x86_64 -O2 -Wall -fPIC"
    python setup.py build

These sites may also be useful:

* `readline fix for ipython <http://blog.zacharyvoase.com/post/174280299>`_
* `to graphically select the full 64-bit environment
  <http://www.ahatfullofsky.comuv.com/English/Programs/SMS/SMS.html>`_

.. _MacPorts: http://www.macports.org/

.. include:: ../links_names.txt

