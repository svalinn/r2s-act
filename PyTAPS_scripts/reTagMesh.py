#! /usr/bin/env python

# This script imports a mesh from mmGridGen and creates a new tag
# for each material. 

from itaps import iBase,iMesh
from optparse import OptionParser
import sys

def reTagMesh( mesh ):
    count=0
    mats=mesh.getTagHandle("MATS")
    fracs=mesh.getTagHandle("FRACTIONS")
    matID=list(mats[mesh.rootSet])
    voxels = mesh.getEntities(iBase.Type.region)

    for num in matID :
        column=[]
        tag=mesh.createTag("mat_"+str(num),1,float)
        
        for i in fracs[voxels] :
            column.append(i[count])    
        
        tag[voxels]=column
        count=count+1
    return 

def parser():
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.set_defaults(output='matFracs.vtk')
    parser.add_option("-o", "--output",
                      action="store", dest="output",
                      help="output filename (can be .h5m or .vtk)")
   
    (options, args) = parser.parse_args()
    return options.output
  
if __name__=='__main__':
     out = parser()
     mesh = iMesh.Mesh()
     mesh.load( sys.argv[1] )
     reTagMesh( mesh )
     mesh.save( out )
