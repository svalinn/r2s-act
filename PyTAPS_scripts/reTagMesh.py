#! /usr/bin/env python


from itaps import iBase,iMesh
from optparse import OptionParser
import sys

def parser():
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.set_defaults(output='matFracs.vtk')
    parser.add_option("-o", "--output",
                      action="store", dest="output", default="mesh.out",
                      help="output filename (can be .h5m or .vtk)")
    parser.add_option("-f", "--fluxinoutput",
                      action="store", dest="fluxin", default="fluxin.out",
                      help="Name of the fluxin output file")
    parser.add_option("-m", "--meshtal",
                      action="store", dest="meshtal",
                      help="meshtal file name to be store on mesh")
    parser.add_option('-b', action='store_true', dest='backwardbool', 
                      default=False, help="print fluxes in decreasing energy")
    parser.add_option("-n", "--normalization", dest="Norm", type="float",
                      default=1, help="flux normalization factor")   
    (options, args) = parser.parse_args()
    return (options, args)

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

def MeshPointCount(m):#Counting Number of Meshpoints
    j=1 #initialising # of points
    while MeshtalInputLines[j+m-1][:11] == MeshtalInputLines[j+m][:11]:
          j=j+1
    print 'Mesh points found:', j
    return j

def EnergyGroupCount(m, j):#finding number of energy groups
    k=(len(MeshtalInputLines)-j-m)/j #number of energy groups
    print 'Energy bins found:', k
    return k

def PrintLowtoHigh(m, j, k, Norm):#Printing values to output file
    #Norm=float(sys.argv[4])
    #Initial normailization factor from command line argument
    for t in range(0, j):
        pointoutput=''
        for s in range(0,k):
           pointoutput+=str(float(MeshtalInputLines[m+s*j + t][42:53])*Norm)+' '
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        FluxinOutput.write(pointoutput + '\n\n')
    print 'File creation sucessful \n'

def PrintHightoLow(m, j, k):
    #Norm=float(sys.argv[4])
    #Initial normailization factor from command line argument
    for t in range(0, j):
        pointoutput=''
        for s in range(k-1,-1,-1):
           pointoutput+=str(float(MeshtalInputLines[m+s*j + t][42:53])*Norm)+' '
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        FluxinOutput.write(pointoutput + '\n\n')
    print 'Fluxin creation sucessful \n'

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

def TagFluxes(mesh, meshtal, m, j, k) :
    print 'Tagging mesh with neutron fluxes'
    voxels = mesh.getEntities(iBase.Type.region)
    column=[]; count=0 ;
    for n_groupID in range(1,k+2):
        tag=mesh.createTag("group_"+str(n_groupID),1,float)
        for x in range(0,j):
            num = MeshtalInputLines[m+x+j*count]
            column.append(num[42:53])
        count=count+1
        tag[voxels]=column
        column=[]
    return

def CloseFiles(): #Closes meshtal input and fluxin output files
    MeshtalInput.close()
    FluxinOutput.close()
  
if __name__=='__main__':
    (options, args)= parser()
    mesh = iMesh.Mesh()
    mesh.load(sys.argv[1])
    TagMats(mesh)    
    if options.meshtal != None :
        print 'Parsing meshtal file'
        MeshtalInput=open(options.meshtal, "r")
        MeshtalInputLines=MeshtalInput.readlines() 
        FluxinOutput=file(options.fluxin, "w")
        m=FindFirstLine(MeshtalInputLines)
        j=MeshPointCount(m)
        k=EnergyGroupCount(m,j)
        if options.backwardbool==False:
            PrintLowtoHigh(m,j,k, options.Norm)
        else:
            PrintHightoLow(m,j,k)
        TagFluxes (mesh, options.meshtal, m, j, k)
    print '\ncomplete'
    mesh.save(options.output)
    CloseFiles()
