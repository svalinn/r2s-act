#! /usr/bin/env python

# This script imports a mesh from mmGridGen and creates a new tag
# for each material. 

from itaps import iBase,iMesh
from optparse import OptionParser
import sys

def TagMats( mesh ):
    print "Tagging mesh with material volume fractions"
    count=0
    mats=mesh.getTagHandle("MATS")
    dims=mesh.getTagHandle("GRID_DIMS")
    fracs=mesh.getTagHandle("FRACTIONS")
    matID=list(mats[mesh.rootSet])
    print "\tMaterials order: "+str(matID)
    dimID=list(dims[mesh.rootSet])
    print "\tNumber of xyz intervals: "+str(dimID)+'\n'
    voxels = mesh.getEntities(iBase.Type.region)

    for num in matID :
        column=[]
        tag=mesh.createTag("mat_"+str(num),1,float)
        
        for i in fracs[voxels] :
            column.append(i[count])    
        
        tag[voxels]=column
        count=count+1
    return 

def TagFluxes( mesh, meshtal ) :
    print "Tagging mesh with neutron fluxes"
    Input=open(meshtal, "r")
    InputLines=Input.readlines() 
    TableHeading ='   Energy         '
    n=1 #number of lines in mcnp file header
    HeaderLine=InputLines[0][:64]
    while HeaderLine != TableHeading:
          n=n+1
          HeaderLine=InputLines[n][:18]
    print '\tSkipping Header:', n, 'lines'
    m=n+1 #first line of values
    j=1
    while InputLines[j+m-1][:11] == InputLines[j+m][:11]:
          j=j+1
    print '\tMesh points found:', j
    k=(len(InputLines)-j-m)/j #number of energy groups
    print '\tEnergy bins found:', k
    voxels = mesh.getEntities(iBase.Type.region)
    column=[]; count=0 ;
    for groupID in range(1,k+2):
        tag=mesh.createTag("group_"+str(groupID),1,float)
        for x in range(0,j):
            num = InputLines[m+x+j*count]
            column.append(num[42:53])
        count=count+1
        tag[voxels]=column
        column=[]
    return 

def parser():
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.set_defaults(output='matFracs.vtk')
    parser.add_option("-o", "--output",
                      action="store", dest="output",
                      help="output filename (can be .h5m or .vtk)")
    parser.add_option("-m", "--meshtal",
                      action="store", dest="meshtal",
                      help="meshtal file name to be store on mesh")   
    (options, args) = parser.parse_args()
    return (options, args)
  
if __name__=='__main__':
     (options, args)= parser()
     mesh = iMesh.Mesh()
     mesh.load( sys.argv[1] )
     TagMats( mesh )
     if options.meshtal != None :
         TagFluxes ( mesh, options.meshtal )
     mesh.save( options.output )
