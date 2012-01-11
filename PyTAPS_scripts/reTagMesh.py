#! /usr/bin/env python
from itaps import iBase,iMesh
from optparse import OptionParser
import re
import sys

def parser():
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.add_option("-m", "--meshtal",
                      action="store", dest="meshtal",
                      help="Path to meshtal input file")
    parser.add_option("-n", "--normalization", dest="Norm", type="float",
                      default=1, help="Flux normalization factor, default: 1")
    parser.add_option("-v", "--volume",
                      action="store", dest="volume", default="1",
                      help="Total volume of the geometry, default: 1")
    parser.add_option("-o", "--output",
                      action="store", dest="output", default="mesh.vtk",
                      help="Mesh output filename (can be .h5m or .vtk), default: mesh.vtk")
    parser.add_option("-f", "--fluxinoutput",
                      action="store", dest="fluxin", default="ALARAflux.in",
                      help="Name of the ALARA flux input file, default: ALARAflux.in")    
    parser.add_option("-a", "--alara",
                      action="store", dest="alaraname", default="ALARA.in",
                      help="Name of the ALARA input file, default: ALARA.in")
    parser.add_option('-b', action='store_true', dest='backwardbool', 
                      default=False, help="print fluxes in decreasing energy")    
    
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

def MeshPointCount(MeshtalInputLines, m):#Counting Number of Meshpoints
    j=1 #initialising # of points
    while MeshtalInputLines[j+m-1][:11] == MeshtalInputLines[j+m][:11]:
          j=j+1
    print 'Mesh points found:', j
    return j

def EnergyGroupCount(MeshtalInputLines, m, j):#finding number of energy groups
    k=(len(MeshtalInputLines)-j-m)/j #number of energy groups
    print 'Energy bins found:', k
    return k

def PrintLowtoHigh(MeshtalInputLines, m, j, k, Norm):#Printing values to output file
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

def PrintHightoLow(MeshtalInputLines, m, j, k):
    #Norm=float(sys.argv[4])
    #Initial normailization factor from command line argument
    for t in range(0, j):
        pointoutput=''
        for s in range(k-1,-1,-1):
           pointoutput+=str(float(MeshtalInputLines[m+s*j + t][42:53])*Norm)+' '
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        FluxinOutput.write(pointoutput + '\n\n')
    print 'ALARAflux.in file creation sucessful \n'

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

def CloseFiles(): #Closes meshtal input and flux.in output files
    MeshtalInput.close()
    FluxinOutput.close()

def meshReader( filename ):
    nmfile = open("matFracs_results", 'w')
    mesh = iMesh.Mesh()
    mesh.load( filename )

    fracs=mesh.getTagHandle("FRACTIONS")
    errors=mesh.getTagHandle("ERRORS")
    mats=mesh.getTagHandle("MATS")  
    dims=mesh.getTagHandle("GRID_DIMS")
    
    nmfile.write("Materials "+re.sub("[\[\]\,]","",str(mats[mesh.rootSet]))+"\n")
    nmfile.write("Dimensions "+re.sub("[\[\]\,]","",str(dims[mesh.rootSet]))+"\n")
    for i in fracs[mesh.getEntities(iBase.Type.region)] :
        nmfile.write(re.sub("[\[\]\,]","",str(map(lambda x: round(x ,6), list(i))))+"\n")
    nmfile.close()
    return 
  
def make_alara(output_filename, geom_volume):
     # Open input file, read input, and create output file
     input = open("matFracs_results", 'r')
     readinp = input.readlines()
     alara_input = open(output_filename, 'w')
     
     # Determine order of material IDs
     matID = readinp[0].strip().split()
     del matID[0]
     matID=map(int ,matID)
     nummats=len(matID)
     print 'Materials order: ', matID

     # Determine intervals of mesh 
     dimID = readinp[1].strip().split()
     del dimID[0]
     dimID=map(int ,dimID)
     print 'Number of xyz intervals: ', dimID
     
     # Calculate volume per mesh element assuming equal volume for all elements
     totalvolume = geom_volume
     try : 
          float(totalvolume)
     except :
          print >>sys.stderr, "Invalid entry for volume."
          sys.exit(1)
     numzones=(dimID[0]*dimID[1]*dimID[2])
     elementvolume = float(totalvolume)/numzones
     print 'Volume per mesh element: ', elementvolume
     
     # Write ALARA geometry card to file
     alara_input.write('geometry rectangular\n\n')

     # Write ALARA volume card to file
     alara_input.write('volume\n')
     for i in range(1,numzones+1):
         zonename='\t'+str(elementvolume)+'\t'+'zone_'+str(i)+'\n'
         alara_input.write(zonename)
     alara_input.write('end\n\n')
     
     # Write ALARA mat_loading card to file
     alara_input.write('mat_loading\n')
     for i in range(1,numzones+1):
         zonemats=readinp[i+1].strip().split()
         if float(zonemats[0])==1.0:
             matname='\t'+'zone_'+str(i)+'\t'+'void'+'\n'
             alara_input.write(matname)  
         else:
             matname='\t'+'zone_'+str(i)+'\t'+'mix_'+str(i)+'\n'
             alara_input.write(matname)
     alara_input.write('end\n\n')
     
     # Write ALARA mixture definitions to file
     for i in range(1,numzones+1):
         zonemats=readinp[i+1].strip().split()
         if float(zonemats[0])==1.0:
             continue
         else:
            mixname='mixture'+'\t'+'mix_'+str(i)+'\n'
            alara_input.write(mixname)
            for j in range(1,nummats):
                     mixdef='\tmaterial\t'+'mat_'+str(matID[j])+'\t'+\
                     str(1)+'\t'+str(float(zonemats[j]))+'\n'
                     alara_input.write(mixdef)
            alara_input.write('end\n\n')
     input.close()
     alara_input.close()
     return
  
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
        j=MeshPointCount(MeshtalInputLines, m)
        k=EnergyGroupCount(MeshtalInputLines, m,j)
        if options.backwardbool==False:
            PrintLowtoHigh(MeshtalInputLines, m, j, k, options.Norm)
        else:
            PrintHightoLow(MeshtalInputLines, m, j, k)
        TagFluxes (mesh, options.meshtal, m, j, k)
        mesh.save(options.output)
    CloseFiles()
    print "generating ALARA input"
    meshReader(sys.argv[1])
    make_alara(options.alaraname,options.volume)
    print '\ncomplete'
	
