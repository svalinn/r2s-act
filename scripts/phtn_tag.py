#! /usr/bin/env python
from itaps import iBase,iMesh
from optparse import OptionParser
import sys

def FindFirstLine(MeshtalInputLines):#Finding # of lines to skip
    TableHeading ='   Energy         '
    n=1 #number of lines in mcnp file header
    HeaderLine=MeshtalInputLines[0][:64]
    while HeaderLine != TableHeading:
          n=n+1
          HeaderLine=MeshtalInputLines[n][:18]
    print 'Skipping Header:', n, 'lines'
    m=n+1 #first line of values
    return m

def MeshPointCount(MeshtalInputLines, m):#Counting Number of Meshpoints
    j=1 #initialising # of points
    while MeshtalInputLines[j+m-1][:11] == MeshtalInputLines[j+m][:11]:
          j=j+1
    print 'Mesh points found:', j
    return j

def EnergyGroupCount(MeshtalInputLines, m, j):#finding number of energy groups
    k=(len(MeshtalInputLines)-j-m)/j #number of energy groups, note, the "-j" is used to neglect flux "Total" rows in
    print 'Energy bins found:', k
    return k

def TagFluxes(mesh, meshtal, m, j, k) :
    print 'Tagging mesh with photon fluxes'
    voxels = mesh.getEntities(iBase.Type.region)
    column=[]; count=0 ;
    for n_groupID in range(1,k+2):
        tag=mesh.createTag("p_group_"+str(n_groupID),1,float)
        for x in range(0,j):
            num = MeshtalInputLines[m+x+j*count]
            column.append(num[42:53])
        count=count+1
        tag[voxels]=column
        column=[]
    return

def CloseFiles(): #Closes meshtal input and flux.in output files
    MeshtalInput.close()
  
def check_meshpoints(MeshtalInputLines, m, j, k, mesh):
    voxels = mesh.getEntities(iBase.Type.region)
    if j !=len(voxels):
        print >>sys.stderr, 'Number of meshtal points does not match number of mesh points'
        sys.exit(1)

    #find number of data points in InputLines
    l=0 #number of datapoints
    while MeshtalInputLines[m+l][:11] != '   Total   ':
        l=l+1
    print 'total data points found:', l
    if l != (j*k) :
        print >>sys.stderr, 'Number of data points does not equal meshpoints*energy groups'
        sys.exit(1)
   
if __name__=='__main__':
    parser = OptionParser()    
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.add_option("-m", "--meshtal",
                      action="store", dest="meshtal",
                      help="Path to meshtal input file")
    parser.add_option("-n", "--normalization", dest="Norm", type="float",
                      default=1, help="Flux normalization factor, default: %default")
    parser.add_option("-o", "--output", action="store", dest="output", default="mesh.vtk")
    (opts, args) = parser.parse_args()
    mesh = iMesh.Mesh()
    mesh.load(args[0])
    MeshtalInput=open(opts.meshtal, "r")
    MeshtalInputLines=MeshtalInput.readlines() 
    m=FindFirstLine(MeshtalInputLines)
    j=MeshPointCount(MeshtalInputLines, m)
    k=EnergyGroupCount(MeshtalInputLines, m,j)
    check_meshpoints(MeshtalInputLines, m, j, k, mesh)
    TagFluxes (mesh, opts.meshtal, m, j, k)
    mesh.save(opts.output)
    CloseFiles()
    print '\ncomplete'
	
