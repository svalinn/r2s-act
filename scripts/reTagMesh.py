#! /usr/bin/env python

# The input to this script is the MOAB file (h5m) from mmGridGen.
# This script records the data stored on the FRACTION tag and creates
# a new tag on every mesh element for each material. This is currently 
# a necessary step in order to visualize the volume fractions using Paraview
# or Visit.

# Written by: Amir Jaber

from itaps import iBase,iMesh
from optparse import OptionParser

def parser():
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.add_option("-o", "--output",
                      action="store", dest="output", default="mesh.vtk",
                      help="Mesh output filename (can be .h5m or .vtk), default: %default")
    return parser.parse_args()

def TagMats(mesh):
    print 'Tagging mesh with material volume fractions'
    count=0
    mats=mesh.getTagHandle("MATS")
    dims=mesh.getTagHandle("GRID_DIMS")
    fracs=mesh.getTagHandle("FRACTIONS")
    matID=list(mats[mesh.rootSet])
    print '\tMaterials order: '+str(matID)
    dimID=list(dims[mesh.rootSet])
    print '\tNumber of xyz intervals: '+str(dimID)+'\n'
    voxels = mesh.getEntities(iBase.Type.region)

    for num in matID :
        column=[]
        tag=mesh.createTag('mat_'+str(num),1,float)
        
        for i in fracs[voxels] :
            column.append(i[count])    
        tag[voxels]=column
        count=count+1
    return

if __name__=='__main__':
    (options, args)= parser()
    mesh = iMesh.Mesh()
    print "Read "+args[0]
    mesh.load(args[0])
    TagMats(mesh)    
    mesh.save(options.output)   
    print "Wrote "+options.output
	
