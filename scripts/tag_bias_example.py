#! /usr/bin/env python

import sys
import os.path
from itaps import iBase, iMesh
import ConfigParser

from r2s import mmgrid
from r2s.scdmesh import ScdMesh, ScdMeshError
from r2s_setup import get_input_file
from r2s_setup import FileMissingError


#####################################################################
# Note, skip beyond this method for setting up the biasing
#
def calc_centers_list(scd):
    """Create list of voxel centroids for a structured cartesian mesh
    
    Method creates a 1D list of voxel centroids in form [x,y,z]
    
    Parameters
    ----------
    scd : cdMesh object.

    Returns
    -------
    centers : list
        a 1D list of voxel volumes in order 'xyz'

    Notes
    -----
    Voxel ordering follows meshtal file convention which is:

    - for x for y iterate z
    - for x iterate y
    - iterate x
    """
    
    meshplanes = [ scd.getDivisions('x'),
                   scd.getDivisions('y'),
                   scd.getDivisions('z') ]

    oldz = meshplanes[2][0]
    oldy = meshplanes[1][0]
    oldx = meshplanes[0][0]

    nxdiv = len(meshplanes[0]) - 1
    nydiv = len(meshplanes[1]) - 1
    nzdiv = len(meshplanes[2]) - 1

    # create 1D list
    centers = [[0,0,0]] * (nxdiv * nydiv * nzdiv)

    for cntx, x in enumerate(meshplanes[0][1:]):
        oldy = meshplanes[1][0]
        for cnty, y in enumerate(meshplanes[1][1:]):
            oldz = meshplanes[2][0]
            for cntz, z in enumerate(meshplanes[2][1:]):
                # Calc volume here
                centers[nydiv*nzdiv*cntx + nzdiv*cnty + cntz] = \
                        [oldx+(x - oldx)/2, \
                         oldy+(y - oldy)/2, \
                         oldz+(z - oldz)/2]
                oldz = z
            oldy = y
        oldx = x
    
    return centers

#####################################################################

# Look for and open configuration file for r2s workflow
cfgfile = 'r2s.cfg'
if len(sys.argv) > 1:
    cfgfile = sys.argv[1]

config = ConfigParser.SafeConfigParser()
config.read(cfgfile)

# Required input file from config file
datafile = get_input_file(config, 'step1_datafile')

# Read in the mesh
smesh = ScdMesh.fromFile(datafile)

# Get the Tag object called PHTN_BIAS
try:
    bias_tag = smesh.imesh.createTag("PHTN_BIAS",1,"d")
except iBase.TagAlreadyExistsError:
    print "Tag already exists. Tags are being overwritten."
    bias_tag = smesh.imesh.getTagHandle("PHTN_BIAS")

# Calculate the center of all voxels in the problem and store in a list
centers = calc_centers_list(smesh)

# EXAMPLE OF MATH FOR DISTANCE BASED BIASING:
# This for loop calculates and tags the bias values.
# In this example, based on the voxel's distance from the plane y == -20
#  we assign a bias value between 1 and (maxBias+1).
# The variable norm is the maximum distance of a voxel from our plane or
#  point of interest.
# In this case, we have a slab going from y = -20 to y = 20, thus norm = 40.
# chkDim determines which dimension to measure distance from, in this 1D case.
for cnt, vox in enumerate(smesh.iterateHex('xyz')):
    # We set up a 1 dimensional distance based linear biasing
    norm = 40
    maxBias = 10 - 1
    chkDim = 1  # 0->x 1->y 2->z
    offset = -20
    # linear scaling of bias value:
    bias_tag[vox] = -1 * (centers[cnt][chkDim] + offset) / norm \
            * maxBias + 1
    # quadratic scaling of bias value:
    #bias_tag[vox] = (((centers[cnt][chkDim]+offset)*maxBias/norm)**2)/maxBias + 1


smesh.imesh.save(datafile)

print "Max bias used:", maxBias + 1
print "Done! Tagged bias values to {0}".format(datafile)
