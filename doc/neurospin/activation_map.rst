
Automatic plotting of activation maps
=====================================

.. currentmodule:: nipy.neurospin.viz.activation_maps

The module :mod:`nipy.neurospin.viz.activation_maps` provides functions to plot
visualization of activation maps in a non-interactive way.

2D cuts of an activation map can be plotted and superimposed on an
anatomical map using matplotlib_. In addition, Mayavi2_ can be used to
plot 3D maps, using volumetric rendering. Some emphasis is made on
automatic choice of default parameters, such as cut coordinates, to give
a sensible view of a map in a purely automatic way, for instance to save
a summary of the output of a calculation.

.. _matplotlib: http://matplotlib.sourceforge.net

.. _Mayavi2: http://code.enthought.com/projects/mayavi

.. warning:: 

    The content of the module will change over time, as neuroimaging
    volumetric data structures are used instead of plain numpy arrays.

An example
-----------

::

    from nipy.neurospin.viz.activation_maps import plot_map, mni_sform, \
            coord_transform

    # First, create a fake activation map: a 3D image in MNI space with
    # a large rectangle of activation around Brodmann Area 26
    import numpy as np
    mni_sform_inv = np.linalg.inv(mni_sform)
    map = np.zeros((182, 218, 182))
    x, y, z = -6, -53, 9
    x_map, y_map, z_map = coord_transform(x, y, z, mni_sform_inv)
    map[x_map-30:x_map+30, y_map-3:y_map+3, z_map-10:z_map+10] = 1
    
    # And now, visualize it:
    plot_map(map, mni_sform, cut_coords=(x, y, z), vmin=0.5)

This creates the following image:

.. image:: activation_map.png

The same plot can be obtained fully automaticaly, by using
:func:`auto_plot_map` to find the activation threshold `vmin` and the cut
coordinnates::

    from nipy.neurospin.viz.activation_maps import auto_plot_map
    auto_plot_map(map, mni_sform)

In this simple example, the code will easily detect the bar as activation
and position the cut at the center of the bar.


`nipy.neurospin.viz.activation_maps` functions
-------------------------------------------------

.. autosummary::
    :toctree: generated

    coord_transform
    find_activation
    find_cut_coords
    plot_map_2d
    auto_plot_map


3D plotting utilities
---------------------------

.. currentmodule:: nipy.neurospin.viz.maps_3d

The module :mod:`nipy.neurospin.viz.maps_3d` can be used as helpers to
represent neuroimaging volumes with Mayavi2_. 

.. autosummary::
    :toctree: generated

    plot_map_3d
    plot_anat_3d

More versalite visualizations, the core idea is that given a 3D map
and an affine, the data is exposed in Mayavi as a volumic source, with
world space coordinates corresponding to figure coordinates.
Visualization modules can be applied on this data source as explained in
the `Mayavi manual
<http://code.enthought.com/projects/mayavi/docs/development/html/mayavi/mlab.html#assembling-pipelines-with-mlab>`_

.. autosummary::
    :toctree: generated

    affine_img_src

