"""
Frame of reference/coordinates package.

Mathematical model
==================
The idea of a chart :lm:`\\phi` : I{U} S{sub} I{M} S{->} B{R}^k
on a "manifold" I{M}.  For a chart both input (I{M}) and output coordinates
(B{R}^k) must be defined and a map relating the two coordinate systems.

Description
===========
The modules in this package contains classes which define the space in which an
image exists and also functions for manipulating and traversing this space.

The basic class which defines an image space is a CoordinateMap (coordinate_map.py). A 
CoordinateMap consists of an input CoordinateSystem (coordinate_system.py), an
output CoordinateSystem, and a Mapping (mapping.py) which converts point in the
input space to points in the output space.

A `CoordinateSystem` consists of a set of ordered `Axis` (axis.py) objects. Each
Axis can be either discrete (`DiscreteAxis`) or continuous (`ContinuousAxis`). 

The typical use of a `CoordinateMap` is to define how points in an `Image`
(core.image.__init__.py) object's raw data map into real space. 

`Image` traversal is general done in terms of the underlying coordinate_map, and a number of
iterators are provided to traverse points in the coordinate_map (iterators.py). Access to
available iterators is done through the CoordinateMap interface, rather than 
accessing the iterator classes directly. 

The other common image access method is to take slices through the coordinate_map. In 
slices.py functions are presented which will return a `CoordinateMap` representing
a single slice through a larger coordinate_map.

"""
__docformat__ = 'restructuredtext'

import axis
import coordinate_system
import coordinate_map
import mni
import slices

__all__ = ["axis", "coordinate_system", "coordinate_map", 
           "mni", "slices"]

from neuroimaging.testing import Tester
test = Tester().test
bench = Tester().bench
