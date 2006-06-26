#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
# 
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.neuroimaging.extra.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
# 
# Author: David C. Morrill
# Date: 10/25/2004
# Description: Define various helper functions that are useful for creating
#              traits based user interfaces.
#  Symbols defined: user_name_for
#------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from string \
    import uppercase, lowercase
    
#----------------------------------------------------------------------------
#  Return a 'user-friendly' name for a specified trait:
#----------------------------------------------------------------------------

def user_name_for ( name ):
    name       = name.replace( '_', ' ' )
    name       = name[:1].upper() + name[1:]
    result     = ''
    last_lower = 0
    for c in name:
        if (c in uppercase) and last_lower:
           result += ' '
        last_lower = (c in lowercase)
        result    += c
    return result

