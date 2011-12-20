#! /usr/bin/env python

from itaps import iBase,iMesh
import sys

def meshReader( filename ):
    mesh = iMesh.Mesh()
    mesh.load( filename )
    fracs=mesh.getTagHandle("FRACTIONS")
    errors=mesh.getTagHandle("ERRORS")
    mats=mesh.getTagHandle("MATS")  
    dims=mesh.getTagHandle("GRID_DIMS")
    
    print "Materials :"+str(mats.getData(mesh.rootSet))
    print "Dimensions :"+str(dims.getData(mesh.rootSet))
    for i in mesh.getEntities(iBase.Type.region) :
        print fracs.getData(i)
        
if __name__=='__main__':
    meshReader(sys.argv[1])
	