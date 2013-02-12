#!/usr/bin/env python
###############################################################################
# This script is used to print the value of a tag on a structured mesh.
# Usage:
# ./get_value.py structured_mesh x_value y_value z_value tag_name
#
# Note, the x_value, y_value, and z_value are the indicies of the mesh, 
# start at (0, 0, 0).
#
# The script will automatically search for a tag in the for tag_name+_error.
# If it exists, the error value will be appended to the answer:
# value (plus/minus) error
# 
###############################################################################

import linecache
from optparse import OptionParser
import sys
from itaps import iMesh, iBase
from r2s.scdmesh import ScdMesh

def print_value(sm, x, y, z, tag_name):
    voxel=sm.getHex(x,y,z)
    ans=str(sm.imesh.getTagHandle(tag_name)[voxel])
    
    try:
        error=sm.imesh.getTagHandle(tag_name+'_error')[voxel]
        print ans, u"\u00B1", error
    except iBase.TagNotFoundError:
        print ans



def main(arguments=None):

    parser = OptionParser\
             (usage='%prog structured_mesh x_value y_value z_value tag_name')

    #parser.add_option('-o', dest='fluxin_name', default='ALARAflux.in',\
    #    help='Name of ALARA fluxin output file, default=%default')

    (opts, args) = parser.parse_args( arguments )

    if len(args) != 6 :
        parser.error\
        ( '\nNeed exactly 5 arguments: run with -h flag for usage' )

    
    #Load Structured mesh from file
    sm=ScdMesh.fromFile(args[1])

    print_value(sm, int(args[2]), int(args[3]), int(args[4]), args[5])

if __name__ == '__main__':
    main(sys.argv)
                                                                                              

